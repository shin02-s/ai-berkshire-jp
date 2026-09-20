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


if __name__ == "__main__":
    unittest.main()
