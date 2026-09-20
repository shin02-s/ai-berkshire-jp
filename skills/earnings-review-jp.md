---
name: earnings-review-jp
description: 日本企業の決算短信・説明資料・有価証券報告書を読み、業績の質と通期見通しを円建てで検証する財報精読。
---

# 日本企業の決算精読

## 入力と正本

対象期間、証券コード、決算発表日を確認する。会社IRまたはTDnetの決算短信、決算説明資料、有価証券報告書・半期報告書を優先し、集計サイトだけで精読を完了しない。

## 読み方

1. 会計基準、連結範囲、決算期、前年同期の組替えを確認する。
2. 売上高、営業利益、親会社株主帰属利益、EPS、営業CF、設備投資、受注・契約残を前年同期・会社計画と比較する。
3. 数量、単価、製品構成、原材料、人件費、為替、稼働率、一時損益に分解する。
4. 会社計画の据置・修正と、進捗率だけでは分からない季節性を確認する。
5. 配当方針、DOE、自己株式取得、消却、株主優待変更を確認する。
6. セグメント間取引、減損、引当金、在庫、売掛金、税率、非支配持分を点検する。
7. 経営者説明と数値の整合、前回説明から変わった表現を抽出する。

## 検証

`skills/financial-data-jp.md` に従って主要数値を二経路で照合する。

```bash
python tools/financial_rigor.py --locale ja cross-validate --field 営業利益 --values '{"決算短信":120000,"説明資料":120000}' --unit 百万円
python tools/financial_rigor.py --locale ja verify-market-cap --price {株価} --shares {株式数} --reported {時価総額} --currency JPY
python tools/financial_rigor.py --locale ja verify-valuation --price {株価} --eps {EPS} --bvps {BPS}
```

## 出力

- 決算の一文判定
- 主要KPI表と前年差・計画差
- 利益変動の要因分解
- キャッシュフローと会計上の注意点
- 会社計画の達成可能性
- 資本政策とガバナンス上の変化
- 投資仮説への影響：強化・不変・弱化・破綻
- 次回までの観測指標

保存後に `python tools/report_audit.py --locale ja extract --market jp --report {レポート}` を実行し、検証結果を用意して `verdict --market jp` まで通す。資料を取得できない場合は第三者集計を正本扱いせず、欠損を明記する。
