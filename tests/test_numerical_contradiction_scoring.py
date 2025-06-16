#!/usr/bin/env python3
"""
Test to verify that numerical contradictions properly impact authenticity scoring
"""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fact_check_agent.authenticity_scorer import AuthenticityScorer

def test_numerical_contradiction_scoring():
    """Test that numerical contradictions severely impact scores"""
    
    print("🧪 TESTING NUMERICAL CONTRADICTION SCORING")
    print("=" * 60)
    
    scorer = AuthenticityScorer()
    
    # Test case 1: Claim with numerical contradiction (like SRA number mismatch)
    claim_text = "MILLS CHODY LLP has SRA number 48778"
    claim_type = "general"
    
    sources = [
        {
            "domain": "sra.org.uk",
            "credibility_score": 0.96,
            "publication_date": "2024-01-01T00:00:00Z"
        }
    ]
    
    evidence = [
        {
            "sentence": "The following regulatory details for Mills Chody LLP are drawn from the Solicitors Regulation Authority (SRA) register",
            "source_url": "https://www.lawstreet.co.uk/solicitors/mills-chody-llp/",
            "source_domain": "lawstreet.co.uk",
            "relevance_score": 0.67,
            "source_credibility": 0.5
        }
    ]
    
    contradictions = [
        {
            "sentence": "Type: Recognised body law practice ; SRA ID: 487179 | SRA Regulated",
            "source_url": "https://solicitors.lawsociety.org.uk/office/466540/mills-chody-llp",
            "source_domain": "solicitors.lawsociety.org.uk",
            "relevance_score": 0.33,
            "source_credibility": 0.5,
            "contradiction_type": "numerical_contradiction"  # This is the key difference
        }
    ]
    
    # Calculate score with numerical contradiction
    result = scorer.calculate_authenticity_score(
        claim_text=claim_text,
        claim_type=claim_type,
        sources=sources,
        evidence=evidence,
        contradictions=contradictions
    )
    
    print(f"📊 Test Results:")
    print(f"Claim: {claim_text}")
    print(f"Final Score: {result.final_score:.3f}")
    print(f"Authenticity Level: {result.authenticity_level.value}")
    print(f"Explanation: {result.explanation}")
    print()
    
    # Test case 2: Same evidence but without numerical contradiction for comparison
    contradictions_no_numerical = [
        {
            "sentence": "Type: Recognised body law practice ; SRA ID: 487179 | SRA Regulated",
            "source_url": "https://solicitors.lawsociety.org.uk/office/466540/mills-chody-llp",
            "source_domain": "solicitors.lawsociety.org.uk",
            "relevance_score": 0.33,
            "source_credibility": 0.5,
            "contradiction_type": "general"  # Not numerical
        }
    ]
    
    result_no_numerical = scorer.calculate_authenticity_score(
        claim_text=claim_text,
        claim_type=claim_type,
        sources=sources,
        evidence=evidence,
        contradictions=contradictions_no_numerical
    )
    
    print(f"📊 Comparison (Non-numerical contradiction):")
    print(f"Final Score: {result_no_numerical.final_score:.3f}")
    print(f"Authenticity Level: {result_no_numerical.authenticity_level.value}")
    print()
    
    # Verify the fix
    print("🔍 VERIFICATION:")
    print(f"Numerical contradiction score: {result.final_score:.3f} ({result.authenticity_level.value})")
    print(f"Regular contradiction score: {result_no_numerical.final_score:.3f} ({result_no_numerical.authenticity_level.value})")
    
    if result.final_score < result_no_numerical.final_score:
        print("✅ PASS: Numerical contradictions properly penalized")
    else:
        print("❌ FAIL: Numerical contradictions not sufficiently penalized")
    
    if result.authenticity_level.value in ['uncertain', 'likely_false', 'false']:
        print("✅ PASS: Numerical contradiction correctly classified as uncertain or worse")
    else:
        print("❌ FAIL: Numerical contradiction incorrectly classified as likely_true or verified")
    
    if "CRITICAL" in result.explanation:
        print("✅ PASS: Explanation properly highlights numerical contradiction")
    else:
        print("❌ FAIL: Explanation doesn't highlight numerical contradiction severity")
    
    print()
    print("🎯 EXPECTED BEHAVIOR:")
    print("- Numerical contradictions should result in 'uncertain' or lower rating")
    print("- Score should be significantly lower than regular contradictions")
    print("- Explanation should highlight the critical nature of numerical mismatches")

if __name__ == "__main__":
    test_numerical_contradiction_scoring()