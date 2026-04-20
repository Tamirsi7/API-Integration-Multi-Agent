# /integration — the platform Integration Spec Orchestrator

**The main command.** Orchestrates 7 specialized sub-agents to research a SaaS application's API
and create a fully structured integration spec in Notion.

No Python script. No Anthropic API key. Just Claude + web search + Notion.

## Usage
```
/integration <AppName>
```
**Example:** `/integration GitHub`

---

## Orchestration Steps

### Step 0 — Validate Setup
Check that `.env` exists with `NOTION_TOKEN` and `NOTION_PARENT_PAGE_ID`.
If missing, stop and direct the user to run `/setup-check`.

---

### Step 1 — Launch 4 Sub-Agents IN PARALLEL

Use the Task tool to launch all four simultaneously (single message, four tool calls):

**Sub-Agent A — OpenAPI Scout (general-purpose type)**
Prompt: Research `$ARGUMENTS` to find an official OpenAPI or Swagger specification.
Search queries:
1. `$ARGUMENTS OpenAPI spec JSON YAML site:github.com OR site:swaggerhub.com`
2. `$ARGUMENTS swagger.json openapi.yaml download official`
3. `$ARGUMENTS API openapi specification developer docs`

HARD STOP: If WebSearch or WebFetch tools return permission errors or are unavailable,
return EXACTLY this block and nothing else:
```
## OpenAPI Scout Result: <App>
- NOT FOUND (web access unavailable in this execution context)
- Spec URL: not found
- Confidence: 0
- Error: WebSearch/WebFetch denied — orchestrator will fall back to main-session research
```
DO NOT guess, invent, or assume any URLs. An honest "not found" is always correct.

Return a structured markdown block:
```
## OpenAPI Scout Result: <App>
- FOUND / NOT FOUND
- Spec URL: <url or "not found">
- Format: OpenAPI 3.x / Swagger 2.0 / not found
- Auth schemes detected: <list>
- Key entity endpoints detected: <list of relevant paths>
- Confidence: 10 (spec found) / 3 (not found, will use HTML docs)
```

**Sub-Agent B — API Info Researcher (general-purpose type)**
Prompt: Research `$ARGUMENTS` API for: authentication method, rate limits, and pagination.
Search queries:
1. `$ARGUMENTS REST API authentication OAuth scopes credentials`
2. `$ARGUMENTS API rate limits headers retry strategy`
3. `$ARGUMENTS API pagination cursor offset page parameters`
4. `$ARGUMENTS API SCIM REST base URL identity management separate endpoint paradigm`
5. `$ARGUMENTS API rate limit headers proactive quota remaining X-RateLimit`
6. `$ARGUMENTS API pagination Link header RFC 5988 offset 0-indexed 1-indexed`

IMPORTANT: If WebFetch on the official docs URL returns a login redirect, Next.js bundle,
or 404 — pivot immediately to one of these alternatives:
1. Search for the raw OpenAPI spec on GitHub (github.com/<org>/<app>-api-spec or similar)
2. Use WebSearch to extract facts from Google's indexed version of the docs page
3. Try the app's Postman public workspace (postman.com/<org>/public-workspace)
Do NOT retry the same SPA URL.

REQUIRED CHECKS (every section must address ALL of these):
- **API Surface Fragmentation**: Do identity management and resource management use different base URLs, token types, or paradigms (SCIM vs REST vs GraphQL)?
- **Rate limit header strategy**: Proactive headers (X-RateLimit-Remaining on every response) or reactive-only (429 with no advance warning)? List any endpoint-specific burst limits.
- **Pagination token location**: Is the next-page token in the HTTP `Link` header or in the JSON body?
- **Offset indexing**: Is offset/page 0-indexed or 1-indexed?
- **Tier gating on auth**: Are any auth methods (especially SCIM) locked to Enterprise/Pro plans?

Every section MUST end with: `- Confidence: X/10 | Source: <source> | Justification: <1 sentence>`

Return structured markdown:
```
## API Info: <App>
### API Surface Fragmentation
- Identity API base URL + auth type: ...
- Resource API base URL + auth type: ...
- Paradigm divergence: SCIM / REST / GraphQL / none
- ⚠️ ARCHITECTURE WARNING (if fragmented): ...
- Confidence: X/10 | Source: <source> | Justification: <1 sentence>

### Authentication
- Method: <OAuth 2.0 / API Key / Bearer / Basic Auth>
- Credentials required: <list>
- Scopes required: <exact scope names>
- Token endpoint: <URL>
- Notes: <token expiry, refresh, header format>
- Tier gating: <enterprise-only methods noted>
- Confidence: <score> | Source: <OpenAPI spec / HTML docs> | Justification: <1 sentence>

### Rate Limits
- Limit: <e.g. 5000 req/hour>
- Scope: <per token / per user / per IP>
- Headers: <exact header names e.g. X-RateLimit-Remaining>
- Header strategy: <proactive / reactive-only>
- Endpoint-specific burst limits: <list or "none found">
- Retry strategy: <e.g. backoff on 429, check Retry-After>
- Confidence: <score> | Source: <source> | Justification: <1 sentence>

### Pagination
- Strategy: <cursor / offset / keyset / page-based / link-header>
- Request params: <list>
- Response fields: <list>
- Link header: <yes — format / no>
- Offset indexing: <0-indexed / 1-indexed>
- Notes: <max page size, edge cases>
- Confidence: <score> | Source: <source> | Justification: <1 sentence>
```

