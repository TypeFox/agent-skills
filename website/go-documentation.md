# Go Documentation

Write Go doc comments that render correctly on pkg.go.dev, add testable examples, and publish or debug modules there.

Source: [skills/go-documentation](https://github.com/TypeFox/agent-skills/tree/main/skills/go-documentation)

## Install

```sh
npx skills add TypeFox/agent-skills -s go-documentation
```

## Background

### Doc comments

Go keeps documentation in the source. A doc comment is an ordinary `//` comment placed directly above a top-level declaration, and the toolchain reads it from there. `go doc` prints it in the terminal, the IDE shows it on hover, and [pkg.go.dev](https://pkg.go.dev) renders it as the public reference page of the package. All three use the same parser, so a comment that follows the rules looks right everywhere, and a comment that breaks them looks wrong everywhere.

The rules are short, and they are an official specification at [go.dev/doc/comment](https://go.dev/doc/comment) rather than a style preference. Since Go 1.19, `gofmt` reformats doc comments to that syntax. These are the rules that matter most:

- **Placement is the only binding.** The comment must sit immediately before the `package`, `type`, `func`, `const` or `var` it documents, with no blank line in between. A blank line turns it into an unrelated comment. The text is still in the source, but the symbol appears on pkg.go.dev without documentation.
- **The first sentence names the symbol.** `Package json implements ...`, `A Reader serves ...`, `Quote returns ...`, `HasPrefix reports whether ...`. Tools show the first sentence on its own as a one-line summary, in `go doc` listings, IDE completions and pkg.go.dev search results, so it has to make sense without the signature next to it.
- **There are no tags and almost no markup.** Nothing like `@param` or `@returns` exists. Parameters and results are described in prose by name, and their types are in the signature. The markup Go knows is paragraphs, one heading level, lists, bare URLs, reference-style links, doc links like `[Name]` or `[pkg.Name]` that resolve to symbols, and code blocks, which are simply lines indented by a tab. Everything else from Markdown renders literally or worse: backticks become curly quotes, `**bold**` prints the asterisks, a `[text](url)` link stays text, and any indented line becomes a code block.
- **Examples are code, not snippets.** A usage example is a function named `ExampleFoo` in a `_test.go` file. `go test` compiles it, compares its printed output against a `// Output:` comment, and pkg.go.dev renders it next to `Foo`. An example cannot drift from the API, because a rename breaks the test.
- **The package comment is the landing page.** pkg.go.dev shows it above the API, and `go doc` prints it as the package overview. By convention it lives in a file named `doc.go`. A README is still useful, but it serves a different reader: someone deciding whether to use the module. Once the module is imported, the README disappears from daily work and the package comment is what developers see.
- **Deprecation is a paragraph.** A paragraph that begins with `Deprecated:` marks a symbol as deprecated. pkg.go.dev folds the symbol away and linters flag its uses. There is no annotation for it.

Developers who come from JSDoc or TSDoc tend to bring all of their habits at once: tags, backticks, Markdown links, `/** */` block comments. Each of them produces a comment that reads fine in the editor and renders broken on pkg.go.dev.

### Publishing

There is no publish step for a Go module. No registry account, no upload, no `go publish`. You push a Git tag with a semantic version such as `v1.2.3`, and the rest happens on request:

1. Someone asks for that version, by running `go get`, by opening the module's page on pkg.go.dev, or from a CI job. The request goes to the public module proxy at [proxy.golang.org](https://proxy.golang.org).
2. The proxy fetches the tagged source from the repository and stores a permanent copy.
3. The proxy lists the new version in the module index at [index.golang.org](https://index.golang.org).
4. pkg.go.dev polls the index, downloads the source from the proxy, and generates the documentation pages.

This design has consequences that surprise newcomers. pkg.go.dev shows the tagged version from the proxy, never the current state of the repository, so a fixed comment stays invisible until the next tag. A version that reached the proxy is immutable. Moving or deleting the tag in Git changes nothing there, and a broken release is handled by publishing a newer version whose `go.mod` carries a [retract directive](https://go.dev/ref/mod#go-mod-file-retract) for the bad one. And pkg.go.dev renders the full documentation only for modules with a recognized [redistributable license](https://pkg.go.dev/license-policy) file in the module root. Without one, the page shows a notice instead of the docs.

The site is open source, so you can run it locally. [pkgsite](https://pkg.go.dev/golang.org/x/pkgsite/cmd/pkgsite) is the program behind pkg.go.dev. Started in a module directory, it serves that module's documentation on localhost and re-reads the source on every page load. That is how you check headings, links, lists and examples before you tag.

## Usage

The skill activates when you write or review Go doc comments, convert comments written in JSDoc or Markdown style, add examples, or publish a module and wonder why pkg.go.dev does not show what you expect.

> A colleague says the docs of this package look broken on pkg.go.dev. Fix the comments.

> I'm publishing my first Go module. Review the package documentation before I tag v1.0.0.

The skill checks every exported symbol against the rules above, rewrites comments that break them, and turns inline snippets into `Example` functions. For publishing problems it follows the proxy chain to find where the version got stuck. It verifies its work with `go doc` and, for comments with markup, with pkgsite. General Go style stays with the [Idiomatic Go](/idiomatic-go) skill.
