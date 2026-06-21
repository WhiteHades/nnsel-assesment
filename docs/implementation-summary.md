# Implementation summary

## Objective

Build a fund-management Odoo addon that prevents double spending across incoming funds, allocations, requisitions, bills, and transfers.

## Runtime

The implementation targets Odoo 19 Community. The local Odoo repository at `/home/efaz/Codes/odoo` was used as the syntax reference for the current ORM APIs, including `models.Constraint`, `_read_group`, and Odoo 19 group membership fields.

## Architecture

The addon uses an append-only ledger model named `fund.movement`. Business documents do not store the source of truth for balances. They create signed movements into named buckets:

- `account_unassigned`
- `account_allocation_hold`
- `target_available`
- `target_requisition_hold`
- `target_transfer_hold`
- `target_reserved`
- `target_spent`

Balance fields on fund accounts, projects, and expense heads aggregate those buckets.

Confirmed incoming funds can be cancelled by finance users only. Cancellation writes an outgoing `account_unassigned` ledger movement instead of mutating the original confirmation movement.

## Main workflows

Incoming funds are confirmed by finance users and create unassigned fund-account money. Duplicate transaction references are blocked per fund account.

Allocations move money from fund-account unassigned balance into allocation hold on submission. Rejection releases it. GM and MD approval move it to the selected project or expense head.

Requisitions move target available money into a requisition hold on submission. Final approval moves the money to approved but unspent. Bills consume approved but unspent money, and reversals restore it.

Transfers move money from target available balance into a transfer hold. Approval releases the hold into the destination target. Rejection or cancellation returns it to the source.

Approval rules can be generic or scoped to a specific project or expense head. Scoped rules are matched before submission writes any hold movements, so an unmatched request stays in draft and does not reserve money.

## Security

The module defines these functional groups:

- Fund User
- Finance User
- GM Approver
- MD Approver
- Fund Administrator
- Self Approval Override

Financial ledger, approval steps, and approval history remain restricted from direct manual writes. Workflow methods create those records internally with elevated rights, while preserving the acting user in business fields and chatter.

## Optional features

The assessment optional scope is covered with:

- configurable approval rules
- target-scoped approval rules for projects and expense heads
- Odoo approval activities
- dashboard totals
- bank email parser prototype
- demo data
- automated tests for double-spending paths
- Vercel-ready presentation site

## Presentation site

The `presentation/` app is a Vite, React, Tailwind, Playwright, and shadcn-style static site. It is separate from the Odoo backend and exists to give reviewers a clean public summary of the implementation, scope coverage, demo path, and repository evidence.

The root `vercel.json` points Vercel at `presentation/dist`, so the presentation can be hosted without pretending that Vercel is an Odoo runtime.

Production URL: `https://nnsel-assesment.vercel.app`

## Verification

Run:

```bash
python -m py_compile addons/nn_fund_management/models/*.py addons/nn_fund_management/tests/*.py
xmllint --noout addons/nn_fund_management/security/*.xml addons/nn_fund_management/data/*.xml addons/nn_fund_management/views/*.xml
TEST_DB=nnsel_final_$(date +%s)
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d "$TEST_DB" --init nn_fund_management --test-enable --test-tags /nn_fund_management --stop-after-init --without-demo=True --log-level=test
cd presentation
npm audit --audit-level=moderate
npm run build
npm run test:e2e
```

Latest result: 22 post-tests, 24 module tests, 0 failures, 0 errors.
