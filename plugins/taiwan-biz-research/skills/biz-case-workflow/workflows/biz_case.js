export const meta = {
  name: 'tw-biz-case',
  description: 'Run a Taiwan business case end-to-end: scope the decision, gather real government data, cross-check independent sources, adversarially verify every claim, synthesize a recommendation',
  whenToUse: 'A Taiwan market-entry, sizing, competitor, investment or timing question that needs numbers behind it rather than assertions',
  phases: [
    { title: 'Scope', detail: 'turn the question into a decision, a framework, and falsifiable claims' },
    { title: 'Evidence', detail: 'one agent per data pull, running the tw-data scripts for real' },
    { title: 'Crosscheck', detail: 'reconcile the independent reads — agreement or divergence' },
    { title: 'Verify', detail: 'adversarial refutation of each claim, three lenses' },
    { title: 'Synthesize', detail: 'assemble the case; a critic names what is still missing' },
    { title: 'Report', detail: 'self-contained HTML report with charts and the evidence appendix' },
  ],
}

// args can arrive as a JSON *string* instead of an object (the Workflow tool
// warns of this). Parse it first — otherwise args.twDataPath / args.runDir are
// undefined and the whole blob silently lands in `question`, wasting a full run.
if (typeof args === 'string') {
  try { args = JSON.parse(args) } catch { /* leave as-is; caught by guards below */ }
}

const question = (args && args.question) || (typeof args === 'string' ? args : null)
const TW = (args && args.twDataPath) || ''
// Deliverables land here: evidence/*.md per data pull + report.html. Without it
// the workflow still runs, but nothing persists beyond the session transcript.
const RUN_DIR = (args && args.runDir) || null

if (!question) {
  return { error: 'No question supplied. Pass args as an object: {question, twDataPath, runDir}.' }
}
// twDataPath is an INPUT: without a real absolute path the data agents have
// nothing to run and the entire ~20-agent run is wasted. Fail in one second, not
// thirty minutes. A leftover ${...} means the caller never expanded the plugin
// root — the sandbox cannot do it (no env, no fs), so this is a launch bug.
if (!TW || TW.includes('${')) {
  return { error: `twDataPath must be an absolute, fully-expanded path to the tw-data skill dir (got: ${JSON.stringify(TW)}). Resolve \${CLAUDE_PLUGIN_ROOT} in a bash step before launching — see the skill's "Run it" section.` }
}
// runDir is an OUTPUT and optional, but a literal ${...} would write the audit
// trail to a nonsense directory — same launch bug, so reject it too.
if (RUN_DIR && RUN_DIR.includes('${')) {
  return { error: `runDir was passed unexpanded (got: ${JSON.stringify(RUN_DIR)}). Compute an absolute path (cwd + slug + date) before launching, or omit it entirely.` }
}

// Every agent needs to know how to actually run the data layer, and needs the
// same standing rules about what these numbers do and do not support.
const CONTEXT = `
You are working a Taiwan business case. The question:

  ${question}

The tw-data skill's scripts live at:
  ${TW}
Run them with python3 from that directory, e.g.:
  cd ${TW} && python3 scripts/ndc_signal.py --json

Available (read ${TW}/SKILL.md if you need the full surface):
  scripts/ndc_signal.py     景氣對策信號 cycle light + components, monthly, 1984-
  scripts/household.py      家庭收支調查 --spend --mix --quintile --tam <類別>
  scripts/twse_revenue.py   listed-company monthly revenue --industry --top --bottom --company
  scripts/moea_orders.py    --orders <類別> (leading) --production [--sectors|--sector] --retail
  scripts/dgbas_macro.py    --gdp --cpi --unemployment --wage [--items]
  scripts/mof_industry.py   營業稅銷售額 by 行業 (3碼小類, 含SME/服務業) --list --industry --county

For numbers outside open data — ad market size (DMA), willingness to pay
(Reuters DNR), industry survey output (TAICCA), precedents — read
${TW}/references/external-sources.md: verified URLs, retrieval methods and
dated snapshots. Re-fetch before citing; snapshots go stale.

Standing rules — violating these makes the output worthless:
- HTTP 200 does not mean data. If a script raises FetchError, report the failure.
  NEVER substitute a number from your own memory for a failed fetch. A missing
  number is a finding; a hallucinated one is a fabrication.
- Anchor every number to its period AND its source. Sources publish on different
  lags: cycle light ~2 months, 家庭收支 ~18 months, MOI households ~1 year.
- 家庭收支調查 is household consumption only — no corporate or government demand.
- TWSE revenue is LISTED companies only. Taiwan's economy is mostly SME. Never
  present a share computed from this as market share.
- Always run --sectors before --sector; the names are not what you would guess.
`.trim()

