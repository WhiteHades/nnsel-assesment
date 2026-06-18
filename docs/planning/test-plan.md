# Test plan

## Test goal

The tests must prove that money cannot be counted twice, held twice, transferred twice, or spent twice.

The best tests are Odoo transaction tests around model actions. They should use real users, groups, companies, records, and workflow actions.

## Test boundary

Test through public action methods such as submit, approve, reject, cancel, post, reverse, close, and release.

Do not test private helper names. Test the visible behavior:

- final workflow state
- balance fields
- movement rows
- history rows
- access errors
- validation errors

## Test data

Create these fixtures in tests:

- one company
- optional second company for isolation tests
- fund account
- Project A
- Project B
- expense head for salary
- expense head for utilities
- fund user
- finance user
- General Manager approver
- Managing Director approver
- fund administrator

## Core test suites

### Incoming funds

- confirmed incoming fund increases unassigned balance
- duplicate reference is blocked in the same fund account
- same reference is allowed in a different fund account only if the business rule allows it
- non-finance user cannot confirm incoming funds
- confirmed incoming fund cannot be deleted
- repeated confirm does not create duplicate movements

### Allocation

- allocation to project can be submitted when unassigned balance is enough
- allocation to expense head can be submitted when unassigned balance is enough
- allocation with both project and expense head is blocked
- allocation with neither project nor expense head is blocked
- allocation above available unassigned balance is blocked
- submitted allocation creates hold and reduces unassigned available balance
- second allocation cannot use held money
- Managing Director approval before General Manager approval is blocked
- wrong approver is blocked
- self approval is blocked without override
- final approval assigns money to target available balance
- rejection releases hold to unassigned balance
- cancellation releases hold to unassigned balance
- repeated approval does not duplicate movements

### Requisition

- requisition can be submitted from a funded project
- requisition can be submitted from a funded expense head
- requisition above available target balance is blocked
- submitted requisition creates hold
- second requisition cannot use held money
- approved requisition moves money to approved but unspent amount
- rejection releases hold
- cancellation releases hold
- unused approved amount can be released on close
- fully billed requisition can be closed

### Bills

- bill can be posted against an approved requisition
- bill against non-approved requisition is blocked
- partial bill reduces remaining billable amount
- multiple partial bills cannot exceed approved amount
- bill above remaining billable amount is blocked
- Project A cannot bill against Project B requisition
- one expense head cannot bill against another expense head's requisition
- reversal restores remaining billable amount
- repeated reversal does not create extra money

### Transfers

- project to project transfer can be submitted
- project to expense-head transfer can be submitted
- expense-head to project transfer can be submitted
- expense-head to expense-head transfer can be submitted
- source equals destination is blocked
- transfer above source available balance is blocked
- submitted transfer creates transfer hold
- held transfer money cannot be requisitioned
- held transfer money cannot be transferred again
- final approval moves money to destination available balance
- rejection returns money to source available balance
- cancellation returns money to source available balance

### Security

- Fund User can create and view allowed requests
- Finance User can confirm incoming funds
- General Manager Approver can approve only General Manager steps assigned to them
- Managing Director Approver can approve only Managing Director steps assigned to them
- Fund Administrator can configure rules and manage records
- users cannot approve their own requests without override
- users cannot access unauthorized company records
- users cannot cancel approved transactions unless authorized
- hiding buttons is not the only protection, because direct action calls are also blocked

### Audit

- submit action records submitter and date
- approval records approver, level, comment, result, and date
- rejection records previous and new status
- movement records reference the source document
- confirmed financial records cannot be unlinked without cancellation or reversal

### Demo flow

Automate the assessment's sample demonstration as one end-to-end test:

1. Receive BDT 1,000,000.
2. Request BDT 600,000 for Project A.
3. Assert BDT 600,000 is held.
4. Reject and assert money returns to unassigned balance.
5. Submit again and approve.
6. Transfer BDT 200,000 from Project A to Project B.
7. Assert BDT 200,000 is held while pending.
8. Approve transfer.
9. Create BDT 150,000 requisition for Project B.
10. Create BDT 100,000 bill.
11. Assert BDT 50,000 remains billable.
12. Try BDT 60,000 bill and assert it is blocked.
13. Try to use Project B's requisition for Project A and assert it is blocked.

## Planned verification commands

The exact command can change after the Docker scaffold exists. The planned command shape is:

```bash
docker compose run --rm odoo odoo -d nnsel_test -i nn_fund_management --test-enable --stop-after-init
```

Also run a fresh install check:

```bash
docker compose run --rm odoo odoo -d nnsel_install -i nn_fund_management --stop-after-init
```

## Manual checks

- install module from Apps
- create demo users and assign groups
- run the sample demonstration from the UI
- confirm button visibility matches permissions
- call protected actions from a user without permission and confirm server-side errors
- inspect chatter and approval history
