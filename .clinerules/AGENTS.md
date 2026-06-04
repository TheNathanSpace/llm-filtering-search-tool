# LLM Agent Instructions

Read this file and `README.md` before acting.

## Back-End

This is a Python project under a Linux filesystem.

- A virtual environment already exists in the project under `.venv`.
- Activate the virtual environment before running Python commands. (`source .venv/bin/activate`)

## Implementation Guidelines

- Make small, targeted changes instead of building for hypothetical future needs.
- If something is unclear, ask before making assumptions.
- Place temporary tests in `tmp_tests/`. Ensure you create and remove this directory when done.
- Ensure you are running Linux commands, NOT Windows commands.
- Make sure to exclude directories called `.venv` or `node_modules` from terminal commands like `ls -R` or similar.
  Their output will be way too long. Use `ls -R --hide node_modules --hide .venv`.

## Front-End

This version of Next.js has breaking changes! APIs, conventions, and file structure may all differ from your training
data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation
notices.

- Ensure you are using the latest MUI version by reading the relevant documentation in:
  - <https://mui.com/material-ui/llms.txt>
  - <https://mui.com/x/llms.txt>
