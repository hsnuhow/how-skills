# data.gov.tw 資料集索引 — 消費力研究相關機關

`endpoints.md`／`schemas.md` 記的是**已接、已驗證欄位**的來源。這一份記的是
**還有哪些資料集存在**——主計總處、財政部、經濟部、外貿、內政部人口/區域、
教育、勞動的完整枚舉，標注每個對「台灣消費力與消費層級」的相關性。

盤點日期 **2026-07-18**，五個 agent 分機關平行枚舉。**只讀你要用的那一個機關檔。**

| 機關檔 | 涵蓋 | 資料集數 |
|---|---|---|
| [`datasets/01-dgbas.md`](datasets/01-dgbas.md) | 主計總處：家庭收支、CPI、薪資、人力、國民所得 | 1,945 |
| [`datasets/02-mof-trade.md`](datasets/02-mof-trade.md) | 財政部：**綜合所得稅**、營業稅、營所稅、關務貿易 | ~4,100 |
| [`datasets/03-moea.md`](datasets/03-moea.md) | 經濟部：批發零售餐飲營業額、生產、外銷、登記家數 | 2,659 |
| [`datasets/04-moi-population.md`](datasets/04-moi-population.md) | 內政部戶政：人口×年齡×性別×教育，到**村里級** | ODRP001-118 |
| [`datasets/05-education-labour.md`](datasets/05-education-labour.md) | 教育部學校/教育程度、勞動部薪資/投保 | ~360 + 859 |

---

## 枚舉方法（正解，可複用於任何機關）

data.gov.tw 是 Nuxt SPA，沒有公開的「機關→資料集」REST API，但前端搜尋走一支
**可直接重放的內部 API，不需 API key**（只要瀏覽器 UA + `Referer: https://data.gov.tw/`）：

```
POST https://data.gov.tw/api/front/dataset/list
Content-Type: application/json
{"bool":[{"agency_tid":{"value":438}}], "page_num":1, "page_limit":1000, "sort":"_score_desc"}
```

- **依機關窮舉**：`bool:[{"agency_tid":{"value":<子機關tid>}}]` → 該機關全部資料集。
- **關鍵字**：`bool:[{"fulltext":{"value":"綜稅"}}]`（關鍵字**必須**包在 `bool[].fulltext.value`；
  放頂層 `qs`/`keyword` 會被忽略、回整個目錄 5.3 萬筆）。
- **機關樹**：`GET /api/front/agency/listbytid/{部會tid}` 列出子機關 tid。過濾**只吃子機關
  tid，不吃部會層 tid**（給 432 財政部回 0，要先展開成 438/434/436…逐一查）。
- 回傳 `payload.search_result[]`，`nid` == 公開 datasetId；細節與真實下載 URL 用
  `GET /api/v2/rest/dataset/{nid}` 取 `distribution[].resourceDownloadUrl`（同樣需瀏覽器 UA）。

**備援枚舉法**：全站 catalog 自己是 dataset 6564，可整包下載離線過濾——
`https://data.gov.tw/datasets/export/csv`（~68 MB，5.3 萬筆，欄位含「提供機關」）。
慢但完整，適合一次抓下來建全量索引。

**死路（別再試）**：`/api/v2/rest/organization` 404；v2 `?organizationId=` GET 405；
`POST /api/v2/rest/dataset`（v2，非 front）需 Authorization Key；WebFetch 無法 render SPA。

關鍵機關 tid：財政部 432 →（FIA **438**／統計處 434／關務署 436／賦稅署 439）；
經濟部含統計處與商業發展署、國際貿易署 **44688**（掛經濟部非財政部）。

---

## 消費力分層金字塔 — 跨機關最優先清單

研究「台灣消費力與消費層級」的骨幹是「**誰有多少錢（所得層）× 在哪（區域）×
什麼人（年齡/教育）× 花在哪（消費終端）**」。跨五個機關，最該優先接的：

### 1. 所得分層（金字塔頂——決定購買力）
- **財政部 綜合所得稅**（全體申報戶，非抽樣，比家庭收支調查全面）：
  `144517/144518` 所得應納稅額×稅率（各縣市／各級距，加計股利新口徑）、
  `144519-521`（5/10/20 分位）、`144527/144528` 總所得、`8864/8865` **各類所得金額**
  （薪資 vs 股利/租賃——所得結構決定消費傾向）。
  **`103066` 綜所總額到村里級**——全台最細的所得地理分布。
- **DGBAS 6565** 五等分位所得×消費×儲蓄（一表看各層花多少存多少）、`6566` 所得差距倍數。

### 2. 教育分層（購買力最強代理）
- **DGBAS 14435** 可支配所得按教育程度、**108266** 消費支出×戶長教育程度（極高相關）。
- **內政部 ODRP053** 15 歲以上教育程度，**到村里級**（1,367 萬筆）、`ODRP020` 村里教育程度。

### 3. 人口／區域（分層的地理底圖）
- **內政部 ODRP052** 現住人口×單一年齡×性別×婚姻（村里級，可自算老化/扶養比）、
  `ODRP048` 鄉鎮市區人口密度、`ODRP060/061` 月更人口與遷徙動能。

### 4. 消費終端（錢實際落地處）
- **經濟部 6842** 批發零售餐飲營業額（消費終端頭號指標，月）、`45261` 綜合商品零售經營實況。
- **營業稅銷售額**（含 SME）已由 `mof_industry.py` 包好（3 碼行業全國 + 大類×縣市）。

### 5. 收入動能（高頻）
- **DGBAS 9634/9663** 受僱員工月薪（總薪資/經常性，月）、**勞動部 162820** 勞保人數×行業×地區
  （各地有申報所得就業人口 proxy）、`6647` 初任人員薪資。

---

## 與現有 wrapper 的關係

**已接、有 script**（見 SKILL.md）：家庭收支調查（`household.py`）、CPI/GDP/薪資/失業
（`dgbas_macro.py`）、批發零售餐飲與生產外銷（`moea_orders.py`）、營業稅（`mof_industry.py`）、
**綜合所得稅（`income_tax.py`：各縣市所得與稅率／所得結構薪資vs股利／村里級，全體申報戶）**、
景氣燈號（`ndc_signal.py`）、上市月營收（`twse_revenue.py`）。

**尚未包 wrapper 的高價值缺口**（值得接）：DGBAS 縣市別失業率（`mp0101a10`）與分行業受僱
人數（`mp05003`）、內政部 ODRP052/053（人口與教育到村里）、勞動部 162820 勞保人數×行業×地區。

## 卡點（誠實標注）

- **web02.mof.gov.tw/njswww 持續不通**（見 endpoints.md 停機記錄）：影響 HS 碼×國別貿易
  （28573、28536-58）與全國賦稅收入實徵淨額（6671/6742）——這兩批的 resource URL 全指向此
  死主機。貿易改走關務署 6053 + service.mof 15392（國別）+ 國貿署 FSC 重放。
- **縣市級以下的教育/薪資資料稀少**：教育程度縣市結構只有 10 年一次普查（20729-750）；
  鄉鎮級所得只有綜所稅村里表這一條。
- **coverage 日期在 metadata 常為空**，實際涵蓋期間要下載檔案看內容。
- 各機關格式不一：家庭收支/綜所稅=CSV（好接）、DGBAS 總經=XML、勞動部=CSV/JSON/XML 齊全。
