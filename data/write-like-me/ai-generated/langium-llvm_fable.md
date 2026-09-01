# From domain language to native software: what Langium and LLVM make possible

A domain-specific language usually starts life as a better way to write things down. Your experts describe rules, models, or processes in a notation that fits their heads, and the tooling checks their work as they type. That alone is worth a lot. But at some point the same question comes up in every project: what happens to these files once they're written?

Sometimes the answer is "we generate documents or configuration." Sometimes it's "another system reads them." And sometimes the honest answer is: this language describes something that needs to *run* — fast, on real hardware, and in a way our team can debug when it misbehaves.

This article is about that last case. It's the non-technical companion to our step-by-step tutorial on connecting Langium to LLVM. We'll skip the code and focus on what the combination gives you, when it's the right call, and what to watch out for.

## Two halves of a language

Every language that gets executed has two halves, whether or not anyone draws the line explicitly.

The **front half** reads what the user wrote: it parses the text, resolves references between elements, validates the result against your domain rules, and powers the editor experience — completion, error markers, navigation. This is what Langium does. You write a grammar, and Langium derives the full front half from it, ready to plug into VS Code, Eclipse Theia, or a web application.

The **back half** turns a validated program into something that can run. Here you have a choice, and it's a real one with consequences for your product.

## The choice: interpret or compile

An **interpreter** walks through the program and carries out each step directly. It's quick to build, easy to change, and perfectly adequate for many domain languages — workflows, configurations, business rules that run a few thousand times a day. In our first article on Langium and LLVM we built exactly such an interpreter for a small teaching language called Ox.

A **compiler** translates the program into machine code once, ahead of time. That's more effort up front, but the result runs natively on the target platform, at the speed of hand-written C, with decades of optimization applied automatically. When your domain language describes signal processing, control logic, simulations, or anything that runs in a tight loop or on constrained hardware, this is the path that pays off.

The catch with compilers has always been that writing a good one for every target platform is a research project of its own. This is where LLVM comes in.

## Why LLVM changes the economics

LLVM is the compiler infrastructure behind a large share of the software industry — the Swift, Rust, and Clang C/C++ toolchains are built on it, among many others. Its central idea is a platform-independent intermediate language, LLVM IR. You generate that once from your language, and LLVM takes it the rest of the way: optimization, machine code, and support for every processor architecture the project covers.

For a domain language, this means the back half of your compiler shrinks to one job: translate your language's concepts into LLVM IR. Everything below that line is somebody else's well-maintained problem. Concretely, you get:

- **Native performance.** Programs written in your language run as compiled machine code, not inside a virtual machine or interpreter loop.
- **Platform independence.** One generator, many targets — desktop, server, embedded — without rewriting the translation.
- **Optimization for free.** The LLVM toolchain applies its optimizers to your output. You can add your own, but you don't have to start there.
- **Debugging in your language, not ours.** This is the part that surprises people. Because the generator annotates the output with source locations, a developer can set a breakpoint on line 3 of their domain file, step through it line by line, and inspect variables by their domain names — using standard debuggers. The translation stays invisible.

That last point matters more than it sounds. A domain language that experts can write but nobody can debug will quietly lose trust. One where a problem can be traced back to the exact line the expert wrote keeps it.

## What it takes

Our tutorial walks through building the Ox compiler in ten steps: setting up the LLVM structures, printing output, then translating literals, variables, arithmetic and logic, if/else, loops, function definitions, and function calls — each mapped from the syntax tree Langium produces. Along the way you get a working executable and a debugging session to prove it.

It's a small language, deliberately. But the shape of the work is the same for a real one, and a few lessons carry over directly:

**The front half does the heavy lifting on correctness.** Code generation should only ever see programs that have passed validation. Every rule you encode in the Langium front half is a class of bug the compiler never has to worry about. Investing in validation is investing in the compiler.

**Types deserve a proper home.** LLVM operations are not polymorphic — the generator has to know exactly which addition to emit for which operand types. For a language with a handful of types that's a lookup table. For one with overloading, conversions, or user-defined types, you want a real type system. That's why we built Typir, an open source TypeScript library for exactly this, designed to integrate with Langium.

**The glue between ecosystems is where experience counts.** Langium lives in the TypeScript world; LLVM's native API is C++. The bindings we used in the tutorial work, but the binding landscape moves at a different pace than either ecosystem, and choosing the right integration path for a production project is a decision worth making deliberately. This is the kind of thing we help clients settle in the first week rather than discover in month six.

## Is this for you?

A quick way to decide:

- If your domain language *describes* things — structures, rules, configurations — and other software consumes the result, you probably want a generator or an interpreter. Langium handles this well, and it's the more common case.
- If your domain language *computes* things and performance, portability, or hardware constraints are part of the requirements, the Langium-plus-LLVM route gives you a real compiler without building one from scratch.
- If you're not sure, that's a normal place to be. The front half is the same in both cases, so starting with Langium doesn't close either door.

## Built by the people who built the tools

Langium started at TypeFox in 2021 and has become the standard toolkit for domain-specific languages on the web. Typir came out of our own need for reusable type systems. The LLVM tutorial exists because we wanted to know, hands-on, how far the combination carries — and it carries further than we expected.

That's the position we like to be in with clients: we designed the frameworks, so when your requirements go beyond the defaults, we know exactly where and how to adapt them.

If your experts have a language in their heads that needs to become running software, we'd like to hear what it looks like. The step-by-step tutorial and the full Ox example are open source on GitHub if your architects want to try it first — and if you'd rather talk it through, that's what we're here for.
