"""
Configuration settings for the Fact Check Agent
"""
import os
from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class FactCheckConfig(BaseSettings):
    """Configuration for the fact check agent"""
    
    # Google Cloud Configuration
    google_cloud_project: str = Field(..., env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: str = Field(..., env="GOOGLE_APPLICATION_CREDENTIALS")
    vertex_ai_location: str = Field(default="us-central1", env="VERTEX_AI_LOCATION")
    vertex_ai_model: str = Field(default="gemini-2.0-flash", env="VERTEX_AI_MODEL")
    
    # Search APIs
    serp_api_key: str = Field(default="", env="SERP_API_KEY")
    google_search_api_key: str = Field(default="", env="GOOGLE_SEARCH_API_KEY")
    google_search_engine_id: str = Field(default="", env="GOOGLE_SEARCH_ENGINE_ID")
    
    # GCP Search JSON API (alternative to Google Custom Search)
    gcp_search_api_key: str = Field(default="", env="GCP_SEARCH_API_KEY")
    gcp_search_engine_id: str = Field(default="", env="GCP_SEARCH_ENGINE_ID")
    
    # Fact-Check Sources
    reuters_api_key: str = Field(default="", env="REUTERS_API_KEY")
    ap_news_api_key: str = Field(default="", env="AP_NEWS_API_KEY")
    bbc_news_api_key: str = Field(default="", env="BBC_NEWS_API_KEY")
    factcheck_org_api_key: str = Field(default="", env="FACTCHECK_ORG_API_KEY")
    snopes_api_key: str = Field(default="", env="SNOPES_API_KEY")
    
    # Document Processing
    ocr_language: str = Field(default="eng", env="OCR_LANGUAGE")
    max_document_size_mb: int = Field(default=50, env="MAX_DOCUMENT_SIZE_MB")
    supported_formats: List[str] = Field(default=[
        # Images
        "jpg", "jpeg", "png", "tiff", "bmp", "gif", "webp",
        # PDF
        "pdf",
        # Microsoft Office
        "docx", "doc", "pptx", "ppt", "xlsx", "xls",
        # OpenOffice/LibreOffice
        "odt", "ods", "odp", "odg",
        # Text formats
        "txt", "rtf", "md", "html", "htm", "xml",
        # E-books
        "epub", "mobi",
        # Email
        "msg", "eml",
        # Archives
        "zip", "7z", "rar",
        # Audio/Video (for transcription)
        "mp3", "wav", "mp4", "avi", "mov"
    ])
    
    # Scoring Configuration
    min_authenticity_score: float = Field(default=0.0, env="MIN_AUTHENTICITY_SCORE")
    max_authenticity_score: float = Field(default=1.0, env="MAX_AUTHENTICITY_SCORE")
    confidence_threshold: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    
    # Application Configuration
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Source configuration for different types of claims
FACT_CHECK_SOURCES = {
    "political": [
        "politifact.com",
        "factcheck.org",
        "snopes.com",
        "reuters.com/fact-check",
        "apnews.com/hub/ap-fact-check"
    ],
    "medical": [
        "who.int",
        "cdc.gov",
        "nih.gov",
        "mayoclinic.org",
        "webmd.com",
        "healthline.com"
    ],
    "scientific": [
        "nature.com",
        "science.org",
        "ncbi.nlm.nih.gov",
        "scholar.google.com",
        "researchgate.net"
    ],
    "financial": [
        "sec.gov",
        "federalreserve.gov",
        "bloomberg.com",
        "reuters.com",
        "wsj.com",
        "ft.com"
    ],
    "technology": [
        "ieee.org",
        "techcrunch.com",
        "arstechnica.com",
        "wired.com",
        "theverge.com"
    ],
    "general": [
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "npr.org",
        "pbs.org"
    ]
}

# Authenticity scoring weights
SCORING_WEIGHTS = {
    "source_credibility": 0.3,
    "cross_reference_consistency": 0.25,
    "evidence_quality": 0.2,
    "publication_date_relevance": 0.1,
    "expert_consensus": 0.15
}

# Initialize global config
config = FactCheckConfig()