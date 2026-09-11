Hi Sam,

Quick one about the 2.4 release: I've pushed the tag but I haven't published the package yet, because the changelog has a hole in it. The filesystem changes from last week aren't in there (my fault, I wrote them up in the PR and forgot to copy them across).

So two things I'd like from you before I hit publish. Have a look at the changelog draft in the release branch and tell me if the wording for the config change makes sense to someone who didn't write it (I've read it so often I can't see it any more). And if you've got ten minutes, run the CLI once on your machine, because I only tested on mine and it's a Mac.

I'm not in a rush. Tomorrow morning is fine, honestly. If anything looks off, just reply here and I'll sort it before publishing.

One more thing: the docs site build is flaky again. Not blocking, but I'd rather we don't ship a release note that points at a page that's a 404 half the time.

Cheers,
Jo
