#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


STATUS_ORDER = {
    "[~] In Progress": 0,
    "[ ] Todo": 1,
    "[x] Done": 2,
}


@dataclass
class TaskSummary:
    task_id: str
    name: str
    epic: str
    status: str
    short_description: str
    source_file: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize backlog task files into a compact board."
    )
    parser.add_argument(
        "--backlog-dir",
        default="backlog",
        help="Backlog directory containing task markdown files.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--write-board",
        action="store_true",
        help="Write backlog/board.md with current task summaries.",
    )
    return parser.parse_args()


def read_front_matter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return {}

    end_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx == -1:
        return {}

    data: dict[str, str] = {}
    for raw in lines[1:end_idx]:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        data[key.strip().lower()] = value.strip().strip('"').strip("'")
    return data


def extract_markdown_title(text: str) -> tuple[str, str]:
    match = re.search(r"^#\s+([A-Z]+-\d+)\s+-\s+(.+)$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "UNKNOWN", "Unknown task"


def extract_markdown_field(text: str, label: str) -> str:
    pattern = rf"^- {re.escape(label)}:\s*(.+)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def extract_description(text: str) -> str:
    match = re.search(
        r"^##\s+Description\s*$\n+(.+?)(?:\n##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""

    block = match.group(1)
    for line in block.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("- "):
            continue
        return clean
    return ""


def shorten_summary(text: str, max_len: int = 160) -> str:
    clean = " ".join(text.split())
    if not clean:
        return "No short description available."

    first_sentence = clean.split(". ", 1)[0].strip()
    if first_sentence.endswith(":"):
        first_sentence = first_sentence[:-1].strip()
    if first_sentence:
        clean = first_sentence

    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3].rstrip() + "..."


def normalize_status(raw: str) -> str:
    val = raw.strip()
    if val in STATUS_ORDER:
        return val

    low = val.lower()
    if "progress" in low:
        return "[~] In Progress"
    if "done" in low:
        return "[x] Done"
    if "todo" in low:
        return "[ ] Todo"
    return "[ ] Todo"


def parse_task_file(path: Path) -> TaskSummary:
    text = path.read_text(encoding="utf-8")
    front = read_front_matter(text)
    fallback_task_id, fallback_name = extract_markdown_title(text)
    task_id = front.get("id", fallback_task_id)
    name = front.get("name", fallback_name)
    epic = front.get("epic", extract_markdown_field(text, "Epic")) or "Unknown epic"
    status = normalize_status(
        front.get("status", extract_markdown_field(text, "Status"))
    )
    short_description = front.get("summary", extract_description(text))

    short_description = shorten_summary(short_description)

    return TaskSummary(
        task_id=task_id,
        name=name,
        epic=epic,
        status=status,
        short_description=short_description,
        source_file=str(path),
    )


def task_sort_key(task: TaskSummary) -> tuple[str, int, str]:
    return (task.epic, STATUS_ORDER.get(task.status, 99), task.task_id)


def discover_tasks(backlog_dir: Path) -> list[TaskSummary]:
    files: Iterable[Path] = sorted(backlog_dir.glob("*.md"))
    tasks: list[TaskSummary] = []
    for file_path in files:
        if file_path.name.lower() == "board.md":
            continue
        tasks.append(parse_task_file(file_path))
    return sorted(tasks, key=task_sort_key)


def render_markdown(tasks: list[TaskSummary], backlog_dir: Path) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Backlog Board",
        "",
        f"_Generated from `{backlog_dir}` on {timestamp}_",
        "",
        "Status legend: `[ ] Todo`, `[~] In Progress`, `[x] Done`",
        "",
        "| Task | Epic | Status | Short Description |",
        "|------|------|--------|-------------------|",
    ]
    for task in tasks:
        lines.append(
            f"| {task.task_id} - {task.name} | {task.epic} | {task.status} | {task.short_description} |"
        )
    lines.extend(
        [
            "",
            "## Usage",
            "",
            "```bash",
            "python3 scripts/backlog_board.py",
            "python3 scripts/backlog_board.py --format json",
            "python3 scripts/backlog_board.py --write-board",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def render_json(tasks: list[TaskSummary]) -> str:
    payload = [asdict(task) for task in tasks]
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def main() -> int:
    args = parse_args()
    backlog_dir = Path(args.backlog_dir).resolve()
    tasks = discover_tasks(backlog_dir)

    if args.format == "json":
        output = render_json(tasks)
    else:
        output = render_markdown(tasks, backlog_dir)

    print(output, end="")

    if args.write_board:
        board_path = backlog_dir / "board.md"
        board_path.write_text(render_markdown(tasks, backlog_dir), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
