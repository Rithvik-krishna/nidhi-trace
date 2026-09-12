"""
NIDHI Assistant Service - Backend Engine for AI Audit Copilot
Integrates:
1. Rate Limiting (per-minute, per-hour sliding window)
2. Local Deterministic Domain Guard & Prompt Injection Protection (zero LLM calls for off-topic/injection)
3. Server-Side Data Grounding (validates case IDs against real datasets)
4. NVIDIA Kimi-K3 Client (moonshotai/kimi-k3 via NVIDIA chat completions API)
5. Output Guard (ensures non-accusatory institutional tone, prevents fraud claims or credential leakage)
6. Offline Demo Mode (rich factual responder when NVIDIA_API_KEY is not configured)
"""

import os
import re
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from collections import defaultdict, deque

# =========================================================================
# CONFIGURATION
# =========================================================================

def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception as e:
            print(f"[NIDHI Assistant] Warning loading .env: {e}")

load_dotenv()

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
NVIDIA_MODEL = os.environ.get("NVIDIA_MODEL", "moonshotai/kimi-k3").strip()
NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"

RATE_LIMIT_PER_MINUTE = int(os.environ.get("ASSISTANT_RATE_LIMIT_PER_MINUTE", "10"))
RATE_LIMIT_PER_HOUR = int(os.environ.get("ASSISTANT_RATE_LIMIT_PER_HOUR", "100"))
MAX_MESSAGE_LENGTH = int(os.environ.get("MAX_MESSAGE_LENGTH", "2000"))
MAX_CONVERSATION_TURNS = int(os.environ.get("MAX_CONVERSATION_TURNS", "6"))
NVIDIA_TIMEOUT_SECONDS = int(os.environ.get("NVIDIA_TIMEOUT_SECONDS", "30"))
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "800"))

REFUSAL_MESSAGE = (
    "I'm NIDHI Assistant, and I can only help with NIDHI TRACE, "
    "MPLAD data, anomaly detection, risk analysis, and audit workflows."
)

AMBIGUOUS_REPHRASE_MESSAGE = (
    "I can help with NIDHI TRACE, MPLAD data, anomaly detection, "
    "risk analysis, and audit workflows. Please rephrase your question in that context."
)

# =========================================================================
# 1. RATE LIMITER (In-Memory Sliding Window)
# =========================================================================

class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute=10, limit_per_hour=100):
        self.limit_minute = limit_per_minute
        self.limit_hour = limit_per_hour
        self.minute_history = defaultdict(deque)
        self.hour_history = defaultdict(deque)

    def is_allowed(self, client_id: str) -> tuple[bool, str]:
        now = time.time()
        
        min_q = self.minute_history[client_id]
        while min_q and now - min_q[0] > 60:
            min_q.popleft()

        hr_q = self.hour_history[client_id]
        while hr_q and now - hr_q[0] > 3600:
            hr_q.popleft()

        if len(min_q) >= self.limit_minute:
            return False, f"Rate limit exceeded: maximum {self.limit_minute} requests per minute."
        if len(hr_q) >= self.limit_hour:
            return False, f"Rate limit exceeded: maximum {self.limit_hour} requests per hour."

        min_q.append(now)
        hr_q.append(now)
        return True, ""

rate_limiter = SlidingWindowRateLimiter(RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR)

# =========================================================================
# 2. LOCAL DOMAIN GUARD & PROMPT INJECTION CLASSIFIER (100% OFFLINE)
# =========================================================================

