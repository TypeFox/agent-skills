# Bundled data

This directory will hold `ai-style-patterns.json`, the AI style-patterns DB: patterns extracted from a corpus of AI-generated documents with the technique in `../references/technique.md` (see its maintainer note), in the format of `../references/db-schema.md` with `"kind": "ai"`.

**TODO:** the AI DB does not exist yet. Until it ships, processing uses the built-in `ai_*` counters of `../scripts/textstats.py` as the AI-evidence column of the comparison table, and the author's absence patterns as the do-not-introduce list. Once the file is here, `textstats.py measure --db user.json --db data/ai-style-patterns.json` measures both in one run, and SKILL.md's DB checks should extend to it (version check, kind `ai`, `partial: false`).
