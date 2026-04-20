#!/usr/bin/env python3
"""
the platform Notion Writer
Receives a PRD JSON file path as argument and creates a structured Notion page.
No Anthropic dependency — only notion-client + python-dotenv.

Usage:
    python3 notion_writer.py /tmp/integration_prd.json
"""

import sys
import os
import json
import datetime

from dotenv import load_dotenv
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

CHUNK_SIZE = 100


def load_env():
    load_dotenv()
    missing = [k for k in ["NOTION_TOKEN", "NOTION_PARENT_PAGE_ID"] if not os.getenv(k)]
    if missing:
        print(f"[ERROR] Missing env vars: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    return os.getenv("NOTION_TOKEN"), os.getenv("NOTION_PARENT_PAGE_ID")


# ── Rich text helpers ─────────────────────────────────────────────────────────

def _rt(text):
    """Plain rich text segment."""
    return [{"type": "text", "text": {"content": str(text)}}]

def _rt_bold(text):
    """Bold rich text segment."""
    return [{"type": "text", "text": {"content": str(text)}, "annotations": {"bold": True}}]

def _rt_link(text, url):
    """Clickable hyperlink rich text segment."""
    return [{"type": "text", "text": {"content": str(text), "link": {"url": url}}}]

def _rt_mixed(segments):
    """Compose multiple rich_text segments into one list.
    Each segment: {"text": "...", "bold": bool, "url": str|None}
    """
    result = []
    for seg in segments:
        item = {"type": "text", "text": {"content": str(seg["text"])}}
        if seg.get("url"):
            item["text"]["link"] = {"url": seg["url"]}
        annotations = {}
        if seg.get("bold"):
            annotations["bold"] = True
        if seg.get("italic"):
            annotations["italic"] = True
        if annotations:
            item["annotations"] = annotations
        result.append(item)
    return result


# ── Block helpers ─────────────────────────────────────────────────────────────

def _h1(t): return {"object": "block", "type": "heading_1", "heading_1": {"rich_text": _rt(t)}}
def _h2(t): return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": _rt(t)}}
def _h3(t): return {"object": "block", "type": "heading_3", "heading_3": {"rich_text": _rt(t)}}

def _para(t):
    rt = t if isinstance(t, list) else _rt(t)
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt}}

def _bullet(t):
    rt = t if isinstance(t, list) else _rt(t)
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt}}

def _quote(t):
    rt = t if isinstance(t, list) else _rt(t)
    return {"object": "block", "type": "quote", "quote": {"rich_text": rt}}

def _divider(): return {"object": "block", "type": "divider", "divider": {}}

def _callout(text, emoji="ℹ️", color="default"):
    rt = text if isinstance(text, list) else _rt(text)
    return {"object": "block", "type": "callout", "callout": {
        "rich_text": rt, "icon": {"type": "emoji", "emoji": emoji}, "color": color
    }}

def _code(text, lang="json"):
    return {"object": "block", "type": "code", "code": {"rich_text": _rt(text), "language": lang}}

def _table(rows):
    if not rows: return _para("(no data)")
    width = len(rows[0])
    table_rows = [
        {"object": "block", "type": "table_row",
         "table_row": {"cells": [[{"type": "text", "text": {"content": str(c)}}] for c in row]}}
        for row in rows
    ]
    return {"object": "block", "type": "table", "table": {
        "table_width": width, "has_column_header": True, "has_row_header": False, "children": table_rows
    }}

def _confidence(conf):
    if not isinstance(conf, dict): return _callout("📊 Confidence: unknown", "📊")
    score = conf.get("score", 0)
    source = conf.get("source", "")
    just = conf.get("justification", "")
    if score >= 8: emoji, color = "🟢", "green_background"
    elif score >= 5: emoji, color = "🟡", "yellow_background"
    else: emoji, color = "🔴", "red_background"
    return _callout(f"📊 Confidence: {score}/10 ({source}) — {just}", emoji, color)

def _get(obj, *keys, default="Data unavailable in public documentation"):
    for k in keys:
        if not isinstance(obj, dict): return default
        obj = obj.get(k)
        if obj is None: return default
    return obj if obj != "" else default

