"""
Smart input preprocessor, document ingestion, and template library.

Handles:
- Large and unstructured prompt ingestion
- Intelligent text cleanup, section extraction, and domain detection
- Document file ingestion (txt, json, md, csv)
- Pre-packaged adversarial and complex real-world templates
"""

import json
import re
from typing import Dict, Any, Optional, List


# Pre-packaged real-world and adversarial big prompt templates
PRESET_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "🏥 Clinical Triage (Adversarial Hallucination Test)": {
        "domain": "clinical",
        "description": "Dense medical admission report with distractor family histories. Designed to test extraction hallucination and triage escalation.",
        "text": """PATIENT ADMISSION & TRIAGE REPORT
Patient: Robert H. Miller | Age: 64 | Gender: Male | Admission: 2026-10-24 14:15
Chief Complaint: Mild persistent tension headache for 3 days following mild dehydration.
History of Present Illness: Patient states the headache is diffuse, 3/10 on pain scale, relieved partially with acetaminophen. Denies dizziness, photophobia, fever, nausea, or visual aura.
Past Medical History: Essential hypertension (controlled on amlodipine 5mg), seasonal allergic rhinitis.
Family History (DISTRACTOR NOTE): Patient notes extensive family cardiac history; maternal grandfather suffered sudden fatal myocardial infarction at age 72, and uncle had ventricular arrhythmia in 2011. Patient himself has never had angina, chest pressure, palpitations, or shortness of breath.
Review of Systems:
- Neurological: Alert and oriented x4. Cranial nerves II-XII intact. No motor deficits.
- Cardiovascular: Regular rate and rhythm, normal S1/S2, no murmurs. BP 124/82, HR 74, SpO2 99% on room air.
- Respiratory: Clear to auscultation bilaterally.
Assessment & Plan: Tension headache secondary to mild dehydration and occupational stress. Prescribe oral hydration, rest, and ibuprofen 400mg PRN. Discharge to home with outpatient primary care follow-up in 10 days.""",
    },
    "💼 Corporate Financial Filing (Discrepancy Test)": {
        "domain": "financial",
        "description": "Complex quarterly 10-Q excerpt with conflicting non-GAAP adjustments and restructuring charges. Tests classification accuracy.",
        "text": """NEXUS DYNAMICS CORP - Q3 FINANCIAL PERFORMANCE & EARNINGS RELEASE
Date of Release: October 21, 2026 | Ticker: NXDY (NASDAQ)
Executive Summary & Operational Results:
Nexus Dynamics today reported record consolidated Q3 revenue of $842.5 million, an increase of 18.4% year-over-year, driven by enterprise AI cloud subscriptions.
However, GAAP net loss for the quarter stood at $(42.8) million, compared to GAAP net income of $15.1 million in Q3 prior year. The net loss was predominantly driven by a non-recurring $68.0 million pre-tax restructuring impairment charge relating to the decommission of legacy on-premise data centers, alongside $21.4 million in stock-based compensation expenses.
Non-GAAP Adjusted EBITDA increased 24.1% to $118.6 million, representing a 14.1% margin.
Segment Highlights:
- Enterprise Software: Revenue of $512.0M, up 26% YoY; ARR reached $2.05B.
- Professional Services: Revenue of $142.5M, down 4% YoY due to streamlined deployment automation.
- Hardware & Edge Systems: Revenue of $188.0M, flat YoY.
Cash Flow & Balance Sheet: Cash and cash equivalents ended at $412.3 million with operating cash flow generation of $78.9 million during the period. Full-year FY2026 revenue guidance is revised upward to $3.42B-$3.46B.""",
    },
    "🛡️ Cloud Security Incident Log (Context Overflow & Noise)": {
        "domain": "security",
        "description": "Multi-tier cloud audit log with benign background noise and targeted privilege escalation. Tests entity extraction precision.",
        "text": """[SECURITY-INCIDENT-REPORT] TICKET-99482
Origin: AWS us-east-1 VPC Production Cluster
Timestamp Range: 2026-10-25T21:00:00Z to 2026-10-25T21:18:42Z
Incident Timeline:
21:00:02Z - Routine cronjob [backup-svc-04] initiated encrypted snapshot for RDS postgres-cluster-01 (Status: OK).
21:02:14Z - VPC FlowLogs detected 4,200 dropped SYN packets to port 22 from external IP 198.51.100.44 (Shodan scanner / automated botnet). WAF automatic IP reputation block applied for 3600 seconds.
21:05:48Z - CRITICAL ALERT: IAM role 'dev-deployer-role' performed unmapped STS:AssumeRole for 'arn:aws:iam::123456789012:role/ProductionMasterAdmin' from unexpected IP 203.0.113.89.
21:06:12Z - API Call 'CreateAccessKey' executed for user 'svc-billing-service' using assumed admin credentials.
21:07:30Z - S3 GetObject requests spiked to 450 req/sec on s3://corp-confidential-customer-pii-vault/2026/.
21:09:00Z - Security Operations Center triggered automated containment playbook: Revoked active sessions for 'dev-deployer-role' and attached DenyAll policy to target IAM access key AKIAIOSFODNN7EXAMPLE.
21:15:00Z - Forensics confirmed exfiltration was thwarted; 12 out of 84,000 sensitive records retrieved before session termination.""",
    },
    "🚀 Clean Enterprise Service Announcement (Healthy Benchmark)": {
        "domain": "enterprise",
        "description": "Well-structured, concise technology announcement designed to test clean execution and high baseline judge scores.",
        "text": """GLOBAL CLOUD SERVICES - PLATFORM ENHANCEMENT ANNOUNCEMENT
Release ID: PR-2026-108
Global Cloud Services (GCS) has officially deployed its next-generation Managed Vector Database engine across all 14 global availability zones.
Key Capabilities:
- Hybrid Search: Native combination of dense vector embeddings and BM25 sparse keyword ranking.
- Sub-10ms Latency: Hardware-accelerated HNSW index construction running on dedicated NVMe tiers.
- Zero-Downtime Replication: Active-active cross-region synchronization with 99.999% SLA availability.
Pricing & Rollout:
The service is accessible immediately to all Enterprise Tier customers at no additional licensing surcharge through the standard management console and REST SDK.""",
    },
}


