# ponytail（commands-only build）

「懶惰的資深工程師」——**精簡優先、反過度設計**。決策階梯：
「這需要存在嗎？(YAGNI) → codebase 裡有了嗎？ → 標準庫能做嗎？ → 平台原生功能？ →
已裝的依賴？ → 一行搞定？ → 否則寫剛好能動的最小量」。

衍生自 [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)（MIT）。
**本 build 移除全部 hooks，主 skill 改為明確呼叫才啟動**——見 [NOTICE.md](NOTICE.md)。

安裝後指令帶命名空間前綴 `ponytail:`。

---

## 指令

### `/ponytail:ponytail [lite|full|ultra]` — 精簡模式
開啟持續性的精簡模式；**明確呼叫才生效**，平常不會自動上身。

- `lite` — 輕度提醒，仍偏精簡
- `full` — 預設強度
- `ultra` — 最激進，能砍就砍

關閉：對話中說「stop ponytail」或「normal mode」。

### `/ponytail:ponytail-review` — 過度設計審查（針對 diff）
只挑「過度設計」：重造標準庫、多餘依賴、臆測性抽象、用不到的彈性。
每個發現一行：位置 → 該砍什麼 → 用什麼取代。一次性報告，不改檔。

### `/ponytail:ponytail-audit` — 全 repo 稽核
同 review，但掃**整個 codebase**，給出可刪／可簡化／可用標準庫取代的**排序清單**。

### `/ponytail:ponytail-debt` — 技術債清單
收集程式碼中的 `ponytail:` 註解（刻意留下的捷徑／延後項），彙整成債務 ledger，
避免「later means never」。一次性報告，不改動任何東西。

### `/ponytail:ponytail-gain` — 效益計分板
以基準中位數顯示 ponytail 的效益（少多少碼／省多少成本／快多少）。
> 註：效益數字為上游專案自稱、未經第三方驗證，僅供參考。

### `/ponytail:ponytail-help` — 速查
所有模式、skill、指令的快速參考卡。

---

## 為什麼是「commands-only」

上游 ponytail 透過 **lifecycle hooks**（SessionStart / SubagentStart / UserPromptSubmit）
在每次 session **自動啟動**、預設 `full` 模式。本 build 刻意：
- **不含任何 hooks** → 不會有背景自動行為
- 主 `ponytail` skill 的觸發描述改為 **explicit-invoke only** → 一般 coding 不會自動套用

結果：**預設完全不啟動，需要時才叫它**。完整改動與致謝見 [NOTICE.md](NOTICE.md)。
