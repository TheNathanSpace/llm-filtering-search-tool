# LLM Agent Instructions

Read this file and `README.md` before acting.

## Environment

This is a Python project under a Linux filesystem.

- A virtual environment already exists in the project under `.venv`.
- Activate the virtual environment before running Python commands. (`source .venv/bin/activate`)
- When running multiple commands, prefer to run each command individually. Avoid chaining commands using `;`, `&&`, or
  `|`.
- Ensure you are running Linux commands, NOT Windows commands.

## Implementation Guidelines

- Make small, targeted changes instead of building for hypothetical future needs.
- If something is unclear, ask before making assumptions.
- Place temporary tests in `tmp_tests/`. Ensure you create and remove this directory when done.
