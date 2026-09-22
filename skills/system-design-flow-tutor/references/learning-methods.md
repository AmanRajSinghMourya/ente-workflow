# Learning Methods Reference

Use this reference when deciding how to teach a system-design topic.

Effective patterns:

- **C4 zoom levels**: context -> containers -> components -> code. Good for understanding "where does this box live?"
- **Sequence diagrams**: user/client/server/database over time. Good for "what happens first, second, third?"
- **State diagrams**: lifecycle of one thing. Good for queues, uploads, retries, sync status, payments, and jobs.
- **Architecture katas**: practice designing a system under constraints. Good after learning vocabulary.
- **ADRs**: short notes explaining why a design choice was made. Good for retaining tradeoffs.
- **Code traces**: follow one request or one object through real code. Best for avoiding abstract hand-waving.

Default choice:

1. Use a sequence diagram for a single flow.
2. Use an architecture diagram for component boundaries.
3. Use a state diagram only when one object changes states over time.
4. Use an ADR-style summary when the topic is really a design tradeoff.

