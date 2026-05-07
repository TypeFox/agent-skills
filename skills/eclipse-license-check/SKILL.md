---
name: eclipse-license-check
description: Run an automated third-party dependency license check for an Eclipse Foundation open source project, using the Eclipse Dash License Tool. Use this whenever the user mentions Eclipse license checking, dependency vetting for an Eclipse project, the Dash License Tool, dash-licenses, IPLab review requests, the Eclipse IP due diligence process, or wants to verify that a project's dependencies are approved for use under the Eclipse IP Policy — even if they don't name the tool directly. Also relevant when the user prepares an Eclipse project for release with respect to third-party content, or asks which dependencies require IP Team review.
---

# Eclipse Dependency License Check

This skill runs an automated third-party dependency license check for an Eclipse Foundation open source project, using the [Eclipse Dash License Tool](https://github.com/eclipse-dash/dash-licenses). The tool maps each dependency to a license, classifies it as `approved` or `restricted`, and (optionally) files IPLab review requests for the restricted ones — the actionable output that tells the project team what still needs IP Team review before a formal release can ship.

When more context is needed, load these reference files:

- `references/intellectual-property.md` — why Eclipse projects need this check, what counts as third-party content, where the dependency graph cuts off, the rules around test/build dependencies, the IPLab issue format. Read this when the user asks "do I need to vet X?", when deciding whether something is a dependency at all, or when filing manual IPLab issues.
- `references/dash-license-tool.md` — installation, CLI flags, Maven plugin properties, per-ecosystem recipes for generating dependency lists, error handling, CI integration. Read this whenever invoking the tool.

## Optional inputs

1. **A local clone of `eclipse-dash/dash-licenses`** — use it when given; otherwise download the released CLI jar per `references/dash-license-tool.md`.
2. **An IPLab access token** — a `gitlab.eclipse.org` personal access token with `api` scope. Needed only to file IPLab review requests automatically. Treat the token as a secret; see "Handling the IPLab token" below.

If neither was mentioned, proceed with the released jar and without filing reviews — do not prompt.

## Preflight: preparing a local Dash License Tool clone

If the user provided a clone path, prepare it before any check runs. The user may have work in progress, so **do not modify unfamiliar state**.

1. Inspect: `git -C <path> status --porcelain` and `git -C <path> rev-parse --abbrev-ref HEAD`.
2. **Clean tree on `master`**: `git -C <path> pull --ff-only`, then `mvn -f <path> -DskipTests clean install`. The `install` goal places both the CLI jar and the Maven plugin into `~/.m2` so later invocations resolve them locally. Drop `-DskipTests` only to validate the tool itself — the suite hits external services and adds minutes.
3. **Only IDE/OS noise dirty** (e.g. `.DS_Store`, modifications under `.settings/` which Eclipse auto-edits on project open, `.idea/`): none of this is real WIP. Offer to discard those paths and continue as in step 2; don't act unilaterally.
4. **Anything else** (modified source/build files, untracked code, other branch, detached HEAD): report what was observed and ask how to proceed.

After a successful build, use the **shaded** jar at `shaded/target/org.eclipse.dash.licenses-<version>.jar` (read `<version>` from the build output — typically `<x.y.z>-SNAPSHOT` on a master clone). The thin jar in `core/target/` is `...licenses.core-<version>.jar` and lacks transitive deps, so it fails at runtime with `NoClassDefFoundError`. Alternatively invoke the now-installed Maven plugin as `org.eclipse.dash:license-tool-plugin:license-check`.

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

## Deciding whether to file IPLab review requests

The `-review` flow files real GitLab issues against `eclipsefdn/emo-team/iplab` that the Eclipse IP Team acts on — a public, irreversible action. Choose based on explicit user intent (see `references/dash-license-tool.md` § Filing automatic IP review requests for issue conventions):

- **User wants reviews AND provided a token** → pass `-review -token "$IPLAB_TOKEN" -project <project-id>` (CLI) or `-Ddash.iplab.token="$IPLAB_TOKEN" -Ddash.projectId=<project-id>` (Maven plugin). Add `-repo <url>` / `-Ddash.repo=<url>` with the public HTTPS source-repo URL — derive it from `git remote get-url origin`, converting any SSH form like `git@github.com:org/repo.git` to `https://github.com/org/repo`. See "Handling the IPLab token" above for how the token value should reach the command.
- **User has said no reviews** → never pass `-review`. Restricted content still appears in the summary.
- **Intent unclear** → ask before running. Do not silently default.

The Eclipse project ID (e.g., `technology.dash`, `ecd.theia`) is required for `-review`. Ask if not supplied — do not guess from directory or repo names.

## Running the check

Identify the project's ecosystem from the manifest files at the project root, then follow the matching subsection. When the tool finishes, continue to "Reporting findings".

Run from the project root so relative lockfile/manifest paths resolve, or pass absolute paths. Always pass `-summary <path>` so the CSV is available for reporting; relative summary paths land in the CWD, so pick a name that won't collide with files the project already tracks (some Eclipse projects commit a `DEPENDENCIES` file). When reviews are enabled (per the previous section), append `-review -token "$IPLAB_TOKEN" -project <project-id>` (and `-repo <url>` if known) to every CLI invocation, and capture stdout — the IPLab issue URLs are printed there, not in the CSV.

### TypeScript / JavaScript (npm, yarn, pnpm)

**Trigger**: a `package.json` at the project root.

The tool parses `package-lock.json`, `yarn.lock`, and `pnpm-lock.yaml` natively — feed the lock file directly:

```bash
java -jar <dash-jar> -summary DEPENDENCIES package-lock.json
# or yarn.lock, or pnpm-lock.yaml
```

**No lock file**: dependencies aren't pinned, so a meaningful check isn't possible. Ask the user to run `npm install` / `yarn install` / `pnpm install` first. Don't run against `package.json` alone.

**Multiple lock files**: a misconfiguration. Ask which package manager is authoritative — running both double-counts.

**Lock file freshness**: assume up to date. Only regenerate if the user says it's stale.

**Yarn parser caveat**: the native `yarn.lock` parser is fragile (the format is undocumented). If the run errors, returns suspiciously few entries, or the user reports a recent yarn version, fall back to the `yarn info -R --name-only` pipeline in `references/dash-license-tool.md` § Yarn (when the lockfile parser fails).

**Workspace coverage**: only deps reachable from the lock file you pass are checked. In a monorepo, the root lock file covers every package listed in `workspaces` (or `pnpm-workspace.yaml`); sibling packages outside that list keep their own graphs and need separate runs.

**Triaging restricted entries**: lock files mix runtime, dev, and transitive deps without preserving that context, so the tool vets them all. When a restricted entry surfaces, recover the context the user needs to act on it:

- Run `yarn why <pkg>` (or `npm ls <pkg>` / `pnpm why <pkg>`) to trace the chain — the entry may be transitive and absent from any `package.json`.
- For direct entries, grep the root `package.json` plus every workspace package's `package.json` to find which key (`dependencies` / `devDependencies`) declares it.

Surface both in the report. The Eclipse exemption hinges on whether the content is **distributed** via an `eclipse.org` property — not on the JSON key alone (see `references/intellectual-property.md` § Test and build dependencies). A `devDependency` used only at build time qualifies; so does a `dependency` of an example or demo the project never publishes. Conversely, a `devDependency` that ends up bundled into a shipped artifact does need review.

**Eclipse-Foundation-published content**: when a `restricted` entry is itself from another Eclipse Foundation project — npm packages like `langium`, `theia`, `sprotty`, etc. — the cause is usually a missing Dash Database entry for that exact coordinate, not a real licensing problem. The tool has no Eclipse-ownership lookup for npm (Maven projects sidestep this with `-DexcludeGroupIds=org.eclipse`; npm has no such convention, since Eclipse-published packages don't share a name prefix). Let `-review` file the IPLab issue anyway and explain in the report that the IP Team typically closes these as already-vetted under the upstream project's own IP review; that resolution itself adds the coordinate to the Dash Database, so future runs return `approved`.

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

When reviews are enabled, append `-Ddash.iplab.token="$IPLAB_TOKEN" -Ddash.projectId=<project-id>` (and `-Ddash.repo=<url>` if known).

**Plugin not resolvable**: if Maven reports `Plugin org.eclipse.dash:license-tool-plugin ... could not be resolved`, the Eclipse plugin repository isn't configured. Fix by either (a) adding `repo.eclipse.org` to `pluginRepositories` (snippet in `references/dash-license-tool.md` § Getting the tool), or (b) building a local clone with `mvn install`. Report and stop; do not silently switch to the CLI fallback.

**Scope**: the plugin defaults to `compile`-scope only, which matches the Eclipse rule that test/build dependencies don't need IP review (`references/intellectual-property.md` § Test and build dependencies). For test deps too, pass `-DincludeScope=test`.

**Multi-module**: run `mvn` once from the reactor root; the plugin walks all modules.

### Go

**Trigger**: a `go.mod` at the project root.

The tool parses `go.sum` natively — feed it directly:

```bash
java -jar <dash-jar> -summary DEPENDENCIES go.sum
```

When reviews are enabled, append `-review -token "$IPLAB_TOKEN" -project <project-id>` (and `-repo <url>` if known).

**No `go.sum`**: either the module has no dependencies, or `go mod download` has never run. Ask the user to run `go mod tidy` first; don't check `go.mod` alone. Assume an existing `go.sum` is up to date unless the user says otherwise.

**Workspaces (`go.work`)**: `go.work` itself lists no dependencies — each member module keeps its own `go.sum`. Run once per member, or concatenate the `go.sum` files.

**Test dependencies**: `go.sum` covers test-only imports too. Same triage approach as the JavaScript section above.

## Reporting findings

Always summarise the tool's important findings to the user after a run, regardless of whether reviews were filed. The CLI only logs items needing review, so derive totals from the summary CSV (`wc -l <summary>`, `grep -c ', approved,' <summary>`, `grep -c ', restricted,' <summary>`). The summary must include, at minimum:

- The total number of dependencies checked.
- The count of `approved` versus `restricted` entries.
- The full list of `restricted` dependencies — each with its identifier, the license the tool reported (the license column in the CSV; an empty column means none was recorded — report this as "no license info"), and the source (`emo_ip_team`, `clearlydefined`, etc.). These are what require attention.
- If `-review` was used: the URLs of every IPLab issue created. The CLI prints these only on stdout (`A review request was created <url> .`) — capture stdout to recover them; they are not in the CSV. The current implementation files at most five per invocation, so flag when the restricted set was larger than the issues filed and a re-run is needed.
- The path to the summary CSV, if one was written.

Do not bury the restricted list under prose. It is the point of the check.
