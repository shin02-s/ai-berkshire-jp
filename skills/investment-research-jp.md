---
name: investment-research-jp
description: 東証内国普通株を事業、競争優位、経営、リスク、円建て評価から総合分析し、投資行動まで落とし込む日本語の深度調査。
---

# 日本株の総合投資研究

## 目的

一社の日本企業について、理解できる事業か、長期で価値を増やせるか、経営者が株主資本を適切に配分するか、現在価格に安全余地があるかを検証する。結論は「買う・保有・待つ・見送る」と、その判断が変わる条件まで書く。

## 必須手順

1. `date` で調査日を確認し、株価・開示の基準日を固定する。
2. `skills/financial-data-jp.md` に従い、有価証券報告書、決算短信、会社IR、TDnet、JPXを収集する。
3. 会社を一文で説明する。誰が何に払い、何が反復し、利益を動かす変数は何かを示す。
4. 売上構成、地域・顧客集中、単価、数量、原価、設備投資、運転資本を3〜5年で追う。
5. 競争優位を価格決定力、切替費用、規模、ブランド、ネットワーク、技術、規制、希少資産に分け、反証可能な形で評価する。
6. 経営陣を買収、売却、設備投資、研究開発、配当、自己株式取得、政策保有株の縮減、負債で評価する。
7. 親子上場、持合い、支配株主、関連当事者取引、少数株主保護を確認する。
8. 最強の弱気論、失敗経路、観測指標、撤回条件を書く。
9. 現在の円建て評価、過去レンジ、同業比較、三情景、期待収益率を計算する。
10. 空売りしていない投資家と既存保有者に分け、価格帯と行動条件を出す。

## 評価計算

```bash
python tools/financial_rigor.py --locale ja verify-market-cap --price {株価} --shares {株式数} --reported {時価総額} --currency JPY
python tools/financial_rigor.py --locale ja verify-valuation --price {株価} --eps {EPS} --bvps {BPS} --dividend {年間配当}
python tools/financial_rigor.py --locale ja three-scenario --price {株価} --eps {EPS} --shares {株式数_億株} --growth {強気} {基準} {弱気} --pe {強気PE} {基準PE} {弱気PE} --currency JPY
```

10年終値モデルを使う場合は、調査日当日の円無リスク金利を財務省公表値から確認して明記する。

```bash
python tools/terminal_value.py --locale ja audit --currency JPY --rf {無リスク金利} --r {資本コスト} --roic {定常ROIC} --g {弱気},{基準},{強気}
python tools/terminal_value.py --locale ja irr --profit {終値年利益} --mcap {現在時価総額} --pe {終値PE} --years 10 --payout {配当等}
```

## 日本株固有の判定

- 低PBRを割安と即断しない。資本効率、余剰資本、政策保有株、改善の実行速度を分解する。
- 株主還元は配当、DOE、自己株式取得、消却、株主優待を分ける。
- 親子上場や支配株主がある場合、利益成長より先に利益相反と資本政策を評価する。
- 海外企業は競合・顧客・供給網の説明に限り、国外上場銘柄を投資候補や評価比較へ混ぜない。

## 出力

`reports/{会社名}/{会社名}-investment-research-{YYYYMMDD}.md` に保存する。冒頭に基準日、証券コード、市場区分、株価、時価総額、主要倍率、情報信頼度を置く。末尾に出典、監査結果、論点別の確信度を付ける。

監査は `python tools/report_audit.py --locale ja extract --market jp --report {レポート}` と `verdict --market jp` で実行する。FAILまたは未照合の重要数値が残る場合はドラフトと明記する。
