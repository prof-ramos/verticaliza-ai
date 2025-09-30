# Repository Guidelines

## Project Structure & Modules
- Root entrypoint: `main.py` (orchestrates processing via `EditalProcessor`).
- Source code: `src/`
  - `extractors/` (PDF text + URL handling)
  - `processors/` (LLM client, prompt templates)
  - `database/` (Supabase models and client)
  - `utils/` (logging, hashing)
  - `exporters/` (CSV export – WIP)
- Data and ops: `input_pdfs/`, `migrations/`, `logs/`, `supabase/`.
- Config: `.env` (use `.env.example` as reference), `requirements.txt`, `pyproject.toml`.

## Build, Test, and Dev Commands
- Create venv: `uv venv && source .venv/bin/activate` (or `python -m venv .venv`).
- Install deps: `uv pip install -r requirements.txt` (or `pip install -r requirements.txt`).
- Run app: `python main.py` (uses `.env`).
- Lint/format (recommended): `ruff check .`, `ruff format .` (add if not installed).
- Type check (optional): `mypy src` (if mypy is added).

## Coding Style & Naming
- Python 3.10+; 4‑space indentation; UTF‑8; max line ~100.
- Prefer type hints on public functions and dataclasses in `src/database/models.py`.
- Docstrings: Google style; logs and comments in pt‑BR.
- Modules: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Keep side‑effects out of imports; pure functions in `utils/` when feasible.

## Testing Guidelines
- Framework: pytest (add `pytest` to `requirements.txt` if missing).
- Test layout: `tests/` mirroring `src/` (e.g., `tests/processors/test_llm_client.py`).
- Naming: files start with `test_`, functions `test_...`.
- Run: `pytest -q`; aim for coverage on critical paths (hashing, parsing, DB I/O).

## Commit & Pull Requests
- Commits: imperative present and scoped prefix when helpful
  - Examples: `feat(processors): add LLM fallback metrics`, `fix(db): handle null dates`.
- PRs must include: clear description, motivation/approach, screenshots/logs when applicable, and linked issues.
- Keep PRs small and focused; include migration notes if DB schema changes.

## Security & Configuration
- Never commit secrets; use `.env` and keep `.env.example` updated.
- Minimal required envs: `OPENROUTER_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.
- Validate external inputs (PDF paths/URLs). Log errors with context via `src/utils/logger.py`.

## Architecture Notes
- Processing flow: extract -> LLM metadata -> LLM verticalization -> parse -> persist.
- Supabase is the source of truth; dedup via SHA‑256 in `utils/file_hash.py`.
- LLM client implements fallback; keep prompts centralized in `processors/prompt_templates.py`.
