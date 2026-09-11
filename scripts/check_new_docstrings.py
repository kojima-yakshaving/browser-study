#!/usr/bin/env python3
"""Fail if a staged gorushi change lacks or misdescribes a docstring.

Checks two things, both scoped to definition lines the staged diff actually
touches so pre-existing undocumented/stale code is left alone:

- ruff's D-rules: the definition has a docstring at all.
- pydoclint: if it has one, its Args/Returns/Raises match the signature.

Run via the `gorushi-docstrings` pre-commit hook.
"""

import json
import re
import subprocess
import sys

DOCSTRING_RULES = ["D100", "D101", "D102", "D103", "D104", "D106"]
PYDOCLINT_LINE_RE = re.compile(r"^\s+(\d+): (DOC\d+): (.*)$")


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


def mismatched_docstrings(path: str) -> list[tuple[int, str, str]]:
    """Return pydoclint's docstring-content violations for path.

    pydoclint has no stdin mode, so this reads path off disk. That's safe
    under pre-commit, which stashes unstaged changes before running hooks,
    so the working tree matches the staged content while this runs.
    """
    result = subprocess.run(
        ["pydoclint", "-q", path], capture_output=True, text=True
    )
    violations = []
    for line in (result.stdout + result.stderr).splitlines():
        match = PYDOCLINT_LINE_RE.match(line)
        if match:
            row, code, message = match.groups()
            violations.append((int(row), code, message))
    return violations


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
    for row, code, message in mismatched_docstrings(path):
        if row in changed:
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
