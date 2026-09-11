# monaco-languageclient 10: from bridge to toolbox

Eight years ago, we taught Microsoft's monaco-editor to speak the Language Server Protocol. The result was monaco-languageclient — a bridge, and deliberately not much more. It had to be a bridge: LSP support lived inside VS Code, and monaco-editor is the one piece of VS Code you can actually install from npm.

Version 10 closes that arc. monaco-languageclient is no longer just a library for LSP integration. It is the toolbox that holds everything you need to build a complete editor-centric web application: one package, three clearly separated concerns, MIT-licensed top to bottom.

If you already know the project, skip ahead to *Version 10: one package, three concerns*. If you'd rather hear how a library that once sat in maintenance mode became shared infrastructure maintained across two companies, start here.

## 2017–2021: a bridge, then a quiet spell

When we launched monaco-languageclient in 2017, the gap was obvious. You could deploy monaco-editor in a browser application, but you could not connect it to a language server. LSP was a VS Code privilege.

From day one, monaco-languageclient wrapped `vscode-languageclient`, the library Microsoft wrote for VS Code — which naturally expects a full VS Code API around it. In a browser, that API isn't there. VS Code ships as one monolithic piece of software, not as packages on a registry; monaco-editor is the artificially extracted exception. So we re-implemented large parts of the VS Code API ourselves and built a bi-directional bridge to move LSP messages in and out of monaco-editor.

Alongside it, we started `vscode-ws-jsonrpc`, which let a language client in the browser talk to a language server running elsewhere over web sockets. Together, the two packages made existing language servers usable inside monaco-editor.

We maintained the project for about three years. Then our focus shifted — the Theia IDE stopped relying on monaco-languageclient — and the project could easily have gone dormant. It didn't, because Loïc Mangeonjean of CodinGame stepped in as maintainer and carried it largely on his own until 2022. Open source works like this more often than the release notes admit.

## 2022: ignition

In early 2022 we saw an opening: a reusable web component around monaco-editor, with language server support included. That's when we rejoined the project as co-maintainers.

Meanwhile, the re-implemented VS Code API had become a running battle. Every VS Code release was a compatibility risk. Loïc's idea was to stop re-implementing and start transforming: convert the VS Code source itself into ESM modules. In June 2022 he released the first version of `monaco-vscode-api` — effectively a modularized VS Code Web, shipping the real VS Code API plus a long list of services across many packages.

The effect on monaco-languageclient was radical. Large amounts of our code simply disappeared, and features previously exclusive to VS Code became available in ordinary web applications. You can see the range in the project's own demo and in CodeSandbox, which builds on it.

We also folded `vscode-ws-jsonrpc` into the main repository to keep maintenance in one place, and the planned web component grew into `monaco-editor-wrapper`, which made it easier to drop monaco-editor plus a language client into any JavaScript UI framework.

## 2023–2024: growing outward

React users asked for a React component, so in 2023 `@typefox/monaco-editor-react` was born as a thin layer over `monaco-editor-wrapper`. In 2024 we consolidated everything into the main repository, grew the example collection, and shipped the last major releases before the refactoring: monaco-languageclient v9 and monaco-editor-wrapper v6, both shortly before the end of the year. That release let a single application manage multiple language clients.

By then the shape of the project had quietly inverted. The outer wrapper had most of the features and most of the attention, while monaco-languageclient had narrowed to supplying the language client and configuring `monaco-vscode-api`.

## Dogfooding, on purpose

The repository has a second job: it is where we validate new tooling before we recommend it to anyone else. We moved development to vite and unit testing to vitest, using vitest's browser mode together with playwright so tests are written the way you'd write them for a normal web app. The published packages have been ESM-only for more than two years.

That validation is not a side effect. Everyone who forks the repository inherits the same setup.

## Version 10: one package, three concerns

Building a real application with monaco-languageclient alone meant writing a lot of boilerplate. `monaco-editor-wrapper` filled that gap. Earlier this year we admitted the obvious: the split between the two was artificial. So the useful parts moved back into monaco-languageclient — one package, one toolbox.

