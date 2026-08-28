# DB migrations

Migrations between `db_version` values, oldest first. `scripts/styledb.py info DB` exits 2 when a DB is older than the skill; apply the sections from the DB's version up to the skill's, in order, then run `styledb.py validate DB --fix` and re-run `info`.

There are no migrations yet: `db_version` 1 is the first format, and every DB in existence is at version 1.

## How to add one

When a change to [db-schema.md](db-schema.md) or the taxonomy bumps `CURRENT_DB_VERSION` in `scripts/styledb.py`, add a section here:

```
## 1 → 2

What changed and why it broke old DBs.

Steps (a script under scripts/ where the change is mechanical; instructions for a
re-extraction where it is not):
1. …
```

Prefer a mechanical migration when the old data can be mapped; fall back to "re-run extraction on the corpus recorded in the DB manifest" when it cannot — the manifest exists so that a re-extraction is always possible.
