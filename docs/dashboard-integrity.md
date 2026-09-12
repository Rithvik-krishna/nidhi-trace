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
