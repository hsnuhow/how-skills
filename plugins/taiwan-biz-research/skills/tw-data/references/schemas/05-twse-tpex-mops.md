All endpoints fetched and verified. Here is the deliverable.

---

### TWSE OpenAPI — `https://openapi.twse.com.tw/v1/`

無金鑰、無 rate limit 標示、無查詢參數（每個 endpoint 只回「最新一期」全表）。`Content-Type: application/json`，body 為 **UTF-8**。**所有值都是字串**，包含數字與百分比。Swagger spec 在 `https://openapi.twse.com.tw/v1/swagger.json`（OpenAPI 3，306 KB，143 paths）。

#### `opendata/t187ap05_L` — 上市公司每月營業收入彙總表

實測 `HTTP 200 · 603,059 bytes · 1,082 rows`（2026-07-18 抓，資料年月 11506）。

| JSON key（原文） | 型別 | 單位 | 說明 |
|---|---|---|---|
| `出表日期` | str | — | **ROC**，`1150717` = 民國115年7月17日 |
| `資料年月` | str | — | **ROC**，`11506` = 民國115年6月（6 碼，YYYMM） |
| `公司代號` | str | — | `1101`、`2330`；含 `-KY` 公司 |
| `公司名稱` | str | — | **簡稱**（`台積電`），非全名 |
| `產業別` | str | — | **中文名稱字串**，非代碼。33 個值 |
| `營業收入-當月營收` | str | **千元** | 可為負值（見坑） |
| `營業收入-上月營收` | str | 千元 | |
| `營業收入-去年當月營收` | str | 千元 | |
| `營業收入-上月比較增減(%)` | str | % | 全精度浮點字串，`6.110785011084273` |
| `營業收入-去年同月增減(%)` | str | % | 同上 |
| `累計營業收入-當月累計營收` | str | 千元 | 年初至當月 |
| `累計營業收入-去年累計營收` | str | 千元 | |
| `累計營業收入-前期比較增減(%)` | str | % | |
| `備註` | str | — | 無備註時為 `"-"`（非空字串、非 null） |

真實範例：

```json
{
  "出表日期": "1150717", "資料年月": "11506",
  "公司代號": "1101", "公司名稱": "台泥", "產業別": "水泥工業",
  "營業收入-當月營收": "13382706",
  "營業收入-上月營收": "12612013",
  "營業收入-去年當月營收": "10107877",
  "營業收入-上月比較增減(%)": "6.110785011084273",
  "營業收入-去年同月增減(%)": "32.39878166305348",
  "累計營業收入-當月累計營收": "71467332",
  "累計營業收入-去年累計營收": "70380916",
  "累計營業收入-前期比較增減(%)": "1.5436229900730476",
  "備註": "-"
}
```

涵蓋期間與更新時點：法定申報期限為次月 10 日前，但**此 feed 的 `出表日期` 實測為 7/17**（資料年月 11506）。安全的 poll 時點是次月 15 日之後；10–15 日之間抓可能拿到不完整或仍是上一期的表。

姊妹端點 `opendata/t187ap05_P`（公開發行公司每月營業收入彙總表）schema 完全相同，母體較大。

#### `exchangeReport/STOCK_DAY_ALL` — 上市個股日成交資訊

實測 `HTTP 200 · 319,209 bytes · 1,371 rows`。**欄位名是英文**（與月營收的中文 key 混用）。

| JSON key | 單位 | 說明 |
|---|---|---|
| `Date` | — | **ROC**，`1150717` |
| `Code` | — | 含 ETF 與主動式（`00400A`） |
| `Name` | — | 簡稱 |
| `TradeVolume` | **股** | 非張 |
| `TradeValue` | **元** | |
| `OpeningPrice` / `HighestPrice` / `LowestPrice` / `ClosingPrice` | 元 | 2 位小數字串 |
| `Change` | 元 | **4 位小數**，`-180.0000`；無符號前綴時為漲 |
| `Transaction` | 筆 | 成交筆數 |

