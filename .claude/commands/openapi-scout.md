# /openapi-scout — Find an App's Official OpenAPI / Swagger Spec

Scout whether a SaaS application publishes a public OpenAPI or Swagger specification.
Used as the first step in every integration — determines confidence level and source quality.

## Usage
```
/openapi-scout <AppName>
```

## Steps

1. **Search for the spec** using WebSearch:
   - `$ARGUMENTS OpenAPI spec JSON YAML site:github.com OR site:swaggerhub.com`
   - `$ARGUMENTS swagger.json openapi.yaml download official`
   - `$ARGUMENTS API reference openapi specification developer`

2. **Validate any URLs found** — use WebFetch to confirm the document starts with `openapi:` or `swagger:`. If it's an HTML page, not a raw spec, discard it.

3. **If spec found** — extract:
   - Format (OpenAPI 3.x or Swagger 2.0)
   - Auth schemes (`securitySchemes`)
   - Total number of paths
   - Endpoints relevant to canonical entities (users, groups, roles, resources)

4. **Output report:**

```markdown
## OpenAPI Scout: <AppName>

### Result: ✅ Found / ❌ Not Found

| Field | Value |
|---|---|
| Spec URL | https://... |
| Format | OpenAPI 3.1 / Swagger 2.0 |
| Auth Schemes | OAuth2, API Key |
| Total Paths | 142 |

### the platform Entity Coverage
| Entity | Found? | Endpoint |
|---|---|---|
| Accounts | ✅ | GET /users |
| Groups | ✅ | GET /teams |
| Roles | ⚠️ Inline only | role field on user object |
| Resources | ✅ | GET /repos |

### Recommendation
→ Confidence: 10/10 — Full OpenAPI spec. Run `/integration $ARGUMENTS`.
```

**If not found:**
```
→ No spec found. /integration will fall back to HTML doc scraping (expected confidence: 7-9/10).
```

5. **Zero hallucination** — Never invent spec URLs. If the URL does not return a valid spec document, say "Data unavailable in public documentation".