The bigger change is what happened on the way back in. `monaco-editor-wrapper` offered a single combined, typed configuration covering the VS Code API, the language client and the editor. Convenient, and genuinely useful for years — but the control flow stayed hidden inside the library, and the configuration structure implied a separation that users never got to see or steer.

Version 10 makes that separation explicit, exposed through three use-case-specific sub-exports:

**`vscodeApiWrapper`** — `MonacoVscodeApiWrapper` handles everything related to `monaco-vscode-api`. It is configured through `MonacoVscodeApiConfig` and must be initialized first, exactly once per application lifecycle. That is not our rule; it's how VS Code works, and we're running a transformed version of it.

**`lcwrapper`** — `LanguageClientWrapper` and `LanguageClientsManager` control one or many language clients, configured via `LanguageClientConfig`. Language clients have their own lifecycle, independent of any editor. When a client starts, it registers globally within `monaco-vscode-api`, just as it would inside VS Code, to serve a language or document type. Dispose it and the registration is revoked — the editor stops offering language services for that language until you restart the client.

**`editorApp`** — `EditorApp` and `EditorAppConfig` cover single monaco-editor applications. Create and dispose editors as often as you like; several `EditorApp` instances can coexist in one page.

The result is slightly more code and considerably less mystery. It is clear what happens at which point in time, and each piece can be tested on its own.

## Beyond a single editor

If you want something closer to a partial VS Code for the web, `EditorApp` isn't required at all. `monaco-vscode-api` supplies services such as `ViewsService` and `WorkbenchService`, and monaco-languageclient includes functions to use `ViewsService` directly without extra glue code. From one embedded editor to a composed workbench, it's the same foundation.

## React: `@typefox/monaco-editor-react` 7

We could have baked a React component into the core libraries. We didn't, because no library here should depend on a particular UI framework. Instead, `@typefox/monaco-editor-react` wraps a React shell around the rest.

Version 7 shipped alongside monaco-languageclient 10 and now uses the same configuration objects, which `MonacoEditorReactComp` passes straight through to the same classes.

One honest limitation: it configures a single language client and is built for single-editor applications. monaco-editor — and much of what we build around it — does not fit naturally into React's component architecture. The component is reliable and covers most React use cases, and we think genuinely complex applications belong outside its scope rather than inside a leaky abstraction.

## See it running

All packages are MIT-licensed, so they're fair game for commercial and closed-source projects too.

The examples in the repository run on GitHub Pages with no backend at all, covering Python, Java, Langium, C++ and more, with language servers executed directly, inside web workers, or from Linux container images. Some are deliberately plain. Others are not: the Python example ships a working debugger, and the Clangd Wasm example synchronizes thousands of header files between client and server.

Real applications go further than any example — that's the nature of examples. Our aim is to make LSP integration on the web as simple as possible, and not one step simpler than that.

## What's next

The major API refactoring is done, so the coming months are about extension rather than upheaval:

- a ready-to-use file-system synchronization mechanism for distributed application parts
- a rethink of `vscode-ws-jsonrpc`, largely unchanged since 2017 and due for attention
- more reusable building blocks aimed at application development
- more documentation — the release-day update was a first step, not the finish line
- more unit tests: from zero in 2022 to 67% coverage today, which is progress, not an achievement

## Building on it

Watching monaco-languageclient go from an uncertain side project to widely adopted open source has been a pleasure, and the collaboration between two maintainers at two different companies is the part we're proudest of. It's also the reason the toolbox exists in this shape at all.

Everything is public and MIT-licensed: fork it, ship it, build a product on it. Issues, pull requests and awkward questions are all welcome — the awkward ones especially.

And if your editor-centric application is more than a weekend project — a domain-specific language that needs a professional home in the browser, a custom IDE, a language server that has to survive workspaces with tens of thousands of files — we don't only maintain these libraries. We build on them for clients, and we tailor them where the standard path stops. Those are the projects we enjoy most. Tell us what you're working on.
