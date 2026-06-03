---
name: publish-vscode-extension
description: Prepare and publish a VS Code extension to the VS Code Marketplace and/or the Open VSX Registry. Use whenever the user wants to publish, ship, release, or re-publish a VS Code extension; build or upload a `.vsix`; set up `vsce` or `ovsx`; create a marketplace publisher or an Open VSX namespace; configure CI for extension releases; bump versions for an extension; or troubleshoot publishing errors. Covers both registries because most production extensions ship to both — invoke even if the user names only one of them.
---

# Publish a VS Code extension

There are two registries where VS Code extensions live:

- **VS Code Marketplace** — Microsoft's registry. Consumed by VS Code, Visual Studio, and Azure DevOps. Authenticated with an Azure DevOps Personal Access Token (PAT). Tooling: `@vscode/vsce`.
- **Open VSX Registry** — the Eclipse Foundation's open-source registry at https://open-vsx.org. Consumed by VS Codium, Gitpod, Theia-based IDEs, Cursor, Windsurf, code-server, and most non-Microsoft forks. Authenticated with a token issued by open-vsx.org after accepting the Eclipse Publisher Agreement. Tooling: `ovsx`.

Most production extensions publish to **both**. The same `.vsix` file works on either registry, so the recommended flow is *package once with `vsce`, then publish that artifact to each registry*. Don't fall into publishing only to Marketplace — non-Microsoft VS Code distributions can't see those extensions.

When more context is needed, load:

- `references/manifest.md` — the full `package.json` extension manifest: every required, recommended, and runtime field, the allowed `categories` list, marketplace presentation fields (`galleryBanner`, `preview`, `badges`, `pricing`, `sponsor`, `qna`), runtime fields (`main`, `browser`, `activationEvents`, `contributes`, `capabilities`, `extensionKind`), dependency fields (`extensionDependencies`, `extensionPack`), and validation gotchas. Read whenever you're editing `package.json`, troubleshooting "field X was rejected" errors, or auditing an unfamiliar extension's manifest.
- `references/vscode-marketplace.md` — Azure DevOps PAT, publisher creation, `vsce` commands, verified publisher, unpublishing, common 401/403 errors. Read whenever a step involves Marketplace authentication, publisher identity, or `vsce`-specific flags.
- `references/open-vsx.md` — Eclipse account setup, the Publisher Agreement, access tokens, namespace ownership and the "unverified" warning, `ovsx` commands, CI integration. Read whenever a step involves Open VSX, namespaces, or `ovsx`.
- `references/bundling.md` — why and how to bundle the extension with esbuild or webpack, wiring into `vscode:prepublish`, externalizing the `vscode` module, Web Extension targets, `.vscodeignore` for bundled extensions. Read whenever the extension isn't bundled yet, ships to Web hosts (`vscode.dev`, `github.dev`), is unexpectedly large, or has a slow activation time.

## Decide what to publish to

If the user hasn't said, default to **both** registries and tell them. The marginal cost of also publishing to Open VSX is small (one token + one namespace) and the audience reached is large. Only skip Open VSX if the extension explicitly depends on proprietary Marketplace-only APIs or telemetry that wouldn't be appropriate for open-source distributions — and even then, say so explicitly.

## Prerequisites that apply to both registries

Install Node.js, then install the publishing CLIs:

```bash
npm install -g @vscode/vsce ovsx
```

`vsce` (the "VS Code Extension manager") is the canonical packager. `ovsx` reuses `vsce` internally for packaging-from-source, so installing both is the normal setup. `npx @vscode/vsce` / `npx ovsx` also work if you'd rather not install globally.

## Prepare the extension

Before publishing anywhere, make sure the extension is publish-ready. These are the same requirements for both registries — the registries reject or downrank extensions that fail them.

### `package.json` manifest

A minimal publish-ready manifest looks like:

```json
{
  "name": "extension-name",
  "displayName": "Human Readable Name",
  "description": "One sentence about what this extension does",
  "version": "0.0.1",
  "publisher": "<publisher-id-or-namespace>",
  "engines": { "vscode": "^1.84.0" },
  "categories": ["Other"],
  "keywords": ["tag1", "tag2"],
  "icon": "icon.png",
  "repository": { "type": "git", "url": "https://github.com/user/repo" },
  "license": "MIT",
  "bugs": { "url": "https://github.com/user/repo/issues" },
  "homepage": "https://github.com/user/repo#readme"
}
```

Four required fields: `name`, `version`, `publisher`, `engines.vscode`. Everything else is technically optional but the registry listing will look broken without `displayName`, `description`, `categories`, `icon`, `repository`, and `license`.

Two cross-cutting things to know up front:

- `publisher` is the same string on both registries by convention, but they're two independent identity systems — registering `acme` on Marketplace does *not* reserve `acme` on Open VSX, and vice versa. Register both names early to avoid squatters.
- `engines.vscode` must be a real published VS Code version range (e.g. `^1.84.0`). Wildcards (`*`) are rejected.