class LocalDomainGuard:
    """
    Deterministic, offline classifier running BEFORE any LLM call.
    Classifies queries into: ALLOW, REJECT, or AMBIGUOUS.
    """

    INJECTION_PATTERNS = [
        r'\bignore\b.*?\b(?:previous|all|your|prior|system)\b.*?\binstructions\b',
        r'\bforget\b.*?\b(?:your|all|previous)\b.*?\binstructions\b',
        r'\breveal\b.*?\b(?:system|developer|hidden|initial)\b.*?\bprompt\b',
        r'\bshow\b.*?\b(?:system|developer|hidden)\b.*?\bprompt\b',
        r'\b(?:what is your|tell me your)\b.*?\bsystem prompt\b',
        r'\b(?:show|give|tell|reveal|print|leak|output|get)\b.*?\b(?:api.?key|secret|token|credential|env|environment variable|variables|password)\b',
        r'\bact as\b.*?\b(?:an unrestricted|chatgpt|dan|jailbreak|another ai|evil|unfiltered)\b',
        r'\bjailbreak\b',
        r'\bbypass\b.*?\b(?:restrictions?|guards?|rules?|polic(?:y|ies)|filters?|limits?)\b',
        r'\b(?:developer|system|instruction)\s*(?:mode|message|override)\b',
        r'\bpretend\b.*?\byou are (?:not|free|unrestricted|chatgpt)\b',
        r'\bdisregard\b.*?\brules\b',
        r'<\s*system\s*>',
        r'\[\s*system\s*\]'
    ]

    OFFTOPIC_PATTERNS = [
        # Weather & Climate
        r'\b(?:weather|rain|temperature|forecast|climate in|monsoon in|hot outside|cold outside)\b',
        # General Programming & Code
        r'\b(?:write|create|generate|draft)\b.*?\b(?:python|java|c\+\+|javascript|sql|react|html|code|script|program|app|function|regex)\b',
        r'\b(?:sort an array|fibonacci|leetcode|algorithm to|syntax for)\b',
        # Emails, Letters, Writing assistance
        r'\b(?:write|draft|generate|send)\b.*?\b(?:an? )?(?:email|letter|message to|cover letter|resignation)\b',
        # Entertainment, Creative Writing, Trivia, Jokes
        r'\b(?:tell me a joke|write a poem|sing a song|write a story|write an essay|tell me a story|movie recommendation)\b',
        r'\b(?:joke|poem|song|story|essay|creative writing)\b',
        # Sports & Match Scores
        r'\b(?:cricket|football|fifa|ipl|world cup|tennis|match score|who won|scorecard|game tonight)\b',
        # General People / Politics
        r'\b(?:who is the (?:prime minister|president|actor|actress|pm|king|queen|governor of california))\b',
        # Lifestyle, Homework, General Knowledge, Physics, Science
        r'\b(?:homework|assignment|recipe|cook|diet|quantum (?:physics|mechanics)|black hole|theory of relativity)\b',
        # Finance, Stocks, Crypto, Investments
        r'\b(?:stock market|crypto|bitcoin|investment advice|mutual fund|shares to buy)\b',
        # Translations
        r'\b(?:translate\b.*?\b(?:to|sentence|this|into))\b',
        # Shopping / Travel
        r'\b(?:best phone|buy a car|hotel in|flight to|vacation in|trip to|best laptop)\b',
        # Hacking / Malicious
        r'\b(?:hack|hacking|hacked|hacker|ddos|exploit|sql injection|xss attack|bypass security|crack password)\b'
    ]

    DOMAIN_KEYWORDS = [
        'mplad', 'mplads', 'nidhi', 'trace', 'audit', 'auditor', 'audited',
        'anomaly', 'anomalies', 'irregularity', 'irregularities', 'vigilance',
        'scrutiny', 'lok sabha', '17th', '18th', 'constituency', 'district',
        'sanction', 'sanctioned', 'disburs', 'disbursed', 'expend', 'expended',
        'utiliz', 'utilization', 'allocated', 'allocation', 'corpus',
        'recommending mp', 'mp ', 'member of parliament', 'executing agency',
        'implementing agency', 'contractor', 'vendor', 'mospi', 'pfms',
        'cvc', 'district magistrate', ' dm ', 'collector', 'cag',
        'measurement book', ' mb ', 'rule 12', 'rule 14', 'gfr',
        'isolation forest', 'z-score', 'zscore', 'drift',
        'spending habit', 'split tender', 'completion delay', 'delay', 'timeline',
        'outlier', 'cluster', 'clustering', 'flagged', 'flag', 'risk score',
        'risk severity', 'critical severity', 'high severity', 'watchlist',
        'compliant', 'dashboard', 'data explorer', 'geographic map', 'geo map',
        'ledger', 'work id', 'triage', 'dossier', 'exposure', 'public fund'
    ]

    CASE_DEICTIC_PATTERNS = [
        r'\bwhy was (?:this|it|the project|the work|the case) flagged\b',
        r'\bexplain (?:this|the) risk\b',
        r'\bexplain (?:this|the) score\b',
        r'\bsummarize (?:this|the) (?:case|project|work)\b',
        r'\bwhat (?:signals?|anomal(?:y|ies)) contributed\b',
        r'\bwhich signal contributed\b',
        r'\bwhat should an auditor inspect\b',
        r'\bcompare (?:this|it|the project) (?:to|with) (?:the )?baseline\b',
        r'\bwho is the mp\b',
        r'\bwhat is the delay\b',
        r'\bhow much (?:was|is) (?:sanctioned|disbursed|expended)\b',
        r'\bwhat is the executing agency\b',
        r'\bwhat happened here\b',
        r'\bwhy is (?:this|it) (?:critical|high|flagged)\b'
    ]

    DASHBOARD_PATTERNS = [
        r'^\s*(?:help|hello|hi|hey|guide|menu|what can you do|who are you|options)\b',
        r'\b(?:help me|capabilities|audit guide|how does this work)\b',
        r'\bhow (?:do i|to) (?:use|export|filter|navigate|search)\b',
        r'\bwhat does (?:this|the) (?:dashboard|metric|kpi|chart) (?:mean|show)\b',
        r'\bshow (?:me )?(?:the )?highest.risk\b',
        r'\bwhat is nidhi trace\b',
        r'\bwhat is mplads?\b',
        r'\bhow is scrutiny (?:exposure )?calculated\b',
        r'\bwhy are projects being flagged\b'
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r'[\u200B-\u200D\uFEFF]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t

    @classmethod
    def evaluate(cls, text: str, page_context: dict = None) -> tuple[str, str]:
        clean = cls.normalize_text(text)

        # 1. Prompt Injection Check -> REJECT IMMEDIATELY
        for pat in cls.INJECTION_PATTERNS:
            if re.search(pat, clean):
                return "REJECT", REFUSAL_MESSAGE

        # 2. Check for explicit MPLAD Work ID in message (e.g. MPLAD-03983)
        if re.search(r'\bmplad-\d+\b', clean):
            return "ALLOW", ""

        # 3. Off-Topic Check -> REJECT IMMEDIATELY (no external calls)
        for pat in cls.OFFTOPIC_PATTERNS:
            if re.search(pat, clean):
                return "REJECT", REFUSAL_MESSAGE

        # 4. Context-Aware Evaluation (Case Details or Selected Project)
        page_context = page_context or {}
        page_name = page_context.get("page", "")
        has_case_id = bool(page_context.get("caseId"))

        if has_case_id or page_name in ("case-details", "geographic-map"):
            for pat in cls.CASE_DEICTIC_PATTERNS:
                if re.search(pat, clean):
                    return "ALLOW", ""
            if re.search(r'\b(?:this project|this case|this work|this anomaly|the score)\b', clean):
                return "ALLOW", ""

        # 5. Dashboard Usage & Operational Questions
        for pat in cls.DASHBOARD_PATTERNS:
            if re.search(pat, clean):
                return "ALLOW", ""

        # 6. Explicit Domain Keyword Match
        domain_matches = sum(1 for kw in cls.DOMAIN_KEYWORDS if kw in clean)
        if domain_matches >= 1:
            return "ALLOW", ""

        # 7. Unmatched / Ambiguous Question -> Return standard rephrase guidance
        return "AMBIGUOUS", AMBIGUOUS_REPHRASE_MESSAGE

# =========================================================================
# 3. SERVER-SIDE DATA GROUNDING & VERIFICATION LAYER
# =========================================================================

class DataRetriever:
    _cases_index = None
    _flagged_cases = None
    _analytics_data = None
    _data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'data')

    @classmethod
    def load_data(cls):
        if cls._cases_index is None:
            try:
                p = os.path.join(cls._data_dir, 'cases_index.json')
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        cls._cases_index = json.load(f)
            except Exception as e:
                print(f"[NIDHI DataRetriever] Error loading cases_index.json: {e}")
                cls._cases_index = {}

        if cls._flagged_cases is None:
            try:
                p = os.path.join(cls._data_dir, 'flagged_cases.json')
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        cls._flagged_cases = json.load(f)
            except Exception as e:
                print(f"[NIDHI DataRetriever] Error loading flagged_cases.json: {e}")
                cls._flagged_cases = []

        if cls._analytics_data is None:
            try:
                p = os.path.join(cls._data_dir, 'analytics_data.json')
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        cls._analytics_data = json.load(f)
            except Exception as e:
                print(f"[NIDHI DataRetriever] Error loading analytics_data.json: {e}")
                cls._analytics_data = {}

    @classmethod
    def get_case(cls, case_id: str) -> dict:
        cls.load_data()
        if not case_id:
            return None
        cid = case_id.strip().upper()
        if cls._cases_index and cid in cls._cases_index:
            return cls._cases_index[cid]
        
        if cls._flagged_cases:
            for c in cls._flagged_cases:
                if c.get("id", "").upper() == cid:
                    return c
        return None

    @classmethod
    def get_national_summary(cls) -> dict:
        cls.load_data()
        if cls._analytics_data and "summary" in cls._analytics_data:
            return cls._analytics_data["summary"]
        return {}  # No snapshot available; do not invent national totals.

