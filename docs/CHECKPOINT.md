# Dashboard cleanup checkpoint — 2026-09-12

## Latest update — all 7 targeted fixes implemented

Fixes **1 through 7 are now fully implemented across separate focused commits** on branch `fix/dashboard-data-integrity`. No code was merged into or pushed directly to `main`.

1. `fd79155` — **Fix 1 (Retired Detector)**: Removed Benford / round-number detector from UI, exports, assistant references, and dashboard scoring.
2. `11960fb` — **Fix 2 (Queue & Disjoint Tiers)**: Reconciled queue (23,907 total union; 23,329 rule-only) and disjoint priority tiers (1,137 critical + 6,844 high + 15,926 medium = 23,907). Unique snapshot row IDs.
3. `d02182b` — **Fix 6 (45-Day SLA Removal)**: Removed unsupported 45-day SLA claims from dossier; drove delay presentation from explicit pipeline flag.
4. `1f33368` — **Fix 7 (Prototype Enforcement Actions)**: Disabled and reworded prototype administrative actions (freeze/assign/escalate) to review suggestions; removed misleading simulation toasts.
5. `3244a43` — **Fix 3 (Signal Count Badge & Dossier Normalization)**:
   - Integrated `assets/js/dossier-signals.js` across root and `screens/`.
   - Reconciled top-level (`dossier-signal-count-badge`) and card-header (`dossier-flag-count-badge`) to use identical explicit pipeline booleans.
   - Removed fuzzy suffix ID matching (`endsWith(numOnly)`) and eliminated fabricated missing-case fallback (replaced with clean `renderMissingCase` notice).
   - Preserved Data Quality booleans (`dq_flag`, `dq_stale_status`, `dq_implausible_amount`, `dq_possible_miscategorization`, `dq_reason`) in `backend/app/services/seeder.py`.
6. `0571288` — **Fix 4 (Inconsistent Percentage Denominators)**:
   - Reconciled "Key Operational Finding" with explicit denominators: 56.2% of 23,907 flagged anomaly works for delay, while 62,089 records (36.1% of 171,890 scanned) are separated into a Data Quality review list.
   - Reconciled static fallback HTML and dynamic synthesis script across `Overview_Dashboard.html`, `index.html`, and `screens/`.
   - Clarified Analytics donut chart subtitle and tooltips as shares of signal occurrences (33,094 occurrences across 23,907 cases).
7. `44ee3f8` — **Fix 5 (Chart Provenance & Transparent Labeling)**:
   - Labeled quarterly financial chart with prominent `ILLUSTRATIVE MODEL — NOT RECORDED PFMS DATA` badge and clarified that releases are modeled at 92% and expenditure estimated from reporting status.
   - Reframed "Monthly Flagged Cases Trend" to "Flagged Works by Sanction Month" with `SANCTION COHORTS (CRIT + HIGH)` badge, explicitly documenting that records are grouped by administrative sanction date, not detection time.
   - Synchronized narration in `loomscript.md` to remove misleading "live surge detector" claims.

---

## Verification completed

- **Dossier signal normalization & counting**:
  - `MPLAD-000007`: Verified genuine zero-signal case (`count = 0`, all booleans `false`).
  - `MPLAD-000217`: Verified single signal (`count = 1`, `flag_delay = true`).
  - `MPLAD-065456`: Verified two signals (`count = 2`, `flag_delay = true`, `flag_mp_drift = true`).
  - `MPLAD-003130`: Verified four signals (`count = 4`, `flag_amount`, `flag_mp_drift`, `flag_isolation_forest`, `dq_flag = true`).
  - `MPLAD-003975`: Verified five signals (`count = 5`, all flags triggered).
  - API-shaped records: Verified top-level booleans and DQ subflags count correctly.
  - Missing ID lookup: Verified `renderMissingCase` shows not-found state without inventing fake values.
- **Python compilation**:
  - `py_compile backend/app/services/seeder.py`: Passed cleanly (exit code 0).
- **File parity & mirrors**:
  - `Case_Details.html` <-> `screens/Case_Details.html`: 100% byte identical.
  - `Analytics.html` <-> `screens/Analytics.html`: 100% byte identical.
  - `Overview_Dashboard.html` <-> `index.html` <-> `screens/Overview_Dashboard.html` <-> `screens/index.html`: 100% byte identical.
  - `assets/js/dossier-signals.js` <-> `screens/assets/js/dossier-signals.js`: 100% byte identical.

---

## What remains untested

- Live browser DOM rendering and layout checks (Playwright/Puppeteer) on full viewports.
- Live HTTP backend integration tests against a freshly seeded SQLite test database.
- Browser responsiveness when loading the full 36 MB flagged cases JSON on low-end client devices.

---

## Git remote state and push

- Previous commits up to `1f33368` were confirmed already present on remote `origin/fix/dashboard-data-integrity`.
- New local commits ready to push:
  - `3244a43`: fix(dossier): reconcile signal-count badges with explicit pipeline booleans and eliminate fabricated fallbacks
  - `0571288`: fix(overview & analytics): reconcile percentage denominators and clarify signal occurrence shares
  - `44ee3f8`: fix(analytics): label modeled quarterly trajectory as illustrative and reframe monthly trend as sanction cohorts

To push using your PowerShell credentials:
```powershell
git push origin fix/dashboard-data-integrity
```
