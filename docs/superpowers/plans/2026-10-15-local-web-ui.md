# CMS Guard Lite Local Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a localhost-only FastAPI service and a separate Vue UI that run CMS checks, demos, benchmarks, reports, and persistent sanitized history from one local command.

**Architecture:** Keep all security decisions and HTTP checks in the existing `cms_guard` package. Add `cms_guard_api` as a thin validated orchestration and SQLite layer, and build `MKARTEX-UI` as a separate Vue 3 application whose production assets are copied into `web_dist/`.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, stdlib SQLite, Vue 3, TypeScript, Vite, Pinia, Vue Router, Vitest, Vue Test Utils.

**Spec:** `docs/superpowers/specs/2026-10-15-local-web-ui-design.md`

## Global Constraints

- Bind the production API to `127.0.0.1:8787` only; do not add a public bind option.
- Preserve all current CLI commands and keep the existing 40 tests passing.
- Allow only one active scan, demo, or benchmark job.
- Never persist or log credentials, raw URLs, canary values, response bodies, or environment-variable values.
- Persist only SHA-256 URL fingerprints and sanitized evidence.
- Support environment-variable credentials and one-run in-memory credentials.
- Serve the production UI from `web_dist/`; Node.js is not a runtime requirement.
- Keep remote checks read-only and retain the current exact-scope, HTTPS, DNS/IP, request, time, and response-size limits.

## Review Focus

- A cancelled job must start no further target requests and must erase its in-memory credentials; pin in Task 4.
- A SQLite or report write failure must not leak request material in an API response or log; pin in Tasks 3 and 5.
- Two browser tabs racing to start work must produce exactly one accepted job and one HTTP 409; pin in Task 4.
- A crafted report ID or path traversal string must never read outside the server-created report directory; pin in Task 5.
- Browser refresh must preserve sanitized history but remove one-run credentials; pin in Tasks 8 and 10.

---

### Task 1: In-memory credential injection in the core

**Files:**
- Modify: `cms_guard/config.py`
- Modify: `cms_guard/engine.py`
- Test: `tests/test_core.py`

**Interfaces:**
- Produces: `credentials(config: dict, supplied: dict[str, str] | None = None) -> dict[str, dict[str, str]]`
- Produces: `run(raw: dict, progress=None, supplied_credentials: dict[str, str] | None = None) -> dict`

- [ ] **Step 1: Write failing tests** for environment fallback, supplied credential precedence, missing values, identical active/revoked values, and absence of supplied secrets from the returned report.
- [ ] **Step 2: Run** `python -m unittest tests.test_core -v` and confirm the new tests fail because the signatures do not accept supplied credentials.
- [ ] **Step 3: Implement the two signatures** without mutating configuration, environment variables, or report contents; clear temporary mappings in the caller after use.
- [ ] **Step 4: Run** `python -m unittest tests.test_core -v` and the full existing suite; expect all tests to pass.
- [ ] **Step 5: Commit** `feat: support ephemeral scan credentials`.

### Task 2: API application shell and local request security

**Files:**
- Create: `cms_guard_api/__init__.py`
- Create: `cms_guard_api/app.py`
- Create: `cms_guard_api/security/session.py`
- Create: `cms_guard_api/routes/health.py`
- Modify: `pyproject.toml`
- Test: `tests/test_api_security.py`

**Interfaces:**
- Produces: `create_app(*, database_path: Path, report_root: Path, web_root: Path, session_token: str | None = None) -> FastAPI`
- Produces: `LocalSession.verify(origin: str | None, token: str | None, mutating: bool) -> None`

- [ ] **Step 1: Write failing API tests** for `/api/health`, allowed production/development origins, missing or wrong session token on mutations, oversized JSON, unsupported content types, and sanitized validation errors.
- [ ] **Step 2: Run** `python -m unittest tests.test_api_security -v`; expect import failures.
- [ ] **Step 3: Add FastAPI/Uvicorn dependencies and implement the app factory**, fixed CORS allowlist, random session token, request-size middleware, and categorical error responses.
- [ ] **Step 4: Run the task tests** and confirm all pass without exposing exception strings.
- [ ] **Step 5: Commit** `feat: add localhost API security shell`.

