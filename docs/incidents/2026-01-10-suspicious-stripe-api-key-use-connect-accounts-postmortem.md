# Postmortem — 2026-01-10 — Suspicious Stripe API key use (Connect account creation attempts)

## Summary

On **2026-01-10**, Stripe temporarily restricted our ability to create **Connect accounts** after detecting suspicious
activity. Investigation in Stripe Workbench showed an unexpected **`POST /v1/accounts`** request (Connect account
creation) made using our **live secret key** (suffix `…lgtgqG`) from an unknown IP with a non-matching user agent (
`python-requests/...`).

We do **not** use Stripe Connect in our product, and our codebase does not call `stripe.accounts.create`. We treated
this as a **probable secret key compromise**, rotated the Stripe secret key, updated CI/CD secrets, redeployed, and
revoked the old key.

## Status

**Resolved (contained)** — key rotated + old key revoked + deployments verified using the new key.  
**Follow-up pending** — rotate webhook signing secret (defense-in-depth).

## Severity

**High** — the leaked key allowed authenticated access to Stripe API endpoints (reads succeeded).

## Impact

- No evidence of successful creation of Connect accounts (request was blocked / returned `400` with Stripe restriction
  message).
- Some **read** endpoints returned `200` around the same time (e.g. `/v1/balance`, `/v1/payouts`), indicating the key
  was usable for API access.
- No evidence (so far) of charges/refunds/subscription mutations. (We validated in Workbench by scanning around the
  incident time, but we did not perform a full historical audit yet.)

## What happened

Stripe flagged suspicious activity around **Connect account creation**. Workbench logs showed:

- An unexpected `POST /v1/accounts` with payload consistent with a generic Connect Express account creation:
  ```json
  { "country": "US", "email": "check_…@example.com", "type": "express" }
  ```

* The request used a live secret key (suffix `…lgtgqG`) and a `python-requests/...` user agent, which does not match our
  production stack (Next.js + Stripe Node SDK).

## Timeline (UTC)

> Note: some times in Workbench were displayed in CET. Convert as needed.

* **2026-01-10 17:46:51Z** — `POST /v1/accounts` (blocked) — suspicious Connect account creation attempt

    * Status: `400`
    * User-Agent: `python-requests/…`
    * Source IP: `85.117.56.xxx`
    * Request ID: `req_6wlayw…`
    * Key: `sk_live_…lgtgqG`

* **2026-01-10 ~17:46:58Z → 17:46:59Z** — burst of reads (some `200 OK`), including:

    * `GET /v1/account` (200)
    * `GET /v1/balance` (200)
    * `GET /v1/payouts` (200)
    * `GET /v1/accounts` (200)
    * `GET /v1/accounts/{platform}/external_accounts` (403)

* **2026-01-11** — Rotated Stripe live secret key, updated CI/CD secrets, redeployed, and revoked the old key.

* **2026-01-11 12:28:13Z** — Workbench shows our infrastructure automation reading the webhook endpoint using the **new
  key** (suffix `…wDgAAa`), consistent with Terraform/provider behavior.

## Detection

* Stripe Dashboard warning: “Verify recent connected account creation requests”.
* Workbench logs confirmed unexpected Connect activity and API reads using our live secret key.

## Root cause (most likely)

**Stripe live secret key exposure** (`sk_live_…lgtgqG`).

We did not determine the exact leakage path during this incident window. Plausible sources include:

* CI/CD secret exposure (mis-scoped secrets, logs, or runner compromise)
* Accidental logging of environment variables in an app/runtime
* A compromised machine/session where the key was available

## Contributing factors

* A single “standard” secret key with broad permissions (no restriction-by-endpoint).
* Key material present in CI/CD to support deployments.
* Stripe Connect endpoints were callable even though the product does not use Connect.

## Response / mitigation

1. **Confirmed suspicious behavior**

    * Identified `POST /v1/accounts` with `python-requests` UA and unknown IP.
    * Verified our codebase does not create Connect accounts.

2. **Rotated + revoked the Stripe live secret key**

    * Created a new live secret key.
    * Updated GitHub Actions secrets.
    * Redeployed production.
    * Revoked/deleted the old secret key (`…lgtgqG`).

3. **Validated deployments are using the new key**

    * Workbench logs show the webhook endpoint read (`GET /v1/webhook_endpoints/{id}`) using the new key, consistent
      with our Terraform automation.

## Follow-up actions

1. **Rotate Stripe webhook signing secret (defense-in-depth)**

    * If the API key was compromised, assume webhook endpoint metadata (including signing secret) *may* have been
      readable.
    * Rotate the webhook signing secret and update the value stored in AWS Secrets Manager, then redeploy.
    * This reduces the risk of forged webhook events if the old signing secret was ever exfiltrated.

2. **Move to least-privilege Stripe keys**

    * Use **restricted keys** for the app (only what’s needed: Checkout + Billing).
    * Use a separate key for Terraform/infrastructure tasks if needed.
    * Consider disabling Connect features if not used, or at least ensure no internal flows rely on `/v1/accounts`.

3. **Audit around the incident window**

    * In Workbench, filter for mutating endpoints (`POST`, `DELETE`) and high-impact objects:

        * charges, refunds, payment_intents, customers, subscriptions, payouts, webhook_endpoints, accounts
    * Confirm no unexpected objects were created/updated.

4. **Harden CI/CD secret handling**

    * Ensure secrets are not printed in logs.
    * Scope secrets per environment and per workflow.
    * Consider additional alerting on Stripe API key usage spikes / unfamiliar user agents.

---

## Appendix — Key evidence (sanitized)

### A) Suspicious request (Connect account creation attempt)

* Endpoint: `POST /v1/accounts`
* Time: 2026-01-10 18:46:51 CET
* Status: `400` (Stripe restriction)
* Request ID: `req_6wlayw…`
* User-Agent: `python-requests/2.32.3`
* Source IP: `85.117.56.xxx`
* Key: `sk_live_…lgtgqG`
* Body:

  ```json
  { "country": "US", "email": "check_…@example.com", "type": "express" }
  ```

### B) Read burst (indicates key was usable)

Around 2026-01-10 18:46:58–18:46:59 CET:

* `GET /v1/account` (200)
* `GET /v1/balance` (200)
* `GET /v1/payouts` (200)
* `GET /v1/accounts` (200)
* `GET /v1/accounts/{platform}/external_accounts` (403)

### C) Webhook endpoint audit (expected automation)

* `GET /v1/webhook_endpoints/{id}` (200)
* User-Agent: `Stripe/v1 GoBindings/78.12.0` (consistent with Terraform/provider)
* Observed with:

    * old key (`…lgtgqG`) before rotation
    * new key (`…wDgAAa`) after rotation

### D) Actions taken

* Rotated live secret key
* Updated CI/CD secrets
* Redeployed production
* Revoked/deleted compromised key (`…lgtgqG`)

### E) Operational notes / commands

No CLI commands were required for Stripe investigation (Workbench/Dashboard-based).
Rotation performed in Stripe Dashboard + CI/CD redeploy.

Optional (Terraform-based) webhook secret rotation plan:

* Recreate the webhook endpoint (new signing secret) and update AWS Secrets Manager.
* Redeploy so the app uses the new `whsec_…` value.
