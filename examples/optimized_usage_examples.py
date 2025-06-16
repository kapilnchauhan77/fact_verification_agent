"""
Usage examples for the optimized fact checker with all bottleneck fixes
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
from fact_check_agent.claim_extractor import ClaimExtractor
from fact_check_agent.fact_checker import FactChecker  # Now optimized!
from fact_check_agent.performance_cache import get_cache_stats, clear_all_caches

async def example_optimized_usage():
    """Example of using the optimized fact checker"""
    
    # Initialize components (now optimized)
    extractor = ClaimExtractor()
    fact_checker = FactChecker()  # Uses optimized implementation
    
    # Test claim
    text = "According to WHO, COVID-19 vaccines are 95% effective."
    
    print("🧠 Extracting claims...")
    claims = extractor.extract_claims(text)
    
    print("🔍 Fact-checking with optimizations...")
    results = await fact_checker.fact_check_claims(claims)
    
    # Display results
    for result in results:
        print(f"\nClaim: {result.claim.text}")
        print(f"Status: {result.verification_status}")
        print(f"Score: {result.authenticity_score:.2f}")
        print(f"Sources: {len(result.sources_checked)}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Cache hits: {result.cache_hits}")
    
    # Show cache statistics
    cache_stats = get_cache_stats()
    print(f"\n📊 Cache Performance:")
    for cache_name, stats in cache_stats.items():
        if isinstance(stats, dict) and 'hit_rate' in stats:
            print(f"   {cache_name}: {stats['hit_rate']:.1%} hit rate")

async def benchmark_example():
    """Example of running performance benchmark"""
    from performance_benchmark import PerformanceBenchmark
    
    print("🚀 Running performance benchmark...")
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_comprehensive_benchmark()
    
    if results:
        improvements = results['performance_improvements']
        print(f"\n🎯 Results: {improvements['speedup_factor']:.2f}x faster!")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_optimized_usage())
    
    # Uncomment to run benchmark
    # asyncio.run(benchmark_example())
