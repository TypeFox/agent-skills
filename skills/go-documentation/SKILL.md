---
name: go-documentation
description: Write idiomatic Go doc comments that render correctly on pkg.go.dev — package comments, `doc.go`, exported-symbol comments, testable `Example` functions, deprecation notices — and publish or debug modules on pkg.go.dev (`pkgsite`, the module proxy). Use when writing or reviewing Go documentation, or when a developer used to writing JSDoc/TSDoc/Markdown is unsure how Go doc comments differ. Not for general Go programming or non-Go languages.
---

# Go Documentation

Go treats documentation as part of the toolchain. `go doc` reads comments locally, [pkg.go.dev](https://pkg.go.dev) publishes them, and `gofmt` normalizes their markup. The conventions here come from the official spec at https://go.dev/doc/comment — tools depend on them, so they are not stylistic preferences.

## Coming from TypeScript

A Go doc comment is a plain `//` comment above a declaration — there are no tags, and almost none of the Markdown that JSDoc/TSDoc allow. These are the habits that silently produce wrong or unrendered docs; reach for the Go column instead.

| TypeScript / JSDoc habit                 | What Go actually does                                                                                     |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `@param`, `@returns`, `@throws` tags     | No tags exist. Name params and results in prose ("It returns the number of bytes written"). Types are in the signature — don't restate them. |
| `` `inline code` `` backticks            | Backticks (and `'single quotes'`) render as curly ‘quotes’. There is no inline-code markup — use a doc link `[Name]` for a symbol, plain text otherwise. |
| Markdown link `[text](url)`              | Not a link. Use a bare URL, or reference style: `[text]` in prose plus `[text]: https://…` defined at the end of the comment. |
| `{@link Foo}` cross-reference            | Not recognized, renders as literal text. Use a doc link: `[Foo]`.                                         |
| Fenced ```` ``` ```` blocks, `**bold**`  | No fences, no emphasis. A code block is any line indented by one tab; `**bold**` renders literally.       |
| `/** ... */` Javadoc-style block comment | Valid Go syntax, and it *does* attach as the doc comment — but `gofmt` recognizes the leading-`*` pattern and deliberately leaves it untouched, so the un-stripped `*` on every line makes `go doc`/pkg.go.dev render it as a mangled code block. Use a plain `//` on every line instead. |
| `@example` with a snippet                | Examples are real compiled functions (`func ExampleFoo()`) in `_test.go`, run by `go test`. See `references/examples.md`. |
| `@deprecated`                            | A paragraph beginning with the exact prefix `Deprecated: `.                                               |
| Summary in any phrasing                  | The first sentence must start with the symbol name: `Foo returns…`, `Package foo…` (see the table below). |
| README is the docs (npmjs.com)           | pkg.go.dev and `go doc` show the **package comment**, in addition to the README, above the API.           |
| Indent comment text freely               | Any indented line becomes a code block. Keep prose flush left.                                            |

These habits usually show up together. Porting one JSDoc comment typically means fixing several rows in the table at once. Before — reads fine in an editor, renders broken or missing on pkg.go.dev:

```go
// `Cache` is a simple LRU cache.
//
// @param size max number of entries
// @returns a new Cache
func NewCache(size int) *Cache { ... }

// Method to look up `key`, returns true if found.
// See the [tuning guide](https://example.com/cache-tuning) for eviction details.
func (c *Cache) Get(key string) (string, bool) { ... }
```

After:

```go
// Cache is a simple LRU cache.
type Cache struct{ ... }

// NewCache creates a Cache that holds at most size entries.
func NewCache(size int) *Cache { ... }

// Get reports whether key is present in the cache, returning its
// value if so. See https://example.com/cache-tuning for eviction details.
func (c *Cache) Get(key string) (string, bool) { ... }
```

## Reference files

Load on demand; don't read upfront.

- `references/comment-syntax.md` — full markup grammar (paragraphs, headings, links, doc links, lists, code blocks, notes, deprecations, directives), the gofmt reformatting rules, and the pitfalls that produce unintended code blocks or broken lists. Read it for any comment richer than plain prose, or when gofmt reformats a comment unexpectedly.
- `references/examples.md` — testable `Example` functions: naming rules (including the `_suffix` lower-case constraint), `// Output:` / `// Unordered output:` assertions, whole-file examples. Read it when adding examples or when one misbehaves.
- `references/publishing.md` — how pkg.go.dev discovers and indexes modules via `proxy.golang.org`: `go.mod` and license requirements, semantic versioning, README rendering, source links, retraction, removal. Read it before publishing, or when a module isn't showing up.
- `references/pkgsite-preview.md` — running `pkgsite` to preview a module's docs locally before publishing. Read it when iterating on comments.

## The attachment rule

A doc comment is a comment placed **immediately** before a top-level `package`, `const`, `func`, `type`, or `var` declaration, with **no blank line between them**. The blank line is what `go/doc` uses to tell a doc comment from an unrelated comment above it. Get it wrong and the docs vanish from `go doc` and pkg.go.dev even though the comment is still in the source. Every exported (capitalized) name should have one.

## First sentence names the symbol

`go doc`, IDE hovers, and pkg.go.dev search all surface the first sentence alone as the one-line summary — often with no symbol name beside it. So the sentence must name the symbol itself.

| Symbol kind            | First-sentence pattern                | Example                                                                         |
| ---------------------- | ------------------------------------- | ------------------------------------------------------------------------------- |
| Package                | `Package <name> ...`                  | `Package path implements utility routines for manipulating slash-separated paths.` |
| Command (`main`)       | `<Command> ...` (capitalized)         | `Gofmt formats Go programs.`                                                     |
| Type                   | `A <Type> ...` / `An <Type> ...`      | `A Reader serves content from a ZIP archive.`                                    |
| Function (returns)     | `<Function> returns ...`              | `Quote returns a double-quoted Go string literal representing s.`                |
| Function (side effect) | `<Function> <verb> ...`               | `Exit causes the current program to exit with the given status code.`            |
| Function (bool result) | `<Function> reports whether ...`      | `HasPrefix reports whether the string s begins with prefix.`                     |
| Constant / variable    | `<Name> is ...` / `<Name> <verb> ...` | `Version is the Unicode edition from which the tables are derived.`              |

Use `reports whether` for booleans, not `returns true if` — it is the standard-library convention and reads better in the index.

## Package documentation

The package comment is the most important comment in a module: it is what pkg.go.dev indexes and shows on the landing page, and what answers "what is this for?". Write the first sentence as a self-contained one-liner starting with `Package <name>` — assume the reader sees nothing else.

Good: `Package errgroup provides synchronization, error propagation, and Context cancellation for groups of goroutines working on subtasks of a common task.`
Weak: `This package is a small library for working with goroutines.` — no `Package errgroup`, says nothing specific.

Put the comment in a dedicated `doc.go` (only the comment plus the `package` clause). It is a stable home that survives the file renames that silently orphan a comment attached to a regular source file, and it signals where package docs live. Only one file may hold the package comment; multiple are concatenated in an unspecified order.

```go
// Package json implements encoding and decoding of JSON as defined in
// RFC 7159. The mapping between JSON and Go values is described
// in the documentation for the [Marshal] and [Unmarshal] functions.
package json
```

For packages beyond a handful of symbols, add a short overview after the first paragraph pointing at the main entry points with doc links, so the page doesn't render as a wall of symbols:

```go
// Package http provides HTTP client and server implementations.
//
// [Get], [Head], [Post], and [PostForm] make HTTP (or HTTPS) requests:
//
//  resp, err := http.Get("http://example.com/")
//
// The client must close the response body when finished with it:
//
//  defer resp.Body.Close()
//
// For control over headers and redirect policy, create a [Client] ...
package http
```

### README vs `doc.go`

Modules typically need both, for two readers — don't paste the same text into both. The `README.md` is read on the host (GitHub/pkg.go.dev landing area) by someone **not yet using** the module: pitch, `go get`, prerequisites, badges, a quick-start snippet. The package comment is read via `go doc`, IDE hover, and the pkg.go.dev API view by someone who **already imported** it: technical overview, main types and call flow, invariants, error and concurrency semantics, doc links to key symbols. After `go get` the README disappears from daily work — a package overview that only says "see README" loses the toolchain integration that makes Go docs distinctive.

For a multi-package module: one `README.md` at the root, and a package comment (usually a `doc.go`) in every package and subpackage — not a README per package.

### Commands (`package main`)

For a binary, the package comment describes the program, not a Go API. Use semantic linefeeds (one sentence per line); gofmt preserves them, giving cleaner diffs.

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
//  -l
//      List files whose formatting differs from gofmt's.
package main
```

## Function and method documentation

Pick the first-sentence pattern from the table, then add what a caller needs. Refer to parameters and results by name in prose, without backticks; avoid names like `a` or `s` that read as ordinary words.

- **Special cases** as an indented block:

  ```go
  // Sqrt returns the square root of x.
  //
  // Special cases are:
  //
  //  Sqrt(+Inf) = +Inf
  //  Sqrt(x < 0) = NaN
  //  Sqrt(NaN) = NaN
  func Sqrt(x float64) float64
  ```

- **Concurrency safety.** Top-level functions are conventionally assumed safe for concurrent use; methods are assumed *not* safe (single goroutine at a time). State any exception explicitly.
- **Complexity** when it matters to callers (e.g. `sort.Sort` documents its O(n log n) comparisons).
- **Deprecation** via a `Deprecated:` paragraph — always name the replacement. See `references/comment-syntax.md` § Deprecations.

Document behavior callers can rely on, not the algorithm. "Uses quicksort internally" locks the implementation behind the doc contract; a maintainer who switches to timsort silently breaks it.

## Type documentation

Start with `A <Type>` / `An <Type>` describing what an instance represents, then add whichever apply:

- **Zero value.** If the zero value is meant to work, say so — readers can only rely on it if documented: `The zero value for Buffer is an empty buffer ready to use.`
- **Concurrency safety.** Default is "not safe"; anything stronger must be explicit.
- **Fields.** Either the type comment describes exported fields collectively, or each field carries its own comment — pick one per type.

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

Use one consistent receiver name across a type's methods; mixing `c *Conn` and `conn *Conn` looks unfinished in the method list.

## Constant and variable documentation

**Grouped** (`const (...)` / `var (...)`): one intro comment for the block, brief end-of-line comments per entry.

```go
// Generic file system errors.
// Errors returned by file systems can be tested against these errors
// using errors.Is.
var (
    ErrInvalid    = errInvalid()    // "invalid argument"
    ErrPermission = errPermission() // "permission denied"
    ErrExist      = errExist()      // "file already exists"
)
```

**Ungrouped** (a single top-level `const`/`var`): a full comment starting with the name, like any other symbol.

## Doc links

Inside any comment, `[Name]` links to an exported identifier in the same package and `[pkg.Name]` links across packages. They render as hyperlinks and are validated by `go doc` and IDEs, so broken links surface immediately. Use them liberally in overviews and wherever prose names another symbol.

```go
// ReadFrom reads data from r until EOF and appends it to the buffer, growing
// the buffer as needed. Any error except [io.EOF] encountered during the read
// is also returned. If the buffer becomes too large, ReadFrom panics with
// [ErrTooLarge].
func (b *Buffer) ReadFrom(r io.Reader) (n int64, err error) { ... }
```

A link must be surrounded by punctuation, spaces, or line boundaries: `map[ast.Expr]TypeAndValue` is *not* a link because the brackets touch other identifier characters. See `references/comment-syntax.md` § Doc links.

## Testable examples

`Example` functions are documented uses compiled (and optionally run) by `go test` and rendered on pkg.go.dev. They can't drift from the API — a rename breaks them at the next test run. Add one for any non-trivial usage pattern prose won't convey; place them in a `_test.go` file, preferably in a `*_test` external package so they import the package as a user would. For naming, output assertions, and whole-file examples, see `references/examples.md`.

## Publishing and previewing

- **Preview locally** with `pkgsite` in the module directory, then iterate. See `references/pkgsite-preview.md`.

  ```bash
  go install golang.org/x/pkgsite/cmd/pkgsite@latest
  cd /path/to/module && pkgsite -open   # http://localhost:8080
  ```

- **Publish**: tag a semantic version and push; pkg.go.dev indexes any public module reachable via the proxy. Force it by visiting `https://pkg.go.dev/<module-path>` and clicking *Request*, or running `go get <module-path>@<version>`. See `references/publishing.md` for license, version, and README requirements.

While editing, `go doc` is the fastest check — same parser as pkg.go.dev:

```bash
go doc                 # current package overview
go doc SomeType        # a specific symbol
go doc SomeType.Method # a method
go doc -all            # everything in the package
```

Switch to `pkgsite` once a comment includes formatting (headings, lists, links, code blocks) — that's where HTML rendering can diverge from `go doc`'s plain text.

For mechanical enforcement in CI, `staticcheck`'s stylecheck rules `ST1000` (package comment format) and `ST1020`–`ST1022` (function/type/const comments must start with the declared name) catch malformed openers — they're opt-in (excluded from the default check set), so enable them explicitly if you want this checked automatically.

## Quick checklist before committing

- [ ] Every exported name has a doc comment with no blank line before its declaration.
- [ ] The first sentence names the symbol and follows the table's pattern.
- [ ] The package has a `Package <name> ...` comment (in `doc.go` for multi-file packages).
- [ ] Package overview and API entry points live in doc comments, not only in `README.md`.
- [ ] No JSDoc leftovers: no `@param`/`@returns` tags, no `/** */` block comments, no `{@link}` refs, no `` `backtick` `` code, no `[text](url)` links, no `**bold**`.
- [ ] `gofmt -d ./...` produces no changes to the comments.
- [ ] `go doc` shows each symbol with the comment you expected.
- [ ] New APIs have at least one `Example`; comments with links/lists/headings/code blocks preview correctly in `pkgsite`.
