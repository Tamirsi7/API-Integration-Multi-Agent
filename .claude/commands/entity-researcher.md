# /entity-researcher — Map App Entities to the platform Canonical Model

Sub-agent specialized in researching a SaaS application's user, group, role, and resource
structure and mapping every finding to the canonical identity data model (identity_model.json).

Invoked by the `/integration` orchestrator as Sub-Agent C. Can also be run standalone.

## Usage
```
/entity-researcher <AppName>
```

## Instructions

Read `identity_model.json` first to understand the target canonical field names.
Then research the application and map its API fields to the platform fields.

## Researcher Guidance

### NHI (Non-Human Identity) Detection Signals
When researching Accounts, look for these signals to determine if an Account is a Non-Human Identity:
- **account_type field**: values like `service_account`, `api_key`, `bot`, `system`
- **Email patterns**: noreply@, system@, svc@, robot@, no-reply@, automated@
- **Display name keywords**: bot, service, api, automation, system, machine, daemon, worker, pipeline, integration, connector
- **Behavioral**: last_login is null AND account has existed >30 days
- **Creation method**: account created via API (not web UI)
- **Security config**: no MFA/SSO configuration
- **Known service patterns**: GitHubApp, Jenkins, Dependabot, CircleCI, Terraform

If the app provides an explicit account type field, use it (confidence 10/10). If NHI must be inferred from email/name patterns, mark confidence 5-7/10.

### NHI Mitigation When Direct Detection Is Impossible
If the Users API does not expose machine identities (private apps, API keys, bots, integrations),
do NOT simply report "NHI detection not possible." Instead, investigate:

1. **Audit / Activity Log APIs**: Search: `$ARGUMENTS API audit log activity events endpoint`
   - Check if actions can be attributed to app IDs, integration IDs, or token IDs
     not present in the human user table
   - If found, document as "NHI Synthesis via Audit Logs" — specify endpoint, actor field
     (e.g., appId, integrationId), and strategy for synthesizing Virtual Service Accounts

2. **Integration / Connected App registries**: Search: `$ARGUMENTS API integrations apps connected list`
   - Some apps expose a list of installed integrations/connected apps via API
   - These can be ingested as NHI Account records

3. **API Key / Token list endpoints**: Search: `$ARGUMENTS API keys tokens list manage`
   - If the app exposes API key management endpoints, each key is an NHI

4. **OAuth Apps / Installed Integrations**: Search: `$ARGUMENTS API installed apps oauth applications connected integrations list endpoint`
   - OAuth applications and third-party integrations authorized to act on behalf of users are machine actors — they are almost never included in the standard user list
   - If an endpoint exists (e.g., GET /orgs/{org}/installations), document it and treat each entry as an NHI Account record
   - If no endpoint exists, explicitly flag: `⚠️ NHI Blindspot: OAuth-authorized apps are not discoverable via the API`

Only write "NHI detection not possible" if ALL four investigation paths return nothing.

**Mandatory output requirement:** Every Accounts section MUST close with one of:
- `✅ NHI detection: <method and field> (Confidence: X/10)`
- `⚠️ NHI Blindspot: System-level machine identities are not exposed in standard user endpoints. Workaround: <strategy or "none found">`

### Common API Patterns by Entity
- **Groups**: GET /groups, /teams, /orgs, /workspaces, /departments
- **Roles**: inline on user object, GET /roles, GET /role-assignments, permission flags
- **Resources**: GET /repos, /projects, /workspaces, /dashboards, /buckets
- **Relations**: GET /groups/{id}/members, /users/{id}/groups, /repos/{id}/collaborators

### Common Resource Types by App Category
- **Code hosting**: repository, organization, team, branch, environment
- **Project management**: project, workspace, board, space
- **CRM**: organization, pipeline, report, dashboard
- **Cloud infrastructure**: organization, project, bucket, cluster, database, secret
- **Identity provider**: application, directory, group, policy
- **Communication**: workspace, channel, app
- **Observability**: organization, dashboard, monitor, alert_policy

---

## Research Steps

### Entity: Accounts
Search: `$ARGUMENTS REST API users list GET endpoint response fields`
Search: `$ARGUMENTS API user object fields id email status type`
Search: `$ARGUMENTS API system admin global administrator discoverable list endpoint superadmin`

Extract:
- List endpoint: HTTP METHOD + path (e.g., `GET /users`)
- Get single endpoint: HTTP METHOD + path (e.g., `GET /users/{id}`)
- Response field mapping to the platform canonical fields:
  - the platform `id` → app field name (e.g., `id`, `user_id`, `uid`)
  - the platform `email` → app field name (e.g., `email`, `primary_email`)
  - the platform `display_name` → app field name (e.g., `name`, `login`, `username`, `display_name`)
  - the platform `status` → app field name + possible values (e.g., `active`, `state: active|inactive`)
  - the platform `account_type` → how to detect human vs NHI (type field, email pattern, name pattern)
- Filter parameters (e.g., `?type=service_account`, `?active=true`)

**System Admin Discoverability:**
- Are global/system-level admins returned in the standard user list endpoint?
- Is there a separate boolean flag (e.g., `is_admin`, `superAdmin`, `god_mode`) that must be evaluated independently of the role system?
- If system admins are NOT discoverable via the standard user endpoint or any role/permission API, flag explicitly:
  `⚠️ Architecture Warning - The Admin Blindspot: System-level admins are not discoverable via the API. Action Required: Document as a visibility gap; do not silently miss these accounts.`

### Entity: Groups
Search: `$ARGUMENTS API groups teams organizations list endpoint`
Search: `$ARGUMENTS API team members list GET`

