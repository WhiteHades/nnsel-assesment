# Recording guide

The assessment asks for a screen recording with facecam. Record this yourself so the reviewer can see you explain the work.

## Setup

1. Start Odoo:

   ```bash
   docker compose up -d
   ```

2. Open Odoo:

   ```text
   http://localhost:8069
   ```

3. Open the live presentation:

   ```text
   https://nnsel-assesment.vercel.app
   ```

4. Keep the repository open at:

   ```text
   https://github.com/WhiteHades/nnsel-assesment
   ```

## Recording outline

Target length: 8 to 12 minutes.

1. Introduce the assessment in one sentence.
2. Say the module name: `nn_fund_management`.
3. Show the live presentation site.
4. Show the GitHub README and point to setup, tests, demo script, and implementation notes.
5. Explain the architecture: append-only ledger movements are the source of truth for balances.
6. Demonstrate incoming funds and duplicate transaction protection.
7. Demonstrate allocation submit, rejection, GM approval, and MD approval.
8. Demonstrate transfer hold and approval.
9. Demonstrate requisition approval, partial bill posting, and overbilling protection.
10. Demonstrate expense-head funding and wrong-head bill protection.
11. Show dashboard totals, activities, ledger movements, and approval history.
12. Show backend tests passing or explain the latest recorded test result.
13. Explain AI use with the checklist below.
14. Explain what you understand: Odoo models, ACLs, record rules, workflow methods, ledger accounting, approval rules, and Docker runtime.
15. Close with known limitations: Vercel hosts only the static presentation, Odoo and PostgreSQL run locally, and the bank email feature is a parser prototype.

## AI-use checklist

Cover these points in plain language:

- AI tools used: Codex, `lp-paddle`, and any local code search or verification tools used during the session.
- AI-assisted parts: assessment extraction, planning, domain modeling, implementation review, test ideas, documentation, and presentation polish.
- Prompt summaries: asked AI to extract the PDF safely, map requirements into Odoo workflows, review double-spending risks, add tests, improve handoff docs, and prepare the demo script.
- Errors found in AI-generated or AI-suggested code: incomplete server-side guards, missing edit locks after ledger movements, cancellation edge cases, and stale or incomplete handoff claims.
- Candidate changes: verified requirements against the assessment, reviewed Odoo source patterns, kept the ledger design, added server-side checks, ran tests, and reviewed diffs before committing.
- Understood parts: computed balance buckets, append-only movements, approval steps, ACLs, record rules, workflow methods, Docker runtime, and how to add or remove approval rules.
- Known limitations: custom bill model instead of Odoo Vendor Bills, local-only Odoo runtime, prototype bank email parsing, and no production deployment hardening.

## Commands to show

Backend test command:

```bash
TEST_DB=nnsel_final_$(date +%s)
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d "$TEST_DB" --init nn_fund_management --test-enable --test-tags /nn_fund_management --stop-after-init --without-demo=True --log-level=test
```

Frontend build command:

```bash
cd presentation
npm audit --audit-level=moderate
npm run build
npm run test:e2e
```

## Tools used

- Codex for planning, implementation support, tests, docs, and repository workflow
- `lp-paddle` for assessment PDF extraction
- Prompt-injection review before using the assessment content
- Odoo 19 source at `/home/efaz/Codes/odoo` for syntax checks
- Docker Compose for local Odoo and PostgreSQL
- GitHub CLI for repository setup and publishing
- Vercel CLI for the public static presentation

## Final checklist

- Facecam visible
- Screen readable at 100 percent browser zoom
- Audio clear
- Local Odoo workflow demonstrated
- GitHub README shown
- Tests mentioned with exact result
- AI tool usage explained honestly
- Vercel limitation explained clearly
