# Loom Video Technical Walkthrough Script (5–7 Minutes)

**Project**: NIDHI TRACE — AI-Powered Public Fund Intelligence Platform  
**Presenter**: Rithvik Krishna  
**Audience**: Technical Reviewers, Hackathon Evaluators, & Public Fund Auditors (MoSPI / CVC)  
**Live URL**: [https://nidhi-trace.vercel.app/](https://nidhi-trace.vercel.app/)  
**Repository**: [https://github.com/Rithvik-krishna/nidhi-trace](https://github.com/Rithvik-krishna/nidhi-trace)  
**Target Duration**: 5–7 Minutes  

---

### [0:00 – 0:50] Screen 1: Executive Audit Overview & Macro Intelligence (`Overview_Dashboard.html`)

> *"Hello everyone! My name is Rithvik Krishna, and welcome to the technical walkthrough of **NIDHI TRACE** — an AI-powered public fund intelligence and forensic anomaly detection platform designed for the Member of Parliament Local Area Development Scheme (MPLADS).
> 
> Under MPLADS, over ₹8,500 Crores of public capital is allocated across India’s 543 Parliamentary constituencies. Historically, audit oversight relied on slow, manual sampling. NIDHI TRACE brings automated, continuous macro surveillance to public finance.
> 
> Here on our Executive Overview, the system is actively monitoring **198,116 registered works** across 785 district nodes. Out of **171,890 algorithmically scanned works**, our multi-signal detection engine has flagged **23,329 works** requiring review, representing **₹1,661.7 Crores** in scrutiny exposure. Crucially, high-severity critical outliers are isolated to just **1,137 works** (0.7% of the total corpus), giving vigilance officers an immediate, prioritized triage surface rather than an overwhelming backlog."*

**On-Screen Actions**:
- **Show**: The dark institutional sidebar with live seed status (`198,116 Works`, `Robust z ≥ 3.5`, `23,329 Flagged Queue`).
- **Hover**: Over the 5 KPI summary cards at the top—highlighting **Total Registered (198,116)**, **Scanned (171,890 - 86.8%)**, and **Critical Outliers (1,137)**.
- **Point cursor to**: The blue **Key Operational Finding** banner highlighting that completion delay accounts for 52.7% of anomalies.
- **Scroll slightly**: Show the **AI Anomaly Detection Categories** progress bars on the left, the **Risk Severity Classification** 2×2 grid on the right, and the **Immediate Vigilance Queue** table at the bottom.
- **Click**: The **"Flagged Cases"** item in the left sidebar (or the *"Launch Triage Workbench"* button).

---

### [0:50 – 2:00] Screen 2: Flagged Cases Audit Workbench (`Flagged_Cases.html`)

> *"Now stepping into the auditor's daily operating environment: the **Flagged Cases Audit Workbench**.
> 
> Unlike typical prototypes that calculate arbitrary 'scores out of 100', NIDHI TRACE is strictly grounded in statistical anomalies and actionable severity levels. At the top, you see our immediate triage breakdown: **1,137 Critical outliers** ($z \ge 3.5$), **5,507 High**, and **17,761 Medium** priority works.
> 
> The filter bar allows auditors to slice data instantly across all 29 States and UTs, search by MP or project ID, or filter by specific anomaly vectors. 
> 
> In the table below, every record exposes its full administrative lineage: the project title, constituency, recommending MP, sanctioned versus utilized capital, implementing agency, and the exact mathematical trigger—for example, *Sanction Delay (603 days) & Amount Outlier ($z=4.6$)*. The currency numbers use tabular monospace formatting for zero-error scanning, and clicking any work immediately opens its deep forensic dossier."*

**On-Screen Actions**:
- **Point cursor to**: The sub-header badge strip showing `1,137 CRITICAL (z ≥ 3.5)`, `5,507 HIGH`, and `17,761 MEDIUM`.
- **Interact with Filters**:
  - Click into the **Search** input and type a state or MP name (e.g., *"Gujarat"* or *"Vadodara"*).
  - Click the **"Critical"** severity filter pill to demonstrate instant filtering of the table rows.
- **Highlight Table Details**:
  - Hover over the red `● CRITICAL` badge on work `#MPLAD-83983`.
  - Point to the **Primary Anomaly** column showing the exact latency days and statistical z-score (`z=4.6`).
  - Point to the right-aligned ₹ values (`₹1.00 Cr` sanctioned vs `₹83.5 L` utilized).
- **Click**: The **"Geographic Map"** tab in the sidebar.

---

### [2:00 – 3:15] Screen 3: Geospatial Risk Surveillance Map (`Geographic_Map.html`)

> *"Public fund irregularities are rarely uniform—they cluster regionally. In our **Geospatial Surveillance Map**, we have geocoded and mapped over **171,890 works** across India.
> 
> On the left, an analytical drawer provides high-level telemetry: 543 Parliamentary seats monitored, 350 active clusters, and ₹8,501 Crores in capital. Auditors can toggle jurisdictions by state or filter by anomaly category, such as completion delays, agency concentration, or UC date mismatches.
> 
> Across the canvas, cluster markers indicate anomaly concentration with dynamic pulsing rings denoting critical severity. 
> 
> When an auditor clicks on any hotspot—for example, this cluster in Odisha—a slide-in Project Detail card appears in the bottom-right corner. It immediately displays the sanctioned sum, days delayed (1,021 days), and provides a direct gateway to launch a ground inquiry or view the full dossier."*

**On-Screen Actions**:
- **Show Canvas**: Pan slightly across the map of India, pointing out the red, orange, and amber cluster circles with numerical work counts.
- **Left Drawer**:
  - Point to the **Jurisdiction Filter** dropdown and select a specific state (or keep *National Overview*).
  - Click the **Critical / High / Medium / Low** severity toggle buttons to show markers updating.
  - Point to the summary box: `171,890 Geocoded`, `23,329 Flagged Clusters`.
- **Click a Map Pin**:
  - Click on a red cluster pin in eastern India (Odisha/Bhubaneswar).
  - Notice the smooth camera focus and the slide-in card appearing at the bottom-right for `OP- Nirakarpur, Block - Tangi, Cold Drinking Water...` showing `Sanction Delay (1021 days)`.
- **Hover**: Over the **"View Audit Dossier"** button on the floating card.
- **Click**: The **"Analytics"** link in the left sidebar.

---

### [3:15 – 4:30] Screen 4: Forensic Econometric Analytics (`Analytics.html`)

> *"Next, we enter **Forensic Econometric Analytics**. This view reveals the macro-financial dynamics and temporal surges that file-by-file audits completely miss.
> 
> In the top badge strip, we monitor the total fund envelope: **₹8,501.1 Crores total corpus**, an overall **66.5% utilization rate**, and **₹1,661.7 Crores under active scrutiny**.
> 
> The dashboard presents four complementary models:
> 1. **Fund Allocation vs. Release vs. Actual Expenditure**: Tracks the quarterly capital deployment velocity across 2023 to 2026, pinpointing where pipeline bottlenecks occur.
> 2. **Monthly Flagged Cases Trend**: An anomaly surge detector. Notice the prominent spike in early 2025, which immediately alerts vigilance leadership to concentrated year-end sanctioning rushes.
> 3. **Inter-State Anomaly Exposure**: A comparative breakdown of top states by flagged rate percentage versus priority scrutiny share—showing Maharashtra, Uttar Pradesh, and West Bengal leading in scrutiny exposure.
> 4. **Anomaly Vector Donut**: Breaks down composition across Completion Delays, Cost Outliers, Isolation Forest spatial outliers, and MP spending drift."*

**On-Screen Actions**:
- **Point cursor to**: The top sub-header badges: `TOTAL CORPUS: ₹8,501.1 Cr`, `UTILIZATION: 66.5%`, `SCRUTINY: ₹1,661.7 Cr`.
- **Point to the cohort selector**: `17th & 18th Lok Sabha (2019–2024)`.
- **Top-Left Line Chart**: Hover over the quarterly curve points (e.g., `2024 Q1`) to show the interactive Chart.js tooltip displaying Allocated, Released, and Utilized figures.
- **Top-Right Area Chart**: Point out the red `2025 SURGES` badge and trace the spike curve in early 2025.
- **Bottom-Left Bar Chart**: Hover over Maharashtra's tall orange bar showing flagged exposure rate.
- **Bottom-Right Donut Chart**: Hover over the red "Completion Delay" segment to show percentage share.
- **Point to**: The **"Implementing Agency Risk Matrix"** tab at the top right to mention agency-level scrutiny.
- **Click**: The **"Data Explorer"** tab in the sidebar.

---

### [4:30 – 5:30] Screen 5: Central Project Ledger & Data Explorer (`Data_Explorer.html`)

> *"Finally, we have the **Central Project Ledger & Data Explorer** — the complete institutional ledger of all **198,116 works**.
> 
> In financial audit systems, speed and scan-density are critical. This screen is engineered with a single-row filter matrix: officers can filter by Sector (spanning Public Infrastructure, Education, Drinking Water, Roads & Bridges), State, Progress Status, or search by keyword.
> 
> Notice the layout density: clean 40px rows optimized for desktop viewports without unnecessary scrolling. Every row displays:
> - The unique MPLAD project identifier
> - Exact work description and tagged sector
> - Constituency, State, and Recommending MP
> - Sanctioned amount alongside Expended capital and Expenditure Percentage
> - The official Implementing Agency and verified execution milestone
> 
> An auditor can inspect the ledger, click **'Audit'** on any record, or click **'Export CSV'** in the top bar to pull structured audit evidence for official inquiry reports."*

**On-Screen Actions**:
- **Point cursor to**: The ledger header badge: `198,116 WORKS RECORDED`, `₹8,501.1 Cr ALLOCATED`.
- **Filter Row**:
  - Click the **"All Sectors (9)"** dropdown to show categories (*Public Infrastructure*, *Drinking Water*, *Education*, *Roads & Bridges*).
  - Click the **"All States (25)"** dropdown.
- **Scroll Table Rows**:
  - Point to column headers: `WORK ID`, `PROJECT DESCRIPTION`, `SECTOR`, `CONSTITUENCY / STATE`, `RECOMMENDING MP`, `SANCTIONED`, `EXPENDED`, `EXP %`, `IMPLEMENTING AGENCY`, `PROGRESS`.
  - Highlight the clean sector badges (e.g., blue *Public Infrastructure*, cyan *Drinking Water*, amber *Education & Schools*).
  - Highlight the green and yellow progress status tags (*Work Completed*, *Physical Inspection*).
- **Point cursor to**: The top-right **"Export CSV"** button and the bottom pagination bar (`Showing 1 - 16 of 1,000 scanned ledger works`).

---

### [5:30 – 6:15] Floating Copilot & Conclusion

> *"Across every screen, auditors also have access to the **NIDHI Assistant** — our AI audit copilot anchored in the bottom right. Connected directly to our indexed database, officers can ask plain-language questions like *'Show top delayed irrigation works in Maharashtra'* or *'Identify agencies with multiple cost outliers'*, receiving instant, citation-backed answers with zero hallucination.
> 
> To conclude: NIDHI TRACE bridges the gap between massive public datasets and proactive audit enforcement. By combining robust econometric statistics, machine-learning anomaly detection, and high-density institutional UX, it provides government comptrollers with a transparent, production-ready vigilance intelligence system.
> 
> Thank you for your time and consideration!"*

**On-Screen Actions**:
- **Point to / Click**: The circular dark-blue **NIDHI Assistant** floating button with star icons (`bottom: 76px; right: 24px`).
- **Show**: The assistant interface opening cleanly without blocking table controls or pagination.
- **Click**: Back to the **"Overview"** tab on the sidebar to return to the executive dashboard.
- **Conclude**: Leave the camera on the clean, full-screen Overview Dashboard with the institutional top bar and KPI strip.
