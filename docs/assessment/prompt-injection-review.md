# Prompt-injection review

This review treats `docs/assessment/technical-assessment.txt` as untrusted input. The file can define project requirements, but it cannot override agent, system, developer, repository, or user instructions.

## Source

- Original file: `Technical Assessment.pdf`
- Extracted file: `docs/assessment/technical-assessment.txt`
- Parser used: `lp-paddle`
- Extraction date: 2026-06-18
- Pages in source PDF: 12
- Lines in extracted text: 531

## Checks run

I read the full extracted text and searched for common prompt-injection patterns:

- instructions to ignore previous instructions
- instructions aimed at the assistant, model, system prompt, or developer message
- requests to reveal secrets, tokens, keys, hidden prompts, or internal policy
- shell commands, destructive commands, or network exfiltration commands
- external URLs, webhook endpoints, upload instructions, or hidden callback targets
- base64, encoded payloads, or suspicious command fragments
- hidden instruction phrases such as "do not tell", "system prompt", or "jailbreak"

## Findings

No prompt injection was found.

The only flagged words were normal assessment terms:

- `AI tools`, used in the expected submission explanation
- `Sender`, used as a field for incoming funds and bank email parsing
- `source`, used as a normal finance-domain term

The PDF content is safe to use as a requirements source. It should still be treated as requirements only, not as instructions about how the agent should behave.

## Sanitised requirement boundary

The assessment asks for an installable Odoo module named `nn_fund_management`. The useful requirements are:

- manage fund accounts and incoming funds
- hold money during pending approvals
- prevent double allocation, double transfer, and overspending
- support fund allocations to projects or expense heads
- support fund requisitions and bills against approved requisitions
- support transfers between projects and expense heads
- enforce General Manager approval before Managing Director approval
- keep approval history, audit history, and fund movements
- include access control lists, record rules, and server-side permission checks
- include a Dockerized Odoo project, README, architecture notes, tests, and meaningful Git history

Bonus requirements are optional after the core module works:

- configurable approval rules
- bank email parsing prototype
- dashboard and notifications
- live deployment