For the full field reference — allowed `categories` values, marketplace presentation fields (`galleryBanner`, `preview`, `badges`, `pricing`, `sponsor`), runtime fields (`main`, `browser`, `activationEvents`, `contributes`, `capabilities`, `extensionKind`), dependency fields (`extensionDependencies`, `extensionPack`), and the validation gotchas (icon constraints, 30-keyword limit, `repository` object vs string, etc.) — read `references/manifest.md`.

### Supporting files

- `README.md` — rendered as the extension's marketplace landing page on both registries. Images in it **must use absolute HTTPS URLs**, not relative paths (the registries serve the README from a different origin).
- `LICENSE` — required for unambiguous licensing. Match the `license` field in `package.json` (SPDX identifier like `MIT`, `Apache-2.0`).
- `CHANGELOG.md` — rendered as the "Changelog" tab. Conventional format is Keep-a-Changelog.
- `.vscodeignore` — exclude files from the `.vsix` (glob per line). Source TypeScript, tests, configs, and `node_modules/` dev deps should not ship. Example:
  ```
  .vscode/**
  .vscode-test/**
  src/**
  .gitignore
  .yarnrc
  vsc-extension-quickstart.md
  **/tsconfig.json
  **/.eslintrc.json
  **/*.map
  **/*.ts
  !out/**/*.js
  ```
  `vsce` automatically excludes `devDependencies` declared in `package.json`, so you don't need to list them.

## Package once

Build the `.vsix` from the extension root:

```bash
vsce package
```

This runs the `vscode:prepublish` script (typically a TypeScript or bundler build), validates the manifest, and produces `<name>-<version>.vsix`. Inspect the file list with `vsce ls` before publishing the first time — finding shipped `node_modules/` or `.git/` directories on the marketplace is embarrassing and hard to undo.

If the extension isn't bundled, `vsce package` will warn and the resulting `.vsix` typically ships the full `node_modules/` tree — large, slow to activate, and **unusable in Web hosts like `vscode.dev` and `github.dev`**. Bundling is strongly recommended before the first publish; see `references/bundling.md` for esbuild and webpack setup.

### Recommended workflow: package once, publish twice

When publishing to both registries, **first build the `.vsix` with `vsce package`, then upload that exact same file to each registry** — do not call `vsce publish` and `ovsx publish` against the source tree separately. Reasons this matters:

- **Byte-identical artifact on both registries.** Users get the same hash whether they install from Marketplace or Open VSX, which is what they expect and what reproducibility / supply-chain audits require. Two from-source publishes can produce subtly different zips (timestamps, file ordering, dev-dep resolution at a different second), and you have no easy way to spot the divergence after the fact.
- **One artifact, one version, one git tag.** The thing you tagged in git, the thing in a release attachment, and the thing on each registry are all literally the same file.
- **Inspectable before either registry sees it.** Run `vsce ls` or `unzip -l <name>-<version>.vsix` on the artifact, fix anything wrong, and only then push to the registries.
- **Half the build cost in CI.** One bundler invocation instead of two.

The concrete commands are in the next section; the shape of the recommended flow is:

```bash
vsce package                                           # produces <name>-<version>.vsix
vsce publish --packagePath <name>-<version>.vsix       # → Marketplace
ovsx publish <name>-<version>.vsix                     # → Open VSX, same file
```

Both CLIs do also support package-and-publish-in-one (`vsce publish`, `ovsx publish` with no path argument) — use those only when publishing to a single registry. For dual-registry publishes, always go through a shared `.vsix`.

## Handling access tokens

Publishing requires two long-lived bearer credentials — a **Marketplace PAT** issued by Azure DevOps and an **Open VSX token** issued by open-vsx.org. Both are equivalent in power to an npm publish token: anyone holding one can push code that runs on every install of every extension under that identity. The agent's handling of these values is the security boundary, so treat this section as a precondition for every publish step below.

**If the user pastes a token directly into the prompt** — stop before running anything. The token is now in the conversation transcript, which may be persisted, logged, or replayed. Tell the user to:

1. Revoke that token immediately:
   - **Marketplace PAT** → https://dev.azure.com → avatar → **User settings** → **Personal access tokens** → revoke.
   - **Open VSX token** → https://open-vsx.org → avatar → **Settings** → **Access Tokens** → revoke.
2. Mint a new one and provide it via the harness's secret-handling mechanism if one exists, or otherwise via an environment variable in the shell that launches the agent:
   - `export VSCE_PAT=...` for Marketplace.
   - `export OVSX_PAT=...` for Open VSX.

Do not proceed using the pasted value.

**Otherwise**, expect the tokens to live in environment variables and let the CLIs pick them up by name. Both tools already read these names natively, so the command line should contain neither the token value nor an explicit `-p` flag with the variable substituted in:

