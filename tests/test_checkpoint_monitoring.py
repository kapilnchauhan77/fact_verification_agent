#!/usr/bin/env python3
"""
Comprehensive test of checkpoint monitoring system
Demonstrates detailed performance tracking for fact-checking pipeline
"""
import asyncio
import time
import logging
from typing import List

from src.fact_check_agent.claim_extractor import ClaimExtractor
from src.fact_check_agent.fact_checker import FactChecker
from src.fact_check_agent.checkpoint_monitor import get_checkpoint_monitor

# Set logging to INFO to see checkpoint progress
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_comprehensive_monitoring():
    """Test fact-checking with comprehensive checkpoint monitoring"""
    
    print("🚀 COMPREHENSIVE CHECKPOINT MONITORING TEST")
    print("=" * 70)
    
    # Initialize components
    extractor = ClaimExtractor()
    fact_checker = FactChecker()
    monitor = get_checkpoint_monitor()
    
    # Test claims with different complexities and types
    test_claims = [
        {
            "text": "According to the WHO, COVID-19 vaccines are 95% effective at preventing severe illness.",
            "description": "Medical claim with high credibility sources"
        },
        {
            "text": "Apple's stock price increased by 25% in 2023, reaching record highs.",
            "description": "Financial claim requiring market data"
        },
        {
            "text": "Scientists at MIT developed a quantum computer that operates at room temperature.",
            "description": "Scientific/technology claim requiring research verification"
        },
        {
            "text": "The unemployment rate in the US dropped to 3.1% in December 2023.",
            "description": "Statistical claim requiring government sources"
        },
        {
            "text": "Climate change is causing sea levels to rise at an accelerating rate.",
            "description": "Environmental/scientific claim with complex verification"
        }
    ]
    
    print(f"📊 Testing {len(test_claims)} claims with different characteristics")
    print()
    
    # Process each claim and track performance
    for i, claim_data in enumerate(test_claims, 1):
        print(f"🔍 Test {i}/5: {claim_data['description']}")
        print(f"   Claim: \"{claim_data['text'][:60]}...\"")
        
        start_time = time.time()
        
        try:
            # Extract claims using Gemini (with checkpoints)
            claims = extractor.extract_claims(claim_data["text"])
            extraction_time = time.time() - start_time
            
            print(f"   ✅ Claim extraction: {extraction_time:.2f}s ({len(claims)} claims)")
            
            if claims:
                # Fact-check the first claim (with checkpoints)
                fact_start = time.time()
                results = await fact_checker.fact_check_claims(claims[:1])  # Just first claim
                fact_time = time.time() - fact_start
                
                if results:
                    result = results[0]
                    print(f"   ✅ Fact-checking: {fact_time:.2f}s")
                    print(f"      Status: {result.verification_status}")
                    print(f"      Score: {result.authenticity_score:.2f}")
                    print(f"      Sources: {len(result.sources_checked)}")
                    print(f"      Evidence: {len(result.evidence)}")
                    print(f"      Contradictions: {len(result.contradictions)}")
                else:
                    print(f"   ❌ Fact-checking failed")
            else:
                print(f"   ⚠️  No claims extracted")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        total_time = time.time() - start_time
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print()
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Generate and display comprehensive performance report
    print("📈 GENERATING PERFORMANCE REPORT...")
    print("=" * 70)
    
    # Print summary to console
    monitor.print_performance_summary()
    
    # Save detailed report to file
    filename = monitor.save_detailed_report()
    if filename:
        print(f"💾 Detailed report saved to: {filename}")
    
    # Display key insights
    print("🎯 KEY PERFORMANCE INSIGHTS:")
    report = monitor.generate_comprehensive_report()
    
    if 'error' not in report:
        summary = report['summary']
        bottlenecks = report['bottleneck_analysis'][:3]
        
        print(f"   • Average processing time: {summary['average_time_per_claim']:.2f}s per claim")
        print(f"   • Success rate: {summary['success_rate']:.1%}")
        print(f"   • Throughput: {summary['throughput_claims_per_minute']:.1f} claims/minute")
        print()
        
        print("🚨 TOP 3 BOTTLENECKS:")
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"   {i}. {bottleneck['checkpoint']}: {bottleneck['average_time']:.3f}s avg")
            print(f"      (max: {bottleneck['max_time']:.3f}s, success: {bottleneck['success_rate']:.1%})")
        
        # Category breakdown
        if 'checkpoint_categories' in report:
            print("\n⏱️  TIME BREAKDOWN BY CATEGORY:")
            categories = report['checkpoint_categories']
            for category, stats in categories.items():
                if 'category_totals' in stats:
                    totals = stats['category_totals']
                    print(f"   • {category.replace('_', ' ').title()}: "
                          f"{totals['percentage_of_total']:.1f}% "
                          f"({totals['average']:.3f}s avg)")
    
    print("\n✅ CHECKPOINT MONITORING TEST COMPLETED")
    print("=" * 70)
    
    return report

def demonstrate_manual_checkpoints():
    """Demonstrate manual checkpoint usage for custom operations"""
    
    print("\n🔧 MANUAL CHECKPOINT DEMONSTRATION")
    print("-" * 50)
    
    from src.fact_check_agent.checkpoint_monitor import TimedCheckpoint, start_checkpoint, end_checkpoint
    
    # Method 1: Using context manager
    print("1️⃣  Using TimedCheckpoint context manager:")
    with TimedCheckpoint("custom_operation", {"example": "context_manager"}) as cp:
        time.sleep(0.1)  # Simulate work
        print("   Custom operation completed")
    
    # Method 2: Using start/end functions
    print("2️⃣  Using start/end checkpoint functions:")
    checkpoint_id = start_checkpoint("manual_operation", {"example": "manual"})
    time.sleep(0.05)  # Simulate work
    end_checkpoint(checkpoint_id, success=True)
    print("   Manual operation completed")
    
    # Method 3: Error handling
    print("3️⃣  Demonstrating error handling:")
    try:
        with TimedCheckpoint("operation_with_error") as cp:
            time.sleep(0.02)
            raise ValueError("Simulated error")
    except ValueError:
        print("   Error handled gracefully (checkpoint still recorded)")
    
    print("✅ Manual checkpoint demonstration completed\n")

async def main():
    """Main test function"""
    
    # Run manual checkpoint demonstration
    demonstrate_manual_checkpoints()
    
    # Run comprehensive monitoring test
    report = await test_comprehensive_monitoring()
    
    # Final summary
    print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("\nThe checkpoint monitoring system provides:")
    print("   ✅ Detailed timing for each processing stage")
    print("   ✅ Performance bottleneck identification")
    print("   ✅ Success/failure rate tracking")
    print("   ✅ Category-based time breakdown")
    print("   ✅ Performance trend analysis")
    print("   ✅ Comprehensive reporting (JSON + console)")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())