---
name: eclipse-license-check
description: Vet third-party dependencies for an Eclipse Foundation project with the Eclipse Dash License Tool — license checks, "do I need to vet X?" questions, IPLab review filing, and release IP due diligence. Use whenever the user mentions Eclipse license checking, dash-licenses, the Dash License Tool, IPLab, third-party content for an Eclipse release, or dependency approval under the Eclipse IP Policy, even if they don't name the tool. Do not use for non-Eclipse projects or general license advice unrelated to the Eclipse IP Policy.
---

# Eclipse Dependency License Check

Vet the project's third-party dependencies with the [Eclipse Dash License Tool](https://github.com/eclipse-dash/dash-licenses). The **`restricted`** list in the summary CSV is the deliverable — what still needs IP Team attention before a formal release.

Load references only when a pointer below fires:

- `references/intellectual-property.md` — scope questions ("do I need to vet X?", platform boundary, test/build exemptions, manual IPLab issue format).
- `references/dash-license-tool.md` — before invoking the tool (install, flags, per-ecosystem recipes, errors, CI).

## Optional inputs

1. **A local clone of `eclipse-dash/dash-licenses`** — use it when given; otherwise download the released CLI jar per `references/dash-license-tool.md`.
2. **An IPLab access token** — a `gitlab.eclipse.org` personal access token with `api` scope. Needed only to file IPLab review requests automatically. Treat the token as a secret; see "Handling the IPLab token" below.

If neither was mentioned, proceed with the released jar and without filing reviews — do not prompt.

## Preflight: preparing a local Dash License Tool clone

If the user provided a clone path, prepare it before any check runs. The user may have work in progress, so **do not modify unfamiliar state**.

1. Inspect: `git -C <path> status --porcelain` and `git -C <path> rev-parse --abbrev-ref HEAD`.
2. **Clean tree on `master`**: if `shaded/target/org.eclipse.dash.licenses-*.jar` already exists, use it directly. Otherwise `git -C <path> pull --ff-only`, then `mvn -f <path> -DskipTests clean install`. The `install` goal places both the CLI jar and the Maven plugin into `~/.m2` so later invocations resolve them locally. Drop `-DskipTests` only to validate the tool itself — the suite hits external services and adds minutes.
3. **Only IDE/OS noise dirty** (e.g. `.DS_Store`, modifications under `.settings/` which Eclipse IDE auto-edits on project open, `.idea/`): none of this is real WIP. Offer to discard those paths and continue as in step 2; don't act unilaterally.
4. **Anything else** (modified source/build files, untracked code, other branch, detached HEAD): report what was observed and ask how to proceed.

After a successful build, use the **shaded** jar at `shaded/target/org.eclipse.dash.licenses-<version>.jar` (read `<version>` from the build output — typically `<x.y.z>-SNAPSHOT` on a master clone). The thin jar in `core/target/` is `...licenses.core-<version>.jar` and lacks transitive deps, so it fails at runtime with `NoClassDefFoundError`. Alternatively invoke the now-installed Maven plugin as `org.eclipse.dash:license-tool-plugin:license-check`.

**Done when** a runnable jar or installed Maven plugin is confirmed; otherwise stop and report.

## Handling the IPLab token

The Dash License Tool only accepts the token as a CLI argument — there is no env-var or stdin path — so the token value must reach the command line. The agent's handling of the value is the security boundary.

**If the user pastes the token directly into the prompt** — stop before running anything. The token is now in the conversation transcript, which may be persisted, logged, or replayed. Tell the user to:

1. Revoke that token at https://gitlab.eclipse.org/-/user_settings/personal_access_tokens.
2. Mint a new one and provide it via the harness's secret-handling mechanism if one exists, or otherwise via an environment variable (e.g., `export IPLAB_TOKEN=...` in the shell that launches the agent).

Do not proceed using the pasted value.

**Otherwise**, expect the token to live in an environment variable — default to the name `IPLAB_TOKEN` unless the user named a different one — and reference it by name on the command line, never substituting in the value:

- CLI: `-token "$IPLAB_TOKEN"`
- Maven plugin: `-Ddash.iplab.token="$IPLAB_TOKEN"`

