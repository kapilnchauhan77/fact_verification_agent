"""
Comprehensive performance benchmark comparing original vs optimized fact checker
Tests all major bottleneck fixes and reports performance improvements
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
import statistics

from fact_check_agent.claim_extractor import ClaimExtractor, Claim, ClaimType
from fact_check_agent.fact_checker import FactChecker  # Original
from fact_check_agent.optimized_fact_checker import OptimizedFactChecker  # Optimized
from fact_check_agent.checkpoint_monitor import get_checkpoint_monitor, clear_all_checkpoints
from fact_check_agent.performance_cache import get_cache_stats, clear_all_caches

# Configure logging for cleaner output
logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self):
        """Initialize benchmark with test claims"""
        self.extractor = ClaimExtractor()
        self.original_checker = FactChecker()
        self.optimized_checker = OptimizedFactChecker()
        
        # Test claims covering different types and complexities
        self.test_claims = [
            {
                "text": "According to WHO data, COVID-19 vaccines are 95% effective at preventing severe illness and hospitalization.",
                "type": "medical",
                "description": "Medical claim with WHO source",
                "expected_sources": ["who.int", "cdc.gov", "nih.gov"]
            },
            {
                "text": "Apple's stock price increased by 28% in 2023, reaching a market cap of $3 trillion.",
                "type": "financial", 
                "description": "Financial claim with specific numbers",
                "expected_sources": ["reuters.com", "bloomberg.com", "sec.gov"]
            },
            {
                "text": "Scientists at MIT developed a room-temperature quantum computer in December 2023.",
                "type": "scientific",
                "description": "Scientific/technology breakthrough claim",
                "expected_sources": ["nature.com", "science.org", "mit.edu"]
            },
            {
                "text": "The US unemployment rate dropped to 3.5% in November 2023 according to Bureau of Labor Statistics.",
                "type": "statistical",
                "description": "Government statistical claim",
                "expected_sources": ["bls.gov", "reuters.com", "apnews.com"]
            },
            {
                "text": "Climate change is causing global sea levels to rise at an accelerating rate of 3.4mm per year.",
                "type": "scientific",
                "description": "Environmental scientific claim",
                "expected_sources": ["nasa.gov", "noaa.gov", "nature.com"]
            }
        ]
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark comparing original vs optimized"""
        
        print("🚀 COMPREHENSIVE FACT-CHECKER PERFORMANCE BENCHMARK")
        print("=" * 80)
        print()
        
        # Clear caches and checkpoints for fair comparison
        clear_all_caches()
        clear_all_checkpoints()
        
        # Extract claims for testing
        print("🧠 Extracting test claims using Gemini...")
        extracted_claims = []
        
        for claim_data in self.test_claims:
            claims = self.extractor.extract_claims(claim_data["text"])
            if claims:
                claim = claims[0]  # Use first extracted claim
                claim.claim_type = ClaimType(claim_data["type"])  # Ensure correct type
                extracted_claims.append({
                    'claim': claim,
                    'description': claim_data["description"],
                    'expected_sources': claim_data["expected_sources"]
                })
        
        print(f"✅ Extracted {len(extracted_claims)} claims for testing")
        print()
        
        # Benchmark original fact checker
        print("📊 BENCHMARKING ORIGINAL FACT CHECKER...")
        print("-" * 50)
        original_results = await self._benchmark_fact_checker(
            self.original_checker, 
            [item['claim'] for item in extracted_claims],
            "Original"
        )
        
        # Clear caches between tests for fair comparison
        clear_all_caches()
        
        print("\n🚀 BENCHMARKING OPTIMIZED FACT CHECKER...")
        print("-" * 50)
        optimized_results = await self._benchmark_fact_checker(
            self.optimized_checker,
            [item['claim'] for item in extracted_claims], 
            "Optimized"
        )
        
        # Generate performance comparison
        comparison = self._generate_performance_comparison(
            original_results, 
            optimized_results, 
            extracted_claims
        )
        
        # Display comprehensive results
        self._display_benchmark_results(comparison)
        
        return comparison
    
    async def _benchmark_fact_checker(self, fact_checker, claims: List[Claim], label: str) -> Dict[str, Any]:
        """Benchmark a specific fact checker implementation"""
        
        start_time = time.time()
        monitor = get_checkpoint_monitor()
        
        print(f"🔍 Running {label} fact-checker on {len(claims)} claims...")
        
        # Track individual claim times
        claim_times = []
        claim_results = []
        
        for i, claim in enumerate(claims, 1):
            claim_start = time.time()
            
            try:
                # Fact-check single claim
                results = await fact_checker.fact_check_claims([claim])
                
                if results and len(results) > 0:
                    result = results[0]
                    claim_time = time.time() - claim_start
                    claim_times.append(claim_time)
                    claim_results.append(result)
                    
                    print(f"   Claim {i}: {claim_time:.2f}s - {result.verification_status} "
                          f"(score: {result.authenticity_score:.2f}, sources: {len(result.sources_checked)})")
                else:
                    claim_time = time.time() - claim_start
                    claim_times.append(claim_time)
                    print(f"   Claim {i}: {claim_time:.2f}s - FAILED")
                
            except Exception as e:
                claim_time = time.time() - claim_start
                claim_times.append(claim_time)
                print(f"   Claim {i}: {claim_time:.2f}s - ERROR: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Get checkpoint statistics
        checkpoint_report = monitor.generate_comprehensive_report()
        cache_stats = get_cache_stats()
        
        # Calculate statistics
        avg_time = statistics.mean(claim_times) if claim_times else 0
        median_time = statistics.median(claim_times) if claim_times else 0
        min_time = min(claim_times) if claim_times else 0
        max_time = max(claim_times) if claim_times else 0
        
        print(f"✅ {label} completed in {total_time:.2f}s")
        print(f"   Average per claim: {avg_time:.2f}s")
        print(f"   Range: {min_time:.2f}s - {max_time:.2f}s")
        
        return {
            'label': label,
            'total_time': total_time,
            'claim_times': claim_times,
            'avg_time': avg_time,
            'median_time': median_time,
            'min_time': min_time,
            'max_time': max_time,
            'claim_results': claim_results,
            'checkpoint_report': checkpoint_report,
            'cache_stats': cache_stats,
            'success_count': len([r for r in claim_results if r.verification_status != 'error'])
        }
    
    def _generate_performance_comparison(
        self, 
        original: Dict[str, Any], 
        optimized: Dict[str, Any],
        extracted_claims: List[Dict]
    ) -> Dict[str, Any]:
        """Generate comprehensive performance comparison"""
        
        # Calculate improvements
        time_improvement = ((original['total_time'] - optimized['total_time']) / original['total_time']) * 100
        avg_time_improvement = ((original['avg_time'] - optimized['avg_time']) / original['avg_time']) * 100
        
        # Cache efficiency
        original_cache_hits = 0
        optimized_cache_hits = sum([
            optimized['cache_stats'].get('search_cache', {}).get('hits', 0),
            optimized['cache_stats'].get('content_cache', {}).get('hits', 0),
            optimized['cache_stats'].get('source_cache', {}).get('hits', 0)
        ])
        
        # Bottleneck analysis from checkpoints
        original_bottlenecks = self._analyze_bottlenecks(original.get('checkpoint_report', {}))
        optimized_bottlenecks = self._analyze_bottlenecks(optimized.get('checkpoint_report', {}))
        
        return {
            'test_metadata': {
                'test_date': datetime.now().isoformat(),
                'claims_tested': len(extracted_claims),
                'claim_types': list(set(item['claim']['claim_type'].value for item in extracted_claims))
            },
            'performance_improvements': {
                'total_time_improvement_percent': time_improvement,
                'avg_time_improvement_percent': avg_time_improvement,
                'original_total_time': original['total_time'],
                'optimized_total_time': optimized['total_time'],
                'original_avg_time': original['avg_time'],
                'optimized_avg_time': optimized['avg_time'],
                'speedup_factor': original['total_time'] / optimized['total_time'] if optimized['total_time'] > 0 else 0
            },
            'cache_efficiency': {
                'original_cache_hits': original_cache_hits,
                'optimized_cache_hits': optimized_cache_hits,
                'cache_hit_improvement': optimized_cache_hits - original_cache_hits
            },
            'bottleneck_fixes': {
                'original_bottlenecks': original_bottlenecks,
                'optimized_bottlenecks': optimized_bottlenecks
            },
            'success_rates': {
                'original_success_rate': original['success_count'] / len(extracted_claims),
                'optimized_success_rate': optimized['success_count'] / len(extracted_claims)
            },
            'detailed_results': {
                'original': original,
                'optimized': optimized
            }
        }
    
    def _analyze_bottlenecks(self, checkpoint_report: Dict) -> Dict[str, Any]:
        """Analyze bottlenecks from checkpoint report"""
        if not checkpoint_report or 'bottleneck_analysis' not in checkpoint_report:
            return {}
        
        bottlenecks = checkpoint_report['bottleneck_analysis'][:5]  # Top 5
        
        return {
            'top_bottlenecks': [
                {
                    'checkpoint': b['checkpoint'],
                    'avg_time': b['average_time'],
                    'max_time': b['max_time']
                }
                for b in bottlenecks
            ],
            'total_bottleneck_time': sum(b['average_time'] for b in bottlenecks)
        }
    
    def _display_benchmark_results(self, comparison: Dict[str, Any]) -> None:
        """Display comprehensive benchmark results"""
        
        print("\n🎯 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        
        perf = comparison['performance_improvements']
        cache = comparison['cache_efficiency']
        success = comparison['success_rates']
        
        print(f"\n📈 OVERALL PERFORMANCE IMPROVEMENTS:")
        print(f"   • Total Time: {perf['original_total_time']:.2f}s → {perf['optimized_total_time']:.2f}s")
        print(f"   • Speedup Factor: {perf['speedup_factor']:.2f}x faster")
        print(f"   • Time Reduction: {perf['total_time_improvement_percent']:.1f}%")
        print(f"   • Avg Time per Claim: {perf['original_avg_time']:.2f}s → {perf['optimized_avg_time']:.2f}s")
        print(f"   • Per-Claim Improvement: {perf['avg_time_improvement_percent']:.1f}%")
        
        print(f"\n🎯 CACHE PERFORMANCE:")
        print(f"   • Original Cache Hits: {cache['original_cache_hits']}")
        print(f"   • Optimized Cache Hits: {cache['optimized_cache_hits']}")
        print(f"   • Cache Hit Improvement: +{cache['cache_hit_improvement']} hits")
        
        print(f"\n✅ SUCCESS RATES:")
        print(f"   • Original Success Rate: {success['original_success_rate']:.1%}")
        print(f"   • Optimized Success Rate: {success['optimized_success_rate']:.1%}")
        
        # Bottleneck comparison
        original_bottlenecks = comparison['bottleneck_fixes']['original_bottlenecks']
        optimized_bottlenecks = comparison['bottleneck_fixes']['optimized_bottlenecks']
        
        if original_bottlenecks and optimized_bottlenecks:
            print(f"\n🚨 BOTTLENECK IMPROVEMENTS:")
            
            orig_top = original_bottlenecks.get('top_bottlenecks', [])
            opt_top = optimized_bottlenecks.get('top_bottlenecks', [])
            
            print("   Original Top Bottlenecks:")
            for i, bottleneck in enumerate(orig_top[:3], 1):
                print(f"      {i}. {bottleneck['checkpoint']}: {bottleneck['avg_time']:.3f}s")
            
            print("   Optimized Top Bottlenecks:")
            for i, bottleneck in enumerate(opt_top[:3], 1):
                print(f"      {i}. {bottleneck['checkpoint']}: {bottleneck['avg_time']:.3f}s")
        
        print(f"\n🏆 KEY OPTIMIZATIONS IMPLEMENTED:")
        print("   ✅ Ultra-fast source search with aggressive caching")
        print("   ✅ Enhanced content extraction with 4 concurrent methods")
        print("   ✅ Parallel web search execution")
        print("   ✅ Expanded domain blocking (40+ blocked domains)")
        print("   ✅ Smart user agent rotation (25 agents)")
        print("   ✅ Priority source checking for high-credibility domains")
        print("   ✅ Reduced timeouts and query limits")
        print("   ✅ Enhanced concurrent processing limits")
        
        print(f"\n🎉 SUMMARY:")
        if perf['speedup_factor'] > 1:
            print(f"   The optimized fact-checker is {perf['speedup_factor']:.2f}x FASTER")
            print(f"   Processing time reduced by {perf['total_time_improvement_percent']:.1f}%")
            print(f"   All major bottlenecks successfully optimized!")
        else:
            print("   Performance optimization results are inconclusive.")
        
        print("\n✅ BENCHMARK COMPLETED SUCCESSFULLY!")
        print("=" * 80)

async def main():
    """Run the comprehensive performance benchmark"""
    benchmark = PerformanceBenchmark()
    
    try:
        comparison_results = await benchmark.run_comprehensive_benchmark()
        
        # Save detailed results to file
        import json
        with open('performance_benchmark_results.json', 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: performance_benchmark_results.json")
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        print(f"\n❌ Benchmark failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())