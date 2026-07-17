---
name: strategy-frameworks
description: Pick the right strategy framework for a Taiwan business question — and know when a framework is the wrong move. Routes a question ("should we enter this market", "how big is this", "why are we losing share", "is now the time") to the one framework that answers it, binds each framework to the tw-data command that feeds it with real numbers, and says which frameworks are undeliverable in Taiwan because the data does not exist. Use this before analysing a market-entry, sizing, competitor, investment or timing question, whenever someone proposes running a SWOT/Porter/BCG, or when an analysis has collected data but has no shape yet.
---

# Choosing a framework for a Taiwan business question

A framework is a way of being wrong in an organised fashion. Its only job is to
turn a vague question into a claim that data can kill. Pick the wrong one and
you produce a deck that is well-structured and says nothing.

This skill picks. It is deliberately thin on what each framework *is* — that is
a search away — and thick on **which question it answers, what number feeds it,
and when it is the wrong tool.**

## The failure mode this exists to prevent

**Framework theater**: applying a framework because it is the framework people
apply, filling its boxes with whatever is at hand, and presenting the filled
boxes as an argument. The tell is that every box has content and none of it
changes the recommendation. A five-force analysis where all five forces are
"moderate" cost a week and decided nothing.

The rule: **a framework earns its place only if a plausible fill of its boxes
would flip the recommendation.** If you cannot say in advance what result would
change your mind, don't run the framework — go get a number instead.

## Route the question first

Start from what was actually asked, not from what is fashionable.

| The question actually asked | Framework | What feeds it (`tw-data`) |
|---|---|---|
| How big is this? Is it worth entering? | **Bottom-up sizing** (TAM/SAM/SOM) | `household.py --tam 類別` · `--mix` — grain check first, see below |
| Can this business model sustain itself? (訂閱/平台/內容/freemium) | **Unit economics** — mostly no data | ARPU, conversion, churn, cost structure need first-party research. 付費意願 and ad-market size are snapshotted with retrieval methods in tw-data's `references/external-sources.md` (Reuters DNR: TW paid-news rate 10% in 2026; DMA: digital ad market 636.83億 in 2024) |
| Is now the time? Should we wait? | **Cycle timing** | `ndc_signal.py` · `moea_orders.py --orders` |
| Is this industry structurally attractive? | **Porter 五力** (partial — see below) | `twse_revenue.py --industry` · `moea_orders.py --production --sector` · `mof_industry.py --industry` (SME-inclusive size/trend) |
| Who are we up against, and who's winning? | **Competitor roll-up** | `twse_revenue.py --industry` · `--top` / `--bottom` |
| Who is the customer? Which segment? | **Segmentation** | `household.py --quintile` · `--spend` (by 縣市) |
| Where do we grow from here? | **Ansoff** | `household.py --mix` (adjacent categories) |
| What is the macro backdrop? | **PEST**, macro half only | `dgbas_macro.py --gdp --cpi --unemployment --wage` |
| Why did the number move? | **Decomposition** — not a framework, arithmetic | whichever series moved; `ndc_signal.py` components |

If the question isn't in this table, either it is not a strategy question, or —
the common case — it is one this data layer cannot feed (unit economics is the
classic). Say which, rather than reaching for the nearest matrix. "This case is
undecidable on free data; here is the cheapest thing that would decide it" is a
deliverable, and often the most valuable one.

## The frameworks, briefly, and when not to

### Bottom-up sizing (TAM/SAM/SOM)

`households × spend per household × category share`, then haircut to what you
could serve and what you could win. `household.py --tam` does the TAM line.

**Grain check first.** `--tam` resolves to the survey's **10 top-level
categories** and nothing finer. If the target market is narrower than a whole
category — a magazine inside 休閒、運動、文化及教育, which also bundles tuition,
cram schools and package tours — the output is an upper bound of an upper bound,
off by orders of magnitude (that bucket is ~NT$5,000億; Taiwan's entire magazine
industry is ~百億級). Use it as a ceiling, never as the TAM, and never let a
failed narrow lookup get "fixed" into a category-level number.

**Share is not level.** A category's falling share of the household budget does
not mean falling NT$, and vice versa — always compute the absolute series too
(share × per-household total spend, CPI-deflated via `dgbas_macro.py --cpi`)
before calling a category "declining". And mind attribution: a bundled category
can move for reasons unrelated to your slice — 少子化 mechanically shrinks the
education sub-item inside 休閒、運動、文化及教育 regardless of what media
spending does. A bundle trend is a proxy for your slice, not evidence about it.

**Use it** for any consumer category at category grain. It is the strongest
thing in this plugin: every line is defensible and a reader can attack the
assumptions rather than the number, which is what you want.