def _bullets(items):
    if not isinstance(items, list) or not items:
        return [_bullet("Data unavailable in public documentation")]
    return [_bullet(str(i)) for i in items]

def _field_mapping_table(krf):
    """Render key_response_fields as a the platform Field → API Field table.
    Supports 3-column format when values are {api_field, notes} objects.
    Accepts dict (preferred) or list (fallback)."""
    if isinstance(krf, dict) and krf:
        filtered = {k: v for k, v in krf.items() if not str(k).startswith("_")}
        has_notes = any(isinstance(v, dict) and "notes" in v for v in filtered.values())
        if has_notes:
            rows = [["the platform Field", "API Field", "Notes"]]
            for k, v in filtered.items():
                if isinstance(v, dict):
                    rows.append([k, str(v.get("api_field", "")), str(v.get("notes", ""))])
                else:
                    rows.append([k, str(v), ""])
            return _table(rows)
        else:
            return _table([["the platform Field", "API Field"]] + [[k, str(v)] for k, v in filtered.items()])
    elif isinstance(krf, list) and krf:
        return _table([["API Field"]] + [[str(f)] for f in krf])
    else:
        return _bullet("Data unavailable in public documentation")

def _relation_entry(rel, key):
    """Extract relation info — supports both new object format and legacy string."""
    entry = rel.get(key, {})
    if isinstance(entry, str):
        return entry, "—", "—"
    if isinstance(entry, dict):
        return (
            entry.get("description", "—"),
            entry.get("endpoint", "—"),
            entry.get("doc_url", "—"),
        )
    return "—", "—", "—"

def _section_doc_url(refs, section_name):
    """Find the first technical_reference URL matching a section name (case-insensitive)."""
    for r in refs:
        if r.get("section", "").lower() == section_name.lower():
            url = r.get("url", "")
            if url and "unavailable" not in url.lower():
                return url
    return ""

def _intro_para(text, doc_url=""):
    """Render a section intro paragraph with optional trailing doc link."""
    if doc_url:
        return _para(_rt_mixed([
            {"text": text + "  "},
            {"text": "→ Official Docs", "url": doc_url},
        ]))
    return _para(text)

def _section_intro(section_data, fallback_text, doc_url=""):
    """Render bottom_line from JSON if available, otherwise use fallback hardcoded text."""
    bl = section_data.get("bottom_line", "") if isinstance(section_data, dict) else ""
    text = bl if bl and "unavailable" not in str(bl).lower() else fallback_text
    return _intro_para(text, doc_url)

def _render_warnings(section_data):
    """Render architecture_warnings as red callout blocks."""
    warnings = section_data.get("architecture_warnings", []) if isinstance(section_data, dict) else []
    if not isinstance(warnings, list):
        return []
    return [_callout(str(w), "🚨", "red_background") for w in warnings if w]


# ── Page builder ──────────────────────────────────────────────────────────────

