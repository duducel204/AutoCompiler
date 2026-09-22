from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ROADMAP = ROOT / "data" / "roadmap.csv"
START = "<!-- ROADMAP_TABLE_START -->"
END = "<!-- ROADMAP_TABLE_END -->"

STATUS_ICON = {
    "implemented": "✅",
    "documented": "✅",
    "draft": "🟡",
    "planned": "⬜",
    "explore": "🔬",
    "blocked": "⛔",
}


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def build_table() -> str:
    with ROADMAP.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    lines = [
        "| ID | Phase | Component | Status | Priority | Complexity | Goal |",
        "|---|---|---|---|---:|---:|---|",
    ]

    for row in rows:
        status = row["status"].strip().lower()
        icon = STATUS_ICON.get(status, "•")
        lines.append(
            "| {id} | {phase} | {component} | {icon} {status} | {priority} | {complexity}/10 | {goal} |".format(
                id=esc(row["id"]),
                phase=esc(row["phase"]),
                component=esc(row["component"]),
                icon=icon,
                status=esc(row["status"]),
                priority=esc(row["priority"]),
                complexity=esc(row["complexity"]),
                goal=esc(row["goal"]),
            )
        )

    counts = {}
    for row in rows:
        key = row["status"].strip().lower()
        counts[key] = counts.get(key, 0) + 1

    completed = counts.get("implemented", 0) + counts.get("documented", 0)
    pct = round((completed / len(rows)) * 100) if rows else 0

    summary = [
        "",
        f"**Tracked items:** {len(rows)} · **Completed/documented:** {completed} · **Progress:** {pct}%",
        "",
        "_Source: `data/roadmap.csv` · Generated automatically. Do not edit this table by hand._",
    ]
    return "\n".join(lines + summary)


def main() -> None:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README markers not found")

    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    generated = f"{START}\n{build_table()}\n{END}"
    README.write_text(before + generated + after, encoding="utf-8")


if __name__ == "__main__":
    main()