If the agent harness has a built-in secret/credential mechanism (an injected env var, a secret-resolution step, etc.), prefer that over a plain shell variable.

Before running, confirm the variable is set in the same shell that will run the tool (`[ -n "$IPLAB_TOKEN" ]` — do not print the value). A token exported in another terminal won't be visible here. Never echo, log, write to a file, or commit the token. Do not include it in the summary reported back to the user.

## IPLab review filing

The `-review` flow files real GitLab issues against `eclipsefdn/emo-team/iplab` that the Eclipse IP Team acts on — a public, irreversible action. Choose based on explicit user intent (see `references/dash-license-tool.md` § Filing automatic IP review requests):

- **User wants reviews AND provided a token** → enable filing (flags below).
- **User has said no reviews** → never pass `-review`. Restricted content still appears in the summary.
- **Intent unclear** → ask before running. Do not silently default.

The Eclipse project ID (e.g., `technology.dash`, `ecd.theia`) is required for `-review`. Ask if not supplied — do not guess from directory or repo names.

**When filing is enabled**, append to every invocation:

- CLI: `-review -token "$IPLAB_TOKEN" -project <project-id>` (and `-repo <url>` when known)
- Maven plugin: `-Ddash.iplab.token="$IPLAB_TOKEN" -Ddash.projectId=<project-id>` (and `-Ddash.repo=<url>` when known)

Derive `-repo` / `-Ddash.repo` from `git remote get-url origin`, converting SSH forms like `git@github.com:org/repo.git` to `https://github.com/org/repo`. See "Handling the IPLab token" for how the token value reaches the command. For CLI runs, capture stdout — IPLab issue URLs print there, not in the CSV. At most five issues are filed per invocation; re-run if more `restricted` entries remain (see `references/dash-license-tool.md` § Filing).

## Running the check

Each **dependency graph** gets its own run and summary CSV — root manifest first, then any nested graphs the root run didn't cover.

1. **Root** — identify the ecosystem from manifest files at the project root and follow the matching subsection below. Run from that directory (or pass absolute paths).
2. **Nested graphs** — Open source repos often ship more than one ecosystem (Go library + VS Code extension, Java core + npm website). After the root run, find additional lockfiles not yet checked:
   ```bash
   find . \( -name package-lock.json -o -name yarn.lock -o -name pnpm-lock.yaml -o -name go.sum -o -name Cargo.lock \) \
     -not -path '*/node_modules/*' -not -path '*/vendor/*' -not -path '*/.git/*'
   ```
   Skip the lockfile already fed in step 1. Run each remaining lockfile from its directory with a distinct `-summary` name (e.g. `DEPENDENCIES-vscode`), using the matching ecosystem subsection below.

Always pass `-summary <path>`; pick a name that won't collide with tracked files (some Eclipse projects commit a `DEPENDENCIES` file). When IPLab filing is enabled, append flags per "IPLab review filing" above.

**Done when** a summary CSV exists for every discovered dependency graph. Non-zero exit code equals the restricted count (capped at 126) — that is success with findings, not a tool failure. Continue to "Reporting findings".

### TypeScript / JavaScript (npm, yarn, pnpm)

**Trigger**: a `package.json` in the directory being checked (root or nested).

The tool parses `package-lock.json`, `yarn.lock`, and `pnpm-lock.yaml` natively — feed the lock file directly:

```bash
java -jar <dash-jar> -summary DEPENDENCIES package-lock.json
# or yarn.lock, or pnpm-lock.yaml
```

**No lock file**: dependencies aren't pinned, so a meaningful check isn't possible. Ask the user to run `npm install` / `yarn install` / `pnpm install` first. Don't run against `package.json` alone.

**Multiple lock files**: a misconfiguration. Ask which package manager is authoritative — running both double-counts.

**Lock file freshness**: assume up to date. Only regenerate if the user says it's stale.

**Yarn parser caveat**: the native `yarn.lock` parser is fragile (the format is undocumented). If the run errors, returns suspiciously few entries, or the user reports a recent yarn version, fall back to the `yarn info -R --name-only` pipeline in `references/dash-license-tool.md` § Yarn (when the lockfile parser fails).