### Task 3: Sanitized SQLite history repository

**Files:**
- Create: `cms_guard_api/storage/schema.py`
- Create: `cms_guard_api/storage/repository.py`
- Create: `cms_guard_api/models.py`
- Test: `tests/test_api_storage.py`

**Interfaces:**
- Produces: `HistoryRepository.create_run(kind: RunKind) -> UUID`
- Produces: `HistoryRepository.finish_run(run_id: UUID, status: JobStatus, report: dict) -> None`
- Produces: `HistoryRepository.get_run(run_id: UUID) -> RunRecord | None`
- Produces: `HistoryRepository.list_runs(filters: RunFilters) -> list[RunSummary]`
- Produces: `HistoryRepository.delete_run(run_id: UUID) -> bool`

- [ ] **Step 1: Write failing repository tests** for schema creation, completed/cancelled/failed runs, filtering, deletion, transaction rollback, URL fingerprinting, and rejection/removal of secret, URL, canary, and response-body fields.
- [ ] **Step 2: Run** `python -m unittest tests.test_api_storage -v`; expect import failures.
- [ ] **Step 3: Implement stdlib SQLite storage** with foreign keys, transactions, explicit JSON serialization, server-generated UUIDs, SHA-256 URL fingerprints, and a strict evidence allowlist.
- [ ] **Step 4: Run the task tests** and inspect a temporary database to confirm no forbidden values are present.
- [ ] **Step 5: Commit** `feat: add sanitized scan history`.

### Task 4: Single-job execution manager and cancellation

**Files:**
- Create: `cms_guard_api/jobs/manager.py`
- Create: `cms_guard_api/jobs/models.py`
- Test: `tests/test_api_jobs.py`

**Interfaces:**
- Consumes: `engine.run`, `benchmark.benchmark`, `HistoryRepository`
- Produces: `JobManager.start_scan(config: dict, secrets: dict[str, str]) -> UUID`
- Produces: `JobManager.start_demo(vulnerable: bool) -> UUID`
- Produces: `JobManager.start_benchmark(repeats: int) -> UUID`
- Produces: `JobManager.cancel(run_id: UUID) -> bool`
- Produces: `JobManager.snapshot(run_id: UUID) -> JobSnapshot`

- [ ] **Step 1: Write failing tests** for state transitions, progress callbacks, completion, engine failure, cancellation before the next target, secret cleanup on every exit path, invalid repeat counts, and two simultaneous starts yielding one `BusyError`.
- [ ] **Step 2: Run** `python -m unittest tests.test_api_jobs -v`; expect import failures.
- [ ] **Step 3: Implement a lock-protected single worker** with a cancellation event and `finally` cleanup; add a core cancellation hook checked before each target without changing completed-result semantics.
- [ ] **Step 4: Run task tests and the existing engine tests**; expect all to pass.
- [ ] **Step 5: Commit** `feat: orchestrate local scan jobs`.

### Task 5: API routes, reports, and safe downloads

**Files:**
- Create: `cms_guard_api/routes/config.py`
- Create: `cms_guard_api/routes/runs.py`
- Create: `cms_guard_api/routes/research.py`
- Create: `cms_guard_api/routes/reports.py`
- Create: `cms_guard_api/services/reports.py`
- Modify: `cms_guard_api/app.py`
- Test: `tests/test_api_routes.py`

**Interfaces:**
- Consumes: `JobManager`, `HistoryRepository`, existing report writers
- Produces: the endpoints fixed in design section 5
- Produces: `ReportService.generate(run_id: UUID) -> dict[ReportFormat, Path]`

