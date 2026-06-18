# Product context

register: product

## Product

NN Fund Management is an Odoo Community addon for a technical assessment. It helps finance and project users control incoming money, allocations, requisitions, bills, transfers, approvals, and audit history.

## Users

- Finance users who confirm incoming funds and post bills
- Fund users who request allocations, requisitions, and transfers
- GM and MD approvers who review money-moving requests
- Reviewers who inspect the code, local workflow, tests, and hosted presentation

## Purpose

The module should make fund movement hard to misuse. Money should not be double-spent while it is waiting for approval, transfer, billing, or closure.

## Tone

Use direct, practical language. The product is an internal finance workflow, so the UI and docs should feel clear, controlled, and reviewable.

## Constraints

- Local Odoo and PostgreSQL run through Docker Compose.
- Vercel hosts only the static presentation.
- No paid Odoo services are required.
- Claims in docs should be backed by code, tests, or visible files.
