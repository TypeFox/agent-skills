# The `package.json` extension manifest

Every VS Code extension is identified, configured, and described by a single `package.json` file at the extension root — the **manifest**. It's a superset of the standard npm `package.json`: VS Code adds its own fields on top, and rejects or warns on missing ones at publish time. This reference covers the publish-relevant fields. The full schema (every `contributes.*` point, every activation event) lives at https://code.visualstudio.com/api/references/extension-manifest and https://code.visualstudio.com/api/references/contribution-points.

Both registries (Marketplace and Open VSX) read the same manifest. Field validity is enforced by `vsce package` before either registry sees the file, so manifest mistakes fail fast and locally.

## Required fields

These four must be present or `vsce package` refuses to build.

| Field | Type | Notes |
|---|---|---|
| `name` | string | Lowercase, no spaces; combined with `publisher` to form the global extension ID `<publisher>.<name>`. Reserved permanently after first publish — choose carefully. |
| `version` | string | Strict SemVer (e.g. `0.1.0`). Each publish must strictly increase this; you cannot republish the same version. |
| `publisher` | string | The Marketplace publisher ID / Open VSX namespace. Same string on both registries by convention but registered independently — see SKILL.md § "Decide what to publish to". |
| `engines.vscode` | string | VS Code version range the extension supports (e.g. `^1.84.0`). Wildcard `*` is rejected. Must be a real released VS Code version. Determines the minimum host the Marketplace will offer the extension to. |

```json
{
  "name": "my-extension",
  "version": "0.1.0",
  "publisher": "my-publisher",
  "engines": { "vscode": "^1.84.0" }
}
```

## Strongly recommended for publishing

Missing these doesn't block `vsce package`, but the resulting Marketplace/Open VSX listing will look broken or unprofessional.

| Field | Purpose | Constraints |
|---|---|---|
| `displayName` | Human-readable extension name shown in search and on the listing page. | Should be unique across the marketplace; gets compared to existing entries. |
| `description` | One-line description in search results and at the top of the listing. | Keep under ~150 chars; no marketing fluff or marketplace tags. |
| `categories` | Array used for filtering and discovery. | Pick from the fixed list below — invalid values are silently dropped. |
| `keywords` | Search keywords; do not appear visibly but improve findability. | **Maximum 30 entries** — exceeding this fails the publish. |
| `icon` | Path to the listing icon. | **PNG only**, at least **128×128px** (256×256 recommended for HiDPI). SVG is rejected. Path is relative to the manifest. |
| `repository` | Source code link shown under "Resources". | Object form: `{ "type": "git", "url": "https://github.com/..." }`. String form works but the object form is required for `vsce publish`'s git-tag behavior. |
| `license` | SPDX identifier (`MIT`, `Apache-2.0`, …) matching the `LICENSE` file. | If the license isn't a stock SPDX, use `"SEE LICENSE IN LICENSE.txt"` and ship the file. |
| `bugs` | Issue tracker link shown under "Resources". | `{ "url": "...", "email": "..." }` — email optional. |
| `homepage` | Documentation/project page link shown under "Resources". | Often the README URL on GitHub. |

### Allowed `categories` values

Per the official manifest reference: `Programming Languages`, `Snippets`, `Linters`, `Themes`, `Debuggers`, `Formatters`, `Keymaps`, `SCM Providers`, `Other`, `Extension Packs`, `Language Packs`, `Data Science`, `Machine Learning`, `Visualization`, `Notebooks`, `Education`, `Testing`.

VS Code adds new categories from time to time (recent versions ship `AI`, `Chat`, etc.). If you're publishing an extension that fits a new category, check the linked manifest reference for the current list before assuming an unrecognized value will be honored.

## Marketplace presentation

| Field | Purpose | Notes |
|---|---|---|
| `galleryBanner` | Color/theme of the listing page header. | `{ "color": "#C80000", "theme": "dark" }`. `theme` is `"dark"` or `"light"` and controls whether the publisher name renders in light or dark text on the banner. |
| `preview` | Marks the extension as Preview (yellow "Preview" badge on listing). | Boolean. Use for extensions that work but aren't 1.0 yet. Distinct from pre-release versioning (see `--pre-release` flag in SKILL.md). |
| `badges` | Extra status badges on the listing. | Array of `{ "url", "href", "description" }`. The marketplace only allows badges from approved hosts: `shields.io`, `github.com`, `codecov.io`, `snyk.io`, `gitlab.com`, etc. Arbitrary URLs are stripped. |
| `markdown` | README rendering engine. | `"github"` (default) or `"standard"`. Use `"github"` so GitHub-Flavored Markdown features (task lists, tables, code fences with language hints) render the same on the marketplace as on the source README. |
| `qna` | Q&A tab control. | `"marketplace"` (default), a URL string to redirect to your own forum, or `false` to disable the tab entirely. |
| `pricing` | `"Free"` (default) or `"Trial"`. | `"Trial"` requires a separate Microsoft Commercial Marketplace setup; almost all extensions use `"Free"`. |
| `sponsor` | Adds a "Sponsor" link on the listing. | `{ "url": "https://github.com/sponsors/<user>" }`. |

## Runtime fields

