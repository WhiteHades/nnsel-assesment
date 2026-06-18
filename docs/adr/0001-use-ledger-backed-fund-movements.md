# ADR 0001: Use ledger-backed fund movements

## Status

Accepted for implementation planning.

## Date

2026-06-18

## Context

The assessment is mainly about preventing double spending. The module must track available, held, assigned, transferred, and spent money across fund accounts, projects, and expense heads.

Several workflows reserve money before final approval:

- allocation submission holds unassigned fund-account money
- requisition submission holds project or expense-head money
- transfer submission holds source target money
- bill posting consumes approved requisition money
- cancellation, rejection, and reversal release money without creating extra money

If the module stores only mutable balance fields, a failed state transition or repeated button click can make balances wrong. It would also be harder to explain why a balance changed during the technical interview.

## Decision

Use an append-only fund movement ledger as the source of truth for financial changes.

Each workflow action that changes money creates one or more movement records. Balance fields read from those movements and are not manually editable.

The module will also enforce idempotency. A repeated approval or posting action must not create duplicate movements for the same source record and movement purpose.

For concurrent submissions, the implementation may use a small, documented PostgreSQL row lock around the source fund account, project, or expense head before checking and reserving available money. This is one of the few cases where direct SQL is justified, because the assessment explicitly evaluates double-spending prevention.

## Alternatives considered

### Store mutable balances only

This is faster to build but riskier. A repeated approval action, failed transaction, or concurrent request could leave balances inconsistent. It also gives a weaker audit trail.

### Use Odoo accounting entries only

This would align with accounting concepts, but it adds setup and permissions that are outside the assessment's core requirement. The assessment allows a custom bill model, so a custom fund ledger is a better first delivery.

### Use a custom movement ledger

This is the chosen approach. It keeps the finance logic clear, testable, and explainable without requiring full Odoo accounting setup.

## Consequences

Positive:

- every money change has an audit record
- balance calculations can be explained from movement history
- repeated workflow actions can be blocked with uniqueness rules
- tests can assert both final balances and movement rows
- direct SQL can stay limited to concurrency locking, if needed

Negative:

- more models and tests are required
- computed balances must be designed carefully
- migration to Odoo accounting entries would need a later integration layer

## Implementation notes

Use Odoo models, access control lists, record rules, and server-side checks. Avoid `sudo()` and raw SQL unless the operation has an explicit security or concurrency reason.

Relevant references:

- Odoo 18 module manifest documentation: https://www.odoo.com/documentation/18.0/th/developer/reference/backend/module.html
- Odoo 18 security documentation: https://www.odoo.com/documentation/18.0/th/developer.html
- Odoo Docker official image: https://hub.docker.com/_/odoo