def build_blocks(data):
    blocks = []
    today = datetime.date.today().isoformat()
    ds = data.get("data_source", {})
    app_name = data.get("app_name", "this app")

    refs = data.get("technical_references", [])

    header = f"🤖 Auto-generated by the platform Integration Spec Generator · {today} · Source: {ds.get('type','unknown')}"
    if ds.get("spec_url") and "unavailable" not in str(ds.get("spec_url","")).lower():
        header += f" · Spec: {ds['spec_url']}"
    blocks.append(_callout(header, "🤖", "blue_background"))

    api_ver = data.get("api_version", "")
    if api_ver and "unavailable" not in str(api_ver).lower():
        blocks.append(_callout(f"📌 API Version: {api_ver}", "📌", "gray_background"))

    blocks.append(_divider())

    # 1. Overview
    ov = data.get("overview", {})
    blocks += [_h1("1. Overview"),
               _section_intro(ov, _get(ov, "description"), ""),
               _confidence(ov.get("_confidence", {}))]
    if _get(ov, "description") != _get(ov, "bottom_line", default=""):
        blocks.append(_para(_get(ov, "description")))
    blocks += [_para(_rt_mixed([{"text": "Integration Purpose", "bold": True}])),
               _para(_get(ov, "integration_purpose"))]
    sync_order = data.get("sync_order", [])
    if isinstance(sync_order, list) and sync_order:
        blocks.append(_para(_rt_mixed([{"text": "Execution Flow (Recommended Sync Order)", "bold": True}])))
        if sync_order and isinstance(sync_order[0], dict):
            for step in sync_order:
                entities = ", ".join(step.get("entities", []))
                rationale = step.get("rationale", "")
                blocks.append(_bullet(f"Step {step.get('step', '?')}: {entities} — {rationale}"))
        else:
            blocks.append(_para(" → ".join(str(s) for s in sync_order)))
    blocks += [_divider()]

    # 2. Authentication
    auth = data.get("authentication", {})
    creds = ", ".join(auth.get("credentials_required", [])) if isinstance(auth.get("credentials_required"), list) else "Data unavailable in public documentation"
    scopes = ", ".join(auth.get("scopes_required", [])) if isinstance(auth.get("scopes_required"), list) else "Data unavailable in public documentation"
    blocks += [_h1("2. Authentication"),
               _section_intro(auth, f"To call any {app_name} API endpoint, you must authenticate every request. {app_name} supports the auth method below.", _section_doc_url(refs, "Authentication")),
               _table([["Property","Value"],["Method",_get(auth,"method")],["Token Endpoint",_get(auth,"token_endpoint")]]),
               _bullet(_rt_mixed([{"text": "Required Credentials: ", "bold": True}, {"text": creds}])),
               _bullet(_rt_mixed([{"text": "Scopes: ", "bold": True}, {"text": scopes}]))]
    if auth.get("notes") and "unavailable" not in str(auth.get("notes","")).lower():
        blocks.append(_quote(auth["notes"]))
    blocks.append(_confidence(auth.get("_confidence", {})))
    blocks += [_divider()]

    # 3. Rate Limits
    rl = data.get("rate_limits", {})
    blocks += [_h1("3. Rate Limits"),
               _section_intro(rl, f"{app_name} enforces rate limits on API calls. Exceeding them returns HTTP 429. Your integration must inspect the response headers on every call and implement backoff logic — failing to do so will result in dropped data during high-volume syncs.", _section_doc_url(refs, "Rate Limits")),
               _table([["Property","Value"],["Limit",_get(rl,"limit")],["Scope",_get(rl,"scope")],["Retry",_get(rl,"retry_strategy")]]),
               _h3("Relevant Headers")] + _bullets(rl.get("relevant_headers")) + [_confidence(rl.get("_confidence", {})), _divider()]

    # 4. Pagination
    pag = data.get("pagination", {})
    blocks += [_h1("4. Pagination"),
               _section_intro(pag, f"{app_name}'s API uses the pagination strategy below. Follow the documented pattern on every list call — do not assume all records fit in a single response. Use the maximum allowed page size to minimize round-trips.", _section_doc_url(refs, "Pagination"))]
    # Render strategy info
    strategy = _get(pag, "strategy")
    if strategy and "unavailable" not in str(strategy).lower():
        blocks.append(_para(strategy))
    blocks += [_h3("Request Parameters")] + _bullets(pag.get("request_params")) + [
               _h3("Response Fields")] + _bullets(pag.get("response_fields"))
    if pag.get("notes") and "unavailable" not in str(pag.get("notes","")).lower():
        blocks.append(_quote(pag["notes"]))
    blocks.append(_confidence(pag.get("_confidence", {})))
    blocks += [_divider()]

    # 5. Entity: Accounts
    acc = data.get("entity_accounts", {})
    blocks += [_h1("5. Entity: Accounts"),
               _section_intro(acc, f"Accounts are the core identity unit in {app_name}. The integration must collect both human users and Non-Human Identities (NHIs — bots, service accounts, API keys).", _section_doc_url(refs, "Accounts")),
               _table([["Endpoint","Path"],["List",_get(acc,"list_endpoint")],["Get",_get(acc,"get_endpoint")]])]
    blocks += _render_warnings(acc)
    blocks += [_h3("Key Response Fields (the platform → API)"),
               _field_mapping_table(acc.get("key_response_fields", {})),
               _h3("Human vs. NHI Detection"), _quote(_get(acc,"human_vs_nonhuman"))]
    if acc.get("notes") and "unavailable" not in str(acc.get("notes","")).lower():
        blocks.append(_para(acc["notes"]))
    blocks.append(_confidence(acc.get("_confidence", {})))
    blocks += [_divider()]

    # 6. Entity: Groups
    grp = data.get("entity_groups", {})
    blocks += [_h1("6. Entity: Groups"),
               _section_intro(grp, f"Groups in {app_name} represent collections of accounts with shared permissions (e.g. teams, departments, organizations).", _section_doc_url(refs, "Groups")),
               _table([["Endpoint","Path"],["List",_get(grp,"list_endpoint")],["Get",_get(grp,"get_endpoint")],["Members",_get(grp,"members_endpoint")]])]
    blocks += _render_warnings(grp)
    blocks += [_h3("Key Response Fields (the platform → API)"),
               _field_mapping_table(grp.get("key_response_fields", {}))]
    if grp.get("notes") and "unavailable" not in str(grp.get("notes","")).lower():
        blocks.append(_para(grp["notes"]))
    blocks.append(_confidence(grp.get("_confidence", {})))
    blocks += [_divider()]

    # 7. Entity: Roles
    rol = data.get("entity_roles", {})
    blocks += [_h1("7. Entity: Roles"),
               _section_intro(rol, f"{app_name} uses the role modeling approach shown below. Roles define the privilege level of an account or group within a given scope.", _section_doc_url(refs, "Roles")),
               _callout(f"Modeling: {_get(rol,'modeling_approach')}", "🎭"),
               _table([["Endpoint","Path"],["List",_get(rol,"list_endpoint")],["Assignments",_get(rol,"assignment_endpoint")]])]
    blocks += _render_warnings(rol)
    blocks += [_h3("Key Response Fields (the platform → API)"),
               _field_mapping_table(rol.get("key_response_fields", {}))]
    if rol.get("notes") and "unavailable" not in str(rol.get("notes","")).lower():
        blocks.append(_para(rol["notes"]))
    blocks.append(_confidence(rol.get("_confidence", {})))
    blocks += [_divider()]

    # 8. Entity: Resources
    res = data.get("entity_resources", {})
    blocks += [_h1("8. Entity: Resources"),
               _section_intro(res, f"Resources in {app_name} are the objects that accounts and groups are granted access to (e.g. repositories, projects, workspaces).", _section_doc_url(refs, "Resources"))]
    blocks += _render_warnings(res)
    blocks += [_h3("Resource Types")] + _bullets(res.get("resource_types"))
    ep = res.get("list_endpoints", {})
    if isinstance(ep, dict) and ep:
        blocks.append(_table([["Resource Type","Endpoint"]] + [[k,str(v)] for k,v in ep.items()]))
    blocks += [_h3("Access List Endpoint"), _para(_get(res,"access_list_endpoint")),
               _h3("Key Response Fields (the platform → API)"),
               _field_mapping_table(res.get("key_response_fields", {}))]
    if res.get("notes") and "unavailable" not in str(res.get("notes","")).lower():
        blocks.append(_para(res["notes"]))
    blocks.append(_confidence(res.get("_confidence", {})))
    blocks += [_divider()]

    # 9. Entity Relations
    rel = data.get("entity_relations", {})
    relation_rows = [["Relationship", "Description & Implementation Strategy", "Endpoint (Data Source)", "Doc URL"]]
    for key, label in [
        ("account_to_group",    "Account → Group"),
        ("account_to_role",     "Account → Role"),
        ("account_to_resource", "Account → Resource"),
        ("group_to_role",       "Group → Role"),
        ("group_to_resource",   "Group → Resource"),
    ]:
        desc, endpoint, doc_url = _relation_entry(rel, key)
        entry = rel.get(key, {})
        strategy = entry.get("resolution_strategy", "") if isinstance(entry, dict) else ""
        if strategy:
            desc = f"{strategy.replace('_', ' ').title()}. {desc}"
        relation_rows.append([label, desc, endpoint, doc_url])
    blocks += [_h1("9. Entity Relations"),
               _section_intro(rel, "The Identity Graph is built from 5 relationships. The table below defines the endpoint and data source for each edge type.", _section_doc_url(refs, "Groups"))]
    blocks += _render_warnings(rel)
    blocks += [_table(relation_rows), _confidence(rel.get("_confidence", {})), _divider()]

    # 10. Remediation Actions
    rem = data.get("remediation_actions", {})
    # Support both new object format and legacy array format
    if isinstance(rem, dict):
        actions = rem.get("actions", [])
        rem_section = rem
    elif isinstance(rem, list):
        actions = rem
        rem_section = {}
    else:
        actions = []
        rem_section = {}
    blocks += [_h1("10. Remediation Actions"), _divider(),
               _section_intro(rem_section, f"Remediation is the write-path of the integration — the platform can take action on {app_name} when a security policy is violated. The table below defines every supported action: the exact HTTP call, payload, and required scope.", _section_doc_url(refs, "Remediation"))]
    blocks += _render_warnings(rem_section)
    if not actions:
        blocks.append(_para("Data unavailable in public documentation"))
    else:
        rows = [["Action", "Method", "Endpoint", "Request Body", "Required Scopes", "Notes & Engineering Guidelines"]]
        for a in actions:
            notes_val = a.get("notes", "")
            notes_str = notes_val if notes_val and "unavailable" not in str(notes_val).lower() else "—"
            rows.append([
                a.get("action_name", "—"),
                _get(a, "http_method"),
                _get(a, "endpoint"),
                _get(a, "request_body"),
                ", ".join(a.get("required_scopes", [])) or "—",
                notes_str,
            ])
        blocks.append(_table(rows))
    blocks.append(_confidence(rem_section.get("_confidence", {})))
    blocks.append(_divider())

    # 11. Developer Handoff Summary
    summary = data.get("developer_summary", "")
    blocks.append(_h1("11. Developer Handoff Summary"))
    if summary and "unavailable" not in str(summary).lower():
        blocks.append(_callout(summary, "🧠", "purple_background"))
    else:
        blocks.append(_para("Data unavailable in public documentation"))

    return blocks


