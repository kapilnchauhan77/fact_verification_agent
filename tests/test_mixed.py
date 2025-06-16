#!/usr/bin/env python3
"""
Test mixed content - some factual, some opinion
"""
from src.fact_check_agent.claim_extractor import ClaimExtractor

def test_mixed_content():
    """Test with mixed factual and opinion content"""
    
    extractor = ClaimExtractor()
    
    # Mix of factual claims and opinions
    texts = [
        "trump loves eating macdonals",  # Opinion - should return 0 claims
        "According to the CDC, COVID vaccines are 95% effective",  # Factual claim
        "I think the weather is nice today",  # Opinion
        "Apple's stock price increased by 15% in 2023",  # Factual claim
        "McDonald's serves over 69 million customers daily worldwide"  # Factual claim
    ]
    
    for text in texts:
        print(f"\nTesting: '{text}'")
        print("-" * 50)
        
        claims = extractor.extract_claims(text)
        
        if claims:
            for claim in claims:
                print(f"✅ Found claim: {claim.text}")
                print(f"   Type: {claim.claim_type.value}, Confidence: {claim.confidence}")
        else:
            print("❌ No claims found (correctly filtered opinion/non-factual)")

if __name__ == "__main__":
    test_mixed_content()