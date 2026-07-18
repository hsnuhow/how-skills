---
name: biz-case-workflow
description: Run a full Taiwan business case end-to-end as a hypothesis-driven multi-agent workflow — frame the question as 2-4 mutually exclusive strategic options, reverse-engineer what-would-have-to-be-true conditions per option, surface the key debates with bull and bear both argued, run skeptic-designed tests in a lazy-man loop that kills options early and expands the search when evidence runs dry, build a driver-tree market model with analog-market parameterization, profile competitors symmetrically, then choose the option with the fewest unresolved barriers and ship a monitoring plan. Use when someone asks for a Taiwan market-entry, sizing, competitor, investment or timing case, an evidence-backed strategic recommendation, or "研究一下台灣的 X 市場" — anything where the answer must be a defensible choice among options. Not for a single lookup; use tw-data directly for that.
---

# Taiwan business case, end to end

This runs a real multi-agent workflow: roughly 15-25 agents, each pulling or
attacking real data. It is the expensive option and it is meant to be. Use it
when the output has to survive someone who wants it to be wrong.

**For a single number — "what's the cycle light", "how big is 醫療保健" — do not
use this.** Call `tw-data` directly. This skill is for questions where the
answer is a *recommendation*, not a value.

## Run it

### 1. Resolve the paths first — do not eyeball them

The workflow runs in a sandbox with **no filesystem, no env, no clock**: it
cannot expand `${CLAUDE_PLUGIN_ROOT}` or compute a dated `runDir` itself. You do
that in one bash step and pass absolute, already-expanded paths:

```bash
TW="${CLAUDE_PLUGIN_ROOT}/skills/tw-data"              # input: where the scripts live
SLUG="wired-taiwan"                                     # short kebab slug of the question
RUN_DIR="$(pwd)/biz-case-runs/${SLUG}-$(date +%F)"      # output: where deliverables land
mkdir -p "$RUN_DIR"
```

**Derive both yourself; ask the user only if derivation genuinely fails** — a
read-only cwd, or a cowork/cloud session where the retrievable outputs location
isn't the working directory. Never ask for `twDataPath`: it is always the plugin
root, so needing to ask means the skill wasn't launched correctly. If the paths
still carry a literal `${...}` or `twDataPath` is empty, the script fails fast in
one second (by design) rather than waste a ~20-agent run — resolve them and relaunch.

### 2. Launch

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/biz-case-workflow/workflows/biz_case.js",
  args: {
    question: "<the user's question, verbatim — do not pre-digest it>",
    twDataPath: "<the resolved $TW — absolute, no ${...} left in it>",
    runDir: "<the resolved $RUN_DIR>"
  }
})
```

Pass `args` as a real JSON object. The script now tolerates a JSON *string* too
(it parses it), but the paths inside must still be absolute and fully expanded.
`question` and `twDataPath` are required; `runDir` is optional but strongly
recommended — without it nothing persists (no evidence pack, no report), results
live only in the session transcript.

### 3. Deliver it — pick the channel by where the reader actually is

When the workflow returns, `report.html` in `runDir` is a **single
self-contained file**: evidence inlined, no external resources, no `file:` links,
inline SVG charts, print-to-PDF ready. First screen is the action summary
(recommendation, stat tiles, flip conditions), then action-titled sections with
one chart each, the adversarial-verification record, untestable declarations,
divergences and blind spots, and the methodology/evidence appendix.

**First, check the report actually got written.** The report agent is the run's
fragile last step — a mid-response API drop or a credit lapse leaves a 60-minute
run with everything computed but no `report.html`. The return carries
`report_status` (`written` / `failed` / `skipped`); confirm with `ls
"$RUN_DIR/report.html"`. **If it's missing, do NOT re-run the workflow** — rebuild
deterministically from the result JSON (no agent, no network, cannot fail the way
the agent did):

```bash
# the harness already persisted the full result at the task-output path;
# build_report.py accepts that wrapper or a raw result object
python3 "$CLAUDE_PLUGIN_ROOT/skills/biz-case-workflow/workflows/build_report.py" \
  --result <task-output.json or extracted result.json> \
  --out "$RUN_DIR/report.html"
```

The rebuilt report renders every section (options map + killed causes, debates,
model, competitor table, what-you-need-to-believe, scenarios, signposts, evidence
appendix) as tables — the same numbers, self-contained, minus the SVG the agent
would have drawn. It is the guaranteed-delivery floor; the agent's version is the
nicer ceiling. (`resumeFromRunId` also works — 19 cached agents replay instantly
and only the report re-runs — but it needs the same session and can hit the same
API/credit wall; the deterministic rebuild cannot.)

That file is the artifact; how you hand it over depends on the reader's surface.
The channels are NOT equally reliable — this ladder is from hard experience:

| Channel | Opens on a phone / remote-control session? | Needs a login? | Fidelity |
|---|---|---|---|
| **Google Doc via a Drive MCP** | ✅ native Docs/Drive app | the user's own Google (already signed in) | high — charts become tables |
| Chat body (recommendation + findings as text) | ✅ always | no | text only |
| Delivered file attachment (PDF / HTML / PNG) | ❌ card shows, tap does nothing | — | — |
| Artifact URL | ❌ 404 unless signed in | claude.ai | full, incl. charts |
| `report.html` / PDF on disk | ✅ but only back at the desktop | no | full |

**So deliver by surface:**

- **Desktop / a real local path:** `report.html` opens straight from disk. Offer
  a PDF too — headless Chrome renders the SVG faithfully:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --no-pdf-header-footer --print-to-pdf="$RUN_DIR/report.pdf" "file://$RUN_DIR/report.html"`.
