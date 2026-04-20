# /remediation-researcher — Research Remediation Endpoints

Sub-agent specialized in finding the API endpoints the platform uses to take action on identities:
adding/removing users from groups and resources, changing roles, and suspending accounts.

Invoked by the `/integration` orchestrator as Sub-Agent D. Can also be run standalone.

## Usage
```
/remediation-researcher <AppName>
```

## Instructions

Reference `identity_model.json → Remediation.standard_actions` for the full list of actions to research.

## Typical API Patterns (guidance — always verify against actual docs)

| Action | Common HTTP Pattern |
|---|---|
| Add user to group | POST /groups/{id}/members, PUT /teams/{id}/memberships/{user_id} |
| Remove user from group | DELETE /groups/{id}/members/{user_id} |
| Add user to resource | POST /repos/{id}/collaborators/{username}, PUT /projects/{id}/members |
| Remove user from resource | DELETE /repos/{id}/collaborators/{username} |
| Change user role | PATCH /users/{id} with role field, PUT /repos/{id}/collaborators/{username} with permission |
| Change group role | PATCH /repos/{id}/teams/{team_slug} with permission field |
| Suspend account | PATCH /users/{id} with status=suspended or active=false |
| Deprovision account | DELETE /users/{id}, POST /scim/v2/Users/{id} with active=false |

---

## Research Steps

For each standard the platform remediation action, search for the exact API endpoint AND its tier/plan requirements:

**Actions to find:**

1. **Add user to group**
   Search: `$ARGUMENTS API add user member group team POST endpoint`
   Search: `$ARGUMENTS API add user group team enterprise plan required tier`

2. **Remove user from group**
   Search: `$ARGUMENTS API remove user member group team DELETE endpoint`

3. **Add user to resource** (repo, project, workspace)
   Search: `$ARGUMENTS API add collaborator user project repository PUT POST`

4. **Remove user from resource**
   Search: `$ARGUMENTS API remove collaborator user project DELETE`

5. **Change user role** (global or per-resource)
   Search: `$ARGUMENTS API change user role PATCH PUT permission endpoint request body`

6. **Change group role** (on a resource)
   Search: `$ARGUMENTS API change team group role permission on repository project`

7. **Suspend account** (deactivate without delete)
   Search: `$ARGUMENTS API suspend deactivate user account PATCH PUT status`
   Search: `$ARGUMENTS API suspend deactivate user enterprise plan tier required`

8. **Deprovision account** (permanent removal or SCIM)
   Search: `$ARGUMENTS API delete user account SCIM deprovision DELETE`
   Search: `$ARGUMENTS API SCIM deprovision enterprise plan tier required`

## Output Format

For each action found, return:

```markdown
## Remediation: <AppName>

### ✅ Add User to Group
- HTTP: PUT /orgs/{org}/teams/{team_slug}/memberships/{username}
- Request Body: { "role": "member" }
- Required Scopes: admin:org, write:org
- Tier requirement: Available on all plans
- Notes: role can be "member" or "maintainer"
- 🟢 Confidence: 10/10 | Source: OpenAPI spec

### ✅ Remove User from Group
- HTTP: DELETE /orgs/{org}/teams/{team_slug}/memberships/{username}
- Request Body: none
- Required Scopes: admin:org
- Tier requirement: Available on all plans
- Notes: Removes user from team but not from org
- 🟢 Confidence: 10/10 | Source: OpenAPI spec

### ❌ Suspend Account
- HTTP: Data unavailable in public documentation
- Required Scopes: Data unavailable in public documentation
- Tier requirement: Enterprise (if endpoint exists at all)
- Notes: GitHub does not support suspending org members via REST API; SCIM deactivation available for Enterprise Cloud only
- 🔴 Confidence: 2/10 | Source: HTML docs | No suspend endpoint found in GitHub REST API docs
```

**Tier Gating Rule**: For every action, always document `Tier requirement`. If the endpoint is gated behind a paid plan, add an explicit callout:
`⚠️ License Gate: This action requires [Plan Name]. On lower tiers the endpoint returns [403/404/empty]. Action Required: Gate this remediation action behind a plan-tier check before invoking.`

### Indirect Remediation Paths
For each standard action where no direct endpoint exists, investigate workarounds before
marking as "Data unavailable":

**Add/Remove User to Resource**: If no explicit ACL endpoint, check if resource objects
have an owner_id, assigned_to, or similar property that can be PATCHED.
Search: `$ARGUMENTS API update {resource_type} owner PATCH properties reassign transfer`
If found: "Indirect — PATCH resource object to set/clear ownership property"
Note whether the API uses PUT (full-replace) or PATCH (partial-update) semantics.

**Suspend Account**: If no suspend/deactivate endpoint:
- Check if the user's role can be changed to a no-permissions baseline role (effective suspension)
- Check if the user can be removed from all groups (access stripping)
- Check if there's a SCIM deactivation endpoint even when REST doesn't have one
Search: `$ARGUMENTS API deactivate user alternative workaround strip permissions baseline`
If found: "Indirect — strip role assignment to effectively suspend access"

**Change Group Role**: If roles are per-user (not per-group), explicitly document:
"Unsupported — roles assigned per-user, not per-group. Do not implement."

For all indirect actions, document:
- The mechanism: "via role stripping" / "via property modification" / "via SCIM"
- PUT vs PATCH semantics (full-replace is dangerous — must include ALL existing values)

## Zero Hallucination
Never invent endpoints. If an action is not supported by the application or not documented,
explicitly state it and give a low confidence score.
