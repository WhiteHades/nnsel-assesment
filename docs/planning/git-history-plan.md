# Git history plan

The assessment asks for meaningful Git history. Commits should be small, phased, and honest.

Commit messages must be one-line, conventional, lowercase, and short.

## Completed planning commits

- `docs: add assessment extraction`
- `chore: add repo guidance`
- `docs: define fund domain`

## Planned planning commit

- `docs: add implementation plan`

## Planned implementation commits

- `chore: add docker scaffold`
- `feat: add module skeleton`
- `feat: add fund accounts`
- `feat: record incoming funds`
- `feat: add fund movement ledger`
- `test: cover incoming funds`
- `feat: add allocation approvals`
- `test: cover allocation balances`
- `feat: add requisition workflow`
- `feat: add bill controls`
- `test: cover requisitions and bills`
- `feat: add fund transfers`
- `test: cover transfer holds`
- `feat: add security rules`
- `test: cover access controls`
- `feat: add dashboard views`
- `docs: finish module readme`
- `chore: add demo data`

## Commit grouping rules

- Commit docs separately from executable code.
- Commit tests with the feature they verify when the test is small.
- Use separate commits for large test suites.
- Do not commit generated database files, local Odoo data, or secrets.
- Do not rewrite history after pushing unless the user asks.

## Interview value

The history should show the path:

1. understand the assignment
2. plan the domain and architecture
3. scaffold the module
4. build the money ledger
5. add workflows one by one
6. harden security and tests
7. prepare the demo and docs
