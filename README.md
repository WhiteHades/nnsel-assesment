<p align="center">
  <img src="docs/assets/nn-fund-logo.svg" width="96" alt="NN Fund Management logo">
</p>

<h1 align="center">NN Fund Management</h1>

<p align="center">
  Odoo Community fund-control module for the NNSEL technical assessment.
</p>

<p align="center">
  <img alt="Odoo 19" src="https://img.shields.io/badge/Odoo-19-714B67">
  <img alt="PostgreSQL 16" src="https://img.shields.io/badge/PostgreSQL-16-336791">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-local-2496ED">
  <img alt="Tests" src="https://img.shields.io/badge/tests-16%20passing-1F8A4C">
  <img alt="Vercel" src="https://img.shields.io/badge/Vercel-presentation-111111">
</p>

<p align="center">
  <a href="https://nnsel-assesment.vercel.app">Live presentation</a>
  &middot;
  <a href="docs/demo-script.md">Demo script</a>
  &middot;
  <a href="docs/recording-guide.md">Recording guide</a>
  &middot;
  <a href="docs/implementation-summary.md">Implementation notes</a>
</p>

## Overview

`nn_fund_management` is an installable Odoo 19 Community addon for controlled fund management. It covers incoming bank funds, project and expense-head allocations, requisitions, bills, transfers, approvals, audit history, dashboard totals, and a bank-email parser prototype.

The business system runs locally with Docker Compose. The hosted Vercel site is a static presentation for reviewers.

## Stack

- Odoo 19 Community, checked against `/home/efaz/Codes/odoo`
- PostgreSQL 16
- Docker Compose
- Python ORM models, XML views, ACLs, record rules, mail activities, and Odoo transaction tests
- Vite, React, Tailwind, Playwright, and shadcn-style components for the presentation site
- No paid services required for the local Odoo runtime

## Run Locally

```bash
cp .env.example .env
docker compose up -d
```

Open Odoo at:

```text
http://localhost:8069
```

Create a database, install `NN Fund Management`, then open the `Fund Management` app menu.

## Verify

Fresh install:

```bash
INSTALL_DB=nnsel_install_$(date +%s)
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d "$INSTALL_DB" --init nn_fund_management --stop-after-init --without-demo=True
```

Backend tests:

```bash
TEST_DB=nnsel_final_$(date +%s)
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d "$TEST_DB" --init nn_fund_management --test-enable --test-tags /nn_fund_management --stop-after-init --without-demo=True --log-level=test
```

Latest backend result: 14 post-test cases, 16 module tests, 0 failures, 0 errors.

Presentation site:

```bash
cd presentation
npm ci
npx playwright install chromium
npm audit --audit-level=moderate
npm run build
npm run test:e2e
npm run preview -- --port 4173
```

Local preview:

```text
http://localhost:4173
```

Live presentation:

```text
https://nnsel-assesment.vercel.app
```

## Scope

- Fund accounts and incoming fund confirmation
- Confirmed incoming fund cancellation with ledger reversal
- Duplicate transaction reference protection per fund account
- Append-only fund movement ledger
- Project and expense-head fund buckets
- Allocation holds, rejection release, GM approval, MD approval, cancellation, and final assignment
- Requisition holds, approval, billing, partial billing, closing, and bill reversal
- Transfers between projects and expense heads with pending-transfer holds
- Configurable approval rules by request type, amount range, company, target project, target expense head, approver user, and approver group
- Self-approval prevention unless an override group is granted
- Odoo activities for the next approver
- Audit history for submissions, approvals, rejections, confirmations, postings, reversals, cancellations, and closures
- Multi-company record rules
- Bank email parser prototype that creates pending incoming funds
- Dashboard totals, held money, and pending approval count

## Demo Path

The automated tests and the demo script cover the reviewer flow:

1. Receive BDT 1,000,000.
2. Allocate BDT 600,000 to Project A.
3. Reject once and verify funds return.
4. Approve through GM, then MD.
5. Transfer BDT 200,000 from Project A to Project B.
6. Confirm pending transfer money cannot be spent again.
7. Approve the transfer.
8. Requisition BDT 150,000 for Project B.
9. Post a BDT 100,000 bill.
10. Block overbilling and wrong-project billing.
11. Demonstrate expense-head funding and wrong-head bill protection.
12. Show dashboard totals, activities, ledger movements, and approval history.

## Key Files

- `addons/nn_fund_management/models/fund_models.py`: fund workflow and ledger logic
- `addons/nn_fund_management/models/project_project.py`: project fund balances
- `addons/nn_fund_management/security/`: groups, ACLs, and record rules
- `addons/nn_fund_management/views/`: Odoo backend UI
- `addons/nn_fund_management/tests/test_fund_management.py`: workflow and money-control tests
- `docs/implementation-summary.md`: implementation notes
- `docs/demo-script.md`: interviewer demo script
- `docs/recording-guide.md`: facecam recording checklist
- `presentation/`: Vercel-ready presentation site
- `vercel.json`: Vercel build configuration for the static presentation

## Deployment

The root `vercel.json` builds only `presentation/`:

```bash
vercel --prod
```

Odoo and PostgreSQL are not deployed to Vercel. They are server/database workloads and run locally through Docker Compose for this assessment.
