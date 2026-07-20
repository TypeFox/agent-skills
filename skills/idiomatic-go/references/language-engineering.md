# Language engineering patterns reference

Patterns that recur in Go tools for *programming languages* — parsers, language servers (LSP), type checkers, validators, DSL implementations — and go beyond baseline idiomatic Go. The other references cover the general idioms; this one covers the design shapes specific to code that reads, analyzes, and serves source code. It assumes the vocabulary of language implementation (AST, scope, symbol, reference, diagnostic) and applies whether you build a toolkit from scratch or extend an existing Go framework. This is deliberate machinery — overkill for ordinary application code, load-bearing for a language implementation.

Version-specific APIs are annotated inline: `iter.Seq` needs Go 1.23, `sync.WaitGroup.Go` needs Go 1.25.

Contents:

- [Nil-safe AST navigation](#nil-safe-ast-navigation)
- [Traversal: a callback primitive under an iterator veneer](#traversal-a-callback-primitive-under-an-iterator-veneer)
- [Optional capability interfaces](#optional-capability-interfaces)
- [Empty means empty: non-nil sentinels](#empty-means-empty-non-nil-sentinels)
- [Source positions as typed units](#source-positions-as-typed-units)
- [One text handle, editor buffer shadowing disk](#one-text-handle-editor-buffer-shadowing-disk)
- [Scopes: lazy chains along AST containment](#scopes-lazy-chains-along-ast-containment)
- [References: typed wrapper, untyped interface](#references-typed-wrapper-untyped-interface)
- [Once-only resolution with context-keyed cycle detection](#once-only-resolution-with-context-keyed-cycle-detection)
- [The build pipeline: phased, parallel within a phase](#the-build-pipeline-phased-parallel-within-a-phase)
- [Incremental state: a progressive aggregate and a phase bitmask](#incremental-state-a-progressive-aggregate-and-a-phase-bitmask)
- [Staying responsive: the write-to-read lock downgrade](#staying-responsive-the-write-to-read-lock-downgrade)
- [Keep the domain free of the protocol](#keep-the-domain-free-of-the-protocol)
- [Performance discipline and hot-path data structures](#performance-discipline-and-hot-path-data-structures)

## Nil-safe AST navigation

AST code chains accessors constantly — "the document of the container of the nearest enclosing block". If every hop panics on nil, every call site sprouts defensive checks. Make the core node and reference accessors *nil-receiver-safe*: guard `if n == nil` and return the zero value, so "not there" degrades to a zero value instead of a crash.

```go
func (n *Node) Container() *Node {
    if n == nil {
        return nil // any nil hop yields nil, not a panic
    }
    return n.container
}

doc := n.Container().Container().Document() // caller checks once, at the end
```

This is SKILL.md's "nil is a meaningful receiver value", applied as a *documented contract*: callers rely on it, so it must hold for every accessor on the type, not just the ones that happen to be safe today.

## Traversal: a callback primitive under an iterator veneer

Deep tree walks are a hot path. Build them on a callback primitive taking a `func(*Node) bool` (return `false` to stop), then layer ergonomic `iter.Seq` wrappers (Go 1.23) on top. The callback form avoids the per-step coroutine handoff a native iterator pays on a deep walk; the public API still reads as a range loop.

```go
func (n *Node) ForEachDescendant(visit func(*Node) bool) bool {
    for _, c := range n.children {
        if !visit(c) || !c.ForEachDescendant(visit) {
            return false // propagate the stop up the recursion
        }
    }
    return true
}

func (n *Node) Descendants() iter.Seq[*Node] {
    return func(yield func(*Node) bool) { n.ForEachDescendant(yield) }
}
```

The subtlety: thread `yield`'s return value back up the recursion. `yield` returns `false` when the consumer `break`s the `for range`; ignore it and the walk keeps running after the consumer has stopped caring. The same discipline lets lazy operators (`Map`, `Filter`, `FlatMap`) compose over `iter.Seq` while still short-circuiting — which is what makes the lazy scope chains below cost nothing until consumed.

**Apply the veneer to every traversal direction the API exposes, not just the one that comes up first.** A node type with both parent-ward and child-ward navigation needs *both* wrapped — shipping `Descendants()` while leaving upward traversal as a bare loop (or vice versa) is a half-finished version of this pattern, not a smaller one:

```go
func (n *Node) Ancestors() iter.Seq[*Node] {
    return func(yield func(*Node) bool) {
        for p := n.Container(); p != nil; p = p.Container() {
            if !yield(p) {
                return // consumer broke out; stop walking upward
            }
        }
    }
}
```

`Ancestors` has no recursion to thread `yield` through — the chain is already linear — but it's the same veneer-over-primitive shape: a plain loop underneath, `iter.Seq[*Node]` on top. The same question is worth asking of any bidirectional relationship a language toolkit models — parent/child, definition/reference, caller/callee: if one direction gets the callback-primitive-plus-veneer treatment, the other is under the same obligation, not a separate feature to add later.

## Optional capability interfaces

A generated AST has dozens of node types, and only some participate in any given concern (validation, symbol export, folding). Rather than force every node to implement a fat interface, define *small, optional* capability interfaces and check for them with a type assertion at the use site, falling back to a default when a node doesn't implement one.

```go
type Validator interface {
    Validate(ctx context.Context, report *Diagnostics)
}

func validate(ctx context.Context, n *Node, report *Diagnostics) {
    if v, ok := n.impl.(Validator); ok {
        v.Validate(ctx, report)
        return
    }
    defaultValidate(ctx, n, report)
}
```

A node opts into a behavior by implementing the interface on its implementation struct — no registration, no base class, no framework edit. The same move discovers lifecycle participants: instead of maintaining an explicit hook list, ask a registry for *every* service that satisfies a participation interface and call them.

```go
for p := range registry.All[InitializeParticipant]() {
    p.OnInitialize(ctx, params)
}
```

Behavior is discovered by what a value *is*, not by a list someone had to remember to populate.

## Empty means empty: non-nil sentinels

"Nothing here" — an empty scope, an empty symbol table, no diagnostics — recurs everywhere, and modeling it as `nil` forces every consumer to nil-check before use. Use a reusable *non-nil* sentinel that answers the interface with empty results, so consumers query it uniformly.

```go
var EmptyScope Scope = emptyScope{}

type emptyScope struct{}

func (emptyScope) Lookup(name string) (Symbol, bool) { return Symbol{}, false }
func (emptyScope) All() iter.Seq[Symbol]             { return func(func(Symbol) bool) {} }
```

Enforce the contract loudly: if a provider returns nil where a sentinel was required, panic with a message that names the fix rather than letting it surface later as a distant nil dereference.

```go
func resolveIn(s Scope, name string) (Symbol, bool) {
    if s == nil {
        panic("nil scope: return EmptyScope for an empty result, never nil")
    }
    return s.Lookup(name)
}
```

This is one of the rare places a library should panic (see SKILL.md's errors section): a nil sentinel is a bug in the *provider*, worth failing on immediately.

## Source positions as typed units

Positions are the most-passed values in a toolkit, and a byte offset, a line, and a column are all "just an int" — which is why they get transposed. Give each its own named type so the compiler rejects the mistake, and pin the semantics that bite everyone in the doc comment.

```go
type (
    ByteOffset int32 // 0-based offset into the UTF-8 source
    Line       int32 // 0-based line number
    Column     int32 // 0-based offset within the line, in UTF-16 code units
)

type Position struct {
    Line   Line
    Column Column
}

// Half-open: End is the first position past the range.
type Range struct{ Start, End Position }
```

Two traps worth encoding in the types: LSP measures columns in *UTF-16 code units* by default (negotiable since LSP 3.17, but UTF-16 is what you get otherwise), so a column is neither a byte offset nor a rune count; and ranges are *half-open*, so boundary comparisons stay consistent. `int32` over `int` is a density choice — positions are stored in bulk, so halving their size matters at scale.

## One text handle, editor buffer shadowing disk

A language server reads text that may live on disk or in an unsaved editor buffer, and lexers, parsers, and resolvers shouldn't care which. Consume all text through one read interface, backed by two implementations — an immutable on-disk snapshot and an *overlay* layering unsaved edits over it. The store resolves a URI to the overlay when one is open, the file otherwise, so every consumer sees the *effective* content.

```go
type Source interface {
    Bytes() []byte
    // The byte <-> UTF-16-position mapping the protocol needs lives here too,
    // computed once against the effective content.
    OffsetAt(Position) ByteOffset
    PositionAt(ByteOffset) Position
}

func (s *Store) Source(uri URI) Source {
    if ov, ok := s.overlays[uri]; ok {
        return ov // unsaved buffer shadows disk
    }
    return s.files[uri]
}
```

Concentrating the position-mapping logic behind this one handle means it's written and tested once, against whatever content is actually in effect.

## Scopes: lazy chains along AST containment

A name-resolution scope needn't be a precomputed symbol table. Assemble it *on lookup* by walking up the container chain: each container contributes its local symbols, chained to the enclosing container's scope, terminating in the global scope.

```go
func ScopeOf(n *Node) Scope {
    c := n.Container()
    if c == nil {
        return GlobalScope
    }
    locals := c.LocalSymbols()
    if !locals.Any() {
        return ScopeOf(c) // skip empty layers to keep the chain short
    }
    return chainedScope{locals: locals, parent: ScopeOf(c)}
}
```

Because lookups flow through the lazy sequence operators, an outer scope is traversed only if the inner ones miss — you pay for exactly the resolution depth a lookup needs. Merging symbols across documents follows the same laziness: wrap the per-document containers in an immutable view that `FlatMap`s over them on iteration, so the merge is O(1) to build and allocates nothing until read.

## References: typed wrapper, untyped interface

A cross-reference wants two audiences. Language-specific code wants compile-time safety — a reference to a `FunctionDecl` resolving to `*FunctionDecl`. Framework code iterating over *all* references wants to treat them uniformly without knowing the target type. Serve both from one value: a generic wrapper for the typed consumer that satisfies a non-generic interface for the framework.

```go
type Reference[T Node] struct { /* target text, resolution state */ }

func (r *Reference[T]) Resolve(ctx context.Context) (T, error) { /* ... */ }

type UntypedReference interface {
    Text() string
    ResolveUntyped(ctx context.Context) (Node, error)
}

var _ UntypedReference = (*Reference[Node])(nil)
```

One implementation, no duplication, no `any`-casting at call sites. The compile-time check keeps the two faces from drifting apart.

## Once-only resolution with context-keyed cycle detection

Reference resolution should be lazy, memoized (resolved at most once, even under concurrent access), and cycle-safe (mutually recursive declarations must not loop forever). The elegant part is cycle detection: key the `context` by the reference *itself*, so a cyclic chain is caught using the call graph — no separate visited set, no shared mutable state.

```go
func (r *Reference[T]) Resolve(ctx context.Context) (T, error) {
    if r.done.Load() { // atomic fast path
        return r.target, r.err
    }
    return r.resolveSlow(ctx)
}

func (r *Reference[T]) resolveSlow(ctx context.Context) (T, error) {
    r.mu.Lock()
    defer r.mu.Unlock()
    if r.done.Load() { // double-check under the lock
        return r.target, r.err
    }
    if ctx.Value(r) != nil { // r is already resolving further up the stack
        var zero T
        return zero, errCyclicReference
    }
    ctx = context.WithValue(ctx, r, true)
    r.target, r.err = r.compute(ctx) // may recursively resolve other references
    r.done.Store(true)
    return r.target, r.err
}
```

This is a legitimate use of a context value — request-scoped, flowing down the call stack, never stored on a struct — exactly the distinction the concurrency reference draws.

## The build pipeline: phased, parallel within a phase

Analyzing a multi-file project has ordering constraints: you can't link references until every document has exported its symbols, nor validate until linking is done. Model this as *ordered phases* with a barrier between them, fanning out one goroutine per document *within* each phase. Check `ctx.Err()` between phases so a superseding edit cancels the build promptly.

```go
func Build(ctx context.Context, docs []*Document) error {
    phases := []func(context.Context, *Document){
        parseAndExport, // phase 1: per-doc; publishes exported symbols
        resolveAndLink, // phase 2: reads other docs' exported symbols
        validate,       // phase 3: reads the fully linked model
    }
    for _, phase := range phases {
        if err := ctx.Err(); err != nil {
            return err
        }
        var wg sync.WaitGroup
        for _, d := range docs {
            wg.Go(func() { phase(ctx, d) }) // sync.WaitGroup.Go, Go 1.25
        }
        wg.Wait() // barrier before the next phase
    }
    return nil
}
```

The barrier is the point: phase 2 reads data phase 1 produced *for other documents*, so it can't start until phase 1 finishes for *every* document. Within a phase there are no cross-document reads, so documents parallelize cleanly.

## Incremental state: a progressive aggregate and a phase bitmask

The `Document` is one struct whose fields fill in as phases run, not a fresh value per phase; each field's doc comment says which phase populates it. Track progress with a bitmask, and — the reusable trick — let `IsComplete` check only the framework-defined bits, leaving the high bits for adopters to define their own phases without the framework mistaking an incomplete document for a complete one.

```go
type Document struct {
    AST     *Node        // set by phase 1 (Parsed); nil before
    Symbols SymbolTable  // set by phase 2 (Linked); empty before
    Diags   []Diagnostic // set by phase 3 (Validated); nil before
    state   State
}

type State uint32

const (
    Parsed State = 1 << iota
    Linked
    Validated

    frameworkComplete = Parsed | Linked | Validated // low bits only
)

func (s State) Has(bits State) bool { return s&bits == bits }
func (s State) IsComplete() bool     { return s.Has(frameworkComplete) }
```

This enables fine-grained incremental rebuilds: on an edit, clear only the fields whose phase must rerun, so a change to one function body needn't re-export symbols for the whole project.

## Staying responsive: the write-to-read lock downgrade

A language server must stay responsive while it rebuilds. An edit rebuilds under an exclusive lock, but read requests — hover, go-to-definition, completion — shouldn't wait for the slow tail (validation) to run against the already parsed-and-linked model. Three decisions make this work:

- **Downgrade the write lock to a read lock atomically**, with no window for another writer to slip in. Reads unblock and observe exactly the state the writer produced, while validation continues under the shared lock.
- **Cancel superseded work, but let the cancelled unit finish its mutations.** A newer edit cancels an in-flight build via context, but the build only skips *expensive optional* work on `ctx.Err()` — dropping a mutation would desync the model from the text.
- **Schedule write-priority**, so the freshest edit always wins and readers never starve the writer.

This is involved, and worth it only on the interactive request path. A batch tool (linter, compiler) has no concurrent readers and should just lock, build, release.

## Keep the domain free of the protocol

An LSP-backed toolkit is tempting to build directly on the protocol types (`lsp.Diagnostic`, `lsp.Position`). Resist it: if the core imports the transport's vocabulary, the domain can't be reused off the protocol (a CLI, a batch validator, a test) and is welded to one wire format. Mirror the protocol type in the core *without importing the protocol package*, and put a thin bridge at the edge.

```go
// Core package: mirrors lsp.Diagnostic but imports nothing from the protocol.
type Diagnostic struct {
    Range    Range
    Severity Severity
    Message  string
}

// LSP layer only:
func (d Diagnostic) toLSP() lsp.Diagnostic {
    return lsp.Diagnostic{
        Range:    d.Range.toLSP(),
        Severity: lsp.DiagnosticSeverity(d.Severity),
        Message:  d.Message,
    }
}
```

The protocol layer adapts to the domain, not the other way around — SKILL.md's "define at the boundary" idea applied to a whole dependency.

## Performance discipline and hot-path data structures

Toolkits have real hot paths — lexing every byte, classifying every token, walking the tree, resolving references. Three habits keep them fit for purpose.

**Annotate non-obvious optimizations with the alternative they beat and the measured factor.** An unexplained micro-optimization is indistinguishable from a mistake, and the next reader will "clean it up".

```go
// atomic.Pointer, not sync.Once: measured ~2x faster here, since the resolved
// case is a single atomic load with no Once bookkeeping.
if cached := n.str.Load(); cached != nil {
    return *cached
}
```

**Reach for a standard `comparable` map first; drop to a hashed bucket map only when keys genuinely aren't comparable** — e.g. structurally-equal types that are distinct pointers. A separate-chaining `map[uint64][]entry` keyed by a user-supplied `Hash() uint64` / `Equals(T) bool` unlocks map behavior for such keys.

**On the parser hot path, make membership a bit test, not a scan.** Back token-type and token-group membership with a bitset — a group's set is the union of its members' — so "is this token in this group?" (and FIRST-set checks for error recovery) become word-wise bit tests.
