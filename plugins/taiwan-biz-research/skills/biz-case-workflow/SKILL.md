---
name: biz-case-workflow
description: Run a full Taiwan business case end-to-end as a multi-agent workflow — scope the decision into falsifiable claims, fan out agents to pull real government data, cross-check the independent sources against each other, adversarially refute every claim from three lenses, then synthesize a recommendation with a completeness critic. Use when someone asks for a Taiwan market-entry, sizing, competitor, investment or timing case, an evidence-backed recommendation, or "研究一下台灣的 X 市場" — anything where the answer must be defensible rather than plausible. Not for a single lookup; use tw-data directly for that.
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

### 3. Deliver it — the report must be openable, including on a phone

When the workflow returns, `report.html` in `runDir` is a **single
self-contained file**: evidence inlined, no external resources, no `file:` links,
inline SVG charts, print-to-PDF ready. First screen is the action summary
(recommendation, stat tiles, flip conditions), then action-titled sections with
one chart each, the adversarial-verification record, untestable declarations,
divergences and blind spots, and the methodology/evidence appendix.

- **Local:** it opens straight from disk.
- **Phone, share, or a cowork/cloud session with no usable local path:** read the
  file and publish it as an **Artifact**. It was built to the Artifact contract
  (self-contained, inline SVG, offline-forever), so it publishes as-is and returns
  a private URL that opens on mobile.

`runDir` is the on-disk audit copy — `report.html` plus `evidence/*.md`, one per
pull (exact command, fetch timestamp, source, raw output; re-running the recorded
command IS the audit). The **Artifact is the portable, mobile-openable
deliverable**. In a session with no usable local path, the Artifact IS the delivery.

**Sharpen the question before launching, not after.** The scope phase is only as
good as what it receives, and a vague question produces a vague case at full
cost. If the question doesn't name a *decision* — enter or not, invest or not,
now or later — ask one or two clarifying questions first. "研究台灣餐飲市場" is
not yet a case; "should we open a 火鍋 chain in 台中 next year" is.

## What it does

| Phase | What happens |
|---|---|
| **Scope** | One agent turns the question into a decision, picks ONE framework via `strategy-frameworks`, and writes 3-6 falsifiable claims + a plan of 3-6 *independent* data pulls |
| **Evidence** | One agent per pull, running the `tw-data` scripts for real. A failed fetch is reported as a failure — never backfilled from memory |
| **Crosscheck** | A barrier: all evidence lands, then one agent reconciles the independent reads. Agreement is confirmation; divergence is the finding |
| **Verify** | Every claim attacked by three agents with different lenses — data, reasoning, framing. Two refutations kill the claim |
| **Synthesize** | The case is written from survivors only, then a completeness critic names what is still missing |
| **Report** | One agent turns everything — draft, critique, verification record, untestable list, evidence links — into the self-contained HTML report (skipped if no `runDir`) |

It returns `{report, decision, framework, untestable, draft, critique, claims: {survived, refuted}, evidence, crosscheck, failed_pulls}`.

## Why it is shaped this way

Three decisions in the script that are not arbitrary:

**Independent pulls, not more pulls.** `tw-data` covers four separate reads on
the same economy — the cycle light, listed-company revenue, export orders, and
production/retail. Four pulls from one script is one read with extra steps. The
scope agent is told this explicitly because it is the easy mistake.

**Three lenses, not three refuters.** A business-case claim fails in three
distinct ways: the number is wrong (data), the number doesn't support the claim
(reasoning), or the claim answers a question nobody asked (framing). Three
identical skeptics find the first and miss the other two.

**Refuted claims are passed to the synthesizer as refuted.** Otherwise they
quietly reappear — a dead claim that was central is itself worth reporting.

## Reading the output

The `draft` is not the deliverable. Read `critique` first — it is the honest
account of what the draft is missing — then decide whether to patch the draft or
re-run with a tighter question.

Also check `failed_pulls` before presenting anything. A case built on three of
five planned sources may still be sound, but the reader is entitled to know.
Silence about a failed pull reads as coverage that never happened.

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
