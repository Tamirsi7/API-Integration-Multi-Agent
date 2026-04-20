# /batch-integrations — Generate Specs for Multiple Apps

Runs `/integration` sequentially for a list of SaaS applications.
Each app gets its own Notion page. A summary report is printed at the end.

## Usage
```
/batch-integrations <App1>, <App2>, <App3>, ...
```
**Example:** `/batch-integrations GitHub, Salesforce, Okta, Slack`

## Steps

1. **Parse app list** — split `$ARGUMENTS` by comma, trim whitespace.

2. **Validate environment** — check NOTION_TOKEN and NOTION_PARENT_PAGE_ID before starting.
   If missing, stop and direct user to `/setup-check`.

3. **Process each app** sequentially (not in parallel — avoids rate limit issues):
   - Print: `━━━ [2/4] Processing: Salesforce ━━━`
   - Run `/integration <AppName>` for each app
   - Capture: Notion URL, data source type, success/failure
   - On failure: log the error, continue to next app (do not abort batch)
   - Wait 5 seconds between apps

4. **Print batch summary**:

```markdown
## Batch Results

| # | App | Status | Data Source | Notion Page |
|---|---|---|---|---|
| 1 | GitHub | ✅ Done | OpenAPI spec | https://notion.so/... |
| 2 | Salesforce | ✅ Done | HTML docs | https://notion.so/... |
| 3 | Okta | ✅ Done | OpenAPI spec | https://notion.so/... |
| 4 | Slack | ❌ Error | — | Notion write failed (see above) |

### Summary
- ✅ Successful: 3/4
- ❌ Failed: 1/4 — retry with `/integration Slack`
- OpenAPI specs found: 2/4
```
