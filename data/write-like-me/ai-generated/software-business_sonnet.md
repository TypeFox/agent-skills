# How the Software Development Business Has Changed: 2023–2026

## Executive Summary

Software development has moved from a human-authored, seat-priced, office-centric craft to something closer to an AI-orchestrated, outcome-priced, distributed discipline. Five forces are driving this shift simultaneously:

1. **AI coding tools went from novelty to infrastructure.** Daily use of AI coding assistants is now the norm, and the frontier has already moved past autocomplete-style copilots to autonomous agents that plan, write, test, and submit code with limited supervision.
2. **The entry-level talent pipeline is contracting** even as senior engineering demand stays strong, triggering the first computer-science enrollment decline in about twenty years and a wave of coding-bootcamp closures.
3. **How software companies charge for their product is being rebuilt.** Per-seat SaaS pricing is losing ground to usage-based and outcome-based pricing as AI agents — not just human "seats" — start doing the work.
4. **The unit economics of building software have collapsed**, enabling solo founders and very small teams to reach revenue levels that once required full departments, while global capital is concentrating into a handful of AI infrastructure companies.
5. **Delivery practice and industry structure are consolidating**: DevOps is being subsumed into "platform engineering," IT outsourcing is shifting from cost arbitrage to capability-and-governance partnerships, and the AI coding-tool market itself is undergoing rapid M&A consolidation into a few large tech ecosystems.

Below, each of these threads is unpacked with supporting data gathered from industry research, labor-market data, and trade coverage through mid/late 2026.

## 1. From Autocomplete to Autonomous Agents

The technical center of gravity in software development has shifted three times in a few years: from code-completion tools, to conversational "copilots," to autonomous coding **agents** that take a ticket or bug report and independently plan, implement, test, and open a pull request with minimal human involvement.

- Adoption is now mainstream rather than experimental: industry surveys put AI coding-tool usage or planned usage among developers in the 73–84% range through 2025–2026, with GitHub Copilot alone reported at roughly 20 million users and Cursor's maker, Anysphere, reaching a multibillion-dollar annualized revenue run rate.
- Trust has not kept pace with adoption. The same body of research shows developer trust in AI-generated output *falling* even as usage rises — one widely cited figure put trust at 29% in 2026, down from about 40% two years earlier — because the dominant failure mode isn't obviously broken code but code that *looks* correct while hiding subtle errors.
- Companies including Razorpay and Rakuten are running autonomous agents in production that pick up a ticket and submit a finished, tested change without a human writing the implementation — pushing engineers toward review, direction, and verification rather than line-by-line authorship.
- Academic and industry research increasingly documents a **productivity–reliability paradox**: controlled studies show real task-level speedups (roughly 20–56% on well-scoped work), yet at least one rigorous randomized trial found a slowdown for experienced engineers working in mature codebases, and large-scale telemetry across thousands of developers found a spike in merged pull requests accompanied by a similarly large spike in code-review time — leaving overall delivery metrics flat.
- Executives are starting to say the quiet part out loud: Microsoft's CEO has described a meaningful share of code in some internal projects as AI-generated, and Salesforce's CEO has said the company hired no new engineers in a recent fiscal year, crediting AI coding tools directly.

**Net effect:** the job is shifting from "writing implementation code" to "specifying, reviewing, and governing what AI agents produce" — a change in job description more than a wholesale replacement of the profession, but one with real winners and losers depending on where an engineer's value used to come from.

## 2. The Labor Market Is Bifurcating, Not Simply Shrinking

The picture in software hiring is not a uniform decline — it's a split between a contracting entry-level market and resilient-to-strong demand for experienced engineers.

