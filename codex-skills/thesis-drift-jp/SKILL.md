---
name: thesis-drift-jp
description: 日本株の過去の投資仮説と現在の事実を比較し、事業変化と文章の言い換えを区別して仮説の漂流を検出する。
---

## Codexアダプター注記

このスキルは `skills/thesis-drift-jp.md` から生成され、Claude Code とCodexで正本を共有する。

- `$ARGUMENTS` は現在のCodexタスクにおけるユーザー依頼として扱う。
- 利用できる検索、シェル、ファイル編集機能を使い、必要な調査と検証を行う。
- 共通ツールはリポジトリ直下から実行し、日本版では `--locale ja`、必要に応じて `--market jp` / `--currency JPY` を付ける。
- 調査前に `date` で当日を確認し、データ基準日をレポート冒頭に記載する。
- `AGENTS.md` の品質規則に従い、財務数値の照合、正確な計算、欠損と不確実性を明示する。

# 日本株の投資仮説ドリフト検出

## 目的

過去の仮説を現在の結果に合わせて無意識に書き換えることを防ぐ。元の仮説、当時の観測指標、現在の事実を並べ、変化を定量化する。

## 手順

1. 元レポートの日付、買付理由、主要仮定、価格、撤回条件を抽出する。
2. 最新の有価証券報告書、決算短信、適時開示、会社IRを取得する。
3. 売上・利益・CF、顧客、価格、数量、競争優位、経営、資本政策、ガバナンスを同じ口径で比較する。
4. 各差分を「事実変化」「仮定外れ」「表現変更」「未確認」に分類する。
5. 政策保有株、親子上場、支配株主、配当・DOE、自己株式取得の変化も追う。
6. 仮説を「維持・要修正・弱化・破綻」で判定し、次の行動条件を示す。

## 計算

```bash
python tools/financial_rigor.py --locale ja verify-valuation --price {現在株価} --eps {現在EPS} --bvps {現在BPS}
python tools/financial_rigor.py --locale ja verify-market-cap --price {現在株価} --shares {現在株式数} --reported {現在時価総額} --currency JPY
python tools/financial_rigor.py --locale ja calc --expr '{変化率等の算式}'
```

評価上昇で仮説が正しかったと判断せず、事業結果と当初仮定を比較する。元仮説に存在しなかった理由を後付けする場合は、新規仮説として明記する。

## 出力

元仮説、差分表、ドリフト判定、最大の誤り、現在の仮説、撤回条件、次回確認日をまとめる。データは `skills/financial-data-jp.md` に従う。
