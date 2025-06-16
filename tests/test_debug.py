#!/usr/bin/env python3
"""
Debug test for the claim extraction issue
"""
import logging
from src.fact_check_agent.claim_extractor import ClaimExtractor

# Set up logging to see debug info
logging.basicConfig(level=logging.DEBUG)

def test_problematic_text():
    """Test with the text that was causing issues"""
    
    extractor = ClaimExtractor()
    
    # Test the exact text that was failing
    text = "trump loves eaeting macdonals"
    
    print(f"Testing text: '{text}'")
    print("=" * 50)
    
    claims = extractor.extract_claims(text)
    
    print(f"Found {len(claims)} claims")
    
    for i, claim in enumerate(claims, 1):
        print(f"Claim {i}: {claim.text}")
        print(f"  Type: {claim.claim_type.value}")
        print(f"  Confidence: {claim.confidence}")

if __name__ == "__main__":
    test_problematic_text()