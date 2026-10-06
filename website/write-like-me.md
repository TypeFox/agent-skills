# Write Like Me

Rewrite AI-generated text so it reads in your own writing voice, driven by a style profile built from documents you wrote yourself.

Source: [skills/write-like-me](https://github.com/TypeFox/agent-skills/tree/main/skills/write-like-me)

## Install

```sh
npx skills add TypeFox/agent-skills -s write-like-me
```

The skill ships three small Python scripts that your agent runs for you. They need Python 3.8 or later and nothing else.

## Background

Text written by an AI agent has a voice of its own, and readers have learned to recognize it. This skill takes such a draft and moves it toward how you write, as a step before your own final read-through, not instead of it.

It works from a profile of your writing habits: how long your sentences run, which words you reach for, which constructions you never use, how you open and close. The profile is built once, from documents you wrote by hand, and every habit in it is backed by counts and quotes from those documents. Nothing in it is guessed, and a rewrite only ever uses forms your own texts show.

Two rules keep a rewrite honest. First, whatever already reads like you is left alone, even if it looks typically machine-made: if you write with em dashes, you keep them. Second, the rewrite aims at how often you do something, not at doing it everywhere. A text that showed every one of your habits at full strength would be a caricature, and no text of yours looks like that.

A rewrite changes the voice and nothing else. Facts, numbers, links, code, headings, the order of sections and the number of list items stay as they were, and a script checks that afterwards. Technical terms and names stay as well, because they belong to the subject, not to your style.

So there are two steps: build your profile once, then rewrite drafts whenever you need to.

## Usage

### Build your profile

The skill builds a profile only when you ask for it and name the documents. It never searches your disk for texts that might be yours.

> write-like-me: extract my style from ~/writing/posts/*.md and ~/writing/emails/*.txt

**What to collect.** At least eight documents with around 6,000 words in total, written by you alone and by hand, as Markdown or plain text. Mix kinds and lengths: blog posts, emails, documentation, notes. Fewer documents still work, but the profile is less certain and the skill says so. Tell the skill which kind each document is, if the folder names do not already say so, because some habits belong to one kind only: an email sign-off must not end up in a blog post.

**Preparing sources.** A few kinds of source need preparation first, and the skill points this out: a file holding a year of emails or issue comments is split into pieces, a PDF is converted to text with its paragraphs intact, and a long single work such as a thesis stays one document.

**Two kinds of habits.** A presence habit is something you do, recorded with how often you do it: around three colons per thousand words, say, within the range your documents cover. An absence habit is something you never do, such as em dashes, and tells the rewrite never to bring it in. The quotes that back a habit are stored with placeholders such as `[colleague]` wherever they named another person, a company, a customer or a product.

**Tiers.** Every habit carries a tier from 1 to 3 that says how sure the profile is that the habit is really yours. Tier 1 is strong evidence: a presence habit that shows in most of your documents and in more than one kind of document, or an absence checked across all of them. Tier 2 is moderate evidence from a few documents. Tier 3 is weak evidence, often a single document. Tiers are computed from the documents, so more documents raise them, and the review round can override them. When a draft is rewritten, the strictness setting says which tiers may be applied; see Rewrite a draft.

**What happens.**

1. The skill checks each document for signs of AI assistance and asks about the ones that stand out. Texts from before AI writing tools are the safest anchor.
2. If one kind of document holds more than half the words, it asks whether to balance the kinds, so that the profile does not turn into a profile of just your emails.
3. It reads everything, finds habits, counts them, and verifies every quote against the source.
4. It opens a review round: a short list of questions, each with a recommended answer that you accept or change. The questions come through your agent's question prompt where it has one, otherwise as a numbered list in the chat. You never edit the profile file yourself. The questions cover:
   - Quotes: is each placeholder enough, and may every remaining name stay?
   - Habits that may come from the topic rather than from you. A word that turns up only because of what you wrote about is removed.
   - Rare constructions, seen a few times across all your documents. The recommended answer files them as an absence at tier 2: the default strictness removes them from drafts, a light touch leaves them in. Tier 1 removes them at every setting, tier 3 only on "go all in". If it is a habit you have but use sparingly, say so, and it stays a presence at tier 3, which the default setting leaves alone.
   - Habits confined to one kind of document, such as a sign-off that appears only in emails.
   - Habits that were counted by reading rather than by script, since those counts are estimates.

   Beyond the questions, you can mark any habit as overstated, which lowers its tier, or point at one the skill missed, which it adds and counts.
5. It writes the profile to `~/.agents/write-like-me/user-style.json`, backs up any profile already there as `user-style_old.json` beside it, and prints a readable summary. It then offers to seal the profile, which drops the file names of your documents from it. The unsealed copy stays next to your documents for later refreshes.

**Growing the profile.** When you have written more since, name the new documents and the skill merges them into the existing profile instead of starting over. The review round then runs again.

### Rewrite a draft

The skill activates when you ask to make a draft sound like you, match your style or tone, remove the AI feel from a text, or polish something before it goes out under your name. Paste the text or give file paths.

> Make this release announcement sound like me.

> Rewrite docs/intro.md in my voice, light touch.

> This reads too clinical. Make it warmer, but keep it factual.

**Without a profile, nothing is rewritten.** The skill tells you where it looked and offers two ways forward: strip the typical machine habits without adding anyone's voice, or build your profile first.

**Strictness.** The strictness setting picks which tiers the rewrite may apply, and so how much of the draft stays as it is. The default applies tiers 1 and 2. Say "light touch" or "just the obvious" for the soft setting, which applies tier 1 only. Say "go all in" for the hard setting, which applies all three, including habits backed by thin evidence. A softer setting is a shorter list of changes, not a gentler hand on each one.

**Tone.** Strictness says how much evidence a change needs. Tone says which end of your own range to aim for. Asking for "more formal" or "warmer" steers toward the end your matching documents show. The skill cannot produce a tone your documents never show, and says so instead of inventing one.

**Earlier edits.** When a draft has been edited by hand before, the skill asks once which of those edits must survive.

**The result.** Pasted text comes back in the reply. A file gets a copy named `<name>.styled.<ext>` beside it, and the original is never overwritten. Long documents are rewritten section by section.

**The report.** Every rewrite ends with an account of what changed, what already matched you, what was left for you to decide, and where the text could not be brought into your range without inventing material. A short input gets one line, a document gets the full report.

**Polishing your own text.** Say that the text is yours, and the skill checks it against your profile alone, for consistency with the rest of your writing.

**A personal skill.** Once your profile is reviewed, you can ask the skill to turn it into a stand-alone `write-like-<name>` skill: one file, no scripts, that rewrites drafts in your voice at lower cost. It gives up the counting and the report, so keep write-like-me around for profile refreshes and exact figures.
