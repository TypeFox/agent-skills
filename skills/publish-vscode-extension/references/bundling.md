# Bundling a VS Code extension

Bundling collapses the extension's source files and its `node_modules` runtime dependencies into a single JavaScript file (typically `dist/extension.js`). It is not the same step as TypeScript compilation — `tsc` turns TS into JS but doesn't merge files or resolve dependencies, so a non-bundled extension still ships its full `node_modules` tree in the `.vsix`.

Three reasons it matters for publishing:

1. **Web Extensions require it.** VS Code for Web (`vscode.dev`, `github.dev`) and Theia/Gitpod web hosts can only load extensions whose entry point is a single bundled file. An unbundled extension ships fine to Marketplace/Open VSX but silently fails to activate in any browser-hosted host. If "Web" is in the extension's `categories` or the manifest declares `"browser"`, bundling is a hard requirement.
2. **Activation latency.** VS Code loads the extension's main file synchronously during activation. Loading one ~200 KB bundle is consistently 5-10× faster than walking 100+ small files in `node_modules/`.
3. **`.vsix` size.** Bundling typically cuts the `.vsix` by an order of magnitude because tree-shaking and minification drop unreachable code, and dev-only branches of dependencies disappear.

If the extension is being published and isn't bundled yet, raise it as a recommendation — especially before the first publish, because adding bundling later is mechanical but changes the on-disk layout (so `.vscodeignore` and `package.json#main` both have to move with it).

## Pick a bundler

Two are worth using in 2025+; both are well-supported by `vsce`:

- **esbuild** — recommended for new extensions. ~10–100× faster builds, simpler config, drops in cleanly. Cost: strips TypeScript types without checking them, so you must run `tsc --noEmit` separately for type safety.
- **webpack** — recommended only when migrating an existing webpack-based extension, or when the extension needs a loader ecosystem feature esbuild doesn't have (e.g. complex asset pipelines). Slower builds, more config surface.

Rollup and Parcel work but are uncommon in the extension ecosystem; prefer esbuild unless the user already has rollup configured.

## Wiring into `vsce`

`vsce package` runs the `vscode:prepublish` npm script before zipping the `.vsix`. The bundler invocation belongs there:

```json
{
  "main": "./dist/extension.js",
  "scripts": {
    "vscode:prepublish": "npm run package",
    "package": "npm run check-types && node esbuild.js --production",
    "check-types": "tsc --noEmit",
    "compile": "npm run check-types && node esbuild.js",
    "watch": "npm-run-all -p watch:*",
    "watch:esbuild": "node esbuild.js --watch",
    "watch:tsc": "tsc --noEmit --watch --project tsconfig.json"
  }
}
```

Three things that catch people out here:

- **`package.json#main` must point at the bundle output** (e.g. `./dist/extension.js`), not at the TypeScript source or the un-bundled `out/extension.js`. VS Code will load whatever `main` says — if it's the un-bundled path, all that bundling effort is wasted.
- **`vscode:prepublish` runs every time `vsce package` runs**, including in CI. Make it idempotent and don't put `npm install` in it — assume dependencies are already installed.
- **Type checking has to be separate.** esbuild strips types without checking; webpack with `transpileOnly: true` (a common speedup) does the same. Run `tsc --noEmit` as part of `package`/`prepublish` so a broken type doesn't ship.

## esbuild setup

```bash
npm install --save-dev esbuild npm-run-all
```

`esbuild.js`:

```javascript
const esbuild = require('esbuild');

const production = process.argv.includes('--production');
const watch = process.argv.includes('--watch');

async function main() {
  const ctx = await esbuild.context({
    entryPoints: ['src/extension.ts'],
    bundle: true,
    format: 'cjs',
    minify: production,
    sourcemap: !production,
    sourcesContent: false,
    platform: 'node',
    outfile: 'dist/extension.js',
    external: ['vscode'],
    logLevel: 'warning',
  });
  if (watch) {
    await ctx.watch();
  } else {
    await ctx.rebuild();
    await ctx.dispose();
  }
}

main().catch(e => { console.error(e); process.exit(1); });
```

`external: ['vscode']` is **mandatory** — see "Externalizing `vscode`" below.

For Web Extensions, change `platform: 'node'` to `platform: 'browser'` and ship a second entry under `package.json#browser` pointing at the browser bundle (the Node bundle stays under `main`).

## webpack setup

```bash
npm install --save-dev webpack webpack-cli ts-loader
```

`webpack.config.js`:

```javascript
const path = require('path');

module.exports = {
  target: 'node',                              // 'webworker' for Web Extensions
  entry: './src/extension.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'extension.js',
    libraryTarget: 'commonjs2',
    devtoolModuleFilenameTemplate: '../[resource-path]',
  },
  devtool: 'source-map',
  externals: { vscode: 'commonjs vscode' },
  resolve: {
    mainFields: ['browser', 'module', 'main'],  // browser-first for Web targets
    extensions: ['.ts', '.js'],
  },
  module: {
    rules: [{ test: /\.ts$/, exclude: /node_modules/, use: ['ts-loader'] }],
  },
};
```

Scripts:

```json
{
  "vscode:prepublish": "npm run package",
  "package": "webpack --mode production --devtool hidden-source-map",
  "compile": "webpack --mode development",
  "watch": "webpack --mode development --watch"
}
```

