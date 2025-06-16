#!/usr/bin/env python3
"""
Demo the optimized fact-checking results format
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
import time
from fact_check_agent.fact_checker import FactChecker, FactCheckResult, Source
from fact_check_agent.claim_extractor import ClaimExtractor, Claim, ClaimType

def create_mock_result():
    """Create a mock result to demonstrate the new format"""
    
    # Mock claim
    claim = Claim(
        text="According to the WHO, COVID-19 vaccines are 95% effective at preventing severe illness.",
        claim_type=ClaimType.MEDICAL,
        confidence=0.95,
        context="Health information from news article",
        sentence_index=0,
        entities=[{'text': 'WHO', 'label': 'ORG'}, {'text': '95%', 'label': 'PERCENT'}],
        keywords=['WHO', 'vaccines', 'effective', 'illness'],
        sources_to_check=['who.int', 'cdc.gov'],
        priority=1
    )
    
    # Mock supporting evidence sentences
    evidence = [
        {
            'sentence': 'According to WHO data, mRNA vaccines show 95% efficacy in preventing severe COVID-19 outcomes.',
            'source_url': 'https://who.int/news/vaccines-effectiveness',
            'source_title': 'WHO Vaccine Effectiveness Report',
            'source_domain': 'who.int',
            'source_credibility': 0.96,
            'relevance_score': 0.92,
            'keyword_matches': 4,
            'has_supporting_language': True,
            'type': 'supporting'
        },
        {
            'sentence': 'Clinical trials demonstrate that COVID-19 vaccines reduce severe illness by approximately 95%.',
            'source_url': 'https://cdc.gov/vaccines/covid-19/effectiveness',
            'source_title': 'CDC Vaccine Effectiveness Studies',
            'source_domain': 'cdc.gov',
            'source_credibility': 0.96,
            'relevance_score': 0.88,
            'keyword_matches': 3,
            'has_supporting_language': True,
            'type': 'supporting'
        }
    ]
    
    # Mock contradictory evidence
    contradictions = [
        {
            'sentence': 'However, recent studies suggest vaccine effectiveness may be lower than initially reported, around 80-85%.',
            'source_url': 'https://reuters.com/health/vaccine-studies-2024',
            'source_title': 'Updated Vaccine Effectiveness Data',
            'source_domain': 'reuters.com',
            'source_credibility': 0.98,
            'relevance_score': 0.75,
            'keyword_matches': 2,
            'contradictory_indicators': ['however'],
            'type': 'contradictory'
        }
    ]
    
    # Mock sources checked
    sources_checked = [
        {'url': 'https://who.int/news/vaccines-effectiveness', 'domain': 'who.int', 'credibility': 0.96},
        {'url': 'https://cdc.gov/vaccines/covid-19/effectiveness', 'domain': 'cdc.gov', 'credibility': 0.96},
        {'url': 'https://reuters.com/health/vaccine-studies-2024', 'domain': 'reuters.com', 'credibility': 0.98}
    ]
    
    return FactCheckResult(
        claim=claim,
        verification_status='verified',
        authenticity_score=0.87,
        sources_checked=sources_checked,
        evidence=evidence,
        contradictions=contradictions,
        processing_time=3.2
    )

def display_detailed_results(result: FactCheckResult):
    """Display detailed fact-check results in the new format"""
    
    print("🎯 OPTIMIZED FACT-CHECK RESULTS")
    print("=" * 50)
    
    print(f"📝 Claim: {result.claim.text}")
    print(f"🏷️  Type: {result.claim.claim_type.value}")
    print(f"📊 Status: {result.verification_status}")
    print(f"⭐ Authenticity Score: {result.authenticity_score:.3f}")
    print(f"🔗 Sources Checked: {len(result.sources_checked)}")
    print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
    print()
    
    # Supporting Evidence Sentences
    print("✅ SUPPORTING EVIDENCE SENTENCES:")
    if result.evidence:
        for i, evidence in enumerate(result.evidence, 1):
            print(f"   {i}. \"{evidence['sentence']}\"")
            print(f"      📍 Source: {evidence['source_domain']} (credibility: {evidence['source_credibility']:.2f})")
            print(f"      🎯 Relevance: {evidence['relevance_score']:.2f}")
            print(f"      🔍 Keyword matches: {evidence['keyword_matches']}")
            if evidence.get('has_supporting_language'):
                print("      ✓ Contains authoritative language")
            print()
    else:
        print("   No supporting evidence found")
        print()
    
    # Contradictory Evidence Sentences
    print("⚠️  CONTRADICTORY EVIDENCE SENTENCES:")
    if result.contradictions:
        for i, contradiction in enumerate(result.contradictions, 1):
            print(f"   {i}. \"{contradiction['sentence']}\"")
            print(f"      📍 Source: {contradiction['source_domain']} (credibility: {contradiction['source_credibility']:.2f})")
            print(f"      🎯 Relevance: {contradiction['relevance_score']:.2f}")
            print(f"      🔍 Keyword matches: {contradiction['keyword_matches']}")
            if contradiction.get('contradictory_indicators'):
                print(f"      ⚠️  Contradictory indicators: {', '.join(contradiction['contradictory_indicators'])}")
            print()
    else:
        print("   No contradictory evidence found")
        print()
    
    # Performance Summary
    print("📈 PERFORMANCE OPTIMIZATIONS:")
    print("   ✅ Reduced 403 errors with expanded blocked domains list")
    print("   ✅ Priority source ordering (WHO, CDC, Reuters first)")
    print("   ✅ Faster processing with 0.3s delays instead of 1.0s")
    print("   ✅ Enhanced concurrent processing (8 vs 5 concurrent)")
    print("   ✅ Shorter timeouts (5s vs 10s) for faster failures")
    print("   ✅ Limited to 15 URLs vs 50 for speed")
    print("   ✅ Detailed sentence-level evidence extraction")

def main():
    """Demo the new optimized fact-checking output"""
    
    print("🚀 OPTIMIZED FACT-CHECKING SYSTEM DEMO")
    print("=" * 60)
    print()
    
    print("📊 System Optimizations:")
    fact_checker = FactChecker()
    print(f"   • Max URLs: {fact_checker.max_urls} (reduced from 50)")
    print(f"   • Priority sources: {fact_checker.priority_sources_limit}")
    print(f"   • Concurrent limit: {fact_checker.concurrent_limit} (increased from 5)")
    print(f"   • Request timeout: {fact_checker.timeout}s (reduced from 10s)")
    print(f"   • Request delay: {fact_checker.delay_between_requests}s (reduced from 1.0s)")
    print(f"   • Blocked domains: {len(fact_checker.blocked_domains)} (expanded list)")
    print(f"   • Priority domains: {len(fact_checker.priority_domains)}")
    print()
    
    # Show the new detailed result format
    result = create_mock_result()
    display_detailed_results(result)
    
    print("\n🎉 Key Features:")
    print("   🔍 Sentence-level evidence and contradiction extraction")
    print("   📊 Relevance scoring for each piece of evidence")
    print("   🏷️  Source credibility ratings")
    print("   ⚡ Speed optimizations for faster fact-checking")
    print("   🚫 Smart blocking of 403-prone domains")
    print("   📈 Priority source ordering for quality")

if __name__ == "__main__":
    main()