# Review With Me

Review a diff, branch, or pull request together with your agent. It asks you about the change one question at a time until you agree on every point, then sums up the agreed feedback.

Source: [skills/review-with-me](https://github.com/TypeFox/agent-skills/tree/main/skills/review-with-me)

## Install

```sh
npx skills add TypeFox/agent-skills -s review-with-me
```

## Usage

The skill activates when you ask to review a change together, for example with "review with me" or "help me review".

> Help me review the changes on this branch before I approve the PR.

The agent then walks through the change part by part:

1. **One question at a time.** Each question covers one concern and comes with the agent's recommended answer. Agree, disagree, or add context, and the agent moves on to the next question. Anything the code itself can answer, the agent looks up instead of asking you.
2. **Summary.** Once every question is settled, you get one line per agreed item, requested changes first:

   ```
   src/retry.ts (17): CHANGE rethrow the last error so callers can still detect a 404
   docs/retry.md (5): NOTE mention the delay cap once it exists
   ```

   `CHANGE` marks something the author must address; `NOTE` marks a question, a nit, or an observation that does not block. Line numbers refer to the reviewed revision.

The skill does not change your files or file the review anywhere. You decide what to send to the author.

### When not to use it

If you want a finished review report without the conversation, or want the agent to fix the code instead of reviewing it, ask for that directly; this skill is built around the back and forth.