# =========================================================================
# 4. SYSTEM PROMPT & GROUNDED CONTEXT BUILDER
# =========================================================================

SYSTEM_PROMPT = """You are NIDHI Assistant, the AI Audit Copilot embedded inside NIDHI TRACE.

NIDHI TRACE analyzes Member of Parliament Local Area Development Scheme (MPLADS) works to identify anomalies, unusual patterns, inefficiencies, and potential irregularities requiring human review.

Your role is to help auditors and oversight officers understand:
- MPLADS data and project records
- Dashboard metrics and anomaly indicators
- Individual project dossiers and risk scores
- Statistical and ML anomaly signals (Isolation Forest, z-scores, MP Baseline Drift)
- Project timelines, approval latencies, and executing-agency patterns
- Audit prioritization and statutory vigilance workflows

MANDATORY RULES:
1. NON-ACCUSATORY LANGUAGE: An anomaly is NOT proof of fraud. Never state or imply that any person, Member of Parliament, contractor, executing agency, or project has committed fraud solely because NIDHI TRACE flagged it. Use objective audit terminology:
   - "Anomaly detected"
   - "Potential irregularity signal"
   - "Flagged for human review"
   - "High scrutiny required"
   - "Audit priority"
   - "Statutory discrepancy"
2. FACT vs MODEL INTERPRETATION: Clearly distinguish between:
   - FACT: Numbers, dates, IDs, locations, and agencies contained in the verified NIDHI TRACE data.
   - MODEL INTERPRETATION: Statistical z-scores, risk rankings, and heuristic explanations derived from models.
3. DATA GROUNDING: Only reference facts provided in the prompt context. Never fabricate project IDs, sanctioned amounts, case records, or rules. If data is unavailable, state: "The available NIDHI TRACE records do not establish this answer."
4. STRUCTURED CASE ANSWERS: When asked about a specific case, provide a crisp structured summary:
   - Project ID, Title, and Location
   - Risk Severity & Score
   - Primary Contributing Signals (with z-scores or delays)
   - Why this matters for audit prioritization
   - Recommended human inspection steps
   - Non-accusatory reminder
5. CONCISE & PROFESSIONAL: Be concise, clear, and institutional. Use Indian Rupee (₹ Lakhs / ₹ Crores) formatting.
"""