```json
{"Date":"1150717","Code":"2330","Name":"台積電","TradeVolume":"97362670",
 "TradeValue":"229051751965","OpeningPrice":"2375.00","HighestPrice":"2395.00",
 "LowestPrice":"2290.00","ClosingPrice":"2290.00","Change":"-180.0000","Transaction":"1150086"}
```

#### 對消費／零售研究有用的其他 TWSE endpoint

| Path | 內容 | 為何有用 |
|---|---|---|
| `opendata/t187ap03_L` | 上市公司基本資料（1,090 rows） | **唯一帶產業「代碼」的表**；另有 `成立日期`/`上市日期`（**西元** `19870221`）、`實收資本額`（元）、`已發行普通股數`（股） |
| `opendata/t187ap03_P` | 公發公司基本資料 | 同上，母體更大 |
| `opendata/t187ap05_P` | 公發公司月營收 | 未上市但已公發者的營收 |
| `opendata/t187ap14_L` | 上市公司各產業 EPS 統計（1,079 rows） | 季頻，**帶中文 `產業別`**，含 `營業收入`/`營業利益`/`稅後淨利`（千元） |
| `opendata/t187ap17_L` | 營益分析查詢彙總表（1,049 rows） | 季頻毛利率／營益率／稅前後純益率；`營業收入(百萬元)` 單位是**百萬元**，與其他表不同 |
| `opendata/t187ap06_L_ci` | 上市公司綜合損益表（一般業） | 季頻損益表，但**無推銷費用細項**（僅到營業費用層級）→ 推銷費用只能走 MOPS |
| `opendata/t187ap07_L_ci` | 上市公司資產負債表（一般業） | 存貨／應收，判斷零售庫存循環 |
| `opendata/t187ap45_L` | 上市公司股利分派情形 | |
| `fund/MI_QFIIS_cat` | 外資及陸資投資類股持股比率 | 類股層級資金流 |

#### 坑（TWSE）

1. **`t187ap05_L` 是當月快照，沒有歷史。** 每次請求只回最新一期，無 query 參數可指定月份。要建時間序列只能每月自行 poll 累積，或改走 MOPS 回補。
2. **日期格式站內混用。** 同一個 API 平台：`t187ap05_L.出表日期` / `STOCK_DAY_ALL.Date` 是 **ROC 7 碼**，但 `t187ap03_L.成立日期` / `上市日期` 是**西元 8 碼**。逐欄確認，不要整站套同一個 parser。
3. **欄位命名混用中英文。** `opendata/*` 系列多為中文 key，`exchangeReport/*` 系列為英文 key。
4. **所有數值是字串且含千分位不定。** 月營收數字**不含**逗號，但股價 `Change` 有 4 位小數、`普通股每股面額` 是 `"新台幣                 10.0000元"` 這種帶大量空白的自由文字。
5. **月營收可以是負數。** 見下方「產業別」段落——2905 三商的 `營業收入-去年當月營收` 為 `-4136304`。任何 `(當月-去年)/去年` 的自算 YoY 在負分母下會產生無意義的巨大百分比。
6. `備註` 欄無內容時是 `"-"`，不是空值；判空要寫 `r["備註"] != "-"`。
7. 產業別彙總的家數包含 `存託憑證`（TDR，2 家）與 `其他`（51 家），做全體加總時要決定是否排除。

---

### TWSE 產業別代碼 ↔ 名稱完整對照表

**沒有單一 endpoint 直接提供對照表。** `t187ap05_L`（月營收）只給**中文名稱**，`t187ap03_L`（基本資料）只給**兩位數代碼**。對照表必須**用 `公司代號` join 這兩個 endpoint 自行還原**：

```
GET /v1/opendata/t187ap03_L  →  {公司代號, 產業別: "24"}
GET /v1/opendata/t187ap05_L  →  {公司代號, 產業別: "半導體業"}
join on 公司代號
```

