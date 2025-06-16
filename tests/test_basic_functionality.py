"""
Basic functionality test without requiring Google Cloud setup
"""
import tempfile
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from src.fact_check_agent.document_processor import DocumentProcessor
        print("  ✅ DocumentProcessor imported successfully")
    except Exception as e:
        print(f"  ❌ DocumentProcessor import failed: {e}")
        return False
    
    try:
        from src.fact_check_agent.claim_extractor import ClaimExtractor
        print("  ✅ ClaimExtractor imported successfully")
    except Exception as e:
        print(f"  ❌ ClaimExtractor import failed: {e}")
        return False
    
    try:
        from src.fact_check_agent.authenticity_scorer import AuthenticityScorer
        print("  ✅ AuthenticityScorer imported successfully")
    except Exception as e:
        print(f"  ❌ AuthenticityScorer import failed: {e}")
        return False
    
    return True

def test_document_processing():
    """Test basic document processing without Google Cloud"""
    print("\n📄 Testing document processing...")
    
    try:
        from src.fact_check_agent.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Test with a simple text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document. According to NASA, Earth orbits the Sun.")
            temp_path = f.name
        
        try:
            result = processor.process_document(temp_path)
            
            if result['success']:
                print(f"  ✅ Text processing successful: {result['word_count']} words extracted")
                print(f"  📝 Content preview: {result['text'][:50]}...")
                return True
            else:
                print(f"  ❌ Text processing failed")
                return False
                
        finally:
            Path(temp_path).unlink()
            
    except Exception as e:
        print(f"  ❌ Document processing test failed: {e}")
        return False

def test_claim_extraction():
    """Test claim extraction functionality"""
    print("\n🔍 Testing claim extraction...")
    
    try:
        from src.fact_check_agent.claim_extractor import ClaimExtractor
        extractor = ClaimExtractor()
        
        test_text = """
        According to the World Health Organization, handwashing can reduce 
        respiratory infections by up to 16%. NASA confirms that Earth's 
        average temperature has risen by 1.1°C since the late 19th century.
        The CDC reports that vaccines are 95% effective at preventing severe illness.
        """
        
        claims = extractor.extract_claims(test_text)
        
        if claims:
            print(f"  ✅ Claim extraction successful: {len(claims)} claims found")
            for i, claim in enumerate(claims[:2], 1):
                print(f"  📝 Claim {i}: {claim.text[:60]}...")
                print(f"     Type: {claim.claim_type.value}, Confidence: {claim.confidence:.2f}")
            return True
        else:
            print(f"  ❌ No claims extracted")
            return False
            
    except Exception as e:
        print(f"  ❌ Claim extraction test failed: {e}")
        return False

def test_authenticity_scorer():
    """Test authenticity scoring functionality"""
    print("\n⭐ Testing authenticity scoring...")
    
    try:
        from src.fact_check_agent.authenticity_scorer import AuthenticityScorer
        scorer = AuthenticityScorer()
        
        # Mock data for testing
        sources = [
            {
                'domain': 'cdc.gov',
                'url': 'https://cdc.gov/test',
                'credibility_score': 0.95,
                'publication_date': '2023-01-01T00:00:00Z'
            }
        ]
        
        evidence = [
            {
                'text': 'CDC confirms vaccine effectiveness',
                'source_credibility': 0.95,
                'relevance_score': 0.8
            }
        ]
        
        result = scorer.calculate_authenticity_score(
            claim_text="Vaccines are effective",
            claim_type="medical",
            sources=sources,
            evidence=evidence,
            contradictions=[]
        )
        
        print(f"  ✅ Authenticity scoring successful")
        print(f"  📊 Score: {result.final_score:.2f}")
        print(f"  🏷️  Level: {result.authenticity_level.value}")
        print(f"  📝 Explanation: {result.explanation[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Authenticity scoring test failed: {e}")
        return False

def test_supported_formats():
    """Test supported format information"""
    print("\n📋 Testing supported formats...")
    
    try:
        from src.fact_check_agent.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        formats_info = processor.get_supported_formats_info()
        
        print(f"  ✅ Format info retrieved successfully")
        print(f"  📄 Document formats: {len(formats_info['documents'])} types")
        print(f"  🖼️  Image formats: {len(formats_info['images'])} types")
        print(f"  📊 Office formats: {len(formats_info.get('presentations', []) + formats_info.get('spreadsheets', []))} types")
        
        # Show some examples
        all_formats = []
        for category, formats in formats_info.items():
            all_formats.extend(formats)
        
        print(f"  🎯 Total supported formats: {len(all_formats)}")
        print(f"  📝 Examples: {', '.join(all_formats[:10])}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Supported formats test failed: {e}")
        return False

def main():
    """Run basic functionality tests"""
    print("🚀 Fact Check Agent - Basic Functionality Tests")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Document Processing", test_document_processing), 
        ("Claim Extraction", test_claim_extraction),
        ("Authenticity Scoring", test_authenticity_scorer),
        ("Supported Formats", test_supported_formats)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test_name} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic functionality tests passed!")
        print("\n💡 Next steps:")
        print("  1. Set up Google Cloud credentials in .env")
        print("  2. Configure API keys for fact-checking sources")
        print("  3. Run full agent tests with: python test_agent.py")
        print("  4. Test extended formats with: python test_extended_formats.py")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    main()