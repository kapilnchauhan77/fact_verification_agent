#!/usr/bin/env python3
"""
Quick test of improved scraping capabilities
"""
import asyncio
import logging
from src.fact_check_agent.fact_checker import FactChecker
from src.fact_check_agent.claim_extractor import ClaimExtractor

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)

async def test_quick():
    """Quick test with simple claim"""
    
    print("⚡ Quick Test of Improved Scraping")
    print("=" * 40)
    
    extractor = ClaimExtractor()
    fact_checker = FactChecker()
    
    # Limit to fewer sources for quick test
    fact_checker.max_urls = 10
    
    # Simple factual claim
    text = "Apple's stock price increased 15% in 2023"
    
    print(f"📝 Claim: {text}")
    
    claims = extractor.extract_claims(text)
    print(f"🎯 Extracted {len(claims)} claims")
    
    if claims:
        print(f"📊 Fact-checking with max {fact_checker.max_urls} URLs...")
        
        results = await fact_checker.fact_check_claims(claims)
        
        for result in results:
            print(f"✅ Status: {result.verification_status}")
            print(f"📈 Score: {result.authenticity_score:.2f}")
            print(f"🔗 Sources checked: {len(result.sources_checked)}")
            print(f"⏱️  Time: {result.processing_time:.1f}s")
            
            if result.error_message:
                print(f"❌ Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(test_quick())