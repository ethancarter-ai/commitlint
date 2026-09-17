from __future__ import annotations

import io
from pathlib import Path

from commitlint import CONVENTIONAL_RE, lint_commit, load_config, main


def test_valid_commit_passes():
    assert lint_commit("feat(app): add login page") == []


def test_invalid_type_reported():
    issues = lint_commit("bad commit message")
    assert any(issue.code == "CL002" for issue in issues)


def test_broken_description_reported():
    issues = lint_commit("fix")
    assert any(issue.code == "CL002" for issue in issues)


def test_subject_length_threshold():
    long_subject = "feat(app): " + "a" * 80
    issues = lint_commit(long_subject)
    assert any(issue.code == "CL003" for issue in issues)


def test_body_line_length_reported():
    body = "fix: auth bug\n" + "a" * 120
    issues = lint_commit(body)
    assert any(issue.code == "CL004" for issue in issues)


def test_regex_matches_basic():
    match = CONVENTIONAL_RE.match("feat(app)!: add feature")
    assert match is not None
    assert match.group("type") == "feat"
    assert match.group("scope") == "app"
    assert match.group("breaking") == "!"


def test_regex_matches_no_scope():
    match = CONVENTIONAL_RE.match("chore: cleanup")
    assert match is not None
    assert match.group("scope") is None


def test_load_config_reads_types():
    root = Path("/tmp/fake-commitlint-config")
    root.mkdir(parents=True, exist_ok=True)
    (root / ".commitlintrc.json").write_text(
        '{"types": ["release", "revert"], "subjectMax": 50}', encoding="utf-8"
    )
    allowed_types, subject_max = load_config(root)
    assert allowed_types == {"release", "revert"}
    assert subject_max == 50


def test_main_from_file_returns_zero_on_valid_commit(tmp_path: Path):
    message = tmp_path / "commit-msg"
    message.write_text("feat: ok\n", encoding="utf-8")
    assert main([str(message)]) == 0


def test_main_stdin_returns_zero_on_valid_commit():
    stdin = io.StringIO("feat: ok from stdin\n")
    assert main(["--stdin"], stdin=stdin) == 0


def test_main_json_output_contains_issues(tmp_path: Path):
    message = tmp_path / "commit-msg"
    message.write_text("bad commit message\n", encoding="utf-8")
    stdin = io.StringIO()
    main([str(message), "--json"], stdin=stdin)
