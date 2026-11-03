# ONECALL online platform — foundation

The application is being developed in two independent layers:

1. **Presentation** — `prototype/web/styles.css` defines design tokens for colors, shapes, spacing, and typography. `prototype/web/design.js` offers reversible local theme presets. The quotation engine does not know about appearance settings. Replacing the theme or page layout will not require changing pricing calculations.
2. **Business processes** — `prototype/pricing.py`, `prototype/database.py` and `prototype/server.py` are a fictional local workflow only. They are **not** production endpoints.
3. **Online data model** — `platform/migrations/001_core.sql` is a **proposed, unexecuted PostgreSQL schema** for multiple businesses, roles, pricing versions, enquiries, quotations, approval events, booking requests, and private photo references.

## What is not live

- No online service has been created, connected or deployed.
- No authentication provider or secure user signup is connected.
- No production client data may be submitted.
- No actual photo uploads, image analysis, booking confirmation, notifications or payment services are connected.
- No user-facing row-level-security policies exist. The migration enables and forces deny-by-default RLS. It is **not ready for real users**.
- The local Python API's owner actions are unauthenticated. Do not expose it publicly.

## Design remains editable

The Design Studio is in the API-connected local prototype under the **Design Studio** tab.

Existing presets: Classic blue/gold, Midnight gold, Violet/pink and Forest green; corner radius, density and text sizes are also adjustable. Theme changes apply on this device only; saving uses browser localStorage. Reset returns to the original palette. Future business-specific branding should be stored server-side under authenticated business ownership, not in the quotation payload.

## Next build milestones

1. Verify the current branch in Codex and run the full test suite, then perform an interactive browser test. Run `python -m unittest discover -s prototype/tests -v` from repository root.
2. Choose a supported identity provider and hosted Postgres option. Keep credentials out of the repo. Obtain explicit approval before turning on any paid option.
3. Implement real tenant/member authorization and tenant isolation tests **before** connecting customer details.
4. Build private uploads and consent/privacy controls, then optional AI image-assistance with deterministic rule-based price calculation and mandatory owner review.
5. Add verified notification and booking flows, then optional deposits through an approved payment provider.
6. Private staging, operational testing, GDPR/privacy review, pilot businesses, production approval.

All backend migrations need reviewed grants, tenant-aware authorization policies, automated tests, backup/restore rehearsals and a security review before execution against an online customer database.

The original `main` branch and deployed site must remain untouched until owner approval.