**Sub-Agent C — Entity Researcher (general-purpose type)**
Prompt: Research `$ARGUMENTS` API for: user/account endpoints, groups/teams, roles/permissions,
and resource types. Map ALL findings to the canonical identity model in identity_model.json.
Search queries:
1. `$ARGUMENTS REST API users list endpoint response fields`
2. `$ARGUMENTS API system admin global administrator discoverable superadmin boolean`
3. `$ARGUMENTS API groups teams members endpoint`
4. `$ARGUMENTS API roles permissions model assignment enterprise tier`
5. `$ARGUMENTS API resources projects repositories workspaces`
6. `$ARGUMENTS API bulk ACL access list all resources permissions endpoint`
7. `$ARGUMENTS API installed apps oauth applications connected integrations NHI`

IMPORTANT: If WebFetch on the official docs URL returns a login redirect, Next.js bundle,
or 404 — pivot immediately to one of these alternatives:
1. Search for the raw OpenAPI spec on GitHub (github.com/<org>/<app>-api-spec or similar)
2. Use WebSearch to extract facts from Google's indexed version of the docs page
3. Try the app's Postman public workspace (postman.com/<org>/public-workspace)
Do NOT retry the same SPA URL.

REQUIRED CHECKS (must address ALL of these):
- **System admin discoverability**: Are global/system admins in the standard user list, or hidden behind a separate boolean (`is_admin`, `superAdmin`)? If not discoverable, flag as a blindspot.
- **NHI completeness**: Check all 4 paths: (1) audit logs, (2) integration registries, (3) API key endpoints, (4) OAuth app installations. Every Accounts section MUST end with ✅ NHI detection or ⚠️ NHI Blindspot.
- **O(N) ACL fetch**: Is there a bulk endpoint to resolve who has access to ALL resources? If not, flag as O(N) fetch explosion.
- **Tier gating**: For Roles and Resources, document which plan is required and what the API returns on lower tiers.

Every section MUST end with: `- Confidence: X/10 | Source: <source> | Justification: <1 sentence>`

Return structured markdown covering all 4 canonical entities with API field → the platform field mappings,
confidence scores, NHI detection logic, and entity relations table.

**Sub-Agent A2 — Doc Collector (general-purpose type)**
Prompt: Collect and validate official documentation URLs for `$ARGUMENTS` API.
Follow the instructions in `/doc-collector`.

IMPORTANT: If WebFetch on the official docs URL returns a login redirect, Next.js bundle,
or 404 — pivot immediately to one of these alternatives:
1. Search for the raw OpenAPI spec on GitHub (github.com/<org>/<app>-api-spec or similar)
2. Use WebSearch to extract facts from Google's indexed version of the docs page
3. Try the app's Postman public workspace (postman.com/<org>/public-workspace)
Do NOT retry the same SPA URL.

Return a structured table of `[Section, Label, URL, Status]`.

---

### Step 1 Error Handling + Timeout Rules

**2-Timeout Kill Rule (CRITICAL):**
- Poll each background sub-agent with `TaskOutput` at most **twice** (3-minute timeout each poll)
- If an agent has not completed after 2 polls → **kill it immediately** with `TaskStop` and do the research in the main session using the same search queries
- Do NOT wait for a slow agent more than twice — main-session WebFetch/WebSearch calls are faster than re-polling

**Sub-agent failure handling:**
1. Log: `⚠️ Sub-Agent [Name] failed: <reason>`
2. **Retry ONCE** as `general-purpose` type — sub-agents sometimes lose web access at task spawn
3. If still failing after 1 retry: fall back to main-session research immediately
4. **Never proceed to Step 3 (Identity Mapper) with zero data from ALL agents** — stop and report error
5. For individual section failures: Identity Mapper uses `"Data unavailable in public documentation"`
   + confidence score 1; flag prominently in the Step 5 summary
6. Suggest retry: `Run /entity-researcher <App> to retry the failed section`

---

### Step 2 — Do Remediation Research IN THE MAIN SESSION (not a sub-agent)

**Do NOT spawn a sub-agent for remediation.** Remediation is only 6–8 targeted WebFetch calls.
Run them directly in the main session in parallel while waiting for Step 1 agents to finish.

Fetch the following endpoint docs directly (adapt URLs to the app being researched):
- Add user to group/team endpoint
- Remove user from group/team endpoint
- Add user to resource (grant access) endpoint
- Remove user from resource (revoke access) endpoint
- Change user role endpoint
- Suspend/deactivate user endpoint (REST + SCIM if applicable)
- Delete/deprovision user endpoint

Use the endpoint slugs discovered by the OpenAPI Scout or Doc Collector.
Run all fetches in parallel (single message, multiple WebFetch tool calls).

