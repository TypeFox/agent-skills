# Bringing ALL(*) Lookahead to Langium & Chevrotain

Published in 2014, Terence Parr's landmark ALL(*) paper introduced the most powerful LL-style lookahead algorithm to date. Yet despite its transformative impact on compiler design, ALL(*) saw almost no adoption outside the ANTLR4 ecosystem.

That changes today. We brought the ALL(*) algorithm to **Chevrotain**—and by extension, **Langium**—via the dedicated `@chevrotain/allstar` package.

Here is the backstory of why we chose Chevrotain over ANTLR4 in the first place, how we ported ALL(*), and what this means for language engineering in the JavaScript/TypeScript ecosystem.

## Why Chevrotain Beat ANTLR4 for Langium

When we evaluated parser engines for Langium in early 2021, ANTLR4 was the obvious candidate to beat. Having previously relied on ANTLR3 while building [Xtext](https://www.google.com/search?q=https://www.eclipse.org/Xtext/), our team at TypeFox was intimately familiar with the framework's strengths. ANTLR4 improved upon older $LL(*)$ lookahead in two crucial ways:

* **Direct Rule Recursion:** It handles arbitrary recursion directly within lookahead evaluation without blowing up the stack.
* **Automatic Left-Recursion Resolution:** It resolves direct left recursion natively, eliminating the need to manually refactor natural grammar rules.

Unbounded lookahead makes grammar design intuitive. Having to refactor clean, human-readable grammar rules simply because an underlying parser engine lacks algorithmic power is frustrating—and it inevitably compromises both grammar readability and Abstract Syntax Tree (AST) construction.

Despite these strengths, **ANTLR4 introduced a dealbreaker for modern web developers: a Java dependency.**

To compile ANTLR grammars, developers must execute a toolchain written in Java. Even if the target runtime parser is pure JavaScript, forcing every Langium user to install and configure a Java Development Kit (JDK) ran entirely counter to our vision of providing a zero-overhead, JS-native developer experience.

When we audited the JavaScript parser landscape, Chevrotain stood out immediately:

1. **Top-Tier Performance:** In rigorous benchmarks, Chevrotain systematically outperformed competing JS parser libraries—and frequently surpassed hand-written parsers.
2. **Robust Error Recovery:** Unlike typical JS parser combinators that crash on the first syntax error, Chevrotain inherited ANTLR-style fault tolerance and error recovery right out of the box.
3. **Zero Build Step:** Chevrotain requires no upfront code generation phase. You define your parser in pure code, and it builds its internal state in memory within milliseconds.

While standard Chevrotain was bound to traditional $LL(k)$ lookahead, its clean architecture and active maintenance made it the ideal foundation for Langium.

## Unintended Superpowers: Pure In-Memory Parsing

Initially, Langium generated static TypeScript files from grammar definitions and compiled them to Chevrotain parsers. This yielded predictable, readable code that was straightforward to step through in a debugger—essential ground while we designed our core AST construction logic.

However, as our architecture matured, Chevrotain’s interpreted nature unlocked a far greater advantage: **pure in-memory parsing without intermediate code generation.**

By Langium v0.2, we leveraged this capability to generate functional, high-performance parsers on the fly directly from raw grammar strings. This unlocked two major features:

* **Instant Unit Testing:** We could evaluate complex parser behaviors on the fly across edge-case grammars without generating temporary local files or setting up project scaffolding.
* **The Langium Playground:** Live, in-browser grammar compilation without a build step became the core engine powering the web-based [Langium Playground](https://langium.org/playground/).

## Understanding the Shift: From $LL(k)$ to ALL(*)

Parser engines must decide which production rule to execute based on upcoming tokens in the input stream. This decision process is known as **lookahead**. The value $k$ represents how many tokens into the future the algorithm must inspect to disambiguate competing branches.

Standard $LL(k)$ algorithms require a fixed, statically known $k$. This hard constraint prevents them from parsing grammars where alternative branches share arbitrary-length or variable-length prefixes.

### The $LL(k)$ Bottleneck

Consider this standard EBNF grammar rule:

```text
A ::= a* b 
    | a* c

```

This grammar matches an arbitrary sequence of `a` tokens terminated by either a `b` or a `c`.

Because the sequence of `a` tokens can be infinitely long, an $LL(k)$ parser cannot predetermine a static numerical value for $k$ to distinguish between the two paths up front. When faced with this structure, standard Chevrotain would throw a static initialization error, forcing you to manually refactor the rule.

## Porting ALL(*) to Chevrotain

Between late 2020 and 2021, I focused my master's thesis on adapting the ALL(*) algorithm to a brand-new parsing framework and evaluating its real-world performance. The objective was to bring dynamic, unbounded lookahead directly into Chevrotain.

The final implementation landed in April 2022. Understanding why the port required six months of deep algorithmic work requires looking at how ALL(*) replaces static lookup tables with dynamic runtime evaluation.

### 1. Static Representation via ATNs

Standard $LL(k)$ parsers construct a static lookahead table mapping decision points to fixed token choices. If an incoming sequence cannot be mapped to a static bucket, the parser fails.

ALL(*) replaces these rigid tables by converting each grammar rule into an **Augmented Transition Network (ATN)**—essentially a Non-Deterministic Finite Automaton (NFA) capable of simulating nested execution paths across grammar rules dynamically.

```
       ┌───┐  'a'  ┌───┐  'b'  ┌───┐
  ┌───>│ s1│──────>│ s2│──────>│ s3│ (Match A1)
  │    └───┘▲      └───┘       └───┘
  │      │  │ 'a'
(s0)     └──┘
  │    ┌───┐  'a'  ┌───┐  'c'  ┌───┐
  └───>│ s4│──────>│ s5│──────>│ s6│ (Match A2)
       └───┘▲      └───┘       └───┘
         │  │ 'a'
         └──┘

```

### 2. Dynamic Decision Building via DFAs

When the parser encounters an ambiguous choice at runtime, it queries the ATN:

1. It initializes a new Deterministic Finite Automaton (DFA) starting at the decision's current ATN state configuration.
2. As tokens arrive from the input stream, it applies **subset construction** to simulate all valid execution paths simultaneously.
3. Token processing continues until alternative paths fall away, leaving exactly one valid route remaining.

### 3. Sub-linear Performance via Memoization

Running subset construction from scratch on every parser decision would degrade execution to an impractically slow $O(n^4)$ worst-case time complexity.

To overcome this, ALL(*) caches every state transition inside the DFA, linking states by token type. When the parser encounters a previously evaluated path, it skips ATN simulation entirely and performs an $O(1)$ state transition lookup.

Inspired by PEG/Packrat parsers, this aggressive memoization brings typical runtime complexity down to a crisp $O(n)$.

## Performance Trade-offs & Architecture

Comparing baseline Chevrotain against the ALL(*) port revealed predictable, highly acceptable trade-offs:

| Metric | Baseline $LL(k)$ | ALL(*) Port (`@chevrotain/allstar`) |
| --- | --- | --- |
| **Parsing Speed** | **Baseline (100%)** | ~95% (5% overhead on trivial grammars) |
| **Memory Footprint** | Minimal (Static tables) | Dynamic (DFA caching & ATN graph) |
| **Grammar Flexibility** | Restricted (Fixed $k$) | **Unbounded** (Arbitrary lookahead & recursion) |

While static $LL(k)$ lookahead remains ~5% faster on simple, non-ambiguous grammars due to zero-overhead static tables, ALL(*) trade-offs are minimal. In exchange for a tiny memory increase, ALL(*) completely removes structural grammar constraints, enabling natural, flexible language design.

### A Pluggable Architecture

The initial ALL(*) pull request introduced over 4,000 lines of complex engine code. Forcing this algorithm onto all existing Chevrotain users carried unnecessary regression risks for standard $LL(k)$ workloads.

Instead of overriding Chevrotain's core, we designed a **pluggable lookahead API** introduced in **Chevrotain v10.4.1**. This decoupled ALL(*) into an optional, standalone module: `@chevrotain/allstar`.

```typescript
import { CstParser } from "chevrotain";
import { AllStarLookaheadProvider } from "@chevrotain/allstar";

class MyParser extends CstParser {
  constructor() {
    super(tokens, {
      // Plug in ALL(*) unbounded lookahead dynamically
      lookaheadProvider: new AllStarLookaheadProvider()
    });
  }
}

```

## Conclusion

With ALL(*) integration complete, Langium users enjoy the best of both worlds: they can author complex, highly expressive grammars without fighting parser constraints or managing Java toolchains—all running on a blazing-fast, JS-native engine.
