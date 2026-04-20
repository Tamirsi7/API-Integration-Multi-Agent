# /prd-validate — Validate PRD JSON Before Notion Write

Validates a generated PRD JSON file against the expected structure in `prd_schema.json`.
Catches structural issues before they reach `notion_writer.py`.

Run this between `/identity-mapper` and `/notion-writer` to prevent silent failures.

## Usage
```
/prd-validate  (paste the PRD JSON when prompted, or provide a file path)
```

## Instructions

1. **Read `prd_schema.json`** from the project root to understand the expected structure.

2. **Read the PRD JSON** (from clipboard, file path, or prior `/identity-mapper` output).

3. **Check each of the following:**

### Required Top-Level Keys
Verify these keys exist: `app_name`, `data_source`, `overview`, `authentication`, `rate_limits`, `pagination`, `entity_accounts`, `entity_groups`, `entity_roles`, `entity_resources`, `entity_relations`, `remediation_actions`, `technical_references`, `sync_order`, `developer_summary`

### `bottom_line` Fields
Every section object must have a `bottom_line` string starting with "🎯". Check: overview, authentication, rate_limits, pagination, entity_accounts, entity_groups, entity_roles, entity_resources, entity_relations, remediation_actions.

### `architecture_warnings` Arrays
Every entity section and `remediation_actions` must have an `architecture_warnings` array. Check: entity_accounts, entity_groups, entity_roles, entity_resources, entity_relations, remediation_actions. Flag if missing.

### `_confidence` Objects
Every section must have a `_confidence` with: `score` (integer 1-10), `source` (string), `justification` (string).
Sections: overview, authentication, rate_limits, pagination, entity_accounts, entity_groups, entity_roles, entity_resources, entity_relations, and each item in remediation_actions.actions.

### `key_response_fields` Type
For `entity_accounts`, `entity_groups`, `entity_roles`, `entity_resources` — `key_response_fields` must be a **dict** (object), NOT an array. Values can be strings or `{api_field, notes}` objects.
Flag any that are arrays.

### `entity_relations` Structure
Each of the 5 relation keys must be an **object** with `resolution_strategy`, `description`, `endpoint`, `doc_url`.
`resolution_strategy` must be one of: `embedded_on_object | property_driven | separate_endpoint | client_side_aggregation | data_limitation`.

### `sync_order` Structure
Must be an array of step objects, each with `step` (integer), `entities` (array), `rationale` (string).
Flag if it's a flat array of strings (legacy format).

### `technical_references`
Must be a non-empty array. Each item must have `section`, `label`, `url`.
Flag if empty or missing.

### `remediation_actions`
Must be an **object** with `bottom_line`, `architecture_warnings`, and `actions` array. Each action in `actions` must have: `action_name`, `http_method`, `endpoint`, `required_scopes`, `_confidence`.
Flag if `actions` array is empty or if `remediation_actions` is a bare array (legacy format).

## Output Format

```markdown
## PRD Validation: <AppName>

| Check | Status | Issue |
|---|---|---|
| Required top-level keys | ✅ Pass | — |
| _confidence on all sections | ✅ Pass | — |
| key_response_fields is dict | ❌ Fail | entity_groups.key_response_fields is an array |
| entity_relations are objects | ✅ Pass | — |
| technical_references not empty | ⚠️ Warning | Array is empty — no doc URLs collected |
| remediation_actions not empty | ✅ Pass | 6 actions |

### Result: ❌ 1 error, 1 warning — fix before running /notion-writer

### Issues to Fix:
1. `entity_groups.key_response_fields` — change from array to dict: {"id": "api_id_field", "name": "api_name_field", ...}

### Warnings:
1. `technical_references` is empty — run `/doc-collector <AppName>` to populate
```

If all checks pass:
```
### Result: ✅ Valid — safe to run /notion-writer
```
