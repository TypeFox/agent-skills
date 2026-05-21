# Testable examples

Go's `testing` package lets you write **example functions** that are compiled (and optionally run) by `go test` and rendered on pkg.go.dev as usage examples. They are the most reliable form of API documentation because they cannot drift away from the code — renaming a function or changing its signature breaks the example at the next test run, surfacing the doc-rot before it reaches users.

Specification: https://pkg.go.dev/testing#hdr-Examples

## Table of contents

- [When to add an example](#when-to-add-an-example)
- [File placement](#file-placement)
- [Naming](#naming)
- [Multiple examples per symbol](#multiple-examples-per-symbol)
- [Output verification](#output-verification)
- [Whole-file examples](#whole-file-examples)
- [Common mistakes](#common-mistakes)

## When to add an example

Add an example whenever the API has a non-trivial usage pattern that prose alone won't communicate clearly — typical cases:

- A type that requires a setup sequence (`New`, configure, then use).
- A function whose return value must be consumed in a particular way (`defer resp.Body.Close()`).
- A package whose primary entry point is one of several functions, and the example shows the "happy path".
- Any signature that takes a callback or option struct where the call site is more revealing than the type signature.

Skip examples for trivial getters, accessors, or functions whose name and signature already say everything (`func Len() int`).

## File placement

Examples live in test files (filename ending in `_test.go`), in the same directory as the package being documented. Two choices for the package clause:

```go
package mypkg          // internal test package — can access unexported identifiers
package mypkg_test     // external test package — same import path as a user
```

Prefer `mypkg_test` for examples. Forcing the example to import the package the way a user would catches mistakes like relying on unexported helpers, and the rendered example on pkg.go.dev includes the `import "mypkg"` line that real users will need to write.

`go test` compiles `_test.go` files when running tests for the package, so a misnamed identifier in an example fails the test run — that's the safety net that keeps examples from rotting.

## Naming

The example's function name selects which symbol it attaches to in the rendered documentation:

| Function name        | Attached to                                  |
| -------------------- | -------------------------------------------- |
| `Example`            | The package as a whole                       |
| `ExampleF`           | Top-level function `F`                       |
| `ExampleT`           | Type `T`                                     |
| `ExampleT_M`         | Method `M` on type `T`                       |

Use the exact identifier capitalization. `ExampleHttpClient` does **not** attach to `HTTPClient`.

## Multiple examples per symbol

To attach more than one example to the same symbol, append `_suffix` to the function name. The suffix has one strict rule: **it must begin with a lower-case letter.** `ExampleClient_basic` works; `ExampleClient_Basic` does not — the parser reads `Basic` as if it were a type or method named `Basic` on `Client`, which doesn't exist, and the example silently misattaches.

```go
func Example_basic()         { ... }   // package-level, "basic" variant
func ExampleClient_pooled()  { ... }   // Client type, "pooled" variant
func ExampleClient_Do_retry(){ ... }   // Client.Do method, "retry" variant
```

pkg.go.dev renders the suffix as a label next to the example (capitalized for display: "Basic", "Pooled", "Retry"). Use the suffix to describe the variant — `_retry`, `_streaming`, `_withTimeout` — not to number them sequentially. Numbered variants (`_1`, `_2`) read as bug reports rather than documentation.

## Output verification

An example can declare expected output with a trailing comment. `go test` captures the example's stdout, trims leading/trailing whitespace from both sides, and compares.

### `// Output:`

Exact match (line-ordered):

```go
func ExampleHello() {
    fmt.Println("hello")
    // Output: hello
}

func ExampleSalutations() {
    fmt.Println("hello, and")
    fmt.Println("goodbye")
    // Output:
    // hello, and
    // goodbye
}
```

The `// Output:` comment must be the final block in the function body. If it doesn't match, the test fails with a diff.

### `// Unordered output:`

For examples where the output order is non-deterministic (e.g., map iteration, goroutines):

```go
func ExamplePerm() {
    for _, value := range Perm(5) {
        fmt.Println(value)
    }
    // Unordered output:
    // 4
    // 2
    // 1
    // 3
    // 0
}
```

The comparison ignores line order but still requires every expected line to appear exactly once.

### No output comment

> Example functions without output comments are compiled but not executed.

This is the right choice when:

- The example uses external resources (network, filesystem) that aren't appropriate for `go test`.
- The example's purpose is to demonstrate the API shape, and asserting the output would just be busywork.
- The example is illustrative and doesn't actually run end-to-end (e.g., it shows what a configuration call site looks like).

Don't add a misleading `// Output:` with fabricated values to "look complete" — `go test` will fail the moment someone runs it.

## Whole-file examples

A `_test.go` file is rendered as a single self-contained example block on pkg.go.dev when it contains:

1. Exactly one `Example` function, and
2. At least one other top-level declaration (function, type, var, or const), and
3. No `Test*` or `Benchmark*` functions.

This is useful when the example needs supporting types or helpers that would clutter the example body — they get rendered alongside the function, as a single coherent listing:

```go
// example_server_test.go
package http_test

import (
    "fmt"
    "log"
    "net/http"
)

type countHandler struct {
    n int
}

func (h *countHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    h.n++
    fmt.Fprintf(w, "count is %d\n", h.n)
}

func ExampleHandler() {
    http.Handle("/count", &countHandler{})
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

If any of the three conditions is violated (e.g., you add a second `Example` function or any `Test*` function), pkg.go.dev falls back to rendering only the `Example` function body without the supporting declarations — usually not what you want. Either keep the file pure or split helpers into a separate file.

## Common mistakes

**`// Output:` not the last block.** Anything after the Output comment is ignored. If you add code after it expecting it to run, it won't.

**Wrong suffix casing.** `ExampleClient_Pooled` attaches to a non-existent `Pooled` method on `Client`, not to `Client` with a "Pooled" label. Suffixes start lower-case.

**Forgetting the package suffix in external tests.** A file in `package mypkg_test` can't see unexported names. If an example relied on an unexported helper, switching from `package mypkg` to `package mypkg_test` will break it.

**Examples calling `os.Exit` or `log.Fatal`.** Either makes the test process exit, which fails the test run for the entire package. Use `fmt.Println` for visible output and let errors propagate as normal Go values.

**Tabs vs spaces in expected output.** `go test` trims leading/trailing whitespace on each side of the comparison, but indentation inside the expected output is matched as written. Inconsistent tabs/spaces in the `// Output:` lines fail the assertion. Let `gofmt` normalize them.

**Examples that depend on map ordering.** Maps iterate in undefined order. Use `// Unordered output:` or sort the keys before printing.

**Examples that import the package as `.`** (dot import). The rendered example loses the `import "mypkg"` line, which is the most useful part of the rendering. Use a normal import.
