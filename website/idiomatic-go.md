# Idiomatic Go

Apply Go community idioms for API and package design, errors, concurrency, naming and generics, including in code review.

Source: [skills/idiomatic-go](https://github.com/TypeFox/agent-skills/tree/main/skills/idiomatic-go)

## Install

```sh
npx skills add TypeFox/agent-skills -s idiomatic-go
```

## Background

Go was designed at Google from 2007 on by Robert Griesemer, Rob Pike and Ken Thompson, and released as open source in 2009. It is a deliberately small language: few features, few ways to express the same thing, and a standard formatter, `gofmt`, that ends every debate about layout before it starts. The community took that attitude further than the language itself. There is usually one accepted way to name a type, to handle an error, or to shape an API, and Go reviewers expect it. A pull request that works but reads like Java or TypeScript in Go syntax gets sent back.

The accepted ways are written down. [Effective Go](https://go.dev/doc/effective_go) is the original guide from the Go team, and the [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) wiki page lists the remarks reviewers make over and over. Rob Pike condensed the attitude into the [Go Proverbs](https://go-proverbs.github.io/), and large Go shops such as [Google](https://google.github.io/styleguide/go/) and [Uber](https://github.com/uber-go/guide/blob/master/style.md) publish style guides that spell out the same rules for their own codebases. Together these documents describe what the community means by idiomatic Go.

The most prominent idioms:

- **Clear is better than clever.** When a concise construction and a plain one do the same thing, Go picks the plain one. Code is read far more often than it is written, and it outlives its author.
- **Errors are values.** A function that can fail returns an `error` as its last result, and the caller checks it right away. There are no exceptions to catch further up. Errors are wrapped with context as they travel up the stack, and their messages are lowercase without trailing punctuation so that a chain of them reads as one sentence. `panic` is reserved for broken invariants, never for expected failures.
- **Line of sight.** The happy path runs down the left margin of a function. Each error check returns early in an indented block, so the reader follows the normal flow from top to bottom without tracking nested branches.
- **Naming.** Names use MixedCaps, never underscores. Initialisms keep one case throughout: `userID`, `ServeHTTP`, `parseJSON`. Package names are short and lowercase, and a type does not repeat its package name, because callers already write `bytes.Buffer`. Getters have no `Get` prefix. Receivers get a short name, the same for every method on the type. The length of a variable name grows with the distance between its declaration and its use.
- **Small interfaces, defined by the consumer.** An interface describes the few methods a caller needs, like `io.Reader` with its single method, and lives in the package that calls it, not in the package that implements it. Functions accept interfaces and return concrete types. The bigger the interface, the weaker the abstraction.
- **Make the zero value useful.** A type should work straight from `var x T` without a constructor, the way `bytes.Buffer` and `sync.Mutex` do.
- **Structs are values.** Assignment, passing and `range` all copy a struct. A method that changes its receiver takes a pointer, and a type keeps the same receiver kind for all its methods.
- **Share memory by communicating.** Channels hand ownership of a value from one goroutine to the next. Mutexes guard state that several goroutines share. Both are idiomatic, and the choice follows what the data represents. Every goroutine has a known way to end, and every function that does I/O takes a `context.Context` as its first parameter so the caller can cancel it. APIs are synchronous by default. Whoever wants concurrency adds the `go` keyword.
- **Generics last.** Write the plain function first and add type parameters only when the same logic would be duplicated for several types. When a caller needs only methods, an interface parameter reads better than a type parameter.

For an agent, the hard part is not knowing these rules but applying them consistently. Models carry habits from other languages into Go, and the result compiles and often works. That is why the skill is filtered to the rules that strong models still slip on, and leaves out syntax and the well-known mechanics.

## Usage

The skill activates when you write or review Go code that involves design choices: an API or package layout, error handling, concurrency, naming, generics, a pull request or diff review, or a question about "the Go way". It also covers Go tooling for programming languages (parsers, language servers, type checkers, validators, DSLs), which gets its own reference with patterns beyond baseline idiomatic Go, such as nil-safe AST navigation, lazy scope chains and incremental builds. The skill stays out of the way for trivial one-line edits, and it leaves doc comments to the [Go Documentation](/go-documentation) skill.

> Review this package and rewrite it the way an experienced Go developer would.

> I'm coming from TypeScript and this is my first Go service. Go through it and point out where I'm writing TypeScript in Go syntax.

The skill treats its rule sections as a checklist and walks every one, so a review reports each violation with the idiom it breaks and the concrete fix rather than stopping at the first few. Where a rule needs a recent Go version, the skill says which one.
