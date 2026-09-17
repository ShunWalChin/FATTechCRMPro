# FAT Tech API v1 · aplicação 0.5.1

Base `/api/v1`, JSON UTF-8, dates ISO-8601 UTC, money integer BRL cents. Interactive typed documentation: `/api/docs`; machine contract: `/api/openapi.json`.

Authentication: `POST /auth/login {email,password}` and `GET /auth/me` return `{user:{id,name,email,role,tenant_id},csrf_token}`. Session cookie `fattech_session` is HttpOnly, SameSite=Lax, Secure in production. `POST /auth/logout`. Browser writes require an allowed Origin or `X-CSRF-Token` from login/me. Send cookies with `credentials: include`.

`POST /auth/password {current_password,new_password}` requires 12–200 characters in the new password and returns `{ok:true,other_sessions_revoked:true}`. `GET /auth/sessions` returns `{items:[{id,expires_at,current}],total}` for the current user's active sessions; `DELETE /auth/sessions/{id}` revokes one of their sessions. These endpoints require a browser session, never an API key. Password whitespace is significant; errors never echo passwords.

CRUD resources: `contacts`, `companies`, `pipelines`, `deals`, `tasks`, `conversations`, `messages`, `campaigns`, `automations`, `knowledge`, `approvals`, `agents`, `projects`, `invoices`, `products`.

`GET /{resource}?q=&status=&stage=&pipeline_id=&contact_id=&conversation_id=&limit=50&offset=0` returns `{items:[],total}`. `GET /{resource}/{id}` returns one record. `POST /{resource}` creates. `PATCH /{resource}/{id}` takes changed fields plus required `version`. `DELETE /{resource}/{id}?version=1` soft deletes. Version mismatch returns 409, missing or foreign tenant record 404. Fields `id,tenant_id,version,created_at,updated_at` are server-owned. Mutations return complete record; deletion returns `{deleted:true}`.

## Retry-safe creation for integrations

Every CRUD `POST /{resource}` accepts optional `Idempotency-Key` (8–200 ASCII letters,
digits, `.`, `_`, `:`, `-`). Generate the key once per business operation and persist it
in the originating workflow. On a timeout, resend the same key and the same data.

The original creation and its receipt commit in one transaction. Concurrent requests
with the same key serialize in the database. The same validated body returns the original
201 JSON result with `Idempotency-Replayed: true`, without a second record or audit event.
Changed content returns 409. A rolled-back creation does not reserve the key.
Default fields and JSON property ordering do not change the request fingerprint.

Keys are scoped to tenant, authenticated user or API credential, and resource. Authentication
and current permissions are always checked before replay. A new API key starts a new namespace.
The cached creation result may have an older version than the current record: use GET before PATCH.
Receipts are durable with no automatic expiry; do not prune them independently of the
integration's replay/retention policy. Without the header, the existing creation behavior remains.
This applies to CRUD creation, not team/password/public-capture or action endpoints.

Example for an n8n HTTP Request node:

```text
POST /api/v1/deals
Authorization: Bearer <credential stored in n8n>
Idempotency-Key: crm-deal:<stable-source-event-id>
Content-Type: application/json

{"title":"Diagnóstico comercial","value_cents":250000}
```

Do not generate a fresh key on each retry. Event delivery to n8n remains at least once;
this receipt prevents duplicate CRM creation and does not promise exactly-once external effects.

## Resource fields

Fields (defaults omitted in examples are supplied by the server):

| Resource | Fields |
|---|---|
| contacts | name (required), email, phone, company, company_id, status=new, source=manual, tags:[], score=0, consent=false, notes, owner_id |
| companies | name (required), website, industry, email, phone, document, status=active, notes |
| pipelines | name (required), description, status=active (active/inactive), is_default=false, stages (required, 1-40 of {key,label,probability=0,outcome=open\|won\|lost,expected_duration_hours=72}); owner/admin only |
| deals | title (required), contact_id, company_id, pipeline_id, stage, value_cents=0, probability, expected_close, next_action_at, position, owner_id, lost_reason, notes; `last_activity_at` is server-owned |

`position` orders a card inside its column and is assigned on creation as the current column maximum plus 1000, leaving room to drop between neighbours. Deal listings carry `contact_name` and `company_name`, resolved in one extra query for the page being returned, so a board shows who each deal is with; both are empty strings when the deal has no such relation. Deal listings are ordered by position ascending and then by creation date, so a board reads in the operator's priority rather than by age.
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

