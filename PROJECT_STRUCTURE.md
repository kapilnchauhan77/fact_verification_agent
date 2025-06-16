# Fact Check Agent - Project Structure

This document outlines the refactored project structure for better organization and maintainability.

## Directory Structure

```
fact_check_agent/
├── src/                          # Source code
│   └── fact_check_agent/         # Main package
│       ├── __init__.py           # Package initialization
│       ├── config.py             # Configuration management
│       ├── fact_check_agent.py   # Main agent class
│       ├── claim_extractor.py    # Claim extraction using Gemini
│       ├── fact_checker.py       # Multi-source fact verification
│       ├── authenticity_scorer.py # Authenticity scoring algorithms
│       ├── document_processor.py # Document processing and OCR
│       ├── report_generator.py   # Report generation
│       ├── security_manager.py   # Security and privacy management
│       ├── performance_monitor.py # Performance monitoring
│       ├── checkpoint_monitor.py # Checkpoint monitoring
│       ├── performance_cache.py  # Caching system
│       ├── enhanced_content_extractor.py # Enhanced content extraction
│       ├── advanced_evidence_analyzer.py # Advanced evidence analysis
│       ├── custom_scrapers.py    # Custom web scrapers
│       ├── intelligent_query_optimizer.py # Query optimization
│       ├── predictive_caching_system.py # ML-based caching
│       ├── ultra_optimized_fact_checker.py # Ultra-optimized implementation
│       └── optimized_fact_checker.py # Optimized implementation
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_agent.py            # Main agent tests
│   ├── test_basic_functionality.py # Basic functionality tests
│   ├── test_working_functionality.py # Working functionality tests
│   ├── test_extended_formats.py # Extended format tests
│   ├── test_fixes.py            # Critical fixes tests
│   ├── test_optimizations.py    # Optimization tests
│   ├── test_ultra_optimizations.py # Ultra-optimization tests
│   ├── test_checkpoint_monitoring.py # Checkpoint monitoring tests
│   ├── test_gemini_*.py         # Gemini integration tests
│   └── test_*.py                # Other specific tests
│
├── docs/                         # Documentation
│   ├── README.md                # Main documentation
│   ├── CLAUDE.md                # Claude Code instructions
│   ├── EXTENDED_FORMATS.md      # Extended format support
│   ├── CHECKPOINT_PERFORMANCE_REPORT.md # Performance analysis
│   ├── ADVANCED_OPTIMIZATIONS_SUMMARY.md # Optimization summary
│   ├── BOTTLENECK_FIXES_SUMMARY.md # Bottleneck fixes
│   ├── FINAL_OPTIMIZATIONS.md   # Final optimization report
│   └── SCRAPING_IMPROVEMENTS.md # Scraping improvements
│
├── examples/                     # Usage examples and demos
│   ├── __init__.py
│   ├── sample_usage.py          # Basic usage examples
│   ├── demo_chunked_extraction.py # Chunked extraction demo
│   ├── demo_checkpoint_report.py # Checkpoint reporting demo
│   ├── demo_optimized_results.py # Optimized results demo
│   └── optimized_usage_examples.py # Advanced usage examples
│
├── scripts/                      # Utility scripts
│   ├── __init__.py
│   ├── fix_imports.py           # Import fixing script
│   ├── integrate_optimizations.py # Optimization integration
│   └── performance_benchmark.py # Performance benchmarking
│
├── main.py                       # Main entry point
├── setup.py                      # Package setup configuration
├── requirements.txt              # Python dependencies
├── requirements-minimal.txt      # Minimal dependencies
├── PROJECT_STRUCTURE.md         # This file
└── mythic-lattice-455715-q1-7383343e4b12.json # Google Cloud credentials
```

## Key Components

### Core Modules (`src/fact_check_agent/`)

1. **fact_check_agent.py** - Main orchestrator class
2. **claim_extractor.py** - Extracts factual claims using Google Gemini
3. **fact_checker.py** - Multi-source fact verification with optimizations
4. **authenticity_scorer.py** - Advanced authenticity scoring algorithms
5. **document_processor.py** - Handles 50+ document formats with OCR
6. **config.py** - Centralized configuration management

### Optimization Modules

1. **ultra_optimized_fact_checker.py** - Ultra-fast implementation (4-7x faster)
2. **advanced_evidence_analyzer.py** - Semantic evidence analysis
3. **predictive_caching_system.py** - ML-based predictive caching
4. **custom_scrapers.py** - Domain-specific web scrapers
5. **intelligent_query_optimizer.py** - Claim-type specific optimization

### Testing (`tests/`)

- Comprehensive test suite covering all functionality
- Performance and benchmark tests
- Integration tests for end-to-end workflows
- Format-specific tests for document processing

### Documentation (`docs/`)

- Complete project documentation
- Performance analysis reports
- Optimization guides and summaries
- Format support documentation

### Examples (`examples/`)

- Usage demonstrations
- Performance optimization examples
- Advanced feature showcases
- Integration examples

## Import Structure

### For modules in `src/fact_check_agent/`:
```python
from .config import config
from .claim_extractor import ClaimExtractor
from .fact_checker import FactChecker
```

### For external scripts/tests:
```python
from src.fact_check_agent.config import config
from src.fact_check_agent.claim_extractor import ClaimExtractor
from src.fact_check_agent.fact_checker import FactChecker
```

### For main package usage:
```python
from fact_check_agent import FactCheckAgent, ClaimExtractor, FactChecker
```

## Installation

```bash
# Development installation
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# Production installation
pip install .
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_fixes.py

# Run with verbose output
python -m pytest tests/ -v
```

## Running Examples

```bash
# Basic usage
python examples/sample_usage.py

# Chunked extraction demo
python examples/demo_chunked_extraction.py

# Performance optimization demo
python examples/optimized_usage_examples.py
```

## Main Entry Points

```bash
# Command line usage
python main.py --mode document --input document.pdf --output results.json

# Interactive mode
python main.py

# Text fact-checking
python main.py --mode text --input "Your claim here"
```

## Development Workflow

1. **Source Code**: Edit files in `src/fact_check_agent/`
2. **Testing**: Add tests in `tests/`
3. **Documentation**: Update docs in `docs/`
4. **Examples**: Add examples in `examples/`
5. **Scripts**: Add utilities in `scripts/`

## Key Features

- ✅ Modular, well-organized codebase
- ✅ Proper Python packaging with setup.py
- ✅ Comprehensive test suite
- ✅ Clear import structure
- ✅ Documentation and examples
- ✅ Performance optimizations (4-7x faster)
- ✅ Support for 50+ document formats
- ✅ Advanced ML-based caching
- ✅ Multi-source fact verification
- ✅ Detailed authenticity scoring