# ── Notion creator ────────────────────────────────────────────────────────────

def create_page(app_name, blocks, token, parent_id):
    notion = NotionClient(auth=token)
    print(f"Creating Notion page for {app_name}...")

    first = blocks[:CHUNK_SIZE]
    rest = [blocks[i:i+CHUNK_SIZE] for i in range(CHUNK_SIZE, len(blocks), CHUNK_SIZE)]

    try:
        resp = notion.pages.create(
            parent={"page_id": parent_id},
            properties={"title": {"title": [{"type": "text", "text": {"content": f"{app_name} — Integration Spec"}}]}},
            children=first
        )
    except APIResponseError as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err:
            print("[ERROR] Notion 401 — check NOTION_TOKEN and connect the integration to the parent page.")
        elif "404" in err or "not_found" in err.lower():
            print("[ERROR] Notion 404 — check NOTION_PARENT_PAGE_ID and ensure integration has access.")
        else:
            print(f"[ERROR] Notion API error: {e}")
        sys.exit(1)

    page_id = resp["id"]
    for chunk in rest:
        try:
            notion.blocks.children.append(block_id=page_id, children=chunk)
        except APIResponseError as e:
            print(f"[WARN] Failed to append chunk: {e}")

    return resp.get("url", f"https://www.notion.so/{page_id.replace('-','')}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 notion_writer.py <path_to_prd.json>")
        sys.exit(1)

    json_path = sys.argv[1]
    try:
        with open(json_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {json_path}: {e}")
        sys.exit(1)

    token, parent_id = load_env()
    app_name = data.get("app_name", "Unknown App")

    blocks = build_blocks(data)
    print(f"Built {len(blocks)} Notion blocks.")

    url = create_page(app_name, blocks, token, parent_id)
    print(f"\n✅ Done! Notion page: {url}")


if __name__ == "__main__":
    main()
