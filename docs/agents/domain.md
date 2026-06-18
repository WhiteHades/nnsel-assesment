# Domain docs

This repository uses a single domain context.

## Layout

- `CONTEXT.md`: domain glossary
- `docs/adr/`: architecture decision records
- `docs/planning/`: planning documents

## Rules

Read `CONTEXT.md` before changing domain terms.

Create an architecture decision record only when the decision is hard to reverse, would surprise a later reader, and has real tradeoffs.

Do not put implementation tasks in `CONTEXT.md`. It is a glossary, not a backlog.
