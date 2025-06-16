# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fact-checking agent built with Google's Agent Development Kit (ADK) that processes documents, extracts claims, and verifies them against authoritative sources. The system uses Google Cloud Vision for OCR, Vertex AI for language processing, and multiple APIs for fact-checking.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install spacy model (required)
python -m spacy download en_core_web_sm

# Minimal install for testing
pip install -r requirements-minimal.txt
```

### Running the Application
```bash
# Interactive mode (default)
python main.py

# Document analysis
python main.py --mode document --input document.pdf --output results.json

# Text fact-checking
python main.py --mode text --input "Your claim here"
```

### Testing
```bash
# Run all tests
pytest test_agent.py -v

# Run specific test modules
python test_agent.py
python test_basic_functionality.py
python test_working_functionality.py

# Run simple functionality test
python test_simple.py

# Sample usage demonstration
python sample_usage.py
```

## Architecture

The system follows a pipeline architecture:

1. **DocumentProcessor** - Handles OCR and text extraction from multiple formats (PDF, DOCX, images)
2. **ClaimExtractor** - Uses Google's Gemini AI to identify and classify factual claims from text
3. **FactChecker** - Searches multiple authoritative sources to verify claims
4. **AuthenticityScorer** - Provides weighted scoring based on 5 factors (source credibility, cross-reference consistency, evidence quality, publication date, expert consensus)
5. **FactCheckAgent** - Main orchestrator that combines all components and provides Google ADK integration

## Configuration

### Required Environment Variables
- `GOOGLE_CLOUD_PROJECT` - Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON
- `VERTEX_AI_LOCATION` - Vertex AI region (default: us-central1)

### Optional API Keys
- `SERP_API_KEY`, `GOOGLE_SEARCH_API_KEY` - For web search
- `REUTERS_API_KEY`, `AP_NEWS_API_KEY` - For news fact-checking
- Various other fact-checking source APIs

Configuration is handled through `config.py` using pydantic settings with automatic .env file loading.

## Key Components

- **config.py** - Centralized configuration with source credibility ratings and scoring weights
- **fact_check_agent.py** - Main agent class with Google ADK integration
- **document_processor.py** - Multi-format document processing with OCR fallbacks
- **claim_extractor.py** - Gemini AI-powered claim detection and classification
- **fact_checker.py** - Multi-source verification engine
- **authenticity_scorer.py** - Weighted authenticity scoring algorithm

## Development Notes

- The system supports 50+ document formats including PDFs, Office docs, images, emails, and archives
- Gemini AI performs intelligent claim extraction with entity recognition and type classification
- Claims are classified into domains: medical, political, scientific, financial, technology, general, statistical, historical
- Source credibility is pre-configured with tiers (Tier 1: 0.95-0.98, Tier 2: 0.85-0.94, etc.)
- All major functions are async for concurrent processing
- **Optimized Web Scraping**: Multi-method extraction, priority source ordering, 70% faster processing (0.3s delays), reduced 403 errors with 16 blocked domains, max 15 URLs for speed
- Testing uses pytest with async support

## Testing Strategy

Tests cover:
- Document processing across multiple formats
- Claim extraction and classification accuracy
- Multi-source fact-checking verification
- Authenticity scoring algorithm validation
- Google ADK integration functionality