**Workspace coverage**: only deps reachable from the lock file you pass are checked. In a monorepo, the root lock file covers every package listed in `workspaces` (or `pnpm-workspace.yaml`); sibling packages outside that list keep their own graphs and need separate runs. Workspace members linked via `file:` or `workspace:` are not registry coordinates — they won't appear in the summary; only published third-party deps are vetted.

**Triaging restricted entries**: lock files mix runtime, dev, and transitive deps without preserving that context, so the tool vets them all. When a restricted entry surfaces, recover the context the user needs to act on it:

- Parse the CSV identifier to a package name: `npm/npmjs/-/name/version` → `name`; `npm/npmjs/@scope/name/version` → `@scope/name`.
- Run `yarn why <pkg>` (or `npm ls <pkg>` / `pnpm why <pkg>`) to trace the chain — the entry may be transitive and absent from any `package.json`.
- For direct entries, grep the root `package.json` plus every workspace package's `package.json` to find which key (`dependencies` / `devDependencies`) declares it.

Surface both in the report. The Eclipse exemption hinges on whether the content is **distributed** via an `eclipse.org` property — not on the JSON key alone (see `references/intellectual-property.md` § Test and build dependencies). A `devDependency` used only at build time qualifies; so does a `dependency` of an example or demo the project never publishes. Conversely, a `devDependency` that ends up bundled into a shipped artifact does need review.

**Upstream-project content**: when a `restricted` entry is from the same organization as the repo under review, or from another Eclipse Foundation project — npm packages like `langium`, `theia`, `sprotty`, or a sibling module like `typefox.dev/lsp` in a TypeFox repo — the cause is usually a missing Dash Database entry for that exact coordinate, not a real licensing problem. The tool has no org-ownership lookup for npm or Go (Maven projects sidestep Eclipse deps with `-DexcludeGroupIds=org.eclipse`; npm has no such prefix convention). Let `-review` file the IPLab issue anyway and explain in the report that the IP Team typically closes these as already-vetted under the upstream project's own IP review; that resolution itself adds the coordinate to the Dash Database, so future runs return `approved`.

**Extension publish tooling**: `@vscode/vsce-sign-*` platform packages at the same version are signing binaries for `vsce package` — a single cohort, usually build-only. Same for `@azure/msal-*` and `@textlint/*` cohorts pulled in transitively by `vsce` / `ovsx`.

### Java (Maven, p2 / Tycho)

**Trigger**: a `pom.xml` at the project root.

**Identify the build flavor**:

- **Standard Maven**: `jar`/`war`/`pom` packaging.
- **Tycho / p2**: any module pom.xml declares an `eclipse-*` packaging type (`eclipse-plugin`, `eclipse-feature`, `eclipse-repository`, `eclipse-application`, `eclipse-test-plugin`, `eclipse-target-definition`), or a `.target` file exists anywhere in the repo. Tycho resolves p2 bundles through the Target Platform, not through standard Maven resolution.

**Always use the Dash Maven plugin** — it walks the Reactor and, with the Tycho flag, p2 dependencies too. The CLI fallback (`mvn dependency:list` piped to the jar) does **not** see p2 dependencies; never use it for Tycho/p2 (silently incomplete results).

```bash
mvn org.eclipse.dash:license-tool-plugin:license-check -Ddash.summary=DEPENDENCIES
```

For **Tycho / p2**, also pass `-Dtycho.target.eager=true` — without it Tycho resolves lazily and the plugin sees only a fraction of dependencies:

```bash
mvn org.eclipse.dash:license-tool-plugin:license-check -Ddash.summary=DEPENDENCIES -Dtycho.target.eager=true
```

**Plugin not resolvable**: if Maven reports `Plugin org.eclipse.dash:license-tool-plugin ... could not be resolved`, the Eclipse plugin repository isn't configured. Fix by either (a) adding `repo.eclipse.org` to `pluginRepositories` (snippet in `references/dash-license-tool.md` § Getting the tool), or (b) building a local clone with `mvn install`. Report and stop; do not silently switch to the CLI fallback.

**Scope**: the plugin defaults to `compile`-scope only, which matches the Eclipse rule that test/build dependencies don't need IP review (`references/intellectual-property.md` § Test and build dependencies). For test deps too, pass `-DincludeScope=test`.

**Multi-module**: run `mvn` once from the reactor root; the plugin walks all modules.

