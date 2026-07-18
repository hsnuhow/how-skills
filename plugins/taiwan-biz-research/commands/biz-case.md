---
description: 跑一個完整的台灣商業案例研究：互斥選項 → 條件檢驗 → 關鍵辯論 → 市場模型 → 競爭分析 → 分析師報告
argument-hint: <研究問題，例如「WIRED科技媒體進入台灣的策略研究」>
---

Run a full hypothesis-driven Taiwan business case for this question:

**$ARGUMENTS**

Follow the `biz-case-workflow` skill (read its SKILL.md at
`${CLAUDE_PLUGIN_ROOT}/skills/biz-case-workflow/SKILL.md`) exactly. In
particular:

1. **Sharpen first.** If the question does not name a decision (enter or not,
   invest or not, now or later), ask 1-2 clarifying questions BEFORE launching —
   a vague question produces a vague case at full cost. If no question was
   given at all, ask for one.

2. **Cost gate.** This is the expensive option (~25-45 agents, 2-4M tokens,
   roughly an hour). Confirm with the user before launching unless they have
   already confirmed in this conversation. For a single number, use `tw-data`
   directly instead.

3. **Resolve paths in bash before launching** (the sandbox cannot):
   `TW="${CLAUDE_PLUGIN_ROOT}/skills/tw-data"`, `RUN_DIR="$(pwd)/biz-case-runs/<slug>-$(date +%F)"`,
   `mkdir -p "$RUN_DIR/evidence"` — then launch the Workflow tool with
   `scriptPath: ${CLAUDE_PLUGIN_ROOT}/skills/biz-case-workflow/workflows/biz_case.js`
   and args `{question, twDataPath, runDir}` as a real JSON object, the
   question passed verbatim.

4. **On completion**: check `report_status`; if `failed`, rebuild with
   `build_report.py` (never re-run the workflow for this). Deliver by surface
   per the skill's ladder — desktop: report.html + PDF; phone/remote: Google
   Doc via Drive MCP (charts as tables); claude.ai: Artifact as value-add.

5. **Then enter Q&A mode**: the result JSON + `runDir/evidence/` is the case
   file. Answer follow-ups from it FIRST (labeled 「根據本案已查證的資料」),
   fetch new data only when it cannot answer, and append new evidence as
   `evidence/qa-<slug>.md`.