**Signals of contraction:**
- Multiple trackers put 2024 tech layoffs above 150,000–260,000 workers globally, with a further ~120,000+ cut through 2026, concentrated at large, previously over-hired tech firms.
- Software-development job postings remained well below pre-2021 peaks through late 2025 on Indeed's tracking, and some sources report double-digit year-over-year declines as of Q3–Q4 2025.
- Entry-level and new-graduate hiring has been hit hardest — some sources cite roughly a 25–35% drop in junior-developer hiring at major firms, and Stanford research (cited via Business Insider, July 2026) found employment for developers aged 22–25 down roughly 20% since ChatGPT's launch.
- This has fed back into education: U.S. computer-science enrollment fell for the first time in roughly two decades in the 2025–26 academic year, with declines in the mid-to-high single digits at the undergraduate level and considerably steeper drops in graduate programs, according to National Student Clearinghouse and Computing Research Association (Taulbee) data. Coding-bootcamp closures (Epicodus, Codeup, Momentum Learning, and others) followed the same tech-hiring slowdown, though the sector isn't dead — some analysts still project the bootcamp market to keep growing overall as employers seek fast upskilling rather than four-year degrees.

**Signals of resilience or growth:**
- U.S. Bureau of Labor Statistics data cited across several sources still shows overall tech employment above pre-pandemic levels, with software-development roles among the faster-growing occupational categories and continued above-average projected growth for developers, QA analysts, and testers into the mid-2030s.
- AI/ML engineering roles, cybersecurity roles, and senior/staff engineering roles are reported as growing even where junior hiring is flat or falling — one analysis found 71% of the 2025–2026 rebound in software job postings came specifically from senior roles.
- Compensation is diverging along the same axis: workers with in-demand AI skills reportedly command a large salary premium over peers without them, while overall average salary growth has been modest (roughly flat to low single digits).

**Remote work has largely stabilized into hybrid, with a late-2025/2026 employer-driven pushback.** Multiple sources describe the share of fully in-office roles rising sharply through 2026 as return-to-office mandates take hold, even though developer preference for remote or hybrid arrangements remains strong (with meaningful shares of engineers saying they would leave a job that went fully in-person). Most mid-size and large employers appear to have settled on a two-to-three-day-in-office hybrid default rather than either extreme.

**Read on this data:** the profession isn't disappearing, but the traditional "learn to code, get a junior job, grow into seniority" ladder is under real strain at its first rung, which several analysts flag as a multi-year risk to the pipeline of future senior engineers.

## 3. Business Models Are Being Rebuilt Around AI Agents

### Pricing: from seats to usage to outcomes
Per-seat SaaS pricing assumed one human logging in per license. That assumption breaks when an AI agent — not a person — is doing the work, and the industry is visibly repricing around it:
- Analysts and consumption-billing vendors report seat-based pricing's *share* of SaaS pricing models falling (one study cited a drop from roughly 21% to 15% of companies in a single year) while hybrid subscription-plus-usage models have grown to be used by a large plurality (over 40%) of companies.
- Forecasts vary in specifics but agree on direction: Gartner-cited projections put 40%+ of enterprise SaaS spend shifting toward usage-, agent-, or outcome-based pricing by 2030, and some analysts (via Bloomberg estimates cited in trade press) foresee subscription pricing's overall share of software pricing roughly halving over the next decade as outcome-based pricing's share rises sharply.
- Concretely, this shows up first in high-volume, easily measured workflows — customer support tickets resolved, features shipped, sales calls booked — because the "unit of work" is easy to define and price against.

### Company size: the "one-person unicorn" narrative
AI coding and orchestration tools have lowered the cost of building and running software so far that solo founders and tiny teams are reaching revenue levels that used to require whole departments:
- Reported examples include a company built by a small (roughly a dozen-person) team reaching a $200M+ annualized revenue run rate, and broader claims that solo-founded startups now represent roughly a third or more of new ventures (up from under a quarter a few years earlier), though these figures come from advocacy-oriented and press sources rather than a single authoritative census.
- The commonly cited economics: a "lean AI stack" (reasoning model, coding agent, hosting, a handful of SaaS subscriptions) can run a few thousand to roughly ten thousand dollars a year, versus tens or hundreds of thousands for an equivalent hire — a claimed 90%+ cost reduction versus traditional staffing, which materially changes the capital and headcount needed to reach product-market fit.
- Investors are reportedly adjusting how they underwrite deals to account for this "agentic leverage," rewarding revenue-per-employee and capital efficiency over headcount as a signal of seriousness.

