# /api-researcher — Research API Authentication, Rate Limits & Pagination

Sub-agent specialized in researching the technical API layer of a SaaS application:
authentication method, rate limiting behavior, and pagination strategy.

Invoked by the `/integration` orchestrator as Sub-Agent B. Can also be run standalone.

## Usage
```
/api-researcher <AppName>
```

## Research Steps

### 1. Find OpenAPI spec or HTML docs
First check if an OpenAPI spec is available — it will contain authoritative answers.
If not, search HTML documentation.

### 2. API Surface Fragmentation
Search: `$ARGUMENTS API SCIM REST base URL identity management separate endpoint paradigm`
Search: `$ARGUMENTS API GraphQL REST multiple APIs identity resource management`

Explicitly verify:
- Do identity management (Users/Groups) and resource management use **different base URLs**?
- Do they require **different token types** (e.g., Bearer vs. OAuth vs. SCIM Bearer)?
- Do they use **different API paradigms** (e.g., SCIM for provisioning vs. REST for resources vs. GraphQL for queries)?

If fragmentation is found:
- Document EACH surface separately: base URL, auth type, which canonical entities it serves
- Flag: `⚠️ ARCHITECTURE WARNING - Fragmented API Surface: [description]. Action Required: [prescription]`

Output:
```
### API Surface Fragmentation
- Identity API base URL: <url or "unified">
- Identity API auth type: <Bearer / API Key / SCIM Bearer>
- Resource API base URL: <url or "same as identity">
- Resource API auth type: <same or different>
- Paradigm divergence: SCIM / REST / GraphQL / none
- ⚠️ ARCHITECTURE WARNING (if fragmented): ...
- Confidence: X/10 | Source: <source> | Justification: <1 sentence>
```

### 3. Authentication
Search: `$ARGUMENTS API authentication OAuth2 API key scopes credentials`
Search: `$ARGUMENTS API SCIM OAuth enterprise tier availability`

Extract:
- Auth method (OAuth 2.0 Authorization Code / Client Credentials, API Key, Bearer, Basic, PAT)
- Exact scope names required for user/group/role/resource read access
- Exact scope names required for remediation (write) operations
- Token endpoint URL
- Header format (e.g., `Authorization: Bearer <token>`, `X-API-Key: <key>`)
- Token expiry and refresh flow
- **Tier gating**: Are any auth methods (especially SCIM or OAuth) locked to Enterprise/Pro plans?

### 4. Rate Limits
Search: `$ARGUMENTS API rate limits headers 429 retry`
Search: `$ARGUMENTS API rate limit headers proactive quota remaining X-RateLimit`
Search: `$ARGUMENTS API endpoint specific rate limit burst secondary limit`

Extract:
- Rate limit value (e.g., 5000 req/hour, 100 req/min)
- Scope (per token, per user, per org, per IP)
- Exact response header names (e.g., `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`)
- **Header strategy**: Does the API provide **proactive quota headers** (e.g., `X-RateLimit-Remaining` on every response) or only **reactive HTTP 429s** with no advance warning?
  - If proactive: list exact header names
  - If reactive-only: flag as `⚠️ No proactive quota headers — implement conservative throttling`
- **Endpoint-specific burst limits**: Some APIs have tighter limits on specific endpoints (e.g., search, audit logs) separate from the global limit. Document any per-endpoint limits found.
- Recommended retry strategy

### 5. Pagination
Search: `$ARGUMENTS API pagination cursor page limit parameters`
Search: `$ARGUMENTS API search endpoint offset pagination limit`
Search: `$ARGUMENTS API pagination Link header RFC 5988`
Search: `$ARGUMENTS API pagination offset index page numbering starts 0 1`

Extract:
- Strategy: cursor | offset | keyset | page-based | link-header
- Request parameters (e.g., `per_page`, `cursor`, `page`, `limit`, `after`)
- Response fields (e.g., `next_cursor`, `has_more`, `total_count`, `Link` header)
- Max page size
- **Link header check**: Is the pagination token/next-page URL embedded in the HTTP `Link` header (RFC 5988) rather than the JSON response body? If yes, document the exact header format.
- **Offset indexing**: Is the offset/page parameter **0-indexed** (starts at 0) or **1-indexed** (starts at 1)? Document explicitly — off-by-one errors here cause data loss on the first or last page.
- Edge cases

⚠️ CRITICAL: Check whether ALL endpoints use the SAME pagination strategy.
Many apps use cursor-based for standard list endpoints but offset-based for Search/filter endpoints.

If strategies differ by endpoint type:
- Document EACH strategy separately as "Strategy A" and "Strategy B"
- Note which entity types / endpoint groups use which strategy
- Flag as: "⚠️ ARCHITECTURE WARNING: Requires two paginator implementations"

Hard record ceilings:
Search: `$ARGUMENTS API pagination offset limit maximum records cap 10000`
If any endpoint has a hard offset ceiling (common: 10,000 records):
- State the exact limit
- Provide the time-windowing workaround: "Sort by createdAt ASC, paginate to ~90% of ceiling,
  checkpoint last record's timestamp, restart with createdAt > checkpoint filter."

## Output Format

Return structured markdown with confidence scores per section:

```markdown
## API Info: <AppName>

### API Surface Fragmentation
- Identity API base URL: https://api.example.com/v1
- Identity API auth type: Bearer token
- Resource API base URL: same / https://resources.example.com/api
- Resource API auth type: same / OAuth 2.0
- Paradigm divergence: SCIM for provisioning, REST for resources
- ⚠️ ARCHITECTURE WARNING (if fragmented): Two separate HTTP clients required...
- 🟢 Confidence: 10/10 | Source: OpenAPI spec | Auth schemes and base URLs confirmed in spec

### Authentication
- Method: OAuth 2.0 Authorization Code Flow
- Credentials: client_id, client_secret, redirect_uri
- Read scopes: read:user, read:org, repo
- Write scopes: write:org, admin:org
- Token endpoint: https://github.com/login/oauth/access_token
- Header: Authorization: Bearer <token>
- Token expiry: No expiry (GitHub PATs); OAuth tokens expire per app config
- Tier gating: SCIM requires Enterprise plan; OAuth available on all tiers
- 🟢 Confidence: 10/10 | Source: OpenAPI spec | GitHub's openapi.github.com spec explicitly defines all auth schemes

### Rate Limits
- Limit: 5000 requests/hour (authenticated), 60/hour (unauthenticated)
- Scope: Per token
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-RateLimit-Used
- Header strategy: Proactive (quota headers present on every response)
- Endpoint-specific burst limits: Search API: 30 req/min; Core API: 5000 req/hour
- Retry: Exponential backoff on 429; check Retry-After header
- 🟢 Confidence: 10/10 | Source: OpenAPI spec

### Pagination
- Strategy: cursor (GraphQL) / link-header (REST)
- Request params: per_page (max 100), page, cursor
- Response: Link header with rel="next", rel="last"; X-Total-Count
- Link header: Yes — next page URL embedded in HTTP Link header, not JSON body
- Offset indexing: 1-indexed (page=1 is first page)
- Max page size: 100
- 🟢 Confidence: 10/10 | Source: OpenAPI spec
```

## Zero Hallucination
Never invent scope names, header names, or endpoint URLs.
Unavailable fields: "Data unavailable in public documentation"
