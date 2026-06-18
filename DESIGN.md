# Design context

## Register

Product. The Odoo module is an operational tool, and the presentation site is a reviewer-facing summary of that tool.

## Principles

- Prefer clarity over decoration.
- Use restrained color and high contrast.
- Keep sections scannable.
- Avoid fake metrics.
- Keep cards for individual items only.
- Use icons for recognition, not decoration.

## Visual system

- Primary color: deep green for fund control and approval.
- Secondary color: muted gold for review and approval accents.
- Backgrounds: light neutral surfaces for readability.
- Typography: system sans, fixed scale, no italic headings.
- Radius: small rounded corners, usually 6 to 8 pixels.
- Motion: minimal and state-driven only.

## Frontend notes

The presentation uses Vite, React, Tailwind, Playwright, lucide icons, and shadcn-style local components. It should remain static, fast, and easy to deploy on Vercel.