### Low-code/no-code keeps eating a share of "software development" that never touches a professional developer
- Market-size estimates for low-code/no-code vary widely by methodology (roughly $30–50B+ in 2026 on most estimates, with longer-range forecasts into the hundreds of billions by 2030), but the direction is consistent: citizen developers (people outside a formal IT/engineering function) are doing a growing share of internal application building, with several analyst forecasts putting citizen developers ahead of professional developers by a ratio approaching 4:1 in large enterprises.
- Generative AI is merging with this category — "vibe coding" and prompt-to-app tools are blurring the line between "no-code platform" and "AI coding assistant."

## 4. Capital Is Concentrating at the Top of the Stack

Venture and growth capital flowing into software has both grown sharply in aggregate and concentrated dramatically at the very top:
- Crunchbase data shows global startup funding hit a record roughly $510B in the first half of 2026 alone — more than all of 2025 — with a single quarter (Q1 2026) absorbing close to 70% of all the venture capital deployed in the whole of 2025.
- A small number of frontier AI labs are capturing an outsized share of this capital: OpenAI and Anthropic alone reportedly accounted for over 40% of all global startup funding in the first half of 2026, and three companies (OpenAI, Anthropic, and xAI) were reported to represent roughly two-thirds of AI-specific VC funding in Q1 2026.
- Sovereign wealth funds (Gulf-state and Singaporean vehicles among them) have become major direct participants in the largest AI funding rounds, a role traditionally held mostly by venture firms.
- Outside the frontier-lab mega-rounds, investors are reported to be more selective than in 2021–2022, favoring startups with real revenue and a credible path to profitability over growth-at-any-cost narratives — a hangover from the 2022–2023 correction.

### M&A: the AI coding-tool market is consolidating fast
Within a roughly 90-day window in mid-2026, most of the previously independent AI coding tools changed hands or were absorbed by larger platforms, according to multiple trade sources:
- Windsurf (formerly Codeium) was acquired for a reported $3 billion, reported by different outlets as going to either OpenAI or Google depending on the source — accounts differ on the acquirer, which itself signals how fast and contested this consolidation has been.
- Cursor's maker, Anysphere, was reported to have agreed to a roughly $60 billion acquisition by SpaceX (following SpaceX's merger with xAI), which would be among the largest acquisitions of a venture-backed startup on record, pending close.
- Google reportedly discontinued its open-source Gemini CLI in favor of a closed-source replacement.
- Microsoft continues to control GitHub Copilot and the VS Code extension ecosystem, while Anthropic's Claude Code was described as maintaining relative independence despite backing from Amazon and Google.

The practical effect for developers and engineering leaders: choice of coding tool is increasingly also a choice of which large AI ecosystem — and whose data policy — a team's code runs through, and tools that look independent today may not remain so for long, raising real switching-cost and vendor-lock-in considerations that didn't exist in the IDE market a few years ago.

## 5. Outsourcing Is Shifting From Cost Arbitrage to Capability Partnership

IT and software-development outsourcing hasn't shrunk — market-size estimates put the global IT services outsourcing market at several hundred billion dollars in 2026 with high-single-digit projected CAGR through the early 2030s — but *why* companies outsource has changed:
- Multiple industry sources describe cost savings as no longer the primary driver; access to specialized talent (cloud, cybersecurity, AI implementation/governance) and delivery speed are now cited as the leading reasons to outsource.
- Nearshoring is gaining share relative to classic offshoring, as companies trade a bit of cost advantage for time-zone alignment, communication ease, and faster iteration — one source claims roughly 80% of North American companies are actively considering nearshore arrangements.
- "Global capability centers" (GCCs) — essentially a company's own captive offshore engineering hub rather than a third-party vendor — are described as a growing alternative to traditional outsourcing, letting companies keep more control over data, IP, and AI systems while still capturing cost and talent advantages of lower-cost regions.
- A tighter U.S./Western senior-engineering labor market is reported to be pushing some of the "quiet rehiring" seen after AI-driven layoffs offshore: companies that cut senior engineers domestically and tried to backfill with AI-augmented juniors have, in some reported cases, gone back to hiring senior engineers offshore at a fraction of U.S. cost once the experience gap became apparent.

