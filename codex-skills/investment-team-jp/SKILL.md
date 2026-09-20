---
name: investment-team-jp
description: 東証内国普通株を複数の独立視点で並行調査し、反対意見を統合して円建て投資判断を作る日本株向け投研チーム。
---

## Codexアダプター注記

このスキルは `skills/investment-team-jp.md` から生成され、Claude Code とCodexで正本を共有する。

- `$ARGUMENTS` は現在のCodexタスクにおけるユーザー依頼として扱う。
- 利用できる検索、シェル、ファイル編集機能を使い、必要な調査と検証を行う。
- 共通ツールはリポジトリ直下から実行し、日本版では `--locale ja`、必要に応じて `--market jp` / `--currency JPY` を付ける。
- 調査前に `date` で当日を確認し、データ基準日をレポート冒頭に記載する。
- `AGENTS.md` の品質規則に従い、財務数値の照合、正確な計算、欠損と不確実性を明示する。

# 日本株投研チーム

## 役割

可能なら独立した担当を並行させる。利用できない場合は同じ順序で一人ずつ実行し、各視点の暫定結論を統合前に固定する。

1. **事業担当**：顧客、価格、数量、コスト、再投資、競争優位を調べる。
2. **財務・評価担当**：開示数値、株式数、時価総額、資本効率、三情景評価を円で検証する。
3. **経営・ガバナンス担当**：資本配分、報酬、政策保有株、親子上場、支配株主、少数株主保護を調べる。
4. **反対意見担当**：最強の見送り理由、失敗経路、会計・循環・規制上の盲点を探す。

全担当は `skills/financial-data-jp.md` を使い、同じ会社・基準日・会計期間を共有する。国外企業は競争環境の説明に限り、投資候補へ加えない。

## リードの統合手順

- 各担当の事実、推論、未確認事項を分離する。
- 数値が食い違う場合は平均せず、期間・単位・連結範囲・株式分割・会計基準を調べる。
- 意見の一致より、結論を変える争点を優先する。
- 良い会社かと、現在価格で良い投資かを別に判定する。
- 最終判断は価格帯、想定保有期間、追加条件、売却・撤回条件を含める。

## 必須計算

```bash
python tools/financial_rigor.py --locale ja verify-market-cap --price {株価} --shares {株式数} --reported {時価総額} --currency JPY
python tools/financial_rigor.py --locale ja verify-valuation --price {株価} --eps {EPS} --bvps {BPS}
python tools/financial_rigor.py --locale ja three-scenario --price {株価} --eps {EPS} --shares {株式数_億株} --growth {強気} {基準} {弱気} --pe {強気PE} {基準PE} {弱気PE} --currency JPY
```

## 出力

統合レポートには、担当別結論、共通認識、対立点、重要な未確認事項、三情景評価、最終行動表を含める。重要データを `python tools/report_audit.py --locale ja extract --market jp --report {レポート}` と `verdict --market jp` で監査し、FAILなら公開判定を出さない。
