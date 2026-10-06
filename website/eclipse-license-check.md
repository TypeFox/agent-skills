# Eclipse License Check

Check the third-party dependencies of an Eclipse Foundation project with the Eclipse Dash License Tool, and find out which ones still need a review before you can release.

Source: [skills/eclipse-license-check](https://github.com/TypeFox/agent-skills/tree/main/skills/eclipse-license-check)

## Install

```sh
npx skills add TypeFox/agent-skills -s eclipse-license-check
```

The skill runs the [Eclipse Dash License Tool](https://github.com/eclipse-dash/dash-licenses), which needs Java 11 or newer. For Maven projects it uses the tool's Maven plugin, which also needs Maven 3.6.3 or newer.

## Background

An Eclipse Foundation project may only ship third-party code whose license the Eclipse Foundation's intellectual property team, the IP Team, has accepted. The team keeps a database of the licenses it has already reviewed. The Dash License Tool compares a project's dependencies against that database and against public license data, and lists every dependency it cannot approve. Those entries go to the IP Team as review requests, filed as issues in [IPLab](https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab), the team's issue tracker. A project cannot make a formal release until the reviews are done.

The rules behind this are in the Eclipse Foundation Project Handbook: the [Intellectual Property](https://www.eclipse.org/projects/handbook/#ip) chapter explains what counts as third-party content and what is exempt, and the [Releases](https://www.eclipse.org/projects/handbook/#release) chapter explains what a release requires.

## Usage

The skill activates when you ask to check the licenses of an Eclipse project's dependencies, ask whether a particular dependency needs a review, want review requests filed, or prepare a release.

> Run the license check on this repo before the next release. Report only, do not file anything.

The skill then works through three steps:

1. **Find what to check.** It looks at the lock files and build files in your repository and picks the matching way to run the tool: the lock file for npm, yarn, pnpm and Go projects, the Maven plugin for Java projects (including Tycho builds), and the recipe from the tool's documentation for other ecosystems. A repository with several parts, such as a Java core and an npm website, gets one run per part.
2. **Run the tool.** Each run writes a summary file that lists every dependency with its license and whether it is approved. The skill picks a file name that does not collide with files your project tracks.
3. **Report.** You get the totals and a table of every dependency the tool could not approve, with its license, where the license information came from, and how the dependency enters your project: directly, through another package, or only at build time.

The table is the point of the exercise. Not every unapproved entry is a licensing problem. Many are packages the databases have not indexed yet, packages from another Eclipse project, or build tools that are never shipped. The report says which of these each entry looks like, so you can tell what needs action from what you can set aside.

### Filing review requests

The tool can file the review requests for you, as issues in IPLab. That is a public action the IP Team acts on, so the skill only does it when you ask for it, and asks first if your request is unclear. Filing needs two things:

- Your project's Eclipse ID, such as `ecd.theia`. The skill asks for it rather than guessing from the repository name.
- A personal access token for gitlab.eclipse.org with the `api` scope.

Never paste the token into the chat. The conversation may be stored or logged. Put the token in an environment variable named `IPLAB_TOKEN` in the shell that starts your agent, and tell the skill if you used a different name. If you paste a token anyway, the skill stops and asks you to revoke it and create a new one.

The tool files at most five issues per run. If more entries remain, ask for another run.

### Using a local checkout of the tool

By default the skill downloads the released tool. If you have a clone of eclipse-dash/dash-licenses, name its path and the skill builds and uses that one. It checks the clone's state first and asks before touching anything that looks like your own work in progress.
