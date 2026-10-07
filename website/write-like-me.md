# Write Like Me

Rewrite AI-generated text so it reads as if you wrote it, driven by a style profile built from your own hand-written documents.

Source: [skills/write-like-me](https://github.com/TypeFox/agent-skills/tree/main/skills/write-like-me)

## Install

```sh
npx skills add TypeFox/agent-skills -s write-like-me
```

The skill ships three small Python scripts, which the agent runs on its own. They need Python 3.8 or later and don't depend on anything else.

## Background

Text written by an AI agent has a voice of its own, and readers have learned to recognize it. This skill takes such a draft and moves it toward your own style. This is meant as the step before your final read-through, not instead of it.

It works from a profile of your writing habits (how long the sentences run, which words recur, which constructions never show up, how a text opens and closes). The profile is built once from hand-written documents, and each habit in it is backed by counts and quotes from those documents. Nothing in it is guessed, and a rewrite uses only forms found in those documents.

Two rules keep a rewrite honest. First, whatever already reads like you is left alone, even if it looks typically machine-made: if you write with em dashes, you keep them. Second, the rewrite aims at how often a habit occurs, not at using it everywhere. A text that showed each habit at full strength would be a caricature (no text of yours looks like that).

A rewrite changes only the voice. Facts, numbers, links, code, headings, the order of sections and the number of list items stay as they were, and a script checks that afterwards. Technical terms and names stay as well, because they belong to the subject, not to your style.

So there are two steps: build the profile once, then rewrite drafts whenever needed.

## Usage

### Build your profile

The skill builds a profile only on explicit request, with the documents named. It doesn't search the disk for texts that might be yours.

> write-like-me: extract my style from ~/writing/posts/*.md and ~/writing/emails/*.txt

**What to collect.** At least eight documents with around 6,000 words in total, written by you alone and by hand (Markdown or plain text). Mix kinds and lengths, e.g. blog posts, emails, documentation and notes. Fewer documents still work. However, the profile is less certain and the skill says so.

**Registers.** The skill calls each kind of document a *register*: blog post, email, documentation, note. Every document you name gets one, from its folder name or from what you tell the skill, and the skill doesn't ask you to confirm it, so name the kinds precisely. The register is where a habit lives. A sign-off seen only in your emails is recorded as an email habit, and a habit you use at different rates in different kinds (one *I* per page in articles, ten in emails) is recorded with both rates.

**Preparing sources.** Several kinds of source need preparation first, and the skill points this out: a file holding a year of emails or issue comments is split into pieces, a PDF is converted to text with its paragraphs intact, and a long single work such as a thesis stays one document.

**Two kinds of habits.** A *presence* habit is something you do, recorded with its frequency: around three colons per thousand words, say, within the range the documents cover. An *absence* habit is something you never do (em dashes, for example), and the rewrite doesn't bring it in. The quotes that back a habit are stored with placeholders such as `[colleague]` wherever they named another person, a company, a customer or a product.

**Tiers.** Each habit carries a tier from 1 to 3 that says how sure the profile is that the habit is really yours. Tier 1 is strong evidence: a presence habit that shows in most of the documents and in more than one register, or an absence checked across all documents. Tier 2 is moderate evidence from a few documents. Tier 3 is weak evidence, often a single document. Tiers are computed from the documents, which means that more documents raise them, and the review round can override them. When a draft is rewritten, the strictness setting decides which tiers may be applied (see below).

**What happens.**

1. The skill checks each document for signs of AI assistance and asks about the ones that stand out. Texts from before AI writing tools are the safest anchor.
2. If one register holds more than half the words, it asks whether to balance the registers, so that the profile doesn't turn into a profile of just your emails.
3. It reads all documents, finds habits, counts them, and verifies each quote against the source.
4. It opens a review round with a short list of questions, each with a recommended answer to accept or change. The questions come via the agent's question prompt where it has one, otherwise as a numbered list in the chat. You don't edit the profile file yourself. The questions cover the following topics:
   - Quotes: is each placeholder enough, and may the remaining names stay?
   - Habits that may come from the topic rather than from you. A word that turns up only because of the subject is removed.
   - Rare constructions, seen a few times across all documents. The recommended answer files them as an absence at tier 2: the default strictness removes them from drafts, a light touch leaves them in. Tier 1 removes them at any setting, tier 3 only on "go all in". If it's a habit you have but use sparingly, say so, and it stays a presence at tier 3, which the default setting leaves alone.
   - Habits confined to one register.
   - Habits that were counted by reading rather than by script, since those counts are estimates.

   Beyond the questions, you can mark any habit as overstated, which lowers its tier, or point at one the skill missed, which it adds and counts.
5. It writes the resulting profile to `~/.agents/write-like-me/user-style.json`, backs up an existing profile as `user-style_old.json` beside it, and prints a readable summary. It then offers to seal the profile, which drops the file names of the source documents from it. The unsealed copy stays next to your documents for later refreshes.

**Growing the profile.** After writing more, name the new documents and the skill merges them into the existing profile instead of starting over. The review round then runs again.

### Rewrite a draft

The skill activates on requests to make a draft sound like you, match your style or tone, remove the AI feel from a text, or polish something before it goes out under your name. Paste the text or give file paths.

> Make this release announcement sound like me.

> Rewrite docs/intro.md in my voice, light touch.

> This reads too clinical. Make it warmer, but keep it factual.

**Without a profile, nothing is rewritten.** The skill says where it looked and offers two ways forward: strip the typical machine habits without adding anyone's voice, or build the profile first.

**Strictness.** The strictness setting picks which tiers the rewrite may apply, and so how much of the draft stays as it is. The default applies tiers 1 and 2. Say "light touch" or "just the obvious" for the soft setting, which applies tier 1 only. Say "go all in" for the hard setting, which applies all three (including habits backed by thin evidence). A softer setting is a shorter list of changes, not a gentler hand on each one.

**Tone.** Strictness says how much evidence a change needs, while tone says which end of your own range to aim for. Asking for "more formal" or "warmer" steers toward the end your matching documents show. The skill can't produce a tone that's missing from your documents, and says so instead of inventing one.

**Register.** The skill names the kind of document the draft is (an email, a blog post, documentation) and reads your profile for that kind. A habit confined to another register is set aside, and where your profile has enough documents of the draft's kind, their rates are the target instead of the average over everything you wrote. Say which kind the draft is when it isn't obvious, or say that the kind doesn't matter and every habit applies. A kind your profile has no documents of is allowed, but then the profile has no evidence about it.

**Earlier edits.** When a draft has been edited by hand before, the skill asks once which of those edits must survive.

**The result.** Pasted text comes back in the reply. A file gets a copy named `<name>.styled.<ext>` beside it, and the original isn't overwritten. Long documents are rewritten section by section.

**The report.** Each rewrite ends with an account of what changed, what already matched your style, what was left for you to decide, and where the text couldn't be brought into your range without inventing material. A short input gets one line, a document gets the full report.

**Polishing your own text.** Say that the text is yours, and the skill checks it against the profile alone, for consistency with the rest of your writing.

**A personal skill.** Once the profile is reviewed, you can ask the skill to turn it into a stand-alone `write-like-<name>` skill (one file, no scripts) that rewrites drafts in your voice at lower cost. It gives up the counting and the report, so keep write-like-me around for profile refreshes and exact figures.
