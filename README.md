# API Integration Multi-Agent

> **One command. ~15 minutes. A complete, engineering-grade API integration spec - delivered straight to Notion.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Claude AI](https://img.shields.io/badge/Claude-Opus%204.6-blueviolet?logo=anthropic&logoColor=white)
![Notion API](https://img.shields.io/badge/Notion-API-black?logo=notion&logoColor=white)
![Multi-Agent](https://img.shields.io/badge/Architecture-Multi--Agent-orange)
![Zero Hallucination](https://img.shields.io/badge/Policy-Zero%20Hallucination-red)

---

## TL;DR

- **What:** An AI agent system that researches any SaaS application's REST API and auto-generates a structured, 11-section integration PRD (Product Requirements Document) - published directly to Notion. An Example:
  www.notion.so/Anthropic-API-Integration-Spec-348a17b6ba9680929908e53188541d3b?source=copy_link
- **Why:** Manual API research for enterprise identity integrations takes weeks per app. This pipeline does it in minutes, with confidence scoring on every field and zero invented data.
- **How:** One slash command (`/integration <AppName>`) spawns 7 specialized Claude AI sub-agents in parallel - each with a narrow research focus - then merges, validates, and publishes the result.

---

## The Problem

Enterprise organizations use **50+ SaaS applications**, each with its own user model, role system, and API quirks. Security and IT teams need visibility into *who has access to what* across all of them - but building that visibility requires deep API research for every single app:

- What are the exact endpoints for users, groups, roles, and resources?
- How does this app model permissions - inline on the user object or as separate role objects?
- Which pagination strategy does it use - cursor, offset, or link-header? With what hard limits?
- How do you revoke a user's access, suspend an account, or change a role via API?

**Doing this manually for a single app takes a senior engineer 3–5 days.** Doing it for 50 apps is a bottleneck that slows down entire platform teams.

This project automates the entire research-to-spec pipeline using multi-agent AI orchestration.

---

## What I Built

A **multi-agent AI system** built on [Claude Code](https://claude.ai/code) that:

1. **Researches** any SaaS API autonomously - finding OpenAPI specs, scraping HTML docs, and extracting structured data with web search + fetch
2. **Maps** every discovered entity and field to a canonical 4-entity identity model (Accounts, Groups, Roles, Resources)
3. **Validates** all data with a confidence scoring system (🟢/🟡/🔴) - never inventing or guessing
4. **Publishes** a complete 11-section engineering PRD directly to Notion via Python + Notion API

### Key Metrics
| Stat | Value |
|---|---|
| Total skill prompts | 16 specialized agents |
| PRD sections per output | 11 |
| Avg. time to complete spec | ~15 minutes |
| Lines of code (Python + prompts) | ~3,000 |
| Confidence scoring | Every field, 1–10 scale |
| Hallucination policy | Zero - `"Data unavailable in public documentation"` if uncertain |

---

## Architecture

```
/integration <AppName>
        │
        ▼
  ORCHESTRATOR  (Claude Opus 4.6)
        │
  ┌─────┼────────────┬───────────────┐  ← PARALLEL (Step 1)
  ▼     ▼            ▼               ▼
[A]   [B]          [C]             [D]
OpenAPI  API Info   Entity          Doc
Scout    Researcher  Researcher      Collector
  │     │            │               │
  └─────┴────────────┴───────────────┘
                    │
              Merge + Validate
              Confidence Gate
                    │
              ┌─────┘
              ▼
         [E] Remediation Research
         (main session - 6–8 parallel WebFetch calls)
                    │
                    ▼
              [F] Identity Mapper
              (research → canonical JSON)
                    │
                    ▼
              [G] Notion Writer
              (Python → Notion API)
                    │
                    ▼
            ✅ Notion Page URL
```

### Sub-Agent Roles

| Agent | Focus | Output |
|---|---|---|
| **OpenAPI Scout** | Find official OpenAPI/Swagger spec | Spec URL, detected endpoints, confidence score |
| **API Info Researcher** | Auth, rate limits, pagination | Exact header names, token flows, pagination params |
| **Entity Researcher** | Map Accounts/Groups/Roles/Resources | Field mappings, NHI detection, admin blindspots |
| **Doc Collector** | Gather official doc URLs | Validated reference table per entity |
| **Remediation Researcher** | Write-path endpoints | Add/remove/suspend/delete user actions |
| **Identity Mapper** | Merge all research → JSON | Canonical PRD JSON matching `prd_schema.json` |
| **Notion Writer** | Publish to Notion | Notion page URL |

**Key design principle:** Sub-agents communicate via **structured markdown**, not prose. Each agent has a narrow scope and a small context window. The orchestrator merges all outputs and enforces schema compliance before publishing.

---

## The 4 Canonical Entities

Every integration maps to the same 4-entity identity model - regardless of how the target app names or structures its data:

| Entity | What It Represents | Examples |
|---|---|---|
| **Accounts** | Individual identities - human or Non-Human (NHI) | Users, service accounts, API keys, bots |
| **Groups** | Collections of accounts with shared permissions | Teams, departments, organizations, workspaces |
| **Roles** | Privilege levels assigned to accounts or groups | Admin, Viewer, Editor, custom permission sets |
| **Resources** | Objects that accounts/groups have access to | Repositories, projects, dashboards, databases |

**Relations (all many-to-many):**
- Account → Group (membership)
- Account → Role (assignment)
- Account → Resource (access grant)
- Group → Role (assignment)
- Group → Resource (access grant)

---

## The 16 Slash Commands

This system is built entirely on **Claude Code custom skills** - no external orchestration framework required.

| Command | Type | Purpose |
|---|---|---|
| `/integration <App>` | **Main** | Full pipeline → Notion page |
| `/batch-integrations <App1, App2, ...>` | Helper | Process multiple apps in sequence |
| `/openapi-scout <App>` | Sub-agent | Find official OpenAPI/Swagger spec |
| `/api-researcher <App>` | Sub-agent | Auth, rate limits, pagination research |
| `/entity-researcher <App>` | Sub-agent | Map all 4 entities + NHI detection |
| `/remediation-researcher <App>` | Sub-agent | Write-path endpoint discovery |
| `/identity-mapper` | Sub-agent | Merge research → canonical JSON |
| `/notion-writer` | Sub-agent | Publish JSON to Notion page |
| `/doc-collector <App>` | Helper | Gather & validate all official doc URLs |
| `/scim-researcher <App>` | Helper | Check SCIM 2.0 provisioning support |
| `/webhook-researcher <App>` | Helper | Research webhooks & real-time events |
| `/entity-sketch <App>` | Helper | Quick entity model - no Notion write |
| `/prd-audit <App>` | Helper | Audit spec for gaps + confidence |
| `/prd-validate` | Helper | Validate JSON against `prd_schema.json` |
| `/spec-diff <f1> <f2>` | Helper | Compare two generated specs |
| `/setup-check` | Helper | Validate env vars + Python deps |

---

## The 11-Section PRD Output

Every generated Notion page contains these sections - all with confidence scores, engineering bottom-lines, and named architecture warnings:

| # | Section | Engineering Focus |
|---|---|---|
| 1 | **Overview** | App summary, Read/Write integration paths, sync execution order |
| 2 | **Authentication** | OAuth/API Key/Bearer method, exact scopes, token endpoint, tier gating |
| 3 | **Rate Limits** | Limit, scope, exact header names (proactive vs. reactive), retry strategy |
| 4 | **Pagination** | Strategy (cursor/offset/keyset), params, hard record ceilings + workarounds |
| 5 | **Entity: Accounts** | List/Get endpoints, field mapping, NHI detection logic |
| 6 | **Entity: Groups** | List/Get/Members endpoints, hierarchy handling |
| 7 | **Entity: Roles** | Modeling approach, endpoints, admin flags, tier-dependent behavior |
| 8 | **Entity: Resources** | Resource types, ACL vs. property-driven access model |
| 9 | **Entity Relations** | 5 relationships with resolution strategies (embedded/separate/aggregation) |
| 10 | **Remediation Actions** | HTTP method, endpoint, request body, required scopes for 8 standard actions |
| 11 | **Developer Handoff** | Critical takeaways, pagination traps, NHI discovery, bottlenecks |

**Every section includes:**
- 🎯 **Bottom-line** - 1–2 sentence engineering summary specific to THIS app
- 🚨 **Architecture Warnings** - named gotchas with "Action Required" prescriptions
- 🟢/🟡/🔴 **Confidence Score** - with source and 1-sentence justification

---

## Quality & Reliability Systems

### Zero Hallucination Policy
If data is not confirmed in official documentation, the system writes exactly:
> `"Data unavailable in public documentation"`

No invented endpoints. No guessed field names. No assumed scopes.

### Confidence Scoring (per section)
| Score | Badge | Meaning |
|---|---|---|
| 8–10 | 🟢 | Extracted from official OpenAPI/Swagger spec |
| 5–7 | 🟡 | Extrapolated from clear HTML documentation |
| 1–4 | 🔴 | Ambiguous or missing - human PM review required |

### Architecture Divergence Detection
When different entities use different strategies for the same concern, the system flags it:
> `⚠️ ARCHITECTURE WARNING: Accounts use cursor pagination; Resources use offset with a 10,000-record hard ceiling. Action Required: implement two separate paginators in the sync engine.`

### SPA Portal Fallback Logic
Many enterprise API portals return login walls or JS bundles when fetched programmatically. The system has explicit fallback routing:
- **HubSpot**: `developers.hubspot.com` → pivot to GitHub raw spec collection
- **Salesforce, Workday, ServiceNow**: WebSearch to extract from Google's cached docs
- **Any Next.js SPA**: pivot to Postman public workspace or raw GitHub spec

### 2-Timeout Kill Rule
Background sub-agents are polled at most **twice** (3 minutes each). If not done → `TaskStop` immediately, research runs in the main session. Prevents pipeline stalls from slow agents.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Orchestration | Claude Code (claude-opus-4-6) + custom slash commands |
| Web Research | `WebSearch` + `WebFetch` tools (built into Claude Code) |
| Multi-Agent Framework | Claude Code Task tool (background agents, TaskOutput, TaskStop) |
| Output Schema | `prd_schema.json` - annotated JSON schema reference |
| Identity Model | `identity_model.json` - 4-entity canonical data model |
| Notion Publishing | `notion_writer.py` - Python, `notion-client` library |
| Credentials | `.env` - `NOTION_TOKEN` + `NOTION_PARENT_PAGE_ID` |

---

## Quick Start

### 1. Prerequisites
- [Claude Code](https://claude.ai/code) installed and authenticated
- A Notion integration token + parent page ID

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure credentials
Create a `.env` file in the project root:
```
NOTION_TOKEN=ntn_your_token_here
NOTION_PARENT_PAGE_ID=your-page-id-here
```

### 4. Validate setup
```
/setup-check
```

### 5. Run your first integration
```
/integration GitHub
```

That's it. The agent researches GitHub's API, maps it to the canonical model, and creates a Notion page - in ~15 minutes.

---

## PM Skills Demonstrated

This project was designed and built end-to-end as a product - not just code. Here's how it maps to core PM competencies:

| PM Skill | How It's Demonstrated |
|---|---|
| **Systems Thinking** | Designed a 7-agent pipeline with clear separation of concerns, structured data contracts between agents, and explicit failure modes |
| **Zero-to-One Product Design** | Created `prd_schema.json` from scratch as the system's source of truth - defining the exact structure every agent must produce and consume |
| **Developer Empathy** | The 11-section PRD format was designed around what engineers actually need: exact field names, HTTP methods, request bodies, scopes, and named gotchas |
| **Quality Systems** | Built confidence scoring, a confidence validation gate, and zero-hallucination enforcement - not as afterthoughts, but as first-class architectural constraints |
| **Scalability Thinking** | `batch-integrations`, timeout kill rules, main-session fallback logic, and sub-agent retry strategies were all designed for production-scale use |
| **Spec Writing** | 16 skill prompts act as product specs for each sub-agent - defining inputs, required checks, output format, and error handling precisely |
| **Research & Synthesis** | The pipeline synthesizes unstructured web data (HTML docs, OpenAPI specs, Postman collections) into structured, validated, schema-conformant output |

---

## AI & Technical Skills Demonstrated

| Skill | Where It Appears |
|---|---|
| **Claude Code** | Primary runtime - slash commands, skill system, multi-agent Task tool |
| **Multi-Agent Orchestration** | 7 parallel sub-agents with background execution, polling, kill rules |
| **Web Research Automation** | WebSearch + WebFetch with SPA detection and pivot logic |
| **Schema-Driven Development** | `prd_schema.json` as source of truth for all agents and the Python renderer |
| **Notion API Integration** | `notion_writer.py` - programmatic page creation with rich blocks, tables, callouts |
| **Structured Prompt Engineering** | 16 skill prompts with required checks, output format contracts, and failure handling |
| **API Architecture** | Deep understanding of OAuth2, pagination strategies, rate limit patterns, REST semantics |
| **Zero-Hallucination Enforcement** | Explicit "Data unavailable" policy enforced at the orchestrator and mapper levels |

---

## Project Structure

```
.
├── CLAUDE.md                        # System role definition, rules, and architecture
├── prd_schema.json                  # Source of truth - PRD JSON structure
├── identity_model.json              # 4-entity canonical identity data model
├── notion_writer.py                 # Python script - converts PRD JSON to Notion page
├── requirements.txt                 # notion-client, python-dotenv
├── .env                             # Credentials (not committed)
└── .claude/
    ├── settings.json                # Model config (claude-opus-4-6)
    └── commands/                    # 16 specialized skill prompts
        ├── integration.md           # Main orchestrator
        ├── openapi-scout.md
        ├── api-researcher.md
        ├── entity-researcher.md
        ├── remediation-researcher.md
        ├── identity-mapper.md
        ├── notion-writer.md
        ├── batch-integrations.md
        ├── scim-researcher.md
        ├── webhook-researcher.md
        ├── doc-collector.md
        ├── entity-sketch.md
        ├── prd-audit.md
        ├── prd-validate.md
        ├── spec-diff.md
        └── setup-check.md
```
---
