# Domain glossary

This file defines the business terms for `nn_fund_management`. It avoids implementation details.

## Terms

### Fund account

A bank, cash, or other financial account that receives money before that money is assigned to a project or expense head.

### Incoming fund

A recorded receipt of money into a fund account. It includes the amount, date, sender or source, reference, attachment, company, and status.

### Transaction reference

The external reference for an incoming fund. The same reference cannot be reused inside the same fund account.

### Unassigned balance

Money in a fund account that has been received but not assigned to any project or expense head.

### Held amount

Money that has been reserved by a pending request. Held money cannot be assigned, transferred, or spent by another request.

### Allocation

A request to assign unassigned fund-account money to one project or one expense head.

### Project

A work area that can receive allocated money, request spending, receive transfers, and send transfers.

### Expense head

A spending category such as salary, rent, utilities, marketing, or administration. It can receive allocated money, request spending, receive transfers, and send transfers.

### Fund target

A project or expense head. A request can use one fund target, never both.

### Requisition

A request to reserve money from a fund target for future bills.

### Bill

A spending record linked to an approved requisition. A bill reduces the requisition's remaining billable amount and increases spent amount.

### Transfer

A request to move money from one fund target to another fund target.

### Approval level

One step in an approval process. The assessment requires General Manager approval before Managing Director approval.

### Current approver

The user or group allowed to approve or reject the current approval level.

### Approval history

The record of every approval decision. It includes approver, date, level, comment, result, previous status, and new status.

### Available fund

Money that is assigned to a fund target and is not held, spent, or transferred away.

### Requisition hold

Money reserved by a pending or approved requisition.

### Transfer hold

Money reserved by a pending transfer.

### Remaining billable amount

The approved requisition amount that has not been billed yet.

### Spent amount

Money consumed by posted bills.

### Cancellation

A workflow action that stops a draft or pending request and releases any held money back to its previous available balance.

### Reversal

A workflow action that undoes a posted bill without creating additional money.

### Double spending

Any case where the same money is assigned, transferred, requisitioned, or billed more than once.