- [ ] **Step 1: Write failing route tests** for validation without network calls, scan/demo/benchmark creation, HTTP 409, polling, cancellation, history filters, deletion confirmation contract, report regeneration, UUID validation, path traversal, and sanitized DB/report failure responses.
- [ ] **Step 2: Run** `python -m unittest tests.test_api_routes -v`; expect failures.
- [ ] **Step 3: Implement request/response models and routes**; map domain errors to fixed status codes and never accept a client file path.
- [ ] **Step 4: Run task tests and full Python suite**; expect all to pass.
- [ ] **Step 5: Commit** `feat: expose scan and report API`.

### Task 6: One-command production launcher

**Files:**
- Create: `cms_guard_api/launcher.py`
- Modify: `cms_guard/__main__.py`
- Modify: `pyproject.toml`
- Test: `tests/test_web_launcher.py`

**Interfaces:**
- Produces: `serve_local(host: str = "127.0.0.1", port: int = 8787, open_browser: bool = True) -> int`
- Produces: CLI commands `python -m cms_guard api` and `python -m cms_guard web`

- [ ] **Step 1: Write failing tests** for fixed host, port conflict, missing `web_dist`, readiness-before-browser, browser URL token handoff, signal shutdown, and no orphan worker.
- [ ] **Step 2: Run** `python -m unittest tests.test_web_launcher -v`; expect failures.
- [ ] **Step 3: Implement the launcher and CLI wiring** while preserving every existing subcommand and exit code.
- [ ] **Step 4: Run launcher tests and full Python suite**; expect all to pass.
- [ ] **Step 5: Commit** `feat: launch local web dashboard`.

### Task 7: Create the separate Vue application and guided shell

**Files (`MKARTEX-UI`):**
- Create: `package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`
- Create: `src/main.ts`, `src/App.vue`, `src/router/index.ts`, `src/styles/*`
- Create: `src/layouts/GuidedLayout.vue`
- Create: `src/pages/DashboardPage.vue`
- Create: `src/api/client.ts`, `src/types/api.ts`
- Test: `src/pages/DashboardPage.spec.ts`

**Interfaces:**
- Consumes: `/api/health`, `/api/runs`
- Produces: `apiClient` methods with typed success and categorical error results

- [ ] **Step 1: Initialize Vue 3 + TypeScript + Vite with Pinia, Router, Vitest, and Vue Test Utils** in a new local `MKARTEX-UI` worktree; do not add a component framework.
- [ ] **Step 2: Write failing tests** for the guided two-card dashboard, recent runs, API-offline state, keyboard navigation, and responsive labels.
- [ ] **Step 3: Run** `npm test -- --run`; expect component failures.
- [ ] **Step 4: Implement the approved guided layout and typed API client** using the selected mockup as visual reference.
- [ ] **Step 5: Run** `npm test -- --run` and `npm run build`; expect success.
- [ ] **Step 6: Commit** `feat: add guided CMS Guard dashboard`.

### Task 8: Four-step scan wizard and ephemeral secrets

**Files (`MKARTEX-UI`):**
- Create: `src/pages/ScanWizardPage.vue`
- Create: `src/components/wizard/{ScopeStep,RolesStep,TargetsStep,ReviewStep}.vue`
- Create: `src/stores/scanDraft.ts`
- Create: `src/api/scans.ts`
- Test: `src/pages/ScanWizardPage.spec.ts`

**Interfaces:**
- Consumes: `/api/config/validate`, `/api/runs`
- Produces: `useScanDraftStore()` whose persisted projection excludes URLs, canaries, and secret values

- [ ] **Step 1: Write failing tests** for all four steps, exact required fields, role/origin matching, environment versus one-run credential mode, `autocomplete="off"`, no local/session storage of secrets, refresh cleanup, validation preview, and final start request.
- [ ] **Step 2: Run** the wizard test; expect failures.
- [ ] **Step 3: Implement the smallest wizard and in-memory store**; persist no sensitive draft fields.
- [ ] **Step 4: Run UI tests and build**; expect success.
- [ ] **Step 5: Commit** `feat: add guided scan setup`.

