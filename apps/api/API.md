# FAT Tech API v1

Base `/api/v1`, JSON UTF-8, dates ISO-8601 UTC, money integer BRL cents. Interactive typed documentation: `/api/docs`; machine contract: `/api/openapi.json`.

Authentication: `POST /auth/login {email,password}` and `GET /auth/me` return `{user:{id,name,email,role,tenant_id},csrf_token}`. Session cookie `fattech_session` is HttpOnly, SameSite=Lax, Secure in production. `POST /auth/logout`. Browser writes require an allowed Origin or `X-CSRF-Token` from login/me. Send cookies with `credentials: include`.

`POST /auth/password {current_password,new_password}` requires 12–200 characters in the new password and returns `{ok:true,other_sessions_revoked:true}`. `GET /auth/sessions` returns `{items:[{id,expires_at,current}],total}` for the current user's active sessions; `DELETE /auth/sessions/{id}` revokes one of their sessions. These endpoints require a browser session, never an API key. Password whitespace is significant; errors never echo passwords.

CRUD resources: `contacts`, `companies`, `pipelines`, `deals`, `tasks`, `conversations`, `messages`, `campaigns`, `automations`, `knowledge`, `approvals`, `agents`, `projects`, `invoices`, `products`.

`GET /{resource}?q=&status=&stage=&pipeline_id=&contact_id=&conversation_id=&limit=50&offset=0` returns `{items:[],total}`. `GET /{resource}/{id}` returns one record. `POST /{resource}` creates. `PATCH /{resource}/{id}` takes changed fields plus required `version`. `DELETE /{resource}/{id}?version=1` soft deletes. Version mismatch returns 409, missing or foreign tenant record 404. Fields `id,tenant_id,version,created_at,updated_at` are server-owned. Mutations return complete record; deletion returns `{deleted:true}`.

Fields (defaults omitted in examples are supplied by the server):

| Resource | Fields |
|---|---|
| contacts | name (required), email, phone, company, company_id, status=new, source=manual, tags:[], score=0, consent=false, notes, owner_id |
| companies | name (required), website, industry, email, phone, document, status=active, notes |
| pipelines | name (required), description, status=active (active/inactive), is_default=false, stages (required, 1-40 of {key,label,probability=0,outcome=open\|won\|lost,expected_duration_hours=72}); owner/admin only |
| deals | title (required), contact_id, company_id, pipeline_id, stage, value_cents=0, probability, expected_close, next_action_at, position=0, owner_id, lost_reason, notes; `last_activity_at` is server-owned |
| tasks | title (required), description, status=todo (todo/in_progress/done), priority=medium (low/medium/high/urgent), due_date, contact_id, deal_id, project_id, owner_id |
| conversations | title (required), contact_id, channel=internal (internal/whatsapp/instagram/email), status=open (open/pending/closed), owner_id, last_message; last_inbound_at is server-controlled and must be null on user writes |
| messages | conversation_id (required), body (required), direction=outbound, status=draft; incoming/status delivery are controlled by integration endpoints |
| campaigns | name (required), channel=email, status=draft, budget_cents=0, audience, scheduled_at, content, tags:[] |
| automations | name (required), description, status=draft, trigger=manual, nodes:[], edges:[]; simulation never sends |
| knowledge | title (required), content, category=general, tags:[], source |
| approvals | title (required), gate=G3, description, status=pending, intent:{}; decision only through decision endpoint |
| agents | name (required), squad, role, status=paused, autonomy=A0, description, budget_cents=0, spent_cents=0; execution disabled until runtime configured |
| projects | name (required), description, status=planning, company_id, owner_id, budget_cents=0, due_date, progress=0 |
| invoices | title (required), company_id, contact_id, status=draft, amount_cents=0, due_date, notes; internal records only, no fiscal issuance/payment |
| products | name (required), description, sku, price_cents=0, category=service, status=active |

`GET /dashboard?pipeline_id=` returns `{contacts,open_deals,pipeline_value_cents,weighted_pipeline_cents,revenue_cents,open_tasks,open_conversations,pending_approvals,active_automations,conversion_rate,pipeline_id,pipeline_name,pipeline:[{stage,label,outcome,count,value_cents,weighted_cents}],recent_activity:[],capabilities:{...}}`. Without `pipeline_id` the tenant default funnel is used; counts are scoped to that funnel. `open_deals` and `pipeline_value_cents` cover stages whose outcome is `open`; `weighted_pipeline_cents` sums `value_cents * probability` across those stages and divides once, so the forecast is exact integer cents. `conversion_rate` is won deals over every deal in the funnel.

## Funnels and deal stages

Stage vocabulary is tenant configuration, not a fixed enum. Each tenant is provisioned with one default funnel (`lead`, `qualified`, `proposal`, `negotiation`, `won`, `lost`) by migration `0002` and by owner bootstrap.

A deal without `pipeline_id` adopts the tenant default funnel and stores that id, so a later default change does not move existing deals. `stage` must be a key declared by the deal's funnel; an unknown key returns 422. When the request omits `probability`, the deal adopts the probability declared by its stage; an explicit value is kept.

