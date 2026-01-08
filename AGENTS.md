# umans.ai Platform

## Quick Principles

- Prefer the nearest `just` recipe; no ad-hoc command mashups.
- Frontend (`conversational-ui`) uses `pnpm`; backend (`issue-solver`) uses `uv`. No npm/yarn/pip.
- Tests should state behaviour (Given/When/Then) and live beside the code they describe.
- Only follow `docs/local-dev-setup.md` when a task explicitly asks for full-stack/manual verification.

## Testing Style (all code)

- Make tests read like short stories of real usage; assert externally visible behaviour, not internal logging or strings that may change.
- Comment only with `# Given`, `# When`, `# Then`; let fixture and helper names explain the setup.
- Centralize fixtures in `tests/**/conftest.py`; build small, realistic fixtures per domain (e.g., minimal filesystem, HTTP payload, queue event) instead of bespoke per-test setup.
- Keep tests fast and deterministic: tighten timeouts when you need one, avoid sleeps, and prefer parametrization over copy‑paste cases.
- Target behaviours that matter to users—successful flows and a few critical failures that change the experience—rather than defensive checks that don’t surface externally.
- Use behavioural assertions (state changed, side effect happened, command allowed/denied) so alternative implementations that keep behaviour intact stay green.

## Frontend (`conversational-ui`)

- To install dependencies (only when the task actually needs them refreshed), run `cd conversational-ui && just install`; it shells out to pnpm install.
- To run the UI for explicit end-to-end requests, the usual order is `just start-services` (one-time Postgres/Redis/MinIO stack) followed by `just dev`, which applies Drizzle migrations and launches `pnpm dev` on port 3000 (auto-increments when occupied). Skip this entire sequence unless the user specifically asks for a live UI.
- Quality guardrail is `just build` (Next build + Drizzle). `just lint` remains red until lint debt is paid down, so leave it alone unless the task is lint remediation; use `pnpm format` and migrations (`pnpm db:generate`, `pnpm db:migrate`) for schema changes.
- When Postgres is not running, use `pnpm build:only` to verify the Next.js build without migrations.

## Backend (`issue-solver`)

- To install dependencies (only when needed), run `cd issue-solver && uv sync --all-extras --dev`; alternate Python tooling (pip/poetry) is unsupported.
- To boot services for explicit end-to-end work, first ensure Docker/Colima is running, then use `just start-services` (LocalStack + backing infra) followed by `just dev` (Alembic + FastAPI). `just solve-priveleged` exists only for swe-agent flows that require sudo.
- The worker (`just w`) powers auto-doc, repo indexing, PR creation, MCP refresh, etc. Before starting it, check `ps aux | grep local_runner.py` or `tail issue-solver/just-w.log` to avoid duplicate runners.
- Tests should mirror existing behavioural suites like `tests/events/test_auto_documentation.py` and `tests/queueing/test_sqs_queueing_event_store.py`—fixtures plus Given/When/Then assertions.
- When adding backend tests, keep them narrative and “non-gameable”: lean on shared fixtures (`api_client`, `time_under_control`, SQS/Postgres helpers) and the existing Brice/“nice repo” personas (`tests/examples/happy_path_persona.py`, `tests/webapi/test_processes_list.py`) so scenarios read like real flows; assert full responses/events, not just a field, and avoid over-mocking internals unless a hard dependency (e.g., git `Repo`) forces it.
- Quality guardrail is the alias chain `just l c f t` (ruff lint → mypy → ruff format → pytest). `TOKEN_ENCRYPTION_KEY` must exist (see `just generate-encryption-key`) before migrations or worker jobs.

## Ops & Deployment

- Use Terraform 1.10+. Workspace names derive from `GH_PR_NUMBER` or branch (`production` on `main`).
- `operations/00-foundation`: bootstrap DNS + blob buckets via `just init|plan|apply`.
- `operations/01-provision`: creates databases/Redis/blob. Helpers: `just output`, `just backend-database-url`, `just frontend-database-url`, `just blob-output`.
- `operations/02-deploy`: deploys webapi, worker, conversational-ui images. Requires AWS + Stripe + LLM secrets as `TF_VAR_*`. Destroy preview stacks with `just destroy` when PRs close.
- CI/CD: `.github/workflows/ci-python-project.yml` (lint → mypy → pytest) and `.github/workflows/cd-workflow.yml` (detect changes, provision, package images, apply Terraform, cleanup previews).

## Environments

- Local: default assumption is "lightweight" unless the task explicitly calls for long-lived services in which case go Full-stack mode (see section below for more details).
- Preview: every PR triggers a Terraform workspace `pr-<number>` plus container builds and deploys to `app.pr-<number>.umans.ai` / `api.pr-<number>.umans.ai`.
- Production: merges to `main` reuse the same pipelines but target the `production` workspace, prod secrets, and stable URLs.

## Working Modes & Quick Checks

- **Default (lightweight) mode:** stay in read/modify/test loops. Do not start `just dev`, `just start-services`, or the worker unless the task explicitly calls for end-to-end verification or background processing.
- **Full-stack mode (explicitly requested):** once asked to verify end-to-end behaviour, follow `docs/local-dev-setup.md` to boot long-lived services (`just start-services`, `just dev`, `just w`). Use nohup logs so you can prove what's running.
- **Is something already running?**
  - Frontend: `curl -I http://localhost:3000` (or increment ports) before starting anything. If you get a 2xx/3xx, reuse the existing server.
  - Backend API: `curl -I http://localhost:8000/health` or `lsof -i :8000` to see if FastAPI is up.
  - Worker: check `ps aux | grep local_runner.py` or `tail issue-solver/just-w.log` before launching `just w`.
  - Services: `docker compose ps` (in `conversational-ui` or `issue-solver`) to tell whether Postgres/Redis/LocalStack containers are alive.
- **Keep the user loop short:** if a required service is missing, state which check failed and ask before spinning up heavy processes.

## Environment Variables & Secrets

- Local: `.env.example` files serve as documentation of required keys; use them as references when something fails due to missing env, but keep actual `.env` files private and untracked.
- Preview/Prod: when a new variable is needed, declare it in `operations/02-deploy/variables.tf`, thread it through the relevant module (`webapi.tf`, `worker.tf`, `conversational-ui.tf`), and create the matching `TF_VAR_*` secret manually in the GitHub UI so `cd-workflow.yml` can inject it.
- Frontend: whenever you add or rename a variable, align `.env.example`, `docker-compose.yml`, and runtime config (`next.config.ts`, etc.) so the build sees consistent keys.
- Backend: mirror changes across `.env.example`, the webapi/worker Dockerfiles, and the Terraform env maps.

## Build/Test Checklist

- UI: `cd conversational-ui && just build`. Skip `just lint` unless assigned to the lint-fix task.
- Backend: `cd issue-solver && just l c f t` (tests currently take ~2 minutes).
- Full-stack: only when requested—follow `docs/local-dev-setup.md` to run services via `nohup`, capture logs, and exercise `/register` + manual verification.

## Security & Secrets

- Never cat or log secrets: OpenAI, Anthropic, Google Generative AI, Exa, PostHog, Stripe, Morph, Notion MCP, Supabase tokens, blob keys, TOKEN_ENCRYPTION_KEY.
- Blob/S3 credentials come from `operations/01-provision` outputs; store them in env vars, not files.
- LocalStack resets data on `just destroy-services`; backup anything important before teardown.
- Vector store cleanup is destructive—`just plan-cleanup` or `just cleanup --dry-run` first.
