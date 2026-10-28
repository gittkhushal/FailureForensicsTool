"""
Tests for smart input preprocessor, multi-provider abstraction, and forensics exporter.
"""

import pytest
from src.pipeline.smart_input import SmartInputPreprocessor, PRESET_TEMPLATES
from src.llm.provider import get_llm_provider, OllamaProvider, GeminiProvider, GroqProvider
from src.failure.report_exporter import ForensicsReportExporter
from src.models.trace_models import Trace, Span, TraceStatus, SpanStatus
from src.models.failure_models import Failure, FailureType


def test_smart_input_domain_detection():
    """Test domain detection heuristics."""
    clinical = SmartInputPreprocessor.detect_domain("Patient has severe headache and elevated blood pressure.")
    assert clinical == "clinical"

    financial = SmartInputPreprocessor.detect_domain("Quarterly GAAP revenue grew 24% with EBITDA margin expansion.")
    assert financial == "financial"

    security = SmartInputPreprocessor.detect_domain("Detected IAM role assume role anomaly in VPC flow logs.")
    assert security == "security"


def test_smart_input_auto_structure():
    """Test auto-structuring large text."""
    raw = "CLINICAL ADMISSION NOTE\nPatient presented with mild symptoms.\nVital signs normal."
    res = SmartInputPreprocessor.auto_structure(raw)
    assert res["domain"] == "clinical"
    assert "CLINICAL ADMISSION NOTE" in res["title"]
    assert res["word_count"] > 0
    assert not res["was_truncated"]


def test_preset_templates_exist():
    """Verify all 4 preset templates are non-empty and categorized."""
    assert len(PRESET_TEMPLATES) == 4
    for name, data in PRESET_TEMPLATES.items():
        assert "text" in data
        assert len(data["text"]) > 100
        assert "domain" in data


def test_file_parsing():
    """Test parsing uploaded bytes."""
    txt_bytes = b"Hello world test log"
    assert SmartInputPreprocessor.parse_uploaded_file(txt_bytes, "test.txt") == "Hello world test log"

    json_bytes = b'{"status": "ok"}'
    parsed_json = SmartInputPreprocessor.parse_uploaded_file(json_bytes, "data.json")
    assert '"status": "ok"' in parsed_json


def test_llm_provider_factory():
    """Test provider factory instantiates correct providers."""
    ollama_p = get_llm_provider("ollama")
    assert isinstance(ollama_p, OllamaProvider)

    gemini_p = get_llm_provider("gemini", api_key="dummy_key")
    assert isinstance(gemini_p, GeminiProvider)
    assert gemini_p.is_available() is True

    groq_p = get_llm_provider("groq", api_key="dummy_groq_key")
    assert isinstance(groq_p, GroqProvider)
    assert groq_p.is_available() is True


def test_report_exporter():
    """Test markdown report generation."""
    trace = Trace(
        trace_id="t12345678",
        pipeline_name="test_pipeline",
        status=TraceStatus.SUCCESS,
        total_latency_ms=150.0,
        final_score=0.92,
        spans=[
            Span(
                span_id="s1",
                trace_id="t12345678",
                step_name="intake",
                step_index=0,
                status=SpanStatus.SUCCESS,
                latency_ms=20.0,
                judge_score=0.95,
            )
        ]
    )
    report = ForensicsReportExporter.generate_markdown(trace)
    assert "# 🔍 Pipeline Forensics Investigation Report" in report
    assert "t12345678" in report
    assert "test_pipeline" in report
