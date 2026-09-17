# commitlint

A minimal Python linter for git commit messages. It checks against the conventional-commits pattern and reports issues for subject format, length, punctuation, and body width.

## About

Small developer tooling matters: bad commit messages slow down `git blame`, changelogs, and release automation. `commitlint` focuses on the highest-signal checks with zero external dependencies.

## Features

- Conventional-commits subject validation
- Subject length and trailing-period checks
- Body line-width reporting
- Configurable allowed types and subject max length
- JSON and human-readable output

## Installation

```bash
python -m pip install .
```

## Usage

```bash
commitlint --help
commitlint
commitlint .git/COMMIT_EDITMSG
commitlint --stdin
commitlint --types feat fix chore --subject-max 80 --json
```

## Configuration

Create a `.commitlintrc.json` at the repository root:

```json
{
  "types": ["feat", "fix", "docs", "refactor", "test", "chore"],
  "subjectMax": 72
}
```

## Tags

git commitlint conventional-commits developer-tools
