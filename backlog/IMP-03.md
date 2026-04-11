---
id: IMP-03
name: Document Local Seed Mode in AUDIENCE_GUIDE and README
epic: Epic 8 - Improvements
status: [x] Done
summary: Update AUDIENCE_GUIDE.md and README.md to document the make seed LOCAL=1 offline fallback for workshop environments.
---

# IMP-03 - Document Local Seed Mode in AUDIENCE_GUIDE and README

- Epic: Epic 8 - Improvements
- Priority: P1
- Estimate: S
- Status: [x] Done
- Source: PRODUCT_BACKLOG.md

## Objective

Update `AUDIENCE_GUIDE.md` and `README.md` so workshop participants know they can run `make seed LOCAL=1` when GitHub Archive access is slow or unavailable, and understand the trade-off between the full dataset and the controlled local fixture.

## Description

The local seed mode added in IMP-01/IMP-02 is only useful if participants know it exists. The AUDIENCE_GUIDE.md is the primary reference for workshop attendees — it must explain when and why to use `LOCAL=1`, what data it loads, and how it affects demo queries. README.md should be updated in the Requirements section to clarify that internet access is only needed for the default seed path.

## Scope

- `AUDIENCE_GUIDE.md` Section 5 (Infrastructure Setup): add a "No internet? Use the local seed" callout showing `make seed LOCAL=1` with a brief note on what data it contains and how it supports the ghost-contributor pattern.
- `AUDIENCE_GUIDE.md` Section 13 (Reference — All Commands): update the `make seed` row to note the `LOCAL=1` option.
- `README.md` Requirements: update the internet access note to say it is only required for the default seed (not `LOCAL=1`).
- `README.md` Quick Start: add `make seed LOCAL=1` as an alternative line with a comment.

## Out Of Scope

- Changing any code or SQL files.
- Adding a new documentation file.
- Updating `docs/TROUBLESHOOTING.md` or other docs/ files.
- Documenting the internal implementation of the seed script.

## Deliverables

- Updated `AUDIENCE_GUIDE.md` with LOCAL seed callout in Section 5 and updated reference table in Section 13.
- Updated `README.md` with internet-access clarification and LOCAL seed alternative in Quick Start.

## Acceptance Criteria

- `AUDIENCE_GUIDE.md` Section 5 includes `make seed LOCAL=1` with a description of the controlled dataset.
- `AUDIENCE_GUIDE.md` Section 13 reference table reflects `LOCAL=1` as an option on the seed row.
- `README.md` Requirements no longer states internet access is unconditionally required.
- `README.md` Quick Start shows `make seed LOCAL=1` as an alternative.

## Dependencies

- IMP-01 and IMP-02 should be complete or in progress so the documented commands actually work.

## Assumptions

- No new sections need to be added to AUDIENCE_GUIDE.md — changes fit into existing sections.
- The local dataset description (10–20 rows, 2–3 repos, ghost-contributor pattern) is sufficient for participants to understand the trade-off.

## Verification

1. Read the updated Section 5 of AUDIENCE_GUIDE.md and confirm the callout is clear and actionable.
2. Check the reference table in Section 13 for the updated seed row.
3. Read the README.md Requirements and Quick Start sections to confirm the changes are accurate.

## Notes

- Created 2026-04-09 as the third task of Epic 8 - Improvements.
- Motivated by the fact that presenters need to know about the offline fallback before the workshop starts.
