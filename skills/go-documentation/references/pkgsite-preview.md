# Previewing documentation locally with pkgsite

`pkgsite` is the same Go program that powers https://pkg.go.dev, packaged so you can run it locally against an unpublished module. Use it to iterate on doc comments and see exactly how they will render once published — particularly important when comments contain anything richer than plain prose (links, lists, code blocks, examples), since the HTML rendering can diverge from the plain-text `go doc` view.

Upstream: https://pkg.go.dev/golang.org/x/pkgsite/cmd/pkgsite. The source is at https://github.com/golang/pkgsite.

## Table of contents

- [Install](#install)
- [Basic usage](#basic-usage)
- [Flags](#flags)
- [Iterating on a single module](#iterating-on-a-single-module)
- [Multi-module workspaces](#multi-module-workspaces)
- [Serving from the module cache or proxy](#serving-from-the-module-cache-or-proxy)
- [Refreshing after edits](#refreshing-after-edits)
- [Common gotchas](#common-gotchas)

## Install

```bash
go install golang.org/x/pkgsite/cmd/pkgsite@latest
```

The binary lands in `$(go env GOBIN)` (or `$(go env GOPATH)/bin` if `GOBIN` is unset). Make sure that directory is on `$PATH`.

Verify:

```bash
pkgsite -help
```

## Basic usage

From the root of a Go module, run:

```bash
cd /path/to/your/module
pkgsite
```

pkgsite reads `go.mod`, generates documentation for the main module and its dependencies, and serves them at http://localhost:8080. Open that URL in a browser.

To open the browser automatically:

```bash
pkgsite -open
```

The module's docs are reachable at `http://localhost:8080/<module-path>` — for a module declared as `module example.com/foo`, that is `http://localhost:8080/example.com/foo`.

## Flags

Verified against the source at `cmd/pkgsite/main.go`:

| Flag           | Default            | Description                                                                  |
| -------------- | ------------------ | ---------------------------------------------------------------------------- |
| `-http`        | `localhost:8080`   | HTTP service address to listen on. Use `-http :8080` to bind on all interfaces. |
| `-open`        | `false`            | Open a browser window to the server's address on startup.                    |
| `-cache`       | `false`            | Fetch modules from the local module cache (`$GOMODCACHE`).                   |
| `-cachedir`    | `""`               | Override the module cache directory; defaults to `go env GOMODCACHE`.        |
| `-proxy`       | `false`            | Fetch from `GOPROXY` if not found locally. Useful to view third-party docs offline-ish. |
| `-list`        | `true`             | For each path argument, serve all modules in the build list (i.e., the module and its required dependencies). Set `-list=false` to serve only the requested modules. |
| `-gorepo`      | `""`               | Path to a local checkout of the Go repo, used to speed up standard library rendering. Without it, pkgsite clones the Go repo on first use of any stdlib package, which is slow. |
| `-gopath_mode` | `false`            | Treat local modules as relative to `$GOPATH/src`. Only relevant for pre-modules code. |
| `-dev`         | `false`            | Developer mode for working on pkgsite itself: reload templates on each request, serve non-minified assets. Not needed for normal documentation preview. |
| `-static`      | `"static"`         | Path to static assets. Defaults work; only change if running from a non-standard install. |

## Iterating on a single module

The recommended loop for working on documentation:

```bash
cd /path/to/module
pkgsite -open
```

This launches the server and opens the module's page. Leave the server running. Edit doc comments, save, then reload the browser tab — pkgsite re-reads the source on every request, so changes appear immediately. There is no file watcher; you trigger refreshes manually via the browser.

The exception is template/asset changes — those require restarting the server (or running with `-dev`, which auto-reloads templates). For normal doc comment editing, no restart needed.

## Multi-module workspaces

For a multi-module project using a Go workspace (`go.work`), pkgsite picks up every module listed in the workspace file:

```bash
go work init ./module-a ./module-b
pkgsite
```

Each module is reachable at its own URL on the local server. This is the right setup when working on documentation for a module that imports a sibling module — both can be edited and previewed side by side without publishing intermediate versions.

## Serving from the module cache or proxy

By default, pkgsite serves docs for the module in the current directory plus its dependencies as resolved by `go list`. With `-cache` or `-proxy`, it also (or instead) serves modules from your `$GOMODCACHE` or the public proxy:

```bash
# Serve a specific cached module
pkgsite -cache example.com/some/dep

# Pull any module from the proxy on demand
pkgsite -proxy
```

When either flag is set, pkgsite does **not** look for a module in the current directory. To serve both the current module and proxied modules, list them explicitly:

```bash
pkgsite -cache -proxy . example.com/other/module
```

The `.` argument tells pkgsite to also include the module rooted at the current directory.

## Refreshing after edits

- **Doc comment edits**: just reload the browser tab. pkgsite re-parses the source on each request.
- **`go.mod` changes** (new dependency, version bump): no restart needed; pkgsite re-resolves the build list per request.
- **Template/CSS/JS changes to pkgsite itself**: restart the server, or run with `-dev` for hot-reload.
- **Switching modules in workspace mode**: the file watcher does not pick up new `go.work` entries; restart the server when editing `go.work`.

## Common gotchas

**Port already in use.** If 8080 is taken, pick another: `pkgsite -http localhost:6060`.

**Standard library docs are slow on first launch.** Without `-gorepo`, pkgsite clones the Go source on first stdlib reference, which takes minutes. If you frequently view stdlib pages, set `-gorepo` to a local Go checkout. If you only care about your own module's docs, this isn't an issue — pkgsite doesn't pre-fetch stdlib unless requested.

**Internal packages are visible locally.** pkgsite serves `internal/` packages on the local server (since you have source access), but pkg.go.dev hides them. A doc link to an `internal/` package will render locally but break once published. Either move the symbol out of `internal/` or rephrase the doc to not link there.

**`go.mod` module path must match the source location.** pkgsite uses the `module` directive to construct URLs. If `go.mod` says `module example.com/foo` but the directory is `~/code/bar`, the docs are still served under `/example.com/foo`. The directory name doesn't matter; the `module` line does.

**Cached pages.** Browser cache can mask doc updates if you reload the same URL with no change. Hard-reload (Cmd-Shift-R / Ctrl-Shift-R) if a comment edit doesn't appear to take effect.

**Dependency docs show "no documentation available".** pkgsite renders documentation from the source it can find. If a dependency is in `vendor/` but you're running without `-mod=vendor`, or if a dependency hasn't been fetched into the cache yet, the page is empty. Run `go mod download` first to populate the cache.

**Render differs between `go doc` and pkgsite.** This is expected for comments with markup — `go doc` outputs plain text, pkgsite outputs HTML. Use `go doc` for quick "did I associate the comment with the right declaration" checks, and pkgsite for the final visual review.

## Verification before publication

Run this checklist before tagging a release:

1. `pkgsite -open` in the module root.
2. Click through every exported package and confirm:
   - The package overview is present and starts with `Package <name>`.
   - The package summary appears in search-style listings (the first sentence).
   - Every exported symbol has a doc comment (no "no documentation available" entries).
   - Doc links resolve (no literal `[Name]` brackets in the rendered text).
   - Examples render with `Output:` sections where expected.
   - Code blocks render preformatted, not as paragraph text.
3. Skim the README rendering on the package landing page.
4. Verify the rendered page matches the symbols and version you intend to publish.

What you see in pkgsite is what users will see on pkg.go.dev. The two render from the same source.
