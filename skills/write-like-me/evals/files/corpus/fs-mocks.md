Last Tuesday the build broke for the third time in a week, and every failure was in a test that mocked the filesystem. Not the code under test. The mock.

So I ripped them out. All forty-one of them (I counted, because I wanted to be angry at a specific number).

Here's what those tests actually did: they set up a fake directory tree in memory, ran the function, and asserted that the fake had been asked the right questions. Which means they tested the conversation with the mock, not the behaviour of the code. Rename a method on the real filesystem wrapper and the tests stay green while production falls over. I've watched it happen. Twice.

The replacement is boring: a real temp directory, real files, delete everything afterwards. It's slower, honestly. The whole suite went from four seconds to seven. I'll take that trade every day, because the seven-second version has caught two actual bugs since, and the four-second version caught none in a year.

There's a fiddly bit, and it's Windows. File handles stay open longer than you'd think, so the cleanup step needs a retry (three attempts with a short sleep did it for me). That's the kind of thing you only learn from real files. A mock would never have told me.

I realise this isn't a new idea. People have been saying "don't mock what you don't own" for ages, and I nodded along and kept doing it, because the mocks were already there and the tests were already green. Green is comfortable.

The trick is to notice when the comfort is the problem. Forty-one tests told me nothing for a year, and I only found out when they started lying loudly enough to break the build.

Anyway. Real files. Temp directory. Retry the cleanup on Windows. That's the whole post.
