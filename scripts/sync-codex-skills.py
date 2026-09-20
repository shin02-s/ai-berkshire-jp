#!/usr/bin/env python3
"""Generate Codex skills from AI Berkshire Claude command files."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILLS = ROOT / "skills"
CODEX_SKILLS = ROOT / "codex-skills"


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :].lstrip("\n")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def metadata_for(name: str, source_name: str, source_text: str) -> str:
    is_jp = name.endswith("-jp")
    existing, body = split_frontmatter(source_text)
    if existing:
        has_name = re.search(r"(?m)^name:\s*", existing) is not None
        has_description = re.search(r"(?m)^description:\s*", existing) is not None
        lines = []
        if not has_name:
            lines.append(f"name: {name}")
        if not has_description:
            title = first_heading(body, name)
            description = (
                f"AI Berkshire 日本株スキル: {title}。生成元: skills/{source_name}。"
                if is_jp
                else f"AI Berkshire skill: {title}. Source: skills/{source_name}."
            )
            lines.append(
                "description: "
                + yaml_quote(description)
            )
        lines.append(existing.rstrip())
        return "---\n" + "\n".join(lines) + "\n---\n\n"

    title = first_heading(source_text, name)
    description = (
        f"AI Berkshire 日本株スキル: {title}。生成元: skills/{source_name}。"
        if is_jp
        else f"AI Berkshire skill: {title}. Source: skills/{source_name}."
    )
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {yaml_quote(description)}\n"
        "---\n\n"
    )


def codex_body(name: str, source_name: str, source_text: str) -> str:
    _, body = split_frontmatter(source_text)
    if name.endswith("-jp"):
        note = (
            "## Codexアダプター注記\n\n"
            f"このスキルは `skills/{source_name}` から生成され、Claude Code とCodexで正本を共有する。\n\n"
            "- `$ARGUMENTS` は現在のCodexタスクにおけるユーザー依頼として扱う。\n"
            "- ソース中のClaude Code固有インターフェースは機能を落とさず、現在のセッションで最も近いCodex機能へ読み替える。"
            "`TeamCreate` は利用可能なサブAgentによるチーム編成、`TaskCreate` は境界の明確な担当割当、"
            "`TaskUpdate` は進捗・完了状態の追跡、`SendMessage` はAgent間の追加指示・結果回収、"
            "`TeamDelete` と `shutdown_request` は全結果回収後の終了・整理として扱う。\n"
            "- `Task` / `Agent` は利用可能なサブAgent、`WebSearch` はWeb検索、`Bash` はシェル、"
            "`Read` / `Write` は通常のファイル読取・編集へ読み替える。サブAgentを利用できない場合は、"
            "同じ役割と検証順序を主タスクで逐次実行し、未実施の並行調査を装わない。\n"
            "- 共通ツールはリポジトリ直下から実行し、日本版では `--locale ja`、"
            "必要に応じて `--market jp` / `--currency JPY` を付ける。\n"
            "- 調査前に `date` で当日を確認し、データ基準日をレポート冒頭に記載する。\n"
            "- `AGENTS.md` の品質規則に従い、財務数値の照合、正確な計算、欠損と不確実性を明示する。\n\n"
        )
    else:
        note = (
            "## Codex adapter note\n\n"
            f"This skill is generated from `skills/{source_name}` so Claude Code "
            "and Codex users share one canonical workflow.\n\n"
            "- Treat `$ARGUMENTS` as the user's request in the current Codex thread.\n"
            "- When the source mentions Claude-only surfaces such as Task, Agent, "
            "WebSearch, Bash, Read, or Write, use the closest Codex capability "
            "available in this session: subagents when available, web search when "
            "needed, shell commands for local tools, and normal file edits for "
            "workspace files.\n"
            "- Use shared project tools from `tools/` in this repository. Prefer "
            "running commands from the repository root with paths like "
            "`python3 tools/financial_rigor.py ...`; if the current thread starts "
            "outside the repo, locate the actual checkout path first instead of "
            "assuming a fixed home-directory path.\n"
            "- Before starting research, run the `date` command to confirm "
            "today's date; treat it as the baseline for \"latest\" data and state "
            "the data cutoff date in the report header. Never assume the current "
            "date from training data.\n"
            "- Preserve the research quality rules from `AGENTS.md`: cross-check "
            "financial data, use exact arithmetic tools for valuation/math, and "
            "clearly label uncertainty and source gaps.\n\n"
        )
    return note + body.rstrip() + "\n"


def main() -> None:
    check = "--check" in sys.argv[1:]
    unknown_args = [arg for arg in sys.argv[1:] if arg != "--check"]
    if unknown_args:
        joined = ", ".join(unknown_args)
        raise SystemExit(f"Unknown argument(s): {joined}")

    if not check:
        CODEX_SKILLS.mkdir(exist_ok=True)

    count = 0
    stale: list[str] = []
    for source in sorted(CLAUDE_SKILLS.glob("*.md")):
        name = source.stem
        source_text = source.read_text(encoding="utf-8")
        target_dir = CODEX_SKILLS / name
        target = target_dir / "SKILL.md"
        content = metadata_for(name, source.name, source_text) + codex_body(
            name, source.name, source_text
        )
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(str(target.relative_to(ROOT)))
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        count += 1

    if check:
        if stale:
            print("Codex skills are out of date:")
            for path in stale:
                print(f"  {path}")
            raise SystemExit(1)
        print(f"Checked {count} Codex skills in {CODEX_SKILLS.relative_to(ROOT)}")
        return

    print(f"Generated {count} Codex skills in {CODEX_SKILLS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
