# /prd-audit — Audit a Generated Integration Spec

Reviews a generated integration spec for completeness, accuracy, and confidence.
Flags sections needing PM validation and suggests targeted follow-up searches.

## Usage
```
/prd-audit <AppName or Notion URL>
```

## Steps

1. **Locate the spec**:
   - If a Notion URL: fetch with WebFetch
   - If an app name: look for `/tmp/integration_prd.json` or ask the user to paste content

2. **Check each section** against these criteria:

| Check | Pass Criteria |
|---|---|
| Section populated | No "Data unavailable" in critical fields |
| Confidence ≥ 7 | Flag sections below 7 for PM review |
| Endpoints are real HTTP paths | Not vague descriptions |
| Auth scopes are exact names | Not generic descriptions like "admin access" |
| Remediation actions complete | HTTP method + endpoint + request body present |
| NHI detection logic present | human vs non-human distinction documented |
| All 5 relations described | account→group, account→role, account→resource, group→role, group→resource |

3. **Output audit report**:

```markdown
## PRD Audit: <AppName>

### Overall
- Sections complete: 8 / 10
- Low-confidence flags: 2
- Critical gaps: 1

### Section Review

#### ✅ Authentication — 10/10
OAuth 2.0 fully documented with exact scopes from OpenAPI spec.

#### ⚠️ Entity: Roles — 5/10
Modeling approach documented but list_endpoint and assignment_endpoint missing.
Suggested search: `<App> API roles list endpoint assignments`

#### 🔴 Remediation: Change User Role — 3/10
No endpoint found. Request body undocumented.
**Requires PM validation before engineering.**

### Gap Summary
| Section | Issue | Priority |
|---|---|---|
| Roles | list_endpoint missing | High |
| Remediation: Change Role | No endpoint | Critical |

### Suggested Follow-Up Searches
1. `<App> API list roles endpoint`
2. `<App> API update user role PATCH request body`

### Verdict
⚠️ Not ready for engineering. Resolve 1 critical gap.
```
