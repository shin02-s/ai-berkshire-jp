---
name: financial-data-jp
description: 東証内国普通株の価格・財務・開示を円建てで取得し、一次資料と独立経路で照合する日本株向けデータ規範。
---

## Codexアダプター注記

このスキルは `skills/financial-data-jp.md` から生成され、Claude Code とCodexで正本を共有する。

- `$ARGUMENTS` は現在のCodexタスクにおけるユーザー依頼として扱う。
- ソース中のClaude Code固有インターフェースは機能を落とさず、現在のセッションで最も近いCodex機能へ読み替える。`TeamCreate` は利用可能なサブAgentによるチーム編成、`TaskCreate` は境界の明確な担当割当、`TaskUpdate` は進捗・完了状態の追跡、`SendMessage` はAgent間の追加指示・結果回収、`TeamDelete` と `shutdown_request` は全結果回収後の終了・整理として扱う。
- `Task` / `Agent` は利用可能なサブAgent、`WebSearch` はWeb検索、`Bash` はシェル、`Read` / `Write` は通常のファイル読取・編集へ読み替える。サブAgentを利用できない場合は、同じ役割と検証順序を主タスクで逐次実行し、未実施の並行調査を装わない。
- 共通ツールはリポジトリ直下から実行し、日本版では `--locale ja`、必要に応じて `--market jp` / `--currency JPY` を付ける。
- 調査前に `date` で当日を確認し、データ基準日をレポート冒頭に記載する。
- `AGENTS.md` の品質規則に従い、財務数値の照合、正確な計算、欠損と不確実性を明示する。

# 日本株の財務データ取得・交差検証規範

## 対象と表記

- 対象は東証プライム・スタンダード・グロースの内国普通株。
- ETF、REIT、外国株は対象外。
- 数字4桁、東証の英数字コード、任意の `.T` 入力を受け付け、内部で正規化する。
- 通貨はJPY。表示単位は円、千円、百万円、億円、兆円から一つを選び、表内で混在させない。
- 日本基準／IFRS、連結／単体、会計年度、継続事業、親会社株主帰属利益を明示する。

---

## 情報源の優先順位

1. **正本**：EDINETの法定開示、会社IRの有価証券報告書・決算短信・適時開示。
2. **適時性**：TDnetの業績・配当修正、自己株式取得、M&A、資本政策等。
3. **市場・銘柄確認**：JPX上場会社情報、東証上場銘柄一覧、公開株価情報。
4. **価格補助**：`tools/jpstock_data.py` が利用するyfinance。公式値ではないため、重要な価格と時価総額はJPX等で照合する。
5. **第二経路**：信頼できる国内市場データまたは別の公開資料。同じ原資料の転載は独立ソースと数えない。

重要な売上高、利益、株式数、配当、株価、時価総額は、正本と独立した第二経路で照合する。第二経路が得られない場合は「単一ソース・低信頼」と表示する。

EDINET APIキーは環境変数 `EDINET_API_KEY` から読み、レポート、ログ、エラー出力へ表示しない。キーがなければEDINET API取得を停止し、会社IRと公開閲覧で代替したことを明記する。

---

## 第1段階：取得

```bash
python tools/jpstock_data.py quote 7203
python tools/jpstock_data.py prices 7203 --period 5y --adjusted
python tools/jpstock_data.py financials 7203
python tools/jpstock_data.py filings 7203 --years 5
```

- `quote`：現在値、前日比、時刻、取得元を確認する。
- `prices`：終値または調整後価格の系列を取得する。
- `financials`：直近18か月の開示から最新年次報告書を探索する。
- `filings`：複数年の開示一覧を取得し、営業日単位のキャッシュを再利用する。

コード不正、対象外証券、資料なし、API制限、通信失敗を区別する。欠損値をゼロへ置換しない。

---

## 第2段階：正確な計算と照合

### 時価総額

`株価 × 自己株式控除後の期末発行済株式数` を基本とする。用途により期中平均株式数や希薄化後株式数を使う場合は名称を変える。

```bash
python tools/financial_rigor.py --locale ja verify-market-cap --price 2800 --shares 1.63e9 --reported 4.564e12 --currency JPY
```

### 評価倍率

```bash
python tools/financial_rigor.py --locale ja verify-valuation --price 2800 --eps 210 --bvps 1850 --fcf-per-share 190 --dividend 75
```

EPSは親会社株主に帰属する利益と自己株式控除後の期中平均株式数の口径を確認する。PBRでは連結BPSか単体BPSかを明記する。

### 複数ソース

```bash
python tools/financial_rigor.py --locale ja cross-validate --field 売上高 --values '{"有価証券報告書":4500000,"決算短信":4500000}' --unit 百万円
```

許容差の目安：

