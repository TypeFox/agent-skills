# Eclipse Dash License Tool

Operational reference for using the [Eclipse Dash License Tool](https://github.com/eclipse-dash/dash-licenses) to run automated license checks on an Eclipse open source project's third-party dependencies. For the conceptual background (project content, third-party content, the IP review process, ClearlyDefined criteria), see `intellectual-property.md`.

## Table of contents

- [What the tool does (and does not do)](#what-the-tool-does-and-does-not-do)
- [Getting the tool](#getting-the-tool)
- [Choosing CLI vs. Maven plugin](#choosing-cli-vs-maven-plugin)
- [Output: the summary file](#output-the-summary-file)
- [CLI usage](#cli-usage)
- [Generating dependency lists per ecosystem](#generating-dependency-lists-per-ecosystem)
- [Maven plugin](#maven-plugin)
- [Filing automatic IP review requests](#filing-automatic-ip-review-requests)
- [Errors and debugging](#errors-and-debugging)
- [CI integration (GitHub Actions)](#ci-integration-github-actions)
- [Authenticated proxies](#authenticated-proxies)

## What the tool does (and does not do)

The tool maps each dependency identifier to a license, classifies it `approved` or `restricted`, and optionally opens IPLab review requests for restricted entries.

It **does not** discover dependencies on its own — except via the Maven plugin (which walks the Reactor). For the CLI you supply the list (lockfile, build-tool output, or a hand-curated flat file). Dependencies that escape the build system — e.g., a JS library checked into `lib/` — must be added manually.

Accepted identifier formats:

- ClearlyDefined ID: `maven/mavencentral/org.apache.commons/commons-csv/1.8`
- Maven GAV: `org.apache.commons:commons-csv:1.8`
- NPM: `npm/npmjs/-/babel-polyfill/6.26.0`
- GitHub: `git/github/<org>/<repo>/<revision>` (e.g., `git/github/nlohmann/json/3.9.1`)
- Crates.io: `crate/cratesio/-/<name>/<version>` (registry is "crates" — Cargo is the package manager)
- PyPI: `pypi/pypi/-/<name>/<version>`
- NuGet: `nuget/nuget/-/<name>/<version>`

For Cargo, **strip the leading `v`** from the version (`v1.0.85` → `1.0.85`) — ClearlyDefined data is keyed without it.

## Getting the tool

**Latest CLI jar:**

```
https://repo.eclipse.org/service/rest/v1/search/assets/download?sort=version&repository=dash-maven2-releases&maven.groupId=org.eclipse.dash&maven.artifactId=org.eclipse.dash.licenses&maven.extension=jar
```

Requires **Java 11 or later**. The Maven plugin additionally requires Maven 3.6.3+.

The Maven plugin coordinates are `org.eclipse.dash:license-tool-plugin` (latest published `1.0.2`). It is published to `repo.eclipse.org`, **not** Maven Central — the project's `pom.xml` (or `~/.m2/settings.xml`) must declare:

```xml
<pluginRepositories>
  <pluginRepository>
    <id>dash-licenses-snapshots</id>
    <url>https://repo.eclipse.org/content/repositories/dash-licenses-snapshots/</url>
    <snapshots><enabled>true</enabled></snapshots>
  </pluginRepository>
</pluginRepositories>
```

## Choosing CLI vs. Maven plugin

For Maven projects, **prefer the Maven plugin** — it discovers dependencies through the Reactor and integrates with the `verify` phase. Note the scope difference: the plugin defaults to `compile` only, while `mvn dependency:list` piped to the CLI includes `test`. To vet test deps via the plugin, set `<includeScope>test</includeScope>`.

For other ecosystems (npm/yarn/pnpm, Go, Gradle, Cargo, .NET, Python, C/C++), use the CLI. It reads a supported lockfile directly or accepts piped identifiers via `-` (stdin).

## Output: the summary file

Pass `-summary <file>` (CLI) or `-Ddash.summary=<file>` (plugin) to write a CSV with one row per dependency:

```
<dependency-id>, <license>, <status>, <source>
```

The `<license>` column is empty when no license information was recorded — common cause of a `restricted` row from `clearlydefined`.

Statuses:

- `approved` — safe to use; license is on the Eclipse approved list and matched by either the Dash Database or ClearlyDefined.
- `restricted` — needs IP Team review. Either no license info was found, the license is not approved, ClearlyDefined's confidence is too low, or the IP Team has previously flagged it.

Source values: `emo_ip_team` / `CQ<n>` (Dash Database hits), `clearlydefined`, etc.

Example summary line:

```
maven/mavencentral/org.glassfish/jakarta.json/2.0.0, EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0, approved, emo_ip_team
```

The Maven plugin always writes a summary even without an explicit `-Ddash.summary` — default location `${project.build.directory}/dash/summary`.

## CLI usage

Basic form:

```
java -jar org.eclipse.dash.licenses-<version>.jar <input>
```

`<input>` can be:

- A path to a flat file (one identifier per line)
- A path to a supported lockfile: `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `go.sum`
- `-` to read identifiers from stdin

CLI flags (from `-help`):

| Flag | Purpose |
|------|---------|
| `-batch <int>` | Number of entries per API call |
| `-confidence <int>` | Minimum ClearlyDefined score (0–100) for approval. Default is sufficient — only lower it with caution |
| `-excludeSources <sources>` | Skip specific data sources |
| `-summary <file>` | Write CSV summary to `<file>` |
| `-timeout <seconds>` | HTTP timeout |
| `-project <id>` | Eclipse project ID (e.g., `technology.dash`). Required with `-review` |
| `-repo <url>` | Project repository URL. Used in review requests |
| `-review` | File IPLab issues for `restricted` entries (see [Filing automatic IP review requests](#filing-automatic-ip-review-requests)) |
| `-token <token>` | GitLab personal access token. Required with `-review` |
| `-help` | Show usage |

Single-library check:

```bash
echo "tech.units:indriya:1.3" | java -jar org.eclipse.dash.licenses-<version>.jar -
```

The `yarn.lock` parser only handles some lockfile versions (format is undocumented — [issue 500](https://github.com/eclipse-dash/dash-licenses/issues/500)). If it misbehaves, use the Yarn recipe below.

## Generating dependency lists per ecosystem

These recipes emit identifiers to stdin via `-`. Save jobs to a script per project; the regexes are sensitive to tool-version output formats.

### npm / pnpm / yarn (lockfile)

Pass the lockfile directly — no preprocessing:

```bash
java -jar org.eclipse.dash.licenses-<v>.jar package-lock.json
java -jar org.eclipse.dash.licenses-<v>.jar pnpm-lock.yaml
java -jar org.eclipse.dash.licenses-<v>.jar yarn.lock
```

### Yarn (when the lockfile parser fails)

```bash
yarn info -R --name-only \
| grep -P "(\S+)@npm:(\S+)" \
| sed -E -e 's|..\s(\S+)@npm:(\S+)|\1@\2|g' \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

### Go

```bash
java -jar org.eclipse.dash.licenses-<v>.jar go.sum
```

### Maven (CLI fallback when not using the plugin)

```bash
mvn verify dependency:list -DskipTests -Dmaven.javadoc.skip=true \
    -DappendOutput=true -DoutputFile=maven.deps
java -jar org.eclipse.dash.licenses-<v>.jar maven.deps
```

For multi-module builds, pass an **absolute path** to `-DoutputFile` so all modules append to the same file ([MDEP-542](https://issues.apache.org/jira/browse/MDEP-542)).

### Gradle (lockfile preferred)

If the project has `gradle.lockfile`:

```bash
cat gradle.lockfile | grep -Pv '^#' | grep -Pv '^empty' | grep -Poh '^[^=]+' \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

Otherwise, parse the dependency report (less reliable — verify with `./gradlew dependencies` first):

```bash
./gradlew dependencies \
| grep -Poh "(?<=\-\-\- ).*" \
| grep -Pv "\([c\*]\)" \
| perl -pe 's/([\w\.\-]+):([\w\.\-]+):(?:[\w\.\-]+ -> )?([\w\.\-]+).*$/$1:$2:$3/gmi;t' \
| sort -u \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

The `(c)` strips constraints; `(*)` strips duplicate-marker rows; the `perl` clause normalises `1.8.20 -> 1.9.0` to the resolved version `1.9.0`.

### Cargo / Rust

```bash
cargo tree -e normal --prefix none --no-dedupe \
| sort -u | grep -v '^[[:space:]]*$' \
| sed -E 's|([^ ]+) v([^ ]+).*|crate/cratesio/-/\1/\2|' \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

`cargo tree` does not separate project crates from third-party crates. Workspace members appear with a local path (e.g., `ank-agent v1.0.0 (/path/to/repo/agent)`); add a `grep -v "/<repo-name>/"` to drop them before piping.

### .NET (PowerShell)

```bash
dotnet list package --include-transitive \
| grep ">" \
| grep -Pv "\s(Microsoft|NETStandard|NuGet|System|runtime)" \
| sed -E -e "s/\s+> ([a-zA-Z\.\-]+).+\s([0-9]+\.[0-9]+\.[0-9]+)\s+/nuget\/nuget\/\-\/\1\/\2/g" \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

The system-package filter is broad; tune it to also drop your own project's namespaces.

### SBT

```bash
./sbt dependencyTree \
| grep -Poh "(?<=\+\-)[^:]+:[^:]+:[^:\s]+" | sort -u \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

### Python

Best, with `pipdeptree` (operates on the active virtualenv):

```bash
pipdeptree -a -f \
| sed -E -e 's|([^= ]+)==([^= ]+)|pypi/pypi/-/\1/\2|' -e 's| ||g' \
| sort -u | java -jar org.eclipse.dash.licenses-<v>.jar -
```

Alternative, using `pip install --dry-run` against a `requirements.txt`:

```bash
pip install -r requirements.txt --dry-run \
| grep -Poh "(?<=^Would install ).*$" | grep -oP '[^\s]+' \
| sed -E -e 's|(.+)\-([a-zA-Z0-9\.]+)|pypi/pypi/-/\1/\2|' \
| java -jar org.eclipse.dash.licenses-<v>.jar -
```

A pure-`grep` parse of `requirements.txt` is brittle — use `pipdeptree` or `--dry-run` when possible.

### C/C++

C/C++ has no canonical dependency-graph tooling. Maintain a hand-written `dependencies.txt` of GitHub identifiers:

```
git/github/nlohmann/json/3.9.1
git/github/zaphoyd/websocketpp/2.8.2
```

Then:

```bash
java -jar org.eclipse.dash.licenses-<v>.jar dependencies.txt
```

## Maven plugin

Goal: `org.eclipse.dash:license-tool-plugin:license-check`. Run ad-hoc:

```bash
mvn org.eclipse.dash:license-tool-plugin:license-check -Ddash.summary=DEPENDENCIES
```

Bind it to the build in `pom.xml`:

```xml
<plugin>
  <groupId>org.eclipse.dash</groupId>
  <artifactId>license-tool-plugin</artifactId>
  <version>1.0.2</version>
  <executions>
    <execution>
      <id>license-check</id>
      <goals><goal>license-check</goal></goals>
    </execution>
  </executions>
</plugin>
```

### Plugin properties

| Property | Default | Notes |
|---|---|---|
| `dash.skip` | `false` | Skip plugin execution |
| `dash.fail` | `false` | Fail the build when restricted content is found. Set `true` in CI |
| `dash.summary` | `${project.build.directory}/dash/summary` | Summary CSV location |
| `dash.review.summary` | – | Review-summary location |
| `dash.iplab.token` | – | GitLab token for `-review` |
| `dash.projectId` | – | Eclipse project ID, e.g., `technology.dash` |
| `dash.repo` | – | Project source-repo URL |
| `dash.proxy` | – | Maven `<proxy>` ID to route requests through |

### Scope and inclusion filters

The plugin filters Maven dependencies before sending them to the tool. Inclusions override exclusions; exact match everywhere except `includeGroupIds`/`excludeGroupIds`, which support partial match (`org.eclipse` matches `org.eclipse.jdt`).

| Property | Values |
|---|---|
| `includeScope` / `excludeScope` | `runtime`, `compile` (default), `test`, `provided`, `system`. `runtime` = runtime+compile; `compile` = compile+provided+system; `test` = all |
| `includeTypes` / `excludeTypes` | Comma-separated artifact types |
| `includeClassifiers` / `excludeClassifiers` | Comma-separated classifiers |
| `includeGroupIds` / `excludeGroupIds` | Comma-separated; partial match |
| `includeArtifactIds` / `excludeArtifactIds` | Comma-separated; exact match |

Exclude all internal Eclipse content (e.g., when an Eclipse project depends on other Eclipse projects):

```bash
mvn org.eclipse.dash:license-tool-plugin:license-check -DexcludeGroupIds=org.eclipse
```

### Eclipse Tycho

If the plugin reports too few dependencies on a Tycho build, force eager Target Platform resolution:

```bash
mvn org.eclipse.dash:license-tool-plugin:license-check -Dtycho.target.eager=true
```

### Pruning unused transitive dependencies

If a restricted transitive dep is genuinely unused at runtime, fix it in the project's own `<dependency><exclusions>` — not via a Dash Tool flag. The tool reports what the build resolves.

## Filing automatic IP review requests

For each `restricted` dependency, the tool can open an IPLab issue (https://gitlab.eclipse.org/eclipsefdn/iplab/iplab) titled with the dependency's identifier and pre-populated for the IP Team. **Maximum 5 issues are filed per invocation** — re-run as needed.

Prerequisites: Eclipse committer status on the project, plus a personal access token from https://gitlab.eclipse.org/-/user_settings/personal_access_tokens with `api` scope.

```bash
# CLI
java -jar org.eclipse.dash.licenses-<v>.jar yarn.lock \
    -review -token "$ECLIPSE_GITLAB_TOKEN" -project ecd.theia

# Maven plugin
mvn org.eclipse.dash:license-tool-plugin:license-check \
    -Ddash.iplab.token="$ECLIPSE_GITLAB_TOKEN" \
    -Ddash.projectId=technology.dash
```

In CI, store the token as a secret and pass it via environment variable.

## Errors and debugging

The tool fails fast on errors — exceptions terminate execution rather than skipping bad entries. Common HTTP errors hitting external services:

- **502 Bad Gateway** from ClearlyDefined — transient, retry immediately.
- **524 Timeout** — ClearlyDefined unreachable; retry later.
- **429 Too Many Requests** — rate-limited; reduce `-batch` or wait.

Enable debug logging when diagnosing:

```bash
java -Dorg.slf4j.simpleLogger.defaultLogLevel=debug \
     -jar org.eclipse.dash.licenses-<v>.jar <input>
```

## CI integration (GitHub Actions)

Maven projects can call a reusable workflow shipped by dash-licenses (marked **experimental** by the Eclipse Foundation):

```yaml
name: License vetting status check
on:
  push:    { branches: [master] }
  pull_request: { branches: [master] }
  issue_comment: { types: [created] }
jobs:
  call-license-check:
    uses: eclipse-dash/dash-licenses/.github/workflows/mavenLicenseCheck.yml@master
    with:
      projectId: <PROJECT-ID>
    secrets:
      gitlabAPIToken: ${{ secrets.<PROJECT-NAME>_GITLAB_API_TOKEN }}
```

Requires the root `pom.xml` at the repository root and a secret named `<PROJECT-NAME>_GITLAB_API_TOKEN`. After setup, committers can request reviews from PR comments by posting `/request-license-review`. Optional inputs: `setupScript` (run before the check) and `submodules` (check out git submodules).

## Authenticated proxies

The plugin reads `~/.m2/settings.xml` `<proxies>` automatically (first active proxy by default). Select another with `-Ddash.proxy=<id>`.
