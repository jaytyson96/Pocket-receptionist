# ONECALL Smart Quote Lab V2 — development branch

This branch preserves the existing Harrow Pilot V3 at the repository root. The **new Smart Quote Lab V2 demonstration** is in `smart-quote/index.html`, added without modifying `main`, `index.html`, or `netlify.toml`.

## What is ready
- Four demo service categories, job-specific form fields, owner-editable illustrative pricing, local photo preview, and owner approval flow.
- Browser-only demonstration. Sample data is stored in browser localStorage; it does **not** use a secure backend.
- Open `smart-quote/index.html` locally or through a development-only preview to inspect the demo.

## Important: do not use with actual customers
The current quotation page has no authenticated business accounts and its owner controls are demonstrative only. Photos are not uploaded or analysed by AI. No live quotations, payments, or bookings are sent. **Do not submit real customer information.**

## Next integration milestone
A separately prepared downloadable local-development package contains Python pricing logic, a SQLite demo API, local-owner workflow and tests, but those backend files have **not yet been committed to this branch**. That Python server runs locally and is not a Netlify serverless function. Its unauthenticated owner actions must not be deployed publicly.

Next, safely integrate and independently test the local Python package in Codex, review the branch diff, add authentication before any public customer launch, then request approval before merging or deploying.

## Check
The existing production homepage and Netlify configuration should remain identical to `main`. No production deployment or merge has been requested.