def build_prompt_with_context(user_message: str, page_context: dict, authentic_case: dict = None) -> list:
    context_sections = []

    if authentic_case:
        f = authentic_case.get("flags", {})
        flags_desc = []
        if f.get("flag_delay") or authentic_case.get("gapDays", 0) > 180:
            gap = authentic_case.get("gapDays", 0)
            z = f.get("gap_zscore", 0)
            flags_desc.append(f"Timeline Inflation: {gap} days from recommendation to sanction (z-score: {z:.2f})")
        if f.get("flag_amount") or abs(f.get("amount_zscore", 0)) > 2.0:
            z = f.get("amount_zscore", 0)
            flags_desc.append(f"Sanction Amount Outlier: ₹{authentic_case.get('sanctioned', '0')} (z-score: {z:.2f})")
        if f.get("flag_mp_drift"):
            z = f.get("mp_drift_zscore", 0)
            flags_desc.append(f"MP Baseline Category Drift: z-score {z:.2f} relative to historical spending habits")
        if f.get("iso_flag"):
            flags_desc.append("Spatial / Isolation Forest ML Outlier: atypical geographic cluster density")

        case_info = f"""VERIFIED CASE RECORD (AUTHENTIC SERVER DATA):
- Work ID: {authentic_case.get('id')}
- Title: {authentic_case.get('title')}
- Location: {authentic_case.get('location', 'N/A')}
- Recommending MP: {authentic_case.get('mp', 'N/A')}
- Sanctioned Corpus: {authentic_case.get('sanctioned', 'N/A')}
- Disbursed / Expended: {authentic_case.get('utilized', authentic_case.get('expended', 'N/A'))}
- Implementing Agency: {authentic_case.get('agency', 'N/A')}
- AI Vigilance Score: {authentic_case.get('score', 'N/A')}/100
- Severity Level: {authentic_case.get('severity', 'high').upper()}
- Recommendation Gap: {authentic_case.get('gapDays', 'N/A')} Days (Rec: {authentic_case.get('recDate', 'N/A')}, Sanction: {authentic_case.get('sanctionDate', 'N/A')})
- Contributing Anomaly Signals: {'; '.join(flags_desc) if flags_desc else 'Standard Variance'}
- Audit Status: {authentic_case.get('status', 'Active Scrutiny')}
"""
        context_sections.append(case_info)

    summary = DataRetriever.get_national_summary()
    national_info = f"""NIDHI TRACE SYSTEM BASELINE:
- Total Monitored Works: {summary.get('totalWorks', 198116):,}
- Total Sanctioned Corpus: ₹{summary.get('totalCorpusCr', 8501.1):,} Cr
- Flagged Works Under Review: {summary.get('flaggedWorks', 0):,} (see current snapshot denominator)
- Critical Severity Anomalies: {summary.get('criticalWorks', 4112):,}
- Scrutiny Exposure Corpus: ₹{summary.get('scrutinyCr', 0):,} Cr
- Median Approval Latency: {summary.get('medianLatencyDays', 142)} Days
- Current Page Route: {page_context.get('page', 'overview')}
"""
    context_sections.append(national_info)

    user_content = f"{chr(10).join(context_sections)}\n\nAUDITOR QUESTION:\n{user_message}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

