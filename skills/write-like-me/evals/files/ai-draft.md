# Why We Moved Away From Mocking the Filesystem

In today's fast-paced world of software development, testing strategies are constantly evolving. Our team recently made a significant decision — we stopped mocking the filesystem in our test suite entirely. This wasn't just a technical change; it was a fundamental shift in how we think about what our tests are really verifying, and it reshaped the way we approach test design across the whole codebase.

The change did not happen overnight. It emerged from a sustained period of frustration, several uncomfortable production incidents, and a growing suspicion that our reassuringly green test suite was telling us a story that had very little to do with reality.

## The Problem With Mocks

Mocking the filesystem seemed like the obvious choice — it's fast, it's isolated, and it's deterministic. However, over time we noticed a troubling pattern. Our tests were passing, but our production code was failing. The mocks had gradually become a comprehensive simulation of a filesystem that didn't actually exist anywhere, highlighting the importance of testing against real behavior rather than convenient assumptions.

The core issue is that mocks test the conversation with the mock, not the behavior of the code. When a method on the real filesystem wrapper was renamed, all 41 tests remained green — while the application crashed in production. This happened not once, but twice.

Furthermore, the maintenance burden turned out to be substantial. Every time the wrapper's interface changed, someone had to update the corresponding mock expectations across dozens of test files. That work produced no verification value whatsoever; it merely restored the illusion that the suite was meaningful. It's worth noting that this ongoing maintenance cost is rarely accounted for when teams reach for mocking libraries in the first place.

There is a deeper problem as well: a mock encodes an assumption about how the underlying system behaves, and that assumption is written by the same person who wrote the code under test. When the assumption is wrong, the mock and the code are wrong together, in perfect agreement, and the test suite has no mechanism by which it could ever notice. The tests become a mirror rather than a check.

## Our New Approach

We replaced every mock with a real temporary directory. The approach is straightforward, robust, and surprisingly effective:

- Create a temp directory before each test
- Run the function under test against real files
- Clean up everything afterward

It's worth noting that this comes at a cost. The test suite went from 4 seconds to 7 seconds. Furthermore, we had to handle a platform-specific edge case on Windows, where file handles remain open longer than expected. The solution was a retry loop:

```python
for attempt in range(3):
    try:
        shutil.rmtree(tmpdir)
        break
    except PermissionError:
        time.sleep(0.1)
```

Additionally, we standardized on the pytest tmp_path fixture rather than managing temporary directories by hand. This eliminated an entire category of cleanup bugs — tests that leaked directories, tests that collided with one another, and tests that failed only when run in a particular order. The fixture handles all three concerns without any configuration on our part.

The migration itself was less dramatic than anticipated: we converted the suite module by module over roughly 3 weeks, keeping both approaches running in parallel until every module had been moved across. At no point was the suite unusable, which mattered a great deal for a team shipping continuously.

## The Results

Since making this change, the results have been clear and measurable:

| Metric | Before | After |
|---|---|---|
| Suite duration | 4 s | 7 s |
| Real bugs caught (12 months) | 0 | 2 |
| Mocked tests | 41 | 0 |

The seven-second suite has caught two genuine bugs that the mocked version would have missed entirely. The first was a path-handling error that only manifested when a directory name contained a space. The second was a permissions bug that appeared exclusively on continuous integration, where the process runs under a different user than it does locally.

Additionally, the Windows retry behavior is something we would never have discovered with mocks — it's a lesson that only real files could teach us. A simulated filesystem releases its handles the instant the test asks it to, because that is what the simulation was written to do.

There were second-order benefits as well: new contributors read the tests and understand them immediately, since the tests now describe what the code does rather than which methods it calls. Code review became easier for the same reason. It's worth noting that neither benefit appeared in our original justification for the change; both emerged only after we had lived with the new approach for a while.

## What We Would Do Differently

The single thing we would change is the sequencing: we converted the noisiest modules first, which felt satisfying but delayed the moment when the suite as a whole became trustworthy. Starting with the modules that had the most production incidents behind them would have surfaced real bugs sooner.

This isn't a new idea, of course. The principle of "don't mock what you don't own" has been discussed extensively in the testing community, and resources like [Martin Fowler's article on test doubles](https://martinfowler.com/bliki/TestDouble.html) and the [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) cover the ground thoroughly. However, the challenge isn't knowing the principle — it's recognizing when comfort with existing green tests is preventing you from applying it.

## Conclusion

In conclusion, moving away from filesystem mocks has made our tests slower, more reliable, and more valuable. By embracing real files, real directories, and real cleanup, we've built a test suite that actually reflects production behavior rather than our assumptions about it. The key takeaway is simple: when your tests are comfortable, ask yourself whether that comfort is hiding a problem. Real files, a temp directory, and a retry on Windows — that's the whole story.
