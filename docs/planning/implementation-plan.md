# Implementation plan

## Goal

Build an installable Odoo custom module named `nn_fund_management` that proves the required fund workflows and prevents double spending.

The implementation should be small enough to explain in an interview and complete enough to demonstrate the sample flow from the assessment.

## Assumptions

- Odoo 19 Community is used because the local Odoo repository is branch `19.0`.
- The project target will use Odoo's `project.project` model.
- Expense heads will be custom records in this module.
- Bills will use a custom model in the first delivery.
- The GitHub repository can be public so the interviewer can view it.
- Live deployment is optional and should only happen after local Docker, tests, and video are ready.

## Source references

- Local Odoo 19 source: `/home/efaz/Codes/odoo`
- Official Odoo Docker image: https://hub.docker.com/_/odoo

## Success criteria

- The module installs in Docker.
- Fund accounts can receive confirmed incoming funds.
- Duplicate incoming transaction references are blocked per fund account.
- Allocation, requisition, and transfer submissions reserve money before approval.
- General Manager approval happens before Managing Director approval.
- Only the current approver can approve or reject.
- Users cannot approve their own requests unless explicitly allowed.
- Repeated approval actions do not create duplicate movements.
- Bills cannot exceed remaining billable amount.
- Bills cannot use another project or expense head's requisition.
- Reversal releases billable amount without creating extra money.
- Security is enforced server side.
- Tests cover the main double-spending paths.
- README explains installation, configuration, tests, assumptions, and limitations.
- The demo video can follow the assessment's sample flow.

## Delivery priority

### Must have

- Docker Compose setup for Odoo and PostgreSQL
- installable `nn_fund_management` module
- fund accounts and incoming funds
- fund movement ledger
- allocations with General Manager and Managing Director approval
- project and expense-head balances
- requisitions and bill control
- transfers between fund targets
- access control lists and record rules
- audit history
- automated tests for core money rules
- README and architecture notes

### Should have

- dashboard views for totals and pending approvals
- Odoo activities for approval tasks
- demo data for the sample scenario
- clear error messages for blocked actions
- GitHub issues matching implementation slices

### Bonus

- configurable approval rules by amount and request type
- bank email parsing prototype
- public live deployment

## Architecture

Use one Odoo addon under `addons/nn_fund_management`.

The addon should keep business logic in model actions and small shared services. Views should only expose actions. They must not be the only place where permissions are enforced.

### Core models

| Model | Purpose |
|---|---|
| `fund.account` | Bank, cash, or other account that receives incoming funds |
| `fund.incoming` | Incoming fund receipt before and after confirmation |
| `fund.expense.head` | Custom expense category that can receive and spend funds |
| `fund.movement` | Append-only record of money moving between balance buckets |
| `fund.allocation` | Request to assign unassigned fund-account money to a fund target |
| `fund.requisition` | Request to reserve project or expense-head money for bills |
| `fund.bill` | Custom bill linked to an approved requisition |
| `fund.transfer` | Request to move money between fund targets |
| `fund.approval.rule` | Configurable approval rule |
| `fund.approval.step` | Current and completed approval steps for a request |
| `fund.approval.history` | Decision log for approvals, rejections, and comments |

### Balance buckets

The ledger should represent these balance buckets:

- fund-account unassigned money
- fund-account allocation hold
- target available money
- target requisition hold
- target transfer hold
- target approved but unspent money
- target spent money

### Movement rules

Incoming confirmation:

- add to fund-account unassigned money

Allocation submission:

- subtract from fund-account unassigned money
- add to fund-account allocation hold

Allocation approval:

- subtract from fund-account allocation hold
- add to target available money

Allocation rejection or cancellation:

- subtract from fund-account allocation hold
- add to fund-account unassigned money

Requisition submission:

- subtract from target available money
- add to target requisition hold

Requisition approval:

- subtract from target requisition hold
- add to target approved but unspent money

Requisition rejection or cancellation:

- subtract from target requisition hold
- add to target available money

Bill posting:

- subtract from target approved but unspent money
- add to target spent money

Bill reversal:

- subtract from target spent money
- add to target approved but unspent money

Transfer submission:

- subtract from source target available money
- add to source target transfer hold

Transfer approval:

- subtract from source target transfer hold
- add to destination target available money

Transfer rejection or cancellation:

- subtract from source target transfer hold
- add to source target available money

## Workflow design

### Incoming funds

States:

1. draft
2. confirmed
3. cancelled

Rules:

- Only finance users can confirm incoming funds.
- A confirmed fund cannot be deleted.
- Transaction reference must be unique per fund account.
- Confirmation creates exactly one incoming movement.

### Allocations

States:

1. draft
2. submitted
3. gm_approved
4. approved
5. rejected
6. cancelled

Rules:

- A request uses either a project or an expense head.
- Submission checks unassigned balance.
- Submission creates a hold.
- General Manager approval must happen before Managing Director approval.
- Final approval assigns money to the target.
- Rejection or cancellation releases the hold.

### Requisitions

States:

1. draft
2. submitted
3. gm_approved
4. approved
5. rejected
6. cancelled
7. closed

Rules:

- A requisition uses either a project or an expense head.
- Submission checks target available balance.
- Submission creates a requisition hold.
- Approval keeps money reserved for bills.
- Closing releases unused approved money.

