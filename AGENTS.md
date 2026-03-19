# AGENTS.md - GenericSuite Agent Guidelines

This file contains guidelines for AI agents working within the GenericSuite repository.

## Purpose

To provide a consistent framework for agent behavior when interacting with this codebase, including coding standards, testing practices, and documentation expectations.

## Agent Behavior

### 1. Code Changes
- Follow the existing code style (PEP 8 for Python, with project-specific exceptions noted in `.flake8` or `pyproject.toml`).
- Ensure all new code is covered by unit tests where applicable.
- Update documentation (docstrings, README, or dedicated docs) when changing public APIs.
- Run the test suite before submitting changes: `make test` or `pytest`.

### 2. Branching and Commits
- Create descriptive branch names (e.g., `feat/`, `fix/`, `refactor/`).
- Write clear, conventional commit messages:
  - `feat: add new authentication provider`
  - `fix: resolve email sending bug in production`
  - `docs: update installation instructions`
- Keep commits atomic and focused on a single change.

### 3. Issue and PR Etiquette
- Reference related issues in commit messages and PR descriptions (e.g., `Closes #123`).
- Ensure PRs pass all CI checks before requesting review.
- Be responsive to reviewer feedback and iterate promptly.
- Squash commits when merging if the branch contains many small fixes.

### 4. Testing
- Unit tests live in the `tests/` directory.
- Aim for high test coverage, especially for core utilities and backend logic.
- Use fixtures and mocks appropriately to isolate units.
- Run tests with coverage: `make coverage` or `pytest --cov=genericsuite`.

### 5. Documentation
- Inline docstrings should follow Google or NumPy style.
- User-facing documentation lives in the `docs/` directory or the project website.
- Update changelog (`CHANGELOG.md`) for notable changes.

### 6. Environment Setup
- Development dependencies are managed via Poetry.
- Install with: `poetry install`
- Activate shell: `poetry shell`
- Pre-commit hooks are available; install with: `pre-commit install`

## Agent-Specific Notes

When operating as an agent in this repository:
- You may use the `skill-creator` to develop or improve agent skills if needed.
- For web searches or fetching external info, use the provided web tools.
- Always verify any generated code against existing patterns.
- When in doubt, consult the README or existing similar files.

Remember: The goal is to augment the project maintainably, not to introduce inconsistency or technical debt.
