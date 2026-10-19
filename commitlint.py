from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, List, Optional, Sequence, Tuple


CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z0-9]+)"
    r"(?:\((?P<scope>[^\)]+)\))?"
    r"(?P<breaking>!?)"
    r":\s*(?P<description>.+)$"
)

# Used for final validation; matches allowed type characters.
TYPE_RE = re.compile(r"^[a-zA-Z0-9]+$")

# Long subject length threshold commonly used in projects.
DEFAULT_SUBJECT_MAX = 72
DEFAULT_TYPES = ("feat", "fix", "docs", "refactor", "test", "chore")


@dataclass
class Issue:
    code: str
    message: str
    line: int
    start: int = 0
    end: int = 0


@dataclass
class CommitFile:
    path: str
    content: str
    issues: List[Issue] = field(default_factory=list)


def _normalize_issue_message(line: str, index: int) -> str:
    try:
        return line.rstrip("\n")
    except Exception:
        return line


def _split_commit_message(text: str) -> Tuple[str, List[str]]:
    lines = text.splitlines()
    if not lines:
        return "", []
    subject = lines[0]
    body = lines[1:]
    return subject, body


def _subject_issues(subject: str, allowed_types: set) -> List[Issue]:
    issues: List[Issue] = []
    if not subject.strip():
        issues.append(Issue(code="CL001", message="Empty subject", line=1))
        return issues

    match = CONVENTIONAL_RE.match(subject)
    if not match or not TYPE_RE.match(match.group("type") or ""):
        issues.append(
            Issue(code="CL002", message="Subject does not match conventional-commits format", line=1)
        )
    elif match.group("type") not in allowed_types:
        issues.append(
            Issue(code="CL005", message=f"Type '{match.group('type')}' is not allowed", line=1)
        )
    if len(subject) > DEFAULT_SUBJECT_MAX:
        issues.append(
            Issue(code="CL003", message=f"Subject exceeds {DEFAULT_SUBJECT_MAX} characters", line=1)
        )
    if subject.endswith("."):
        issues.append(
            Issue(code="CL004", message="Subject should not end with a period", line=1)
        )
    return issues


def _body_issues(body: List[str], subject: str) -> List[Issue]:
    issues: List[Issue] = []
    in_body = False
    for idx, line in enumerate(body, start=2):
        if not in_body:
            if line.strip() == "":
                continue
            in_body = True
        if in_body:
            if len(line.rstrip("\n")) > 100:
                issues.append(
                    Issue(code="CL004", message="Body line exceeds 100 characters", line=idx)
                )
    return issues


def lint_commit(text: str, allowed_types: Optional[set] = None) -> List[Issue]:
    if allowed_types is None:
        allowed_types = set(DEFAULT_TYPES)
    subject, body = _split_commit_message(text)
    issues = _subject_issues(subject, allowed_types)
    issues.extend(_body_issues(body, subject))
    return issues


def format_report(issues: Sequence[Issue], path: str = "<stdin>") -> str:
    if not issues:
        return f"{path}: OK\n"
    lines = [f"{path}:"]
    for issue in issues:
        lines.append(f"  line {issue.line}: {issue.code} - {issue.message}")
    return "\n".join(lines) + "\n"


def load_config(root: "os.PathLike[str] | str | None" = None) -> Tuple[set, Optional[int]]:
    if root is None:
        root = os.getcwd()
    config_path = Path(root) / ".commitlintrc.json"
    allowed_types = set(DEFAULT_TYPES)
    subject_max = DEFAULT_SUBJECT_MAX
    if not config_path.exists():
        return allowed_types, subject_max
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return allowed_types, subject_max
    if isinstance(data.get("types"), list):
        allowed_types = {str(item) for item in data["types"] if item}
    if isinstance(data.get("subjectMax"), int) and data["subjectMax"] > 0:
        subject_max = data["subjectMax"]
    return allowed_types, subject_max


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="commitlint",
        description="Lint git commit messages against conventional-commits style.",
    )
    parser.add_argument("path", nargs="?", help="Commit message file path")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read commit message from stdin instead of a file",
    )
    parser.add_argument(
        "--types",
        nargs="*",
        default=None,
        help="Allowed types. Defaults to built-in conventional set.",
    )
    parser.add_argument(
        "--subject-max",
        type=int,
        default=None,
        help="Maximum subject length",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit issues as JSON",
    )
    return parser.parse_args(argv)


def _read_input(path: Optional[str], stdin: IO[str], force_stdin: bool) -> Tuple[str, str]:
    if path:
        text = Path(path).read_text(encoding="utf-8")
        return path, text
    if force_stdin or not sys.stdin.isatty():
        text = stdin.read()
        return "<stdin>", text
    return "<stdin>", stdin.read()


def main(argv: Optional[Sequence[str]] = None, stdin: Optional[IO[str]] = None) -> int:
    args = parse_args(argv)
    source = stdin if stdin is not None else sys.stdin

    load_config()  # keep config lookup side-effect; args overrides are not used by this linter

    try:
        display_path, text = _read_input(args.path, source, args.stdin)
    except OSError as exc:
        print(f"commitlint: failed to read input: {exc}", file=sys.stderr)
        return 1

    issues = lint_commit(text)
    if args.json:
        payload = [
            {"code": issue.code, "message": issue.message, "line": issue.line}
            for issue in issues
        ]
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(issues, display_path), end="")
    return 1 if issues else 0


__all__ = [
    "CONVENTIONAL_RE",
    "Issue",
    "CommitFile",
    "lint_commit",
    "format_report",
    "load_config",
    "parse_args",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
