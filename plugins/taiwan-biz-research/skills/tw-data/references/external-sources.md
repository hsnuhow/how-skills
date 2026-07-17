# External sources — verified, not API-able

Numbers a business case needs that live outside open data: advertising market
size, willingness to pay, industry survey output. Everything below was fetched
for real on **2026-07-17**; the snapshot numbers WILL go stale — re-fetch by the
documented method before citing, and update this file when you do.

## 台灣數位廣告市場量 — DMA (annual, first-hand PDF)

- Report page: https://www.dma.org.tw/newsPost/2559 (2024 full-year, published
  2025-08). Yearly list: https://www.dma.org.tw/trend?search=台灣數位廣告量
- PDF via Google Drive — convert the share link to
  `https://drive.google.com/uc?export=download&id=<FILE_ID>` and curl it.
  **No email wall, no registration.**
- **Pitfall: pages 8-16 (the core figures) are bitmap images** — pdftotext gets
  nothing. Render with `gs -sDEVICE=png16m -r110` and read visually.
- Method caveat: DMA member survey + GfK estimation, not monitoring — do not
  add to Nielsen-monitored numbers.

Snapshot (2024, NT$億): total digital **636.83** (+4.32%); 一般媒體平台 396.04
(62.2%) vs 社群 240.79 (37.8%). Within 一般媒體: 關鍵字 40.6% (≈Google), 串流影音
36.1% (≈YouTube), 展示型 ~42.4億, 內容置入 ~48.7億 (置入 -1.95%, 網紅 -0.38% —
both below the +4.32% market). Ten-year series: 2015 193.52 → 2020 482.56 →
2024 636.83. Non-digital (Nielsen AIS via this report): 2024 253.49億, shrinking.

**Analyst inference, NOT a DMA statistic** (label it as such when citing): the
"pool local publishers can compete for" ≈ display + 置入 ≈ 91億 ≈ 14% rests on
attribution DMA's format×platform grid cannot verify — it assumes keyword goes
wholly to Google, streaming to YouTube, and display to publishers, when in fact
Yahoo/LINE take display too (overstating the pool) and publishers do earn video
and social placements (understating it). Use it as an order-of-magnitude
boundary, never as a measured share.

Rainmaker/潤利 (xkm.com.tw): monthly 有效廣告量 reports free, but free tier =
top-100 advertiser rankings in traditional media only; market totals are
paywalled. 「有效廣告量」is rate-card × discount estimation — yet another
incompatible 口徑.

## 線上新聞付費率 — Reuters Institute DNR (annual)

- URL pattern: `https://reutersinstitute.politics.ox.ac.uk/digital-news-report/{year}/taiwan`
  (2021-2026 live; 2017-2020 only via Wayback CDX — the old digitalnewsreport.org
  redirects to the RISJ homepage, so `/2020/taiwan` 404s).
- **Pitfall: chart series are Datawrapper iframes** — page text only carries the
  headline stats. Pull `https://datawrapper.dwcdn.net/{chartID}/{version}/dataset.csv`
  (chart ID + version from the iframe src; **no version → 404**).
- Method: YouGov online panel (2026: n=2,030, fieldwork Jan-Feb), weighted;
  under-represents old/low-income; read as "online population". Δ≤2pp not
  significant.

Snapshot — paid for online news in the last year (台灣): 2017 15%, 2018 **18%**
(peak), then 12-15% flatline for eight years, **2026 10% (-4pp, series low)**.
Global average 17%, Norway 40%. Also 2026: digital news trust 25% (global 37%);
top online gateway is Yahoo! News 45% weekly reach (aggregator-first market —
structural headwind for direct-subscription); brand trust led by 商業週刊/天下
(55%) — knowledge-brand membership models have the trust base pure news lacks.

Complementary (headline-level, verify before citing): TAICCA 文化內容消費趨勢調查
(research.taicca.tw/static/trend_consumer) — content-payment framing, 出版整體
讀者付費率 >60%: "paying for content" and "paying for news" are different
questions in Taiwan, ~6x apart. TWNIC 台灣網路報告 (report.twnic.tw) — 付費影音
/音樂串流訂閱 26.8% (2024). 臺灣傳播調查資料庫 TCS (crctaiwan.dcat.nycu.edu.tw)
— raw survey data via SRDA.

## 出版/雜誌產業產值 — 文化統計 & TAICCA (annual PDFs)

- **The 403 trap: taicca.tw and research.taicca.tw block plain fetches.** Both
  report families download cleanly from the 文化統計 mirror instead:
  `https://stat.moc.gov.tw/Research_Download.aspx?idno={NNNN}` (curl -sL works).
  產調 list: `stat.moc.gov.tw/research.aspx?type=4`; 年報 list: `?type=5`.
- Two incompatible 口徑, never join them:
  - **產調報告** (survey-based, 專營 core operators only): 雜誌業 2023 營業額
    **72.49億** (+0.32%). Old-edition series (2019 75.75 / 2020 83.85 / 2021
    91.54億) was re-based — the 2021-22 restated values are inside chart images,
    text layer doesn't have them.
  - **文創年報** (tax-based, from MOF 稅籍): 出版產業 2023 **1,051億**; 實體雜誌
    及期刊 (5812-11) **156.71億** (+8.6%); 數位雜誌 (5812-12) only **5.25億** —
    firms self-select 實體/數位 when filing, so the digital line wildly
    understates digital revenue.
- Both understate magazines structurally: 營業稅法第8條 exempts magazines'
  own-publication sales and ad revenue (the 年報 says so itself).
- For tax-口徑 numbers, prefer the wrapped `mof_industry.py` (monthly, by
  county, 3-digit classes) over the annual PDF.

## 外銷拓展情報 — TAITRA (human-read, crawlable URLs)

- **各國市場檔案**: `market.meettaiwan.com/taitraesource/AreaCountry/{區域碼}/{國別碼}`
  (e.g. `/04/US`; 區域: 00 亞太 01 中東 02 歐洲 03 非洲 04 美洲 05 中亞; ~190
  countries, enumerable from the homepage). Annual country reports — investment
  climate, market analysis, 拓銷建議, and **local buyer/distributor directories**
  (US page: 29 distributor-association links). **403 to default UAs / WebFetch;
  curl with a full browser User-Agent works.**
- **經貿透視** (trademag.org.tw): field-office market intelligence, free full
  text per article, paginated lists crawlable; the biweekly e-book needs a
  subscriber login — don't cross it.
- **iTrend** (itrend.taitra.org.tw): dashboard over customs data, registration
  wall, no CSV/API — citation material only.
- Exporter digital-marketing survey: only the free PDF《台灣企業跨境關鍵報告 2.0》
  (TAITRA×Google×台經院, **2020 — stale**) at thinkwithgoogle.com; headline-level
  use only. No machine-readable successor exists free (資策會 MIC is paywalled).

These are reports for humans, not data: quote the 拓銷建議 and buyer directories,
pull the numbers from FSC/customs instead (see endpoints.md).

## 前例: WIRED 正體中文版已經存在過，而且死了

Condé Nast-licensed **WIRED.tw**: beta 2011, launched 2012-01-04, positioned as
WIRED's first digital-first licensed edition, founding editor-in-chief 戴季全
(TechOrange founder), succeeded by 程九如 2013. No shutdown announcement exists;
Wayback CDX shows the site alive through 2017-01, HTTP 500 from 2017-03, domain
redirected after — **inferred death: early 2017, ~5 years of life** (mark as
Wayback-inferred, not official). Source: techorange.com/2012/01/03/wired-20120104/.
Any Taiwan digital-media licensing case should reckon with this precedent first.