### Bills

States:

1. draft
2. posted
3. reversed
4. cancelled

Rules:

- A bill must link to an approved requisition.
- A bill must use the same project or expense head as the requisition.
- Total posted bills cannot exceed approved requisition amount.
- Reversal restores remaining billable amount.
- Reversal does not create extra money.

### Transfers

States:

1. draft
2. submitted
3. gm_approved
4. approved
5. rejected
6. cancelled

Rules:

- Source and destination cannot be the same.
- Source and destination can be project or expense head.
- Submission checks source available balance.
- Submission creates transfer hold.
- Approval moves money to destination available balance.
- Rejection or cancellation returns money to source available balance.

## Security design

Groups:

- Fund User
- Finance User
- General Manager Approver
- Managing Director Approver
- Fund Administrator
- Self Approval Override

Server-side checks:

- confirm incoming funds only for Finance User or Fund Administrator
- approve only for the current approval step's user or group
- block self approval unless the user has Self Approval Override
- cancel approved financial records only for Finance User or Fund Administrator
- block unlink on confirmed, approved, posted, or reversed financial records
- enforce company ownership on all major models

Record rules:

- users can see records for their allowed companies
- requesters can see their own requests
- approvers can see requests assigned to their approval step
- administrators can see all records in allowed companies

## Phase plan

### Phase 0: initialization

Output:

- extracted assessment text
- prompt-injection review
- repo guidance
- domain glossary
- architecture decision record
- PRD and implementation plan
- GitHub repository

Verification:

- extracted text is readable
- prompt-injection scan is recorded
- Git history has phased planning commits
- remote points to GitHub

### Phase 1: Docker and module scaffold

Output:

- `compose.yaml`
- `config/odoo.conf`
- `addons/nn_fund_management` skeleton
- module manifest
- base menus
- empty security files

Verification:

- Odoo starts through Docker Compose
- module appears in Apps
- module installs without model access warnings

### Phase 2: fund accounts and incoming funds

Output:

- fund account model
- incoming fund model
- transaction reference uniqueness
- confirmation action
- basic views

Verification:

- confirmed incoming funds increase unassigned balance
- duplicate references are blocked
- non-finance users cannot confirm incoming funds

### Phase 3: movement ledger and balances

Output:

- `fund.movement`
- balance calculation methods
- movement idempotency constraints
- tests for incoming movements

Verification:

- balances match movement totals
- repeated confirm actions are blocked
- confirmed records cannot be deleted directly

### Phase 4: allocation workflow

Output:

- allocation request model
- project and expense-head targets
- approval rules and approval steps
- hold, approve, reject, and cancel logic

Verification:

- unavailable allocation is blocked
- pending allocation money cannot be reused
- General Manager approval is required before Managing Director approval
- repeated approval does not duplicate movements

### Phase 5: requisitions and bills

Output:

- requisition model
- bill model
- remaining billable amount
- post and reverse actions

Verification:

- requisition submission reserves money
- over-billing is blocked
- wrong-target bills are blocked
- reversal restores billable amount

### Phase 6: transfers

Output:

- transfer model
- source and destination target fields
- transfer hold logic
- transfer approval flow

Verification:

- source equals destination is blocked
- unavailable transfer is blocked
- pending transfer money cannot be spent or requisitioned
- rejected transfer returns money to the source

### Phase 7: security and audit hardening

Output:

- final access control lists
- record rules
- group checks
- approval history records
- chatter tracking

Verification:

- unauthorized approvals are blocked by server-side checks
- multi-company access is blocked
- confirmed financial records cannot be deleted
- audit history contains each decision

### Phase 8: dashboard and notifications

Output:

- dashboard menu or reporting views
- pending approval views
- Odoo activities for approval tasks
- demo data

Verification:

- dashboard shows received, held, assigned, spent, and pending approvals
- activity is created for current approver
- demo flow can be run from a fresh database

### Phase 9: documentation and submission

Output:

- README with version, installation, dependencies, configuration, tests, assumptions, limitations
- architecture explanation
- AI usage notes
- demo script
- screen recording

Verification:

- fresh clone install works
- test command works
- video follows the required sample scenario
- GitHub link is accessible

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Balance bugs | Use movement ledger and tests for every workflow transition |
| Approval bypass | Put checks in server-side action methods |
| Record rule gaps | Test with separate users and companies |
| Time pressure | Deliver core workflows first and keep bank email integration as bonus |
| Overbuilt UI | Use normal Odoo views before custom JavaScript |
| Odoo accounting complexity | Use a custom bill model first |
| Concurrency double spending | Use a documented row lock around reservation checks if tests show risk |

## Open questions with recommended answers

1. Should the repository be public or private?
   Recommended answer: public, because the interviewer needs a repository link.

2. Should bills use Odoo Vendor Bills?
   Recommended answer: not for the first delivery. Use a custom bill model so the assessment stays focused on fund control.

3. Should approval rules be fully configurable from the start?
   Recommended answer: build default General Manager and Managing Director rules first, then add amount-based configuration if time remains.

4. Should live deployment be required?
   Recommended answer: treat it as bonus. Local Docker, tests, and video carry more evaluation weight.

5. Should direct SQL be avoided completely?
   Recommended answer: avoid it except for a documented row lock if needed to prevent concurrent double spending.