- 同じ一次資料・同じ定義：原則0%。丸めだけ許容。
- 株価・時価総額：取得時刻差を考慮しつつ1%超は要確認。
- 財務集計：1%超または重要性基準超は要確認。
- 一株指標：株式分割・自己株式・期中平均の違いを確認。

閾値内でも定義が違えば一致扱いにしない。

---

## 第3段階：データの表示

```markdown
| 項目 | 値 | 単位 | 期間・時点 | 会計口径 | 出典1 | 出典2 | 差異 | 信頼度 |
|---|---:|---|---|---|---|---|---:|---|
```

値の横に、基準日、期間、単位、連結／単体、日本基準／IFRS、出典を置く。推定値は「推定」とし、算式と入力を残す。

### 信頼度

- 高：正本と独立経路が一致し、定義も一致。
- 中：正本を確認したが第二経路が同一原資料または小さな口径差。
- 低：単一ソース、推定、または未解消の不一致。

---

## よくある差異の原因

1. 連結と単体。
2. 日本基準とIFRS。
3. 通期、直近12か月、会社予想、実績。
4. 親会社株主帰属利益と営業利益・包括利益。
5. 期末株式数、期中平均株式数、希薄化後株式数。
6. 自己株式の控除、株式分割、株式併合。
7. 億円と百万円、端数処理、括弧・△・▲による負数。
8. 取得時刻、権利落ち、特別配当、株価調整。
9. 買収・売却、会計方針変更、決算期変更。
10. 営業CFから控除する設備投資の範囲。

差異を平均して消さず、原因を解明する。解明できない場合は両方の値と低信頼表示を残す。

---

## 日本企業で必ず確認する事項

- 政策保有株式と持合いの残高、売却実績、議決権方針。
- 親子上場、支配株主、関連当事者取引、特別委員会、少数株主保護。
- 配当性向、DOE、累進配当、下限配当、記念配当の区別。
- 自己株式取得枠、実績、取得価格、消却の有無。
- 株主優待の対象、費用、廃止可能性。現金配当と分離する。
- 資本コストや株価を意識した経営への対応と実行実績。
- ROE、ROIC、余剰現金、遊休資産、のれん、退職給付、リース。

---

## 株価と調整後価格

- 現在価値・時価総額：その時点の未調整株価と対応株式数を使う。
- 保有期間収益：分割・配当を反映した調整後価格を原則使い、配当を別加算して二重計上しない。
- 高値・安値：未調整か調整後かを明記する。
- 権利落ち：配当・優待落ちによる機械的変動と事業ニュースを区別する。

---

## 三情景と終価

```bash
python tools/financial_rigor.py --locale ja three-scenario --price {株価} --eps {EPS} --shares {株式数_億株} --growth {楽観} {基準} {保守} --pe {楽観PER} {基準PER} {保守PER} --currency JPY
python tools/terminal_value.py --locale ja company --currency JPY --rf {調査日当日の財務省公表値} ...
python tools/terminal_value.py --locale ja audit --currency JPY --rf {調査日当日の財務省公表値} ...
```

JPYでは無リスク金利を固定値で埋め込まず、調査日の財務省公表値を必ず指定する。`r > g`、最低スプレッド、すべてのCFと時価総額が円建てであることを確認する。

---

## レポート監査

```bash
python tools/report_audit.py --locale ja extract --report {レポートパス} --market jp
python tools/report_audit.py --locale ja verdict --results '<照合済みJSON>' --report {レポート名} --market jp
```

監査は円、千円、百万円、億円、兆円、倍、△・▲・括弧負数を含めて確認する。FAILのレポートは公開可能と扱わず、不一致項目を修正して再実行する。

---

## 失敗時の規則

- 一次資料が取得できない：会社IRの同一資料を探し、取得不能と基準日を書く。
- 第二ソースがない：低信頼とし、断定的な結論の根拠にしない。
- 数値が不一致：期間、単位、会計基準、連結範囲、株式数を照合する。
- 価格だけ取れない：財務分析を続けてもよいが、評価と時価総額を保留する。
- 古い資料しかない：最新と表現せず、データ截止日を明記する。

## クイック索引

| 目的 | 標準手段 |
|---|---|
| 現在株価 | `jpstock_data.py quote` + JPX照合 |
| 過去価格 | `jpstock_data.py prices` |
| 年次財務 | EDINET・会社IR + `jpstock_data.py financials` |
| 開示一覧 | `jpstock_data.py filings`、TDnet、会社IR |
| 時価総額 | `financial_rigor.py --locale ja verify-market-cap --currency JPY` |
| PER/PBR等 | `financial_rigor.py --locale ja verify-valuation` |
| 複数ソース照合 | `financial_rigor.py --locale ja cross-validate` |
| 終価 | `terminal_value.py --locale ja audit --currency JPY --rf ...` |
| 公開前監査 | `report_audit.py --locale ja ... --market jp` |
