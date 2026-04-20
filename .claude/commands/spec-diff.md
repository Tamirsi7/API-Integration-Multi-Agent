# /spec-diff — Compare Two Integration Specs

Compares two the platform PRD JSON files section-by-section and produces a structured diff.

Useful for:
- Detecting regressions when re-running `/integration` on the same app
- Comparing coverage between similar apps (e.g., GitHub vs GitLab)
- Tracking confidence score improvements over time

## Usage
```
/spec-diff <file1_path> <file2_path>
```

**Example:**
```
/spec-diff /tmp/github_v1.json /tmp/github_v2.json
```

## Instructions

1. **Read both JSON files** using the Read tool.
2. **Compare section by section** across all PRD sections.
3. **Highlight differences** in: field values, confidence scores, presence/absence of data.

## What to Compare

### Section-level comparison
For each PRD section (overview, authentication, rate_limits, pagination, entity_accounts, entity_groups, entity_roles, entity_resources, entity_relations, remediation_actions, technical_references):

- **Confidence delta**: did the score go up or down?
- **New fields**: keys present in file2 but not file1
- **Removed fields**: keys present in file1 but not file2
- **Changed values**: values that differ between the two files

### Entity field mapping comparison
For each entity's `key_response_fields` dict, show which the platform→API mappings changed.

### Remediation action comparison
Show which actions were added, removed, or changed between the two specs.

### Technical references comparison
Show which URLs were added or removed.

## Output Format

```markdown
## Spec Diff: <App> v1 vs v2

### Summary

| Metric | File 1 | File 2 | Delta |
|---|---|---|---|
| Data source | html_docs | openapi_spec | ⬆️ Upgraded |
| Avg confidence | 6.2/10 | 8.7/10 | ⬆️ +2.5 |
| Sections with data | 9/11 | 11/11 | ⬆️ +2 |
| Remediation actions | 5 | 8 | ⬆️ +3 |
| Technical references | 4 | 9 | ⬆️ +5 |

### Confidence Changes

| Section | v1 | v2 | Change |
|---|---|---|---|
| Authentication | 6 | 9 | ⬆️ +3 |
| Entity: Accounts | 7 | 10 | ⬆️ +3 |
| Entity: Roles | 3 | 7 | ⬆️ +4 |
| Rate Limits | 8 | 8 | — |

### Changed Values

**authentication.method:** `API Key` → `OAuth 2.0`
**entity_accounts.list_endpoint:** `GET /users` → `GET /api/v2/users`

### New in v2
- entity_accounts.key_response_fields.last_login: `last_seen_at`
- remediation_actions: suspend_account (was missing in v1)
- remediation_actions: change_group_role (was missing in v1)

### Removed from v1
- (nothing removed)

### Entity Field Mapping Changes

**Accounts:**
| the platform Field | v1 | v2 |
|---|---|---|
| status | `active` (boolean) | `status` (active\|inactive\|suspended) |
| display_name | `name` | `display_name` |

### Recommendation
v2 is a significant improvement. Consider re-running `/prd-validate` on v2 before writing to Notion.
```
