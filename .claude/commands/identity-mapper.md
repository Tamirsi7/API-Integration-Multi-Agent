# /identity-mapper — Merge Research into Canonical the platform JSON

Sub-agent that receives all research outputs from the parallel sub-agents and merges them
into a single, canonical JSON object matching the full the platform PRD schema.

Invoked by the `/integration` orchestrator as Sub-Agent E. Always runs after the research agents.

## Usage

This skill is invoked by the orchestrator with the collected research as input.
It is not typically run standalone.

## Instructions

You will receive:
1. OpenAPI Scout result (markdown)
2. API Info Researcher result (auth, rate limits, pagination — markdown)
3. Entity Researcher result (accounts, groups, roles, resources, relations — markdown)
4. Remediation Researcher result (remediation actions — markdown)
5. Contents of `identity_model.json` (canonical field definitions)

Your task: merge all inputs into a single valid JSON object matching the schema below.

## Rules

- **Zero Hallucination**: Every field must come from the research inputs. If a field was not
  researched or is marked "Data unavailable in public documentation", preserve that exactly.
- **Confidence required**: Every section must have a `_confidence` object with `score` (1-10),
  `source`, and `justification`.
- **Field names**: Use exact API field names from the entity researcher output for mappings.
- **No prose**: Return only the JSON. No markdown, no preamble.
- **Schema**: Output must match the structure defined in `prd_schema.json`. Read that file first.

## Key Schema Rules

- **`key_response_fields`** for ALL entities must be a **dict** mapping `"canonical_field": "api_field"` or `"canonical_field": {"api_field": "...", "notes": "..."}` — use the object form when a field needs critical context (derivation logic, CRITICAL flags, caveats). NOT an array.
- **`entity_relations`** entries must be **objects** with `{resolution_strategy, description, endpoint, doc_url}`. `resolution_strategy` is one of: `embedded_on_object | property_driven | separate_endpoint | client_side_aggregation | data_limitation`.
- **`technical_references`** is a required top-level array of `{section, label, url}` — compile all doc URLs found during research.
- **`remediation_actions`** is an object with `bottom_line`, `architecture_warnings`, and `actions` array. Each action has `_confidence`.
- **`bottom_line`** is required on EVERY section — a 🎯-prefixed 1-2 sentence summary specific to THIS app.
- **`architecture_warnings`** is required on every entity section and remediation_actions — array of named warnings with Action Required prescriptions.
- **`api_version`**: Extract the exact API version string from docs (e.g. `"REST API v3"`, `"Graph API 1.0"`). If not explicitly stated: `"Data unavailable in public documentation"`.
- **`sync_order`**: Array of step objects `{step, entities, rationale}` — ordered by API dependencies. Each step explains WHY those entities go in that order.
- **`developer_summary`**: 3-4 sentences covering critical takeaways, bottlenecks, and gotchas. Include cross-cutting concerns: rate limit strategy, pagination traps, NHI discovery approach. This replaces the former standalone `edge_cases` section — weave operational concerns into the summary and into per-entity `architecture_warnings`.

## Writing Quality Rules

These rules govern ALL narrative text fields you write: `overview.description`,
`overview.integration_purpose`, `authentication.notes`, `rate_limits.retry_strategy`,
`pagination.notes`, all `entity_*.notes`, `developer_summary`, and `edge_cases`.

### Rule 1 — Bottom-Line Actionable Summaries (No Boilerplate)
Write for a senior backend engineer who has 30 seconds to understand what matters.
- **NEVER** open with generic phrases: "The API uses...", "This section describes...", "[App] provides..."
- Every field must answer: *What does this mean in production? What breaks if I ignore it?*
- BAD: "HubSpot uses cursor pagination. Follow the links."
- GOOD: "A full portal sync can involve tens of thousands of contacts and owners. Fetch in batches
  of 100 (limit=100); the absence of `paging.next.after` is your only termination signal —
  treat a missing cursor as EOF, not a network error."