實測 join 結果為乾淨的 1:1（每個代碼只對到一個名稱，無衝突）。上市（TWSE）33 類完整對照：

| 代碼 | 名稱 | 家數 | 代碼 | 名稱 | 家數 |
|---|---|---|---|---|---|
| 01 | 水泥工業 | 7 | 22 | 生技醫療業 | 61 |
| **02** | **食品工業** | **25** | 23 | 油電燃氣業 | 8 |
| 03 | 塑膠工業 | 21 | 24 | 半導體業 | 96 |
| 04 | 紡織纖維 | 42 | 25 | 電腦及週邊設備業 | 64 |
| 05 | 電機機械 | 50 | 26 | 光電業 | 68 |
| 06 | 電器電纜 | 16 | 27 | 通信網路業 | 45 |
| 08 | 玻璃陶瓷 | 5 | 28 | 電子零組件業 | 104 |
| 09 | 造紙工業 | 7 | 29 | 電子通路業 | 21 |
| 10 | 鋼鐵工業 | 31 | 30 | 資訊服務業 | 11 |
| 11 | 橡膠工業 | 11 | 31 | 其他電子業 | 46 |
| 12 | 汽車工業 | 43 | 35 | 綠能環保 | 26 |
| 14 | 建材營造 | 55 | 36 | 數位雲端 | 12 |
| 15 | 航運業 | 28 | **37** | **運動休閒** | **18** |
| **16** | **觀光餐旅** | **19** | **38** | **居家生活** | **11** |
| 17 | 金融保險業 | 32 | 20 | 其他 | 51 |
| **18** | **貿易百貨** | **18** | 91 | 存託憑證 | 2 |
| 21 | 化學工業 | 28 | | | |

代碼 07、13、19、32、33、34 在上市不存在（32 文化創意業、33 農業科技只在上櫃有，見 TPEx 段落）。

**消費相關產業精確代碼：`02` 食品工業、`16` 觀光餐旅、`18` 貿易百貨、`37` 運動休閒、`38` 居家生活。**（`12` 汽車工業含大量零組件代工廠，不宜當消費指標。）

#### 坑：「貿易百貨 +67.6%」為何不可讀為零售復甦

比原本推測的「該類含貿易商」更嚴重。18 家成分股實測 2026-06：

| 公司 | 當月營收 | YoY |
|---|---|---|
| 2912 統一超 | 306.2 億 | **+6.3%** |
| **2905 三商** | **156.8 億** | **+479.2%** |
| 2908 特力 | 28.6 億 | +0.8% |
| 2903 遠百 | 23.2 億 | **−2.4%** |
| 2945 三商家購 | 16.9 億 | +39.1% |
| 2906 高林 | 7.3 億 | +5.2% |
| （其餘 12 家皆 < 3 億） | | |

整類 +67.6% 幾乎全部由 **2905 三商**一家貢獻，而三商的 `營業收入-去年當月營收` 是 **`-4136304`（負 41 億）**，其 `備註` 欄自述：

> `"當期及累計與去年同期增加，主係子公司人壽外匯價格變動準備淨變動增加收入所致。"`

也就是說：三商是持有人壽子公司的控股公司，其「營收」含保險外匯價格變動準備的淨變動，去年同期為負。這個負分母被加進產業合計，使「貿易百貨」的 YoY 成為**算術偽影**。真正的零售龍頭統一超只有 +6.3%、遠百是 −2.4%。

實務規則：(a) 產業彙總前先剔除 `營業收入-去年當月營收 <= 0` 的公司；(b) `18 貿易百貨` 與 `17 金融保險業` 之外，`20 其他` 也常混入控股公司，做消費解讀時一律下鑽到公司層級再看；(c) 有 `備註` 非 `"-"` 的公司要人工讀過再納入趨勢判斷。

---

### TPEx OpenAPI — `https://www.tpex.org.tw/openapi/v1/`

