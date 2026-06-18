# Demo script

## Setup

1. Start Docker:

   ```bash
   docker compose up -d
   ```

2. Open `http://localhost:8069`.
3. Create a database if one does not exist.
4. Install the `NN Fund Management` app.
5. Assign users to the needed groups:
   - Finance User
   - Fund User
   - GM Approver
   - MD Approver
   - Fund Administrator

## Walkthrough

### 1. Confirm incoming funds

Open `Fund Management > Incoming Funds`.

Create an incoming fund:

- Fund Account: main bank account
- Amount: BDT 1,000,000
- Transaction Reference: a unique bank reference
- Sender: NN Services

Click `Confirm`.

Expected result: the fund account unassigned balance increases by BDT 1,000,000.

### 2. Submit and reject an allocation

Open `Fund Management > Allocations`.

Create an allocation:

- Fund Account: main bank account
- Project: Project A
- Amount: BDT 600,000
- Purpose: Project A funding

Click `Submit`.

Expected result: unassigned balance drops to BDT 400,000 and allocation hold becomes BDT 600,000.

Log in or impersonate the GM approver and click `Reject`.

Expected result: the hold is released and unassigned balance returns to BDT 1,000,000.

### 3. Approve an allocation

Create the allocation again for BDT 600,000.

Click `Submit`, then approve as GM, then approve as MD.

Expected result: Project A available fund becomes BDT 600,000.

### 4. Transfer funds

Open `Fund Management > Transfers`.

Create a transfer:

- Source Project: Project A
- Destination Project: Project B
- Amount: BDT 200,000
- Reason: move funds to Project B

Click `Submit`.

Expected result: Project A available fund drops by BDT 200,000 and transfer hold becomes BDT 200,000.

Approve as GM, then MD.

Expected result: Project B available fund becomes BDT 200,000.

### 5. Requisition and bill

Open `Fund Management > Requisitions`.

Create a requisition:

- Project: Project B
- Amount: BDT 150,000
- Purpose: supplier bill

Submit, approve as GM, then approve as MD.

Open `Fund Management > Bills`.

Create a bill:

- Requisition: the approved Project B requisition
- Amount: BDT 100,000
- Vendor: any supplier

Click `Post`.

Expected result: BDT 100,000 moves to spent, and BDT 50,000 remains billable.

### 6. Show blocked cases

Try a second bill for BDT 60,000 against the same requisition.

Expected result: Odoo blocks the bill because only BDT 50,000 remains.

Try to create a bill for Project A against the Project B requisition.

Expected result: Odoo blocks the wrong-target bill.

Try to approve your own request without the override group.

Expected result: Odoo blocks self approval.

### 7. Show expense-head controls

Open `Fund Management > Allocations`.

Create an allocation to an expense head, for example `Salary`, then approve it as GM and MD.

Open `Fund Management > Requisitions`.

Create a requisition against the same expense head, approve it, and post a partial bill.

Expected result: the expense head available, approved, and spent balances update separately from project balances.

Try to create a bill for another expense head against that requisition.

Expected result: Odoo blocks the wrong-head bill.

### 8. Show cancellation and parser controls

Open `Fund Management > Incoming Funds`.

Confirm an incoming fund, then cancel it as a finance user.

Expected result: the record is cancelled and the unassigned balance is reversed by a cancellation ledger movement.

Open `Fund Management > Bank Emails`.

Parse a valid bank message with amount and reference.

Expected result: Odoo creates a pending incoming fund for finance review.

Parse an invalid message.

Expected result: Odoo marks parsing as failed and creates an activity for follow-up.

## Close

Open the dashboard and audit history to show:

- total received
- unassigned balance
- pending approvals
- ledger movement trail
- approval history

For the final interview recording, follow `docs/recording-guide.md`.
