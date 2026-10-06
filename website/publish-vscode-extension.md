# Publish VS Code Extension

Publish a VS Code extension to the VS Code Marketplace and the Open VSX Registry, from manifest to CI release setup.

Source: [skills/publish-vscode-extension](https://github.com/TypeFox/agent-skills/tree/main/skills/publish-vscode-extension)

## Install

```sh
npx skills add TypeFox/agent-skills -s publish-vscode-extension
```

The skill works with the publishing tools `vsce` and `ovsx`, which run on Node.js.

## Background

VS Code extensions are distributed through two registries. The [VS Code Marketplace](https://marketplace.visualstudio.com/vscode) is run by Microsoft, and its terms of use restrict it to Microsoft products. VSCodium, Cursor, Windsurf, code-server and tools built on Eclipse Theia pull their extensions from the [Open VSX Registry](https://open-vsx.org) instead, a vendor-neutral registry run by the Eclipse Foundation. An extension that is published only to the Marketplace does not exist for any of them.

Each registry has its own tool, account and access token. The Marketplace uses `vsce` with a Personal Access Token from Azure DevOps. Open VSX uses `ovsx` with a token from open-vsx.org, issued after you sign the Eclipse Publisher Agreement. A publisher name registered on one registry is not reserved on the other. Both registries accept the same `.vsix` package, so the usual approach is to package once and upload that one file to both.

The publishing process itself is documented by the registries:

- [Publishing Extensions](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) in the VS Code docs covers `vsce`, the Marketplace publisher account, versioning and pre-releases.
- [Extension Manifest](https://code.visualstudio.com/api/references/extension-manifest) lists the `package.json` fields that make up a listing.
- [Bundling Extensions](https://code.visualstudio.com/api/working-with-extensions/bundling-extension) explains why an extension should ship as one bundled file.
- [Publishing Extensions](https://github.com/eclipse/openvsx/wiki/Publishing-Extensions) in the Open VSX wiki covers the Eclipse account, namespaces and `ovsx`.

## Usage

The skill activates when you want to publish, release or ship a VS Code extension, prepare one for its first release, set up a release workflow, or find out why a publish failed. It considers both registries even if you name only one.

> Audit this extension for publish-readiness. Dry run only, do not publish.

> Write a GitHub Actions workflow that releases this extension to the Marketplace and Open VSX on every version tag.

> Our release job gets a 401 from the Marketplace, and Open VSX shows the extension as unverified. What is wrong?

Most sessions prepare a release rather than run one, and the skill keeps the two apart. It does not run a publish command or ask for tokens unless you ask it to publish.

- **Audit the manifest and listing.** The skill checks `package.json` for the required fields and for the ones a listing looks broken without, the README for relative image links the registries cannot serve, and `.vscodeignore` for sources and dev dependencies that would end up in the package. An unbundled extension ships its whole `node_modules` tree and does not run on vscode.dev or github.dev. The skill points that out and sets up esbuild or webpack bundling when you want it.
- **Set up the release workflow.** The recommended setup is a GitHub Actions workflow that runs on version tags from a protected branch and uses the [gh-publish-npm](https://github.com/TypeFox/gh-publish-npm) action. The action packages once, uploads the same `.vsix` to both registries, skips a registry that already has the version, and masks tokens in its logs.
- **Publish on request.** For a one-off publish from your machine, the skill settles the target registries with you, packages the extension, inspects the file list, checks that the tokens are set, and uploads the one package to each registry. It also handles version bumps, pre-release versions, and platform-specific packages for extensions with native binaries.
- **Diagnose failures.** The skill knows the usual causes: a token scoped to one Azure DevOps organization instead of all of them, a publisher created under a different Microsoft account than the token, an unsigned Publisher Agreement, an Open VSX namespace without an owner, or a version that is already published.

### Access tokens

Never paste a token into the chat. The conversation may be stored or logged, and a publish token lets its holder push code that runs with full IDE privileges on every install of your extension. Put the tokens in environment variables named `VSCE_PAT` and `OVSX_PAT` in the shell that starts your agent. Both tools read these names on their own, so the value never appears on a command line. If you paste a token anyway, the skill stops and asks you to revoke it first.