225 paths。Spec 在 `https://www.tpex.org.tw/openapi/swagger.json`（**不在 `/v1/` 底下**，實測 `HTTP 200 · 476,923 bytes`）。`servers[0].url` 宣告為 `https://www.tpex.org.tw/openapi/v1`。body 為 **UTF-8**、全字串。

#### `mopsfin_t187ap05_O` — 上櫃公司每月營業收入彙總表

實測 `HTTP 200 · 494,191 bytes · 891 rows`。**schema 與 TWSE `t187ap05_L` 完全相同**（同樣 14 個中文 key、同樣 ROC 日期、同樣千元），可以共用 parser。

```json
{"出表日期":"1150717","資料年月":"11506","公司代號":"1240","公司名稱":"茂生農經",
 "產業別":"農業科技","營業收入-當月營收":"270176","營業收入-上月營收":"244093",
 "營業收入-去年當月營收":"217592","營業收入-上月比較增減(%)":"10.685681277218109",
 "營業收入-去年同月增減(%)":"24.166329644472224","累計營業收入-當月累計營收":"1440672",
 "累計營業收入-去年累計營收":"1350363","累計營業收入-前期比較增減(%)":"6.68775729192817","備註":"-"}
```

#### `mopsfin_t187ap03_O` — 上櫃股票基本資料

實測 `HTTP 200 · 1,071,842 bytes · 891 rows`。**欄位名是英文**（與 TWSE 同一份資料的中文 key 不同），且部分 key 含句點：

| JSON key | 單位／格式 | 對應 TWSE 欄位 |
|---|---|---|
| `Date` | **ROC** `1150717` | 出表日期 |
| `SecuritiesCompanyCode` | — | 公司代號 |
| `CompanyName` / `CompanyAbbreviation` | — | 公司名稱／簡稱 |
| `SecuritiesIndustryCode` | 兩位數代碼 `"33"` | 產業別 |
| `UnifiedBusinessNo.` | — | 統編（**key 結尾有句點**） |
| `DateOfIncorporation` / `DateOfListing` | **西元** `19670218` | 成立／上市日期 |
| `Paidin.Capital.NTDollars` | **元** | 實收資本額 |
| `IssueShares` | **股** | 已發行普通股數 |
| `PrivateStock.shares` / `PreferredStock.shares` | 股 | |
| `ParValueOfCommonStock` | 自由文字 `"新台幣                 10.0000元"` | |

#### `tpex_mainboard_daily_close_quotes` — 上櫃個股日收盤行情

實測 `HTTP 200 · 3,915,518 bytes · 10,012 rows`（含 ETF／權證，遠多於個股數）。

| JSON key | 單位 |
|---|---|
| `Date` | **ROC** |
| `SecuritiesCompanyCode` / `CompanyName` | — |
| `Close` / `Open` / `High` / `Low` / `Average` | 元 |
| `Change` | 元，**值尾帶空白**：`"-3.26 "` |
| `TradingShares` | 股 |
| `TransactionAmount` | 元 |
| `TransactionNumber` | 筆 |
| `LatestBidPrice` / `LatesAskPrice` | 元（**`LatesAskPrice` 官方拼字就是少一個 t**） |
| `Capitals` | 元 |
| `NextReferencePrice` / `NextLimitUp` / `NextLimitDown` | 元 |

#### TPEx 產業別代碼 ↔ 名稱（同樣需 join `mopsfin_t187ap03_O` × `mopsfin_t187ap05_O`）

