export const meta = {
  name: 'tw-biz-case',
  description: 'Hypothesis-driven Taiwan business case: frame mutually exclusive strategic options, reverse-engineer what-would-have-to-be-true conditions, surface key debates with skeptic-designed tests, run an iterative lazy-man evidence loop, build a driver-tree market model with analog-market parameterization, profile competitors symmetrically, then choose the option with the fewest unresolved barriers',
  whenToUse: 'A Taiwan market-entry, sizing, competitor, investment or timing question where the answer must be a defensible strategic choice among options, not a single verified fact',
  phases: [
    { title: 'Frame', detail: 'turn the question into 2-4 mutually exclusive options, each a coherent winning story' },
    { title: 'Conditions', detail: 'per option: what would have to be true, across industry / customer / position / competition' },
    { title: 'Debates', detail: 'rank conditions by confidence; the weakest become key debates; skeptics design the tests' },
    { title: 'Test', detail: 'lazy-man loop: test the least-believed conditions first, kill options early, expand search when evidence runs dry' },
    { title: 'Model', detail: 'driver-tree market model: boundary, segments, two-ended range, analog-market parameters, sensitivity' },
    { title: 'Competitors', detail: 'one bespoke decomposition applied symmetrically to every named player; archetype + binding constraint each' },
    { title: 'Choose', detail: 'fewest unresolved barriers wins; killed options ship with their cause of death; critic names what is missing' },
    { title: 'Report', detail: 'self-contained HTML: debates record, model, comp table, what-you-need-to-believe, signposts, evidence appendix' },
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
const RUN_DIR = (args && args.runDir) || null

if (!question) {
  return { error: 'No question supplied. Pass args as an object: {question, twDataPath, runDir}.' }
}
// twDataPath is an INPUT: without a real absolute path the data agents have
// nothing to run and the entire run is wasted. Fail in one second, not an hour.
if (!TW || TW.includes('${')) {
  return { error: `twDataPath must be an absolute, fully-expanded path to the tw-data skill dir (got: ${JSON.stringify(TW)}). Resolve \${CLAUDE_PLUGIN_ROOT} in a bash step before launching — see the skill's "Run it" section.` }
}
if (RUN_DIR && RUN_DIR.includes('${')) {
  return { error: `runDir was passed unexpanded (got: ${JSON.stringify(RUN_DIR)}). Compute an absolute path (cwd + slug + date) before launching, or omit it entirely.` }
}

// Fan-out caps. The pipeline is expensive by design; these keep it bounded.
const MAX_OPTIONS = 4
const MAX_DEBATES = 4
const MAX_TESTS_PER_ROUND = 6
const MAX_ROUNDS = 3

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
(Reuters DNR), industry survey output (TAICCA), analog-market curves (JP/KR/
HK/SG penetration and paid rates), precedents — read
${TW}/references/external-sources.md: verified URLs, retrieval methods and
dated snapshots. Re-fetch before citing; snapshots go stale. You may also
WebSearch/WebFetch beyond that file when a test requires evidence the file
does not cover — an expanded search is legitimate; an invented number is not.

Standing rules — violating these makes the output worthless:
- HTTP 200 does not mean data. If a script raises FetchError, report the failure.
  NEVER substitute a number from your own memory for a failed fetch. A missing
  number is a finding; a hallucinated one is a fabrication.
- Anchor every number to its period AND its source.
- 家庭收支調查 is household consumption only — no corporate or government demand.
- TWSE revenue is LISTED companies only. Taiwan's economy is mostly SME. Never
  present a share computed from this as market share.
- Always run --sectors before --sector; the names are not what you would guess.
`.trim()

// ── Frame ────────────────────────────────────────────────────────────────────
// Martin/Lafley: until at least two mutually exclusive options are framed, the
// choice cannot be made. The status quo is itself an option and faces the same
// tests — unless no coherent winning story can be told for it, which is itself
// a recorded finding.
phase('Frame')

const FRAME_SCHEMA = {
  type: 'object',
  required: ['decision', 'options'],
  properties: {
    decision: { type: 'string', description: 'The actual decision this case informs, in one sentence' },
    consumer_or_b2b: { type: 'string', enum: ['consumer', 'b2b', 'b2g', 'mixed'] },
    options: {
      type: 'array',
      description: `2-${MAX_OPTIONS} MUTUALLY EXCLUSIVE strategic options. Include the status quo unless no winning story can be told for it (then record it in excluded_options).`,
      items: {
        type: 'object',
        required: ['id', 'name', 'happy_story', 'where_to_play', 'how_to_win'],
        properties: {
          id: { type: 'string', description: 'short slug, e.g. "asset-light"' },
          name: { type: 'string' },
          happy_story: { type: 'string', description: 'A coherent narrative of how this option WINS — intended advantage, scope, and the activities that deliver the advantage. Mild standard: internal coherence, not proof.' },
          where_to_play: { type: 'string' },
          how_to_win: { type: 'string' },
          is_status_quo: { type: 'boolean' },
        },
      },
    },
    excluded_options: {
      type: 'array',
      description: 'Options considered and excluded at framing (including the status quo if no winning story exists), each with the reason',
      items: {
        type: 'object', required: ['name', 'why'],
        properties: { name: { type: 'string' }, why: { type: 'string' } },
      },
    },
  },
}

const frame = await agent(`${CONTEXT}

Frame this question as a strategic CHOICE, per the Martin/Lafley discipline:

1. State the decision in one sentence. A genuine choice specifies what the firm
   will and will NOT do — the test: a competitor could take the rejected path
   and succeed. "Focus on the customer" is not a choice.
2. Generate 2-${MAX_OPTIONS} MUTUALLY EXCLUSIVE options. Each option is a "happy
   story": a coherent narrative of how the firm WINS by taking it — intended
   advantage, where to play, how to win. The standard at this stage is
   deliberately mild — internal coherence ending in winning, no proof required.
   NO critique at this stage; skepticism becomes testable conditions later.
3. Include the STATUS QUO as an option facing the same tests — unless no member
   could tell a winning story for it, in which case exclude it and say why.
4. Ground the options in reality: check (WebSearch) who already operates in this
   space in Taiwan — an option that ignores an existing local operation of the
   same brand/company is framed wrong.

Diversity matters: options should represent genuinely different theories of
winning (e.g. different revenue models, ownership structures, or entry vehicles),
not gradations of one idea.`,
  { label: 'frame', phase: 'Frame', schema: FRAME_SCHEMA })

if (!frame) return { error: 'Frame agent failed; nothing to test.' }
const options = frame.options.slice(0, MAX_OPTIONS)
log(`${options.length} options framed: ${options.map(o => o.id).join(', ')}`)

// ── Conditions ───────────────────────────────────────────────────────────────
// WWHTBT: for each option, what would have to be TRUE for it to be a terrific
// choice — conditions, not arguments. A condition needs no evidence yet and
// cannot be disputed as fact; that is what lets skeptics engage.
phase('Conditions')

const CONDITIONS_SCHEMA = {
  type: 'object',
  required: ['option_id', 'conditions'],
  properties: {
    option_id: { type: 'string' },
    conditions: {
      type: 'array',
      description: '3-6 binding conditions after weeding with the must-have test',
      items: {
        type: 'object',
        required: ['id', 'area', 'statement', 'must_have', 'confidence', 'why_confidence'],
        properties: {
          id: { type: 'string', description: 'unique slug across the whole case, e.g. "asset-light-royalty-terms"' },
          area: { type: 'string', enum: ['industry', 'customer', 'position', 'competition'] },
          statement: { type: 'string', description: 'Declarative: what WOULD HAVE TO BE TRUE. Not an argument about what IS true.' },
          must_have: { type: 'boolean', description: 'true if refuting this single condition kills the option' },
          confidence: { type: 'number', description: '0-1: current confidence this condition IS true, before testing. Low = barrier.' },
          why_confidence: { type: 'string' },
        },
      },
    },
  },
}

const conditionSets = (await parallel(options.map(o => () =>
  agent(`${CONTEXT}

Option under examination — imagine it as a GREAT idea, even if you dislike it
(the required mindset shift: from "what do I believe?" to "what would I have to
believe?"):

  [${o.id}] ${o.name}
  Happy story: ${o.happy_story}
  Where to play: ${o.where_to_play}
  How to win: ${o.how_to_win}

Reverse-engineer the conditions: what would have to be TRUE for this option to
be a terrific choice? Enumerate across FOUR areas:
- industry: structure/segmentation must look like...
- customer: channel and end-customer must value...
- position: our capabilities and cost position must be...
- competition: competitors must react by / be unable to...

Rules:
- Conditions are declarative statements about what WOULD NEED to be true —
  never arguments with evidence attached. Evidence comes later.
- Weed with the must-have test: "if every other condition held but this one,
  would you kill the option?" Keep only binding conditions (3-6).
- Score each condition with your honest CURRENT confidence it is true (0-1),
  and say why. Do NOT research to raise confidence — the low-confidence ones
  are supposed to surface; they become the tests.`,
    { label: `conditions:${o.id}`, phase: 'Conditions', schema: CONDITIONS_SCHEMA })
))).filter(Boolean)

const allConditions = conditionSets.flatMap(cs =>
  cs.conditions.map(c => ({ ...c, option_id: cs.option_id })))
log(`${allConditions.length} binding conditions across ${conditionSets.length} options`)

// ── Debates ──────────────────────────────────────────────────────────────────
// The conditions we are LEAST confident about are the key debates. Each debate
// is genuinely two-sided, evidence-resolvable, and value-material — and its
// test is designed by a skeptic at the highest standard of proof.
phase('Debates')

const DEBATES_SCHEMA = {
  type: 'object',
  required: ['debates'],
  properties: {
    debates: {
      type: 'array',
      description: `2-${MAX_DEBATES} key debates, drawn from the lowest-confidence binding conditions. A debate may span conditions from several options.`,
      items: {
        type: 'object',
        required: ['id', 'question', 'linked_condition_ids', 'bull', 'bear', 'value_at_stake'],
        properties: {
          id: { type: 'string' },
          question: { type: 'string', description: 'A genuine open question — informed people could hold either side' },
          linked_condition_ids: { type: 'array', items: { type: 'string' } },
          bull: { type: 'string', description: 'The strongest honest case that the condition IS true' },
          bear: { type: 'string', description: 'The strongest honest case that it is NOT' },
          value_at_stake: { type: 'string', description: 'What flips in the final recommendation if this resolves each way' },
        },
      },
    },
  },
}

const debatesOut = await agent(`${CONTEXT}

Here are every option's binding conditions with pre-test confidence scores:

${JSON.stringify(allConditions, null, 2)}

Identify the KEY DEBATES — the 2-${MAX_DEBATES} questions that actually decide
this case. Draw them from the LOWEST-confidence conditions (those are the
barriers; the elicitation test: "if you could buy a guarantee for one condition,
which would you buy first?"). Qualifying criteria, all required:
- genuinely two-sided: state the strongest honest bull AND bear case;
- decision-relevant: resolving it must change which option wins — if it
  wouldn't, it is background, cut it;
- evidence-resolvable: some obtainable data can adjudicate it;
- where one condition appears in several options, one debate covers them all.

Write both sides at full strength. A strawman bear case makes the whole
run worthless.`,
  { label: 'debates', phase: 'Debates', schema: DEBATES_SCHEMA })

const debates = (debatesOut && debatesOut.debates || []).slice(0, MAX_DEBATES)
log(`${debates.length} key debates framed`)

// Skeptic-designed tests: the doubter does not argue — they set the
// falsification bar, at the highest standard of proof any member would demand.
const TESTS_SCHEMA = {
  type: 'object',
  required: ['debate_id', 'tests'],
  properties: {
    debate_id: { type: 'string' },
    tests: {
      type: 'array',
      description: '1-3 tests for this debate, each runnable with named sources',
      items: {
        type: 'object',
        required: ['id', 'condition_id', 'metric', 'pass_threshold', 'standard_rationale', 'data_plan'],
        properties: {
          id: { type: 'string' },
          condition_id: { type: 'string' },
          metric: { type: 'string', description: 'The observable to measure' },
          pass_threshold: { type: 'string', description: 'Quantitative where possible: the value above/below which the condition PASSES' },
          standard_rationale: { type: 'string', description: 'Why this threshold is the HIGHEST standard a skeptic would demand — every parameter justified' },
          data_plan: { type: 'array', items: { type: 'string' }, description: 'Exact commands / sources to run, tw-data first, then external-sources.md retrievals, then web search angles' },
          cost: { type: 'string', enum: ['cheap', 'moderate', 'expensive'] },
        },
      },
    },
  },
}

const testDesigns = (await parallel(debates.map(d => () =>
  agent(`${CONTEXT}

You are the MOST SKEPTICAL member of the team on this debate. You do not argue —
you design the test that would satisfy YOU. Debate:

  ${d.question}
  Bull: ${d.bull}
  Bear: ${d.bear}
  Linked conditions: ${JSON.stringify(d.linked_condition_ids)}
  Conditions detail: ${JSON.stringify(allConditions.filter(c => d.linked_condition_ids.includes(c.id)), null, 2)}

Design 1-3 tests. Rules:
- Each test names a measurable metric and a pass threshold. Set the threshold
  at the HIGHEST standard of proof you would demand — justify every parameter
  (the AP-case style: "3 or fewer segments", "share equal to the leader",
  "70% of allowable cut" — each number was someone's stated bar).
- The data plan must be runnable: exact tw-data commands where the data layer
  covers it, retrieval methods from ${TW}/references/external-sources.md where
  it doesn't, and named web-search angles as the third rung. If NO obtainable
  evidence could adjudicate, say so via a data_plan entry "UNTESTABLE: <where
  the number would come from, e.g. a paid pretest>" — that is a legitimate
  outcome the choice phase must know about.
- Mark each test cheap/moderate/expensive. Cheap tests that could kill an
  option are the most valuable ones.`,
    { label: `test-design:${d.id}`, phase: 'Debates', schema: TESTS_SCHEMA })
))).filter(Boolean)

let allTests = testDesigns.flatMap(td =>
  (td.tests || []).map(t => ({ ...t, debate_id: td.debate_id })))
log(`${allTests.length} skeptic-designed tests`)

// ── Test (lazy-man loop) ─────────────────────────────────────────────────────
// Run the least-believed, cheapest-to-kill tests first. A failed must-have
// condition kills its option immediately — no further spend on it. Insufficient
// evidence triggers an expanded search next round, not a shrug.
phase('Test')

const RESULT_SCHEMA = {
  type: 'object',
  required: ['test_id', 'verdict', 'findings'],
  properties: {
    test_id: { type: 'string' },
    verdict: { type: 'string', enum: ['pass', 'fail', 'insufficient', 'untestable'] },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['statement', 'value', 'period', 'source'],
        properties: {
          statement: { type: 'string' }, value: { type: 'string' },
          period: { type: 'string' }, source: { type: 'string' },
          caveat: { type: 'string' },
        },
      },
    },
    reasoning: { type: 'string', description: 'How the findings compare to the pass threshold' },
    searched_beyond_plan: { type: 'boolean' },
  },
}

const confOf = id => { const c = allConditions.find(x => x.id === id); return c ? c.confidence : 0.5 }
const costRank = { cheap: 0, moderate: 1, expensive: 2 }
// Lazy-man order: least-believed condition first; among equals, cheap first.
allTests.sort((a, b) => (confOf(a.condition_id) - confOf(b.condition_id)) || (costRank[a.cost || 'moderate'] - costRank[b.cost || 'moderate']))

const deadOptions = {}          // option_id -> cause of death
const conditionVerdicts = {}    // condition_id -> verdict
const testResults = []
let pending = allTests.filter(t => !(t.data_plan || []).some(p => String(p).startsWith('UNTESTABLE')))
const untestable = allTests.filter(t => (t.data_plan || []).some(p => String(p).startsWith('UNTESTABLE')))
untestable.forEach(t => { conditionVerdicts[t.condition_id] = 'untestable' })

for (let round = 1; round <= MAX_ROUNDS && pending.length; round++) {
  // Skip tests whose option is already dead — no spend on corpses.
  pending = pending.filter(t => {
    const cond = allConditions.find(c => c.id === t.condition_id)
    return cond && !deadOptions[cond.option_id]
  })
  if (!pending.length) break
  const batch = pending.slice(0, MAX_TESTS_PER_ROUND)
  const isRetry = round > 1
  log(`Test round ${round}: ${batch.length} tests${isRetry ? ' (expanded search)' : ''}`)

  const results = (await parallel(batch.map(t => () =>
    agent(`${CONTEXT}

Execute this test FOR REAL and report only what the output actually says.

  Test: ${t.id} (condition: ${t.condition_id}, debate: ${t.debate_id})
  Metric: ${t.metric}
  Pass threshold: ${t.pass_threshold}
  Why this bar: ${t.standard_rationale}
  Data plan: ${JSON.stringify(t.data_plan)}
${isRetry ? `
This is an EXPANDED-SEARCH round: the primary plan returned insufficient
evidence. Go beyond it — alternative tw-data cuts, external-sources.md
retrievals, web search including analog markets (JP/KR/HK/SG) where a Taiwan
number does not exist and an analog bounds it. Label analog evidence as analog.` : ''}

Verdict rules:
- pass / fail: the findings clear or miss the stated threshold. Say how.
- insufficient: you genuinely could not obtain adjudicating evidence. This is
  honest and triggers a wider search next round — but exhaust the plan first.
- A failed fetch is reported as a failure, never backfilled from memory.
${RUN_DIR ? `
Persist the audit trail: after reporting, Write ${RUN_DIR}/evidence/${t.id}.md
with the exact commands run, fetch timestamp, source URLs, and raw output.` : ''}`,
      { label: `test:${t.id}`, phase: 'Test', schema: RESULT_SCHEMA })
  ))).filter(Boolean)

  for (const r of results) {
    testResults.push(r)
    const t = allTests.find(x => x.id === r.test_id)
    if (!t) continue
    if (r.verdict === 'insufficient') continue // stays pending for next round
    conditionVerdicts[t.condition_id] = r.verdict
    pending = pending.filter(p => p.id !== t.id)
    if (r.verdict === 'fail') {
      const cond = allConditions.find(c => c.id === t.condition_id)
      if (cond && cond.must_have && !deadOptions[cond.option_id]) {
        deadOptions[cond.option_id] = `must-have condition "${cond.statement}" failed test ${t.id}: ${r.reasoning || ''}`
        log(`Option ${cond.option_id} KILLED by ${t.id}`)
      }
    }
  }
  // Drop tests that only had insufficient verdicts from the batch back into
  // pending order (they are already there); loop continues with expansion.
}

const alive = options.filter(o => !deadOptions[o.id])
log(`${alive.length}/${options.length} options alive after testing; ${testResults.length} test executions`)

// ── Model + Competitors (parallel) ───────────────────────────────────────────
phase('Model')

const MODEL_SCHEMA = {
  type: 'object',
  required: ['boundary', 'drivers', 'range'],
  properties: {
    boundary: { type: 'string', description: 'Explicit market definition: what is in, what is out, and why' },
    segments: { type: 'array', items: { type: 'string' } },
    drivers: {
      type: 'array',
      description: '3-5 drivers that parameterize the range',
      items: {
        type: 'object',
        required: ['name', 'basis', 'low', 'high'],
        properties: {
          name: { type: 'string' }, basis: { type: 'string', description: 'Where the low/high values come from — a Taiwan series or a named analog market curve' },
          low: { type: 'string' }, high: { type: 'string' },
          analog_used: { type: 'string', description: 'If parameterized by analog: which market, which period, why it is the right analog' },
        },
      },
    },
    range: {
      type: 'object', required: ['low', 'high', 'unit'],
      properties: { low: { type: 'string' }, high: { type: 'string' }, unit: { type: 'string' }, horizon: { type: 'string' } },
    },
    sensitivity: { type: 'string', description: 'The two most contested drivers and how the range moves as each swings — a 2-way table in text form' },
    reconciliation: { type: 'string', description: 'Top-down vs bottom-up: do independent builds land in the same range? Divergence is a finding.' },
    what_model_cannot_see: { type: 'array', items: { type: 'string' } },
  },
}

const COMP_SCHEMA = {
  type: 'object',
  required: ['dimensions', 'players'],
  properties: {
    dimensions: { type: 'array', items: { type: 'string' }, description: 'The bespoke decomposition built for THIS question (not a stock framework), applied to every player symmetrically' },
    players: {
      type: 'array',
      description: 'Up to 6 named competitors/incumbents, measured on the same dimensions',
      items: {
        type: 'object',
        required: ['name', 'archetype', 'binding_constraint'],
        properties: {
          name: { type: 'string' },
          type: { type: 'string', description: 'incumbent / adjacent / platform / potential entrant' },
          metrics: { type: 'string', description: 'The dimension readings, with period + source per number' },
          archetype: { type: 'string', description: 'Named strategic archetype, e.g. "knowledge-membership pivot", "aggregator gatekeeper"' },
          binding_constraint: { type: 'string', description: 'The open question that decides this player\'s trajectory' },
        },
      },
    },
    share_dynamics: { type: 'string', description: 'Who is gaining/losing, over what period, per what source' },
    blind_spots: { type: 'array', items: { type: 'string' }, description: 'What the data cannot see here (SME invisibility, private financials...)' },
  },
}

const [model, competitors] = await parallel([
  () => agent(`${CONTEXT}

Build the MARKET MODEL for the surviving options:

${JSON.stringify(alive.map(o => ({ id: o.id, name: o.name, where_to_play: o.where_to_play })), null, 2)}

Evidence already gathered (reuse; do not re-pull what is here):
${JSON.stringify(testResults.flatMap(r => r.findings || []).slice(0, 40), null, 2)}

MGI discipline, in order:
1. BOUNDARY first: define exactly what market is being sized — what's in,
   what's out, why. A boundary the data cannot honor gets narrowed, and the
   narrowing is stated.
2. SEGMENTS chosen by the hypothesis, not inherited from a stats bureau.
3. DRIVERS: 3-5. Each low/high value must name its basis — a real Taiwan
   series (pull it), or where Taiwan has no number, a NAMED ANALOG market
   curve (JP/KR/HK/SG — see external-sources.md analog section; fetch, do not
   recall). "Analog" means: this market reached X% at maturity / lagged the
   leader by N years — state why it is the right analog.
4. RANGE, two-ended, from the driver lows/highs. No single-point estimates.
5. SENSITIVITY: the two most contested drivers; how the range moves as each
   swings across its low-high. Present as a small 2-way table in text.
6. RECONCILE top-down (macro ratios, industry tax base) against bottom-up
   (per-household / per-subscriber build). If they diverge, the divergence is
   a finding to report, not to average away.
State plainly what the model cannot see.`,
    { label: 'model', phase: 'Model', schema: MODEL_SCHEMA }),

  () => agent(`${CONTEXT}

Build the COMPETITOR analysis for this case. Surviving options:
${JSON.stringify(alive.map(o => ({ id: o.id, name: o.name })), null, 2)}

BCG discipline:
1. Build ONE bespoke decomposition for this question — the 4-6 dimensions on
   which competition in this specific market actually turns (not Porter boxes
   filled ritually). Then apply it to EVERY player symmetrically.
2. Name up to 6 real players (incumbents, adjacent entrants, platform
   gatekeepers). Pull real numbers where they exist: twse_revenue.py --company
   for listed ones, mof_industry.py for industry aggregates, WebSearch for the
   rest. Every metric carries period + source.
3. Give each player a strategic ARCHETYPE (a named pattern of how they compete)
   and a BINDING CONSTRAINT (the open question that decides their trajectory).
   Uncertainty is stated, not hidden.
4. Share dynamics: who is gaining/losing over 3-5 years, per what source. If
   share data cannot exist here (SME invisibility), say so explicitly.
List the blind spots — what this comp analysis structurally cannot see.`,
    { label: 'competitors', phase: 'Competitors', schema: COMP_SCHEMA }),
])

// ── Choose ───────────────────────────────────────────────────────────────────
phase('Choose')

const CHOICE_SCHEMA = {
  type: 'object',
  required: ['chosen_option', 'rationale', 'what_you_need_to_believe', 'scenarios', 'signposts'],
  properties: {
    chosen_option: { type: 'string', description: 'Option id, or "undecidable" if every option died or key debates remain untestable' },
    rationale: { type: 'string', description: 'Anticlimactic: fewest / least serious unresolved barriers. Not a sales pitch.' },
    unresolved_barriers: { type: 'array', items: { type: 'string' } },
    what_you_need_to_believe: {
      type: 'array', items: { type: 'string' },
      description: 'The chosen option\'s conditions that remain assumptions — published so the reader can calibrate their own view',
    },
    scenarios: {
      type: 'object', required: ['bull', 'base', 'bear'],
      properties: {
        bull: { type: 'string', description: 'The key debates resolve the bulls\' way — what the outcome looks like, driver values named' },
        base: { type: 'string' },
        bear: { type: 'string', description: 'The debates resolve the bears\' way. Not "everything goes wrong" — the specific downside thesis' },
      },
    },
    signposts: {
      type: 'array',
      description: 'The monitoring plan: observable indicators with thresholds, each naming which scenario/option it moves you toward',
      items: {
        type: 'object', required: ['indicator', 'threshold', 'moves_toward'],
        properties: { indicator: { type: 'string' }, threshold: { type: 'string' }, moves_toward: { type: 'string' } },
      },
    },
    cheapest_decisive_action: { type: 'string', description: 'If undecidable or thin: the single cheapest action that would resolve the biggest unresolved barrier (a pretest, one named report, one negotiation)' },
  },
}

const choice = await agent(`${CONTEXT}

Make the choice. Everything on the table:

OPTIONS (alive): ${JSON.stringify(alive, null, 2)}
OPTIONS (killed, with cause of death): ${JSON.stringify(Object.entries(deadOptions).map(([id, cause]) => ({ id, cause })), null, 2)}
CONDITIONS + verdicts: ${JSON.stringify(allConditions.map(c => ({ ...c, verdict: conditionVerdicts[c.id] || 'untested' })), null, 2)}
KEY DEBATES: ${JSON.stringify(debates, null, 2)}
TEST RESULTS: ${JSON.stringify(testResults, null, 2)}
MARKET MODEL: ${JSON.stringify(model, null, 2)}
COMPETITORS: ${JSON.stringify(competitors, null, 2)}

Rules:
- The choice is anticlimactic by design: the option with the fewest / least
  serious unresolved barriers wins. If every option died, or the deciding
  debates are untestable with obtainable data, the honest answer is
  "undecidable" plus the cheapest decisive action — that IS a recommendation.
- Absence of evidence is never evidence of no. Untested/untestable conditions
  go into what_you_need_to_believe, not into a verdict.
- Scenarios: bull/base/bear are the KEY DEBATES resolving each way, with the
  model's driver values named. One cause per assumption delta — no stacking
  unrelated luck.
- Signposts must be observable within a realistic horizon, each with a
  threshold and which way it moves the decision — the case must be useful
  beyond day one.`,
  { label: 'choose', phase: 'Choose', schema: CHOICE_SCHEMA })

const critique = await agent(`${CONTEXT}

You are the completeness critic. The case so far:

CHOICE: ${JSON.stringify(choice, null, 2)}
OPTIONS: ${JSON.stringify({ alive: alive.map(o => o.id), dead: Object.keys(deadOptions) })}
DEBATES: ${JSON.stringify(debates.map(d => d.question))}
MODEL RANGE: ${JSON.stringify(model && model.range)}
COMPETITORS: ${JSON.stringify(competitors && competitors.players ? competitors.players.map(p => p.name) : [])}

Attack what is MISSING or WRONG, prioritised. Specifically check:
- a real-world fact that reframes the case (a WebSearch you should run now);
- a claim quietly upgraded beyond its evidence (intent reported as achievement);
- an in-plugin read that would bound an asserted-but-unsized premise;
- an internal tension between the choice and the evidence (e.g. recommending
  the one model with a recorded local death while calling the death unreadable);
- a cost/upside comparison asserted but never bounded;
- a load-bearing number with no source.
If something is genuinely fine, say nothing about it. Short, prioritised list.`,
  { label: 'critic', phase: 'Choose' })

// ── Report ───────────────────────────────────────────────────────────────────
phase('Report')
let reportPath = null
if (RUN_DIR) {
  reportPath = `${RUN_DIR}/report.html`
  await agent(`${CONTEXT}

Build the deliverable: ONE self-contained HTML report at ${reportPath} (use the
Write tool). 正體中文. No external resources — no CDN, no webfonts, no <img>;
system font stack and inline SVG only, so the file opens offline forever.

Raw material:
- The decision: ${frame.decision}
- Choice: ${JSON.stringify(choice)}
- Options alive: ${JSON.stringify(alive)}
- Options killed (cause of death): ${JSON.stringify(Object.entries(deadOptions).map(([id, cause]) => ({ id, cause })))}
- Options excluded at framing: ${JSON.stringify(frame.excluded_options || [])}
- Key debates: ${JSON.stringify(debates)}
- Conditions + verdicts: ${JSON.stringify(allConditions.map(c => ({ ...c, verdict: conditionVerdicts[c.id] || 'untested' })))}
- Test results (with findings): ${JSON.stringify(testResults)}
- Market model: ${JSON.stringify(model)}
- Competitor analysis: ${JSON.stringify(competitors)}
- Critic's findings — fix what is fixable; what you cannot fix goes verbatim
  into a「已知限制」box. Hiding any of it is falsification:\n${critique}

Structure (Pyramid Principle — the answer first, then the support):
1. 行動摘要 first screen: the chosen option (or undecidable + cheapest decisive
   action) as one large-type sentence; 3-4 stat tiles; bull/base/base scenario
   strip; badge row (options alive/killed, debates, tests run, untestable count).
2. 選項地圖: every option framed — the happy story, its conditions with
   verdicts (pass/fail/untested/untestable color-coded), killed options shown
   WITH their cause of death. The rejected-alternatives exhibit is a
   credibility engine, give it space.
3. 關鍵辯論紀錄: per debate — the question, bull at full strength, bear at
   full strength, the skeptic's test (metric + threshold + why that bar), the
   verdict with the actual numbers. This is the dialectic record.
4. 市場模型: boundary, driver table (each with basis/analog), the two-ended
   range as a chart, sensitivity table, top-down vs bottom-up reconciliation.
5. 競爭者分析: the bespoke dimensions, symmetric player table, archetype +
   binding constraint per player, share dynamics, blind spots.
6. What you need to believe: the chosen option's surviving assumptions,
   published so the reader can calibrate their own view.
7. Signposts 監測計畫: indicator / threshold / which way it moves the decision.
8. 方法論與證據附錄: one row per test — command, timestamp, source, key raw
   output inlined (wrap long output in <details>). No file: links — evidence
   travels inside this file. Close with: 所有來源免費、免金鑰、公開，重跑指令
   即是驗證.

Every section heading is an ACTION TITLE (a complete sentence stating the
point); the titles alone, read in order, must reconstruct the argument. Every
number carries 期間 and 來源 as text. Charts: inline SVG, line for series,
horizontal bars for rankings; one accent color (#2563eb), red (#dc2626) only
for negative/refuted; every datapoint gets an SVG <title>; mark data gaps
visibly. <meta charset="utf-8">, responsive max-width ~960px, @media print
rules, footer with generation date, plugin version, run directory.

Your final message: confirm the file was written and list any critic points
you could not fix.`,
    { label: 'report', phase: 'Report' })
} else {
  log('No runDir supplied — skipping evidence pack and HTML report; results return inline only')
}

return {
  report: reportPath,
  decision: frame.decision,
  options: { framed: options, excluded: frame.excluded_options || [], killed: Object.entries(deadOptions).map(([id, cause]) => ({ id, cause })), alive: alive.map(o => o.id) },
  debates,
  conditions: allConditions.map(c => ({ ...c, verdict: conditionVerdicts[c.id] || 'untested' })),
  test_results: testResults,
  model,
  competitors,
  choice,
  critique,
}
