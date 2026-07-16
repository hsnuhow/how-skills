---
name: skill-RCM
description: >
  Recommend skills worth installing for THIS project, grounded in its
  development memory, CLAUDE.md, product/requirement docs, and codebase.
  One-shot recommendation report in Traditional Chinese. RCM = recommend.
  Trigger ONLY on /skill-RCM or an explicit request for skill recommendations.
  Do NOT auto-activate, and do NOT install anything without confirmation.
argument-hint: ""
---

# skill-RCM — 依專案脈絡建議可安裝的 skill

被呼叫時，根據這個專案的**實際脈絡**推薦值得裝的 skill。推薦要有憑有據，扣著讀到的證據，不憑空亂建議。

## 步驟
1. **蒐集專案脈絡**（存在才讀，沒有就略過）：
   - 開發記憶：`~/.claude/projects/<專案 slug>/memory/MEMORY.md` 及其 topic 檔。
     （slug 是把工作目錄路徑的 `/` 換成 `-`；找不到就 glob `~/.claude/projects/*/memory/` 對照目前 cwd。）
   - `CLAUDE.md`、`.claude/CLAUDE.md`、`.claude/rules/`。
   - 產品／需求文件：`README*`、`docs/`、`PRD*`、`spec*`、描述產品的 `*.md`。
   - 技術棧：`package.json`、`pyproject.toml`、`go.mod`、`Cargo.toml` 等，判斷語言／框架。
2. **比對已裝的 skill**（用 skill-status 的邏輯掃 `~/.claude/skills` 與 `.claude/skills`），避免推薦已經有的。
3. **候選來源**：本 session available-skills 清單、已知的 Anthropic 官方 skill、plugin marketplace skill。

## 輸出（列表式、繁體中文，依優先級分組）
每則推薦：
- **skill 名稱** — 這個專案為什麼需要它（一句，扣著剛讀到的證據，如「因為 memory 提到要處理 PDF」「因為 repo 用 Python」）。
- 安裝方式：使用者層級複製 ／ `/plugin install` ／ 其實已可用。
- 優先級：**高／中／低**。

分「高／中／低」三組呈現。結尾加一句：「以上為建議，要我幫你裝哪個再說。」

## 界線
- 只推薦，不安裝。要動手安裝一定先取得使用者明確同意。
- **不得把推薦內容或 skill 管理相關資訊寫入記憶**（專案或使用者層級），避免污染專案記憶。可讀取記憶作為判斷依據，但不回寫。
