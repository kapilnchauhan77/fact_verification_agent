#!/usr/bin/env python3
"""
Test script for Gemini-based claim extraction
"""
import asyncio
import logging
from src.fact_check_agent.claim_extractor import ClaimExtractor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_claim_extraction():
    """Test Gemini claim extraction with sample text"""
    
    # Sample text with various types of claims
    test_text = """
    According to the CDC, COVID-19 vaccines are 95% effective at preventing severe illness.
    The unemployment rate in the United States dropped to 3.4% in January 2023, the lowest in 50 years.
    Apple's iPhone 14 was released in September 2022 and costs $799.
    A new study published in Nature shows that regular exercise can reduce the risk of heart disease by 30%.
    President Biden signed the Infrastructure Investment and Jobs Act in November 2021, allocating $1.2 trillion for infrastructure projects.
    """
    
    try:
        # Initialize extractor
        logger.info("Initializing claim extractor...")
        extractor = ClaimExtractor()
        
        if not extractor.model:
            logger.error("Failed to initialize Gemini model")
            return
        
        # Extract claims
        logger.info("Extracting claims from test text...")
        claims = extractor.extract_claims(test_text)
        
        # Display results
        print(f"\n🔍 Found {len(claims)} claims:")
        print("=" * 60)
        
        for i, claim in enumerate(claims, 1):
            print(f"\nClaim {i}:")
            print(f"  Text: {claim.text}")
            print(f"  Type: {claim.claim_type.value}")
            print(f"  Confidence: {claim.confidence:.2f}")
            print(f"  Priority: {claim.priority}")
            print(f"  Entities: {[e.get('text', '') for e in claim.entities[:3]]}")
            print(f"  Keywords: {claim.keywords[:5]}")
            print(f"  Sources: {claim.sources_to_check[:3]}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_gemini_claim_extraction()