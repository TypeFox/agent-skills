# Unbounding the Web Parser: The Engineering Behind ALL(*) in Chevrotain & Langium

When building domain-specific languages (DSLs), language servers, or complex developer tools for web and cloud environments, software architects are frequently confronted with a frustrating trade-off: **choose an expressive grammar engine that requires heavy build-time native tooling (like a Java-based parser generator), or pick a lightweight JavaScript parser library that fails on complex, ambiguous language constructs.**

In 2022, TypeFox bridged this gap by bringing **ALL(*) ("All-Star", adaptive LL(*))** parsing logic—the foundational prediction algorithm behind ANTLR4—directly into the JavaScript ecosystem via Chevrotain. Today, that port powers **Langium** and handles **nearly 4 million weekly downloads** across the global developer ecosystem.

Here is the technical story of why we brought ALL(*) to TypeScript, how it works under the hood, its performance cost, and how it continues to shape language architecture at TypeFox.

---

### Impact At A Glance

* **~4 Million** Weekly NPM downloads (driven by Langium and downstream tools like Mermaid.js).
* **< 5%** Runtime overhead compared to strictly bounded LL(k) parsers.
* **0 JVM Dependencies** Required for grammar compilation or runtime execution.

---

## 1. The Problem: Grammar Limits in JS Toolchains

Traditional parsers rely on statically determined lookahead to decide which branch of a grammar rule to execute. The spectrum of lookahead strategies highlights why web ecosystems struggled with complex grammars:

* **LL(k):** Precomputes a fixed $k$-token lookahead table at compile time. It is lightning fast (a simple table lookup), but strictly bounded. Simple and common language patterns like `A ::= a* b | a* c` fail immediately during parser initialization because both branches share an arbitrarily long run of `a` tokens.
* **LL(*):** Introduced in ANTLR3, it attempts to lift static bounds using Deterministic Finite Automata (DFAs). However, static analysis still collapses on complex recursive grammars, requiring engineers to refactor left-recursion by hand.
* **ALL(*):** Introduced by Terence Parr, Sam Harwell, and Kathleen Fisher (OOPSLA 2014), ALL(*) shifts lookahead calculation from grammar-compile time to runtime. Each grammar rule becomes an **Augmented Transition Network (ATN)**. On ambiguous branches, the parser simulates the ATN against the real token stream, caching decision states dynamically into DFAs.

When TypeFox launched **Langium** in 2021 as the modern TypeScript successor to Eclipse Xtext, ANTLR4 was the natural benchmark for language expressiveness. However, ANTLR4 requires a Java runtime to compile grammars. Requiring a JVM build step completely breaks modern developer experiences—such as running pure JavaScript language tools in VS Code extensions, web browsers, or web-based playgrounds.

To eliminate external build steps, Langium adopted **Chevrotain**—a high-performance, pure JS parser toolkit that constructs parsers in memory at runtime. But Chevrotain was strictly LL(k). Language authors frequently hit fixed lookahead walls, forcing them to manually reorder alternatives or count tokens.

---

## 2. Bringing ALL(*) to Chevrotain

To resolve this constraint, Mark Sujew (TypeFox) ported the ALL(*) algorithm to Chevrotain as part of his master's thesis. Contributed upstream in Chevrotain PR #1793 and released as the plugin `chevrotain-allstar`, the implementation follows a three-phase execution model:

1. **Static ATN Construction:** At parser instantiation, Chevrotain rules are translated into Augmented Transition Networks with explicit rule-call and rule-return edges.
2. **Dynamic Simulation (Subset Construction):** When a decision point encounters ambiguity, the engine executes a deterministic subset construction over the actual incoming tokens until only one valid alternative remains.
3. **DFA Memoization:** The resulting state configurations are cached in dynamic DFA transitions linked by lookahead tokens. Subsequent encounters with the same token patterns execute instantly via table lookups, bringing typical runtime complexity down from worst-case polynomial $\mathcal{O}(n^4)$ to linear $\mathcal{O}(n)$.

### Measured Runtime Performance

A primary concern with moving decision logic to runtime is performance degradation. Benchmarks against Chevrotain's original LL(k) baseline demonstrated that ALL(*) introduces minimal overhead:

| Grammar Benchmark | Throughput (Ops/sec) | Relative Speed vs. LL(k) Baseline |
| --- | --- | --- |
| **JSON** | 9,184.94 ± 0.76% | **99.06%** |
| **CSS** | 3,092.55 ± 0.68% | **98.20%** |
| **ECMA5** | 470.71 ± 0.37% | **94.82%** |

For less than 5% throughput cost, developers gain unbounded lookahead flexibility and complete freedom from manual alternative ordering.

---

## 3. Adoption & Ecosystem Impact

To maintain backward compatibility for lightweight Chevrotain users, the maintainers introduced a pluggable lookahead strategy API (Chevrotain 10.4.1). Integrating ALL(*) lookahead in custom Chevrotain parsers requires only a single constructor option:

```typescript
import { EmbeddedActionsParser } from "chevrotain";
import { LLStarLookaheadStrategy } from "chevrotain-allstar";

class DomainParser extends EmbeddedActionsParser {
  constructor() {
    super(tokens, { 
      lookaheadStrategy: new LLStarLookaheadStrategy() 
    });
    this.performSelfAnalysis();
  }
}

```

In **Langium 1.0 (December 2022)**, TypeFox enabled `chevrotain-allstar` by default. Today, the package serves over **3.7 to 4 million weekly downloads on npm**—widely deployed through Langium and downstream frameworks such as Mermaid.js for web-based diagram parsing.

---

## 4. Production Trade-Offs & Known Limits

Engineers adopting `chevrotain-allstar` for production languages should be aware of specific algorithmic boundaries:

* **SLL Simulation Only:** The port currently implements Strong-LL (SLL) lookahead simulation. It does not evaluate the surrounding rule call-stack during nested predictions. Grammars requiring full-context LL(*) evaluation may experience lookahead conflicts (tracked as issue #1). Restructuring grammar rules or specifying an explicit `maxLookahead` serves as an effective workaround.
* **Direct Left-Recursion:** Unlike full Java ANTLR4, left recursion is not automatically eliminated. Langium grammars resolve this using explicit tree-rewriting or the high-performance `infix` operator notation introduced in Langium 4.0 (which boosts expression parsing speed by ~50%).

---

## 5. Looking Ahead: Coexistence with Fastbelt

In June 2026, TypeFox introduced **Fastbelt**, a high-throughput, Go-based language engineering framework designed for heavy-workload environments. Fastbelt takes a zero-CST approach, linking tokens directly to AST nodes and saving over 70% of workspace memory compared to standard CST architectures.

| Framework | Architecture | Primary Use Case |
| --- | --- | --- |
| **Langium + ALL(*)** | TypeScript / LSP-First | Ideal for VS Code extensions, web browsers, rapid DSL prototyping, and rich Language Server Protocol (LSP) integrations with zero native dependencies. |
| **Fastbelt Pipeline** | Go / High Performance | Designed for enterprise-scale language infrastructure, ultra-low latency, and minimal memory footprints where native binary speeds are paramount. |

---

## Conclusion

By embedding ANTLR4's decision-making algorithm into Chevrotain, TypeFox eliminated one of the largest architectural roadblocks in JavaScript-based language engineering. Today, developers can build production-grade, highly expressive DSLs that run anywhere JavaScript runs—with no build step, no JVM, and no compromises on lookahead power.
