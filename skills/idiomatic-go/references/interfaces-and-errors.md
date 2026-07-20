# Interfaces and errors reference

Patterns LLMs get subtly wrong: where interfaces live, how to model errors, when to wrap and when not to, and when (if ever) to panic. SKILL.md states the rules; this file gives the worked examples and edge cases.

Contents:

- [Where interfaces live: a worked example](#where-interfaces-live-a-worked-example)
- [Compile-time interface satisfaction](#compile-time-interface-satisfaction)
- [Embedding interfaces and structs](#embedding-interfaces-and-structs)
- [Type assertions and type switches](#type-assertions-and-type-switches)
- [Sentinel errors vs custom types vs ad-hoc](#sentinel-errors-vs-custom-types-vs-ad-hoc)
- [Wrapping: when and when not to](#wrapping-when-and-when-not-to)
- [`errors.Is`, `errors.As`, `errors.Join`](#errorsis-errorsas-errorsjoin)
- [Structured errors with fields](#structured-errors-with-fields)
- [Panic and recover: the narrow use case](#panic-and-recover-the-narrow-use-case)

## Where interfaces live: a worked example

The producer exports a concrete type. The consumer declares the interface it needs.

```go
// Producer package — exports concrete type.
package httpfetch

type Client struct {
    httpClient *http.Client
    baseURL    string
}

func NewClient(baseURL string) *Client {
    return &Client{httpClient: http.DefaultClient, baseURL: baseURL}
}

func (c *Client) Fetch(ctx context.Context, id string) (*Doc, error) {
    // ... real implementation
}
```

```go
// Consumer package — declares only what it needs.
package orderprocessor

type DocFetcher interface {
    Fetch(ctx context.Context, id string) (*Doc, error)
}

type Service struct {
    docs DocFetcher
}

func NewService(docs DocFetcher) *Service {
    return &Service{docs: docs}
}

func (s *Service) ProcessOrder(ctx context.Context, orderID string) error {
    doc, err := s.docs.Fetch(ctx, orderID)
    // ...
}
```

Three things this gets right:

1. `httpfetch.NewClient` returns `*Client`, not `DocFetcher`. The consumer sees every method `Client` exports and can use the parts it needs.
2. `orderprocessor.DocFetcher` lives next to the code that calls `Fetch`. The producer is unaware of it and can grow new methods on `Client` without breaking the consumer.
3. Tests in `orderprocessor` mock `DocFetcher` directly. They never need to know about `httpfetch`.

A common anti-pattern: defining `httpfetch.DocFetcher` *and* `httpfetch.Client` *and* having `NewClient` return the interface. The first interface is speculative; the third decision blocks the producer from exposing a new method without an `errors.As`-style cast at every call site.

## Compile-time interface satisfaction

When a type is meant to satisfy an interface but isn't *used* as one yet (or only via reflection), a single line gives the compiler a chance to catch a missing or wrong-signature method:

```go
var _ io.Reader = (*MyReader)(nil)
```

The variable is `_`, so it allocates nothing. The cast `(*MyReader)(nil)` is a nil typed pointer with the right type. If `*MyReader` doesn't satisfy `io.Reader`, this line fails to compile — a clear error at the type's home, not at some distant call site.

Use this when:

- The type implements an interface defined elsewhere and you want to fail loudly if the contract drifts.
- You add a method to an interface; the line in every implementer fails to compile until updated.

## Embedding interfaces and structs

Embedding adds the methods of the embedded type to the outer type. It is not inheritance — there is no override, no `super` call, no shared identity.

```go
// Interface embedding: union of method sets.
type ReadWriter interface {
    io.Reader
    io.Writer
}

// Struct embedding: methods promote to the outer type.
type Server struct {
    *log.Logger        // *Server gets Printf, Println, etc.
    addr string
}

s := &Server{Logger: log.New(os.Stderr, "srv: ", log.LstdFlags), addr: ":8080"}
s.Printf("listening on %s", s.addr)  // forwards to the embedded *log.Logger
```

When the outer type and the embedded type both have a method `X`, the outer type's `X` wins. The embedded type's `X` is still accessible as `s.Logger.X(...)`.

**Embedding is wrong when** you want to *restrict* the embedded type's surface area — embedding promotes all exported methods, including ones you'd rather not expose. In that case, hold the embedded type as a named field and forward only what you want.

## Type assertions and type switches

The comma-ok form is the safe one:

```go
if rc, ok := r.(io.ReadCloser); ok {
    defer rc.Close()
}
```

A bare assertion `r.(io.ReadCloser)` panics if `r` doesn't satisfy the interface. Reserve it for cases where the dynamic type is a documented invariant of the caller.

The type switch handles multiple possibilities:

```go
switch v := value.(type) {
case nil:
    return ErrNil
case string:
    return parseString(v)
case int, int64:
    return parseInt(v)  // v is interface{} here, because the case has multiple types
case error:
    return v
default:
    return fmt.Errorf("unexpected type %T", v)
}
```

Inside a single-type case, `v` has that type. Inside a multi-type case, `v` has the original interface type — the cases share a body but not a specific type.

## Sentinel errors vs custom types vs ad-hoc

Three ways to construct an error; each is right in different places.

**Sentinel errors** — a package-level `var Err... = errors.New("...")` that callers compare via `errors.Is`:

```go
package fs

var ErrNotFound = errors.New("not found")
var ErrPermission = errors.New("permission denied")
```

Use sentinels when callers need to branch on *which* failure occurred and the failure carries no useful payload. Sentinels become part of the package's public contract — renaming or removing one is a breaking change.

**Custom error types** — a struct that carries fields:

```go
type PathError struct {
    Op   string
    Path string
    Err  error
}

func (e *PathError) Error() string {
    return e.Op + " " + e.Path + ": " + e.Err.Error()
}

func (e *PathError) Unwrap() error { return e.Err }
```

Use custom types when callers need to inspect the failure's details (the path, the operation, the underlying error). The receiver is conventionally a pointer so `errors.As` can match. Implement `Unwrap` if the type wraps another error.

**Ad-hoc errors via `fmt.Errorf`** — the default. Use when callers will only display the message and don't need to branch:

```go
return fmt.Errorf("parse %s line %d: %w", path, lineNum, err)
```

## Wrapping: when and when not to

`%w` chains the inner error into the outer one so `errors.Is` and `errors.As` traverse the chain. Use it whenever the inner error is part of the API contract — the caller may legitimately want to check it.

Do **not** wrap when:

- The inner error is an implementation detail the caller should not depend on. Wrapping leaks that detail into the public contract; a future change to the implementation now breaks callers that grew an `errors.Is(err, internal.ErrFoo)` check.
- You want to fully replace the error with a new one (use `%v` or construct a new error directly).

A useful rule: wrap when the inner error came from a public API of another package or from your own caller; replace when the inner error came from an internal helper whose existence is incidental.

**Wrapping and branching are independent decisions — do both when the caller needs to.** Returning `fmt.Errorf("...: %w", err)` preserves the chain for *some* future caller to inspect; it does not make the current function itself react to the failure. When your immediate caller needs one failure treated differently from the rest, check it with `errors.Is`/`errors.As` before you return, then wrap for whatever caller is further up:

```go
// The service branches on the sentinel it cares about, then wraps for its own caller.
func (s *Service) Checkout(ctx context.Context, cartID string) error {
    cart, err := s.carts.Find(ctx, cartID)
    switch {
    case errors.Is(err, store.ErrNotFound):
        return fmt.Errorf("checkout: %w", ErrCartNotFound) // the service's own sentinel
    case err != nil:
        return fmt.Errorf("checkout: find cart %s: %w", cartID, err)
    }
    // ...
}
```

A wrap-only version compiles and looks identical to a caller who never checks — the gap only shows up when someone needs to branch and can't.

## `errors.Is`, `errors.As`, `errors.Join`

- `errors.Is(err, target)` — walks the chain looking for an error that equals `target`. Use for sentinel-error checks.
- `errors.As(err, &target)` — walks the chain looking for an error assignable to `*target`. Use for custom-type checks where you want the fields. `target` must be a non-nil pointer to the target type.
- `errors.Join(errs ...error)` — combines multiple errors into one. The result satisfies `errors.Is` and `errors.As` for each input. Use when an operation can fail in several independent ways (e.g., validating multiple fields).

```go
var pe *PathError
if errors.As(err, &pe) {
    log.Printf("op=%s path=%s", pe.Op, pe.Path)
}

if errors.Is(err, fs.ErrNotFound) {
    return nil  // not-found is fine here
}
```

## Structured errors with fields

When a custom error type carries fields, the `Error()` method composes them in a stable form so wrapping reads naturally:

```go
type ValidationError struct {
    Field  string
    Reason string
}

func (e *ValidationError) Error() string {
    return e.Field + ": " + e.Reason
}

// At a call site:
return fmt.Errorf("validate user: %w", &ValidationError{Field: "email", Reason: "invalid format"})
// Renders: "validate user: email: invalid format"
```

The lowercase-and-no-trailing-punctuation rule applies here too — `e.Reason` should be lowercase so the composed message reads cleanly.

## Panic and recover: the narrow use case

Panic is for impossible invariants — the kind of condition that means your program has a bug, not that the input was bad. Even then, prefer returning an error and letting the caller decide.

The narrow legitimate use of `panic` and `recover` is *intra-package* cross-function escape: a deep parser hits an unrecoverable input, panics with a typed value, and a top-level function recovers and converts it to a returned error. `encoding/json` does this; so do parts of `html/template`. The panic never escapes the package's API boundary.

```go
type parseError struct{ msg string }

func parse(input string) (out Output, err error) {
    defer func() {
        if r := recover(); r != nil {
            if pe, ok := r.(*parseError); ok {
                err = errors.New(pe.msg)
                return
            }
            panic(r)  // not ours — re-raise
        }
    }()
    // ... deeply recursive code that calls panic(&parseError{...}) on bad input
}
```

Two rules even for this case:

- Recover only inside a deferred function; nowhere else does it do anything.
- Re-panic anything you don't recognize. Swallowing all panics turns real bugs into silent corruption.
