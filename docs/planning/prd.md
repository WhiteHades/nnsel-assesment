# Product requirements document

## Problem statement

NN Services and Engineering needs an Odoo module that tracks fund receipts, fund assignment, approvals, requisitions, bills, transfers, balances, and audit history. The main risk is double spending. The same money must not be assigned, held, transferred, or billed twice.

The assessment also evaluates development discipline. The submission must include Docker setup, security files, tests, readable documentation, AI usage transparency, and a meaningful Git history.

## Solution

Build an installable Odoo Community module named `nn_fund_management`.

The module will record incoming funds into fund accounts, reserve money during pending approvals, assign approved money to projects or expense heads, reserve money for requisitions, post bills against approved requisitions, transfer money between fund targets, and keep an audit trail for every financial action.

The implementation will use a ledger-backed movement model. Workflow actions create fund movements, and balance fields are calculated from those movements. This makes balances explainable and gives tests a clear source of truth.

## User stories

1. As a finance user, I want to create a fund account, so that incoming money has a known source.
2. As a finance user, I want to record an incoming fund, so that received money enters the system.
3. As a finance user, I want duplicate transaction references blocked per fund account, so that the same receipt is not counted twice.
4. As a finance user, I want to confirm an incoming fund, so that it increases the unassigned balance.
5. As a fund user, I want to request allocation from a fund account to a project, so that project spending can start after approval.
6. As a fund user, I want to request allocation from a fund account to an expense head, so that category spending can start after approval.
7. As a fund user, I want submitted allocation money placed on hold, so that another request cannot use it.
8. As a General Manager approver, I want to approve or reject submitted requests assigned to me, so that the first approval level is controlled.
9. As a Managing Director approver, I want to approve only after General Manager approval, so that approval order is enforced.
10. As an approver, I want comments recorded with each decision, so that later reviewers understand the decision.
11. As a requester, I want rejected or cancelled allocation money released, so that money can be used again.
12. As a fund user, I want project and expense-head balances to update automatically, so that I do not edit financial totals by hand.
13. As a fund user, I want to request money from a project or expense head, so that spending is reserved before a bill is posted.
14. As a fund user, I want pending requisition money placed on hold, so that another requisition or transfer cannot use it.
15. As a finance user, I want to post a bill against an approved requisition, so that spending reduces remaining billable amount.
16. As a finance user, I want partial bills allowed, so that a requisition can be used across more than one bill.
17. As a finance user, I want over-billing blocked, so that bills cannot exceed approved requisition money.
18. As a finance user, I want wrong-project and wrong-expense-head bills blocked, so that one target cannot spend another target's requisition.
19. As a finance user, I want bill reversal to restore remaining billable amount, so that cancellation does not create extra money.
20. As a fund user, I want to request transfers between projects and expense heads, so that money can be reassigned after approval.
21. As a fund user, I want pending transfer money placed on hold, so that it cannot be spent while waiting for approval.
22. As a fund administrator, I want approval rules configured by amount, request type, company, and approver, so that approvers are not hard-coded.
23. As a fund administrator, I want users grouped by role, so that each role has only the permissions it needs.
24. As a company user, I want records limited by company, so that I cannot access another company's financial records.
25. As an auditor, I want every status change and money movement recorded, so that I can explain a balance later.
26. As a reviewer, I want a dashboard with totals and pending approvals, so that I can inspect the module during the demo.
27. As an interviewer, I want tests for double spending and access control, so that I can trust the implementation.
28. As the candidate, I want a concise demo flow, so that I can show the required behavior before the deadline.

## Implementation decisions

- Use Odoo 19 Community for the Dockerized development environment.
- Use the official Odoo Docker image with PostgreSQL, mounted custom addons, and a local config file.
- Build one custom addon under `addons/nn_fund_management`.
- Depend on `base`, `mail`, and `project`.
- Use `project.project` for project targets.
- Create a custom `fund.expense.head` model for expense-head targets.
- Create a custom bill model first. Do not integrate with Odoo Vendor Bills in the first delivery.
- Use a custom fund movement ledger as the source of truth for balances.
- Use approval rules and approval step records so approvers are configurable.
- Use server-side action methods for submit, approve, reject, cancel, post, reverse, close, and release.
- Use access control lists, record rules, and explicit group checks.
- Use chatter and custom history records for audit history.
- Use direct SQL only if needed for row-level locking around balance reservation.
- Keep bank email integration as a bonus prototype after core workflows and tests pass.

## Testing decisions

- Test workflow behavior at the Odoo model action boundary.
- Test final balances and fund movement rows after each action.
- Test rejected, cancelled, and reversed workflows.
- Test repeated approve, repeated post, and repeated reverse actions.
- Test security through users in different groups.
- Test multi-company isolation.
- Test the assessment demonstration path end to end.
- Avoid tests that depend on view layout or internal helper names.

## Out of scope for the first implementation pass

- Full Odoo accounting integration
- Real bank credentials
- Production deployment before local Docker and tests pass
- Complex custom JavaScript dashboard
- Payroll or HR integration
- Multi-currency conversion unless time remains

## Further notes

The first delivery should optimize for correctness, explainability, and test coverage. Bonus features should not weaken the core fund controls.
