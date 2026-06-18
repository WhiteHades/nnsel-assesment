# User stories

These stories cover the assessment requirements and the planned implementation scope.

## Fund accounts and incoming funds

1. As a finance user, I want to create a fund account with a type, company, and name, so that incoming money has a source.
2. As a finance user, I want to record the date, amount, reference, sender, description, and attachment for incoming funds, so that receipts are traceable.
3. As a finance user, I want to confirm an incoming fund, so that the fund account's unassigned balance increases.
4. As a finance user, I want duplicate transaction references blocked inside the same fund account, so that the same receipt cannot be counted twice.
5. As a fund administrator, I want confirmed incoming funds protected from deletion, so that audit history is preserved.

## Allocations

6. As a fund user, I want to request allocation to a project, so that project spending can be funded.
7. As a fund user, I want to request allocation to an expense head, so that category spending can be funded.
8. As a fund user, I want an allocation to use either a project or an expense head, so that a request has one clear target.
9. As a requester, I want submitted allocation money held, so that the request cannot be undercut by another request.
10. As a requester, I want allocation submission blocked when unassigned balance is too low, so that balances never go negative.
11. As an approver, I want to approve or reject with a comment, so that the decision is recorded.
12. As a Managing Director approver, I want General Manager approval completed first, so that the required approval order is enforced.
13. As a requester, I want rejected allocation money returned to unassigned balance, so that it can be used later.
14. As a requester, I want cancelled allocation money returned to unassigned balance, so that draft mistakes do not trap money.

## Project and expense-head balances

15. As a fund user, I want to see total allocated money for each project or expense head, so that I understand funding.
16. As a fund user, I want to see available money, so that I know what can still be used.
17. As a fund user, I want to see requisition hold and transfer hold, so that pending requests are visible.
18. As a finance user, I want to see approved but unspent money, so that I know what is reserved for bills.
19. As a finance user, I want to see spent money, so that posted spending is visible.
20. As an administrator, I want balance fields protected from manual edits, so that the ledger remains the source of truth.

## Requisitions

21. As a fund user, I want to create a requisition from a project, so that project spending can be approved before billing.
22. As a fund user, I want to create a requisition from an expense head, so that category spending can be approved before billing.
23. As a requester, I want requisition submission blocked when available balance is too low, so that money cannot be over-reserved.
24. As a requester, I want submitted requisition money held, so that another requisition or transfer cannot use it.
25. As an approver, I want to approve a requisition, so that the approved amount can be billed later.
26. As a requester, I want unused approved requisition money releasable, so that leftover money returns to available balance.
27. As a requester, I want to close a fully billed requisition, so that completed spending is marked finished.

## Bills

28. As a finance user, I want to create a bill against an approved requisition, so that spending is linked to an approval.
29. As a finance user, I want partial bills allowed, so that one requisition can pay several bills.
30. As a finance user, I want a bill blocked when it exceeds remaining billable amount, so that over-spending is prevented.
31. As a finance user, I want wrong-project bills blocked, so that Project A cannot use Project B's requisition.
32. As a finance user, I want wrong-expense-head bills blocked, so that one expense head cannot use another expense head's requisition.
33. As a finance user, I want bill reversal to restore remaining billable amount, so that cancellation does not create extra money.

## Transfers

34. As a fund user, I want to transfer money from project to project, so that funding can move when project needs change.
35. As a fund user, I want to transfer money from project to expense head, so that funding can move to category spending.
36. As a fund user, I want to transfer money from expense head to project, so that category funds can support project work.
37. As a fund user, I want to transfer money from expense head to expense head, so that category budgets can be adjusted.
38. As a requester, I want transfer submission blocked when source available balance is too low, so that money cannot be over-transferred.
39. As a requester, I want source equals destination blocked, so that meaningless transfers cannot be created.
40. As a requester, I want submitted transfer money held, so that it cannot be spent or requested while pending.
41. As a requester, I want rejected or cancelled transfer money returned to source available balance, so that unused money is not trapped.

## Approvals

42. As a fund administrator, I want approvers configured by rule, so that user IDs are not hard-coded.
43. As an approver, I want to see only requests waiting for my approval, so that my queue is focused.
44. As a requester, I want self approval blocked, so that requesters cannot approve their own money.
45. As a fund administrator, I want a self-approval override group, so that exceptional cases can be granted deliberately.
46. As an auditor, I want each decision to record approver, date, level, comment, and result, so that approvals are explainable.

## Security and audit

47. As a fund user, I want to view records I am allowed to access, so that I can track my requests.
48. As a finance user, I want finance-only actions protected, so that normal fund users cannot confirm or cancel financial records.
49. As a company user, I want records limited to my allowed company, so that company data is isolated.
50. As an administrator, I want access rules enforced on the server, so that hiding buttons is not the only protection.
51. As an auditor, I want confirmed financial records preserved, so that history cannot be erased silently.
52. As an interviewer, I want clear error messages, so that blocked actions are understandable during the demo.

## Bonus stories

53. As a fund administrator, I want amount-based approval rules, so that larger requests can require more approval levels.
54. As a finance user, I want bank emails parsed into pending incoming fund records, so that receipts can be entered faster.
55. As a finance user, I want duplicate bank emails blocked by message ID, so that the same email is not processed twice.
56. As a finance user, I want failed email parsing logged, so that bad messages can be reviewed.
57. As a reviewer, I want a dashboard with totals and recent movements, so that the module can be inspected at a glance.
58. As an approver, I want Odoo activities for pending approvals, so that approval work appears in my queue.