**Don't** for B2B, government, or infrastructure demand — 家庭收支調查 is
household consumption only. Sizing a B2B market from it is not conservative, it
is unrelated. For B2G use PCC 政府採購 (not yet wrapped; see tw-data's endpoints
reference).

**The SOM is where sizing dies.** TAM is arithmetic; SOM is a claim about your
company. Never present a SOM as if the data produced it.

### Cycle timing

The 景氣對策信號 tells you where the economy is; 外銷訂單 tells you where it is
going, because orders are booked before they ship. `ndc_signal.py` gives the
score, the light, and the component breakdown.

**Use it** when the recommendation is *when*, not *whether*, and when the answer
plausibly changes with the cycle.

**Don't** let it decide a structural question. A red light does not make a bad
market good. Timing arguments are only interesting once the market has already
survived the sizing question — and the light is a **national** signal, so it is
close to irrelevant for a niche that moves on its own drivers.

**The trap**: Taiwan's cycle light is currently dominated by export electronics.
A 紅燈 while 零售營業額 is +3% and 民生工業 production is negative means the
economy is booming *somewhere else*. If your case is domestic consumer, the
headline light is actively misleading. Decompose before you cite it.

### Porter 五力 — usable at about 40% in Taiwan

Honest accounting of what free data can and cannot support:

| Force | Feasible? | With what |
|---|---|---|
| 現有競爭 | **Yes, if the industry's top players are listed** | `twse_revenue.py --industry` — concentration, growth dispersion. TWSE's 33 產業別 have no 出版/媒體/文創 (those are TPEx or private); for media, education and professional services this cell is **No** |
| 新進入者 | Partial | GCIS 公司登記 (not wrapped) for entry rates |
| 供應商議價 | **No** | Needs cost structure — not in any free source |
| 買方議價 | Partial | `household.py --quintile` for consumer; nothing for B2B |
| 替代品 | **No** | Requires judgement, not data |

**So**: run the rivalry force properly and *say the other four are judgement*.
A five-force where four boxes are opinion dressed as analysis is worse than one
force with a number. Never present the five as equally evidenced.

**Don't** use Porter for "how do we win" — it is an industry-attractiveness
tool. Firm-level questions need a different lens.

### Competitor roll-up

`twse_revenue.py --industry 半導體業` gives every listed company's monthly
revenue and YoY in that industry. Rolled up, that is an industry demand tracker;
read down the rows, it is a competitive scoreboard, monthly, free.

**The hard limit**: **listed companies only.** Taiwan's economy is overwhelmingly
SME, and none of them are here. In a fragmented consumer category — restaurants,
clinics, retail — the listed set may be a rounding error on the real market. Do
not compute market share from this and present it as market share. State the
coverage or don't use the number.

`--min-revenue` (default 1億) exists because a company going from NT$2m to
NT$6m posts +200% YoY and will top any unfiltered ranking with pure noise.

### Segmentation

`--quintile` (income fifths) and `--spend` (by 縣市) are the two real axes free
data gives you. Both are structural and slow: 家庭收支 lags ~18 months.

**Don't** invent psychographic segments and pretend the survey supports them. If
the segment isn't a cut the data actually makes, it is a hypothesis — label it.

### Ansoff, PEST, and the rest

Use them as **checklists, not analyses**. Ansoff is a prompt to ask "is this new
product or new market"; ten minutes, verbally, no slide. PEST's P/S/T legs have
no data behind them here — the E leg is `dgbas_macro.py` and the rest is
reading. A PEST slide is almost always filler.

## What this skill will not help you produce

- **SWOT** — the purest form of framework theater. Every box fills, nothing
  decides. If someone asks for one, ask what decision it informs; there usually
  isn't one. Ansoff or a sizing pass answers the real question underneath.
- **BCG growth-share matrix** — needs relative market share. Taiwan free data
  cannot give you market share in any fragmented category (see the SME gap
  above). You would be plotting guesses on two axes.
- **Any framework requiring cost structure or margin by competitor** — not
  available free. TWSE gives revenue, not margin.

Being unable to build these is a finding worth stating, not a gap to paper over
with estimates.

## Framework → argument

The framework is scaffolding; it comes down before delivery. What ships is a
claim, a number, and what would falsify it:

- **Bad**: "Porter analysis shows moderate rivalry." (fills a box, decides nothing)
- **Good**: "The top 3 listed players hold X% and all three grew slower than the
  industry last year — the share is moving to companies we can't see, which
  means our competitor set is SMEs, not the incumbents." (a claim, a number, and
  a clear thing that would prove it wrong)

Then cross-check. tw-data's four independent reads — cycle light, listed revenue,
export orders, production/retail — exist so a claim can be corroborated. When they
agree, the finding is solid. **When they diverge, the divergence is the finding.**

Related: `tw-data` for the numbers, `biz-case-workflow` to run the whole case
end-to-end.