`hidden-source-map` keeps stack traces useful internally while not shipping the `.map` to the marketplace.

## Externalizing the `vscode` module

The `import vscode from 'vscode'` API is provided by VS Code itself at runtime — there is no `node_modules/vscode/` package with the implementation. The `@types/vscode` package supplies types only. Bundlers must be told to leave `vscode` as an external import:

- esbuild: `external: ['vscode']`
- webpack: `externals: { vscode: 'commonjs vscode' }`

Skipping this produces a build error like "Could not resolve 'vscode'" or, worse, accidentally bundles a stale copy that breaks at activation.

If the extension uses other host-provided modules (rare — `keytar` used to be one), externalize them the same way and add a non-ignored copy under `node_modules/` in `.vscodeignore` (see below).

## `.vscodeignore` for bundled extensions

After bundling, the `.vsix` should contain `dist/extension.js`, the manifest, README, LICENSE, and the icon — and basically nothing else. A minimal `.vscodeignore`:

```
.vscode/**
.vscode-test/**
.github/**
src/**
out/**
test/**
**/*.ts
**/*.map
**/tsconfig*.json
**/.eslintrc*
**/*.test.js
esbuild.js
webpack.config.js
node_modules/**
```

Counter-intuitive part: `node_modules/**` is excluded **because the bundle already contains everything from it**. If an externalized module needs to ship (rare), un-ignore it: `!node_modules/keytar/**`. Verify with `vsce ls` — if you see your dependencies' source trees in the listing, the bundle isn't being picked up.

## Web Extensions

If the extension declares `"browser"` in `package.json` or sets `Web` in `categories`, the bundle has to target browser environments:

- esbuild: `platform: 'browser'`, and avoid Node-only APIs (`fs`, `path`, `child_process`, etc.) in the source.
- webpack: `target: 'webworker'`, plus `resolve.mainFields: ['browser', 'module', 'main']` so npm packages pick their browser-compatible entry points.

`package.json` ships both entries when an extension supports both desktop and web:

```json
{
  "main": "./dist/extension-node.js",
  "browser": "./dist/extension-web.js"
}
```

Web hosts (vscode.dev, github.dev, the Open VSX-fed Theia browser hosts) load `browser`; desktop loads `main`. Build both with separate bundler invocations in `package`/`vscode:prepublish`.

## Minification and source maps

- **Minification on**: turn on for production (`minify: production` / `--mode production`). Saves significant bytes.
- **Minification breaks code that relies on `Function.prototype.name`** — class names get mangled. Most VS Code extensions are safe, but if the extension uses reflection or a DI container that looks up types by class name, either disable minification or configure the bundler to keep names (esbuild: `keepNames: true`; webpack: `optimization.minimizer` with `terserOptions: { keep_classnames: true, keep_fnames: true }`).
- **Source maps**: ship hidden source maps in production so stack traces are debuggable but the maps aren't visible to users. esbuild: `sourcemap: true, sourcesContent: false` and exclude the `.map` from the `.vsix` via `.vscodeignore`. webpack: `--devtool hidden-source-map`.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Extension activates locally but doesn't appear in `vscode.dev` / `github.dev` | Not bundled, or `package.json#browser` missing | Bundle for `browser`/`webworker` target and add the `browser` entry. |
| `Cannot find module 'vscode'` at build time | `vscode` not externalized | Add `external: ['vscode']` (esbuild) or `externals: { vscode: 'commonjs vscode' }` (webpack). |
| Activation throws `Cannot find module '<dep>'` after publish | A runtime dep got tree-shaken or wasn't bundled; `node_modules` is ignored in `.vscodeignore` | Either ensure the dep is reachable from `entryPoints`, or externalize it and un-ignore it in `.vscodeignore`. |
| webpack: `Critical dependency: the request of a dependency is an expression` | A `require(variable)` the bundler can't statically resolve | Refactor to a static `require`, or externalize the module and ship it via `.vscodeignore`. |
| `.vsix` is 30 MB+ for a small extension | Bundling not actually running (`vscode:prepublish` not wired up, or `main` still points at unbundled output) | Run `vsce ls` and look for `node_modules/**` in the listing; check `main`. |
| TypeScript type error reached production | Bundler strips types without checking | Add `tsc --noEmit` to the `package`/`vscode:prepublish` script chain. |
| Class-based DI breaks only after publish | Minifier renamed classes | Enable `keepNames` / `keep_classnames`, or disable minification. |
| Icons, snippets, or other static files missing at runtime | Bundler doesn't copy non-JS assets; `.vscodeignore` may exclude them too | Reference assets via `vscode.Uri.joinPath(context.extensionUri, ...)` and ensure those files are NOT excluded by `.vscodeignore`. Bundlers do not copy them by default; either copy via a build step or leave them outside `dist/`. |

## Inspecting the bundle before publish

Before the first publish — and any time `.vscodeignore` or the bundler config changes — run:

```bash
vsce ls         # list every file that will be in the .vsix
vsce package    # actually build it
unzip -l <name>-<version>.vsix   # double-check the zip contents
```

If you see `src/`, `node_modules/<your-deps>/`, or multiple JS files where there should be one, the bundle isn't being shipped correctly and the next publish will be the slow, oversized one.
