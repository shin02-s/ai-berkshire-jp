---
name: earnings-team-jp
description: 日本企業の決算を事業、財務、経営、反対意見の複数視点で精読し、投資仮説への影響を統合するチーム分析。
---

# 日本企業の決算精読チーム

## 担当

1. **数値担当**：決算短信と法定開示から損益、CF、財政状態、株式数を検証する。
2. **事業担当**：数量・単価・構成・受注・稼働率・顧客動向から再現性を判断する。
3. **経営担当**：会社計画、説明の一貫性、資本配分、配当、DOE、自己株式取得、政策保有株を評価する。
4. **反対意見担当**：一時要因、季節性、会計判断、在庫、減損、利益相反、見落とされた弱気材料を探す。

各担当は同じ対象期間と `skills/financial-data-jp.md` を使う。並行実行できない場合も、各担当の暫定判定を先に記録してから統合する。

## 統合

- 発表前予想ではなく、会社計画と過去説明に対する差を中心にする。
- 上振れでも質が悪ければ明記し、下振れでも先行投資なら回収条件を示す。
- 数値不一致は平均せず、単位・期間・会計基準・連結範囲を特定する。
- 投資仮説を「強化・不変・弱化・破綻」で判定する。
- 株価反応は事実と市場解釈を分け、価格変動だけで決算の質を決めない。

## 共通計算

```bash
python tools/financial_rigor.py --locale ja cross-validate --field {項目} --values '{"資料A":1,"資料B":1}' --unit 百万円
python tools/financial_rigor.py --locale ja verify-valuation --price {株価} --eps {EPS} --bvps {BPS}
python tools/financial_rigor.py --locale ja three-scenario --price {株価} --eps {EPS} --shares {株式数_億株} --growth {強気} {基準} {弱気} --pe {強気PE} {基準PE} {弱気PE} --currency JPY
```

## 成果物

冒頭に発表日時、対象期間、会計基準、株価基準日を置く。担当別メモ、争点、決算の質、通期見通し、仮説への影響、次回観測表、行動条件を統合し、`python tools/report_audit.py --locale ja extract --market jp --report {レポート}` と `verdict --market jp` の結果を末尾へ付ける。
