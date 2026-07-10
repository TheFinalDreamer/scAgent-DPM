"""Tests for report generation."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporting.markdown_report import generate_markdown_report
from src.reporting.html_report import generate_html_report


def test_generate_markdown_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        results = {
            "annotation": {"method": "celltypist", "is_fallback": True},
            "dynamics": {"method": "pseudotime", "is_fallback": False},
        }
        path = generate_markdown_report(results, tmpdir)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "scAgent-DPM" in content
        assert "FALLBACK" in content


def test_generate_html_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        results = {
            "annotation": {"method": "celltypist", "is_fallback": False},
        }
        path = generate_html_report(results, tmpdir)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "scAgent-DPM" in content
        assert "<html" in content


def test_fallback_warning_in_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Results with fallback should include warning
        results = {"annotation": {"method": "scgpt", "is_fallback": True}}
        path = generate_markdown_report(results, tmpdir)
        content = path.read_text(encoding="utf-8")
        assert "FALLBACK" in content
        assert "NOT for publication" in content
