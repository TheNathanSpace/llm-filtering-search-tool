# LLM Agent Instructions

Read this file and `README.md` before acting.

## Back-End

This is a Python project under a Linux filesystem.

- A virtual environment already exists in the project under `.venv`.
- Activate the virtual environment before running Python commands. (`source .venv/bin/activate`)

## Front-End

This version of Next.js has breaking changes! APIs, conventions, and file structure may all differ from your training
data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation
notices.

- Ensure you are using the latest MUI version by reading the relevant documentation in:
  - <https://mui.com/material-ui/llms.txt>
  - <https://mui.com/x/llms.txt>

## Docker (WSL)

When running in WSL, execute Docker CLI commands outside the Cursor Shell sandbox
(`required_permissions: ["all"]`). See `.cursor/rules/wsl-docker-outside-sandbox.mdc`.

## Implementation Guidelines

- Make small, targeted changes instead of building for hypothetical future needs.
- If something is unclear, ask before making assumptions.
- Place temporary tests in `tmp_tests/`. Ensure you create and remove this directory when done.
- Ensure you are running Linux commands, not Windows commands.
- Your code needs to be well-designed, well-implemented, and professional grade.
- Do everything now, with no incremental migration, and no concern of backwards compatibility.
- Reduce the risk of regressions or bad behavior due to poor design of the internals.
- Professionally use object-oriented programming patterns. (ABSOLUTELY NO spaghetti code. DO NOT overcomplicate things.)
- You are free to do whatever is necessary to achieve these goals.
- Prioritize a strong, useful common library of shared patters and components that can be reused across the project.
