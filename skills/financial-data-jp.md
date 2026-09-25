# 財務データの取得とクロスチェック基準

本基準は、企業の財務データを扱うすべての調査に適用する。**各重要データは、必ず2つの独立した情報源から取得し、誤差が1%を超える場合は印を付ける。**

---

## データソースの優先順位

### 米国株（PDD、テンセントADR、NetEase ADRなど）

| 優先度 | 情報源 | URL | 取得方法 |
|--------|------|-----|---------|
| 1（主） | **macrotrends** | macrotrends.net/stocks/charts/{ticker} | 直接アクセス、登録不要 |
| 2（副） | **stockanalysis** | stockanalysis.com/stocks/{ticker}/financials | 直接アクセス、登録不要 |
| 一次資料 | SEC EDGAR | sec.gov/cgi-bin/browse-edgar | 10-K／10-Q原文 |

### 香港株（テンセント0700、NetEase 9999、美団3690など）

| 優先度 | 情報源 | URL | 取得方法 |
|--------|------|-----|---------|
| 1（主） | **aastocks** | aastocks.com/tc/stocks/analysis/company-fundamental | 直接アクセス |
| 2（副） | **macrotrends**（ADRコード） | テンセントはTCEHY、NetEaseはNTES | 直接アクセス |
| 一次資料 | HKEXnews | hkexnews.hk | 年次報告書PDF |

### 中国A株（三七互娯、G-bitsなど）

| 優先度 | 情報源 | URL | 取得方法 |
|--------|------|-----|---------|
| 1（主） | **Eastmoney** | eastmoney.com → 株式コードを検索 → 財務諸表 | 直接アクセス |
| 2（副） | **CNINFO** | cninfo.com.cn | 年次報告書／四半期報告書の原文PDF |

### 台湾株（TSMC 2330、MediaTek 2454、Largan Precision 3008など）

| 優先度 | 情報源 | URL | 取得方法 |
|--------|------|-----|---------|
| 1（主） | **FinMind API** | api.finmindtrade.com | `tools/twstock_data.py`（依存関係のないスクリプト。下記参照） |
| 2（副） | **Goodinfo台湾株式情報サイト** | goodinfo.tw/tw/StockDetail.asp?STOCK_ID={コード} | 直接アクセス |
| 一次資料 | 公開情報観測站（MOPS） | mops.twse.com.tw | 決算原文／月次売上高の開示 |

**FinMindデータ取得ツール**（台湾株の分析時に優先して使用。出力には時価総額の再計算を含む）：

```bash
python3 tools/twstock_data.py quote 2330        # 最新の株価情報 + PER/PBR/配当利回り + 時価総額の再計算
python3 tools/twstock_data.py valuation 2330    # バリュエーション指標 + PERの1年間レンジ + 52週高値・安値
python3 tools/twstock_data.py financials 2330   # 直近5年間の主要年次財務データ（売上高/粗利率/親会社株主帰属純利益/EPS/自己資本利益率）
python3 tools/twstock_data.py revenue 2330      # 直近13カ月の月次売上高と前年同期比
python3 tools/twstock_data.py dividend 2330     # 近年の配当方針（現金/株式配当、権利落ち日）
python3 tools/twstock_data.py search 台積        # 株式コードを検索（台湾株の名称は繁体字である点に注意）
```

台湾株の特記事項：

1. **通貨単位はニュー台湾ドル（TWD）**。香港ドル／人民元／米ドルと併記する場合は必ず明示し、市場をまたぐ比較では先に同一通貨へ換算する
2. **月次売上高は台湾株独自の強み**：上場・店頭公開企業は毎月10日までに前月の売上高を開示することが義務付けられており、ファンダメンタルズの転換点を追跡する最も速い公開シグナルである。earnings-review／thesis-tracker系の分析では優先して利用する（`revenue` サブコマンド）
3. FinMindの利益計算書は**単四半期の値**。ツールは自動的に年次の値へ合算する。4四半期に満たない年には「第N四半期までの累計のみ」と表示する
4. FinMindは未登録でも直接利用可能（1時間当たりの上限あり）。登録後のAPIトークンは**ローカルのみに保存し、gitへ絶対にコミットしない**。ツールは次の優先順位で自動的に読み込む：①環境変数 `FINMIND_TOKEN`、②ローカルファイル `local/finmind_token.txt`（`local/` は `.gitignore` で恒久的に除外済み。トークンだけを1行でこのファイルへ記載）。トークンをレポート、skill、commitに含めてはならない
5. クロスチェック：FinMindの数値をGoodinfo（またはTSMCなどADRがある企業はmacrotrends上のADR）と照合し、下記と同じ誤差ルールを適用する。TSMCなどADRがある企業では、ADRと台湾原株の為替／預託比率の差に注意する（TSM ADR 1株 = 2330の5株）

---

### 日本株（トヨタ7203、任天堂7974など）

| 優先度 | 情報源 | 用途 | 取得方法 |
|---|---|---|---|
| 1（正本） | **EDINET API v2** | 有価証券報告書、XBRL財務数値、発行済株式数 | `tools/jpstock_data.py financials 7203` / `filings 7203` |
| 2（価格補助） | **Yahoo Finance / yfinance** | 日足、出来高、配当、株式分割、調整後株価 | `tools/jpstock_data.py quote 7203` / `prices 7203 --period 5y --adjusted` |
| 3（クロスチェック） | TDnet／企業IR | 決算短信と企業開示 | 原文へ直接アクセス |

**日本株データ取得ツール**：

```bash
python tools/jpstock_data.py quote 7203
python tools/jpstock_data.py prices 7203 --period 5y --adjusted
python tools/jpstock_data.py financials 7203
python tools/jpstock_data.py filings 7203 --years 5
```

