# how-skills — 個人 Claude Code plugin marketplace

一個 **單一 repo** 的 [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)，
把我常用的 skill 收成可安裝的 plugin，讓它們在**任何一台電腦**上都能用（跨機、可版本控管、可更新）。

- 一個 marketplace：`how-skills`
- 三個 plugin：[`skill-tools`](plugins/skill-tools/README.md)、[`ponytail`](plugins/ponytail/README.md)、[`media-tools`](plugins/media-tools/README.md)

---

## 目錄
- [這是什麼 / 為什麼要 plugin](#這是什麼--為什麼要-plugin)
- [安裝](#安裝)
- [Plugin 一覽與用法](#plugin-一覽與用法)
- [維護流程](#維護流程)
- [Repo 結構](#repo-結構)
- [設計原則](#設計原則)
- [授權與致謝](#授權與致謝)

---

## 這是什麼 / 為什麼要 plugin

Claude Code 的個人 skill 放在 `~/.claude/skills/`，但那是**本機**的、不會跟帳號同步。
要在多台電腦共用，官方做法就是包成 **plugin** 放進一個 git-hosted **marketplace**，
每台機器 `add` 一次、`install` 想要的 plugin 即可，日後更新只要 `git push` + `marketplace update`。

> **命名空間**：裝成 plugin 後，指令會加上 plugin 名前綴。
> 例如 `skill-list` → `/skill-tools:skill-list`、`ponytail-review` → `/ponytail:ponytail-review`。

---

## 安裝

在**每一台**要使用的電腦上：

```shell
# 1) 加入這個 marketplace（一次即可）
/plugin marketplace add hsnuhow/how-skills

# 2) 安裝想要的 plugin
/plugin install skill-tools@how-skills
/plugin install ponytail@how-skills
/plugin install media-tools@how-skills
```

安裝後**開一個新的 session** 指令才會載入。

驗證是否裝好：
```shell
/plugin                 # 互動式查看已裝 plugin
claude plugin list      # CLI 列出
```

---

## Plugin 一覽與用法

### 🧰 skill-tools — skill 管理指令
> 詳見 [plugins/skill-tools/README.md](plugins/skill-tools/README.md)

| 指令 | 用途 | 範例 |
|---|---|---|
| `/skill-tools:skill-list` | 列出所有可用 skill，附**中文用途**（要點式、跨專案格式一致） | 想快速看「我有哪些 skill」 |
| `/skill-tools:skill-status` | 分清 skill 來自**系統／專案／plugin** 哪一層，並標記同名衝突 | 想知道某個 skill 是哪來的 |
| `/skill-tools:skill-RCM` | 依**專案記憶＋CLAUDE.md＋產品文件＋技術棧**，建議該裝哪些 skill | 進到新專案想知道「該補什麼工具」 |

三者皆**唯讀**、**絕不寫入記憶**。

### 🐴 ponytail — 精簡優先 / 反過度設計（commands-only）
> 詳見 [plugins/ponytail/README.md](plugins/ponytail/README.md)

| 指令 | 用途 |
|---|---|
| `/ponytail:ponytail [lite\|full\|ultra]` | 開啟「懶惰資深工程師」精簡模式（**明確呼叫才啟動**） |
| `/ponytail:ponytail-review` | 針對 diff 只審過度設計、列出可刪項 |
| `/ponytail:ponytail-audit` | 掃整個 repo 的過度設計 |
| `/ponytail:ponytail-debt` | 收集程式碼中的 `ponytail:` 註解成技術債清單 |
| `/ponytail:ponytail-gain` | 顯示 ponytail 的效益計分板 |
| `/ponytail:ponytail-help` | 指令與模式速查 |

本 build **不含任何 hooks**，預設**完全不自動啟動**（見[設計原則](#設計原則)）。

### 🎬 media-tools — 媒體檔案處理
> 詳見 [plugins/media-tools/README.md](plugins/media-tools/README.md)

| 指令 | 用途 |
|---|---|
| `/media-tools:video-to-gif` | 影片（或指定時間區段）轉動畫 GIF（ffmpeg） |
| `/media-tools:pptx-to-pdf` | 簡報轉高保真 PDF、字型內嵌（LibreOffice） |
| `/media-tools:compress-pdf` | 壓縮 PDF 到可 email 的大小（Ghostscript） |

⚠️ 需先在該機安裝系統工具：**ffmpeg**、**ghostscript**、**libreoffice**。

---

## 維護流程

改 skill 就三步：

```shell
# 1) 編輯 SKILL.md
$EDITOR plugins/skill-tools/skills/skill-list/SKILL.md

# 2) 提交並推上 GitHub
git add -A && git commit -m "改了什麼" && git push

# 3) 各機器更新
/plugin marketplace update how-skills
```

**版本控制**：`plugin.json` 有寫 `version` 時，使用者只有在你**改版號**後才會收到更新；
若拿掉 `version`，git 每個 commit 都算新版本。本 repo 目前有寫 `version`，發佈新版記得 bump。

**開發機小抄**：這台開發機的 marketplace 直接指向本機這個 repo 資料夾，
所以 `marketplace update` 會抓到你剛編輯的內容，不必先 push 也能本機測。
（其他電腦則是從 GitHub 抓。）

---

## Repo 結構

```
how-skills/
├── .claude-plugin/
│   └── marketplace.json                # marketplace 目錄，列出兩個 plugin
├── plugins/
│   ├── skill-tools/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── README.md
│   │   └── skills/
│   │       ├── skill-list/SKILL.md
│   │       ├── skill-status/SKILL.md
│   │       └── skill-RCM/SKILL.md
│   └── ponytail/
│       ├── .claude-plugin/plugin.json
│       ├── README.md
│       ├── NOTICE.md                    # 對上游 ponytail 的致謝與改動說明
│       └── skills/
│           ├── ponytail/SKILL.md
│           ├── ponytail-audit/SKILL.md
│           ├── ponytail-debt/SKILL.md
│           ├── ponytail-gain/SKILL.md
│           ├── ponytail-help/SKILL.md
│           └── ponytail-review/SKILL.md
├── README.md
└── LICENSE
```

**格式要點**（照 Claude Code plugin 規範）：
- `marketplace.json` 頂層需要 `name`、`owner`、`plugins[]`；每個 plugin 用 `source: "./plugins/<名稱>"`（相對路徑，必須 `./` 開頭，相對 repo 根）。
- `plugin.json` 只有 `name` 必填。
- 一個 plugin 的 skill 放在該 plugin 的 `skills/<名稱>/SKILL.md`。
- 驗證：`claude plugin validate ./plugins/<名稱> --strict`。

---

## 設計原則

1. **不自動啟動**：skill-tools 三個指令綁明確觸發、`ponytail` 主 skill 改成 explicit-invoke，
   且 ponytail **不帶 hooks**——平常都不會自動上身，只有你叫它才動。
2. **不污染記憶**：skill-tools 系列**只讀不寫**記憶，避免在專案記憶累積無關雜訊。
3. **要點式輸出**：`skill-list` 固定精簡、跨專案一致。

---

## 授權與致謝

- 本 repo 以 **MIT** 授權（見 [LICENSE](LICENSE)）。
- `plugins/ponytail` 衍生自 [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)（MIT）。
  本 build 移除其全部 hooks 並將主 skill 改為 explicit-invoke；
  詳細改動與致謝見 [plugins/ponytail/NOTICE.md](plugins/ponytail/NOTICE.md)。
