I gave a talk last month and the demo failed. Not the fun kind of failure where you laugh it off: the projector showed a stack trace for a full minute while I typed the wrong command three times.

So here's what I've changed for next time, mostly for my own benefit (writing it down is how I remember).

The demo now runs from a script. Every command I'd type is in a file, in order, and the talk just steps through it. I realise this makes the demo less "live", but honestly the audience doesn't care whether I typed it. They care whether it works. The trick is to keep the script visible on screen, so they can see what's being run and it doesn't feel like a video.

I also cut the demo in half. The original had eleven steps and each one depended on the previous one, which means one typo at step four kills steps five to eleven. The new one has five steps and three of them work on their own. If step two dies, I can skip to step four and nobody notices.

There's a network bit I couldn't remove (the whole point is that the tool talks to a server). For that I've got a recorded response on disk, and a flag that makes the tool read from the recording instead of the network. Conference wifi is a coin toss and I'm done betting on it.

And I've started doing a full run-through the night before, on the actual laptop, on the actual resolution of the projector. The stack trace last time was a font size problem: the output was fine at my desk and unreadable at 1024 by 768. Neat lesson. Expensive way to learn it.

None of this is clever. It's just the stuff I'd tell a colleague, and then not do myself because the demo worked fine at my desk.

It always works fine at my desk.
