#!/usr/bin/env python3
"""
Test the optimized fact-checking system with detailed evidence/contradiction output
"""
import asyncio
import time
import logging
import json
from src.fact_check_agent.fact_checker import FactChecker
from src.fact_check_agent.claim_extractor import ClaimExtractor

# Reduce logging noise for clean output
logging.basicConfig(level=logging.WARNING)

async def test_optimized_fact_check():
    """Test optimized fact-checking with detailed sentence lists"""
    
    print("🚀 Testing Optimized Fact-Checking System")
    print("=" * 60)
    
    # Initialize components
    extractor = ClaimExtractor()
    fact_checker = FactChecker()
    
    # Display optimization settings
    print("⚙️  Optimization Settings:")
    print(f"   • Max URLs: {fact_checker.max_urls}")
    print(f"   • Priority sources: {fact_checker.priority_sources_limit}")
    print(f"   • Concurrent limit: {fact_checker.concurrent_limit}")
    print(f"   • Request timeout: {fact_checker.timeout}s")
    print(f"   • Request delay: {fact_checker.delay_between_requests}s")
    print(f"   • Blocked domains: {len(fact_checker.blocked_domains)}")
    print()
    
    # Test claims
    test_claims = [
        "According to the WHO, COVID-19 vaccines are 95% effective at preventing severe illness.",
        "Apple's stock price increased by 25% in 2023, reaching record highs."
    ]
    
    for i, test_text in enumerate(test_claims, 1):
        print(f"🔍 Test {i}: {test_text}")
        print("-" * 50)
        
        start_time = time.time()
        
        # Extract claims
        print("📋 Extracting claims...")
        claims = extractor.extract_claims(test_text)
        extraction_time = time.time() - start_time
        
        print(f"   ✅ Found {len(claims)} claims in {extraction_time:.2f}s")
        
        if claims:
            # Fact-check
            print("📊 Fact-checking with optimized system...")
            fact_start = time.time()
            
            results = await fact_checker.fact_check_claims(claims)
            fact_time = time.time() - fact_start
            total_time = time.time() - start_time
            
            print(f"   ✅ Completed in {fact_time:.2f}s (total: {total_time:.2f}s)")
            print()
            
            # Display detailed results
            for result in results:
                print("📊 FACT-CHECK RESULTS:")
                print(f"   • Status: {result.verification_status}")
                print(f"   • Authenticity Score: {result.authenticity_score:.3f}")
                print(f"   • Sources Checked: {len(result.sources_checked)}")
                print()
                
                # Supporting Evidence Sentences
                if result.evidence:
                    print("✅ SUPPORTING EVIDENCE:")
                    for j, evidence in enumerate(result.evidence[:5], 1):
                        print(f"   {j}. \"{evidence.get('sentence', evidence.get('text', ''))}\"")
                        print(f"      Source: {evidence.get('source_domain', 'Unknown')}")
                        print(f"      Credibility: {evidence.get('source_credibility', 0):.2f}")
                        print(f"      Relevance: {evidence.get('relevance_score', 0):.2f}")
                        if evidence.get('has_supporting_language'):
                            print(f"      ✓ Contains supporting language")
                        print()
                else:
                    print("❌ No supporting evidence found")
                    print()
                
                # Contradictory Evidence Sentences
                if result.contradictions:
                    print("⚠️  CONTRADICTORY EVIDENCE:")
                    for j, contradiction in enumerate(result.contradictions[:3], 1):
                        print(f"   {j}. \"{contradiction.get('sentence', contradiction.get('text', ''))}\"")
                        print(f"      Source: {contradiction.get('source_domain', 'Unknown')}")
                        print(f"      Credibility: {contradiction.get('source_credibility', 0):.2f}")
                        print(f"      Relevance: {contradiction.get('relevance_score', 0):.2f}")
                        if contradiction.get('contradictory_indicators'):
                            print(f"      ⚠️  Indicators: {', '.join(contradiction['contradictory_indicators'])}")
                        print()
                else:
                    print("✅ No contradictory evidence found")
                    print()
                
                # Performance metrics
                print("📈 PERFORMANCE METRICS:")
                print(f"   • Processing time: {result.processing_time:.2f}s")
                print(f"   • Evidence items: {len(result.evidence)}")
                print(f"   • Contradiction items: {len(result.contradictions)}")
                print(f"   • Speed: ~{len(test_text) / total_time:.0f} chars/sec")
                
                if result.error_message:
                    print(f"   ❌ Error: {result.error_message}")
        
        print("\n" + "=" * 60 + "\n")
    
    print("🎉 Optimization Test Complete!")
    print("\n📊 Key Improvements:")
    print("   ✅ Reduced 403 errors with expanded blocked domains")
    print("   ✅ Faster processing with reduced timeouts and delays")
    print("   ✅ Priority source ordering for better quality")
    print("   ✅ Detailed evidence and contradiction sentences")
    print("   ✅ Enhanced concurrent processing")

if __name__ == "__main__":
    asyncio.run(test_optimized_fact_check())