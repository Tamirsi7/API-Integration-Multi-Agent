# /setup-check — Validate Environment

Checks all prerequisites before running integrations.
Run this once after initial setup or when troubleshooting.

## Usage
```
/setup-check
```

## Steps

1. **Check `.env` file** — Look for `.env` in the project root. Verify:
   - `NOTION_TOKEN` starts with `ntn_` (or legacy `secret_`)
   - `NOTION_PARENT_PAGE_ID` is UUID format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

2. **Check Python** — Run `python3 --version`. Must be 3.8 or higher.

3. **Check packages** — Run `pip show notion-client python-dotenv`.
   If missing: show `pip install -r requirements.txt`.

4. **Test Notion connectivity**:
   ```bash
   python3 -c "
   import os; from dotenv import load_dotenv; load_dotenv()
   from notion_client import Client
   n = Client(auth=os.getenv('NOTION_TOKEN'))
   p = n.pages.retrieve(os.getenv('NOTION_PARENT_PAGE_ID'))
   print('✅ Notion OK —', p.get('url', 'page found'))
   "
   ```
   - 401 → NOTION_TOKEN invalid or integration not created
   - 404 → NOTION_PARENT_PAGE_ID wrong, or integration not connected to page

5. **Output summary**:

```markdown
## Setup Check

| Check | Status | Notes |
|---|---|---|
| .env file | ✅ OK | |
| NOTION_TOKEN | ✅ OK | starts with ntn_ (or secret_) |
| NOTION_PARENT_PAGE_ID | ✅ OK | valid UUID |
| Python 3.x | ✅ OK | Python 3.11.4 |
| notion-client | ✅ OK | v3.0.0 |
| python-dotenv | ✅ OK | v1.2.1 |
| Notion API | ✅ OK | parent page accessible |

### Status: ✅ Ready. Run `/integration <AppName>` to get started.
```

If any checks fail, show exact fix instructions including the Notion Internal Integration setup steps from the README if needed.
