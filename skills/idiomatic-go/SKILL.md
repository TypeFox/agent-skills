---
name: idiomatic-go
description: Apply Go community idioms for API and package design, error and concurrency patterns, naming (initialisms, stutter, receivers), generics vs interfaces, and Go code review — including PR or diff review and questions about "the Go way", pointer vs value receivers, or channels vs mutexes, even when the user doesn't say "idiomatic." Skip trivial one-line Go edits with no design choices. Do not use for godoc or doc comments — use the `go-documentation` skill.
---

# Idiomatic Go

The conventions here come from [Effective Go](https://go.dev/doc/effective_go) and [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) — the documents that codify what Go reviewers reject pull requests over. The content is filtered to the rules that strong models still slip on, so basic syntax, `gofmt` usage, and well-known mechanics (LIFO `defer`, `new` vs `make`, channel basics) are not repeated here.

The guiding principle is **clear is better than clever** (Rob Pike's phrasing, elaborated in [Dave Cheney's article of the same name](https://dave.cheney.net/2019/07/09/clear-is-better-than-clever)). When choosing between a concise/clever construction and an explicit/plain one, pick the explicit one. Code is decoded, not skimmed, and it outlives the person who wrote it. For godoc and doc-comment conventions, use the sibling `go-documentation` skill — this one stays focused on code style.

APIs that require **Go 1.22 or later** are called out inline below. Older stable symbols (`errors.Is`, `fmt.Errorf` with `%w`, `slices.Clone`, and similar) are not annotated.

## Reference files

Load these as needed — don't read them upfront. This file has the rules and decision points; the references hold the long tail.

- `references/naming.md` — the full initialism table with the awkward cases (`OAuth`, `IPv4`, `gRPC`, `IDs`, `HTTPSProxy`), worked naming examples, deeper package-naming guidance (why `util`/`common`/`misc` collect garbage and how to split them), import grouping, and file naming with build constraints. Read this when naming anything exported or organizing a new package.
- `references/interfaces-and-errors.md` — interface placement worked end-to-end, embedding, compile-time satisfaction checks; sentinel errors vs custom error types vs `fmt.Errorf`; the `errors.Is`/`As`/`Join` model and when *not* to wrap; structured errors; `panic`/`recover` discipline. Read this when designing an API, writing a non-trivial error type, or wrapping errors across abstraction boundaries.
- `references/concurrency-patterns.md` — the `context.Context` contract end-to-end, the four ways a goroutine exits, the `for select` skeleton, channel-direction signatures, semaphore and leaky-buffer patterns, `sync.Once`/`WaitGroup`/`errgroup` decisions, channel-closing rules, and the anti-patterns (sleeping in tests, polling, fire-and-forget goroutines). Read this when starting a goroutine, designing a cancellable operation, or reviewing concurrent code.

## Naming

Naming is where Go diverges most visibly from other languages and where models slip most often.

**Initialisms keep one case throughout.** `URL`, `ID`, `HTTP`, `XML`, `JSON`, `API`, `IO`, `DB`, `URI` — either all uppercase or all lowercase, never mixed. So `userID` not `userId`, `ServeHTTP` not `ServeHttp`, `parseJSON` not `parseJson`, `xmlHTTPRequest` not `xmlHttpRequest`. The rule applies even when the initialism appears in the middle of a name. The reference has the edge cases.

**MixedCaps, not snake_case.** Both exported (`MaxRetries`) and unexported (`maxRetries`) names use mixed caps. Unexported constants are *not* `MAX_RETRIES`, even if other languages would write them that way.

**Package names: short, lowercase, no underscores.** The package name prefixes every call site (`http.Get`, `json.Marshal`), so it must read well in context. Avoid `util`, `common`, `helpers`, `misc`, `base`, `shared` — they collect unrelated code and never repay the loan. If a function doesn't fit anywhere, find a more specific home or start a narrower package.

**Avoid stutter.** Package `chubby` exports `File`, not `ChubbyFile`. Callers write `chubby.File` and the package prefix supplies the namespacing. Same for functions: `bytes.NewBuffer`, not `bytes.NewBytesBuffer`.

**Variable name length scales with scope.** Use `i` for a tight loop index, `r` for a `Reader` in a five-line function, `customerID` for a field on an exported struct, `defaultTimeout` for a package-level constant. The further from declaration a name is used, the more descriptive it must be.

**Receiver names are short and consistent.** One or two letters that reflect the type — `c` for `Client`, `b` for `Buffer`, `srv` for `Server`. Use the same name across every method on a type. Never `self`, `this`, `me` — receivers are just parameters in Go.

**No `Get` prefix on getters.** `owner.Name()` not `owner.GetName()`. Setters keep their `Set` prefix to mark the asymmetry: `owner.SetName(n)`.

**Single-method interfaces end in `-er`.** `Reader`, `Writer`, `Stringer`, `Closer`, `Formatter`. Multi-method interfaces don't force the suffix.

## Interfaces

**Define interfaces in the consumer package, not the producer's.** The package that *needs* a `Fetcher` declares the shape it requires. The package that *implements* fetching exports a concrete `*Client` and lets consumers wrap it in whatever interface they need. This keeps the producer free to add methods without breaking consumers, and avoids a forest of speculative interfaces in the implementer.

**Accept interfaces, return concrete types.** Function parameters use interfaces to describe the minimum needed; return values are concrete so callers see every method and the package can add fields without breaking callers.

```go
// Good: minimal interface input, concrete return.
func NewServer(log Logger) *Server

// Bad: hides fields, blocks future methods, forces type assertions.
func NewServer(log Logger) HTTPHandler
```

**Don't pre-create interfaces "for mocking".** Mocks belong in the consumer's test package, against the consumer's interface. A speculative interface in the producer is dead weight and a future API hazard.

**Small interfaces compose better.** Prefer `io.Reader` to a six-method `Source`. If you need read+write, embed: `io.ReadWriter` is just `io.Reader` plus `io.Writer`.

See `references/interfaces-and-errors.md` for type-assertion forms, embedding, and the compile-time satisfaction check `var _ io.Reader = (*MyReader)(nil)`.

## Generics

**Write functions first; add type parameters when you would duplicate the same logic for different types.** Starting with constraint interfaces is usually the wrong path ([When To Use Generics](https://go.dev/blog/when-generics)).

**Prefer interfaces over type parameters** when callers only need methods (`io.Reader`, `io.Writer`). Do not rewrite `func Read(r io.Reader)` into `func Read[T io.Reader](r T)` — harder to read, rarely faster.

**Prefer the standard library** (`slices`, `maps`, `cmp`) over custom generic utilities; use `cmp.Ordered`, not `golang.org/x/exp/constraints`.

**Use type parameters** for language containers (slice/map/channel ops with no element-specific logic) and shared data structures — not when each type needs a different method body (use interfaces and separate implementations).

**Preserve named slice types:** constrain slice args as `S ~[]E` and return `S`, not `[]E`, when callers may pass a defined slice type ([An Introduction To Generics](https://go.dev/blog/intro-generics) Scale example).

**Map keys need `comparable`** in the type parameter list when a generic type uses `map[K]V`.

**Go 1.27 — generic methods:** From Go 1.27, a method may declare type parameters (`func (t *T) M[P any](...)`). Use them for helpers that naturally live on the receiver type instead of polluting the package with `func helper[T, P any](t *T, ...)`. A generic method **does not** implement a non-generic interface method: `func (*R) Read[E any]([]E)` does not satisfy `io.Reader`. For interface satisfaction, keep ordinary methods or package-level generic functions.

## Errors

**Return errors as values.** Never use in-band sentinels like `-1`, `""`, or `nil` to signal failure when the real return type can take those values legitimately. An explicit `(T, error)` return makes the failure case unmissable.

**Error strings are lowercase, no trailing punctuation.** Errors get wrapped and chained: `failed to open config: open /etc/app.conf: permission denied` only reads right if every link in the chain starts lowercase and ends with no period.

```go
// Good.
return fmt.Errorf("open %s: %w", path, err)

// Bad. Capitalized, ends with period — breaks when wrapped.
return fmt.Errorf("Failed to open %s: %v.", path, err)
```

**Wrap with `%w` once** so `errors.Is` and `errors.As` work. Use `%v` only when you intentionally want to flatten — i.e., the inner error is an implementation detail not part of your contract.

**Don't `_ = err`.** If you genuinely cannot act on an error, leave a comment explaining why. Silent discard is the default failure mode for `os.Setenv`, `f.Close()` on a read-only file, and similar cases.

**Indent the error branch, not the happy path.** Early return on failure; let success flow down the page.

**Don't panic in libraries.** Panic is for unrecoverable invariants, and even then prefer returning an error. `recover` only works inside a deferred function. See `references/interfaces-and-errors.md` for the rare cases where intra-package panic-as-cross-function-return is idiomatic.

## Concurrency

**"Don't communicate by sharing memory; share memory by communicating."** This is a guiding principle, not a rule. Channels model *ownership transfer* — a value passes from one goroutine's responsibility to another's. Mutexes model *guarded state* — many goroutines need to read or write the same data with a single owner. Both are idiomatic; pick by what the data represents.

**Every goroutine needs a documented exit path.** A goroutine without a planned termination is a leak waiting to happen. Four standard exits: (1) the work is finite and the function returns, (2) `<-ctx.Done()`, (3) an explicit close-channel signal, (4) a `sync.WaitGroup` the parent joins on. If you cannot say which one applies, do not start the goroutine.

**`context.Context` is the first parameter** of any function that does I/O, may block, or starts goroutines. Never store a `Context` in a struct — its lifetime is the call, not the object's. The parameter name is conventionally `ctx`.

```go
// Good.
func (c *Client) Fetch(ctx context.Context, id string) (*Doc, error)

// Bad. Context in struct; lifetime is now ambiguous.
type Client struct { ctx context.Context; /* ... */ }
```

**Prefer synchronous APIs.** A function that returns `(Result, error)` is composable, testable, and trivially wrappable in a goroutine by anyone who wants concurrency. A function that returns `<-chan Result` decides for the caller, leaks if the caller forgets to drain it, and complicates error reporting. Write the synchronous version first; let the caller add the goroutine.

**Unbuffered channels are synchronization; buffered channels are throughput tolerance.** `make(chan T)` blocks the sender until the receiver receives — that *is* the synchronization. `make(chan T, N)` lets the sender get ahead by N values; it doesn't "make things faster", it changes semantics. Pick the capacity by what the data flow requires, not by tuning.

See `references/concurrency-patterns.md` for the `for select { case <-ctx.Done(): ... }` skeleton, channel-direction signatures, and decision trees for mutex vs channel and `sync.Once` vs `sync.WaitGroup` vs `errgroup`.

## Receiver type: value or pointer

**Be consistent within a type.** If any method of `T` takes a pointer receiver, every method should. Mixing forces the reader to remember which is which and produces surprising method-set behavior at interface boundaries.

Use **pointer receivers** when:

- The method mutates the receiver.
- The struct contains a `sync.Mutex` or another field that must not be copied.
- The struct is large enough that copying matters.
- You want `nil` to be a meaningful receiver value.

Use **value receivers** when:

- The type is a small fixed-size value: `time.Time`, a 2-int struct, a primitive alias.
- The type is already a reference (`map`, `slice`, `chan`, `func`) — those are pointer-shaped headers; wrapping them in another pointer adds indirection without benefit.

When in doubt, use a pointer receiver. The cost is one indirection; the cost of inconsistency is bugs.

## Pass values; avoid pointer-itis

Don't reflexively reach for `*int`, `*string`, `*bool` to "save a copy" or to model optionality. Pointer-to-primitive forces nil-checks at every call site, hides intent, and costs more than the value would have.

For optional configuration, use a zero-value-friendly struct, a functional `Option` pattern, or distinct method names. For truly optional outputs, return `(value, ok)` or `(value, error)`.

## Zero-value design

**Design types so the zero value is usable.** `bytes.Buffer{}`, `sync.Mutex{}`, `http.Client{}` all work straight from `var x T` with no construction step. When the zero value works, **skip the constructor** — `NewFoo()` returning `&Foo{}` with no setup adds a name to maintain without value.

**Nil slices are usable.** `var s []T` is an append-able, range-able nil slice. Prefer it over `s := []T{}` *unless* you need to distinguish "empty but present" from "absent" — the JSON `[]` vs `null` distinction is the canonical case where the explicit empty literal matters.

**Maps must be made before writing.** The zero value of a map is read-only; `var m map[string]int; m["x"] = 1` panics. Either initialize at declaration (`m := map[string]int{}`) or `make` before first write.

## Data gotchas

**Slices share backing arrays — until they don't.** A slice is a header over an array; two slices into the same array see each other's writes. Then `append` exceeds capacity and reallocates, and the two slices silently diverge. When passing slices across an API boundary, document whether you retain or copy, and `slices.Clone` when in doubt.

**Composite literals: use field-name form.** `&File{fd: fd, name: name}` is robust to field reordering; `&File{fd, name, nil, 0}` breaks the day someone adds a field.

**Nil maps panic on write.** See zero-value design above.

## Control flow and structure

**Line-of-sight coding.** The happy path stays at the leftmost indent so the function reads top-to-bottom as a straight line. Conditional bodies hold only cleanup, return, or error handling — never the main logic. Mat Ryer's term, popularized by Dave Cheney; it is the most useful single framing for Go control flow.

```go
// Good: happy path on the left margin.
f, err := os.Open(path)
if err != nil {
    return err
}
defer f.Close()
// ... use f
```

**`switch` with no condition is the idiomatic `if`/`else if` ladder.** It makes the selection explicit and forces every branch to terminate.

```go
switch {
case n < 0:
    return ErrNegative
case n == 0:
    return nil
default:
    return process(n)
}
```

**Avoid `fallthrough`.** Go's no-fall-through default is the feature; opting back into the C behavior re-introduces the bug class.

**Naked returns only in functions short enough to read at a glance.** In longer functions, explicit returns document what's being returned at every exit.

**Named result parameters when meaning would be unclear** (e.g., `func Split(path string) (dir, file string)`) or when needed by `defer` to set a result. Don't name results just to enable naked returns.

## Security: `crypto/rand` over `math/rand`

For tokens, IDs, keys, session identifiers, or anything an attacker could exploit by predicting: use `crypto/rand` (`Read`, `Int(rand.Reader, max *big.Int)`, and from Go 1.24 `Text`). `math/rand` and `math/rand/v2` (Go 1.22) are for simulation, jitter, sampling, and tests — not security. The default autocomplete is `math/rand`; flag it on every use that produces a value an attacker would care about.

## Quick checklist before committing

- [ ] Initialisms are single-cased: `URL`, `ID`, `HTTP`, `JSON` — `userID`, `ServeHTTP`, `parseJSON`.
- [ ] Package names are short, lowercase, single words; no `util`/`common`/`misc`.
- [ ] Receiver names are 1–2 letters, consistent across the type — never `self`/`this`/`me`.
- [ ] Interfaces are defined in the consumer; constructors return concrete types.
- [ ] Generics only where the same logic would otherwise be duplicated; interfaces kept for method-only APIs.
- [ ] Named slice types preserved (`S ~[]E`); `cmp`/`slices`/`maps` preferred over `x/exp/constraints`.
- [ ] Go 1.27+: generic methods not used where the type must implement a non-generic interface method.
- [ ] No `Get` prefix on getters.
- [ ] Error strings are lowercase, end with no punctuation, and wrap with `%w` when chained.
- [ ] No `_ = err` without an explaining comment.
- [ ] Every goroutine has a documented exit (finite work, `ctx.Done()`, close signal, or `WaitGroup`).
- [ ] `context.Context` is the first parameter where it appears; never stored in a struct.
- [ ] Receiver types are consistent within a type (all value or all pointer).
- [ ] No `*int`/`*string`/`*bool` parameters unless `nil` is genuinely distinct from the zero value.
- [ ] `crypto/rand` for anything security-sensitive; `math/rand` only for simulation/jitter.
- [ ] Happy path stays at the leftmost indent; error branches are early returns.
- [ ] `gofmt`/`goimports` clean.
