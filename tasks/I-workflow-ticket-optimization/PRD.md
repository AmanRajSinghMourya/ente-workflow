# Ticket optimization

[Working chat](codex://threads/01a0c8ab-af62-7271-8947-165e47061813)

The existing Zoho Desk server is saved as zoho-desk in personal Codex configuration on MacBook Air. Its endpoint returned HTTP 401 with an OAuth challenge. Codex OAuth login has opened Zoho consent in the browser; authorization and ticket access are not yet verified.

Next: finish browser authorization, then verify the organization and all three supplied tickets, including conversation bodies and actual attachment/log access. No ticket has been retrieved yet. The supplied console screenshot shows getTicket, getTicketConversations and getThread; search/tag filtering and attachment downloads are not established.

The intended workflow retrieves relevant assigned tickets, checks conversations and logs, then investigates source and merged changes. Outcomes include evidence-backed diagnosis, a draft request for missing settings or fresh logs, reproduction steps, or mitigation. Customer replies, status/assignment changes and product fixes require separate authorization.

Aman deferred ticket workflow decisions until later this week. Consider filtering by aman/mobile tags before fetching bodies, and decide the Claude/Codex division then. T- naming remains pending with that follow-on. Keep customer logs and credentials out of shared records. No ticket automation, sync automation or prompt analyzer work has been started.

References: [Zoho setup](https://help.zoho.com/portal/en/kb/mcp/implementation-guide/articles/zoho-mcp-implementation-guide), [Codex MCP](https://developers.openai.com/codex/mcp).
