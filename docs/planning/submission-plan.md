# Submission plan

## Deadline

The assessment deadline is 24 June 2026 at 11:59 PM.

The safest submission target is 24 June 2026 by 8:00 PM, leaving a final buffer before the deadline.

## Deliverables

- installable Odoo module
- GitHub repository link
- README with Odoo version, installation, dependencies, configuration, testing, assumptions, and limitations
- access control and security files
- short architecture explanation
- screen recording with UI and code walkthrough
- AI usage explanation
- meaningful commit history
- Dockerized project

## Work calendar

### 18 June 2026

- convert assessment PDF
- check prompt-injection risk
- create planning docs
- create GitHub repository
- commit planning work

### 19 June 2026

- create Docker Compose setup
- create Odoo config
- create module skeleton
- add base groups, menus, access control files
- verify module installation

### 20 June 2026

- implement fund accounts and incoming funds
- implement movement ledger
- implement allocation workflow
- add allocation tests

### 21 June 2026

- implement requisitions
- implement custom bills
- implement bill posting and reversal
- add requisition and bill tests

### 22 June 2026

- implement transfers
- harden security checks and record rules
- add multi-company and authorization tests
- add audit history

### 23 June 2026

- add dashboard or reporting views
- add Odoo activities where useful
- add demo data
- finish README and architecture notes
- run full fresh install and test commands

### 24 June 2026

- record video
- review GitHub repository from a clean clone
- upload video to Google Drive with public access
- submit repository link and video link before 8:00 PM

## Video outline

Keep the video short and concrete:

1. State Odoo version and module name.
2. Show Docker Compose running.
3. Install or open the module.
4. Show security groups and users.
5. Run the sample demonstration:
   - receive BDT 1,000,000
   - request BDT 600,000 for Project A
   - show pending hold
   - reject and show release
   - submit again and approve
   - transfer BDT 200,000 to Project B
   - show pending transfer hold
   - approve transfer
   - create BDT 150,000 requisition
   - post BDT 100,000 bill
   - show BDT 50,000 remaining
   - show blocked BDT 60,000 bill
   - show blocked wrong-project bill
6. Show tests running.
7. Show key code:
   - movement ledger
   - approval checks
   - server-side security checks
   - tests for double spending
8. Explain AI usage:
   - planning help
   - code generation assistance
   - human review and corrections
   - errors found in AI output
9. State known limitations.

## README checklist

- Odoo version
- Docker prerequisites
- setup commands
- default users or demo accounts
- installation instructions
- module dependencies
- configuration steps
- testing commands
- architecture summary
- assumptions
- known limitations
- AI usage notes
- demo flow

## Known limitations to state if still true

- Vendor Bill integration is not included in the first version.
- Bank email parsing is a prototype or omitted if time runs out.
- Live deployment is optional and may be omitted if local Docker and tests are complete.
- Multi-currency support is not included unless added deliberately.

## Final verification checklist

- fresh clone starts with Docker Compose
- module installs in a new database
- tests pass
- README commands match the repository
- no secrets are committed
- GitHub repository is visible to the interviewer
- Google Drive video link is public
- commit history reads as phased work
