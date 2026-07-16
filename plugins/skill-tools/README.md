# skill-tools

三個查詢／管理 skill 的指令，幫你搞清楚「手上有哪些 skill、來自哪一層、該補什麼」。
全部**唯讀**、**不寫入記憶**、以**繁體中文**輸出。

安裝後指令帶命名空間前綴 `skill-tools:`。

---

## `/skill-tools:skill-list` — 列出所有可用 skill

**做什麼**：把目前 session 能用的所有 skill 列成清單，每個附**一句中文用途**。

**輸出方式**：要點式、精簡，依來源分區塊——
- 使用者層級（個人裝的）
- 專案層級（`.claude/skills/`）
- Plugin 內建（依類別分組，大組只給總述＋數量）

結尾給各層總數。跨專案格式一致。

**何時用**：想快速盤點「我到底有哪些 skill」、或幫別人介紹環境時。

**範例輸出（節錄）**：
```
## 使用者層級
- **docx** — 建立／編輯 Word 文件
- **browser-use** — 用瀏覽器爬資料／自動化

## Plugin 內建
- 工程（engineering）— 10 個：架構、審查、除錯、測試策略…
...
總計：使用者層級 5、專案 0、Plugin 約 130+
```

---

## `/skill-tools:skill-status` — skill 啟用來源與範圍

**做什麼**：回報每個 skill 是在**哪一層**啟用的，分三塊：
1. 系統／使用者層級（`~/.claude/skills/`，跨所有專案）
2. 本專案層級（`.claude/skills/`，僅此專案）
3. Plugin 內建（依 plugin/marketplace 分組）

**特別處理**：同名 skill 出現在多層時會**標記衝突**並說明誰優先（一般專案覆蓋使用者）。

**何時用**：搞不清「這個 `/foo` 是哪來的」、或懷疑有重複／衝突時。

---

## `/skill-tools:skill-RCM` — 依專案脈絡建議該裝的 skill

**做什麼**：讀這個專案的實際脈絡，建議值得安裝的 skill：
- 開發記憶（`~/.claude/projects/<slug>/memory/`）
- `CLAUDE.md`、`.claude/rules/`
- 產品／需求文件（README、docs/、PRD、spec…）
- 技術棧（package.json、pyproject.toml、go.mod…）

比對已裝的 skill 避免重複，再依**高／中／低優先級**列出建議，每則附**理由**與**安裝方式**。

**何時用**：進到一個新專案、想知道「這個案子該補哪些工具」。

**界線**：只建議，**不會**未經你同意就安裝；也**不會**把建議寫進記憶。

---

## 設計備註
- 三個指令的 frontmatter 都綁**明確觸發**，平常不會自動啟動、不佔 context。
- 全部**只讀不寫記憶**，避免專案記憶累積 skill 管理相關的雜訊。