### Task 9: Progress, result, research, and history pages

**Files (`MKARTEX-UI`):**
- Create: `src/pages/RunProgressPage.vue`
- Create: `src/pages/RunResultPage.vue`
- Create: `src/pages/ResearchPage.vue`
- Create: `src/pages/HistoryPage.vue`
- Create: `src/components/ResultTable.vue`, `StatusSummary.vue`, `RunComparison.vue`
- Create: `src/api/{runs,research,reports}.ts`
- Test: `src/pages/{RunProgressPage,RunResultPage,ResearchPage,HistoryPage}.spec.ts`

**Interfaces:**
- Consumes: all run, research, history, cancel, delete, and report endpoints
- Produces: one-second polling stopped on terminal state/unmount; compare view keyed by result target and role

- [ ] **Step 1: Write failing tests** for polling cleanup, cancel, five result statuses, search/filter, three report downloads, benchmark limits and disclaimer, history persistence, two-run comparison, and delete confirmation.
- [ ] **Step 2: Run the page tests**; expect failures.
- [ ] **Step 3: Implement the four pages and shared components** with accessible status text in addition to color.
- [ ] **Step 4: Run all UI tests and build**; expect success.
- [ ] **Step 5: Commit** `feat: add results research and history UI`.

### Task 10: Production asset integration and end-to-end verification

**Files:**
- Modify (`MKARTEX-UI`): `vite.config.ts`, `README.md`
- Create (`MKARTEX_2026`): `scripts/sync_web_dist.py`
- Modify (`MKARTEX_2026`): `.gitignore`, `README.md`, `.github/workflows/tests.yml`, `docs/VALIDATION.md`
- Create (`MKARTEX_2026`): `tests/test_web_integration.py`
- Generated: `web_dist/*`

**Interfaces:**
- Consumes: UI production build and `serve_local`
- Produces: reproducible `web_dist/` sync and documented local workflow

- [ ] **Step 1: Write failing integration tests** for SPA fallback, hashed static assets, session bootstrap, normal/vulnerable demo, benchmark display payload, sanitized persisted history, refresh behavior, and shutdown cleanup.
- [ ] **Step 2: Run** `python -m unittest tests.test_web_integration -v`; expect failure because assets are absent.
- [ ] **Step 3: Add a deterministic UI build-and-copy command** that replaces only `web_dist/` and records the UI source commit in `web_dist/build-info.json`.
- [ ] **Step 4: Update both READMEs, CI, and validation documentation** with development, build, one-command run, privacy boundaries, and test commands.
- [ ] **Step 5: Run** `npm test -- --run`, `npm run build`, the web asset sync, `python -m unittest discover -s tests -v`, and a smoke run of `python -m cms_guard web`; require zero failures and no secret/URL matches in SQLite or reports.
- [ ] **Step 6: Commit UI** `build: prepare production dashboard assets` and **commit backend** `feat: integrate local web dashboard`.

### Task 11: Release and repository handoff

**Files:**
- Modify: version fields and release notes in both repositories

**Interfaces:**
- Produces: reviewable `MKARTEX-UI` repository and `MKARTEX_2026` v0.2 release candidate

- [ ] **Step 1: Review both repository diffs** against every spec section and record any intentional deviation.
- [ ] **Step 2: Run the complete verification matrix** on supported Python and Node versions through GitHub Actions.
- [ ] **Step 3: Confirm public trees contain no real company domains, credentials, local databases, generated private reports, or environment files.**
- [ ] **Step 4: Push both repositories and verify README rendering, Actions results, and downloadable source archives.**
- [ ] **Step 5: Tag only after the user reviews the running UI and explicitly approves the release candidate.**
