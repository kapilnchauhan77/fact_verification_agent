# Fact Check Agent - Google ADK Implementation

A comprehensive fact-checking agent built using Google's Agent Development Kit (ADK) that analyzes documents, extracts claims, and verifies them against multiple authoritative sources with detailed authenticity scoring.

## 🚀 Features

### Document Processing
- **OCR Support**: Extract text from PDFs, DOCX, and images (JPG, PNG, TIFF)
- **Multi-format Processing**: Handles various document formats with fallback mechanisms
- **Google Cloud Vision Integration**: High-accuracy OCR with Tesseract fallback

### Claim Extraction & Classification
- **Intelligent Claim Detection**: Uses NLP to identify factual claims
- **Domain Classification**: Categorizes claims into medical, political, scientific, financial, technology, or general
- **Entity Recognition**: Extracts named entities and keywords
- **Priority Scoring**: Assigns priority levels to claims based on importance

### Multi-Source Fact-Checking
- **Authoritative Sources**: Checks against government, academic, and credible news sources
- **Source Credibility Scoring**: Each source has a credibility rating (0.0-1.0)
- **Cross-Reference Verification**: Compares findings across multiple sources
- **Contradiction Detection**: Identifies conflicting information

### Advanced Authenticity Scoring
- **Comprehensive Scoring**: 5-factor authenticity score (0.0-1.0)
  - Source credibility (30%)
  - Cross-reference consistency (25%)
  - Evidence quality (20%)
  - Publication date relevance (10%)
  - Expert consensus (15%)
- **Confidence Intervals**: Statistical confidence bounds
- **Detailed Explanations**: Human-readable scoring rationale

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Document       │    │  Claim           │    │  Fact           │
│  Processor      │───▶│  Extractor       │───▶│  Checker        │
│  (OCR/Text)     │    │  (NLP/Claims)    │    │  (Multi-Source) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│  Google ADK     │◀───│  Authenticity    │◀────────────┘
│  Agent          │    │  Scorer          │
│  (Interface)    │    │  (AI Analysis)   │
└─────────────────┘    └──────────────────┘
```

## 📦 Installation

1. **Clone and Setup**
```bash
cd /path/to/fact_check_agent
pip install -r requirements.txt
```

2. **Install spaCy Model**
```bash
python -m spacy download en_core_web_sm
```

3. **Setup Google Cloud**
```bash
# Set up authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## 🔧 Configuration

### Required Environment Variables
```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
VERTEX_AI_LOCATION=us-central1

# Search APIs (Optional but recommended)
SERP_API_KEY=your-serp-api-key
GOOGLE_SEARCH_API_KEY=your-google-search-api-key

# Fact-Check Sources (Optional)
REUTERS_API_KEY=your-reuters-api-key
AP_NEWS_API_KEY=your-ap-news-api-key
```

### Source Credibility Database
The agent includes a comprehensive database of source credibility ratings:

**Tier 1 (0.95-0.98)**: WHO, CDC, NIH, Nature, Science, Reuters, AP News
**Tier 2 (0.85-0.94)**: BBC, NPR, FactCheck.org, PolitiFact
**Tier 3 (0.70-0.84)**: WebMD, Healthline, ArsTechnica

## 🎯 Usage

### Command Line Interface
```bash
# Analyze a document
python main.py --mode document --input document.pdf --output results.json

# Fact-check text
python main.py --mode text --input "Climate change has increased temperatures by 1.1°C"

# Interactive mode
python main.py --mode interactive
```

### Interactive Mode Commands
```
> doc /path/to/document.pdf    # Analyze document
> text Your claim here         # Fact-check text  
> chat How does scoring work?  # Chat with agent
> help                         # Show commands
> quit                         # Exit
```

### Python API
```python
from fact_check_agent import FactCheckAgent
import asyncio

async def main():
    agent = FactCheckAgent()
    
    # Analyze document
    result = await agent.analyze_document("document.pdf")
    print(f"Overall score: {result['summary']['overall_authenticity_score']}")
    
    # Fact-check text
    result = await agent.fact_check_text("Your claim here")
    for claim in result['results']:
        print(f"Claim: {claim['claim']}")
        print(f"Score: {claim['authenticity_score']:.2f}")

asyncio.run(main())
```

## 📊 Output Format

