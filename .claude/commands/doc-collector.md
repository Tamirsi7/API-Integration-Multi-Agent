# /doc-collector — Collect & Validate Documentation URLs

Sub-agent that gathers and validates all official API documentation URLs for a SaaS application.
Its output feeds directly into the **Technical References** section (Section 11) of the PRD.

Invoked by the `/integration` orchestrator as Sub-Agent A2 (parallel with OpenAPI Scout, API Researcher, Entity Researcher). Can also be run standalone.

## Usage
```
/doc-collector <AppName>
```

## Instructions

Search for official documentation pages for each PRD section area. For each URL found, use WebFetch to verify it returns actual content (not a 404 or redirect to a login wall).

## Search Queries

Run these searches:
1. `$ARGUMENTS API documentation developer docs reference`
2. `$ARGUMENTS REST API authentication OAuth scopes documentation`
3. `$ARGUMENTS API users accounts endpoint documentation`
4. `$ARGUMENTS API groups teams organizations endpoint docs`
5. `$ARGUMENTS API roles permissions documentation`
6. `$ARGUMENTS API resources projects repositories endpoint docs`
7. `$ARGUMENTS SCIM provisioning documentation`
8. `$ARGUMENTS API rate limits pagination documentation`
9. `$ARGUMENTS API webhooks events changelog`

## Validation

For each candidate URL:
- Attempt a WebFetch to confirm it loads
- Mark as `✅ Verified` if it returns readable documentation
- Mark as `⚠️ Unverified` if WebFetch fails or the page is behind auth
- Do NOT include URLs you cannot confirm

## Output Format

Return structured markdown:

```markdown
## Doc Collector: <AppName>

| Section | Label | URL | Status |
|---|---|---|---|
| Overview | API Documentation Home | https://... | ✅ Verified |
| Authentication | OAuth 2.0 Guide | https://... | ✅ Verified |
| Rate Limits | Rate Limiting Docs | https://... | ✅ Verified |
| Pagination | Pagination Reference | https://... | ✅ Verified |
| Accounts | Users API Reference | https://... | ✅ Verified |
| Groups | Teams/Groups API | https://... | ✅ Verified |
| Roles | Permissions & Roles | https://... | ✅ Verified |
| Resources | Resources API | https://... | ✅ Verified |
| Remediation | Add/Remove Members | https://... | ✅ Verified |
| SCIM | SCIM Provisioning | https://... | ⚠️ Unverified |
```

## Zero Hallucination
Never fabricate documentation URLs. Only include URLs found via web search and confirmed via WebFetch.
If no URL is found for a section, omit that row entirely — do not invent a placeholder.