### Rule 2 — App-Specific Creative Voice (No Template Feel)
Each integration is different. The summaries must reflect the specific quirks of THIS app.
- Never reuse sentence structures across integrations
- Reference the app's actual architecture (HubSpot's dual-API inventory problem, Salesforce's
  governor limits, GitHub's per-token-tier divergence, Okta's rate limit burst windows)
- `developer_summary` must read like a warning from someone who has already built this
  integration: battle-tested, opinionated, no hand-holding

### Rule 3 — Flag Divergent Strategies (CRITICAL ARCHITECTURAL ALERT)
If different entities use **different** strategies for the same concept, it is an
architecture-level alert that MUST be surfaced explicitly.

Check for divergence across all entities in:
- Pagination strategy (cursor vs. offset vs. link-header)
- Auth scopes (different scopes per entity type)
- Rate limit handling (different headers or limits per endpoint group)
- Response field naming conventions (inconsistent field names across entity objects)
- API version differences (v1 for users, v3 for CRM)

**If divergence is detected:**
- Open the affected section's `notes` with: `"⚠️ ARCHITECTURE WARNING: ..."`
- Name exactly which entity uses which strategy and why
- State the implementation consequence clearly

Example: `"⚠️ ARCHITECTURE WARNING: Account sync via /settings/v3/users uses cursor pagination
(paging.next.after), but fetching deactivated accounts requires /crm/v3/owners which also uses
cursor pagination but returns different field names (userId vs id) — the ingestion layer needs
a field normalization step before merging both result sets."`

### Rule 4 — Hard Limits + Architectural Workarounds
If any endpoint has a hard record ceiling (e.g., offset pagination capped at 10,000 rows,
a max lookback window, or a non-paginated endpoint):
- State the exact limit
- Provide the workaround: "Implement time-windowing: sort by `createdAt` ASC, paginate until
  approaching the limit, checkpoint the last record's timestamp, then restart with a
  `createdAt > <checkpoint>` filter to continue the scan without hitting the ceiling."

### Rule 5 — Inline Formatting for Headers and Scopes
- `relevant_headers`: write as a single comma-separated inline string, not a bullet list.
  Example: `"X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After"`
- When contextualizing scopes per operation in notes, use inline format:
  `"Read: settings.users.read, crm.objects.owners.read — Write: settings.users.write"`
- Avoid bullet lists for values that read naturally as one sentence

### Rule 6 — Write for Developers, Not Analysts
Assume full fluency with: OAuth2, Bearer tokens, cursor pagination, rate limiting, HMAC signatures,
REST semantics (PUT = full replace, PATCH = partial update), JSON Schemas.
Do NOT define these terms. Instead, explain THIS app's implementation details and gotchas.
- BAD: "OAuth 2.0 is an authorization protocol that uses access tokens to grant access..."
- GOOD: "Private app tokens are the right choice — unlike OAuth access tokens (30-min TTL
  requiring refresh-token rotation in prod), private app tokens are static and never expire,
  eliminating an entire category of auth-related incidents."

### Rule 7 — Bottom-Line Summary Per Section
Every section's `bottom_line` field must answer:
"What is the ONE thing an engineer must understand about this section for THIS app?"
Start with "🎯 The Bottom Line:" — never repeat the section name.
Never use generic descriptions. Reference the app's specific architecture.

### Rule 8 — Name Your Gotchas
Every `architecture_warnings` entry must have a memorable name.
Format: "🚨 Architecture Warning - The [Name]: [explanation]. Action Required: [prescription]."
Examples: "The 10K Hard Limit Trap", "The SuperAdmin Disconnect", "The Embedded Members Optimization".
Engineers will use these names in code comments, PR reviews, and incident reports.

### Rule 9 — Anti-Patterns and Negative Instructions
For each entity, include at least one explicit "DO NOT" instruction in `architecture_warnings`:
- "Do NOT attempt to find a /members endpoint — membership is embedded on the entity object"
- "Do NOT make secondary API calls for relationships already embedded on the entity payload"
- "Do NOT treat an empty roles list as a failure — it means the account is on a lower tier"
These prevent the single most common implementation mistake for each entity.

## Output JSON Schema

Read `prd_schema.json` for the complete annotated structure. The file is located in the project root.