## Instagram accounts and the credential vault

`GET /integrations/instagram/accounts` returns `{items:[{id,instagram_user_id,username,label,status,version,connected_at,updated_at,token}],total}`.
`GET|PATCH|DELETE /integrations/instagram/accounts/{id}`, `POST /integrations/instagram/accounts` and
`POST /integrations/instagram/accounts/{id}/token` complete the set. Reading requires
`integrations:read`; every write requires `integrations:write` **and** an administrative role.

**The access token is never returned, by any endpoint, in any form.** `token` is either `null` or
`{fingerprint,scopes,expires_at,rotated_at}`, where `fingerprint` is 16 hexadecimal characters of
SHA-256 — enough to confirm a rotation changed the value, not enough to reconstruct it. The token is
stored AES-256-GCM encrypted, with the key in the server environment and never in the database, and
the additional authenticated data binds the ciphertext to `instagram:{tenant_id}:{account_id}`, so a
row copied to another organisation fails to decrypt rather than decrypting silently.

`instagram_user_id` matches `^[0-9]{1,32}$` and is unique across the whole database: a second
attempt to connect it returns 409, whichever organisation makes it. `PATCH` and the token rotation
require the current `version`; a mismatch returns 409. With no vault key configured, `POST` returns
503 and writes nothing. `DELETE` returns `{deleted:true,id}` and removes the credential row.

`POST /api/public/webhooks/instagram` resolves the owning organisation from `entry[].id` against
connected accounts. An unrecognised account returns **404**, audited with the account id and without
the body; a delivery spanning accounts of different organisations is refused the same way.

## Funnels and deal stages

Stage vocabulary is tenant configuration, not a fixed enum. Each tenant is provisioned with one default funnel (`lead`, `qualified`, `proposal`, `negotiation`, `won`, `lost`) by migration `0002` and by owner bootstrap.

A deal without `pipeline_id` adopts the tenant default funnel and stores that id, so a later default change does not move existing deals. `stage` must be a unique key declared by the funnel; unknown keys return 422. For open stages, creation without `probability` adopts the stage value, and explicit zero is preserved. An update staying in the same stage preserves probability unless supplied. Changing stage adopts its probability unless explicitly supplied. Won/lost outcomes always use 100/0 on new writes. Occupied stages cannot change outcome. Configuration writes serialize per tenant, including concurrent default selection.

Moving a deal to a stage whose `outcome` is `lost` requires a non-empty `lost_reason` (422 otherwise). Moving it back to any other stage clears the reason. Stage keys match `^[a-z][a-z0-9_-]{0,39}$` and are unique per funnel.

Removing or renaming a stage that still holds active deals returns 409, as does deleting a funnel with active deals. An `inactive` funnel refuses new deals and reassignments but keeps the deals already inside it editable, so a funnel can be archived without stranding history. Setting `is_default` demotes the previous default in the same transaction.

`GET /notifications` derives what needs attention from the records themselves: overdue tasks, pending approvals and deals the radar ranks as `critico` or `em_risco`. It returns `{items:[{kind,severity,id,title,detail,href,at}],total,counts}` ordered by severity. Nothing is stored: resolving the underlying record is what makes an entry disappear, because no background job reconciles a stored notice.

`POST /contacts/import {rows:[{...}],commit:false}` previews up to 500 rows and writes nothing. Response: `{total,ready,created,committed,invalid:[{line,errors}],duplicates:[{line,contact_id,contact_name,reason}]}`. Version 0.3 accepts only `name,email,phone,company,source,notes`; the authenticated actor is owner and consent starts false. API keys require both `contacts:read` and `contacts:write`.

`commit:true` requires `Idempotency-Key`. It revalidates the current database under the tenant contact lock; duplicates that appeared since preview are skipped. **Any invalid row rejects the whole batch with 422 and `detail.report`**, without committed contacts or receipt. Repeat the same key/content to recover the original successful report; changed content returns 409. Preview and confirmation are separate transactions, never a lock held while the user reviews.

`POST /sales/proposals`, `GET|PATCH /sales/proposals/{id}`, `POST|GET|PATCH /sales/goals` and `GET /sales/report` are mounted under the sales router: proposals snapshot catalogue prices at creation time, goals are per-owner targets, and the report describes a cohort of deals.

