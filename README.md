# nnsel-assesment

This repository is the planning and delivery workspace for the NN Services and Engineering technical assessment.

The target deliverable is an installable Odoo custom module named `nn_fund_management`. The module will manage incoming funds, allocation approvals, requisitions, bills, transfers, balances, audit history, and access control.

## Current status

Planning and initialization are complete enough to start implementation after review.

## Source documents

- `docs/assessment/technical-assessment.txt`: extracted assessment text
- `docs/assessment/prompt-injection-review.md`: safety review of the extracted assessment
- `docs/planning/implementation-plan.md`: implementation plan
- `docs/planning/user-stories.md`: user stories and acceptance criteria
- `docs/planning/test-plan.md`: test strategy
- `docs/planning/submission-plan.md`: demo, recording, and handoff plan
- `CONTEXT.md`: domain glossary
- `docs/adr/0001-use-ledger-backed-fund-movements.md`: main architecture decision

## Draft tech stack

- Odoo 18 Community
- Python and the Odoo Object Relational Mapping layer
- PostgreSQL through the official Odoo Docker setup
- Custom Odoo module under `addons/nn_fund_management`
- Odoo access control lists, record rules, groups, and server-side checks
- Odoo transaction tests for balance and workflow rules

## Implementation note

The implementation phase has not started in this repository yet. The next phase should create the Dockerized Odoo scaffold and the module skeleton first, then build the fund ledger and workflows in small commits.
