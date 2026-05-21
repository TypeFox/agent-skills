# Naming reference

This file expands the naming rules in SKILL.md with edge cases, worked examples, and the longer tail of decisions: the full initialism table, package anti-patterns, import grouping, file naming.

Contents:

- [Initialisms: the full table](#initialisms-the-full-table)
- [Worked naming examples](#worked-naming-examples)
- [Package naming: what to avoid](#package-naming-what-to-avoid)
- [Stutter and the package prefix](#stutter-and-the-package-prefix)
- [Acronyms inside type names](#acronyms-inside-type-names)
- [File naming and build constraints](#file-naming-and-build-constraints)
- [Import grouping and ordering](#import-grouping-and-ordering)
- [Line-length philosophy](#line-length-philosophy)

## Initialisms: the full table

The rule: an initialism keeps one case throughout. Either all uppercase (exported identifiers, or initialisms not in the first position of an unexported identifier) or all lowercase (when the initialism leads an unexported identifier).

| Initialism | Exported uses         | Unexported uses        | Notes                                                              |
| ---------- | --------------------- | ---------------------- | ------------------------------------------------------------------ |
| URL        | `URL`, `ParseURL`     | `url`, `rawURL`        | `URLs` (plural) keeps the `s` lowercase                            |
| ID         | `ID`, `UserID`        | `id`, `userID`         | `IDs` for plural                                                   |
| HTTP       | `HTTP`, `ServeHTTP`   | `http`, `httpClient`   |                                                                    |
| HTTPS      | `HTTPS`, `HTTPSProxy` | `https`, `httpsProxy`  |                                                                    |
| JSON       | `JSON`, `MarshalJSON` | `json`, `parseJSON`    |                                                                    |
| XML        | `XML`, `XMLReader`    | `xml`, `xmlReader`     |                                                                    |
| API        | `API`, `RESTAPI`      | `api`, `restAPI`       |                                                                    |
| IO         | `IO`, `ReadIO`        | `io`, `readIO`         |                                                                    |
| DB         | `DB`, `*sql.DB`       | `db`, `userDB`         |                                                                    |
| UI         | `UI`, `UIComponent`   | `ui`, `mainUI`         |                                                                    |
| UUID       | `UUID`                | `uuid`, `txUUID`       |                                                                    |
| OAuth      | `OAuth`, `OAuthToken` | `oauth`, `oauthToken`  | A proper name with mixed case — keep the brand form                |
| IPv4 / IPv6| `IPv4`, `IPv6Addr`    | `ipv4`, `ipv6Addr`     | Proper-name camel survives                                         |
| gRPC       | `GRPCServer`, or `Server` if the package is `grpc` | `grpcServer` | Stylized brand; uppercase or lowercase wins by context |

The rule cascades: `parseJSONResponse`, `xmlHTTPRequest`, `userIDs`, `OAuthAccessToken`, `HTTPSProxyAddr`.

## Worked naming examples

Cases models get subtly wrong:

| Wrong              | Right                          | Why                                                  |
| ------------------ | ------------------------------ | ---------------------------------------------------- |
| `userId`           | `userID`                       | `ID` is an initialism                                |
| `parseJson`        | `parseJSON`                    | `JSON` is an initialism                              |
| `ServeHttp`        | `ServeHTTP`                    | `HTTP` is an initialism                              |
| `xmlHttpRequest`   | `xmlHTTPRequest`               | Initialism in the middle                             |
| `Urls`             | `URLs`                         | Plural `s` stays lowercase                           |
| `getUser`          | `User` (method) / `FetchUser`  | No `Get` prefix on getters; if real work, name it    |
| `MAX_RETRIES`      | `maxRetries`                   | MixedCaps, not snake_case                            |
| `_internalState`   | `internalState`                | Leading underscore is not Go's convention            |
| `userIdString`     | `userID`                       | Don't restate the type in the name                   |

## Package naming: what to avoid

Names that mean nothing collect everything. `util`, `common`, `helpers`, `misc`, `base`, `shared`, `types`, `interfaces`, `models`, `lib` — every one of these has shipped in production codebases and every one of them has become a graveyard of unrelated functions.

If you find yourself reaching for one of these names, ask: **what is this code actually about?** Concrete answers point at concrete package names:

- "It's helpers for parsing config files" → package `config`.
- "It's types shared between server and client" → factor the types into the domain package they describe; if they're not about one domain, the abstraction is wrong.
- "It's small utilities" → split them. Each utility lives in the package whose API it serves.

The right test for a package: can a new contributor predict, from the import path alone, what does and does not belong there? If `util` passes that test, you have invented a new vague word.

## Stutter and the package prefix

The package name is part of every call site: `bytes.NewBuffer`, `json.Marshal`, `http.Get`, `time.Now`. Repeating the package name in the type or function name reads as stutter:

```go
// Stutter.
package chubby

type ChubbyFile struct { /* ... */ }

func NewChubbyFile() *ChubbyFile

// Idiomatic.
package chubby

type File struct { /* ... */ }

func New() *File          // when the package has one obvious central type
// or
func NewFile() *File      // when there are several
```

The standard library is the model: `bytes.Buffer`, not `bytes.BytesBuffer`; `http.Client`, not `http.HTTPClient`; `time.Time`, not `time.TimeValue`.

Exception: when the bare name would collide with the package name itself (`time.Time` is the textbook case), or when disambiguation actually helps a reader (`net.IP` and `net.IPNet` coexist deliberately).

## Acronyms inside type names

Acronym casing is the same rule applied inside compound type names:

| Wrong              | Right             |
| ------------------ | ----------------- |
| `HttpsProxy`       | `HTTPSProxy`      |
| `XmlHttpRequest`   | `XMLHTTPRequest`  |
| `JsonDecoder`      | `JSONDecoder`     |
| `IdTokenValidator` | `IDTokenValidator`|

Adjacent acronyms keep their case independently — `XMLHTTPRequest` is three runs (`XML`, `HTTP`, `Request`) and reads cleanly even though it looks dense.

## File naming and build constraints

Go file names are lowercase, optionally with underscores: `client.go`, `client_test.go`, `internal_helper.go`. Identifiers inside use mixed caps; only file names accept underscores.

Special suffixes the toolchain reads:

- `_test.go` — file is part of the test binary, not the main build.
- `_GOOS.go`, `_GOARCH.go`, `_GOOS_GOARCH.go` — implicit build constraint by file name. `client_linux.go`, `client_windows_amd64.go`. The toolchain only compiles the file on a matching system.
- A leading `_` or `.` excludes the file from the build entirely.

For finer-grained constraints, use a `//go:build` directive at the top of the file (above the package clause, with a blank line between).

## Import grouping and ordering

`goimports` groups imports by source, separated by blank lines:

```go
import (
    "fmt"
    "io"
    "os"

    "github.com/example/sdk"
    "golang.org/x/sync/errgroup"

    "internal.example.com/myorg/internal/foo"
)
```

The conventional grouping is stdlib → third party → local module, blank line between each group. Within a group, imports are alphabetical. `goimports` does this automatically; don't fight it.

Avoid renaming imports unless you have a collision. The package name on the import declaration must match the package's declared name; aliases like `import myname "github.com/example/sdk"` are reserved for collision resolution, not aesthetics.

Two restricted forms:

- **Blank import** `import _ "pkg"` — only for packages with intentional `init` side effects (`net/http/pprof`, image-format registration). Restrict to `main` packages and tests.
- **Dot import** `import . "pkg"` — only in test files that need access to unexported names from the package under test, and only when the alternative (moving the test into the package) doesn't work. Never in non-test code.

## Line-length philosophy

Go does not impose a line length limit. Break lines at semantic boundaries — between arguments, after operators that bind weakly, around the `{` of a multi-clause `if`. Do not break a line just to fit an arbitrary 80- or 100-character cap if the break would split a thought.

If a line is uncomfortably long, the answer is often shorter names (variables that are descriptive but not verbose) or extracting a temporary, not adding a backslash or wrapping mid-expression.
