# Contributing to FOSDEM Explorer

## Getting Started

1. Fork the repository
2. Clone your fork and create a branch:
   ```bash
   git clone https://github.com/HenryPenton/fosdem-explorer.git
   git checkout -b feat/your-feature
   ```
3. Install dev dependencies (creates a virtualenv automatically):
   ```bash
   make dev
   ```

## Code Standards

- **Python 3.11+** — use modern syntax (`X | Y` unions, `match`, etc.)
- **Type annotations** required on all public functions and methods
- **Strict mypy** — do not add `# type: ignore` without an explanatory comment
- **ruff** handles linting and formatting (`line-length = 100`)
- Run `make lint` and `make test` before pushing

## Commit Messages

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) spec.
The `commit-msg` pre-commit hook enforces this. Use `make commit` for an interactive prompt.

## Pull Request Process

1. Open a PR against `main`
2. Ensure all CI checks pass (`make lint` and `make test`)
3. One approving review required before merge
4. Do not use `--no-verify` to bypass pre-commit hooks
