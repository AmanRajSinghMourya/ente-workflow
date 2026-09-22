# Ticket optimization

[Working chat](codex://threads/01a0c8ab-af62-7271-8947-165e47061813)

Zoho Desk read access was verified on MacBook Air on 2026-09-22 through Codex app-server: ticket metadata, five conversation entries and one plain-text thread body were retrieved for one supplied verification ticket. OAuth and all three configured read tools work. Ordinary agent tool discovery still needs investigation: this workflow discussion and a fresh Codex CLI run did not expose the Zoho tools.

Next: resolve ordinary agent tool discovery and verify organization/assignment, the other two supplied tickets and actual attachment/log access. The tested ticket reports no attachments. Search/tag filtering and attachment downloads remain unverified; only getTicket, getTicketConversations and getThread are currently exposed by the server.

The intended workflow retrieves relevant assigned tickets, checks conversations and logs, then investigates source and merged changes. Outcomes include evidence-backed diagnosis, a draft request for missing settings or fresh logs, reproduction steps, or mitigation. Customer replies, status/assignment changes and product fixes require separate authorization.

Aman deferred ticket workflow decisions until later this week. Consider filtering by aman/mobile tags before fetching bodies, and decide the Claude/Codex division then. T- naming remains pending with that follow-on. Keep customer logs and credentials out of shared records. No ticket automation, sync automation or prompt analyzer work has been started.

References: [Zoho setup](https://help.zoho.com/portal/en/kb/mcp/implementation-guide/articles/zoho-mcp-implementation-guide), [Codex MCP](https://developers.openai.com/codex/mcp).