`GET /sales/report` takes `date_basis=created|closed` (default `created`). `created` dates the cohort by `Record.created_at` and reports the outcome those deals have now. `closed` dates it by the server-owned `closed_at`, written when a deal enters a won or lost stage and cleared when it reopens, and admits only deals currently won or lost. Deals closed before that field existed carry no trustworthy instant, so they belong to no period: `closed` excludes them and discloses how many under `excluded_missing_closed_at`, counted after the owner and source filters and before the date filter. `date_basis` is echoed in `date_basis` as `deal_created_at_utc` or `deal_closed_at_utc`. Both bases use whole UTC days; `date_from > date_to` is 422.

Each `PipelineStage` may declare `required_fields`, a closed list drawn from `contact_id`, `company_id`, `owner_id`, `value_cents`, `expected_close` and `next_action_at`; unknown names and repeats are 422, and the default is empty so funnels written before this field keep advancing. Creating a deal in a stage, or moving one into it, without those fields returns 422 with `detail.message`, `detail.required_fields` and `detail.stage`, leaving stage, version and audit untouched. The check lives in the shared deal service, so a session, an API key and the public capture are held to it equally — a public lead missing them keeps its contact and its follow-up task and records `contacts.qualification_pending` instead of entering the funnel. `value_cents` is satisfied by a value above zero, so an explicit zero is an absent value, not a filled one.

`GET /work-queue` needs `tasks:read` and answers `{items,total,limit,offset,reference_at,timezone}`. It filters in the database by `q` (title and description, with `%` and `_` escaped), `owner_id` (an id, `me`, or `unassigned`), `status` (`open` means todo or in progress), `priority` and `due`. `due` reads deadlines in UTC: a date without a time expires only once its day ends, an instant expires at that instant, `overdue` excludes work already done, and `undated` is its own bucket rather than a silent omission. Ordering is by deadline with undated last and `id` as the tiebreaker, so paging is stable. Contact, deal and owner names are attached only for a principal that may read those kinds, so a `tasks:read` key sees tasks without borrowing names it cannot request directly.

`GET /audit` returns entries carrying `label`, `actor_name` and `resource_name` alongside the raw `action`, `actor_id` and `resource_id`. The label is Portuguese wording derived server side and agreeing in gender ("Criou o contato", "Alterou a automação"); an action nobody mapped keeps its raw key rather than receiving invented wording. Names are resolved in two batched queries, and the subject is omitted when it is the actor itself, as in a sign-in. `GET /dashboard` carries the same shape under `recent_activity`.

`GET /integrations` returns `{items:[{id,name,status,description}],total}`. External providers are explicitly `not_configured`; no simulated delivery. The payload also carries `scopes`, the full catalogue the key endpoint validates against, so a client never offers a permission the API would reject. `GET /team` returns members; owner/admin can `POST /team {name,email,password,role}`.

`PATCH /team/{id} {name?,role?,active?}` updates membership. Roles are `root`, `super_admin`, `admin`, `member`, `viewer`; legacy `owner` is equivalent to Super Admin. Root manages tenant roles, Super Admin manages Admin/member/viewer, Admin manages member/viewer. The last active Root and last elevated administrator are protected. Role changes, deactivation and administrative password resets revoke the target's sessions and API keys. `POST /team/{id}/password {new_password}` requires a manageable subordinate; personal password changes use `/auth/password`. Administrative team listings include inactive users and `active`; other members see active users only. `viewer` cannot mutate resources. Creating/updating agents, automations and invoices requires an administrative session; approvals may be requested by members but require a separate authorized decision maker. Login/me also return `role_label` and `permissions`, including `assignable_roles`; clients must use these capabilities.

A duplicate contact conflict returns 409 with `detail` as an object carrying `message`, `contact_id` and `contact_name`, so a caller can link to the record it collided with instead of leaving a dead end.

Public capture: `POST /public/leads {name,email,phone,company,interest,message,consent:true,utm_source,utm_medium,utm_campaign,utm_content,utm_term}` -> `{id,status:accepted}`. A resubmission matching one existing contact by normalized e-mail or phone returns 202 with that contact's id and appends the new message to its history. If e-mail and phone match different contacts, the API returns a generic 409 without choosing an identity. First-touch attribution, consent refusals and opt-out are preserved; an unauthenticated form cannot reactivate permission to contact.

Capture also opens the work, not just the record: the lead gets an opportunity in the first open stage of the default funnel and a high-priority task due the next day. A resubmission attaches to the opportunity already running instead of opening a second one, and only creates a follow-up task when the contact has none open, so repeated form fills cannot inflate the pipeline or repeat the reminder. Set `FATTECH_CAPTURE_CREATES_DEAL=false` to keep capture to the contact alone. Consent and rate limit required. Tenant selected by server configuration, never public request.