- **Phone or a remote-control session — the reader can't open attachments and
  isn't on claude.ai:** if a **Google Drive MCP is connected**, that is the
  delivery. Upload the report as an HTML file with conversion ON so Drive turns it
  into a Google Doc (`create_file` with `contentMimeType: "text/html"`,
  `disableConversionToGoogleType: false`). The conversion **drops inline SVG**, so
  build that upload from a table-based version of the charts, not the SVG report.
  The user opens it in the native Docs app — no claude.ai login, no attachment card.
  If no Drive MCP is available, put the recommendation and the driving findings
  **in the chat body** — it is the only surface that always renders — and note the
  full report is on disk for when they're back at a desktop.
- **On claude.ai (web/desktop app):** publishing the self-contained `report.html`
  as an **Artifact** gives a private URL with the charts intact. Treat it as the
  value-add for a signed-in reader, not the primary mobile path — the URL 404s for
  anyone not signed in.

`runDir` stays the on-disk audit copy — `report.html` plus `evidence/*.md`, one
per pull (exact command, fetch timestamp, source, raw output; re-running the
recorded command IS the audit). Nothing above replaces it; they are how the reader
*sees* it, on whatever surface they're on.

**Sharpen the question before launching, not after.** The scope phase is only as
good as what it receives, and a vague question produces a vague case at full
cost. If the question doesn't name a *decision* — enter or not, invest or not,
now or later — ask one or two clarifying questions first. "研究台灣餐飲市場" is
not yet a case; "should we open a 火鍋 chain in 台中 next year" is.

## What it does

Hypothesis-driven, per the composite MBB/sell-side method (Martin/Lafley
strategic-choice structuring × McKinsey driver models × Goldman key debates):

| Phase | What happens |
|---|---|
| **Situation** | The market-and-consumer foundation laid down BEFORE any option: market definition, size with an explicit build, quantified consumer segments (income×geo×age from 家庭收支; behavioral from TAICCA/DNR), media/payment behavior, unmet needs (hypotheses labeled), trends. Every finding ends in the linkage grammar: [quantified behavior]+[structural reason]→[opportunity/threat] |
| **Frame** | 2-4 MUTUALLY EXCLUSIVE strategic options (status quo included), each a coherent "happy story" of how it wins, grounded in the Situation. No critique yet — skepticism becomes conditions |
| **Conditions** | Per option: what would have to be TRUE (industry / customer / position / competition), weeded to 3-6 binding conditions, each scored with pre-test confidence |
| **Debates** | The lowest-confidence conditions become 2-4 key debates — bull and bear both at full strength. A skeptic agent designs each test: metric, pass threshold at the highest standard of proof, runnable data plan |
| **Test** | Lazy-man loop (≤3 rounds): least-believed conditions first, cheap kills first. A failed must-have condition kills its option — no further spend on it. Insufficient evidence triggers an EXPANDED search (analog markets, web) next round |
| **Model** | Driver-tree market model: explicit boundary, hypothesis-driven segments, 3-5 drivers each with a named basis (Taiwan series or analog-market curve), a two-ended range, sensitivity on the two most contested drivers, top-down vs bottom-up reconciliation |
| **Competitors** | One bespoke decomposition applied symmetrically to up to 6 named players; each gets real metrics (period + source), a strategic archetype, and a binding constraint |
| **Choose** | Anticlimactic: fewest unresolved barriers wins (or "undecidable" + the cheapest decisive action). Bull/base/bear = the debates resolving each way. Then a completeness critic attacks what is missing |
| **Report** | Self-contained HTML: options map with killed options and their cause of death, the debates record, model, comp table, what-you-need-to-believe, signposts monitoring plan, inlined evidence appendix (skipped if no `runDir`) |

It returns `{report, report_status, decision, situation, options: {framed,
excluded, killed, alive}, debates, conditions, test_results, model,
competitors, choice, critique}`. `report_status` is `written` / `failed` /
`skipped` — on `failed`, rebuild `report.html` with `build_report.py` (see
"Deliver it" step 3).