| Field | Purpose | Notes |
|---|---|---|
| `main` | Entry point for the Node.js extension host (desktop). | Path relative to the manifest, **without `.js`**. After bundling this should point at the bundle output (e.g. `./dist/extension`), not at the un-bundled TypeScript output. See `references/bundling.md`. |
| `browser` | Entry point for the Web Extension host (`vscode.dev`, `github.dev`, web Theia hosts). | Same shape as `main`. Without it, the extension is unavailable in web hosts. |
| `activationEvents` | Array of events that cause VS Code to load the extension. | Examples: `"onLanguage:markdown"`, `"onCommand:myExt.helloWorld"`, `"onStartupFinished"`, `"workspaceContains:**/.mytool"`. VS Code 1.74+ auto-generates events for most contribution points, so this array is usually short. Avoid `"*"` (load-on-startup) — it tanks startup time and is grounds for marketplace rejection of large extensions. |
| `contributes` | Static declarations of commands, menus, keybindings, languages, grammars, themes, settings, views, etc. | Each contribution point has its own schema; see https://code.visualstudio.com/api/references/contribution-points. |
| `capabilities.untrustedWorkspaces` | Declares behavior in restricted-trust workspaces. | `{ "supported": true \| false \| "limited", "description": "..." }`. Required for the extension to load at all in untrusted workspaces; declaring `false` is fine but be honest about it. |
| `capabilities.virtualWorkspaces` | Declares behavior in virtual workspaces (e.g. GitHub repo opened in `vscode.dev`). | Same shape as `untrustedWorkspaces`. |
| `extensionKind` | Where the extension runs in Remote Development setups (SSH, WSL, Containers). | Array of `"ui"` (runs on the local UI side) and/or `"workspace"` (runs in the remote workspace). `["workspace", "ui"]` means "prefer workspace, fall back to UI". Affects nothing on local-only installs. |
| `l10n` | Path to a directory of localization bundles. | Typically `"./l10n"`. Combined with `vscode.l10n` API. |

## Dependency / packaging fields

| Field | Purpose | Notes |
|---|---|---|
| `extensionDependencies` | Other extensions that must be installed for this one to work. | Array of `<publisher>.<name>` IDs. Installing this extension also installs the deps. Use sparingly — it creates install-graph coupling and forks behavior across registries (an Open VSX install can't depend on a Marketplace-only extension). |
| `extensionPack` | Bundles multiple extensions together as a single install. | Array of `<publisher>.<name>` IDs. Extension Packs must also set `"categories": ["Extension Packs"]`. The pack itself usually has no `main` or code. |
| `dependencies` | npm runtime deps. | Standard npm semantics. Bundled extensions don't ship `node_modules/` — see `references/bundling.md`. |
| `devDependencies` | npm dev deps. | `vsce` auto-excludes these from the `.vsix`, so they don't need to be in `.vscodeignore`. |
| `scripts.vscode:prepublish` | Runs automatically before `vsce package` / `vsce publish`. | Where the build/bundle invocation belongs. Must be idempotent — do not run `npm install` here. |
| `scripts.vscode:uninstall` | Runs when the user uninstalls the extension. | Only Node.js scripts are honored. Use for cleanup (deleting cached files, etc.). Don't rely on it running — if VS Code crashes or the user wipes the extensions folder, it won't fire. |

## Worked example

A minimal but publish-ready manifest for a bundled extension that targets both desktop and web:

```json
{
  "name": "wordcount",
  "displayName": "Word Count",
  "description": "Reports word count in Markdown files.",
  "version": "0.1.0",
  "publisher": "ms-vscode",
  "engines": { "vscode": "^1.84.0" },
  "categories": ["Other"],
  "keywords": ["markdown", "wordcount"],
  "icon": "images/icon.png",
  "galleryBanner": { "color": "#C80000", "theme": "dark" },
  "license": "MIT",
  "main": "./dist/extension-node.js",
  "browser": "./dist/extension-web.js",
  "activationEvents": ["onLanguage:markdown"],
  "contributes": {
    "commands": [
      { "command": "wordcount.count", "title": "Word Count: Count selection" }
    ]
  },
  "capabilities": {
    "untrustedWorkspaces": { "supported": true },
    "virtualWorkspaces": { "supported": true }
  },
  "scripts": {
    "vscode:prepublish": "npm run package",
    "package": "npm run check-types && node esbuild.js --production",
    "check-types": "tsc --noEmit"
  },
  "repository": { "type": "git", "url": "https://github.com/microsoft/vscode-wordcount.git" },
  "bugs": { "url": "https://github.com/microsoft/vscode-wordcount/issues" },
  "homepage": "https://github.com/microsoft/vscode-wordcount#readme"
}
```

## Validation gotchas

- **`repository` as a string** parses fine but breaks `vsce publish <semver>`'s automatic git-tag step. Always use the object form.
- **`engines.vscode` not pinned**: a bare `"*"` is rejected; an unrealistically old floor (`^1.0.0`) renders fine but is dishonest — VS Code uses this to gate updates, so pin it at a version you actually test against.
- **`keywords` over 30**: returns `You exceeded the number of allowed tags of 30`. Trim and republish.
- **`icon` is SVG**: rejected at package time. Re-export to PNG ≥ 128×128.
- **`main` still pointing at un-bundled output after adopting a bundler**: extension publishes "successfully" but ships the wrong file. Run `vsce ls` and verify the listing matches what the bundler produced.
- **Missing `browser` entry on a web-relevant extension**: extension installs in `vscode.dev` but never activates. If the extension claims `Web` capability or you want it on browser-hosted IDEs, both `main` and `browser` must be set and the corresponding bundle must exist.
- **`extensionDependencies` to an extension that exists only on Marketplace**: that extension's Open VSX install will fail because the dep can't be resolved. Either remove the hard dep, or publish a forked manifest with the dep removed for Open VSX (rare).
- **Activation event `"*"`** in modern extensions: VS Code 1.74+ auto-generates activation events for most contribution points, so `"*"` is almost always wrong. Replace with the specific `onLanguage:`, `onCommand:`, `onView:`, etc. event.