Compile results as structured markdown:
```
## Remediation: <Action Name>
- HTTP Method: POST/PATCH/DELETE
- Endpoint: /path/to/endpoint
- Request Body: { "field": "value" }
- Required Scopes: [list]
- Tier requirement: <Enterprise / Pro / Available on all plans>
- Notes: <any important details>
- Confidence: <score> | Source: <source> | Justification: <1 sentence>
```

For **every** action also verify: Is this endpoint gated behind a paid plan? If yes, what does the API return on lower tiers (403, 404, empty response)?

**Timing:** Start remediation fetches as soon as Sub-Agent A (OpenAPI Scout) or A2 (Doc Collector)
returns — you will have the endpoint slugs needed. Do not wait for Sub-Agent C (Entity Researcher).

---

### Step 2.5 — Confidence Validation Gate

Before spawning the Identity Mapper, validate that every sub-agent output contains confidence scores.

For each sub-agent result (A, B, C, A2, D), check that each returned section ends with:
`Confidence: X/10 | Source: <source> | Justification: <1 sentence>`

If any section is **missing** a confidence score:
- Do NOT ask the sub-agent to re-run
- Insert a fallback confidence annotation inline:
  `[CONFIDENCE MISSING — defaulting to 1/10 | Source: sub-agent output incomplete | Justification: Confidence scores absent from sub-agent output — requires human PM validation]`
- Flag it in the Step 5 summary under "Low-confidence sections needing review"

This ensures `_confidence` objects are never omitted in the final JSON, which would cause the Notion Writer to silently drop confidence callouts from the PRD.

---

### Step 3 — Identity Mapper Sub-Agent

**Sub-Agent E — Identity Mapper (general-purpose type)**
Provide it: the outputs from Sub-Agents A, B, C, A2, D and the contents of `identity_model.json` and `prd_schema.json`.
Task: Merge all research into a single canonical JSON object matching the full PRD schema.

Critical requirements:
- Read `prd_schema.json` first — the output must match its structure exactly
- `key_response_fields` for ALL entities must be a **dict**. Values can be plain strings OR `{api_field, notes}` objects — use objects when a field needs critical context.
- `entity_relations` entries must be **objects** with `{resolution_strategy, description, endpoint, doc_url}`. `resolution_strategy` is one of: `embedded_on_object | property_driven | separate_endpoint | client_side_aggregation | data_limitation`.
- `technical_references` must be populated from the Doc Collector output
- Every section must have a `_confidence` object
- Every section must have a `bottom_line` field — a 🎯-prefixed 1-2 sentence engineering summary specific to THIS app
- Every entity section and `remediation_actions` must have an `architecture_warnings` array — named warnings with Action Required prescriptions
- `remediation_actions` is now an **object** with `{bottom_line, architecture_warnings, actions: [...]}` — not a bare array
- Apply zero hallucination — any field not confirmed: `"Data unavailable in public documentation"`
- `api_version`: Extract the exact API version string from docs (e.g. "REST API v3", "Graph API 1.0"). If not explicitly stated, write `"Data unavailable in public documentation"`
- `sync_order`: Array of step objects `{step, entities, rationale}` — ordered by API dependencies. Each step explains WHY those entities go in that order.
- `developer_summary`: 3-4 sentences. Critical takeaways, bottlenecks, and gotchas. Include cross-cutting concerns: rate limit strategy, pagination traps, NHI discovery. Weave edge-case handling into this and into per-entity `architecture_warnings` (there is no standalone edge_cases section).

The output is a single valid JSON object (the full PRD spec).

---

### Step 4 — Notion Writer Sub-Agent

**Sub-Agent F — Notion Writer (general-purpose type)**
Provide it: the final JSON from Step 3, plus `NOTION_TOKEN` and `NOTION_PARENT_PAGE_ID` from `.env`.
Task:
1. Derive `<app_name_lower>` by lowercasing the app name and replacing spaces with underscores.
2. Write the JSON to a temp file:
   ```bash
   cat > /tmp/<app_name_lower>_prd.json << 'EOF'
   <the full PRD JSON>
   EOF
   ```
3. Run: `python3 notion_writer.py /tmp/<app_name_lower>_prd.json`
4. Report the Notion page URL from stdout.
5. Clean up: `rm -f /tmp/<app_name_lower>_prd.json`

---

### Step 5 — Report to User

Print a summary:
```
✅ Integration spec created for <App>

Notion page: <URL>
Data source: <OpenAPI spec / HTML docs / mixed>

Confidence summary:
  🟢 High (8-10): <N sections>
  🟡 Medium (5-7): <N sections>
  🔴 Low (1-4): <N sections — need PM review>

Low-confidence sections needing review:
  - <section name>: <issue>

Failed sub-agents (if any):
  - <Agent name>: <reason> — retry with /<skill> <App>
```

---

## Zero Hallucination Rule
Never invent API endpoints, scope names, field names, or HTTP methods.
If a sub-agent returns unavailable data, preserve `"Data unavailable in public documentation"` — do not fill it in yourself.
