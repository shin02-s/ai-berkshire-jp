"""日本株版スキルの命名・市場境界・生成物を検証する。"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = {
    "bottleneck-hunter-jp", "deep-company-series-jp", "dyp-ask-jp",
    "earnings-review-jp", "earnings-team-jp", "era-alpha-jp",
    "financial-data-jp", "income-investment-jp", "industry-funnel-jp",
    "industry-research-jp", "investment-checklist-jp",
    "investment-research-jp", "investment-team-jp",
    "management-deep-dive-jp", "news-pulse-jp", "portfolio-review-jp",
    "private-company-research-jp", "quality-screen-jp", "thesis-drift-jp",
    "thesis-tracker-jp", "wechat-article-jp",
}
CODEX_ONLY = "investment-memo-craft-jp"
FORBIDDEN = re.compile(
    r"SEC|EDGAR|FinMind|twstock_data|ashare_data|xueqiu_scraper|"
    r"USD|CNY|HKD|TWD|美股|A股|港股|台股|中国株|台湾株|米国株"
)

REQUIRED_FEATURE_MARKERS = {
    "bottleneck-hunter-jp": (
        "6基準", "10年出口テスト", "毎時スキャンモード", "master-map.md",
    ),
    "deep-company-series-jp": (
        "3～8本", "修訂時の7項目", "全回の整合性検査", "連動修訂",
    ),
    "dyp-ask-jp": (
        "しないことの一覧", "能力圏", "企業文化", "平常心",
        "ペルソナと語り口", "実行指示", "禁止事項",
    ),
    "earnings-review-jp": (
        "資料可得性", "親会社株主", "経営者説明", "注記", "データ監査",
    ),
    "earnings-team-jp": (
        "4 Agent", "TeamCreate", "TaskCreate", "team-lead", "Agent 5：編集",
        "Agent 6：読者レビュー", "TaskUpdate", "SendMessage",
        "shutdown_request", "TeamDelete",
    ),
    "era-alpha-jp": (
        "業界認知地図", "三つの核心質問", "五方向", "評価の錨", "転換点",
    ),
    "financial-data-jp": (
        "jpstock_data.py quote", "EDINET_API_KEY", "調整後価格",
        "terminal_value.py", "失敗時の規則",
    ),
    "income-investment-jp": (
        "遮断門", "基準・悪化・深刻", "税務と通貨", "利回り罠", "データ不足",
    ),
    "industry-funnel-jp": (
        "5つの粗選別基準", "最大10社", "4視点", "最大3社",
    ),
    "industry-research-jp": (
        "投資論理チェーン", "利益プール", "AI調査バイアス", "業界意思決定レポート",
    ),
    "investment-checklist-jp": (
        "情報充実度", "六つの門", "鏡テスト", "快速否決", "複数社の比較",
    ),
    "investment-research-jp": (
        "AI調査バイアス", "逆向き思考", "10年終価・IRR", "総合判断",
    ),
    "investment-team-jp": (
        "WebSearch", "TeamCreate", "TaskCreate", "TaskUpdate", "SendMessage",
        "shutdown_request", "8. 総括", "TeamDelete",
    ),
    "management-deep-dive-jp": (
        "4つのAgent", "約束と実績", "資本配分", "側面検証",
        "主要人物が去った場合",
    ),
    "news-pulse-jp": (
        "4つの偵察タスク", "イベント時系列", "主因", "副因", "反証", "TeamDelete",
    ),
    "portfolio-review-jp": (
        "個別保有の健康診断", "共通リスクと相関", "機会費用",
        "ストレステスト", "調整履歴",
    ),
    "private-company-research-jp": (
        "6つのタスク", "単位経済", "退出経路", "技術・知的財産",
        "代替データ信号", "信号整合性", "情報盲区",
    ),
    "quality-screen-jp": (
        "7つの除外基準", "3つの免除規則", "個別／業界／指数／テーマ",
        "境界判断", "データ不足",
    ),
    "thesis-drift-jp": (
        "モードA", "モードB", "モードC", "証拠の正規化",
        "固定5次元", "基準不足",
    ),
    "thesis-tracker-jp": (
        "モードA", "モードB", "200字以内", "核心仮定", "赤線",
        "健康度", "履歴更新",
    ),
    "wechat-article-jp": (
        "TeamCreate", "TaskCreate", "著者Agent", "編集Agent", "読者Agent",
        "TaskUpdate", "SendMessage", "初稿", "最終ファイル",
        "shutdown_request", "TeamDelete",
    ),
}


class TestJapaneseSkills(unittest.TestCase):

    def test_complete_skill_set_exists(self):
        sources = {path.stem for path in (ROOT / "skills").glob("*-jp.md")}
        prompts = {path.stem for path in (ROOT / "codex-prompts").glob("*-jp.md")}
        generated = {
            path.parent.name
            for path in (ROOT / "codex-skills").glob("*-jp/SKILL.md")
        }
        self.assertEqual(sources, CANONICAL)
        self.assertEqual(prompts, CANONICAL)
        self.assertEqual(generated, CANONICAL | {CODEX_ONLY})

    def test_frontmatter_name_matches_folder(self):
        for path in (ROOT / "codex-skills").glob("*-jp/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*(.+)$", text)
            self.assertIsNotNone(match, path)
            self.assertEqual(match.group(1).strip(), path.parent.name, path)

    def test_no_foreign_market_acquisition_instructions(self):
        paths = list((ROOT / "skills").glob("*-jp.md"))
        paths += list((ROOT / "codex-skills").glob("*-jp/SKILL.md"))
        paths += list((ROOT / "codex-prompts").glob("*-jp.md"))
        paths += list((ROOT / "codex-skills").glob("*-jp/agents/openai.yaml"))
        for path in paths:
            match = FORBIDDEN.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(match, f"{path}: forbidden token {match.group(0) if match else ''}")

    def test_internal_skill_references_use_jp_suffix(self):
        for path in (ROOT / "skills").glob("*-jp.md"):
            text = path.read_text(encoding="utf-8")
            for ref in re.findall(r"skills/([a-z0-9-]+)\.md", text):
                self.assertTrue(ref.endswith("-jp"), f"{path}: {ref}")

    def test_required_workflow_features_survive_localization(self):
        self.assertEqual(set(REQUIRED_FEATURE_MARKERS), CANONICAL)
        for name, markers in REQUIRED_FEATURE_MARKERS.items():
            source = ROOT / "skills" / f"{name}.md"
            generated = ROOT / "codex-skills" / name / "SKILL.md"
            for path in (source, generated):
                text = path.read_text(encoding="utf-8")
                for marker in markers:
                    self.assertIn(marker, text, f"{path}: missing {marker}")

    def test_jp_codex_adapter_maps_claude_lifecycle(self):
        text = (
            ROOT / "codex-skills" / "investment-team-jp" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "Claude Code固有インターフェース",
            "TeamCreate", "TaskCreate", "TaskUpdate", "SendMessage",
            "TeamDelete", "shutdown_request", "WebSearch", "Bash",
            "Read", "Write", "サブAgentを利用できない場合",
        ):
            self.assertIn(marker, text)

    def test_codex_only_memo_keeps_full_craft_contract(self):
        text = (
            ROOT / "codex-skills" / CODEX_ONLY / "SKILL.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "中核ワークフロー", "文章基準", "レイアウト基準",
            "既定のレポート構成", "日本株固有の必須判断",
            "品質基準", "他スキルとの連携",
        ):
            self.assertIn(marker, text)

    def test_jp_command_examples_keep_required_flags(self):
        for path in (ROOT / "skills").glob("*-jp.md"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("python ") and "financial_rigor.py" in line:
                    self.assertIn("--locale ja", line, f"{path}: {line}")
                if line.startswith("python ") and "report_audit.py" in line:
                    self.assertIn("--locale ja", line, f"{path}: {line}")
                    self.assertIn("--market jp", line, f"{path}: {line}")
                    self.assertIn("--report", line, f"{path}: {line}")
                    if " verdict " in line:
                        self.assertIn("--results", line, f"{path}: {line}")
                if (
                    line.startswith("python ")
                    and "terminal_value.py" in line
                    and " audit " in line
                ):
                    self.assertIn("--locale ja", line, f"{path}: {line}")
                    self.assertIn("--currency JPY", line, f"{path}: {line}")
                    self.assertIn("--rf", line, f"{path}: {line}")


if __name__ == "__main__":
    unittest.main()
