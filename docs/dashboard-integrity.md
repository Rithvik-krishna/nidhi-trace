# Dashboard data integrity audit

## 1. Retired amount-digit detector

Benford/round-number diagnostics are excluded from dashboard scoring, labels,
exports and the assistant prompt. The exporter previously added 14 points plus a
multi-signal bonus, so removing only the chart would leave contaminated scores.
The supplied validation CSV has 171,890 real rows; its 20 most common sanction
amounts cover 39.7365% of those rows. Administrative slab values make digit
nonconformity unsuitable as an anomaly signal for this dataset. The rule engine,
Isolation Forest and bootstrap scripts are unchanged. Aggregates and case scores
are regenerated as part of fix 2 below.

## 2. One queue definition and disjoint tiers

Commit c56717a replaced the exported total 25,483 with 23,329 while retaining
old score tiers 1,137 / 5,507 / 17,761. Those tiers were not overlapping: they
came from a different calculation. The exporter also ORed a legacy MP-baseline
flag with the validated flag, and mixed IF-only flagged cases with unflagged
cases in its low bucket. The total 23,329 is the *rule-only* queue.

Recomputed from all 171,890 real validation rows (72 synthetic rows excluded):
23,907 unique records trigger any of delay, amount, MP drift or Isolation Forest.
The existing score thresholds are retained for prioritization: 1,137 critical,
6,844 high and 15,926 remaining flagged records (medium), summing to 23,907.
There are 147,983 records with no anomaly signal. DQ is a separate, overlapping
review list and is not silently added to the anomaly queue. These are dashboard
priority tiers, not calibrated fraud probabilities or model severity classes.

Every flagged record is exported, rather than a capped sample. Previously reused
sanction serial IDs caused dossier collisions; IDs now use the six-digit real
source row, qualified by the snapshot SHA-256 stored in provenance. Original WORK
references are preserved. IDs must not be carried between different snapshots.
Unflagged dossiers remain a sample, so summary endpoints read the full export,
not the partial SQLite corpus. Existing populated SQLite databases must be
reseeded explicitly on deployment; this change does not overwrite live databases.

Reproduce with NIDHI_PROCESSED_DIR pointing at the processed CSV folder, then run
`python scripts/generate_dashboard_data.py`. Source hashes are in overview_kpis.json.
The supplied files were read from E:/nidhitrace/data/processed without modification.
The GitHub detector source differs from that backend's validated pipeline;
no detector or validation code was changed or re-run to manufacture agreement.

## 6. Remove unsupported SLA

Repository-wide searches of UI, backend, scripts, API and documentation found
no rule/config source for a 45-day SLA. Removed the claim from initial and dynamic
dossier text and the technical modal. Delay-card state now uses the explicit
top-level or nested pipeline flag instead of a UI-invented day cutoff. This does
not complete the separate multi-signal badge fix (#3).

## 7. Prototype review actions

The dossier's assignment, escalation, freeze, verification, BoQ and clearance
handlers only wrote browser storage/notes and displayed toasts; they had no
backend integration. Reworded enforcement buttons as review suggestions and
disabled the six controls with a visible prototype notice and tooltips. Removed
the simulated action writes; direct handler calls now only explain unavailability.
Legacy saved action badges in the dossier/workbench are labeled local demos;
global stub toasts no longer claim approval, escalation or audit orders occurred.
Existing user notes are preserved. No backend or model changes were needed.

Quick verification for fixes 6–7: JavaScript syntax checks, root/screens equality,
explicit delay flag versus elapsed-day checks, disabled button checks and direct
prototype-handler checks (no storage/API calls). Full browser layout and backend
integration tests remain pending.