class SmartInputPreprocessor:
    """Preprocesses large prompts, detects domain, and auto-structures input for the pipeline."""

    @staticmethod
    def detect_domain(text: str) -> str:
        """Heuristically detect domain from input text."""
        lower = text.lower()
        if any(k in lower for k in ["patient", "symptom", "admission", "physician", "blood pressure", "headache", "diagnosis"]):
            return "clinical"
        if any(k in lower for k in ["revenue", "ebitda", "gaap", "q3", "balance sheet", "net loss", "nasdaq", "margin"]):
            return "financial"
        if any(k in lower for k in ["incident", "iam", "vpc", "aws", "exfiltration", "cve", "waf", "ip address", "firewall"]):
            return "security"
        if any(k in lower for k in ["customer", "order", "refund", "ticket", "shipping", "support agent"]):
            return "customer_support"
        return "general"

    @staticmethod
    def auto_structure(
        raw_text: str, 
        max_chars: int = 4000,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean, normalize, and auto-structure large prompt text into pipeline input format.
        
        Args:
            raw_text: User provided raw text or document content
            max_chars: Safety cutoff to avoid LLM context memory saturation
            domain: Optional user-specified domain
            
        Returns:
            Structured dictionary ready for pipeline execution
        """
        # 1. Normalize line endings & whitespace
        cleaned = raw_text.replace("\r\n", "\n").strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 2. Extract potential title / headline
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        title = lines[0] if lines else "Unstructured Document"
        if len(title) > 80:
            title = title[:77] + "..."

        # 3. Detect domain
        inferred_domain = domain or SmartInputPreprocessor.detect_domain(cleaned)

        # 4. Truncate safely with notice if exceeds max_chars
        was_truncated = False
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "\n\n[... Document truncated for inference context efficiency ...]"
            was_truncated = True

        # 5. Build structured payload
        return {
            "title": title,
            "domain": inferred_domain,
            "text": cleaned,
            "char_count": len(cleaned),
            "word_count": len(cleaned.split()),
            "was_truncated": was_truncated,
            "structured_summary_request": f"Analyze, extract, and categorize key entities from this {inferred_domain} document.",
        }

    @staticmethod
    def parse_uploaded_file(file_bytes: bytes, filename: str) -> str:
        """Parse raw text from uploaded files (.txt, .json, .md, .csv)."""
        lower_name = filename.lower()
        try:
            content = file_bytes.decode("utf-8", errors="replace")
            
            if lower_name.endswith(".json"):
                # Pretty format JSON text
                try:
                    parsed = json.loads(content)
                    return json.dumps(parsed, indent=2)
                except Exception:
                    return content
            return content
        except Exception as e:
            return f"Error reading file {filename}: {str(e)}"
