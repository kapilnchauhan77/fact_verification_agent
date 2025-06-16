"""
Fact Check Agent - Core module

This module provides the main fact-checking functionality including:
- Document processing and OCR
- Claim extraction using Google AI
- Multi-source fact verification
- Authenticity scoring
- Report generation
"""

from .fact_check_agent import FactCheckAgent, get_fact_check_agent
from .claim_extractor import ClaimExtractor, Claim, ClaimType
from .fact_checker import FactChecker, FactCheckResult
from .authenticity_scorer import AuthenticityScorer, AuthenticityLevel
from .document_processor import DocumentProcessor
from .report_generator import ReportGenerator
from .config import config

__version__ = "1.0.0"
__all__ = [
    "FactCheckAgent",
    "get_fact_check_agent", 
    "ClaimExtractor",
    "Claim",
    "ClaimType",
    "FactChecker",
    "FactCheckResult",
    "AuthenticityScorer",
    "AuthenticityLevel",
    "DocumentProcessor",
    "ReportGenerator",
    "config"
]