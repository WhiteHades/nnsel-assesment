# nnsel-assesment

Odoo Community technical assessment for NN Services and Engineering.

The deliverable is an installable Odoo 19 addon named `nn_fund_management`. It manages incoming funds, fund allocations, requisitions, bills, transfers, balances, approvals, audit history, and basic bank-email parsing.

## Status

Implementation is complete for the local Odoo deliverable. The module installs in Docker and the backend workflow tests pass.

## Stack

- Odoo 19 Community, validated against the local Odoo source at `/home/efaz/Codes/odoo`
- PostgreSQL 16
- Docker Compose
- Python Odoo ORM models, XML views, ACLs, record rules, mail activities, and transaction tests
- Vercel-ready presentation site under `presentation/`

## Run Locally

Copy the environment example if needed:

```bash
cp .env.example .env
```

Start Odoo and PostgreSQL:

```bash
docker compose up -d
```

Open Odoo:

```text
http://localhost:8069
```

Create a database, install `NN Fund Management`, then use the `Fund Management` app menu.

## Verify

Fresh install:

```bash
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d nnsel_install_clean --init nn_fund_management --stop-after-init --without-demo=True
```

Backend tests:

```bash
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d nnsel_final_clean --init nn_fund_management --test-enable --test-tags /nn_fund_management --stop-after-init --without-demo=True --log-level=test
```

Latest local result: 6 post-install tests, 8 test assertions reported by Odoo, 0 failures, 0 errors.

Frontend presentation:

```bash
cd presentation
npm ci
npm audit --audit-level=moderate
npm run build
npm run preview -- --port 4173
```

The preview site runs at `http://localhost:4173`.

## Vercel Presentation

Live URL:

```text
https://nnsel-assesment.vercel.app
```

The root `vercel.json` builds only the static presentation site:

```bash
vercel --prod
```

The Odoo server and PostgreSQL database are intentionally not deployed to Vercel. They run locally with Docker Compose.

## Implemented Scope

- Fund accounts and incoming fund confirmation
- Duplicate transaction reference protection per fund account
- Append-only fund movement ledger
- Project and expense-head fund buckets
- Allocation holds, GM approval, MD approval, rejection, cancellation, and final assignment
- Requisition holds, approval, billing, partial billing, closing, and reversal
- Transfers between projects and expense heads with pending-transfer holds
- Configurable approval rules by request type, amount range, company, approver user, and approver group
- Self-approval prevention unless an override group is granted
- Odoo activities for the next approver
- Audit history for submissions, approvals, rejections, confirmations, postings, reversals, and closures
- Multi-company record rules
- Bank email parser prototype that creates pending incoming funds
- Dashboard totals and pending approval count

## Demo Flow

The automated tests cover the assessment flow:

1. Receive BDT 1,000,000.
2. Allocate BDT 600,000 to Project A.
3. Reject once and verify funds return.
4. Approve through GM then MD.
5. Transfer BDT 200,000 from Project A to Project B.
6. Confirm pending transfer funds cannot be spent.
7. Approve the transfer.
8. Requisition BDT 150,000 for Project B.
9. Post a BDT 100,000 bill.
10. Block overbilling and wrong-project billing.

## Key Files

- `addons/nn_fund_management/models/fund_models.py`: fund workflow and ledger logic
- `addons/nn_fund_management/models/project_project.py`: project fund balances
- `addons/nn_fund_management/security/`: groups, ACLs, and record rules
- `addons/nn_fund_management/views/`: Odoo backend UI
- `addons/nn_fund_management/tests/test_fund_management.py`: workflow and money-control tests
- `docs/implementation-summary.md`: implementation notes
- `docs/demo-script.md`: interviewer demo script
- `presentation/`: Vercel-ready presentation site
- `vercel.json`: Vercel build configuration for the static presentation

## Notes

This project intentionally uses native Odoo backend UI instead of a separate custom frontend for the business workflow. The Vercel site is only a public presentation layer, because Vercel is not a fit for hosting the Odoo server and PostgreSQL runtime.
