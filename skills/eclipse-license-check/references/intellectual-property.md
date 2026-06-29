# Intellectual Property at the Eclipse Foundation

This reference summarizes the Eclipse Foundation's rules for handling intellectual property (IP), focused on what is needed to run dependency license checks for an Eclipse open source project. It is condensed from the [Intellectual Property](https://www.eclipse.org/projects/handbook/#ip) section of the Eclipse Project Handbook.

## Table of contents

- [Core concepts](#core-concepts)
- [Key resources and systems](#key-resources-and-systems)
- [Project content vs. third party content](#project-content-vs-third-party-content)
- [What counts as a third-party dependency](#what-counts-as-a-third-party-dependency)
- [The platform boundary](#the-platform-boundary)
- [Versions and service releases](#versions-and-service-releases)
- [Test and build dependencies](#test-and-build-dependencies)
- [License compatibility](#license-compatibility)
- [How content gets classified as approved or restricted](#how-content-gets-classified-as-approved-or-restricted)
- [Requesting an IP review (IPLab issues)](#requesting-an-ip-review-iplab-issues)
- [Release gate](#release-gate)

## Core concepts

The Eclipse Foundation runs an **IP Due Diligence Process** to confirm that what a project produces and consumes is correctly licensed and compatible. Two facts shape how the process works in practice:

- The IP Team **identifies** licenses and **judges** consistency. It does **not give legal advice** — final compatibility decisions rest with adopters and their counsel.
- Review focuses on **source content** (source code, configuration, property files, images, icons), not compiled artifacts — the team reviews source, not JAR files.

Committers engage the IP Team by filing [IPLab](https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab) issues.

## Key resources and systems

**Eclipse Dash License Database** ("Dash Database") — the curated database of license decisions made by the IP Team. Accessed via API, primarily through the Eclipse Dash License Tool.

**IPLab** — a GitLab repository (https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab) where IP review requests are filed and tracked. IPLab data feeds the Dash Database.

**ClearlyDefined** (https://clearlydefined.io/) — an OSI project that aggregates license information from public software repositories. The Eclipse Foundation uses it as a *secondary* source. **Do not query ClearlyDefined directly**; use the Eclipse Dash License Tool, which consults both sources. When the Dash Database and ClearlyDefined disagree, **the Dash Database wins**.

**Eclipse Dash License Tool** (https://github.com/eclipse-dash/dash-licenses) — the canonical automation for license checks. Available as a CLI and a Maven plugin. This is the tool to use for automated checks.

**Eclipse approved licenses list** — https://www.eclipse.org/legal/licenses.php#approved. Licenses on this list are *generally* compatible with most Eclipse project licenses; licenses outside the list are not automatically prohibited but require careful review.

## Project content vs. third party content

**Project content** is everything the project owns and maintains in its Eclipse-managed repositories. Forked third-party content that lives in a project repository is project content. Project content does not flow through the Dash License Tool.

**Third party content** is anything the project leverages but does not maintain — typically libraries pulled in by the build. License-check automation focuses on this category.

## What counts as a third-party dependency

Anything the project references but does not maintain — and the full **transitive** closure, not just direct dependencies. Beyond the obvious build-manifest entries (Maven `<dependencies>`, npm `package.json`, Go modules, etc.), watch for less-obvious cases:

- Java/OSGi manifest references to bundles or packages
- Reflective or service-locator references
- OSGi service bindings to specific implementations
- Binaries invoked via a CLI
- C/C++ `#include` of vendored headers

## The platform boundary

The dependency graph is cut off at the **platform** — the layer adopters install themselves and accept licensing for independently. Examples:

- Java application → Java runtime is the platform
- Jakarta EE application → application server is the platform
- NPM application → Node.js is the platform
- Native application → Linux/Windows/macOS is the platform

Rule of thumb: if your project bundles or auto-installs the layer, it is a dependency. If the adopter installs it separately and accepts its license, it is the platform. When in doubt, ask the IP Team (`emo-ip-team@eclipse.org`).

## Versions and service releases

Each major and minor version of a dependency is treated as **distinct content** and must be vetted separately — problematic IP can be introduced in a new release.

**Service releases** (backwards-compatible, bug-fix-only releases on top of an already-vetted release) do not require a fresh review. If unsure whether a release qualifies as a service release, submit it for review.

## Test and build dependencies

Open-source-only test/build dependencies (used during build/test, not distributed via any `eclipse.org` property) are **non-distribution contributions** — they don't need an IP review. They may be referenced from build scripts but must not be checked into the repository or appear on `eclipse.org` download servers. List them in project documentation with how they're obtained.

This is why the Dash Maven plugin's default `compile`-only scope matches the Eclipse rule: test deps don't need vetting unless they end up distributed.

## License compatibility

Compatibility between two licenses is often situational ("it depends"). The Eclipse Foundation's [approved licenses page](https://www.eclipse.org/legal/licenses.php#approved) provides the working list of licenses generally compatible with Eclipse project licenses. Anything off-list is not banned, but warrants careful review by the IP Team.

## How content gets classified as approved or restricted

For each dependency, the classification flow is:

1. Query the **Dash Database** (the IP Team's curated decisions).
   - Vetted and approved → `approved`.
   - Vetted and flagged → `restricted`.
2. For everything not in the Dash Database, query **ClearlyDefined**.
   - Meets the ClearlyDefined criteria below → `approved`.
   - Otherwise → `restricted`.

ClearlyDefined criteria for an automatic `approved`: a *Licensed* score of at least 60, all *declared* and *discovered* licenses are on the Eclipse approved list, and the licenses are mutually consistent. **Any** of the following forces a manual IP Team review:

- `NOASSERTION` appears as a declared license.
- `NOASSERTION` appears as a discovered license.
- No declared license is recorded.
- The *Licensed* score is below 60.

The Eclipse Dash License Tool implements this flow and is the canonical automation. For installation, CLI flags, Maven plugin configuration, per-ecosystem dependency-list recipes, and review-request mechanics, see `dash-license-tool.md`.

## Requesting an IP review (IPLab issues)

When `-review` can't handle a dependency automatically (e.g., a JS library dropped into `lib/` that no manifest references), file an IPLab issue manually using a template:

- Project Content: https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab/-/issues/new?issuable_template=vet-project
- Third Party Content: https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab/-/issues/new?issuable_template=vet-third-party

The IPLab scanner parses the issue title and body — exact formatting matters.

### Issue title — must be a valid identifier

Use exactly one of these formats; do not add extra text to the title:

- ClearlyDefined ID: `{type}/{source}/{namespace}/{name}/{revision}`
- Maven GAV: `{groupid}:{artifactid}:{revision}`
- Package URL: `pkg:{type}/{namespace}/{name}@{revision}`
- GitHub commit URL: `https://github.com/{org}/{project}/commit/{ref}`
- GitHub pull request URL: `https://github.com/{org}/{project}/pull/{id}` (always requires manual review)

### Required body content

1. **Eclipse project identifier** — name and ID (not the GitLab/GitHub project):
   ```
   Project: [Eclipse Dash](https://projects.eclipse.org/projects/technology.dash)
   ```

2. **Basic Information** — license as understood (use [SPDX identifiers](https://spdx.org/licenses/)) and URLs to binary and source.

3. **Source pointer** — the most important field, formatted as `[Source](<url>)`. The URL must be one of:
   - A direct source archive link (`*.zip`, `*.tar.gz`, etc.)
   - An IPLab attachment (rename the auto-generated `[filename](/uploads/...)` to `[Source](/uploads/...)`)
   - An Eclipse GitLab merge-request URL or GitHub pull-request URL

   Do **not** point at a Git repo root — point at a specific archived release. A provided source pointer overrides IPLab's automatic detection. If you can't supply one, omit it and describe what you have; the IP Team will fill it in.

4. **Additional information** — free-form details.

### Labels

Do not apply labels. The scanner only auto-processes issues with a valid ClearlyDefined ID in the title and either no labels or only `Review Needed`.

## Release gate

A project cannot make a formal [release](https://www.eclipse.org/projects/handbook/#release) until IP due diligence — covering both project content and third-party content in that release — is complete. Milestone builds may be distributed earlier, but a formal release is blocked on IP completion.
