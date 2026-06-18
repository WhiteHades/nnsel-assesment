# Issue breakdown

This is the proposed `to-issues` breakdown. It is not published to GitHub Issues yet. The skill expects user approval of issue granularity before publishing.

## Proposed slices

1. **Create Dockerized Odoo scaffold**
   - Blocked by: none
   - User stories covered: 1, 2, 27

2. **Add installable module shell and security groups**
   - Blocked by: issue 1
   - User stories covered: 23, 47, 48, 50

3. **Record fund accounts and incoming funds**
   - Blocked by: issue 2
   - User stories covered: 1 to 5

4. **Add ledger-backed balances**
   - Blocked by: issue 3
   - User stories covered: 15 to 20, 25, 51

5. **Build allocation workflow with approvals**
   - Blocked by: issue 4
   - User stories covered: 6 to 14, 42 to 46

6. **Build requisition workflow**
   - Blocked by: issue 5
   - User stories covered: 21 to 27

7. **Build bill posting and reversal controls**
   - Blocked by: issue 6
   - User stories covered: 28 to 33

8. **Build transfer workflow**
   - Blocked by: issue 5
   - User stories covered: 34 to 41

9. **Harden access control and multi-company rules**
   - Blocked by: issues 5, 6, 7, 8
   - User stories covered: 47 to 52

10. **Add dashboard, activities, and demo data**
    - Blocked by: issues 7, 8, 9
    - User stories covered: 57, 58

11. **Finish README, architecture notes, and demo script**
    - Blocked by: issues 7, 8, 9
    - User stories covered: 27, 52

12. **Add optional bank email prototype**
    - Blocked by: issue 3
    - User stories covered: 54 to 56

## Publication rule

Publish these to GitHub only after the user confirms the granularity and dependencies. If published, apply `ready-for-agent` to implementation-ready issues.
