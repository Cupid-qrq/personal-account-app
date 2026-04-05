---
name: iteration-workflow
description: "Use when managing this ledger project iteration workflow: analyze current code first, implement focused fixes or upgrades, validate with syntax/data checks, update README/docs/context/memory, and push the release to the connected GitHub repo. Trigger for v0.x -> v1.0 release planning, bug fixing, UI/analytics improvements, and repository packaging."
---

# Iteration Workflow Skill

## Purpose
Use this skill when working on the ledger project to keep each iteration consistent, release-ready, and documented.

## When to Use
- Fixing bugs in `src/ui_app.py`, `src/analytics.py`, or `src/data_pipeline.py`
- Adding UI/visual improvements or monthly analysis features
- Packaging a release version
- Updating README, docs, context compression, and repo memory
- Preparing a commit and push for Streamlit Cloud deployment

## Operating Rules
1. Inspect the current code and data state before editing.
2. Prefer root-cause fixes over surface patches.
3. Keep changes minimal and aligned with existing style.
4. After edits, run validation:
   - syntax checks
   - data sanity checks if data files changed
   - error scan for edited files
5. Update release notes and context docs when behavior changes.
6. Keep root directory clean:
   - do not restore legacy root sample files (`2026.csv`, `2026-04.csv`, `context_v0.6.txt`, root `项目需求.md`)
   - keep baseline assets in `data/origin/`
7. Keep README external-facing only:
   - keep sections minimal: main features, tech stack, deployment, quick start, license
   - remove local run details that are not essential for external readers
   - avoid internal debugging notes, internal changelog details, and credentials
8. For medium/large feature updates, README and `.gitignore` must be reviewed and updated in the same iteration:
   - README reflects current architecture and user-facing behavior
   - `.gitignore` hides non-essential local/debug/intermediate files from repository surface
9. Keep project memory updated with durable facts:
   - workflow rules
   - stable conventions
   - release status
10. Finalize by committing and pushing to the connected GitHub repo.
11. If Streamlit Cloud is connected, verify redeploy after push.

## Standard Iteration Flow
### 1. Analyze
- Read the affected files.
- Check current repo status and identify the smallest safe fix.
- Confirm whether file deletions are intentional and part of workspace cleanup.

### 2. Implement
- Edit only the files needed for the iteration.
- Prefer modular changes in `src/` and keep `app.py` as thin entrypoint only.

### 3. Validate
- Run syntax checks.
- Verify data import/archiving paths if CSV logic changed.
- Confirm the app still loads and key views still render.
- Ensure deleted legacy files are not unintentionally reintroduced.

### 4. Document
- Update `README.md` if user-facing behavior changes.
- For medium/large iterations, check and update `.gitignore` to keep repo surface clean.
- Update `docs/迭代日志.md` for version history.
- Update `docs/context_compact.md` for compressed project state.

### 5. Persist
- Update repo memory with durable workflow or architecture facts.
- Commit and push `main` after validation.

## Project Conventions
- `app.py` is a thin startup wrapper that imports `src/ui_app.py`.
- `src/ui_app.py` owns Streamlit page composition and interaction.
- `src/data_pipeline.py` owns import, normalization, archiving, and master-table merge logic.
- `src/sqlite_store.py` owns SQLite master persistence.
- `src/data_contract.py` is the single source of truth for canonical schema.
- `src/analytics.py` owns aggregation and insight calculations.
- Keep baseline raw assets under `data/origin/`.
- Keep CSV archives under `data/archive/` and processed snapshots under `data/processed/`.
- Keep external documentation concise and user-facing.

## Release Checklist
- [ ] Code validated
- [ ] Data paths verified
- [ ] README updated for external audience
- [ ] Iteration log updated
- [ ] Context compact updated
- [ ] Repo memory updated
- [ ] Commit created
- [ ] Push completed
- [ ] Streamlit Cloud redeploy checked

## Trigger Style
When asked to continue this project, assume the workflow above unless the user says otherwise.
