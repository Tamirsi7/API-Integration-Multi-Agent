# /webhook-researcher — Research Webhook & Event Support

Sub-agent that researches whether a SaaS application supports webhooks, event streams, or audit logs
relevant to identity lifecycle events. Real-time event support enables the platform to react to changes
(user created, role changed, access granted) without polling.

Can be run standalone or as an optional enrichment step after the main integration pipeline.

## Usage
```
/webhook-researcher <AppName>
```

## Why It Matters for the platform

Real-time events enable proactive identity governance:
- Detect new accounts immediately (vs. scheduled sync)
- React to role changes and access grants in real-time
- Audit log APIs provide historical event data for compliance

## Search Queries

1. `$ARGUMENTS API webhooks events documentation`
2. `$ARGUMENTS webhook event types user created role changed`
3. `$ARGUMENTS audit log API events identity access`
4. `$ARGUMENTS API event subscription setup endpoint`
5. `$ARGUMENTS real-time notifications user membership changes`

## What to Extract

- **Delivery mechanism**: Webhook push (outbound HTTP) | Polling endpoint | Server-Sent Events (SSE) | None
- **Event types relevant to identity**: user.created, user.deleted, role.changed, group.membership.updated, access.granted, etc.
- **Webhook setup**: endpoint to register webhooks, authentication (HMAC signature, shared secret)
- **Audit log API**: if the app has a dedicated `/audit-logs` or `/events` endpoint
- **Payload structure**: key fields in event payloads (event_type, user_id, timestamp, etc.)
- **Retention**: how long events are retained / pagination support

## Output Format

```markdown
## Webhook Research: <AppName>

### Event Support: ✅ Webhooks / ✅ Audit Log API / ❌ No Real-time Support

### Delivery Mechanism
- Type: Webhook push (outbound HTTP POST to your endpoint)
- Setup endpoint: POST /webhooks
- Authentication: HMAC-SHA256 signature in X-Hub-Signature-256 header

### Identity-Relevant Event Types

| Event Type | Trigger | Key Payload Fields |
|---|---|---|
| user.created | New user account created | user_id, email, created_at |
| user.deleted | Account deleted/deprovisioned | user_id, deleted_by |
| team.member_added | User added to team | user_id, team_id, role |
| team.member_removed | User removed from team | user_id, team_id |
| role.assigned | Role assigned to user | user_id, role_name, resource_id |
| permission.changed | Permission level changed | user_id, resource_id, old_role, new_role |

### Audit Log API (if available)

| Property | Value |
|---|---|
| Endpoint | GET /audit-log |
| Authentication | Same as REST API |
| Filters | ?action=user.login&from=2024-01-01 |
| Pagination | Cursor-based |
| Retention | 90 days |

### Webhook Setup Steps
1. POST /hooks with { "url": "https://your-endpoint", "events": ["user.created"] }
2. Verify HMAC signature on incoming requests
3. Doc URL: <link>

🟢 Confidence: <score>/10 | Source: <source>
```

If no webhook/event support found:
```
### Event Support: ❌ No Real-time Support Found
No webhook or audit log API documentation found for <AppName>.
the platform must use scheduled polling to detect identity changes.
🔴 Confidence: 2/10 | Source: Not found
```

## Zero Hallucination
Never invent event types or webhook endpoints. Only include what is explicitly documented.