| 代碼 | 名稱 | 家數 | | 代碼 | 名稱 | 家數 |
|---|---|---|---|---|---|---|
| **02** | **食品工業** | 9 | | 27 | 通信網路業 | 45 |
| 03 | 塑膠工業 | 4 | | 28 | 電子零組件業 | 106 |
| 04 | 紡織纖維 | 10 | | 29 | 電子通路業 | 16 |
| 05 | 電機機械 | 50 | | 30 | 資訊服務業 | 34 |
| 06 | 電器電纜 | 1 | | 31 | 其他電子業 | 48 |
| 10 | 鋼鐵工業 | 17 | | **32** | **文化創意業** | **26** |
| 14 | 建材營造 | 33 | | **33** | **農業科技** | **4** |
| 15 | 航運業 | 6 | | 35 | 綠能環保 | 19 |
| **16** | **觀光餐旅** | **32** | | 36 | 數位雲端 | 27 |
| 17 | **金融業** | 9 | | **37** | **運動休閒** | 9 |
| 20 | 其他 | 42 | | **38** | **居家生活** | 24 |
| 21 | 化學工業 | 14 | | 22 | 生技醫療業 | 99 |
| 23 | 油電燃氣業 | 4 | | 24 | 半導體業 | 110 |
| 25 | 電腦及週邊設備業 | 45 | | 26 | 光電業 | 48 |

跨市場對照差異（**做上市＋上櫃合併時必踩**）：

- 代碼 `17` 在 TWSE 叫「金融保險業」、在 TPEx 叫「**金融業**」——同代碼、不同字串，用名稱 join 會漏。
- TPEx 獨有：`32 文化創意業`、`33 農業科技`。TWSE 無此二類。
- TPEx **完全沒有 `18 貿易百貨`**，也沒有 01/08/09/11/12。零售通路的上櫃公司散落在 `20 其他` 與 `38 居家生活`。
- TPEx `16 觀光餐旅` 有 32 家，比 TWSE 的 19 家還多——餐飲研究若只看上市會漏掉一半以上母體。

#### 坑（TPEx）

1. **未知路徑 302 導向首頁。** 實測 `GET /openapi/v1/does_not_exist` → `HTTP 302`，`Location: https://www.tpex.org.tw/`。加 `-L` 會得到 `HTTP 200 · 22,964 bytes · text/html`（櫃買中心首頁 HTML）。**打錯 path 不會拿到 4xx，而是拿到一份看起來成功的 22KB HTML。** 抓取時務必：不要用 `-L`，並檢查 `Content-Type` 是否為 `application/json`。
2. **`mopsfin_t187ap05_OA` 文件描述是「二十九大類股營收變化統計表」，但實測回傳與 `mopsfin_t187ap05_O` byte-identical**（同為 494,191 bytes、891 rows、md5 相同 `0e332a2e…`，第一筆同為 1240 茂生農經）。想要現成的類股彙總表的話，這個 endpoint 拿不到，得自己 roll-up。
3. **swagger.json 不在 `/v1/` 底下。** `https://www.tpex.org.tw/openapi/v1/swagger.json` 會落入第 1 點的 302 陷阱。正確位置是 `https://www.tpex.org.tw/openapi/swagger.json`。
4. **同一站中英文 key 混用且不一致。** `mopsfin_t187ap05_O` 用中文 key（與 TWSE 相同），但 `mopsfin_t187ap03_O`、行情類全用英文 key。且英文 key 有官方拼寫錯誤（`LatesAskPrice`）與含句點的 key（`UnifiedBusinessNo.`、`Paidin.Capital.NTDollars`），用點記法存取的 ORM/工具會炸。
5. **日期同站混用 ROC 與西元**：`Date` 是 ROC 7 碼，`DateOfListing` / `DateOfIncorporation` 是西元 8 碼。
6. 行情端點回 10,012 筆，含大量 ETF／權證／債券；要濾個股需自行以代號規則排除。

---

### MOPS inline-XBRL 財報 — 推銷費用的唯一免費路徑

```
https://mopsov.twse.com.tw/server-java/t164sb01?step=1&CO_ID={代號}&SYEAR={西元}&SSEASON={1-4}&REPORT_ID=C
```

**編碼：Big5（`<meta charset=big5>`）。** 實測 body 無法以 UTF-8 解碼（`'utf-8' codec can't decode byte 0xb2 in position 3642`）。必須 `raw.decode('big5')` 之後再搜尋關鍵字，否則 `推銷費用` 等字串全部 miss。