Extract:
- List endpoint, get endpoint, members endpoint
- Key response fields (id, name, type, description)

### Entity: Roles
Search: `$ARGUMENTS API roles permissions model assignment`
Search: `$ARGUMENTS API user role field inline permission set`

Extract:
- How roles are modeled: inline_on_user | separate_role_objects | permission_sets | scoped_roles
- List roles endpoint (if exists)
- Role assignment endpoint
- Key role fields and values

### Admin Flags Outside the Role System
Many apps have a highest-privilege boolean (superAdmin, is_admin, god_mode, etc.) that is
COMPLETELY DECOUPLED from the role/permission-set assignment. A user can have an empty roles
array but still be a super admin.

Search: `$ARGUMENTS API user superadmin admin flag boolean privilege`
If found: document that engineers must evaluate this flag independently and map it to a
synthetic the platform role (e.g., "Super Admin" or "System Administrator").

### Tier-Dependent API Behavior
Some endpoints only return data on certain subscription tiers (Enterprise, Pro, etc.).
On lower tiers they return empty results — NOT errors.

Search: `$ARGUMENTS API roles permissions enterprise plan tier availability`
Search: `$ARGUMENTS API SCIM roles enterprise plan required tier gating`
If found:
- Document which endpoints are tier-dependent
- Document what the API returns on lower tiers (empty array / 403 / 404)
- Add to output: `Tier requirement: Enterprise / Pro / Free | Lower-tier behavior: <empty results / 403 / 404>`
- Instruct engineers to handle empty results as a valid response (zero entities), not a failure
- Flag as: `⚠️ ARCHITECTURE WARNING - The Tier Trap: [endpoint] returns empty results on [plan], not an error. Action Required: Do NOT retry or error-handle empty role lists — treat as a valid zero-entity response.`

### Entity: Resources
Search: `$ARGUMENTS API resources projects repositories workspaces list`
Search: `$ARGUMENTS API collaborators access permissions resource`
Search: `$ARGUMENTS API bulk ACL access list all resources permissions single endpoint`
Search: `$ARGUMENTS API enterprise tier required resources SCIM plan`

Extract:
- All major resource types (repositories, projects, workspaces, etc.)
- List endpoint per resource type
- Endpoint to list who has access to a resource
- Key response fields
- **Tier gating**: Are any resource types or their ACL endpoints locked to Enterprise/Pro plans?
  - Add: `Tier requirement: <plan> | Lower-tier behavior: <empty results / 403 / 404>`

**Bulk ACL Availability Check (MANDATORY):**
Determine how "who has access to a resource" is resolved:
- Is there a **bulk endpoint** that returns access edges across ALL resources in a single call?
- Or does resolving access require **iterating over every single resource individually** (one API call per resource)?

If no bulk ACL endpoint exists:
- Flag explicitly: `⚠️ ARCHITECTURE WARNING - The O(N) Fetch Explosion: No bulk ACL endpoint exists. Resolving access edges requires one API call per resource. For an org with N resources, this is N sequential calls. Action Required: Implement a queue-based resource iterator with rate-limit-aware throttling (e.g., token bucket). Cache resource lists between sync cycles to avoid re-fetching unchanged resources.`

### Resource Access Model Investigation
Many SaaS apps do NOT have explicit per-resource ACL endpoints (e.g., /resources/{id}/access).
Instead, access is determined by properties ON the resource object itself.
Always investigate these patterns when no ACL endpoint is found:

1. **Ownership properties**: Does the resource object have an `owner_id`, `created_by`,
   `assigned_to`, or similar field that references an Account?
   Search: `$ARGUMENTS API {resource_type} object properties owner assigned_to fields`
2. **Team/Group properties**: Does the resource have a `team_id` or `group_id` property
   that references a Group?
   Search: `$ARGUMENTS API {resource_type} object team property group assignment`
3. **Permission-set-driven only**: Is access entirely governed by global roles with no
   per-resource granularity? (If so, document this explicitly)

If ownership/team properties exist on resource objects:
- Document them as the access resolution mechanism for Account→Resource and Group→Resource edges
- Note the exact property name and which the platform entity it maps to
- Tag as "Property-Driven Access" in the relations section
- Identify the correct API to FETCH these resources (may be a Search API, not a simple GET list)
- Include the search/fetch endpoint as a resource list endpoint alongside any structural endpoints (e.g., pipelines)

### Entity Relations
Based on all findings, describe all 5 relations:
- Account → Group (how membership is represented in the API)
- Account → Role (how role assignment is represented)
- Account → Resource (how direct access grants are represented)
- Group → Role (how group-level role assignment works)
- Group → Resource (how group access to resources is represented)

## Output Format

Return structured markdown with full field mappings and confidence scores:

```markdown
## Entity Research: <AppName>

### Accounts
- List: GET /users
- Get: GET /users/{id}
- Field mapping:
  | the platform Field | API Field | Notes |
  |---|---|---|
  | id | id | integer |
  | email | email | primary email |
  | display_name | login | GitHub username |
  | status | active | boolean → active/inactive |
  | account_type | type | User=human, Bot=bot |
- NHI detection: type == "Bot" OR login ends with [bot]
- Filter params: ?type=all, ?since=<id>
- 🟢 Confidence: 10/10 | Source: OpenAPI spec

### Groups
...

### Roles
...

### Resources
...

### Entity Relations
| Relation | API Representation | Endpoint |
|---|---|---|
| Account → Group | GET /orgs/{org}/members | member.role field |
...
```

## Zero Hallucination
Use exact field names from the API. If a field doesn't exist, write "Data unavailable in public documentation".