const SCOPE_SCHEMA = {
  type: 'object',
  required: ['decision', 'framework', 'framework_rationale', 'claims', 'data_plan', 'untestable_claims'],
  properties: {
    decision: { type: 'string', description: 'The actual decision this case informs, in one sentence' },
    framework: { type: 'string', description: 'The ONE framework that answers it' },
    framework_rationale: { type: 'string', description: 'What result would flip the recommendation. If nothing would, say so.' },
    consumer_or_b2b: { type: 'string', enum: ['consumer', 'b2b', 'b2g', 'mixed'] },
    claims: {
      type: 'array',
      description: '3-6 falsifiable claims that together decide the question',
      items: {
        type: 'object',
        required: ['claim', 'falsified_by'],
        properties: {
          claim: { type: 'string' },
          falsified_by: { type: 'string', description: 'The concrete observation that would kill this claim' },
        },
      },
    },
    untestable_claims: {
      type: 'array',
      description: 'Decision-critical questions this data layer CANNOT answer (willingness to pay, ad/B2B market size, cost structure, sub-category demand finer than the 10 survey buckets). Naming them is required honesty, not failure. Empty array only if the decision is fully coverable.',
      items: { type: 'string' },
    },
    data_plan: {
      type: 'array',
      description: 'Up to 6 independent data pulls, each naming the exact command to run. If fewer than 3 genuinely bear on the decision, return the smaller number and say so — do NOT pad with weakly-related macro series to look thorough',
      items: {
        type: 'object',
        required: ['label', 'command', 'why'],
        properties: {
          label: { type: 'string' },
          command: { type: 'string' },
          why: { type: 'string', description: 'Which claim this bears on' },
        },
      },
    },
  },
}