參數：`SYEAR` 為**西元 4 碼**（非 ROC）；`SSEASON` 為 1–4；`REPORT_ID=C` 為合併報表。

2330 / 2025Q1 實測 `HTTP 200 · 725,996 bytes`，內含 1,193 個 `<ix:nonFraction>` 標籤。

#### Schema（inline XBRL 標籤）

每個數字是一個 `<ix:nonFraction>` 元素，屬性即為完整 schema：

```html
<td style="text-align:center">6100</td>
<td><span class="zh">　推銷費用</span><span class="en">　Selling expenses</span></td>
<td class="amt"><pre><ix:nonFraction name="ifrs-full:SellingExpense"
    contextRef="From20250101To20250331" format="ixt:numdotdecimal"
    scale="3" decimals="-3" unitRef="TWD">3,754,815</ix:nonFraction> </pre></td>
```

| 屬性 | 意義 |
|---|---|
| `name` | IFRS taxonomy 概念名，如 `ifrs-full:SellingExpense`。**這是唯一穩定的抓取鍵**，不要靠中文文字定位 |
| `contextRef` | 期間，如 `From20250101To20250331`（期間型）或 `AsOf20250331`（時點型）。**日期為西元** |
| `scale` | 實測只有 `"0"` 與 `"3"`。`scale="3"` 表示**畫面顯示值為千元**，乘 10³ 得元 |
| `decimals` | `-3`（四捨五入至千位） |
| `unitRef` | 實測只有 `TWD` 與 `EarningsPerShare` |
| 文字節點 | 帶千分位逗號的字串 `3,754,815`；**節點後有一個尾隨空白** |

會計科目代碼（`6100`、`6200`…）出現在同一 `<tr>` 的第一個 `<td>`，可作為次要定位鍵。

`contextRef` 對應的期間定義在文件內的 `<xbrli:context>`：

```xml
<xbrli:context id="From20250101To20250331">
  <xbrli:entity><xbrli:identifier scheme="http://www.twse.com.tw">2330</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-03-31</xbrli:endDate></xbrli:period>
</xbrli:context>
```

#### 驗證結果（2330 · 2025Q1 · REPORT_ID=C，單位千元）

| 科目代碼 | 中文 | IFRS `name` | 2025Q1 | 2024Q1 |
|---|---|---|---|---|
| — | 營業收入 | `ifrs-full:Revenue` | 839,253,664 | 592,644,201 |
| — | 營業毛利 | `ifrs-full:GrossProfit` | 493,395,076 | 314,505,269 |
| 6100 | 推銷費用 | `ifrs-full:SellingExpense` | **3,754,815** ✅ | 3,111,259 |
| 6200 | 管理費用 | `ifrs-full:AdministrativeExpense` | **24,883,748** ✅ | 16,137,086 |
| 6300 | 研究發展費用 | `ifrs-full:ResearchAndDevelopmentExpense` | **56,547,493** ✅ | 46,108,936 |
| — | 營業費用合計 | `ifrs-full:OperatingExpense` | 85,186,056 | 65,357,281 |
| — | 營業利益 | `ifrs-full:ProfitLossFromOperatingActivities` | 407,080,808 | 249,018,306 |

三項已知答案全部吻合。

同一支解析器對消費股同樣有效（2912 統一超 2025Q1，`HTTP 200 · 917,447 bytes`）：`Revenue` 84,641,319 / `SellingExpense` **22,028,588** / `AdministrativeExpense` 3,084,244 千元 — 推銷費用佔營收 26.0%，與台積電的 0.45% 形成對照，證實這條路徑能區分「賣通路」與「賣製造」的成本結構。

涵蓋期間：季報自各公司上市起可回溯多年（實測 2024Q4、2025Q3 皆正常回應 780–790 KB）。發布時點跟隨法定財報期限（Q1/Q3 為季後 45 天、Q2 為 60 天、年報為次年 3/31）。

