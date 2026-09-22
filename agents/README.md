# Personal workflow agents

This directory is shared through the private `ente-workflow` repository. Agent definitions and registration are still being designed; no replacement custom agents have been installed yet.

## Storage and discovery

Use `agents/codex/*.toml` for Codex role definitions and `agents/claude/*.md` for Claude Code role definitions. These are small application-specific adapters. Keep reusable procedures and references in the existing shared `skills/` directory, with explicit skill loading in each adapter. Do not independently maintain two copies of the full workflow.

On each host, managed installations must register the definitions in that user's `~/.codex/agents/` and `~/.claude/agents/`. A Git fetch alone does not update a checkout or register agents; the update path must fetch, merge/fast-forward, install the owned definitions and verify discovery. The current sync helper registers skills only. Extending it to register agents is proposed, not implemented.

Use file links only after testing each application's discovery and refresh behavior. Preserve unrelated files in personal agent directories. Keep local paths, credentials and Zoho authentication in host-local configuration. No Ente repository-local instructions are needed.

Codex adapters can use `gpt-6-astra` at low or medium effort. Claude adapters use supported Claude model settings; the role is shared, not the model identifier. Existing independent CLI review behavior remains in place.

## Documentation roles

- `external_docs` (proposed Codex effort: low): verify external framework, SDK and API behavior using primary sources for the relevant version. This replaces the ambiguous proposed name `docs_researcher`; it does not require documentation inside Ente's source tree.
- `help_reader` (low): read the relevant page and section at https://ente.com/help/, explain the documented user behavior, provide exact links for a support answer, and flag contradictions with observed behavior. Missing documentation is a gap, not proof that a feature is unsupported.
- `help_writer` (medium): draft new or revised help content from the accepted feature behavior and verification evidence. Include platform/version availability, actual steps and applicable limitations. Distinguish an unreleased feature draft from published behavior. Return a proposed article or patch for review; do not publish or reply to a customer merely because a draft exists.

The help roles should share one proposed `ente-help-docs` skill and writing references. That skill has not been created yet.

## Proposed attachment points

| Flow | Relevant roles |
| --- | --- |
| Customer ticket | Parent retrieves ticket; `help_reader` finds applicable guidance; `log_reader` extracts supplied logs; `code_explorer` traces the customer's version. Add `external_docs` only for an external technical question. |
| Feature planning | `product_analyst` and `code_explorer` develop behavior and scope; `design_reviewer` handles affected UI; `help_reader` checks existing public promises when relevant. |
| Feature completion | `help_writer` drafts documentation from accepted, verified behavior; parent aligns the draft with release availability and publication approval. |
| Review and verification | Use the existing proposed reviewer, verification reviewer and UI observer boundaries, alongside current workflow checks and independent CLI reviews. |

The working task is the coordinator and maintains the task records. Specialists return bounded results and do not create separate TODO tasks. Store only sanitized support findings in shared records; raw customer logs remain local and excluded from Git.

## Update approach

Prefer the existing Git-based distribution plus deterministic installation over asking a model to copy/update prompts on every change. An optional message can tell the other machine that an update is available, but it is not the source of truth or proof that the update loaded. Do not start or change sync schedules as part of this proposal.

References: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents), [Claude Code subagents](https://code.claude.com/docs/en/sub-agents), [shared skill sync](../skills/ente-workflow-sync/SKILL.md).
