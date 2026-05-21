# Doc comment syntax

The full markup grammar used by Go doc comments, as defined at https://go.dev/doc/comment. This reference covers everything richer than plain prose: paragraphs, headings, links, lists, code blocks, notes, deprecations, and directives. It also documents how `gofmt` reformats comments (since Go 1.19) and the half-dozen common pitfalls that produce unintended code blocks or broken lists.

## Table of contents

- [Paragraphs](#paragraphs)
- [Headings](#headings)
- [Links](#links)
- [Doc links](#doc-links)
- [Lists](#lists)
- [Code blocks and preformatted text](#code-blocks-and-preformatted-text)
- [Notes](#notes)
- [Deprecations](#deprecations)
- [Directives](#directives)
- [How gofmt reformats comments](#how-gofmt-reformats-comments)
- [Common pitfalls](#common-pitfalls)

## Paragraphs

A paragraph is a run of unindented non-blank lines. Use full sentences. Paragraphs are separated by one blank line; gofmt collapses multiple blank lines to one.

Gofmt **does not rewrap paragraph text** — it preserves your line breaks. This lets you use *semantic linefeeds*: one sentence per source line, which produces cleaner diffs when prose is edited. Use it especially in long package overviews and command docs.

```go
// Encode writes the JSON encoding of v to the stream,
// followed by a newline character.
//
// See the documentation for [Marshal] for details about
// the conversion of Go values to JSON.
```

Backtick pairs (`` ` ``) and single-quote pairs (`'`) are converted to Unicode curly quotes in rendered output, mimicking typographic conventions. Don't use them to mark code — use a code block or a doc link instead.

## Headings

A heading is a single line starting with `#` followed by a space and the heading text. It must be unindented, on its own line, and set off from adjacent paragraphs by blank lines:

```go
// # Numeric conversions
//
// The following functions perform conversions ...
```

Not headings:

```go
// #This has no space after the hash
// # This continues
// #onto a second line, which is not allowed
//     # This one is indented
```

The `#` syntax was added in Go 1.19. Before that, headings were detected heuristically (a single capitalized line with no terminal punctuation, surrounded by blank lines). The heuristic detection still works but is fragile; prefer the explicit `#` form.

There is only one heading level. Don't try to nest `##` or `###` — gofmt strips the extra hashes.

## Links

Two forms of explicit hyperlinks:

### Reference-style links

Define link targets in a separate section at the end of the comment using `[Text]: URL` on a line of their own, and reference them in prose as `[Text]`:

```go
// Package json implements encoding and decoding of JSON as defined in
// [RFC 7159]. The mapping between JSON and Go values is described
// in the documentation for the Marshal and Unmarshal functions.
//
// For an introduction to this package, see the article
// "[JSON and Go]."
//
// [RFC 7159]: https://tools.ietf.org/html/rfc7159
// [JSON and Go]: https://golang.org/doc/articles/json_and_go.html
package json
```

Why a separate definitions section: it keeps URLs out of the text, where they would interrupt reading. If `[Text]` has no corresponding `[Text]: URL` definition in the same comment, the brackets are preserved as literal text — useful for cases where the bracketed name is itself the content (e.g., `[error]`).

Link definitions are **comment-local** — a definition in one comment does not affect another comment.

Gofmt automatically moves all link definitions to the end of the comment, in up to two blocks:

1. Definitions that are referenced from the comment.
2. Definitions that are **not** referenced (so unused links are easy to spot during review).

### Plain URLs

A URL in prose (e.g., `https://example.com`) is auto-linked in the HTML rendering. There is no Markdown-style `[Text](URL)` form — use the reference style if you need link text.

## Doc links

A doc link is a hyperlink to another Go identifier, written without a URL declaration:

| Form                  | Refers to                                        |
| --------------------- | ------------------------------------------------ |
| `[Name1]`             | Exported identifier in the current package       |
| `[Name1.Name2]`       | Nested exported identifier in the current package (e.g., method) |
| `[pkg]`               | Another package (by short name or import path)   |
| `[pkg.Name1]`         | Exported identifier in another package           |
| `[pkg.Name1.Name2]`   | Nested identifier in another package             |
| `[*bytes.Buffer]`     | Pointer-form type (optional leading `*`)         |

In `[pkg.X]`, `pkg` is treated as the full import path if it starts with a domain name with a dot (`example.com/foo`) or is a standard library package (`os`, `io/fs`). Otherwise it is treated as the short package name as used in `import` statements.

Examples:

```go
// ReadFrom reads data from r until EOF and appends it to the buffer, growing
// the buffer as needed. The return value n is the number of bytes read. Any
// error except [io.EOF] encountered during the read is also returned. If the
// buffer becomes too large, ReadFrom will panic with [ErrTooLarge].
func (b *Buffer) ReadFrom(r io.Reader) (n int64, err error) { ... }
```

Constraint that bites: doc links must be **surrounded by punctuation, spaces, tabs, or line boundaries**. The text `map[ast.Expr]TypeAndValue` is *not* a doc link — `[ast.Expr]` is adjacent to other identifier characters, so the brackets are treated as part of a Go expression and rendered literally. This is usually what you want for generic-looking syntax, but be aware of it.

If you want a link to render but pkg.go.dev shows literal brackets, the most common cause is a typo in the package or symbol name (the renderer falls back to literal text when it can't resolve the target).

## Lists

### Bullet lists

Marker is one of `*`, `+`, `-`, or `•`, followed by a space or tab and the item text. Each marker line starts a new item.

```go
// PublicSuffixList provides the public suffix of a domain. For example:
//   - the public suffix of "example.com" is "com",
//   - the public suffix of "foo1.foo2.foo3.co.uk" is "co.uk", and
//   - the public suffix of "bar.pvt.k12.ma.us" is "pvt.k12.ma.us".
type PublicSuffixList interface { ... }
```

Gofmt canonicalizes bullet lists to use `-` as the marker, with two spaces before the dash and four-space continuation indent.

### Numbered lists

Marker is a decimal number followed by `.` or `)`, then a space or tab, then the item text. Numbers are preserved as written — pkg.go.dev does not renumber them, so you can intentionally start at 0 or use `1, 1, 1` for a worked example.

```go
// Clean returns the shortest path name equivalent to path
// by purely lexical processing. It applies the following rules
// iteratively until no further processing can be done:
//
//  1. Replace multiple slashes with a single slash.
//  2. Eliminate each . path name element (the current directory).
//  3. Eliminate each inner .. path name element (the parent directory)
//     along with the non-.. element that precedes it.
//  4. Eliminate .. elements that begin a rooted path:
//     that is, replace "/.." by "/" at the beginning of a path.
```

Gofmt canonicalizes to one space before the number, `.` after it, and four-space continuation indent. A blank line is inserted between the list and any following paragraph or heading.

### No nesting

Go doc comments do **not** support nested lists. Gofmt will flatten any apparent nesting. If you have hierarchical content, either rewrite it as separate flat lists with intervening prose, or use a code block.

A workaround that sometimes works is to mix list markers with blank lines (numbered outer, bulleted inner, blank lines separating items) — see https://go.dev/doc/comment for the example. But it is fragile and the rendered output is not as clean as well-written prose. Prefer to refactor.

## Code blocks and preformatted text

A code block is a span of indented or blank lines that does not start with a list marker. The whole block renders as preformatted text. Use a tab or four spaces for indentation; gofmt normalizes the indentation to a single tab.

```go
// Search uses binary search to find and return the smallest index i
// in [0, n) at which f(i) is true ...
//
// As a more whimsical example, this program guesses your number:
//
//  func GuessingGame() {
//      var s string
//      fmt.Printf("Pick an integer from 0 to 100.\n")
//      answer := sort.Search(100, func(i int) bool {
//          fmt.Printf("Is your number <= %d? ", i)
//          fmt.Scanf("%s", &s)
//          return s != "" && s[0] == 'y'
//      })
//      fmt.Printf("Your number is %d.\n", answer)
//  }
func Search(n int, f func(int) bool) int
```

Use code blocks for any non-prose content: Go snippets, shell commands, file contents, ASCII grammars, special-case tables (e.g., `Sqrt(-1) = NaN`). There is no syntax for inline code — render short identifiers as plain text, or use a doc link if it names a Go symbol.

Gofmt inserts a blank line before and after each code block.

## Notes

A note is a paragraph beginning with `MARKER(uid):`, where `MARKER` is two or more uppercase letters and `uid` is at least one character (conventionally a username):

```go
// TODO(rsc): refactor to use standard library context
// BUG(rsc): not cleaned up
var ctx context.Context
```

pkg.go.dev collects notes into a separate section per package — `BUG` notes appear under "Bugs", `TODO` under "Notes", etc. Use notes when you want the comment to surface in the package-level summary rather than only on the symbol it documents.

## Deprecations

A paragraph beginning with `Deprecated:` marks the symbol as deprecated. Tools (gopls, staticcheck, the Go vet) warn callers, and pkg.go.dev hides the symbol by default behind a "Show deprecated" toggle.

```go
// Reset zeros the key data and makes the Cipher unusable.
//
// Deprecated: Reset can't guarantee that the key will be entirely removed from
// the process's memory.
func (c *Cipher) Reset()
```

The deprecation paragraph can appear anywhere in the comment, not just at the end. Always include a recommended alternative when one exists — `Deprecated: Use the new XYZ function instead.` saves callers a search.

Deprecation also applies to packages:

```go
// Package rc4 implements the RC4 stream cipher.
//
// Deprecated: RC4 is cryptographically broken and should not be used
// except for compatibility with legacy systems.
//
// This package is frozen and no new functionality will be added.
package rc4
```

## Directives

Directives are comments interpreted by the Go toolchain or other tools — `//go:generate`, `//go:build`, `//go:embed`, `//line`, `//export`, etc. They look like comments but are **not part of the doc comment** even when adjacent to a declaration. pkg.go.dev omits them from rendered docs.

Gofmt moves directives to the end of the doc comment block, preceded by a blank line, so the doc text stays on top:

```go
// An Op is a single regular expression operator.
//
//go:generate stringer -type Op -trimprefix Op
type Op uint8
```

A line is treated as a directive if it matches the pattern `//tool:directive args` (or one of the special forms `//line`, `//extern`, `//export`). When in doubt, leave the directive in place and let gofmt move it.

## How gofmt reformats comments

Since Go 1.19, gofmt has rules for canonicalizing doc comment formatting. The rewrite is conservative — an analysis by the Go team found only ~3% of public Go module doc comments are touched, and 87% of those rewrites are unambiguously correct. The remaining cases are usually the pitfalls in the next section.

What gofmt does:

- Strips leading/trailing blank lines from each comment.
- Removes a common leading indent shared by all lines.
- Collapses runs of blank lines between paragraphs to a single blank line.
- Reformats bullet markers to `-` with two-space lead and four-space continuation.
- Reformats numbered markers to `1.` style with one-space lead and four-space continuation.
- Reorders link definitions to two blocks at the end (referenced, then unreferenced).
- Indents code blocks with a single tab.
- Inserts blank lines around code blocks.
- Moves directive lines to the end with a separating blank line.

What gofmt does **not** do: rewrap paragraph text. Your semantic linefeeds are preserved.

Run `gofmt -d ./...` to see proposed changes without applying them. Run `gofmt -w ./...` to apply.

## Common pitfalls

These are the recurring mistakes that produce broken rendering. All of them stem from the rule that **any indented non-list line is a code block**.

### Unindented numbered list

```go
// cancelTimerBody is an io.ReadCloser that wraps rc with two features:
// 1) On Read error or close, the stop func is called.
// 2) On Read failure, if reqDidTimeout is true, the error is wrapped and
//    marked as net.Error that hit its timeout.
```

Renders as a three-line paragraph (the `1)` and `2)` are not at column 0 of a list — they are inline text) followed by a one-line code block (the indented continuation). Fix by indenting the list marker so the wrapped lines hang correctly:

```go
// cancelTimerBody is an io.ReadCloser that wraps rc with two features:
//  1. On Read error or close, the stop func is called.
//  2. On Read failure, if reqDidTimeout is true, the error is wrapped and
//     marked as net.Error that hit its timeout.
```

### Indented continuation of a wrapped sentence

```go
// TODO Revisit this design. It may make sense to walk those nodes
//      only once.
```

The continuation `only once.` is indented, so it becomes a code block on its own. Fix by unindenting the continuation:

```go
// TODO Revisit this design. It may make sense to walk those nodes
// only once.
```

### Brace-delimited code blocks with mixed indentation

```go
// On the wire, the JSON will look something like this:
// {
//  "kind":"MyAPIObject",
//  "apiVersion":"v1",
// }
```

The opening `{` is at column 0 and is therefore prose, but the inner lines are indented and become a code block. Result: only the inner lines render preformatted, the braces render as part of the surrounding paragraph. Fix by indenting the whole block uniformly:

```go
// On the wire, the JSON will look something like this:
//
//  {
//      "kind":"MyAPIObject",
//      "apiVersion":"v1",
//  }
```

### Multi-line shell command with indented continuation

```go
// localhostCert is a PEM-encoded TLS cert generated from src/crypto/tls:
//
// go run generate_cert.go --rsa-bits 1024 --host 127.0.0.1,::1,example.com \
//     --ca --start-date "Jan 1 00:00:00 1970" --duration=1000000h
```

The first line of the command is unindented (paragraph), the second is indented (code block). Fix by indenting both:

```go
// localhostCert is a PEM-encoded TLS cert generated from src/crypto/tls:
//
//  go run generate_cert.go --rsa-bits 1024 --host 127.0.0.1,::1,example.com \
//      --ca --start-date "Jan 1 00:00:00 1970" --duration=1000000h
```

### Wrapped list item where the wrap isn't indented

```go
// Uses of this error model include:
//
//   - Partial errors. If a service needs to return partial errors to the
// client, it may embed the `Status` in the normal response.
```

The wrapped continuation `client, it may ...` is at column 0, breaking out of the list item. Fix by indenting continuations to align with the item text:

```go
// Uses of this error model include:
//
//   - Partial errors. If a service needs to return partial errors to the
//     client, it may embed the `Status` in the normal response.
```

### Heuristic gofmt fixes can mask the real fix

Go 1.19+ gofmt applies heuristics that merge unindented lines into adjacent code blocks or lists when it looks unambiguous. This silently fixes some of the above cases — useful, but also means a comment may render correctly today and incorrectly tomorrow under a slightly different gofmt version.

If you want a paragraph clearly separated from following non-paragraph content, insert a blank line between them. The blank line is the unambiguous separator and is preserved through every gofmt revision.

## Quick verification

Before committing comment changes that include any of the markup above:

1. `gofmt -d <file>` — see what gofmt wants to change. If it touches your comment, eyeball the diff for correctness.
2. `go doc <symbol>` — read the comment as `go/doc` parses it. This catches broken paragraph/code-block boundaries.
3. `pkgsite -open` — view the HTML rendering. See `pkgsite-preview.md`. This is the only way to confirm doc links resolve, lists render unnested, and heading levels are correct.
