#!/usr/bin/env python3
"""Fail if a staged change adds/edits a gorushi def or class with no docstring.

Pre-existing undocumented code is left alone; only definition lines that are
part of the staged diff are required to have a docstring. Run via the
`gorushi-docstrings` pre-commit hook.
"""

import json
import subprocess
import sys

DOCSTRING_RULES = ["D100", "D101", "D102", "D103", "D104", "D106"]


def staged_content(path: str) -> str | None:
    """Return the staged (index) contents of path, or None if not staged."""
    result = subprocess.run(
        ["git", "show", f":{path}"], capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout


def added_lines(path: str) -> set[int]:
    """Return the line numbers path's staged diff adds or modifies."""
    diff = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    lines: set[int] = set()
    for line in diff.splitlines():
        if not line.startswith("@@"):
            continue
        new_range = line.split("+", 1)[1].split(" ", 1)[0]
        if "," in new_range:
            start, count = (int(part) for part in new_range.split(","))
        else:
            start, count = int(new_range), 1
        if count:
            lines.update(range(start, start + count))
    return lines


def missing_docstrings(path: str, content: str) -> list[dict]:
    """Return ruff's docstring-rule violations for content as path."""
    result = subprocess.run(
        [
            "ruff",
            "check",
            "--select",
            ",".join(DOCSTRING_RULES),
            "--output-format",
            "json",
            "--stdin-filename",
            path,
            "-",
        ],
        input=content,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return []
    return json.loads(result.stdout)


def check_file(path: str) -> list[str]:
    """Return docstring problems for path introduced by the staged diff."""
    content = staged_content(path)
    if content is None:
        return []
    changed = added_lines(path)
    problems = []
    for violation in missing_docstrings(path, content):
        row = violation["location"]["row"]
        if row in changed:
            code, message = violation["code"], violation["message"]
            problems.append(f"{path}:{row}: {code} {message}")
    return problems


def main() -> int:
    """Check every staged .py path given on argv for new missing docstrings."""
    problems = []
    for path in sys.argv[1:]:
        if path.endswith(".py"):
            problems.extend(check_file(path))

    if problems:
        print(
            "Missing docstrings on new/changed definitions:", file=sys.stderr
        )
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
