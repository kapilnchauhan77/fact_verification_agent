#!/usr/bin/env python3
"""
Test the improved web scraping with progress tracking
"""
import asyncio
import logging
from src.fact_check_agent.fact_checker import FactChecker
from src.fact_check_agent.claim_extractor import ClaimExtractor

# Set up logging to see progress
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

async def test_improved_scraping():
    """Test the improved scraping with progress bars"""
    
    print("🔧 Testing Improved Web Scraping")
    print("=" * 50)
    
    # Initialize components
    extractor = ClaimExtractor()
    fact_checker = FactChecker()
    
    # Test claim that should find sources
    test_text = "According to the World Health Organization, vaccines are 95% effective at preventing severe illness."
    
    print(f"📝 Testing claim: {test_text}")
    print()
    
    # Extract claims
    print("🔍 Step 1: Extracting claims with Gemini...")
    claims = extractor.extract_claims(test_text)
    print(f"   Found {len(claims)} claims")
    print()
    
    if claims:
        # Fact-check with improved scraping
        print("📊 Step 2: Fact-checking with improved scraping...")
        print("   - Rate limited to 50 URLs max")
        print("   - Progress tracking enabled")
        print("   - Multiple extraction methods")
        print("   - Blocked domains filter applied")
        print()
        
        results = await fact_checker.fact_check_claims(claims)
        
        print("\n✅ Results:")
        print("-" * 30)
        
        for result in results:
            print(f"Claim: {result.claim.text[:80]}...")
            print(f"Status: {result.verification_status}")
            print(f"Score: {result.authenticity_score:.3f}")
            print(f"Sources: {len(result.sources_checked)}")
            print(f"Evidence: {len(result.evidence)}")
            print(f"Contradictions: {len(result.contradictions)}")
            print(f"Processing time: {result.processing_time:.2f}s")
            
            if result.error_message:
                print(f"Error: {result.error_message}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_improved_scraping())