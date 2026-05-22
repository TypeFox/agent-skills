# VS Code Marketplace specifics

The VS Code Marketplace (`marketplace.visualstudio.com`) is operated by Microsoft as part of Azure DevOps. Identity, billing, and authentication all flow through a Microsoft account and an Azure DevOps organization, which is the part most users haven't seen before.

## Identity model

Two things you have to register before the first publish:

1. **Azure DevOps account + organization.** This is what owns the Personal Access Token used by `vsce`. Anyone with a Microsoft account can create one for free at https://dev.azure.com.
2. **A Marketplace publisher.** This is the `publisher` field in `package.json`. Created separately at https://marketplace.visualstudio.com/manage. The publisher ID becomes part of the marketplace URL (`marketplace.visualstudio.com/items?itemName=<publisher>.<extension>`) and **cannot be changed** once chosen.

Both must use the **same Microsoft account**, or `vsce login` will succeed against Azure DevOps but every publish will return 401/403 — a confusing failure mode worth checking first when authentication looks broken.

## Create the Personal Access Token (PAT)

1. Sign in at https://dev.azure.com with the Microsoft account that will own the publisher.
2. Click your avatar → **User settings** → **Personal access tokens**.
3. **New Token** with:
   - **Organization**: `All accessible organizations` (not just the current one — Marketplace lives in a separate Microsoft-owned org, so a single-org PAT will 401).
   - **Expiration**: up to 1 year. Set a calendar reminder; expired PATs are the most common publish failure.
   - **Scopes**: `Custom defined` → **Show all scopes** → **Marketplace** → tick **Manage**. (Default scopes do not include Marketplace at all.)
4. Copy the token immediately — it's shown only once.

## Create the publisher

1. Visit https://marketplace.visualstudio.com/manage, signed into the same Microsoft account.
2. **Create publisher**:
   - **ID**: permanent. Lowercase letters/numbers/hyphens. This is what goes in `package.json`'s `publisher` field. Choose carefully — see the note on Open VSX namespace parity in `open-vsx.md`.
   - **Name**: display name shown on the extension page. Can be changed later.
3. Save.

## Authenticate `vsce`

See SKILL.md § "Handling access tokens" first — the token must never enter the chat.

For an agent-driven publish, set `VSCE_PAT` in the shell that launches the agent; `vsce publish` reads it automatically, no login step required.

For interactive local use, the user can run `vsce login <publisher-id>` and paste the PAT when the CLI prompts for it. That value lands in the OS keychain (macOS Keychain, Windows Credential Manager, libsecret on Linux) and subsequent `vsce publish` calls reuse it. The agent should not invoke `vsce login` itself — there's nothing useful it can do with the prompt.

## Publishing commands

```bash
# package-and-publish in one step (also bumps the version)
vsce publish patch
vsce publish minor
vsce publish major
vsce publish 1.5.3

# publish a pre-built .vsix
vsce publish --packagePath ./my-ext-1.0.0.vsix

# publish a pre-release channel build
vsce publish --pre-release

# publish a platform-specific build
vsce publish --target win32-x64 --packagePath ./win32-x64.vsix
```

When invoked inside a git repository on a clean tree, `vsce publish <semver>` also creates a version-bump commit and tag. Suppress with `--no-git-tag-version`; override the commit message with `-m "Release v%s"`.

## Verified publisher badge

The blue checkmark next to a publisher name. Eligibility:

- Publisher must have an extension on the marketplace for at least **6 months**.
- The domain you're verifying must be registered for at least **6 months**.
- You must control DNS for the domain.

Process:

1. Publisher details page → **Verified domain** → enter the domain.
2. Marketplace shows a TXT record value.
3. Add it under the apex domain in your DNS provider. Subdomains are not eligible.
4. Click **Verify**.
5. Microsoft reviews within ~5 business days.

The domain must serve HTTPS and return HTTP 200 on `HEAD /`.

## Unpublish vs. remove

These are not the same operation, and only one is recoverable.

- **Unpublish** (recoverable): hides the extension from search and installs, but preserves stats, reviews, and the name. Done from the management page: **More Actions** → **Unpublish**.
- **Remove** (irreversible): wipes the extension and **permanently reserves the name** — nobody, including you, can ever publish another extension under that `publisher.extension` pair. Done via `vsce unpublish <publisher>.<extension>` or **More Actions → Remove**.

Use unpublish for "this was a mistake, I'll re-release shortly." Use remove only when the extension shouldn't exist (compromise, mistaken trademark, etc.).

## Deprecation

Marketplace doesn't expose deprecation via `vsce` — request it by filing a discussion at https://github.com/microsoft/vscode-discussions/discussions/1. You can deprecate with:

- no replacement,
- a pointer to an alternative extension, or
- a pointer to a built-in setting that subsumes the functionality.

The marketplace renders the extension's name struck-through with a yellow warning icon, and (if alternatives are configured) offers users a **Migrate** button.

## Common errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Unauthorized` on every publish | PAT scope is `User Profile` only, not `Marketplace (Manage)` | Reissue PAT with the right scope; do not edit existing PAT scopes — Azure DevOps doesn't let you. |
| `403 Forbidden` on every publish | PAT organization is "current" not "All accessible organizations" | Reissue PAT with `All accessible organizations`. |
| `Make sure to edit your publisher` / publisher not found | The Microsoft account that owns the PAT is not the account that owns the publisher | Re-create one of them under the matching account. |
| `You exceeded the number of allowed tags of 30` | `keywords` array > 30 entries | Trim `keywords` in `package.json`. |
| `Missing publisher name` | `publisher` field absent from `package.json` | Add it. `vsce` cannot infer it. |
| `ERR_INVALID_ARG_TYPE … repository` | `repository` is a string not an object | Use `{ "type": "git", "url": "..." }` form. |
| Extension shows but icon is missing | Icon is SVG, or smaller than 128×128, or the path in `package.json` doesn't match the file shipped in the `.vsix` | Re-export as ≥128×128 PNG; verify with `vsce ls`. |
| `Extension name already taken` | Someone (possibly you, under another account) reserved this `publisher.extension` pair | Pick a new extension name; remember `remove` is permanent. |

## Inspecting before publish

```bash
vsce ls           # list files that will be packaged
vsce show <publisher>.<extension>   # show current marketplace metadata
vsce package --no-yarn   # force npm even when yarn.lock is present
```

Running `vsce ls` before the first publish catches almost every "I accidentally shipped my `.env`" disaster.