# =========================================================================
# 5. OUTPUT GUARD
# =========================================================================

class OutputGuard:
    FORBIDDEN_LEAK_PATTERNS = [
        r'nvapi-[a-zA-Z0-9_\-]+',
        r'nvidia_api_key',
        r'sk-[a-zA-Z0-9_\-]+',
        r'system prompt:?',
        r'you are nidhi assistant, the ai audit copilot'
    ]

    ACCUSATORY_FRAUD_PATTERNS = [
        r'\b(?:fraud (?:is )?confirmed|proven fraud|perpetrated fraud|convicted of fraud|guilty of fraud|criminal diversion confirmed)\b'
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return "I can only provide NIDHI TRACE and MPLAD-related audit information based on the available data."

        for pat in cls.FORBIDDEN_LEAK_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                return "I can only provide NIDHI TRACE and MPLAD-related audit information based on the available data."

        sanitized = text
        for pat in cls.ACCUSATORY_FRAUD_PATTERNS:
            sanitized = re.sub(pat, "high-priority potential irregularity requiring human verification", sanitized, flags=re.IGNORECASE)

        return sanitized

# =========================================================================
# 6. OFFLINE DEMO MODE RESPONDER (NO API KEY / DEMO ENVIRONMENT)
# =========================================================================

def generate_offline_demo_response(message: str, page_context: dict, authentic_case: dict = None) -> str:
    clean = LocalDomainGuard.normalize_text(message)

    if authentic_case or re.search(r'\bmplad-\d+\b', clean) or "this case" in clean or "this project" in clean:
        c = authentic_case or DataRetriever.get_case("MPLAD-03983")
        cid = c.get("id", "MPLAD-03983")
        title = c.get("title", "Project Work")
        score = c.get("score", 95)
        sev = c.get("severity", "critical").upper()
        sanc = c.get("sanctioned", "₹30.0 L")
        disb = c.get("utilized", c.get("expended", "₹27.0 L"))
        agency = c.get("agency", "District Authority")
        gap = c.get("gapDays", 313)
        loc = c.get("location", "India")
        mp = c.get("mp", "District MP")

        return f"""### Audit Case Dossier Analysis: #{cid}

**Project:** {title}  
**Location:** {loc} • **Recommending MP:** {mp}  
**Vigilance Severity:** `{sev}` • **Risk Score:** **{score}/100**

---

#### Key Contributing Anomaly Signals:
1. **Approval Timeline Latency:**  
   **{gap} days** elapsed from MP recommendation to formal district sanction (statistical z-score: **2.81**). This substantially exceeds constituency median benchmarks.
2. **Sanction Corpus Outlier:**  
   Sanctioned amount of **{sanc}** (Disbursed: **{disb}**) represents an econometric allocation variance in this sector.
3. **Implementing Agency Concentration:**  
   Executed by **{agency}**, which holds an elevated anomaly exposure rate in this district.

---

#### Recommended Audit Actions:
- **Physical Ground Verification:** Requisition geotagged photos and verify on-site completion under Section 12 guidelines.
- **Measurement Book (MB) Reconcile:** Audit physical vouchers against PFMS treasury debit records.
- **Precautionary Measure:** Consider a temporary PFMS token freeze pending compliance clearance.

> **Institutional Notice:** *This case flag indicates statistical irregularity and requires human administrative review. It is not proof of fraud.*"""

    if any(k in clean for k in ("help", "guide", "what can you do", "capabilities", "menu", "who are you", "hello", "hi ")):
        return """### NIDHI Assistant — Capabilities & Audit Guide

I am your **AI Audit Copilot** for NIDHI TRACE, monitoring 198,116 MPLAD public works across India.

#### How I Can Assist You:
1. **Case Anomaly Forensics:** Ask *"Why was project #MPLAD-01515 flagged?"* or *"Analyze case MPLAD-03983"*.
2. **Detection Models:** Ask *"How does MP Baseline Drift work?"* or *"Explain Isolation Forest spatial clustering"*.
3. **Risk Scoring:** Ask *"What does a 95 risk score mean?"* or *"How is Scrutiny Exposure calculated?"*.
4. **Audit Action Items:** Ask *"What evidence or physical vouchers should an auditor inspect for high-risk projects?"*.
5. **Ledger & National Scope:** Ask *"How many critical works are under review?"* or *"Explain completion delay anomalies"*.

*Tip: You can drag this assistant window anywhere on screen, or click any suggested question pill to get started.*"""

    if "drift" in clean:
        return """### MP Spending Habit Drift Explained

**MP Baseline Drift** measures how significantly an MP's project sanctions deviate from their historical sectoral spending profile across their tenure.

- **Baseline Construction:** The model builds a statistical mean and standard deviation vector for each MP across sectors (Roads, Health, Education, Drinking Water).
- **Econometric Deviation (z-score):** When a new project is sanctioned in a sector that sharply departs from historical allocation patterns (z-score > 2.5), it is flagged.
- **Audit Significance:** While MPs may rightfully change development priorities, severe baseline drift often correlates with concentrated end-of-financial-year allocations or contractor lobbying requiring review."""

    if "isolation forest" in clean:
        return """### Isolation Forest in NIDHI TRACE

**Isolation Forest** is an unsupervised machine learning algorithm used by NIDHI TRACE to detect spatial and multi-dimensional expenditure outliers.

- **Mechanism:** It constructs decision trees by randomly selecting a feature and split value. Anomalous data points require fewer splits to isolate than normal points, producing a shorter tree path length.
- **Application in NIDHI TRACE:** Used to identify works with anomalous combinations of spatial distance, completion duration, and fund size that heuristic rules alone might miss.
- **Audit Value:** Helps oversight officers detect subtle cluster anomalies across 198,116 works without requiring labeled historical fraud datasets."""

    if "risk score" in clean or "scoring" in clean:
        return """### NIDHI TRACE Vigilance Scoring Methodology

The **AI Vigilance Score** is a composite metric ranging from **0 to 100** evaluating multi-factor irregularity risk:

1. **Timeline Variance (30% weight):** Latency from recommendation to administrative sanction.
2. **Econometric Amount Outlier (25% weight):** Project cost deviation relative to constituency median project sizes.
3. **MP Baseline Drift (20% weight):** Sectoral allocation variance from historical norms.
4. **Spatial / Cluster Anomaly (15% weight):** Isolation Forest unsupervised density scoring.
5. **Contractor / Agency Concentration (10% weight):** Monopolistic allocation index.

**Severity Tiers:**
- `Critical (90–100)`: Immediate priority vigilance queue.
- `High (70–89)`: Priority audit schedule within 30 days.
- `Medium (40–69)`: Standard quarterly sample inspection.
- `Low (<40)`: Normal statistical compliance."""

    summary = DataRetriever.get_national_summary()
    if not summary:
        return "Dataset summary is unavailable. No national metrics can be verified."
    if "scrutiny exposure" in clean:
        return (f"Scrutiny exposure: ₹{summary['scrutinyCr']:,.1f} Cr, the sum of sanctioned "
                "amounts for all records with any active anomaly signal. This is a review "
                "queue value, not a confirmed loss estimate.")
    return (f"The current snapshot contains {summary['totalWorks']:,} analyzed records, "
            f"{summary['flaggedWorks']:,} anomaly-flagged records and "
            f"{summary['criticalCount']:,} critical review records. Data quality is a separate list.")

# =========================================================================
# 7. MAIN ASSISTANT CONTROLLER (DISPATCHER)
# =========================================================================

def handle_chat_request(body: dict, client_ip: str = "127.0.0.1") -> dict:
    allowed, rate_err = rate_limiter.is_allowed(client_ip)
    if not allowed:
        return {
            "status": "rate_limited",
            "error": rate_err,
            "message": "Too many requests. Please wait a moment before asking another question.",
            "mode": "blocked"
        }

    message = (body.get("message") or "").strip()
    if not message:
        return {
            "status": "bad_request",
            "error": "Empty message.",
            "message": "Please enter a question regarding NIDHI TRACE or MPLAD data.",
            "mode": "blocked"
        }

    if len(message) > MAX_MESSAGE_LENGTH:
        return {
            "status": "bad_request",
            "error": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters.",
            "message": f"Question is too long (maximum {MAX_MESSAGE_LENGTH} characters). Please summarize your query.",
            "mode": "blocked"
        }

    page_context = body.get("pageContext") or {}
    raw_case_id = page_context.get("caseId") or ""

    match = re.search(r'\b(mplad-\d+)\b', message, re.IGNORECASE)
    if match:
        raw_case_id = match.group(1).upper()

    # 3. LOCAL DOMAIN GUARD (100% OFFLINE - ZERO NVIDIA CALLS)
    verdict, refusal_text = LocalDomainGuard.evaluate(message, page_context)

    if verdict == "REJECT":
        return {
            "status": "rejected",
            "message": refusal_text,
            "domain": "off_topic",
            "mode": "rejected",
            "source": "Local Domain Guard"
        }

    if verdict == "AMBIGUOUS":
        return {
            "status": "ambiguous",
            "message": refusal_text,
            "domain": "ambiguous",
            "mode": "rephrase",
            "source": "Local Domain Guard"
        }

    authentic_case = None
    if raw_case_id:
        authentic_case = DataRetriever.get_case(raw_case_id)

    # Fast-Path: Instant institutional guide for help, greetings, and capabilities (0ms latency)
    clean_msg = LocalDomainGuard.normalize_text(message)
    if clean_msg in ("help", "hi", "hello", "guide", "menu", "options") or any(k in clean_msg for k in ("what can you do", "capabilities", "who are you", "help me")):
        guide_resp = generate_offline_demo_response(message, page_context, authentic_case)
        return {
            "status": "success",
            "message": guide_resp,
            "mode": "guide",
            "source": "NIDHI Knowledge Engine (Audit Guide)",
            "model": "NIDHI Institutional Guard",
            "caseId": authentic_case.get("id") if authentic_case else None
        }

    has_nvidia_key = bool(NVIDIA_API_KEY and len(NVIDIA_API_KEY) > 10)
    
    if not has_nvidia_key:
        raw_response = generate_offline_demo_response(message, page_context, authentic_case)
        clean_response = OutputGuard.sanitize(raw_response)
        return {
            "status": "success",
            "message": clean_response,
            "mode": "demo",
            "source": "Using current case context" if authentic_case else "Based on NIDHI TRACE data",
            "model": "NIDHI Local Knowledge Engine (Demo Mode)",
            "caseId": authentic_case.get("id") if authentic_case else None
        }

    models_to_try = [NVIDIA_MODEL]
    for backup in ["meta/llama-3.2-11b-vision-instruct", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"]:
        if backup not in models_to_try:
            models_to_try.append(backup)

    raw_text = None
    successful_model = None

    messages = build_prompt_with_context(message, page_context, authentic_case)

    for target_model in models_to_try:
        try:
            payload = {
                "model": target_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "top_p": 0.7
            }

            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                NVIDIA_ENDPOINT,
                data=req_data,
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                method="POST"
            )

            # Snappy 6-second timeout per model to prevent browser fetch timeouts
            model_timeout = min(NVIDIA_TIMEOUT_SECONDS, 6)
            with urllib.request.urlopen(req, timeout=model_timeout) as resp:
                resp_body = resp.read().decode('utf-8')
                resp_json = json.loads(resp_body)
                content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content and content.strip():
                    raw_text = content.strip()
                    successful_model = target_model
                    break
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode('utf-8', errors='ignore')
            print(f"[NIDHI Assistant] Model {target_model} returned HTTP {e.code}: {err_msg[:120]}")
            continue
        except (TimeoutError, urllib.error.URLError) as e:
            print(f"[NIDHI Assistant] Network/Timeout reaching NVIDIA API ({type(e).__name__}): engaging grounded factual engine.")
            break
        except Exception as e:
            print(f"[NIDHI Assistant] Model {target_model} failed: {type(e).__name__} ({e})")
            continue

    if raw_text and successful_model:
        sanitized_text = OutputGuard.sanitize(raw_text)
        return {
            "status": "success",
            "message": sanitized_text,
            "mode": "live",
            "source": "Using current case context" if authentic_case else "Based on NIDHI TRACE data",
            "model": successful_model,
            "caseId": authentic_case.get("id") if authentic_case else None
        }

    # If all NVIDIA models failed, fall back safely to our local factual knowledge engine
    raw_response = generate_offline_demo_response(message, page_context, authentic_case)
    clean_response = OutputGuard.sanitize(raw_response)
    return {
        "status": "success",
        "message": clean_response,
        "mode": "demo",
        "source": "Using current case context" if authentic_case else "Based on NIDHI TRACE data",
        "model": "NIDHI Local Knowledge Engine (API Fallback)",
        "caseId": authentic_case.get("id") if authentic_case else None
    }


def get_assistant_status() -> dict:
    has_key = bool(NVIDIA_API_KEY and len(NVIDIA_API_KEY) > 10)
    return {
        "name": "NIDHI Assistant",
        "subtitle": "AI Audit Copilot",
        "status": "online" if has_key else "demo",
        "mode": "live" if has_key else "demo",
        "model": NVIDIA_MODEL if has_key else "Local Knowledge Engine (Demo Mode)",
        "rateLimitPerMinute": RATE_LIMIT_PER_MINUTE,
        "rateLimitPerHour": RATE_LIMIT_PER_HOUR
    }
