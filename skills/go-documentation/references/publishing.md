# Publishing to pkg.go.dev

How pkg.go.dev discovers, indexes, and renders a Go module's documentation. The pkg.go.dev project's own about page is at https://pkg.go.dev/about — what follows is the agent-facing summary.

## Table of contents

- [How pkg.go.dev finds your module](#how-pkggodev-finds-your-module)
- [Requirements](#requirements)
- [Publishing a new module or version](#publishing-a-new-module-or-version)
- [Triggering indexing manually](#triggering-indexing-manually)
- [README rendering](#readme-rendering)
- [Source-code links](#source-code-links)
- [Retracting or hiding versions](#retracting-or-hiding-versions)
- [Build constraints and platform-specific docs](#build-constraints-and-platform-specific-docs)

## How pkg.go.dev finds your module

> Data for the site is downloaded from proxy.golang.org. We monitor the Go Module Index regularly for new packages to add to pkg.go.dev.

The chain is:

1. You tag a version in your source repository and push the tag.
2. Anyone (you, a user, a CI job, pkg.go.dev itself) requests that version from `proxy.golang.org`. The proxy is a public read-through cache — it fetches the module from your source repo and stores a permanent immutable copy.
3. The proxy adds the new version to `index.golang.org`, the public module index.
4. pkg.go.dev polls the index every few minutes; new versions trigger documentation generation from the proxy's cached source.

You don't push to pkg.go.dev directly. Everything flows through the proxy. The implication: pkg.go.dev shows what's in the proxy at a specific version, not what's in your source repo right now. If you fix a doc comment but don't tag a new version, pkg.go.dev keeps showing the old text indefinitely.

## Requirements

pkg.go.dev will index any public module reachable via `go get`, but several quality indicators determine what shows up well:

- **`go.mod` file in the module root.** Without it, the module is treated as legacy GOPATH code; documentation may still render but version listing breaks. Required since Go 1.16's module-aware default.
- **Redistributable license.** pkg.go.dev only displays full documentation when the module has a license file that places minimal restrictions on use, modification, and redistribution. The site detects the license from a top-level `LICENSE`, `LICENSE.txt`, `LICENSE.md`, `COPYING`, or similar file using https://github.com/google/licensecheck. Common OSI-approved licenses (MIT, Apache-2.0, BSD-3-Clause, etc.) are recognized automatically. Modules without a recognized redistributable license render with documentation hidden and a notice explaining why; the full policy is at https://pkg.go.dev/license-policy.
- **Tagged semantic version.** Untagged commits (`v0.0.0-<date>-<hash>` pseudo-versions) work but are treated as unstable and de-prioritized. Use `vMAJOR.MINOR.PATCH` tags (`v1.2.3`).
- **`v1.0.0` or later for stable APIs.** Anything `v0.x.y` is conventionally treated as experimental; breaking changes are allowed without bumping the major version, and pkg.go.dev (and `go get`) flag it accordingly.
- **Major version 2+ in the import path.** Modules at `v2` or higher must encode the major version in the module path: `example.com/foo/v2` for `v2.x.y`. The `go.mod` `module` directive must match. This is a `go` toolchain rule, not a pkg.go.dev quirk, but pkg.go.dev surfaces the mismatch as a missing version.

## Publishing a new module or version

The full flow for a first-time publish:

1. Initialize the module: `go mod init <module-path>`. The module path is the canonical import path — usually the source repo URL (`github.com/<org>/<repo>`), or a vanity path that resolves to one via a `<meta>` redirect.
2. Add a `LICENSE` file with a redistributable license.
3. Write the package documentation (see the main `SKILL.md`).
4. Preview locally with `pkgsite` (see `pkgsite-preview.md`) and confirm the rendering looks correct.
5. Commit and push to the public source repo.
6. Tag a semantic version: `git tag v0.1.0 && git push --tags`. Use `v1.0.0` when the API is stable.
7. Trigger indexing (see next section).

For subsequent versions, repeat steps 4–7. Note that once a version is published to the proxy, **its source is immutable**. You cannot reuse or retroactively fix a tag — you can only publish a new version. If a tag was pushed with a bad commit, see [Retracting or hiding versions](#retracting-or-hiding-versions).

## Triggering indexing manually

pkg.go.dev picks up new versions automatically within a few minutes of the proxy seeing them. To force the process:

- **Visit the package page** at `https://pkg.go.dev/<module-path>` and click the *Request* button. pkg.go.dev queues a fetch from the proxy.
- **Use `go get`** from any machine with the Go toolchain installed:

  ```bash
  GOPROXY=https://proxy.golang.org go get <module-path>@<version>
  ```

  This forces the proxy to fetch and cache that exact version, which in turn makes it visible to the index.

- **Hit the proxy directly** with curl:

  ```bash
  curl https://proxy.golang.org/<module-path>/@v/<version>.info
  ```

  Same effect as `go get` but doesn't require Go to be installed. Replace `<module-path>` with the lower-case escaped form (capital letters are encoded as `!<letter>`, e.g., `github.com/!foo/!bar`).

If the package still doesn't appear after a few minutes, the most common causes are: the source repo is private, the tag isn't a valid semantic version (`v1.2.3`, not `1.2.3` or `release-1.2.3`), or the module path in `go.mod` doesn't match the repo URL.

## README rendering

pkg.go.dev pulls a top-level `README.md`, `README.markdown`, `README.mkd`, `README`, or `README.txt` from the module root and renders it under the package overview. Markdown READMEs render as CommonMark (with sanitization); plain-text READMEs render preformatted.

Relative links and images in the README are rewritten to absolute URLs pointing at the source repo, so `[the docs](docs/usage.md)` and `![logo](assets/logo.png)` work as expected once published.

Notes on README authoring for pkg.go.dev:

- The README is a complement to the package doc, not a replacement. Put the package overview, examples, and reference material in doc comments — they show up in `go doc`, IDE hover cards, and pkg.go.dev's structured layout. The README is for installation, motivation, project status, badges, and links to broader docs.
- The README is rendered as plain Markdown; doc-link syntax `[Name]` does **not** resolve to Go symbols inside the README. Use Markdown links to pkg.go.dev URLs instead: `[Client](https://pkg.go.dev/example.com/foo#Client)`.
- HTML inside Markdown is sanitized aggressively. Iframes, scripts, and most styling attributes are stripped.

## Source-code links

pkg.go.dev tries to link each symbol on a package page to its definition in the source repo. For repos hosted on GitHub, GitLab, Bitbucket, and a handful of other recognized providers, this works automatically.

For vanity import paths or self-hosted repos, add a `<meta name="go-source">` tag on the import-path's landing page; the format is documented at https://github.com/golang/gddo/wiki/Source-Code-Links. If even that doesn't work, the pkgsite project accepts contributions adding the pattern to `internal/source` — see https://go.dev/issues/40477.

If symbol "Source" links from pkg.go.dev land on a 404, the most common cause is a tag/branch mismatch: pkg.go.dev links to the tagged version, but the file or line moved on the default branch. The link is correct for the version that was published; checking out the tag locally will show the symbol where pkg.go.dev says it is.

## Retracting or hiding versions

A version pushed to the proxy is permanent. If you tagged a bad release, you have two recourse mechanisms.

### Retraction (the supported path)

Add a `retract` directive to `go.mod` and publish a **new** version that contains the retraction:

```
// go.mod
module example.com/foo

go 1.21

retract v1.2.3 // contains broken Marshal — use v1.2.4 instead
```

After tagging and pushing the new version:

- `go get` skips the retracted version in `@latest` resolution and warns users who explicitly request it.
- pkg.go.dev hides the retracted version from the version list by default.

You can retract ranges: `retract [v1.0.0, v1.2.3]`. You can also retract the current version by including its own retraction — but the retraction only takes effect once a *newer* version exists that contains the directive. So the realistic flow is: bump version, add the retraction to the new version's `go.mod`, push.

See https://go.dev/ref/mod#go-mod-file-retract for the full spec.

### Removal request (when retraction isn't enough)

If the source repo or domain is gone, or you want to remove all current and future versions from pkg.go.dev (not from the proxy or `go get`), file a request via the pkgsite team's form at https://go.dev/s/pkgsite-package-removal. The package will continue to be reachable via `go get` and `go install` — only the pkg.go.dev rendering is suppressed.

## Build constraints and platform-specific docs

When a package contains files with build constraints (e.g., `//go:build linux`), pkg.go.dev shows documentation for one build context by default and offers a dropdown to switch.

The supported build contexts are a fixed set defined at https://go.googlesource.com/pkgsite/+/master/internal/build_context.go (typical OS/arch pairs like `linux/amd64`, `darwin/arm64`, `windows/amd64`, `js/wasm`). Documentation that exists *only* under an unsupported build constraint won't render.

If you maintain a package whose API differs by platform and a specific platform isn't showing up:

- Verify the build constraint syntax (use `//go:build` form, not the older `// +build` form, for any new code).
- Confirm at least one file in the package satisfies a *supported* build context — otherwise pkg.go.dev has nothing to render.
- For docs that should appear regardless of platform, put them in a file with no build constraint (or in `doc.go`).
