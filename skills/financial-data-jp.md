---
name: financial-data-jp
description: 東証内国普通株の価格・財務・開示データを円建てで取得し、一次資料と別経路で照合する日本株向けデータ規範。
---

# 日本株の財務データ取得・交差検証規範

## 対象

- 東証プライム、スタンダード、グロースの内国普通株だけを投資対象にする。
- ETF、REIT、外国株、未上場証券はこのスキルの対象外とする。
- 証券コードは数字4桁または東証の英数字コードを使い、価格取得時は `.T` を許容する。
- 金額は原則として円、百万円、億円、兆円のいずれかに統一する。異なる単位を同じ表で混ぜない。

## 情報源の優先順位

1. **法定開示の正本**：EDINETの有価証券報告書、半期報告書、臨時報告書、大量保有報告書。
2. **適時開示の正本**：会社IR、TDnetの決算短信、業績予想・配当予想の修正、自己株式取得等。
3. **市場・銘柄確認**：JPX上場会社情報、東証株価検索、東証上場銘柄一覧。
4. **価格補助**：`tools/jpstock_data.py` が使うYahoo Finance。補助情報であり、重要な価格・時価総額はJPX等で照合する。
5. **第二経路**：信頼できる国内市場データサービスまたは別の公開経路。元資料が同一なら「独立した第二ソースではない」と明記する。

重要な売上高、利益、株式数、配当、時価総額、株価は二経路で照合する。独立した第二ソースを確保できなければ、数値を捨てずに「単一ソース・低信頼」と表示する。

## 取得コマンド

```bash
python tools/jpstock_data.py quote 7203
python tools/jpstock_data.py prices 7203 --period 5y --adjusted
python tools/jpstock_data.py financials 7203
python tools/jpstock_data.py filings 7203 --years 5
```

EDINET APIキーは環境変数 `EDINET_API_KEY` から読む。キーをレポート、ログ、コマンド履歴へ出力しない。

## 検証コマンド

```bash
python tools/financial_rigor.py --locale ja verify-market-cap \
  --price 2800 --shares 1.63e9 --reported 4.564e12 --currency JPY

python tools/financial_rigor.py --locale ja verify-valuation \
  --price 2800 --eps 210 --bvps 1850 --dividend 75

python tools/financial_rigor.py --locale ja cross-validate \
  --field 売上高 --values '{"有価証券報告書":4500000,"決算短信":4500000}' --unit 百万円
```

時価総額は `株価 × 自己株式控除後の発行済株式数` で再計算する。株式分割、自己株式、潜在株式、期中平均株式数と期末株式数の違いを確認する。

## 日本企業で必ず確認する事項

- 会計基準と決算期。日本基準、IFRS等を混同しない。
- 連結・単体、継続事業・非継続事業、親会社株主帰属利益の口径。
- 政策保有株式、持合い、親子上場、支配株主との取引、少数株主保護。
- 配当方針が配当性向、DOE、累進配当のどれか。自己株式取得と消却を区別する。
- 株主優待を総還元へ含める場合は、現金配当と分離して対象株主・換算根拠を示す。
- 資本コストや株価を意識した経営への対応、ROE、ROIC、PBR改善策の実行実績。

## レポート監査

保存後に次を実行し、抽出された数値を信頼できる経路で照合する。

```bash
python tools/report_audit.py --locale ja extract --market jp --report reports/{会社名}/{ファイル名}.md
python tools/report_audit.py --locale ja verdict --market jp --results '<検証済みJSON>' --report {ファイル名}.md
```

監査FAILのレポートは公開可能と扱わない。不一致が会計基準、期間、単位、株式分割、為替換算に由来する場合は、原因を数値の横に残す。
