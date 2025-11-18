# AGENTS.md
## Quick Principles
- Prefer the nearest `just` recipe; no ad-hoc command mashups.
- Frontend (`conversational-ui`) uses `pnpm`; backend (`issue-solver`) uses `uv`. No npm/yarn/pip.
- Tests should state behaviour (Given/When/Then) and live beside the code they describe.
- Only follow `docs/local-dev-setup.md` when a task explicitly asks for full-stack/manual verification.

## Repo Map
- `conversational-ui/` – Next.js 15 + Vercel AI SDK frontend.
- `issue-solver/` – FastAPI API, worker, and CLI (`cudu`).
- `operations/00-foundation|01-provision|02-deploy` – Terraform stacks for shared infra, per-env services, and deployments.
- `docs/` – Runbooks plus ADRs (`docs/decisions/*.md`). Keep them synced when behaviour changes.

## Frontend (`conversational-ui`)
- Setup: `cd conversational-ui && just install` after copying `.env.example` → `.env` and aligning Redis/Postgres/MinIO with `docker-compose.yml`.
- Dev loop: make sure your container runtime (Docker Desktop, Colima, etc.) is running, run `just start-services` the first time (brings up Postgres/Redis/MinIO), then use `just dev` (installs deps, applies migrations, starts `pnpm dev`). UI listens on :3000 and auto-increments if that port is busy.
- Quality: `just build` is the required gate (Next build + Drizzle). `just lint` currently fails until we clean up lint debt—skip it unless you're explicitly working that task. Use `pnpm format` + Drizzle migrations (`pnpm db:generate`, `pnpm db:migrate`) when schema changes.

## Backend (`issue-solver`)
- Setup: `cd issue-solver && uv sync --all-extras --dev` (same flags as CI). No pip/poetry installs.
- Dev loop: keep your container runtime running, call `just start-services` once to boot LocalStack/backing infra, then use `just dev` to apply Alembic migrations and start FastAPI. Use `just worker-start`, `just run`, `just solve`, or `just start-services` when you need components individually. `just solve-priveleged` exists for Dockerized swe-agent flows that need sudo.
- Worker: run `just w` (alias for `just worker-start`) whenever you need background features—`issue_solver/worker/local_runner.py` drives queue consumers, so auto-documentation, repo indexing, PR creation, and MCP refresh flows will stall if it isn't running.
- Tests: follow the behavioural style shown in `tests/events/test_auto_documentation.py` or `tests/queueing/test_sqs_queueing_event_store.py`—fixtures set context, assertions describe outcomes in Given/When/Then form.
- Quality: use the aliases in `issue-solver/justfile`—`just l c f t` (lint ➜ typing ➜ format ➜ pytest).
- Secrets: set `TOKEN_ENCRYPTION_KEY` (use `just generate-encryption-key`) before migrations or worker processes.

## Ops & Deployment
- Use Terraform 1.10+. Workspace names derive from `GH_PR_NUMBER` or branch (`production` on `main`).
- `operations/00-foundation`: bootstrap DNS + blob buckets via `just init|plan|apply`.
- `operations/01-provision`: creates databases/Redis/blob. Helpers: `just output`, `just backend-database-url`, `just frontend-database-url`, `just blob-output`.
- `operations/02-deploy`: deploys webapi, worker, conversational-ui images. Requires AWS + Stripe + LLM secrets as `TF_VAR_*`. Destroy preview stacks with `just destroy` when PRs close.
- CI/CD: `.github/workflows/ci-python-project.yml` (lint ➜ mypy ➜ pytest) and `.github/workflows/cd-workflow.yml` (detect changes, provision, package images, apply Terraform, cleanup previews).

## Environments
- Local: run everything from your machine. Spin up containers via `just start-services` (frontend) or `just start-services`/`just dev` (backend) and store secrets in untracked `.env` files copied from each component’s `.env.example`. Follow `docs/local-dev-setup.md` when you need long-running services or nohup logs.
- Preview: every PR triggers a Terraform workspace `pr-<number>` plus container builds and deploys to `app.pr-<number>.umans.ai` / `api.pr-<number>.umans.ai`. Keep `just destroy` handy (or rely on the cleanup workflow) so dormant previews don’t leak infra.
- Production: merges to `main` reuse the same workflows but switch to the `production` workspace, production Stripe/PostHog keys, and stable URLs.

## Working Modes & Quick Checks
- **Default (lightweight) mode:** stay in read/modify/test loops. Do not start `just dev`, `just start-services`, or the worker unless the task explicitly calls for end-to-end verification or background processing.
- **Full-stack mode (explicitly requested):** once asked to verify end-to-end behaviour, follow `docs/local-dev-setup.md` to boot long-lived services (`just start-services`, `just dev`, `just w`). Use nohup logs so you can prove what’s running.
- **Is something already running?**
  - Frontend: `curl -I http://localhost:3000` (or increment ports) before starting anything. If you get a 2xx/3xx, reuse the existing server.
  - Backend API: `curl -I http://localhost:8000/health` or `lsof -i :8000` to see if FastAPI is up.
  - Worker: check `ps aux | grep local_runner.py` or `tail issue-solver/just-w.log` before launching `just w`.
  - Services: `docker compose ps` (in `conversational-ui` or `issue-solver`) to tell whether Postgres/Redis/LocalStack containers are alive.
- **Keep the user loop short:** if a required service is missing, state which check failed and ask before spinning up heavy processes.

## Environment Variables & Secrets
- Local: treat each `.env.example` as the contract—list every required variable with a short comment, then copy to `.env` (ignored by git). Check that file first whenever something fails due to missing env.
- Preview/Prod: new variables must flow through Terraform _and_ GitHub secrets. Add them to `operations/02-deploy/variables.tf`, thread them into the relevant module (`webapi.tf`, `worker.tf`, `conversational-ui.tf`), and then create the matching `TF_VAR_*` entry manually in the GitHub UI (Settings → Secrets → Actions) so `cd-workflow.yml` can inject it at deploy time.
- Frontend: whenever you add or rename a variable, update `.env.example`, `docker-compose.yml`, and whatever runtime config consumes it (`next.config.ts`, etc.) so `pnpm build` sees the same key.
- Backend: keep `.env.example`, the Dockerfiles (webapi/worker), and Terraform env maps in sync whenever you add or rename a variable.

## Build/Test Checklist
- UI: `cd conversational-ui && just build`. Skip `just lint` unless assigned to the lint-fix task.
- Backend: `cd issue-solver && just l c f t` (tests currently take ~2 minutes).
- Full-stack: only when requested—follow `docs/local-dev-setup.md` to run services via `nohup`, capture logs, and exercise `/register` + manual verification.

## Security & Secrets
- Never cat or log secrets: OpenAI, Anthropic, Google Generative AI, Exa, PostHog, Stripe, Morph, Notion MCP, Supabase tokens, blob keys, TOKEN_ENCRYPTION_KEY.
- Blob/S3 credentials come from `operations/01-provision` outputs; store them in env vars, not files.
- LocalStack resets data on `just destroy-services`; backup anything important before teardown.
- Vector store cleanup is destructive—`just plan-cleanup` or `just cleanup --dry-run` first.