The report is written as an ANALYST ARTICLE, not a data record: SCR opening
with a 摘要 box, continuous prose with claim-first topic sentences and paired
numbers, frameworks named as they are applied ("以 TAM driver tree 拆解…"),
killed options delivered with the four-move dignity template (verdict /
mechanism / quantified downgrade / resurrection clause), and verdict-speak
(PASS/FAIL) confined to the appendix. The full style contract lives in the
report agent's prompt.

## After the run: the case file and Q&A mode

A completed run leaves a CASE FILE: the result JSON (persisted at the task
output path) plus `runDir/evidence/*.md`. **Follow-up questions are answered
from the case file FIRST, new data second.** The protocol:

1. **Consult the case file**: the result JSON's `situation`, `test_results`
   findings, `model`, `competitors`, and the evidence files already carry
   sourced, period-stamped numbers. If the answer is there, answer from it and
   cite the original pull (source + period) — do not re-fetch what is already
   verified on disk.
2. **Say which it is**: answers from the case file are labeled as such
   (「根據本案已查證的資料…」); the reader must know whether they are getting
   the audited evidence or something new.
3. **Only then fetch new data** — when the case file genuinely cannot answer.
   Run the same discipline as the workflow (tw-data first, external-sources
   retrievals, then web; FetchError is a finding). Append what you fetched as
   a new `evidence/qa-<slug>.md` so the case file grows instead of forking.
4. **Never re-run the workflow to answer a question.** A full run is for a new
   decision, not a follow-up. If a follow-up reveals the case's framing was
   wrong, say so and propose a re-scope — that is the user's call.

Cost: expect roughly 25-45 agents and 2-4M tokens per run — two to three times
the old verification pipeline. It buys a strategy machine instead of a
fact-checking machine; for a single verified fact, use `tw-data` directly.

## Why it is shaped this way

**Options before evidence.** Until at least two mutually exclusive options are
framed, no choice can be made — analysis without a choice frame is territory
survey. The status quo enters as an option and faces the same tests.

**Conditions, not arguments.** "What would have to be true" needs no evidence
yet and cannot be disputed as fact — which is what converts a team's
disagreement into testable conditions instead of dueling advocacy. The
skeptic doesn't argue; the skeptic sets the falsification bar.

**Lazy-man sequencing.** Test the least-believed condition first; if it fails,
the option dies with no further spend. Analysis goes an inch wide and a mile
deep on what actually decides the case.

**Two-ended ranges, analog parameterization.** Where Taiwan has no number, a
named analog market's curve (JP/KR/HK/SG) bounds it — parameterization by
precedent, not abstract optimism. Single-point estimates are prohibited.

**Killed options ship with their cause of death.** The
rejected-alternatives exhibit is a credibility engine, not an embarrassment.

## Reading the output

Read `choice.what_you_need_to_believe` and `critique` first — they are the
honest account of what remains assumption. Then `options.killed`: a killed
option whose cause of death is thin deserves a second look. `test_results`
verdicts of `insufficient` after 3 rounds mean the search was exhausted, not
that the answer is no.

## Re-running

Every invocation persists its script and returns a `runId`. To iterate — a
sharper question, a fixed prompt — edit the returned script path and re-launch
with `{scriptPath, resumeFromRunId}`. The unchanged prefix returns from cache;
only what you changed re-runs. Re-scoping is cheap; re-pulling data is not.

## When it will disappoint you

- **B2B or B2G questions.** The data layer is strongest on consumer, because
  家庭收支調查 is a household survey. The workflow will correctly refuse to size
  a B2B market from it, which means it returns a thin case. That is honest, not
  broken — but know it before you spend the agents.
- **Mixed revenue models — 訂閱＋廣告, platforms, freemium.** Media is the
  canonical case: the consumer half gets data, the advertising/B2B half is
  fully blind (the ad market number lives in DMA's PDF report, not open data).
  The case comes back half-covered by construction.
- **Markets narrower than the household survey's 10 categories.** A magazine, a
  streaming service, a niche product — `--tam` can only give the whole bucket,
  which may be orders of magnitude wider. The workflow now refuses to swap the
  bucket in, so these come back as "undecidable, run a pretest".
- **Anything hinging on behaviour or willingness data** — conversion, churn,
  付費意願. Government statistics don't ask; a paid pretest or Reuters DNR's
  Taiwan page is the actual source.
- **Pure services industries** — media, education, professional services are
  invisible to all four fast reads (no 出版/媒體 in TWSE's 33 產業別; MOEA is
  manufacturing-only). `mof_industry.py` (營業稅 by industry, includes SMEs) is
  the free fallback and is now wrapped.
- **Fragmented consumer categories.** Listed-company revenue can't see SMEs, so
  competitive questions about restaurants or clinics come back with a large,
  explicit blind spot.
- **Anything needing margin or cost structure.** Not available free, anywhere —
  and for a licensed brand (a WIRED, a franchise), the licence fee is a cost
  line no public data will ever show you.

Related: `tw-data` for the numbers, `strategy-frameworks` for the framework
choice this workflow automates.
