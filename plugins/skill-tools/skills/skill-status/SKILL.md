---
name: skill-status
description: >
  Show which skills are enabled at the SYSTEM/user level versus the current
  PROJECT level (and which come from plugins), so the user can see the scope
  and source of each skill. One-shot read-only report. Trigger ONLY on
  /skill-status or an explicit request. Do NOT auto-activate on other tasks.
argument-hint: ""
---

# skill-status — 專案已啟用 vs 系統已啟用的 skill

被呼叫時，回報 skill 的**啟用範圍與來源**，分成三塊。

## 1. 系統／使用者層級（跨所有專案生效）
列出 `~/.claude/skills/` 底下每個子資料夾——每個都是所有專案都吃得到的個人 skill。
用 `ls ~/.claude/skills` 取得。

## 2. 本專案層級（僅此專案生效）
列出目前工作目錄下 `.claude/skills/` 的子資料夾（若資料夾不存在就註明「本專案未設定專案層級 skill」）。

## 3. Plugin 內建（由已安裝 plugin 提供）
根據本 session 的 available-skills 內容，列出目前載入的 plugin skill，依 plugin／marketplace 分組（如 anthropic-skills、engineering、productivity、zoom-plugin…）。

## 輸出
- 用表格或清楚分段呈現。
- 每個 skill：名稱 ＋ 範圍（系統／專案／plugin）＋ 一句中文用途。
- 若同名 skill 同時存在於多個範圍，**標記衝突**並說明誰優先（一般專案層級覆蓋使用者層級）。
- 結尾給每個範圍的小計。

## 界線
- 唯讀。不啟用、不停用、不修改任何 skill。
- **不得寫入任何記憶**（專案或使用者層級）。此指令純顯示、不留痕跡。
