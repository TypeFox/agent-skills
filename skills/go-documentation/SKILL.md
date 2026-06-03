---
name: go-documentation
description: Write idiomatic Go doc comments that render correctly on pkg.go.dev. Use whenever the user is writing or reviewing Go documentation — package comments, `doc.go` files, exported symbol comments, testable `Example` functions, deprecation notices — or wants to publish a module to pkg.go.dev, preview docs locally with `pkgsite`, or debug a broken pkg.go.dev page. Do not use for general Go programming questions or non-Go languages.
---

# Go Documentation

Go treats documentation as part of the language toolchain, not an afterthought. `go doc` reads comments locally, [pkg.go.dev](https://pkg.go.dev) publishes them on the public index, and `gofmt` normalizes their formatting. The conventions in this skill come from the official spec at https://go.dev/doc/comment — they are not stylistic preferences. Tools depend on them.

Use this skill when:

- Adding or revising doc comments on exported names.
- Writing or improving a package-level overview.
- Preparing a Go module for publication on pkg.go.dev.
- Previewing rendered documentation locally before tagging a release.
- Diagnosing why pkg.go.dev shows the wrong summary, no documentation, or a stale version.

## Reference files

Load these as needed — don't read them upfront. The main SKILL.md has the conventions and decision points; the references hold operational detail.

- `references/comment-syntax.md` — the full markup grammar of doc comments: paragraphs, headings, links (reference-style and doc links), lists, code blocks, notes, deprecations, directives, plus the gofmt reformatting rules and the half-dozen common pitfalls that produce unintended code blocks or broken lists. Read this whenever a comment includes anything richer than plain prose, or when `gofmt` reformats a comment in a surprising way.
- `references/examples.md` — testable `Example` functions: naming rules (including the `_suffix` casing constraint), `// Output:` and `// Unordered output:` assertion comments, whole-file examples, and the rule that examples without an Output comment are compiled but not run. Read this when adding examples, or when an example test fails unexpectedly.
- `references/publishing.md` — how pkg.go.dev discovers and indexes modules via `proxy.golang.org`, the `go.mod` and redistributable-license requirements, semantic-versioning expectations, README rendering, source-code linking, retraction, and removal. Read this before publishing a new module, or when an existing module isn't showing up or is showing the wrong content.
- `references/pkgsite-preview.md` — installing and running `pkgsite` to preview the current module's docs in a browser before publication. Read this when iterating on doc comments locally.

## Core convention: every exported name gets a doc comment

A doc comment is a comment placed immediately before a top-level `package`, `const`, `func`, `type`, or `var` declaration, with **no blank line in between**. The blank line is what separates a doc comment from an unrelated comment above it — `go/doc` uses that rule to associate the comment with the declaration. Get that detail wrong and the documentation disappears from `go doc` and pkg.go.dev even though the comment is still in the source.

Every exported (capitalized) name should have one. Unexported names benefit from comments too, but the conventions below specifically target what shows up in published documentation.

## Naming the symbol in the first sentence

Every doc comment starts with a full sentence whose first word names the symbol being documented. This isn't decorative: `go doc`, IDE hover cards, and pkg.go.dev's search results all surface the first sentence as a one-line summary, often without the symbol name shown alongside. A reader scanning the function list of a package sees only that first sentence — if it doesn't name the function, they can't tell what they're looking at.

| Symbol kind            | First-sentence pattern                | Example                                                                       |
| ---------------------- | ------------------------------------- | ----------------------------------------------------------------------------- |
| Package                | `Package <name> ...`                  | `Package path implements utility routines for manipulating slash-separated paths.` |
| Command (`main`)       | `<Command> ...` (capitalized)         | `Gofmt formats Go programs.`                                                  |
| Type                   | `A <Type> ...` / `An <Type> ...`      | `A Reader serves content from a ZIP archive.`                                 |
| Function (returns)     | `<Function> returns ...`              | `Quote returns a double-quoted Go string literal representing s.`             |
| Function (side effect) | `<Function> <verb> ...`               | `Exit causes the current program to exit with the given status code.`        |
| Function (bool result) | `<Function> reports whether ...`      | `HasPrefix reports whether the string s begins with prefix.`                  |
| Constant / variable    | `<Name> is ...` / `<Name> <verb> ...` | `Version is the Unicode edition from which the tables are derived.`           |

The `reports whether` phrasing for booleans is idiomatic Go — prefer it over `returns true if`. It reads more naturally in the doc index and matches the standard library convention.

## Package documentation

Package documentation is the single most important comment in a module — it is what pkg.go.dev's search indexes, what shows on the package's landing page, and what answers "what is this library for?" for everyone who arrives without context. The detail that follows applies broadly; for a focused checklist on multi-file packages and commands, the rules below are sufficient on their own.

### Where to put it

The package comment sits directly above the `package` declaration. In a multi-file package, by convention place it in a dedicated `doc.go` file:

```go
// Package json implements encoding and decoding of JSON as defined in
// RFC 7159. The mapping between JSON and Go values is described
// in the documentation for the [Marshal] and [Unmarshal] functions.
//
// See "JSON and Go" at https://golang.org/doc/articles/json_and_go.html
// for an introduction to this package.
package json
```

The `doc.go` file usually contains only the package comment and the `package` declaration — no other code. Two reasons to prefer this layout over attaching the comment to a regular source file:

1. **Stability.** Source files get split, renamed, or deleted during refactors. A package comment attached to `client.go` quietly disappears the day someone renames `client.go` to `transport.go` and forgets to move the comment. `doc.go` is a stable home that future contributors recognize as "the file that holds package documentation."
2. **Discoverability.** Anyone opening the directory immediately sees that the package has dedicated documentation and where to edit it.

In a multi-file package, only one file should hold the package comment; if multiple files do, `go/doc` concatenates them in an unspecified order, which is almost never what you want.

### First sentence

The first sentence MUST begin with `Package <name>` (exact capitalization of the package name). pkg.go.dev indexes this sentence and shows it in search results. Write it as a self-contained one-liner — assume the reader sees nothing else.

Good: `Package errgroup provides synchronization, error propagation, and Context cancellation for groups of goroutines working on subtasks of a common task.`

Weak: `This package is a small library for working with goroutines.` — doesn't start with `Package errgroup`, doesn't say what it does specifically.

### Overview for larger packages

For packages with more than a handful of exported symbols, include a short overview after the first paragraph. Point readers at the most important types and functions using doc links (see `references/comment-syntax.md` § Doc links):

```go
// Package http provides HTTP client and server implementations.
//
// [Get], [Head], [Post], and [PostForm] make HTTP (or HTTPS) requests:
//
//  resp, err := http.Get("http://example.com/")
//  ...
//
// The client must close the response body when finished with it:
//
//  resp, err := http.Get("http://example.com/")
//  if err != nil {
//      // handle error
//  }
//  defer resp.Body.Close()
//
// For control over HTTP client headers, redirect policy, and other
// settings, create a [Client] ...
package http
```

The overview shows up at the top of the pkg.go.dev page, before the symbol index. Long packages with no overview render as a wall of symbols and force readers to guess where to start.

### Commands (`package main`)

For binary commands, the package comment describes the program rather than its Go API. The first sentence begins with the program name capitalized as a normal sentence start:

```go
// Gofmt formats Go programs.
// It uses tabs for indentation and blanks for alignment.
//
// Usage:
//
//  gofmt [flags] [path ...]
//
// The flags are:
//
//  -d
//      Do not print reformatted sources to standard output.
//      Instead, print diffs.
//  -l
//      List files whose formatting differs from gofmt's.
//  ...
package main
```

Use semantic linefeeds (one sentence per line) in command documentation. Gofmt preserves line breaks within paragraphs, so this produces cleaner diffs when text is edited and reads naturally when rendered.

## Function and method documentation

Pick the first-sentence pattern from the table above. Beyond that, include the details a caller would reasonably need:

- **Special cases and edge cases.** Document edge cases as an indented preformatted block, as in the standard library's `math.Sqrt`:

  ```go
  // Sqrt returns the square root of x.
  //
  // Special cases are:
  //
  //  Sqrt(+Inf) = +Inf
  //  Sqrt(±0) = ±0
  //  Sqrt(x < 0) = NaN
  //  Sqrt(NaN) = NaN
  func Sqrt(x float64) float64
  ```

- **Asymptotic complexity** when it matters to callers (e.g., `sort.Sort` documents its O(n log n) call count to `Less` and `Swap`).
- **Concurrency safety.** Top-level functions are conventionally assumed to be safe for concurrent use; state otherwise if not. For methods, the default assumption is the opposite — only safe for a single goroutine at a time. State exceptions in the method comment, or in the type's doc comment if it applies to all methods.
- **Deprecation.** A paragraph beginning `Deprecated:` triggers tools to warn callers and causes pkg.go.dev to hide the symbol by default. See `references/comment-syntax.md` § Deprecations.

Leave out internal implementation details. The doc comment describes behavior callers can rely on, not the algorithm currently used. Documenting "uses quicksort internally" locks the implementation behind the doc contract — a future maintainer who switches to timsort will silently break that contract.

Refer to named parameters and results directly by name in prose, without backticks: `Copy copies from src to dst until either EOF is reached on src or an error occurs. It returns the total number of bytes written and the first error encountered while copying, if any.` Avoid parameter names like `a` or `s` that could be confused with ordinary words.

## Type documentation

Start with `A <Type>` or `An <Type>` and describe what an instance represents. Then add whichever of these apply:

- **Zero value.** Go encourages designing types whose zero value is useful. When the zero value is meant to work — `var b Buffer` is a valid empty buffer — document it: `The zero value for Buffer is an empty buffer ready to use.` Readers can only count on the zero value working if you say so.
- **Concurrency safety.** The default assumption is "not safe for concurrent use". Anything stronger (`A Regexp is safe for concurrent use by multiple goroutines, except for configuration methods, such as Longest.`) must be explicit.
- **Field documentation.** For structs with exported fields, either the type's doc comment describes the fields collectively, or each exported field has its own per-field comment. Pick one approach per type — don't mix the two awkwardly.

```go
// A LimitedReader reads from R but limits the amount of
// data returned to just N bytes. Each call to Read
// updates N to reflect the new amount remaining.
// Read returns EOF when N <= 0.
type LimitedReader struct {
    R Reader // underlying reader
    N int64  // max bytes remaining
}
```

For methods, use a consistent receiver name across the type so the method list reads uniformly on pkg.go.dev. A type with `func (c *Conn) Read` and `func (conn *Conn) Write` looks unfinished.

## Constant and variable documentation

**Grouped** (a `const (...)` or `var (...)` block of related items): one introductory doc comment for the whole block, with brief end-of-line comments on individual entries:

```go
// Generic file system errors.
// Errors returned by file systems can be tested against these errors
// using errors.Is.
var (
    ErrInvalid    = errInvalid()    // "invalid argument"
    ErrPermission = errPermission() // "permission denied"
    ErrExist      = errExist()      // "file already exists"
    ErrNotExist   = errNotExist()   // "file does not exist"
)
```

For typed constants displayed next to their type on pkg.go.dev, the type's doc comment can cover them; the const block need not repeat the explanation.

**Ungrouped** (a single top-level `const` or `var`): a full doc comment starting with the name, same as for any other top-level symbol:

```go
// Version is the Unicode edition from which the tables are derived.
const Version = "13.0.0"
```

## Testable examples

Go's `testing` package supports `Example` functions: documented uses of a package that are compiled (and optionally run) by `go test` and rendered on pkg.go.dev. They are the most reliable form of documentation because they cannot drift away from the API — a renamed function breaks the example at the next test run.

Add an example when the API has any non-trivial usage pattern that prose alone won't communicate. Place examples in a `_test.go` file in the same package (or a `*_test` external package if they need to import the package the same way users would). For naming rules, output assertions, and the whole-file example pattern, see `references/examples.md`.

## Cross-references with doc links

Inside any doc comment, use `[Name]` to link to another exported identifier in the same package, or `[pkg.Name]` to link across packages. Doc links render as hyperlinks on pkg.go.dev and are validated by `go doc` and IDEs — broken links surface immediately.

```go
// ReadFrom reads data from r until EOF and appends it to the buffer, growing
// the buffer as needed. The return value n is the number of bytes read. Any
// error except [io.EOF] encountered during the read is also returned. If the
// buffer becomes too large, ReadFrom will panic with [ErrTooLarge].
func (b *Buffer) ReadFrom(r io.Reader) (n int64, err error) { ... }
```

Use them liberally in package overviews and in any prose that names another symbol. See `references/comment-syntax.md` § Doc links for the full syntax (including the `[*pkg.Type]` pointer form and the rule about adjacent punctuation).

## Publishing and previewing

Two distinct workflows:

- **Local preview before publishing**: run `pkgsite` in the module directory and open the rendered docs in a browser. Iterate on comments, refresh, repeat. See `references/pkgsite-preview.md`.

  ```bash
  go install golang.org/x/pkgsite/cmd/pkgsite@latest
  cd /path/to/module
  pkgsite -open      # opens http://localhost:8080
  ```

- **Publishing to pkg.go.dev**: pkg.go.dev indexes any public module reachable via the Go module proxy. Tag a semantic version, push the tag, and either visit `https://pkg.go.dev/<module-path>` and click *Request*, or run `go get <module-path>@<version>` from any machine — both trigger indexing. See `references/publishing.md` for license, version, and README requirements.

While editing, `go doc` is the fastest way to verify a comment renders as intended. It uses the same parsing as pkg.go.dev, so what you see locally matches what users will see published:

```bash
go doc                          # current package overview
go doc .                        # same
go doc SomeType                 # a specific symbol
go doc SomeType.Method          # a method
go doc -all                     # everything in the current package
go doc -src SomeType            # also show source
```

Reach for `pkgsite` once the comment includes formatting (headings, lists, links, code blocks) — that's where the HTML rendering can diverge from the plain-text `go doc` view, particularly around code block indentation and list formatting.

## Quick checklist before committing

- [ ] Every exported name has a doc comment with no blank line between the comment and the declaration.
- [ ] The first sentence names the symbol and follows the pattern from the table above.
- [ ] The package has a `Package <name> ...` comment (in `doc.go` for multi-file packages).
- [ ] `gofmt` produces no changes to the comments (`gofmt -d ./...`).
- [ ] `go doc` shows the symbol with the comment you expected.
- [ ] For new APIs: at least one `Example` function demonstrates the common usage path.
- [ ] If any comment uses links, lists, headings, or code blocks: previewed in `pkgsite` and renders as intended.
