# ONECALL Smart Quote V2 — localhost development

This folder is a **fictional-data prototype** and is deliberately not integrated into the production Netlify site.

## Start locally (Python 3.11+)
```bash
cd prototype
python server.py
```
Then open http://127.0.0.1:4173/.

Run tests from the repository root:
```bash
python -m unittest discover -s prototype/tests -v
```
No third-party Python dependencies, AI API keys, paid services, or internet connection are needed.

## What the local demonstration supports
- Driveway and patio scope, entered measurements, surface/condition choices, optional biocide and block-paving re-sanding
- Deterministic £ GBP quote calculations from business-editable pricing rules
- Versioned and itemised draft with original pricing snapshot retained
- SQLite persistence for fictional enquiries
- Local owner dashboard for single approval/rejection and revised approved price
- Local browser photograph preview ONLY (not transmitted or inspected by AI)
- Health and basic HTTP endpoints for tests

## Privacy, security, and deployment limitations
**Do not use real customer data.** There are no accounts, login sessions, role isolation, or CSRF-proof business authentication. The owner controls are a simulation. The local web server binds to `127.0.0.1`; do not reverse-proxy it, expose it to the internet, or deploy these files to a publicly accessible host.

Do not assume the local `server.py` will run on Netlify: it is a long-running Python HTTP server, not a Netlify Function. It was not added to `netlify.toml`.

Inputs are owner-entered; AI image analysis, remote photo uploads, email, bookings, and payments are not implemented. The active root `index.html` is untouched.

## Before production
Introduce business authentication, authorization, audit logging, secure storage, GDPR/data retention handling, secure media storage, and verified email/booking/payments. Run security review and browser tests on an isolated staging setup. Do not merge or deploy until the owner approves.

## Version notes
This repository's `smart-quote/index.html` remains the earlier browser-only V2 reference. `prototype/web/index.html` is the newer API-connected local UI. The two are intentionally separate to preserve the prior prototype.
