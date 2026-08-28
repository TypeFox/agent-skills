# Why We Moved Away From Mocking the Filesystem

In today's fast-paced world of software development, testing strategies are constantly evolving. Our team recently made a significant decision — we stopped mocking the filesystem in our test suite. This wasn't just a technical change; it was a shift in how we think about what our tests are really verifying.

## The Problem With Mocks

Mocking the filesystem seemed like the obvious choice — it's fast, it's isolated, and it's deterministic. However, over time we noticed a troubling pattern. Our tests were passing, but our production code was failing. The mocks had become a comprehensive simulation of a filesystem that didn't actually exist, highlighting the importance of testing against real behavior rather than assumptions.

The core issue is that mocks test the conversation with the mock, not the behavior of the code. When a method on the real filesystem wrapper was renamed, all 41 tests remained green — while the application crashed in production. This happened not once, but twice.

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

## The Results

Since making this change, the results have been clear:

| Metric | Before | After |
|---|---|---|
| Suite duration | 4 s | 7 s |
| Real bugs caught (12 months) | 0 | 2 |
| Mocked tests | 41 | 0 |

The seven-second suite has caught two genuine bugs that the mocked version would have missed entirely. Additionally, the Windows retry behavior is something we would never have discovered with mocks — it's a lesson that only real files could teach us.

This isn't a new idea, of course. The principle of "don't mock what you don't own" has been discussed extensively in the testing community, and resources like [Martin Fowler's article on test doubles](https://martinfowler.com/bliki/TestDouble.html) and the [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) cover it well. Ultimately, the challenge isn't knowing the principle — it's recognizing when comfort with existing green tests is preventing you from applying it.

## Conclusion

In conclusion, moving away from filesystem mocks has made our tests slower, more reliable, and more valuable. By embracing real files, real directories, and real cleanup, we've built a test suite that actually reflects production behavior. The key takeaway is simple: when your tests are comfortable, ask yourself whether that comfort is hiding a problem. Real files, a temp directory, and a retry on Windows — that's the whole story.