const EVIDENCE_SCHEMA = {
  type: 'object',
  required: ['label', 'succeeded', 'findings'],
  properties: {
    label: { type: 'string' },
    succeeded: { type: 'boolean', description: 'false if the fetch failed — do not invent data' },
    error: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['statement', 'value', 'period', 'source'],
        properties: {
          statement: { type: 'string' },
          value: { type: 'string' },
          period: { type: 'string', description: 'The period this number is FOR, e.g. 2026M05, 2024' },
          source: { type: 'string' },
          caveat: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['refuted', 'reasoning'],
  properties: {
    refuted: { type: 'boolean' },
    reasoning: { type: 'string' },
    strongest_counterevidence: { type: 'string' },
  },
}

// ── Scope ────────────────────────────────────────────────────────────────────
phase('Scope')
const scope = await agent(`${CONTEXT}

Scope this case before any data is pulled.

Read ${TW}/../strategy-frameworks/SKILL.md and follow its routing table to pick
the framework. Pick exactly ONE. The rule that matters: a framework earns its
place only if a plausible fill of its boxes would flip the recommendation — if
nothing would, say so plainly in framework_rationale rather than picking a
framework anyway.

Then write 3-6 falsifiable claims, and a data_plan of INDEPENDENT pulls.
Independent matters: the cycle light, listed revenue, export orders, and
production/retail are four separate reads on the same economy, and the case is
only as strong as their agreement. Do not plan four pulls that all come from
the same script.

If the decision hinges on questions this data layer cannot answer at all —
willingness to pay, advertising or any B2B market size, cost structure,
sub-category demand finer than the household survey's 10 buckets, a services
industry invisible to all four reads — list them in untestable_claims. A case
that is partly undecidable on this data is a legitimate scoping outcome;
padding the data_plan with weakly-related macro pulls to reach 3 is not.

Each data_plan command must be a real, runnable command line.`,
  { label: 'scope', schema: SCOPE_SCHEMA })

if (!scope) return { error: 'Scoping failed.' }
log(`Framework: ${scope.framework} · ${scope.claims.length} claims · ${scope.data_plan.length} pulls · ${(scope.untestable_claims || []).length} untestable`)

// The b2b/mixed classification must reach every later phase, or it dies here as
// a decoration — the ad-revenue half of a media case has no data source at all.
const CONTEXT2 = scope.consumer_or_b2b && scope.consumer_or_b2b !== 'consumer'
  ? `${CONTEXT}\n\nThis case is ${scope.consumer_or_b2b}: this plugin has NO data source for the B2B side, including the advertising market. Claims on that side are untestable here — label them so; do not proxy them with retail or consumer series and let the page density imply evidence that does not exist.`
  : CONTEXT
const UNTESTABLE = (scope.untestable_claims || []).length
  ? `\n\nDeclared untestable at scope (no data source in this plugin — these stay open questions, never silently resolved):\n${scope.untestable_claims.map(u => `- ${u}`).join('\n')}`
  : ''

// ── Evidence ─────────────────────────────────────────────────────────────────
// Fan out one agent per pull. These genuinely need to converge before the
// cross-check can reconcile them, so the barrier below is real.
phase('Evidence')
const evidence = (await parallel(scope.data_plan.map(p => () =>
  agent(`${CONTEXT2}

Execute this data pull and report ONLY what the output actually says.

  Label:   ${p.label}
  Command: ${p.command}
  Bears on: ${p.why}

Run it for real. If it fails, set succeeded=false and report the error — a
failed pull is a legitimate result. Do not fall back to remembered numbers.

If the command has a syntax problem (bad flag, misspelled name), fix it and
note what you changed — run --sectors / --items first to discover valid names.
But NEVER substitute a coarser category for a target the data cannot resolve:
if no category matches the target market at the right granularity (e.g.
--tam 雜誌 fails and the nearest bucket is a 10-category aggregate), report
succeeded=false and say which bucket exists and roughly how much wider it is.
A too-wide number silently swapped in is worse than no number.

Every finding needs the period it is FOR, not the date you ran it.
${RUN_DIR ? `
Persist the audit trail: after reporting, Write ${RUN_DIR}/evidence/${p.label}.md
containing (1) every command you ran, verbatim, (2) the fetch timestamp, (3) the
source URL(s) the script hits, (4) the complete raw stdout — truncate beyond
~200 lines and say so. This file is how a reader verifies your numbers without
trusting you: the sources are free and keyless, so re-running the command IS the
verification. Failed pulls get an evidence file too, recording the error.` : ''}`,
    { label: `pull:${p.label}`, phase: 'Evidence', schema: EVIDENCE_SCHEMA })
))).filter(Boolean)

const ok = evidence.filter(e => e.succeeded)
const failed = evidence.filter(e => !e.succeeded)
if (failed.length) log(`${failed.length} pull(s) failed: ${failed.map(f => f.label).join(', ')}`)
if (!ok.length) {
  return { error: 'Every data pull failed.', scope, failed }
}
log(`${ok.length}/${evidence.length} pulls returned data`)

// ── Crosscheck ───────────────────────────────────────────────────────────────
// Needs all evidence at once by construction: it is about the relationship
// BETWEEN the independent reads.
phase('Crosscheck')
const crosscheck = await agent(`${CONTEXT2}${UNTESTABLE}

Here is the evidence gathered from independent sources:

${JSON.stringify(ok, null, 2)}

${failed.length ? `These pulls FAILED and their gap must be acknowledged:\n${JSON.stringify(failed.map(f => ({label: f.label, error: f.error})), null, 2)}` : ''}

Reconcile them. Specifically:
- Where do independent sources AGREE? Those findings are solid.
- Where do they DIVERGE? The divergence is itself the finding — the classic
  Taiwan case is a national indicator booming on export electronics while
  domestic demand is flat. Do not average a divergence away.
- Are any two "independent" numbers actually the same underlying series? Say so.
- Do the periods line up? A table mixing 2024 spend with 2026 households is
  acceptable but MUST be labelled.
- Coverage, not just coherence: even if every source agrees, how much of the
  DECISION do they jointly cover? Which decisive questions have zero evidence?
  Three weakly-related series agreeing is not a covered case — say plainly if
  this evidence, all of it true, still could not answer the question asked.

Return prose. Lead with what the sources jointly establish, then what they
contest.`, { label: 'crosscheck', phase: 'Crosscheck' })

// ── Verify ───────────────────────────────────────────────────────────────────
// Three distinct lenses per claim, not three identical refuters: a claim here
// can fail on the data, on the reasoning, or on the framing.
phase('Verify')
const LENSES = [
  { key: 'data', prompt: 'Attack the DATA: is the number real, current, and does the source actually cover what the claim needs? Is 家庭收支 being used for B2B? Is a listed-company figure being passed off as market share? Is a stale period doing work it cannot? Is a budget-SHARE trend doing work only an absolute-NT$ LEVEL trend can do — a subscription or sales claim needs the level series (share × per-household spend, CPI-deflated), and the two can move oppositely?' },
  { key: 'logic', prompt: 'Attack the REASONING: does the evidence actually support this claim, or merely coexist with it? Correlation sold as cause? A national signal applied to a niche? A SOM presented as if data produced it? An attribution the data cannot make — e.g. a bundled category trend (education + travel + media in one bucket) read as evidence about one sub-slice, when 少子化 or a pandemic could be driving the whole move?' },
  { key: 'framing', prompt: 'Attack the FRAMING: is this claim answering the decision that was actually asked, or a neighbouring question that happens to have data? Would the recommendation change if this claim were false — if not, the claim is decoration. Run the symmetry test: could the same evidence support the OPPOSITE reading equally well (a hot cycle read as cost headwind vs customer-income tailwind)? If both readings flow, the claim is a choice dressed as a derivation.' },
]

const verified = await parallel(scope.claims.map(c => () =>
  parallel(LENSES.map(l => () =>
    agent(`${CONTEXT2}

Adversarially test this claim. Your job is to REFUTE it, not to be fair.

  Claim:        ${c.claim}
  Falsified by: ${c.falsified_by}

${l.prompt}

Evidence available:
${JSON.stringify(ok, null, 2)}

Cross-check reading:
${crosscheck}

You may re-run any tw-data command to check. Default to refuted=true when you
are uncertain — an unproven claim in a business case is a liability, and it is
far cheaper to drop a true claim than to ship a false one.`,
      { label: `verify:${l.key}`, phase: 'Verify', schema: VERDICT_SCHEMA })
  )).then(votes => {
    const v = votes.filter(Boolean)
    const refutations = v.filter(x => x.refuted)
    return {
      claim: c.claim,
      falsified_by: c.falsified_by,
      survives: v.length > 0 && refutations.length < 2,
      refutations: refutations.map(x => x.reasoning),
    }
  })
))

const good = verified.filter(Boolean)
const survivors = good.filter(c => c.survives)
const killed = good.filter(c => !c.survives)
log(`${survivors.length}/${good.length} claims survived; ${killed.length} refuted`)

// ── Synthesize ───────────────────────────────────────────────────────────────
phase('Synthesize')
if (!survivors.length) log('Zero claims survived — the case will be written as undecidable, not as a recommendation')
const draft = await agent(`${CONTEXT2}${UNTESTABLE}

Write the business case.
${survivors.length ? '' : '\nNOTE: ZERO claims survived adversarial verification. This case MUST be written as undecidable on the available data — a confident recommendation in either direction is prohibited. The deliverable is: what was tested, why each claim died, and the cheapest action that would make the case decidable.\n'}

Decision:  ${scope.decision}
Framework: ${scope.framework} — ${scope.framework_rationale}

Claims that SURVIVED adversarial verification:
${JSON.stringify(survivors, null, 2)}

Claims that were REFUTED — these must NOT reappear as findings. Where one was
central, its death is itself worth reporting:
${JSON.stringify(killed, null, 2)}

Evidence:
${JSON.stringify(ok, null, 2)}

Cross-check:
${crosscheck}

${failed.length ? `Failed pulls (state these as gaps):\n${JSON.stringify(failed.map(f => ({label: f.label, error: f.error})), null, 2)}` : ''}

Structure:
1. The recommendation, in one sentence, first. If the surviving evidence cannot
   support a yes/no, the honest first sentence is "本案無法以現有資料裁決" plus
   the cheapest action that WOULD decide it (a pretest, one external number) —
   that is a recommendation too, and a better one than false confidence.
   Absence of evidence is never evidence for "no": do not let untestable claims
   silently harden into negative findings. And run point 5 BEFORE writing this
   sentence: when the option-space check yields a cheaper decisive action, that
   action IS the headline recommendation — do not headline the binary and
   demote the honest answer to a later section.
2. The two or three findings that drive it, each with its number, period and source.
3. Where the independent sources diverge, and what that divergence means.
4. What would change the recommendation — concretely, and actually observable
   within a realistic horizon. A flip condition that cannot trigger for years,
   or has no precedent in the series, is decoration; prefer an action the reader
   could take (a paid pretest, obtaining one named external report).
5. Before committing to a binary, check the option space: does the evidence
   point at a cheaper third option (a scoped-down variant, a pretest)? If your
   own numbers put a success threshold within your own estimated range, the
   recommendation is "test it", not "no".
6. What this analysis cannot see (SME gap, B2B blind spot, publication lag,
   failed pulls, bundled categories that cannot be decomposed). Be specific; a
   vague caveat is not a caveat. And check yourself: no headline finding may
   rest on a decomposition your own caveat list says the data cannot make.

The framework is scaffolding — it does not appear in the output. What ships is a
claim, a number, and what would falsify it. Never present an unsourced number.`,
  { label: 'draft', phase: 'Synthesize' })

const critique = await agent(`${CONTEXT2}${UNTESTABLE}

Here is a draft Taiwan business case:

---
${draft}
---

You are the completeness critic. Do not praise it. Name only what is MISSING or
WRONG:
- A number with no period or no source attached?
- A claim that quietly returned after being refuted?
- A caveat that is stated so vaguely it does nothing (e.g. "data has limits")?
- A caveat that CONTRADICTS a headline finding — if the blind-spot list says a
  category cannot be decomposed, no finding may rest on that decomposition?
- An independent source that should have been consulted and was not — inside
  this plugin's four reads, OR outside it (an industry report, a survey, a
  precedent a WebSearch would find)? Name the specific missing source.
- The symmetry test: rewrite the recommendation's opposite using only numbers
  already in the draft. If it reads just as well, the recommendation is not a
  function of the evidence — say so.
- Does the recommendation collapse the choice to a binary when the draft's own
  numbers leave a cheaper third option (a pretest, a scoped-down variant) open?
- Does it actually answer "${scope.decision}", or a neighbouring question?
- Is the recommendation falsifiable, or hedged into meaninglessness? Are the
  flip conditions triggerable within a realistic horizon, or decorative?
- Is "no evidence available" anywhere being converted into "evidence of no"?

Return a short prioritised list. If something is genuinely fine, say nothing
about it.`, { label: 'critic', phase: 'Synthesize' })

// ── Report ───────────────────────────────────────────────────────────────────
phase('Report')
let reportPath = null
if (RUN_DIR) {
  reportPath = `${RUN_DIR}/report.html`
  await agent(`${CONTEXT2}

Build the deliverable: ONE self-contained HTML report at ${reportPath} (use the
Write tool). 正體中文. No external resources — no CDN, no webfonts, no <img>;
system font stack and inline SVG only, so the file opens offline forever.

Raw material:
- Draft case:\n${draft}
- Critic's findings — fix what is fixable in the report; what you cannot fix
  goes verbatim into a「已知限制」box. Hiding any of it is falsification:\n${critique}
- Claims that survived adversarial verification: ${JSON.stringify(survivors)}
- Claims refuted (with reasons): ${JSON.stringify(killed)}
- Untestable declarations: ${JSON.stringify(scope.untestable_claims || [])}
- Evidence: ${JSON.stringify(ok)}
- Failed pulls: ${JSON.stringify(failed.map(f => ({ label: f.label, error: f.error })))}
- Cross-check reading:\n${crosscheck}
- The full evidence is in the `ok` array above — command, output, source per
  pull. INLINE it into the methodology appendix (§6). Do NOT hyperlink to
  evidence/*.md: a file: link dies the instant this HTML is opened on another
  machine, on a phone, or published as an Artifact. This file must stand alone.

Structure (Pyramid Principle — the answer first, then the support):

1. 行動摘要, the whole first screen: the recommendation as one large-type
   sentence; 3-4 stat tiles (headline number + period + one-line claim each);
   the flip conditions as concrete actions; a visible badge row for
   untestable-count and failed-pull-count. A reader who stops here has the
   answer.
2. Sections, each headed by an ACTION TITLE — a complete sentence stating the
   point (「本土出版商可競爭的廣告池只占市場 14%」), never a topic noun
   (「廣告市場分析」). The titles alone, read in order, must reconstruct the
   argument — that is the titles test, and it is the acceptance bar.
   One chart per section where a series exists. Every number carries 期間 and
   來源 as text (not a link) — the raw evidence is testified in §6 below.
3. 對抗驗證紀錄: a table of every claim — survived ones with what they withstood,
   refuted ones with their cause of death. This is the report's credibility
   engine; give it space.
4. 不可檢驗聲明: what this analysis declared it cannot know, and where that
   number would come from (name the source). Never let absence read as negative
   evidence.
5. 分歧與盲區: where independent sources disagree and what that means; the SME
   gap, publication lags, bundled categories.
6. 方法論與證據附錄: one row per pull — command, fetch timestamp, source, and
   the key raw output inlined right there (wrap long output in a <details> block
   so it collapses). No file: links — the evidence travels inside this file.
   Close with one line: 所有來源免費、免金鑰、公開，重跑指令即是驗證.

Chart rules (inline SVG):
- Line for time series, horizontal bars for rankings, stacked bar for
  composition; no pie beyond 5 slices. Label axes with real 期間 values; mark
  data gaps visibly instead of interpolating over them.
- One accent color (#2563eb) plus neutral grays; red (#dc2626) reserved for
  negative values and refuted claims. Every datapoint gets an SVG <title> so
  hover shows the exact value. Include the number as text next to key points —
  the chart illustrates, the text testifies.
- Chart headline = its action title; caption = source + period.

Also: <meta charset="utf-8">, responsive (max-width ~960px, readable on mobile),
@media print rules with sane page breaks so print-to-PDF works, footer with
generation date, plugin name/version, and the run directory path.

Your final message: just confirm the file was written and list any critic
points you could not fix.`,
    { label: 'report', phase: 'Report' })
} else {
  log('No runDir supplied — skipping evidence pack and HTML report; results return inline only')
}

return {
  report: reportPath,
  decision: scope.decision,
  framework: scope.framework,
  untestable: scope.untestable_claims || [],
  draft,
  critique,
  claims: { survived: survivors, refuted: killed },
  evidence: ok,
  crosscheck,
  failed_pulls: failed.map(f => ({ label: f.label, error: f.error })),
}
