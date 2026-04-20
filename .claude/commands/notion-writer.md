# /notion-writer — Create Notion Page from PRD JSON

Sub-agent that takes the final the platform PRD JSON and creates a structured Notion page.
Uses `notion_writer.py` (Python, no Anthropic dependency — only notion-client + python-dotenv).

Invoked by the `/integration` orchestrator as Sub-Agent F. Can also be run standalone.

## Usage

This skill is invoked by the orchestrator with the final PRD JSON as input.
It is not typically run standalone, but can be:
```
/notion-writer  (paste JSON when prompted)
```

## Steps

1. **Write the JSON to a temp file**:
   ```bash
   cat > /tmp/integration_prd.json << 'EOF'
   <the full PRD JSON>
   EOF
   ```

2. **Run notion_writer.py**:
   ```bash
   python3 notion_writer.py /tmp/integration_prd.json
   ```

3. **Report the result**:
   - If successful: print the Notion page URL prominently
   - If Notion 401: "Check NOTION_TOKEN and ensure the integration is connected to the parent page"
   - If Notion 404: "Check NOTION_PARENT_PAGE_ID — page not found or integration not connected"
   - If Python error: show the traceback and suggest running `/setup-check`

4. **Clean up**:
   ```bash
   rm -f /tmp/integration_prd.json
   ```

## Error Handling

| Error | Message to show |
|---|---|
| NOTION_TOKEN missing | Run `/setup-check` — NOTION_TOKEN not set |
| 401 Unauthorized | Check NOTION_TOKEN; ensure integration is connected to parent page via ··· menu |
| 404 Not Found | Check NOTION_PARENT_PAGE_ID in .env |
| notion-client not installed | Run: pip install -r requirements.txt |
| JSON syntax error | The Identity Mapper produced invalid JSON — re-run `/identity-mapper` |
