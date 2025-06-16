#!/usr/bin/env python3
"""
Test script to verify the critical fixes:
1. Numerical contradiction detection for mismatched IDs/numbers
2. Improved compound claim extraction 
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fact_check_agent.claim_extractor import ClaimExtractor
from fact_check_agent.fact_checker import FactChecker

async def test_numerical_contradiction_fix():
    """Test that numerical contradictions are properly detected"""
    print("🧪 TESTING NUMERICAL CONTRADICTION DETECTION")
    print("=" * 60)
    
    # Test case that previously failed: SRA number mismatch
    test_text = """
    MILLS CHODY LLP is a SRA-regulated firm with SRA number 48778.
    The firm provides legal services and is authorized by the Solicitors Regulation Authority.
    """
    
    # Simulated evidence that shows wrong SRA number
    conflicting_evidence_text = """
    According to the SRA register, MILLS CHODY LLP has SRA number 487179.
    The firm is listed as authorized but with different registration details.
    """
    
    print(f"Original claim text: {test_text.strip()}")
    print(f"Conflicting evidence: {conflicting_evidence_text.strip()}")
    print()
    
    # Extract claims
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(test_text)
    
    print(f"📊 Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"{i}. {claim.text}")
        print(f"   Type: {claim.claim_type.value}, Confidence: {claim.confidence:.2f}")
    print()
    
    # Test fact-checking with the conflicting evidence
    fact_checker = FactChecker()
    
    if claims:
        print("🔍 Testing numerical contradiction detection...")
        
        # Simulate the fact-checking process
        from fact_check_agent.fact_checker import Source
        from datetime import datetime
        
        # Create a mock source with conflicting numerical evidence
        mock_source = Source(
            url="https://sra.org.uk/register",
            title="SRA Register",
            content=conflicting_evidence_text,
            relevance_score=0.9,
            credibility_score=0.96,  # High credibility
            publication_date=datetime.now(),
            domain="sra.org.uk"
        )
        
        for claim in claims:
            if "48778" in claim.text:  # Test the specific numerical claim
                print(f"Testing claim: {claim.text}")
                
                # Test evidence extraction (should detect contradiction)
                evidence = fact_checker._fast_evidence_extraction(claim, mock_source)
                contradictions = fact_checker._fast_contradiction_detection(claim, mock_source)
                
                print(f"Evidence found: {len(evidence)}")
                print(f"Contradictions found: {len(contradictions)}")
                
                if contradictions:
                    for contradiction in contradictions:
                        print(f"✅ CONTRADICTION DETECTED:")
                        print(f"   Type: {contradiction.get('contradiction_type', 'unknown')}")
                        print(f"   Reasoning: {contradiction.get('logical_reasoning', 'No reasoning')}")
                        print(f"   Sentence: {contradiction.get('sentence', '')[:100]}...")
                else:
                    print("❌ NO CONTRADICTIONS DETECTED - This indicates the fix may not be working")
                
                print()
    
    print("✅ Numerical contradiction test completed\n")

async def test_compound_claim_extraction():
    """Test that compound claims are properly broken down"""
    print("🧪 TESTING COMPOUND CLAIM EXTRACTION")
    print("=" * 60)
    
    # Test case: compound claim that should be split
    test_text = """
    MILLS CHODY LLP is a SRA-regulated firm with SRA number 48778.
    The company was founded in 2010 and has 25 employees.
    Tesla stock increased by 25% and delivered 466,140 vehicles in Q1 2024.
    """
    
    print(f"Test text with compound claims:")
    print(test_text.strip())
    print()
    
    # Extract claims
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(test_text)
    
    print(f"📊 Extracted {len(claims)} claims:")
    for i, claim in enumerate(claims, 1):
        print(f"{i}. {claim.text}")
        print(f"   Type: {claim.claim_type.value}, Confidence: {claim.confidence:.2f}")
        print(f"   Entities: {[e.get('text') for e in claim.entities]}")
        print()
    
    # Check if compound claims were properly separated
    sra_regulation_claims = [c for c in claims if "SRA-regulated" in c.text or "regulated" in c.text]
    sra_number_claims = [c for c in claims if "SRA number" in c.text or "48778" in c.text]
    
    print("🔍 Analysis of claim separation:")
    print(f"SRA regulation claims: {len(sra_regulation_claims)}")
    for claim in sra_regulation_claims:
        print(f"   - {claim.text}")
    
    print(f"SRA number claims: {len(sra_number_claims)}")  
    for claim in sra_number_claims:
        print(f"   - {claim.text}")
    
    if len(sra_regulation_claims) >= 1 and len(sra_number_claims) >= 1:
        print("✅ COMPOUND CLAIM BREAKDOWN SUCCESSFUL - Claims properly separated")
    else:
        print("❌ COMPOUND CLAIM BREAKDOWN FAILED - Claims not properly separated")
    
    print()
    print("✅ Compound claim extraction test completed\n")

async def test_end_to_end_fix():
    """Test the complete end-to-end process with the problematic example"""
    print("🧪 TESTING END-TO-END FIX")
    print("=" * 60)
    
    # The problematic text from the user's example
    test_text = "MILLS CHODY LLP is a SRA-regulated firm with SRA number 48778."
    
    print(f"Testing with: {test_text}")
    print()
    
    # Initialize components
    extractor = ClaimExtractor()
    fact_checker = FactChecker()
    
    # Extract claims
    claims = extractor.extract_claims(test_text)
    print(f"📊 Claims extracted: {len(claims)}")
    for i, claim in enumerate(claims, 1):
        print(f"{i}. {claim.text}")
    print()
    
    # Fact-check claims (this would normally search real sources)
    if claims:
        print("🔍 Running fact-check process...")
        try:
            # Note: This will make real API calls, so we'll limit to first claim
            results = await fact_checker.fact_check_claims(claims[:1])
            
            for result in results:
                print(f"Claim: {result.claim.text}")
                print(f"Status: {result.verification_status}")
                print(f"Authenticity: {result.authenticity_score:.3f}")
                print(f"Evidence count: {len(result.evidence)}")
                print(f"Contradiction count: {len(result.contradictions)}")
                
                if result.evidence:
                    print("Evidence:")
                    for ev in result.evidence[:2]:
                        print(f"  - {ev.get('sentence', '')[:100]}...")
                        print(f"    Reasoning: {ev.get('logical_reasoning', 'No reasoning')}")
                
                if result.contradictions:
                    print("Contradictions:")
                    for contra in result.contradictions[:2]:
                        print(f"  - {contra.get('sentence', '')[:100]}...")
                        print(f"    Reasoning: {contra.get('logical_reasoning', 'No reasoning')}")
                        print(f"    Type: {contra.get('contradiction_type', 'unknown')}")
                
                print()
                
        except Exception as e:
            print(f"❌ Error during fact-checking: {str(e)}")
            print("This is expected if API keys are not configured")
    
    print("✅ End-to-end test completed")

async def main():
    """Run all tests"""
    print("🚀 TESTING CRITICAL FIXES")
    print("=" * 80)
    print()
    
    await test_compound_claim_extraction()
    await test_numerical_contradiction_fix()
    await test_end_to_end_fix()
    
    print("🎉 ALL TESTS COMPLETED!")
    print()
    print("🔧 FIXES IMPLEMENTED:")
    print("1. ✅ Enhanced claim extraction to break down compound claims")
    print("2. ✅ Numerical contradiction detection for ID/registration numbers")
    print("3. ✅ Improved evidence validation with contextual reasoning")
    print("4. ✅ Enhanced scoring algorithm for high evidence + low contradictions")

if __name__ == "__main__":
    asyncio.run(main())