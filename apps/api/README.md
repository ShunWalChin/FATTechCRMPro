# FAT Tech transactional API

Python 3.12+ / FastAPI / Pydantic / SQLAlchemy. PostgreSQL is mandatory in production; SQLite is supported for local development and deterministic tests. The canonical HTTP contract is [API.md](API.md). External adapters are explicitly unavailable until configured and tested.

## Local commands

Run from `apps/api` with `uv` installed:

```powershell
uv sync --frozen --extra test
$env:FATTECH_DATABASE_URL = 'sqlite:///./fattech.db'
uv run python -m fattech.migrate
# Set FATTECH_BOOTSTRAP_EMAIL and FATTECH_BOOTSTRAP_PASSWORD in your environment, never commit them.
uv run python -m fattech.seed --demo
uv run uvicorn fattech.main:app --host 127.0.0.1 --port 8000
```

`--demo` creates clearly identified fictional records only when the tenant has no CRM records. It is forbidden in production. Bootstrap never resets an existing owner's password or overwrites customer data. Use the authenticated password-change API to rotate credentials.

## Files and responsibilities

| File | Responsibility |
|---|---|
| `fattech/config.py` | Typed environment configuration; production fail-closed checks |
| `fattech/db.py` | Engine/session lifetime; transaction-local tenant RLS context |
| `fattech/models.py` | Persistent tables and indexes |
| `fattech/schemas.py` | Strict resource/input schemas and bounds |
| `fattech/security.py` | Argon2 password hashing, cookie sessions, scoped keys, CSRF and shared rate limits |
| `fattech/services.py` | Tenant-scoped CRUD, version conflicts, relationship protection, audit/outbox and flow simulation |
| `fattech/main.py` | HTTP routes, membership, approvals, capture, integrations and errors |
| `fattech/migrate.py` | Transactional schema 0001, PostgreSQL policies and application grants |
| `fattech/seed.py` | Explicit owner bootstrap and optional development examples |
| `fattech/worker.py` | Outbox claim, signed HTTP delivery, retry/dead-letter and graceful shutdown |
| `tests/test_api.py` | Auth, membership, isolation, CRUD, compliance, webhook and validation checks |
| `tests/test_worker.py` | Durable lease, stale worker fencing, retry, signature and HTTP failure classification |
| `tests/test_postgres.py` | Actual PostgreSQL RLS, grants and context reset across commit/rollback/pool reuse |
| `pyproject.toml`, `uv.lock`, `requirements.txt` | Direct requirements, complete lock and exported runtime requirements with hashes |

## Data model and transaction boundaries

Every customer-owned row has a `tenant_id` foreign key. `records` contains the fourteen bounded resource types and their validated JSON fields, a version number, soft-delete marker and UTC timestamps. All queries include tenant/kind filters. Parent records are locked while relationships are created or changed; deletion rejects active dependants. Updates use a version predicate and return 409 on stale writes. Generic JSON storage is a deliberate first schema: it permits one consistent mutation/audit pipeline. High-volume reporting and new hard uniqueness constraints will require explicit indexed columns and additive migrations.

`audit_log` stores actor, action, resource ID, changed field names and timestamps; it does not copy message bodies or credentials. Runtime grants prohibit audit updates/deletion. `event_outbox` persists event payload, trace/hop metadata, attempt count, availability, lease and unique claim token. `idempotency_keys` binds a tenant/key pair to the raw body digest and original response. These four tables enforce and force PostgreSQL RLS. `set_config(..., true)` is restored at every transaction start for the active session and cannot leak through a pooled connection.

`tenants` is the tenant directory. `users`, `login_sessions`, `api_keys` and `rate_limits` support pre-tenant authentication and therefore do not use RLS. Their application access is scoped by authenticated identity, tenant and cryptographic token hash. The runtime has read-only access to the tenant directory. Cookies use random 384-bit session tokens; the database stores SHA-256 hashes and expiration/revocation, not the original tokens. Passwords use Argon2id. API keys are returned once and stored only as hash plus display prefix and explicit scopes.

All successful business mutations, audit rows and events commit together. Rejected transactions roll back. The fixed-window rate counter commits independently before business writes so repeated failures still consume the limit; counters are shared across processes. Requests are limited to 1 MiB before parsing. Logs contain trace IDs/error classes, not database URLs or request bodies.

## Production operations

Set `FATTECH_ENV=production`, `FATTECH_ALLOWED_ORIGINS` to explicit HTTPS origins, and a 32+ character `FATTECH_WEBHOOK_SECRET`. Run migration and initial seed with the database owner URL in `FATTECH_DATABASE_URL` and `FATTECH_DB_APP_PASSWORD` to provision `fattech_app`. Then run API/worker using the separate `fattech_app` connection URL. Production startup refuses superusers, BYPASSRLS roles, table owners, absent schema migrations, or tenant tables without enforced RLS.

The migration uses a transaction and PostgreSQL advisory lock. Version 0001 is non-destructive and repeatable. It is not a general-purpose schema diff engine: subsequent model changes need a new explicit migration. Back up and restore the database through the repository production runbook; never attempt rollback by deleting customer rows.

Outbound n8n is opt-in through `FATTECH_N8N_OUTBOUND_URL` (HTTPS in production) and optional `FATTECH_N8N_OUTBOUND_TOKEN`. The incoming gateway uses the API key and HMAC described in API.md. The worker is `python -m fattech.worker`; `--once` performs one bounded pass. Without outbound configuration it preserves pending events and emits one startup notice. A configured consumer must verify signatures and deduplicate event IDs before external effects. Inspect `/api/v1/events` for `dead_letter`, correct the underlying error, and use the restricted retry action.

Session/team administration is available through the HTTP interface. Password changes invalidate other sessions; account deactivation invalidates sessions and keys. The final active owner is protected by a membership lock and refreshed permission checks. Approvals store immutable intent, expiry, separate requester/decider and `execution_status=not_executed`; approval alone never sends messages or spends funds.

## Verification

```powershell
uv run pytest -q
uv run ruff check fattech tests
uv run python -m compileall -q fattech
```

The PostgreSQL test is skipped unless `FATTECH_TEST_POSTGRES_OWNER_URL` and `FATTECH_TEST_POSTGRES_APP_URL` point to the same disposable database whose name includes `test`. Optional `FATTECH_TEST_DB_APP_PASSWORD` provisions the runtime role. The test inserts uniquely named tenants and cleans only its own rows. SQLite tests do not prove PostgreSQL RLS or real provider delivery. HTTP worker tests use `httpx.MockTransport`, with no external messages sent.

This backend implements the documented CRM operations, durable event gateway and restricted administration. It does not claim WhatsApp/Instagram/email delivery, payment settlement, fiscal issuance, calendar OAuth or autonomous AI execution: these require real provider adapters, credentials and production validation. No software is unbreakable; the repository documents controls and observable failure states instead of promising that.
