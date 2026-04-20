# /scim-researcher — Research SCIM 2.0 Provisioning Support

Sub-agent that checks whether a SaaS application supports SCIM 2.0 (System for Cross-domain Identity Management).
SCIM is critical for the platform: it enables automated identity lifecycle management (create, update, deactivate) without REST API calls.

Can be run standalone or as an optional enrichment step after the main integration pipeline.

## Usage
```
/scim-researcher <AppName>
```

## Why It Matters for the platform

SCIM endpoints are often more reliable for provisioning than REST APIs:
- Standardized schema across all apps
- Supports bulk operations
- Explicit `active` flag for suspend/deprovision
- Sometimes available even when REST API lacks a suspend endpoint

## Search Queries

1. `$ARGUMENTS SCIM 2.0 provisioning documentation`
2. `$ARGUMENTS SCIM Users endpoint schema`
3. `$ARGUMENTS SCIM Groups provisioning`
4. `$ARGUMENTS identity provider SSO SCIM setup`
5. `$ARGUMENTS API SCIM base URL token authentication`

## What to Extract

- **SCIM base URL** (e.g., `https://app.example.com/scim/v2`)
- **Authentication method** for SCIM (usually Bearer token, sometimes separate from REST API token)
- **Supported resources**: Users, Groups (not all apps support both)
- **Supported operations** per resource: Create (POST), Read (GET), Update (PUT/PATCH), Delete (DELETE)
- **Schema attributes**: What SCIM fields map to (userName, emails, active, groups, etc.)
- **Plan availability**: Is SCIM available on all plans or enterprise/paid-tier only?
- **Setup location**: Where to configure SCIM in the app's admin UI

## Output Format

```markdown
## SCIM Research: <AppName>

### SCIM Support: ✅ Available / ❌ Not Found / ⚠️ Enterprise Only

| Property | Value |
|---|---|
| SCIM Base URL | https://... |
| Authentication | Bearer token (separate from REST API) |
| Plan Requirement | Enterprise / All plans |

### Supported Resources & Operations

| Resource | Create | Read | Update | Delete |
|---|---|---|---|---|
| Users | ✅ POST /Users | ✅ GET /Users/{id} | ✅ PATCH /Users/{id} | ✅ DELETE /Users/{id} |
| Groups | ✅ POST /Groups | ✅ GET /Groups/{id} | ✅ PATCH /Groups/{id} | ❌ Not supported |

### Key SCIM Attributes (Users)

| SCIM Attribute | Maps To |
|---|---|
| userName | Login / username |
| emails[0].value | Primary email |
| active | Account status |
| groups | Group memberships |

### Remediation via SCIM

| the platform Action | SCIM Endpoint |
|---|---|
| Suspend account | PATCH /Users/{id} → { "active": false } |
| Deprovision account | DELETE /Users/{id} |
| Add to group | PATCH /Groups/{id} → add member |

### Notes
- SCIM token obtained at: <admin UI location>
- Doc URL: <link>

🟢 Confidence: <score>/10 | Source: <source>
```

If SCIM is not found:
```
### SCIM Support: ❌ Not Found
No SCIM 2.0 documentation found for <AppName>. Use REST API endpoints for provisioning.
🔴 Confidence: 2/10 | Source: Not found
```

## Zero Hallucination
Never invent SCIM endpoints or attribute mappings. Only include what is found in official docs.