### Document Analysis Result
```json
{
  "success": true,
  "document_info": {
    "file_name": "document.pdf",
    "pages": 5,
    "processing_method": "ocr"
  },
  "summary": {
    "total_claims": 8,
    "verified_claims": 5,
    "disputed_claims": 1,
    "unverified_claims": 2,
    "overall_authenticity_score": 0.72,
    "overall_authenticity_level": "mostly_authentic",
    "recommendation": "Document is generally reliable with some verification needed"
  },
  "claims": [
    {
      "claim": {
        "text": "COVID-19 vaccines are 95% effective",
        "type": "medical",
        "confidence": 0.9,
        "priority": 1
      },
      "verification": {
        "status": "verified",
        "authenticity_score": 0.89,
        "authenticity_level": "verified",
        "confidence_interval": [0.79, 0.99],
        "explanation": "This claim is highly likely to be accurate. Verified by 3 high-credibility sources. Supported by 2 pieces of evidence."
      },
      "scoring_breakdown": {
        "source_credibility": 0.92,
        "cross_reference": 0.85,
        "evidence_quality": 0.88,
        "publication_date": 0.95,
        "expert_consensus": 0.90
      },
      "sources": [
        {
          "url": "https://cdc.gov/covid/vaccines",
          "domain": "cdc.gov",
          "credibility_score": 0.98,
          "relevance_score": 0.95
        }
      ],
      "evidence": [...],
      "contradictions": []
    }
  ]
}
```

### Authenticity Levels
- **Verified** (0.8-1.0): Highly reliable, safe to cite
- **Likely True** (0.6-0.8): Generally reliable, consider cross-checking
- **Uncertain** (0.4-0.6): Requires additional verification
- **Likely False** (0.2-0.4): Exercise caution, appears inaccurate
- **False** (0.0-0.2): Do not share, likely false or misleading

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest test_agent.py -v

# Integration test
python test_agent.py

# Test with sample document
python main.py --mode document --input sample_document.pdf
```

### Test Coverage
- Document processing (PDF, DOCX, images)
- Claim extraction and classification
- Multi-source fact-checking
- Authenticity scoring algorithms
- Google ADK integration

## 🔍 Supported Claim Types

1. **Medical**: Health, diseases, treatments, medical research
2. **Political**: Policies, elections, government actions
3. **Scientific**: Research findings, studies, academic claims
4. **Financial**: Economic data, market information, financial statistics
5. **Technology**: Tech developments, AI, digital innovations
6. **Statistical**: Numerical claims, percentages, data points
7. **Historical**: Past events, historical facts
8. **General**: Other factual claims

## 🌐 Fact-Check Sources

### Government & Official
- WHO, CDC, NIH, FDA
- SEC, Federal Reserve
- Government websites (.gov domains)

### Academic & Scientific
- Nature, Science, NCBI
- Peer-reviewed journals
- University research

### News & Media
- Reuters, AP News, BBC
- NPR, PBS
- Financial: Bloomberg, WSJ

### Fact-Checking Organizations
- FactCheck.org, PolitiFact
- Snopes, Full Fact
- Domain-specific fact-checkers

## 🚨 Limitations

1. **API Dependencies**: Requires active internet connection and API keys
2. **Language Support**: Currently optimized for English content
3. **Real-time Events**: May not capture very recent developments
4. **Context Sensitivity**: May miss nuanced or contextual claims
5. **Source Availability**: Limited by accessible source APIs

## 🔐 Security & Privacy

- No storage of processed documents
- API keys encrypted in environment
- Session-based processing
- GDPR-compliant data handling
- Configurable data retention policies

## 📈 Performance

- **Document Processing**: ~2-5 seconds per page
- **Claim Extraction**: ~1-3 seconds per 1000 words
- **Fact-Checking**: ~3-10 seconds per claim (depends on sources)
- **Concurrent Processing**: Up to 5 simultaneous fact-checks

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the [troubleshooting guide](#troubleshooting)
2. Review [API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk)
3. Submit issues via GitHub Issues

## 🔧 Troubleshooting

### Common Issues

**Authentication Error**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
gcloud auth application-default login
```

**Missing Dependencies**
```bash
pip install --upgrade -r requirements.txt
python -m spacy download en_core_web_sm
```

**OCR Failures**
- Ensure Tesseract is installed: `brew install tesseract` (macOS)
- Check image quality and resolution
- Verify supported file formats

**API Limits**
- Monitor API quotas in Google Cloud Console
- Implement rate limiting for high-volume usage
- Consider caching frequently checked claims

---

**Built with Google ADK** | **Powered by Vertex AI** | **Advanced NLP Pipeline**