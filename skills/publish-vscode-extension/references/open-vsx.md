# Open VSX Registry specifics

The Open VSX Registry (https://open-vsx.org) is the Eclipse Foundation's vendor-neutral alternative to the VS Code Marketplace. VS Codium, Gitpod, Theia, Eclipse Che, Cursor, Windsurf, code-server, and most non-Microsoft VS Code distributions pull extensions from here — Microsoft's Marketplace ToS forbids non-Microsoft products from using it.

The CLI is `ovsx`, published to npm. Installation: `npm install -g ovsx`. It can also be invoked as `npx ovsx`.

## One-time account setup

Two accounts must be linked before you can publish, because Open VSX uses GitHub for login but the publisher contract is legally with the Eclipse Foundation.

1. **Create an Eclipse Foundation account** at https://accounts.eclipse.org/user/register. The **GitHub Username** field must exactly match the GitHub account you'll log into open-vsx.org with — Open VSX links accounts by this string.
2. **Log into https://open-vsx.org** using "Log In with GitHub."
3. Go to **Profile Settings** and complete the **Log in with Eclipse** step so the two accounts are linked.
4. Accept the **Publisher Agreement**. This is **not the same as the Eclipse Contributor Agreement (ECA)** — it's a separate document specific to Open VSX, and a publish call returns a clear error if it isn't signed yet. The signing page lives under the Eclipse profile, not under open-vsx.org.

If the user has previously contributed to Eclipse projects and signed the ECA, they still must sign the Publisher Agreement separately.

## Generate an access token

1. Open-vsx.org → avatar → **Settings** → **Access Tokens** → **Generate New Token**.
2. Give it a description (e.g. `local`, `ci-github-actions`).
3. **Copy the token immediately** — it isn't shown again. Store it as `OVSX_PAT` in the shell that launches the agent, or as a CI secret.

Unlike Marketplace PATs, Open VSX tokens don't expire. Rotate manually if you suspect leakage.

See SKILL.md § "Handling access tokens" for the safe-handling rules — the token must never be pasted into the conversation, and the agent must reference it by env-var name (`OVSX_PAT`), never substitute the value on the command line.

## Namespaces

A namespace on Open VSX is what `publisher` on Marketplace is — the prefix in `publisher.extension`. Valid namespace names match `[\w\-\+\$~]+` (letters, digits, `_`, `-`, `+`, `$`, `~`).

Important: registering a Marketplace publisher does **not** register the matching Open VSX namespace, and they live in entirely separate trust domains. Anyone can call `ovsx create-namespace foo` and immediately publish under `foo.*` — to prevent typosquatting your brand, claim the namespace early.

```bash
ovsx create-namespace <name>
```

With `OVSX_PAT` exported in the environment, `ovsx` picks it up automatically — no `-p` flag needed. This creates the namespace and adds the calling user as a **contributor**. Contributors can publish but cannot manage members. The namespace has no **owner** yet — see "verified vs unverified" below.

## Verified vs unverified extensions

When users browse Open VSX, extensions show one of two states:

- **Verified** ✅ — namespace has at least one owner AND the publishing user is a namespace member. This is the steady state you want.
- **Unverified** ⚠️ — namespace has no owner yet, or the publisher isn't a member. Users see a yellow warning on the extension page. Functional, but it looks bad.

To move from unverified to verified, the namespace needs an owner — and only the Open VSX admins can assign the first one.

### Claim ownership of a namespace

1. Log into open-vsx.org so admins know which Eclipse user is making the claim.
2. File a public issue at https://github.com/EclipseFdn/open-vsx.org/issues/new/choose, using the "Publisher Agreement / namespace ownership" template.
3. Include: the namespace name, evidence you own the corresponding brand (link to the GitHub org, the Marketplace publisher page, a project README, etc.), and the Eclipse account username.
4. Wait for an admin to grant ownership. The issue is public so others can object before it's processed — this is the typosquatting check.

Once you're the owner, the extension's "unverified" badge clears on the next publish.

### Add additional members

Owners get a **Namespaces** section in profile settings. From there:

- **Owner** — full authority, including adding/removing members. Multiple humans on a team should each be owners.
- **Contributor** — can publish but cannot manage members. Use this role for **service accounts and CI tokens** so a leaked CI token can't be used to reassign ownership.

History note (December 17, 2020): namespaces used to be public — anyone could publish to a namespace they hadn't claimed. That's gone. Only members can publish now. Orphaned namespaces from that era had their previous publishers automatically added as contributors.

### The `@open-vsx` exception

A privileged service account `@open-vsx` can publish to any namespace, even without membership. It's used by the community-managed [`open-vsx/publish-extensions`](https://github.com/open-vsx/publish-extensions) repo, which mirrors high-demand extensions whose authors haven't published to Open VSX themselves. If a user complains "someone else's account already published my extension to Open VSX", that's almost always `@open-vsx` mirroring — opening a PR to that repo lets them take over publishing themselves.

## Publishing commands

All examples assume `OVSX_PAT` is exported in the environment (see SKILL.md § "Handling access tokens"). `ovsx` picks it up automatically — do **not** add `-p $OVSX_PAT` on the command line; the env-var path keeps the value out of process listings and shell history.

```bash
# publish a pre-built .vsix (recommended — produced by vsce package)
ovsx publish ./my-ext-1.0.0.vsix

# package-and-publish from source
ovsx publish
ovsx publish --yarn                          # use yarn instead of npm for the build

# publish a pre-release channel build
ovsx publish ./my-ext.vsix --pre-release

# publish a platform-specific build (same target names as vsce)
ovsx publish --target linux-x64 ./linux-x64.vsix
```

The CLI also has:

```bash
# manage stored tokens (interactive — user runs these, not the agent)
ovsx login <namespace>
ovsx logout <namespace>

# inspect what's already published
ovsx get <namespace>.<extension>                 # download latest .vsix
ovsx get <namespace>.<extension> -o ./out.vsix   # to a specific path
ovsx get <namespace>.<extension> --metadata      # JSON metadata, no binary

# verify a PAT is valid
ovsx verify-pat <namespace>
```

Useful flags:

- `-p, --pat <token>` — override the env-var token. Only use this with another env-var name (`-p "$MY_OTHER_PAT"`) — never substitute a literal value.
- `-r, --registryUrl <url>` — publish to a different Open VSX instance (e.g. an internal mirror at a corporate Theia install). Defaults to `https://open-vsx.org`.
- `OVSX_STORE=file` — disable the system keychain (useful in Docker / headless CI containers where `libsecret` isn't installed).

## Post-publish processing

After `ovsx publish` returns, the extension appears with status **Deactivated** while async scanning runs. This usually completes in 5–10 seconds, longer for large extensions. Scans include:

- **Secret detection** — flags leaked AWS keys, GitHub tokens, etc. To suppress a false positive on a specific line, add a `// secret-detector:ignore` comment. Don't blanket-suppress; admins do review escalations.
- **Blocklist** — file hashes are compared against known-malicious artifacts.
- **Namespace similarity** — typosquatting check against existing high-traffic namespaces.

If a publish gets flagged, it stays Deactivated and you'll get notified via the linked Eclipse email. Fix the issue and republish a new patch version — you can't reactivate the same version.

## CI integration

For dual-registry CI, use [`TypeFox/gh-publish-npm`](https://github.com/TypeFox/gh-publish-npm) — see SKILL.md § "Typical CI release flow". It handles both Marketplace and Open VSX in one step with project-local `vsce`/`ovsx`.

For Open VSX only, publish a pre-built `.vsix` with `OVSX_PAT` in the environment (never `-p` on the command line):

```yaml
- run: ovsx publish ./my-ext-1.0.0.vsix
  env:
    OVSX_PAT: ${{ secrets.OVSX_PAT }}
```

Add the CI service account to the namespace as a **Contributor** (not Owner) so a token leak limits blast radius.

## Common errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `Unknown publisher` / namespace doesn't exist | `ovsx create-namespace` was never run, or was run on a different account | Run `ovsx create-namespace <name> -p $OVSX_PAT`. |
| `Insufficient access rights` on publish | Token's user isn't a member of the namespace | Add the user as Contributor or Owner in the namespace settings, or use a different token. |
| `Publisher Agreement not signed` | Eclipse profile is missing the Open-VSX-specific agreement (separate from ECA) | Sign it under the Eclipse account page, then re-publish. |
| Extension shows ⚠️ "unverified" after publish | Namespace has no owner | File the namespace-ownership claim issue (see above). |
| `Mismatching publisher` | `publisher` field in `package.json` doesn't equal the namespace being published to | Make them match — Open VSX won't override the manifest. |
| Publish fails on a clean `.vsix` that worked yesterday | Token expired or was revoked, or scanner blocklisted the artifact | `ovsx verify-pat <namespace>`; check the Open VSX email notification. |
