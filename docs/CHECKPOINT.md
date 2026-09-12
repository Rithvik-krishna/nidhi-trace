# Dashboard cleanup checkpoint — 2026-09-12

## Latest update — quick fixes resumed

Fixes **6 and 7 are now implemented** in separate commits: removed the unsupported
SLA and disabled/reworded prototype administrative actions. Focused JavaScript
checks passed; full browser/backend integration tests have not run.
**Remaining: fix 3 (signal badge), fix 4 (percentage denominators), fix 5 (chart
provenance/labels), plus the integration/performance checks below.**
The sections below record the earlier checkpoint; their unfinished entries for
6–7 are superseded by this update and `dashboard-integrity.md`.


Stopped at the user's request. This is a partial implementation, not a release.
Branch: `fix/dashboard-data-integrity`. Nothing was merged into main or deployed.

## Saved implementation

1. `fd79155` — Remove retired round-number scoring, export fields, Overview cards,
   Analytics donut entries, dossier detector entry and assistant references.
   The exporter previously added 14 points and could add a multiple-signal bonus.
   Regenerated case scores and aggregates are in the next commit.
2. `11960fb` — Reconcile the full real validation snapshot, regenerate exports,
   remove legacy MP flag mixing, make priority tiers disjoint, export the complete
   flagged queue, use unique snapshot row IDs, and share exported API summaries.
   Git history confirms c56717a changed the total without changing the old tiers.
   Corrected counts: **1,137 + 6,844 + 15,926 = 23,907**. The **23,329** figure is
   rule-only; the full anomaly queue also includes Isolation Forest flags.

See `dashboard-integrity.md` and `overview_kpis.json.provenance` for definitions,
source hashes and known differences between the GitHub and local detector code.
No rule engine, Isolation Forest or bootstrap validation code was changed.
The existing `E:/nidhitrace` backend and datasets were read only.

## Verification actually completed

- Ran the original exporter against the supplied CSVs into a scratch directory
  to establish the old calculation, then ran the revised exporter.
- Independently counted all 171,890 real validation rows, excluding 72 synthetic
  rows. Confirmed the active signal union, rule-only count and monetary exposure.
- Confirmed all merged/real-validation rows align on sanction amount and gap days.
- `scripts/test_dashboard_integrity.py`: **4 tests passed** with the source CSV
  directory supplied. Checks cover disjoint/complete tiers, unique case IDs,
  every flagged dossier, matching root/screens exports, retired detector removal,
  source SHA-256 and every exported case's active flags and sanction amount.
- Python compilation passed for backend, API and scripts after the summary edits.
- The unintegrated signal helper passed `node --check` only.
- Working-tree whitespace check passed before checkpointing.

## Incomplete fix 3

`assets/js/dossier-signals.js` is a **draft, unintegrated helper**. It normalizes
explicit top-level/nested booleans and counts DQ subflags as one signal. It is not
loaded by the HTML and has no render test. The attempted integration script
stopped before modifying the dossier or seeder. The badge bug therefore remains.

Confirmed causes to address next:

- `renderFlagsList()` returns because `dossier-flags-list` does not exist in HTML;
  the badge update is below that return.
- `normalizeDossierData()` ignores nested delay/amount/drift flags and substitutes
  thresholds and invented fallback z-scores. Count explicit pipeline booleans.
- Set both badges before optional cards/accordion rendering. Test real cases
  with zero, two and multiple signals, static and API-shaped records, and missing IDs.
- Remove fuzzy suffix case matching and the fabricated missing-case fallback.
- Seed DQ booleans into API dossiers; currently they are not preserved by the seeder.

## Fixes 4–7 remain unfinished

4. **Denominators:** 36.1% came from 62,089 DQ records / 171,890 analyzed records.
   52.7% came from 13,435 delay flags / an older roughly 25,483-record queue.
   Overview ranks raw counts but displays these inconsistent percentages. Rewrite
   the finding and category labels from one explicit denominator (or clearly
   separate DQ and anomaly metrics). The regenerated exporter currently includes
   four anomaly categories; decide how to display the separate DQ count without
   reinstating the stale static percentages. Static fallback copy still needs cleanup.
5. **Charts:** quarterly releases are estimated at 92% of allocation; expenditure
   is inferred from work status. The financial chart still needs removal or an
   explicit illustrative badge, including related utilization KPIs. Monthly
   counts are actually grouped by sanction date, not detection date, and export
   only critical/high series. Verify and relabel accurately or remove. Neither
   chart has yet been removed or visibly labeled as illustrative.
6. **45-day SLA:** found in dossier text, breach logic and technical modal. No
   supporting rule/config definition was found in the searched repository files.
   Remove the claim and drive delay presentation from the exported flag; a final
   repository-wide check is still required.
7. **Enforcement copy:** assign/freeze/escalation handlers update browser storage,
   local notes, status badges and toast messages. No backend action is called in
   those handlers. Reword buttons, dialogs, restored statuses, notes and toasts;
   add visible prototype clarification and disabled state or tooltip.

## Untested / deployment considerations

- No browser/render checks have run for any changed page. No backend HTTP or
  freshly seeded SQLite integration test has run. Do not present those as passed.
- Existing populated SQLite databases are not automatically reseeded. Verify that
  their active-flag queries match the snapshot before deployment; do not overwrite
  an existing live database without an explicit migration/reseed decision.
- Exporting all 23,907 flagged cases produces roughly 36 MB of flagged JSON and
  39 MB of dossier JSON per root/screens copy. Browser loading/performance has not
  been checked. These files are below GitHub's per-file 100 MB limit.
- IDs now identify source rows within this hashed snapshot. Audit hardcoded/default
  links, historical saved notes and callers before deployment. Old serial-number
  aliases are not retained because they were ambiguous; `originalWorkId` is retained.
- Root/screens HTML and data were synchronized. A full UI regression, zero-value
  KPI rendering, API fallback and assistant response checks are still pending.
- The existing sitewide audit script contains stale expected totals (198,116 /
  25,483); it was not run or represented as passing.
- A scratch virtual environment was being installed outside the repo for future
  backend tests. Its dependency installation is not an application verification.

## Resume and push

The user confirmed a successful push dry run in their own PowerShell. This agent's
credential store access was unavailable; no push was performed by the agent.

```powershell
Set-Location 'C:\Users\ACER.DESKTOP-R4G9UL6\Documents\Codex\2026-09-12\yes-let-s-do-it-directly\nidhi-trace'
git push -u origin fix/dashboard-data-integrity
```

Continue from fix 3, then 4–7, preserving a separate commit for each completed fix.