Moving a deal to a stage whose `outcome` is `lost` requires a non-empty `lost_reason` (422 otherwise). Moving it back to any other stage clears the reason. Stage keys match `^[a-z][a-z0-9_-]{0,39}$` and are unique per funnel.

Removing or renaming a stage that still holds active deals returns 409, as does deleting a funnel with active deals. An `inactive` funnel refuses new deals and reassignments but keeps the deals already inside it editable, so a funnel can be archived without stranding history. Setting `is_default` demotes the previous default in the same transaction.

`GET /integrations` returns `{items:[{id,name,status,description}],total}`. External providers are explicitly `not_configured`; no simulated delivery. `GET /team` returns members; owner/admin can `POST /team {name,email,password,role}`.

`PATCH /team/{id} {name?,role?,active?}` updates membership. Roles are `owner`, `admin`, `member`, `viewer`; only an owner may modify an owner or promote another member to owner. The final active owner cannot be demoted or disabled. Disabling an account revokes sessions and API keys. Owner/admin team listings include inactive users and `active`; other members see active users only. `viewer` cannot mutate resources. Creating/updating agents, automations and invoices requires owner/admin session; approvals may be requested by members but require a separate authorized decision maker.

Public capture: `POST /public/leads {name,email,phone,company,interest,message,consent:true,utm_source,utm_medium,utm_campaign,utm_content,utm_term}` -> `{id,status:accepted}`. A resubmission matching an existing contact by normalized e-mail or phone returns 202 with that contact's id and appends the new message to its history: it never duplicates and never answers a visitor with a conflict. First-touch attribution and the original consent instant are preserved. Consent and rate limit required. Tenant selected by server configuration, never public request.

`GET /crm/radar?pipeline_id=` ranks the funnel's open deals by commercial risk and returns `{pipeline_id,pipeline_name,items:[{id,title,stage,stage_label,value_cents,probability,band,risk:{bucket,elapsed_hours,ratio},needs_action,...}],total,summary}`. Buckets are `em_dia`, `em_voo`, `em_risco` and `critico`, derived from the time since `last_activity_at` against the stage's `expected_duration_hours`; a `next_action_at` in the future holds a deal in `em_voo`. `band` is `quente`/`morno`/`frio` from probability.

`POST /messages/{id}/compliance` returns the send decision without sending: `{allowed,policy,reason,tag,seconds_left,preview,explanation}`. Policies are `internal`, `standard_24h`, `human_agent_7d`, `private_reply_7d`, `whatsapp_template` and `blocked`. `POST /messages/{id}/send` applies the same decision: a blocked message returns 409 carrying `detail.compliance`, and an allowed one returns 503 while external sends are disarmed or no provider adapter is configured. Consent, service window, blocklist and cooldown are re-evaluated at the moment of sending, never when the draft is written.

Special actions: `POST /automations/{id}/simulate {input:{}}`; `POST /messages/{id}/send {version}` validates compliance and provider capability (503 until a provider adapter is configured); `POST /approvals/{id}/decision {version,decision:approved|rejected,reason}`; `POST /agents/{id}/run {input}` fails closed without configured runtime/budget.

Owner/admin: `POST /api-keys {name,scopes:[contacts:read,contacts:write,...],expires_in_days:90}` returns secret once; `GET /api-keys`, `DELETE /api-keys/{id}`. Bearer keys are bound to tenant and explicit scopes. No wildcard scopes. `GET /audit` reads audit metadata without message bodies or credentials.

Webhook ingestion: `POST /webhooks/n8n` with scoped bearer key (`webhooks:write`), `Idempotency-Key`, `X-Fattech-Timestamp` unix seconds, `X-Fattech-Signature: sha256=<hex>`. Signature is HMAC-SHA256 over `timestamp + '.' + raw request bytes` using `FATTECH_WEBHOOK_SECRET`. ±300s replay window. Payload `{event_type,payload,trace_id?,hops:0}`. Same key+body is replay safe, changed body returns 409, hops >5 rejected. Ingest persists event and audit in one transaction. `GET /events` exposes outbox to keys scoped `events:read`.

`POST /events/{id}/retry` is an owner/admin action accepting only dead-letter events. The worker delivers outbox events to the configured `FATTECH_N8N_OUTBOUND_URL` with a 90-second lease, 20-second HTTP timeout, signed raw JSON, event ID as `Idempotency-Key`, bounded exponential retry and a dead-letter state after eight attempts. 408/425/429, 5xx and network failures retry; other non-2xx results fail permanently. Redirects are not followed. Consumers must deduplicate by event ID before any external effect: delivery is at least once. No URL means events remain pending. Configuring an outbound workflow is a separate deployment action, not implied by accepting an incoming webhook.

All date fields accept ISO date `YYYY-MM-DD` or ISO datetime; invalid calendar dates return 422. Optional email fields accept omitted/null values, not an empty string. Public lead attribution and consent timestamp are server-owned and survive contact edits. Amounts are strict nonnegative integer cents up to 100,000,000,000; database aggregates use 64-bit integers.

Production requires PostgreSQL, an HTTPS origin list, a 32+ character webhook secret and explicitly provisioned users. `python -m fattech.seed` requires `FATTECH_BOOTSTRAP_PASSWORD` (12+ chars); development demo data only with `--demo`, never implicitly in production.