## 6. How Software Gets Delivered Is Also Changing

Independent of AI, the discipline of shipping software has continued to formalize and consolidate:
- **Platform engineering** is increasingly described as absorbing and extending DevOps rather than replacing it — internal developer platforms that provide self-service, standardized "paved paths" so product teams don't reinvent CI/CD, IAM, and observability from scratch. Analyst estimates cited across several sources put roughly 80% of large engineering organizations as having a dedicated platform-engineering team by 2026, up from under half a few years earlier.
- **DevSecOps and software-supply-chain security** (SBOMs, artifact signing, frameworks like SLSA) are described as moving from optional to load-bearing, driven by regulatory pressure (GDPR, CCPA, and a growing list of sector- and state-level rules) that most individual product teams can't fully staff for internally — a factor that itself feeds back into the outsourcing trends above.
- **AI is entering the delivery pipeline itself**, not just the editor — AI-assisted CI/CD, automated test generation, anomaly detection, and even autonomous first-pass incident remediation are described as increasingly common in 2026 DevOps stacks, with agentic AI acting as a "first-pass executor" across planning, build, test, and review stages of the software development lifecycle.

## 7. The Macro Backdrop: Software Spending Is Still Growing Fast

None of the above is happening against a shrinking market — quite the opposite. Gartner's IT-spending forecasts for 2026 were revised *upward* multiple times through the year:
- Worldwide IT spending is forecast at roughly $6.3–6.4 trillion in 2026, up on the order of 13–15% year-over-year across successive 2026 forecast revisions.
- Software specifically is forecast at roughly $1.4 trillion, growing in the 14–15% range, with generative-AI model spending alone reported to be growing at a much faster clip (estimates ranging from roughly 80% to more than doubling year-over-year across different forecast vintages).
- Data-center/AI-infrastructure spending is the single fastest-growing category (Gartner cited growth above 50% year-over-year in several 2026 revisions), underscoring that a large share of "software" growth is really compute and AI-infrastructure buildout rather than traditional application spend.
- For a typical mid-market enterprise (as opposed to hyperscalers), analysts suggest a more modest but still healthy 6–9% year-over-year IT budget growth is a more realistic planning assumption than the headline global growth rate.

## 8. Key Tensions to Watch

1. **The productivity-reliability paradox.** Individual-level speedups from AI tools are well documented, but organization-level delivery metrics (cycle time, defect rates) have not obviously improved in step, and review overhead appears to be rising as fast as raw code output — suggesting the *governance* of AI-assisted development matters as much as adoption itself.
2. **A thinning entry-level pipeline.** If junior hiring stays depressed for several more years, multiple analysts warn of a future shortage of the mid-level and senior engineers a growing, AI-augmented industry will still need — a multi-year lagging risk rather than an immediate one.
3. **Vendor concentration in the tools developers now depend on daily.** Rapid M&A among AI coding-tool makers means the editors and agents developers use are increasingly owned by a small number of large AI/tech platforms, with real implications for data policy, pricing power, and long-term product continuity.
4. **Pricing transition risk.** The shift from predictable per-seat subscriptions to variable usage- and outcome-based pricing benefits vendors and customers whose usage/outcomes are easy to measure, but it introduces cost unpredictability that enterprise buyers and finance teams are still building tooling (FinOps-style) to manage.
5. **Trust lagging adoption.** Developers are using AI tools more while trusting their output less — a gap that, if unaddressed by better verification tooling and workflows, is a plausible source of future high-profile production incidents.
