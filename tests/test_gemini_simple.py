#!/usr/bin/env python3
"""
Simple test for Gemini claim extraction
"""
from src.fact_check_agent.claim_extractor import ClaimExtractor

def test_simple():
    extractor = ClaimExtractor()
    
    text = "According to WHO, vaccines are 95% effective. The stock market rose 10% last year."
    
    claims = extractor.extract_claims(text)
    
    print(f"✅ Successfully extracted {len(claims)} claims using Gemini:")
    for i, claim in enumerate(claims, 1):
        print(f"  {i}. {claim.text[:50]}... [{claim.claim_type.value}]")

if __name__ == "__main__":
    test_simple()