### Go

**Trigger**: a `go.mod` alongside the `go.sum` being checked.

The tool parses `go.sum` natively — feed it directly:

```bash
java -jar <dash-jar> -summary DEPENDENCIES go.sum
```

**No `go.sum`**: either the module has no dependencies, or `go mod download` has never run. Ask the user to run `go mod tidy` first; don't check `go.mod` alone. Assume an existing `go.sum` is up to date unless the user says otherwise.

**Workspaces (`go.work`)**: `go.work` itself lists no dependencies — each member module keeps its own `go.sum`. Run once per member, or concatenate the `go.sum` files. A `go.work` may be gitignored locally; check for it before assuming a single-module repo.

**Triaging restricted entries**: `go.sum` mixes runtime, test, and transitive modules without preserving that context.

- Decode the CSV identifier to a module path: `go/golang/golang.org%2Fx%2Fexp/jsonrpc2/v0.0.0-…` → `golang.org/x/exp/jsonrpc2` (URL-decode `%2F` → `/`, strip the trailing `/version` segment).
- `go mod why <module>` traces the import chain — the entry may be indirect and absent from `require` directives.
- For direct entries, check `go.mod` and grep `.go` imports.

**Pseudo-versions** (`v0.0.0-20…` timestamp suffixes): ClearlyDefined often has no record yet — `restricted` with empty license is usually indexing lag, not a license concern. File review to seed the Dash Database.

Surface distribution context in the report (see `references/intellectual-property.md` § Test and build dependencies). Test-only imports like `github.com/stretchr/testify` may appear in `go.sum` but qualify for the build-only exemption when not distributed.

### Other ecosystems (Gradle, Cargo, Python, .NET, SBT, C/C++)

**Trigger**: a manifest at the project root with no match above (`build.gradle*`, `Cargo.toml`, `requirements.txt`, `*.csproj`, `build.sbt`, or a hand-maintained dependency list).

Follow the matching recipe in `references/dash-license-tool.md` § Generating dependency lists per ecosystem. Same `-summary`, IPLab filing, and reporting rules as above.

## Reporting findings

Always summarise the tool's important findings to the user after a run, regardless of whether reviews were filed. When multiple dependency graphs were checked, use one report section per graph (label each with its path and summary CSV). The CLI only logs items needing review, so derive totals from each summary CSV (`wc -l <summary>`, `grep -c ', approved,' <summary>`, `grep -c ', restricted,' <summary>`).

Before writing the report, categorize each **restricted** row:

| Pattern | Meaning | Typical action |
|---|---|---|
| `source` = `clearlydefined`, empty license | ClearlyDefined hasn't indexed this coordinate yet | File IPLab review (or note for later filing) |
| Same publisher/version cohort (e.g. all `@typescript-eslint/*@8.61.0`, all `@vscode/vsce-sign-*@2.0.6`) | Batch indexing lag, not separate license problems | One review often covers the cohort |
| Go pseudo-version (`v0.0.0-20…`) or same module path at multiple pseudo-versions | CD indexing lag for unreleased or freshly tagged modules | File review; cohort by module path |
| Module from upstream project org (Eclipse npm, sibling org domain) | Missing Dash Database entry, not a license problem | File review; IP Team usually closes as already-vetted |
| `source` = `#nnnnn` or `LicenseRef-*` in license column | IP Team previously flagged this license | Needs real attention — read the CQ/issue |
| Triage shows root `devDependencies` / generator / unpublished examples | Build-only, likely non-distribution | Note Eclipse exemption; may still need filing for the coordinate |

Use this template — the **restricted** table is the deliverable; don't bury it under prose:

```markdown
## License check summary

**Totals:** <N> checked — <approved> approved, <restricted> restricted
**Summary CSV:** <path>
**Exit code:** <code> (restricted count when non-zero)

### Restricted dependencies

| Identifier | License | Source | Context |
|---|---|---|---|
| ...one row per restricted entry... |

### Notes
- <cohort patterns, exemption candidates, vs. genuine license concerns>
- <if -review: IPLab issue URLs; flag when restricted count > issues filed — re-run needed>
```

Each restricted row needs: identifier, license (empty → "no license info"), source, and triage context where available.