`GET /crm/radar?pipeline_id=` ranks the funnel's open deals by commercial risk and returns `{pipeline_id,pipeline_name,items:[{id,title,stage,stage_label,value_cents,probability,band,risk:{bucket,elapsed_hours,ratio},needs_action,...}],total,summary}`. Buckets are `em_dia`, `em_voo`, `em_risco` and `critico`, derived from the time since `last_activity_at` against the stage's `expected_duration_hours`; a `next_action_at` in the future holds a deal in `em_voo`. `band` is `quente`/`morno`/`frio` from probability.

`POST /messages/{id}/compliance` returns the send decision without sending: `{allowed,policy,reason,tag,seconds_left,preview,explanation}`. Policies are `internal`, `standard_24h`, `human_agent_7d`, `private_reply_7d`, `whatsapp_template` and `blocked`. `POST /messages/{id}/send` applies the same decision: a blocked message returns 409 carrying `detail.compliance`, and an allowed one returns 503 while external sends are disarmed or no provider adapter is configured. Consent, service window, blocklist and cooldown are re-evaluated at the moment of sending, never when the draft is written.

Special actions: `POST /automations/{id}/simulate {input:{}}`; `POST /messages/{id}/send {version}` validates compliance and provider capability (503 until a provider adapter is configured); `POST /approvals/{id}/decision {version,decision:approved|rejected,reason}`; `POST /agents/{id}/run {input}` fails closed without configured runtime/budget.

Owner/admin: `POST /api-keys {name,scopes:[contacts:read,contacts:write,...],expires_in_days:90}` returns secret once; `GET /api-keys`, `DELETE /api-keys/{id}`. Bearer keys are bound to tenant and explicit scopes. No wildcard scopes. `GET /audit` reads audit metadata without message bodies or credentials.

Webhook ingestion: `POST /webhooks/n8n` with scoped bearer key (`webhooks:write`), `Idempotency-Key`, `X-Fattech-Timestamp` unix seconds, `X-Fattech-Signature: sha256=<hex>`. Signature is HMAC-SHA256 over `timestamp + '.' + raw request bytes` using `FATTECH_WEBHOOK_SECRET`. ±300s replay window. Payload `{event_type,payload,trace_id?,hops:0}`. Same key+body is replay safe, changed body returns 409, hops >5 rejected. Ingest persists event and audit in one transaction. `GET /events` exposes outbox to keys scoped `events:read`.

`POST /events/{id}/retry` is an owner/admin action accepting only dead-letter events. The worker delivers outbox events to the configured `FATTECH_N8N_OUTBOUND_URL` with a 90-second lease, 20-second HTTP timeout, signed raw JSON, event ID as `Idempotency-Key`, bounded exponential retry and a dead-letter state after eight attempts. 408/425/429, 5xx and network failures retry; other non-2xx results fail permanently. Redirects are not followed. Consumers must deduplicate by event ID before any external effect: delivery is at least once. No URL means events remain pending. Configuring an outbound workflow is a separate deployment action, not implied by accepting an incoming webhook.

All date fields accept ISO date `YYYY-MM-DD` or ISO datetime; invalid calendar dates return 422. Optional email fields accept omitted/null values, not an empty string. Public lead attribution and consent timestamp are server-owned and survive contact edits. Amounts are strict nonnegative integer cents up to 100,000,000,000; database aggregates use 64-bit integers.

Production requires PostgreSQL, an HTTPS origin list, a 32+ character webhook secret and explicitly provisioned users. `python -m fattech.seed` requires `FATTECH_BOOTSTRAP_PASSWORD` (12+ chars); development demo data only with `--demo`, never implicitly in production.
# Operação comercial na interface (0.2.2)

`/crm/propostas` usa as rotas `/api/v1/sales/proposals` e
`/api/v1/sales/proposals/{id}`. Criações enviam `Idempotency-Key`; a interface mantém
a chave ao repetir o mesmo corpo após uma resposta incerta. Emissão e decisões usam
`version` e os estados `issued`, `accepted` e `rejected`. Não executam envios externos.

`/crm/metas` usa `/api/v1/sales/goals`: cadastro por administrador, consulta conforme
papel e atualização versionada do valor. O relatório conserva a base temporal
`deal_created_at_utc`. Veja o registro da versão em
`docs/releases/2026-09-12-versao-0.2.2.md` para limites e evidências.
