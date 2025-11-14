# Local Dev Runbook

Notes on how we got every developer service running inside the Codex CLI sandbox, including the background log setup and the workaround for Next.js file-watcher limits.

## issue-solver

- **API + web UI (`just dev`)**
  ```bash
  cd issue-solver
  nohup just dev > just-dev.log 2>&1 & echo $! > just-dev.pid
  ```
  - `just-dev.log` captures all stdout/stderr (LocalStack bootstrap, Alembic migrations, FastAPI dev server).
  - `just-dev.pid` keeps the background PID so we can stop it with `kill $(cat just-dev.pid)`.
  - We hit `[Errno 48] Address already in use` on port 8000; freeing the host FastAPI processes (PIDs 18172/18185 at the time) resolved it.
- **Worker queue (`just w`)**
  ```bash
  cd issue-solver
  nohup just w > just-w.log 2>&1 & echo $! > just-w.pid
  ```
  - Writes worker output (SQS poller + lambda shim) to `just-w.log`.
  - Stop via `kill $(cat just-w.pid)`.

## conversational-ui

Running `just dev` here required two tweaks:

1. **Port conflict** – another Node process already bound to 3000 in the sandbox. Next.js automatically moved to 3001, so we pointed the browser/curl to `http://localhost:3001`.
2. **Too many file watches (EMFILE)** – Turbopack’s default watcher exhausted the sandbox FD limit, causing every route to 404. Switching Watchpack to polling fixes it:

```bash
cd conversational-ui
rm -f just-dev.log just-dev.pid
WATCHPACK_POLLING=true WATCHPACK_POLLING_INTERVAL=200 \
  nohup just dev > just-dev.log 2>&1 & echo $! > just-dev.pid
```

- Logs land in `conversational-ui/just-dev.log`, PID in `just-dev.pid`.
- Stop it with `kill $(cat just-dev.pid)`.
- Verify readiness with `curl -I http://localhost:3001/` (NextAuth redirects to `/login`, confirming the middleware runs).

These steps keep all three long-running services alive with tailable logs while we keep working in the CLI. Adjust the polling interval or switch back to normal watchers if you are on a host without the EMFILE constraint.

### Creating a throwaway UI account (no email service)

Because the sandbox cannot receive email, we verified accounts manually:

1. **Register through the UI** – browse to `http://localhost:3001/register`, submit an email/password (example: `codex.agent+ts1@example.com` / `CodexTest123!`). The app creates the user but marks it as unverified.
2. **Grab the verification token from Postgres** – the `conversation-ui` stack exposes Postgres as `postgres-umansuidb`. Run:
   ```bash
   docker exec postgres-umansuidb \
     psql -U user -d umansuidb \
     -c 'select "email","emailVerificationToken" from "User";'
   ```
   Copy the long token for the email you just registered.
3. **Manually hit the verification API** – call the local endpoint so the account flips to verified:
   ```bash
   curl -s -X POST http://localhost:3001/api/auth/verify \
     -H 'Content-Type: application/json' \
     -d '{"token":"<copied token>"}'
   ```
   You should receive `{"message":"Email verified successfully"}` and can now log in at `/login`.

After logging in, click **New Chat**, type a message (e.g., `hi`), and send it via the round arrow button to confirm the end-to-end UI flow.

## Preview testing playbook (app.pr-XXX.umans.ai)

When a PR deploys to the preview stack, we can exercise it without re-doing auth every time:

1. **Preview URLs**  
   - UI: `https://app.pr-<PR_NUMBER>.umans.ai`  
   - API: `https://api.pr-<PR_NUMBER>.umans.ai`  
   (See `.github/workflows/cd-workflow.yml`: the workspace/tag is `pr-${number}`.)

2. **Reuse an existing login**  
   - Ask a teammate (or yourself) to log into the preview UI once in the shared browser profile.
   - In the CLI sandbox we have to use Playwright’s `~/Library/Caches/ms-playwright/mcp-chrome` profile, so before driving it, kill any leftover instances:  
     ```bash
     pkill -f mcp-chrome || true
     ```
   - Launch Playwright again; since the profile now contains the authenticated cookies, the preview app loads already signed in.

3. **Exercise the relevant feature**  
   - If the PR touches repo-aware features (docs prompts, chat tooling, etc.), connect a repository from the header’s **Connect Repository** dialog. Prefer a small public repo so indexing finishes quickly; wait for the Git icon to show “indexed” before testing.
   - Navigate straight to the area under test—for example `https://app.pr-<PR>.umans.ai/docs/<KB_ID>` for auto docs, `/chat/<chatId>` for conversation flows, or whatever route the UI exposes.
   - Drive the scenarios exactly as a user would (submit forms, trigger `/api/repo/sync`, call new endpoints via the console, etc.) and confirm the UI updates as expected.
   - When helpful, hit the preview API (`https://api.pr-<PR>.umans.ai/...`) to inspect JSON responses or process status while the feature runs.