#### 坑（MOPS）

1. **Big5，且必須先解碼。** 直接對 raw bytes 做 `if '推銷費用' in body` 永遠是 False。且 `.decode('utf-8')` 會拋例外——用 `raw.decode('big5', errors='replace')`。
2. **`REPORT_ID=A`（個體報表）在此端點是死路。** 實測 2330 於 **2025Q1 與 2024Q4（年報）皆回 `HTTP 200 · 98 bytes`**，body 解 Big5 後為 `<h4 align='center'><font color='red'>檔案不存在!</font></h4>`。「200 但只有 98 bytes」是失敗訊號，不是空資料——必須檢查 `Content-Length` 或 body 長度，只看 status code 會誤判成功。個體推銷費用請改用合併報表 `C`。
3. **主機必須是 `mopsov.twse.com.tw`。** 新站 `mops.twse.com.tw` 同一路徑回 `HTTP 200 · 800 bytes`，內容為 UTF-8 的「因為安全性考量，您所執行的頁面無法呈現。/ FOR SECURITY REASONS, THIS PAGE CAN NOT BE ACCESSED.」附錯誤代碼。這也是一個 200 偽成功。
4. **`SYEAR` 是西元不是民國**，與 TWSE/TPEx 的 ROC 慣例相反。傳 `SYEAR=114` 會落入「檔案不存在」。
5. **不要用中文字串定位數字。** 應以 `name="ifrs-full:XXX"` 定位。中文標籤前綴含全形空白（`　推銷費用`）作縮排，不同公司縮排層級不同；`<span class="zh">` 與 `<span class="en">` 並存，正則若不謹慎會抓到英文列。
6. **`scale="3"` 不可忽略。** 標籤文字 `3,754,815` 的實際金額是 3,754,815 **千元**（= 3,754,815,000 元）。若日後某公司送出 `scale="0"` 的報表，同樣的解析會差 1000 倍——一律讀 `scale` 屬性而非假設千元。
7. **每個科目有兩個值**（本期 + 去年同期），`contextRef` 是唯一區分方式。用 `re.search` 只取第一個匹配會拿到本期，但這是巧合，順序不保證。
8. `contextRef` 有大量 `_XxxMember` 後綴的變體（權益變動表的維度切分，實測 96 個不同 context）。過濾時要用精確相等 `contextRef == "From20250101To20250331"`，不能用 `startswith`。
9. 單檔 725 KB－920 KB，逐公司逐季抓取要自行 rate-limit；MOPS 對高頻請求會擋。

---

### 失敗與異常彙總

| 目標 | 結果 | 失敗模式 |
|---|---|---|
| `mopsfin_t187ap05_OA`（TPEx 二十九大類股營收變化統計表） | **失敗（靜默）** | `HTTP 200`，但回傳與 `_O` byte-identical（md5 相同），非類股彙總表。無錯誤訊息 |
| `REPORT_ID=A`（MOPS 個體報表） | **失敗** | `HTTP 200 · 98 bytes`，Big5 body = `檔案不存在!`。季報與年報皆然 |
| `mops.twse.com.tw`（MOPS 新站） | **失敗** | `HTTP 200 · 800 bytes`，UTF-8 安全性阻擋頁 |
| TPEx 未知路徑 | **失敗（危險）** | 無 `-L`：`302 → https://www.tpex.org.tw/`；有 `-L`：`200 · 22,964 bytes · text/html` 首頁 |
| `https://www.tpex.org.tw/openapi/v1/swagger.json` | **失敗** | 同上 302 陷阱；正確位置為 `/openapi/swagger.json` |
| TWSE 產業別代碼對照表單一 endpoint | **不存在** | 需 join `t187ap03_L` × `t187ap05_L`（join 結果驗證為乾淨 1:1） |
| `t187ap05_L` 歷史月份 | **不支援** | 無 query 參數，永遠只回最新一期 |