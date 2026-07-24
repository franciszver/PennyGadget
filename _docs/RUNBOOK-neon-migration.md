# Neon.tech Postgres Migration Runbook (#50)

> **STATUS: PLAN ONLY -- NOT YET EXECUTED.** This runbook has NOT been run
> against a live Neon instance. Nothing in this document has been verified
> against real Neon connectivity; the DSN-handling test
> (`tests/test_neon_dsn_handling.py`) only proves the URL is well-formed,
> not that it connects. The owner must execute and verify each step below
> against a real Neon project before this migration is considered complete.

**Scope:** Move ElevareAI's Postgres database off Render's free-tier
Postgres (which expires 30 days after creation, see
`_docs/RUNBOOK-db-expiry-recovery.md`) onto Neon.tech, which has no such
expiry. No application code changes are required -- `get_database_url()` in
`src/config/settings.py` already passes `DATABASE_URL` through verbatim
(only normalizing `postgres://` to `postgresql://`), so a Neon DSN with
`?sslmode=require` works unchanged.

## Ordering -- read this before starting

Steps 1-5 are additive/reversible: at every point up through step 5, the
existing Render `elevareai-db` is untouched and still there as a fallback.
**Step 6 (removing the Render database) is destructive and irreversible.**
Do not perform step 6 until steps 4 and 5 have both succeeded against Neon.
If you remove the Render database before confirming Neon is serving traffic
correctly, and something is wrong with the Neon setup, there is no
fallback -- the data is gone.

## Steps

### 1. Provision a Neon project

- Create a Neon project (https://neon.tech).
- From the Neon dashboard, copy the **pooled** connection string (the host
  contains `-pooler`, e.g. `ep-xxx-pooler.us-east-2.aws.neon.tech`) -- not
  the direct/unpooled one. Ensure it includes `?sslmode=require`.
- Format: `postgresql://USER:PASSWORD@ep-xxx-pooler.REGION.aws.neon.tech/DB?sslmode=require`
- Treat this string as a secret; do not commit it anywhere.

### 2. Set DATABASE_URL in the Render dashboard

- In the Render dashboard, go to `elevareai-api` -> Environment.
- Set `DATABASE_URL` to the Neon pooled connection string from step 1.
- This PR's `render.yaml` already changes `DATABASE_URL` from a
  `fromDatabase:` binding to `sync: false` (manual secret) and removes the
  `databases:` block -- but do NOT apply/sync that blueprint change (or
  delete the Render database) until step 6. Setting the dashboard env var
  now is independent of the blueprint sync and does not touch the existing
  Render database.

### 3. Run migrations and seed data against Neon

Run this from wherever you run the seed script, with the environment
pointed at Neon. Reference: `_docs/RUNBOOK-db-expiry-recovery.md` step 4
uses the same script.

```bash
python scripts/seed_demo_data.py
```

This runs `scripts/setup_db.py` (schema/migrations) followed by idempotent
demo-account seeding.

**`DB_*` vs `DATABASE_URL` (resolved):** `scripts/setup_db.py`'s
`get_db_connection_string()` now prefers `DATABASE_URL` when set, returning
it verbatim (aside from normalizing `postgres://` to `postgresql://`), the
same precedence `src/config/database.py`'s `get_database_url()` uses. So
with `DATABASE_URL` set to the Neon pooled connection string (including
`?sslmode=require`), `setup_db.py` connects with that DSN as-is -- no
separate `DB_*` parsing is needed for this step. `DB_*` remains a fallback
for local dev when `DATABASE_URL` is unset. See
`tests/test_setup_db_connection.py` for coverage.

### 4. Redeploy and verify /health

- Trigger a manual deploy of `elevareai-api` in the Render dashboard (or
  push a commit) so it picks up the new `DATABASE_URL`.
- Verify:

```bash
curl https://elevareai-api.onrender.com/health
```

Expected: `{"status":"healthy","database":"connected"}`

### 5. Verify demo login and data

- Open the frontend, log in as `demo@elevare.ai` with the `DEMO_PASSWORD`
  value set in the Render dashboard.
- Confirm demo data (goals, sessions, practice items) is visible.

### 6. Remove the Render database -- ONLY AFTER 4 AND 5 SUCCEED

> ⚠️ **This step is destructive.** Removing the `databases:` block (applying
> this PR's `render.yaml` via a Blueprint sync) and/or deleting the Render
> `elevareai-db` instance permanently deletes that database. Do this LAST,
> never before Neon is confirmed serving traffic in steps 4-5, or you lose
> the database with no fallback.

Once Neon is confirmed working:
- Sync the Blueprint (applies this PR's `render.yaml`, which no longer
  declares `elevareai-db`), or manually delete the `elevareai-db` instance
  in the Render dashboard.
- `elevareai-db` is no longer referenced by anything once `DATABASE_URL`
  points at Neon.

### 7. Relationship to the #34 expiry-recovery runbook

This migration supersedes the 30-day Render-Postgres expiry problem that
`_docs/RUNBOOK-db-expiry-recovery.md` (#34) addresses. That runbook now
carries a pointer at the top noting it no longer applies once migrated to
Neon.