EDINETコマンドには必ず `EDINET_API_KEY` を設定する。Windowsでは
`powershell -ExecutionPolicy Bypass -File scripts/set-edinet-api-key.ps1` を実行する。キーはユーザー環境変数にのみ保存し、レポート、Git、コマンド出力へ記載してはならない。yfinanceは価格データの補助にのみ使用し、EDINETの財務原本を絶対に代替してはならない。重要な財務数値には、TDnetまたは企業IRを第2の情報源として使用し、`financial_rigor.py cross-validate` で差異を記録する。

---

## 実行基準

### ステップ1：データを取得する

各財務指標（売上高、純利益、粗利率、営業キャッシュフロー、負債比率など）について、**情報源1**と**情報源2**からそれぞれ数値を取得する。

### ステップ2：誤差の計算と表示

```
誤差率 = |情報源1の数値 - 情報源2の数値| / 情報源1の数値 × 100%
```

| 誤差 | 対応方法 |
|------|---------|
| 1%以下 | ✅ 一致。情報源1の数値を採用し、2つの情報源を明記 |
| 1%超～5% | ⚠️ 「データに差異あり」と表示。両方の数値を記載し、考えられる理由（為替／会計基準）を説明 |
| 5%超 | ❌ 「データに重大な差異あり」と表示。決算原文で必ず確認し、そのまま使用してはならない |

### ステップ3：データの表示形式

各重要データは、必ず次の形式で表示する：

```
売上高：1,239億元 ✅
  - macrotrends：1,241億元
  - stockanalysis：1,237億元
  - 誤差：0.3%
```

差異がある場合の例：
```
純利益：245億元 ⚠️ データに差異あり
  - macrotrends：245億元（GAAP）
  - stockanalysis：278億元（Non-GAAP）
  - 誤差：13.5% — 理由：会計基準の違い（GAAP vs Non-GAAP）
```

---

## よくある差異の原因（必ずしもデータ誤りではない）

| 原因 | 説明 |
|------|------|
| GAAP vs Non-GAAP | 最も一般的。特に利益関連データで多い |
| 為替換算 | 香港ドル／人民元／米ドルの換算時点が異なる |
| 会計年度の定義 | 暦年 vs 会計年度（Appleの会計年度は10月終了など） |
| 連結範囲 | 非支配株主持分を含むかどうか |
| データ更新の遅れ | 一部プラットフォームが最新の決算をまだ反映していない |

---

## 特別ルール

1. **未上場企業**（miHoYo、Lilith Gamesなど）：一次資料が1つしかない場合は、データの前に `[推定]` と表示し、クロスチェックを行わない
2. **四半期データ vs 年次データ**：クロスチェックでは年次データを優先する。四半期データは一部の情報源で更新が遅れる場合がある
3. **決算原文を優先**：2つの情報源がいずれも決算原文（10-K／年次報告書PDF）と一致しない場合は、決算原文を正とし、情報源の誤りを表示する

---

## 株価と調整（過去時系列の分析では必読）

株価には3つの基準があり、混在させると過去の株価水準、長期上昇率、過去のバリュエーション分位がすべて不正確になる：

| 基準 | 意味 | 用途 |
|------|------|------|
| 未調整 | 実際の約定価格。権利落ち・配当落ち日にギャップが生じる | 「現在時点」のスナップショットにのみ使用 |
| 前方調整 | 最新株価を基準に過去の株価を遡及調整 | 過去の株価比較、N年間の上昇率、過去PERバンドには必ずこれを使用 |
| 後方調整 | 上場初日の株価を基準に将来方向へ調整 | 過去のトータルリターン／年率リターンの計算 |

ルール：

1. 過去の価格を扱う分析では、すべて**前方調整後株価**を使用し、同一分析内で**調整済みと未調整の情報源を混在させてはならない**。
2. 現在の時価総額／現在のPERは、**現在の実株価 × 現在の発行済株式総数**で計算でき、調整とは無関係。調整が影響するのは過去の時系列だけである。
3. 株式分割／大規模な無償増資をまたぐ1株当たり指標（過去EPS、過去株価）は、必ず調整してから前年同期比を計算する。
4. トータルリターン／年率リターンには配当を含める必要がある（後方調整には反映済み）。株価上昇率だけでは過小評価になる。
5. 増資／自社株買い後の時価総額再計算には、最新の発行済株式総数を使う（`financial_rigor.py verify-market-cap` は偏差が5%を超えると確認を促す）。

---

## クイックインデックス

| 対象 | 主な情報源 | 予備の情報源 |
|------|---------|---------|
| PDD／Pinduoduo | macrotrends.net/stocks/charts/PDD | stockanalysis.com/stocks/pdd |
| テンセント | macrotrends.net/stocks/charts/TCEHY | aastocks（0700.HK） |
| NetEase | macrotrends.net/stocks/charts/NTES | aastocks（9999.HK） |
| 三七互娯 | eastmoney.com（002555） | cninfo.com.cn |
| G-bits | eastmoney.com（603444） | cninfo.com.cn |
| Nintendo | macrotrends.net/stocks/charts/NTDOY | stockanalysis.com/stocks/ntdoy |
| Capcom | macrotrends（CCOEY） | stockanalysis（CCOEY） |
| TSMC | tools/twstock_data.py（2330） | goodinfo.tw / macrotrends（TSM、1 ADR = 5株である点に注意） |
| MediaTek | tools/twstock_data.py（2454） | goodinfo.tw |
| トヨタ | tools/jpstock_data.py（7203）EDINET財務 | TDnet／トヨタIR |
| 任天堂 | tools/jpstock_data.py（7974）EDINET財務 | TDnet／任天堂IR |
