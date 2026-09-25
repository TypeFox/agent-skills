# tidy

A small command that tells you which files in a directory nobody has touched in a while, and optionally moves them out of the way. I wrote it because my downloads folder had 3,000 files in it and I couldn't face sorting them by hand.

## how it works

Run it in a directory. It lists every file older than the threshold (30 days by default) with its size and last access time. Nothing is moved unless you say so: the default is a dry run, always.

```sh
tidy            # list stale files
tidy --move     # move them into ./stale/
tidy --days 90  # be more patient
```

The output is plain text, one file per line, sorted by age. Which means you can pipe it into anything.

## the fiddly bits

Access times are unreliable on some filesystems (many mount with noatime, so "last access" is really "last modified"). tidy uses whichever is newer and tells you which one it picked.

Moving files across devices is a copy plus a delete, not a rename. On a slow disk that takes a while. There's a progress line, so you know it hasn't hung.

## things it won't do

- delete anything (it moves, you delete)
- follow symlinks
- touch hidden files unless you pass --all

That's on purpose. I'd rather it does less and I trust it.

## install

Copy the script somewhere on your path. It's one file and it needs nothing but Python 3.
