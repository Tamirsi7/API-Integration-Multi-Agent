# /entity-sketch — Quick Entity Model Sketch

Rapidly sketch the 4 canonical entities for a SaaS application using web search.
No Notion page created. Output is structured markdown — ideal for quick assessments
or deciding whether to run a full `/integration`.

## Usage
```
/entity-sketch <AppName>
```

## Steps

1. Run targeted web searches:
   - `$ARGUMENTS REST API users list endpoint response fields`
   - `$ARGUMENTS API groups teams members`
   - `$ARGUMENTS API roles permissions model`
   - `$ARGUMENTS API resources projects workspaces`

2. Output the sketch:

```markdown
## Entity Sketch: <AppName>
*Quick research — not a full spec. Run `/integration <AppName>` for the complete PRD.*

### 🧑 Accounts
| Field | Value |
|---|---|
| List Endpoint | GET /users |
| Key Fields | id, email, login, type, site_admin |
| NHI Detection | type == "Bot" OR login ends with [bot] |
| Filter Params | ?type=all&since=<id> |

### 👥 Groups
| Field | Value |
|---|---|
| List Endpoint | GET /orgs/{org}/teams |
| Members Endpoint | GET /orgs/{org}/teams/{slug}/members |
| Key Fields | id, name, slug, description, privacy |

### 🎭 Roles
| Field | Value |
|---|---|
| Modeling | Scoped roles per resource (org-level + repo-level) |
| Values | owner, member, maintainer, admin, write, read, triage |
| Endpoint | Inline on membership/collaboration response |

### 📦 Resources
| Resource Type | List Endpoint |
|---|---|
| Repository | GET /orgs/{org}/repos |
| Organization | GET /user/orgs |

### Entity Relations
| Relation | How |
|---|---|
| Account → Group | GET /orgs/{org}/teams/{slug}/members |
| Account → Role | Inline on user object + scoped per resource |
| Account → Resource | GET /repos/{owner}/{repo}/collaborators |
| Group → Role | Inline on team response (permission field) |
| Group → Resource | GET /repos/{owner}/{repo}/teams |

### the platform Coverage
| Entity | Available? | Confidence |
|---|---|---|
| Accounts | ✅ Full | High |
| Groups | ✅ Full | High |
| Roles | ⚠️ Partial (scoped) | Medium |
| Resources | ✅ Full | High |

**Recommendation:** Ready for full spec. Run `/integration $ARGUMENTS`.
```

## Zero Hallucination
Mark any unconfirmed field as "Data unavailable in public documentation".