- `vsce` reads `VSCE_PAT` automatically; just run `vsce publish …`.
- `ovsx` reads `OVSX_PAT` automatically; just run `ovsx publish …`.

If the user wants to keep different names (e.g., for a multi-publisher setup), reference them by name (`-p "$MY_PAT"`), never by value. Do not echo, log, write to a file, paste into a commit, or include the value in the summary reported back to the user.

Before running anything that needs a token, confirm the variable is actually set in the same shell that will run the tool — `[ -n "$VSCE_PAT" ]` and `[ -n "$OVSX_PAT" ]`, **do not print the value**. A token exported in another terminal won't be visible here. If a variable is missing, ask the user to set it; do not ask them to paste it.

If the agent harness has a built-in secret/credential mechanism (an injected env var, a secret-resolution step, etc.), prefer that over a plain shell variable.

The `vsce login` / `ovsx login` flows store tokens in the OS keychain after an interactive prompt. That path is fine when the **user** is running the CLI on their own machine — the value never enters the chat. It is **not** appropriate when the agent is doing the publishing, because the agent can't usefully interact with a `Password:` prompt and shouldn't be feeding the value into one anyway. Use the env-var path instead.

## Publish

With `VSCE_PAT` and `OVSX_PAT` set in the environment (see above) and following the "package once, publish twice" recommendation:

```bash
# build a single .vsix
vsce package

# publish that file to each registry — tokens come from the env vars
vsce publish --packagePath <name>-<version>.vsix
ovsx publish <name>-<version>.vsix
```

Both commands accept the same `.vsix` because the registries treat it as an opaque artifact; the manifest inside the zip identifies which `<publisher>.<name>@<version>` slot it belongs to on each side.

## Versioning

Both registries enforce monotonically increasing SemVer per extension. You cannot republish the same version — bump first.

`vsce` can do the bump-commit-tag for you on a clean git tree:

```bash
vsce publish patch          # 1.0.0 → 1.0.1
vsce publish minor          # 1.0.0 → 1.1.0
vsce publish major          # 1.0.0 → 2.0.0
vsce publish 1.5.3          # explicit version
vsce publish minor -m "Release v%s"   # custom commit message
```

`ovsx` doesn't have a version-bumping mode — let `vsce` handle the bump, then point `ovsx` at the resulting `.vsix`.

## Pre-release versions

Both registries support a pre-release channel that's installed only when the user opts in (or runs VS Code Insiders):

```bash
vsce package --pre-release
vsce publish --pre-release
ovsx publish <file> --pre-release
```

Requires `engines.vscode >= 1.63.0`. The convention is **odd minor numbers for pre-release, even minor numbers for release** (e.g. `0.3.*` pre-release, `0.4.*` release) — this avoids the pre-release and stable channels colliding when SemVer compares them.

## Platform-specific extensions

If the extension ships native binaries (a debug adapter, a language server in Rust/Go, native node modules), build and publish one `.vsix` per platform:

```bash
vsce package --target win32-x64
vsce package --target darwin-arm64
# … repeat for each target, then publish each artifact

vsce publish --packagePath ./pkgs/*.vsix
ovsx publish ./pkgs/*.vsix
```

Available targets: `win32-x64`, `win32-arm64`, `linux-x64`, `linux-arm64`, `linux-armhf`, `alpine-x64`, `alpine-arm64`, `darwin-x64`, `darwin-arm64`, `web`. A `.vsix` without `--target` is treated as universal and installable everywhere.

## Typical CI release flow

The community-standard GitHub Action is [`HaaLeo/publish-vscode-extension`](https://github.com/HaaLeo/publish-vscode-extension), which wraps both `vsce` and `ovsx`. A minimal release job:

```yaml
- run: npm ci
- run: npx vsce package
  # produces <name>-<version>.vsix
- uses: HaaLeo/publish-vscode-extension@v2
  with:
    pat: ${{ secrets.VSCE_PAT }}
    registryUrl: https://marketplace.visualstudio.com
    extensionFile: ./<name>-<version>.vsix
- uses: HaaLeo/publish-vscode-extension@v2
  with:
    pat: ${{ secrets.OVSX_PAT }}
    extensionFile: ./<name>-<version>.vsix
    # registryUrl defaults to https://open-vsx.org
```

Trigger on tag push (`v*`) rather than every merge, so the version bump is intentional.

## What to do next

- Editing `package.json` or hitting a "field X was rejected" validation error? Read `references/manifest.md`.
- Going to authenticate or troubleshoot a Marketplace publish? Read `references/vscode-marketplace.md`.
- Going to register an Open VSX namespace, deal with the unverified-publisher warning, or set up an Eclipse account? Read `references/open-vsx.md`.
- Extension isn't bundled yet, or needs Web Extension support? Read `references/bundling.md` before the next publish.
- Don't know whether the user has identity on either registry yet? Ask before issuing token-creation steps — registering a publisher is a permanent ID claim, and they may already have one under a different account.
