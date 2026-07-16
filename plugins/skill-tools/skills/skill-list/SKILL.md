---
name: skill-list
description: >
  List every skill currently available in this session, each with a concise
  Traditional Chinese explanation of its purpose, in list format. One-shot
  display, read-only. Trigger ONLY when the user invokes /skill-list or
  explicitly says "列出 skill" / "有哪些 skill". Do NOT auto-activate on other
  tasks.
argument-hint: ""
---

# skill-list — 列出所有可用 skill（中文說明）

被呼叫時，產出一份**列表式**的 skill 清單，每個 skill 附**一句繁體中文**用途說明。

## 收集來源（合併去重，以 name 為鍵）
1. 本 session 的 available-skills 內容（system-reminder 中列出的 skill）——這是最權威的即時清單。
2. 使用者層級：`~/.claude/skills/*/SKILL.md`
3. 專案層級：相對於目前工作目錄的 `.claude/skills/*/SKILL.md`（若存在）

可用 `ls ~/.claude/skills` 與 `ls .claude/skills` 輔助，並讀各 SKILL.md 的 frontmatter `description` 來寫中文摘要。

## 輸出格式（要點式、精簡；跨所有專案格式一致）
- 全程用**要點（bullet）**呈現，力求精簡；每個 skill **一行、不超過一句**。
- 依來源分區塊：**使用者層級（個人裝的）**、**專案層級**、**Plugin 內建**。
- 每行一個：`- **skill 名稱** — 中文用途（一句話）`
- 中文說明濃縮成一句，講「它幫你做什麼」，不要照抄英文、不要展開細節。
- Plugin 內建通常很多（數十個），請**依類別分組**：每組**一行總述 + 一個數量**即可，不要逐項展開（除非使用者指定「展開某組」）。
- 結尾給**總數**（使用者層級 X 個、專案 Y 個、Plugin 約 Z 個）。
- 不論在哪個專案，都維持同一套要點式格式。

## 界線
- 只顯示，不安裝、不啟用、不修改任何東西。
- **不得寫入任何記憶**（專案或使用者層級）。此指令純顯示、不留痕跡。
