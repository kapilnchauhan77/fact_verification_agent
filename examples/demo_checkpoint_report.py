#!/usr/bin/env python3
"""
Demo checkpoint monitoring report with sample data
Shows the comprehensive performance reporting capabilities
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
from datetime import datetime
from fact_check_agent.checkpoint_monitor import CheckpointMonitor, CheckpointTiming, add_claim_report

def create_sample_performance_data():
    """Create sample performance data to demonstrate reporting"""
    
    from fact_check_agent.checkpoint_monitor import get_checkpoint_monitor
    monitor = get_checkpoint_monitor()
    
    # Clear any existing data
    monitor.reports.clear()
    
    # Sample checkpoints for different claim types
    sample_claims = [
        {
            'claim_id': 'claim_001',
            'text': 'According to WHO, vaccines are 95% effective',
            'type': 'medical',
            'checkpoints': [
                CheckpointTiming('prompt_creation', time.time(), time.time() + 0.05, 0.05, True),
                CheckpointTiming('gemini_api_call', time.time(), time.time() + 2.3, 2.3, True),
                CheckpointTiming('response_parsing', time.time(), time.time() + 0.1, 0.1, True),
                CheckpointTiming('source_search', time.time(), time.time() + 8.5, 8.5, True),
                CheckpointTiming('web_search_execution', time.time(), time.time() + 6.2, 6.2, True),
                CheckpointTiming('source_prioritization', time.time(), time.time() + 0.8, 0.8, True),
                CheckpointTiming('newspaper3k_extraction', time.time(), time.time() + 3.2, 3.2, False, 'HTTP 403'),
                CheckpointTiming('requests_extraction', time.time(), time.time() + 2.1, 2.1, True),
                CheckpointTiming('evidence_analysis', time.time(), time.time() + 4.5, 4.5, True),
                CheckpointTiming('authenticity_calculation', time.time(), time.time() + 0.3, 0.3, True),
                CheckpointTiming('result_compilation', time.time(), time.time() + 0.2, 0.2, True)
            ]
        },
        {
            'claim_id': 'claim_002', 
            'text': 'Apple stock increased 25% in 2023',
            'type': 'financial',
            'checkpoints': [
                CheckpointTiming('prompt_creation', time.time(), time.time() + 0.04, 0.04, True),
                CheckpointTiming('gemini_api_call', time.time(), time.time() + 1.8, 1.8, True),
                CheckpointTiming('response_parsing', time.time(), time.time() + 0.08, 0.08, True),
                CheckpointTiming('source_search', time.time(), time.time() + 12.1, 12.1, True),
                CheckpointTiming('web_search_execution', time.time(), time.time() + 9.3, 9.3, True),
                CheckpointTiming('source_prioritization', time.time(), time.time() + 0.6, 0.6, True),
                CheckpointTiming('newspaper3k_extraction', time.time(), time.time() + 1.8, 1.8, True),
                CheckpointTiming('evidence_analysis', time.time(), time.time() + 5.2, 5.2, True),
                CheckpointTiming('authenticity_calculation', time.time(), time.time() + 0.4, 0.4, True),
                CheckpointTiming('result_compilation', time.time(), time.time() + 0.15, 0.15, True)
            ]
        },
        {
            'claim_id': 'claim_003',
            'text': 'Scientists developed room temperature quantum computer',
            'type': 'scientific',
            'checkpoints': [
                CheckpointTiming('prompt_creation', time.time(), time.time() + 0.06, 0.06, True),
                CheckpointTiming('gemini_api_call', time.time(), time.time() + 2.1, 2.1, True),
                CheckpointTiming('response_parsing', time.time(), time.time() + 0.12, 0.12, True),
                CheckpointTiming('source_search', time.time(), time.time() + 15.3, 15.3, True),
                CheckpointTiming('web_search_execution', time.time(), time.time() + 11.8, 11.8, True),
                CheckpointTiming('source_prioritization', time.time(), time.time() + 1.2, 1.2, True),
                CheckpointTiming('newspaper3k_extraction', time.time(), time.time() + 4.1, 4.1, False, 'Timeout'),
                CheckpointTiming('requests_extraction', time.time(), time.time() + 3.5, 3.5, True),
                CheckpointTiming('evidence_analysis', time.time(), time.time() + 6.8, 6.8, True),
                CheckpointTiming('authenticity_calculation', time.time(), time.time() + 0.5, 0.5, True),
                CheckpointTiming('result_compilation', time.time(), time.time() + 0.18, 0.18, True)
            ]
        },
        {
            'claim_id': 'claim_004',
            'text': 'US unemployment dropped to 3.1% in December 2023',
            'type': 'statistical',
            'checkpoints': [
                CheckpointTiming('prompt_creation', time.time(), time.time() + 0.045, 0.045, True),
                CheckpointTiming('gemini_api_call', time.time(), time.time() + 1.9, 1.9, True),
                CheckpointTiming('response_parsing', time.time(), time.time() + 0.09, 0.09, True),
                CheckpointTiming('source_search', time.time(), time.time() + 7.2, 7.2, True),
                CheckpointTiming('web_search_execution', time.time(), time.time() + 5.8, 5.8, True),
                CheckpointTiming('source_prioritization', time.time(), time.time() + 0.5, 0.5, True),
                CheckpointTiming('newspaper3k_extraction', time.time(), time.time() + 2.3, 2.3, True),
                CheckpointTiming('evidence_analysis', time.time(), time.time() + 3.9, 3.9, True),
                CheckpointTiming('authenticity_calculation', time.time(), time.time() + 0.25, 0.25, True),
                CheckpointTiming('result_compilation', time.time(), time.time() + 0.12, 0.12, True)
            ]
        },
        {
            'claim_id': 'claim_005',
            'text': 'Climate change causing sea level rise acceleration',
            'type': 'scientific',
            'checkpoints': [
                CheckpointTiming('prompt_creation', time.time(), time.time() + 0.055, 0.055, True),
                CheckpointTiming('gemini_api_call', time.time(), time.time() + 2.4, 2.4, True),
                CheckpointTiming('response_parsing', time.time(), time.time() + 0.11, 0.11, True),
                CheckpointTiming('source_search', time.time(), time.time() + 18.6, 18.6, True),
                CheckpointTiming('web_search_execution', time.time(), time.time() + 14.2, 14.2, True),
                CheckpointTiming('source_prioritization', time.time(), time.time() + 1.5, 1.5, True),
                CheckpointTiming('newspaper3k_extraction', time.time(), time.time() + 2.8, 2.8, True),
                CheckpointTiming('aiohttp_extraction', time.time(), time.time() + 1.9, 1.9, True),
                CheckpointTiming('evidence_analysis', time.time(), time.time() + 8.3, 8.3, True),
                CheckpointTiming('authenticity_calculation', time.time(), time.time() + 0.6, 0.6, True),
                CheckpointTiming('result_compilation', time.time(), time.time() + 0.2, 0.2, True)
            ]
        }
    ]
    
    # Add all sample claims to monitor
    for claim_data in sample_claims:
        add_claim_report(
            claim_id=claim_data['claim_id'],
            claim_text=claim_data['text'],
            claim_type=claim_data['type'],
            checkpoints=claim_data['checkpoints'],
            success=True
        )
    
    return monitor

def demonstrate_performance_report():
    """Demonstrate comprehensive performance reporting"""
    
    print("📊 CHECKPOINT MONITORING SYSTEM DEMONSTRATION")
    print("=" * 80)
    print()
    
    print("🔧 Creating sample performance data...")
    monitor = create_sample_performance_data()
    print("✅ Sample data created (5 claims processed)")
    print()
    
    # Generate and display the performance report
    monitor.print_performance_summary()
    
    # Show detailed breakdown for specific checkpoints
    print("🔍 DETAILED CHECKPOINT ANALYSIS:")
    print("-" * 50)
    
    key_checkpoints = [
        'gemini_api_call',
        'web_search_execution', 
        'evidence_analysis',
        'newspaper3k_extraction',
        'source_search'
    ]
    
    for checkpoint in key_checkpoints:
        stats = monitor.get_checkpoint_stats(checkpoint)
        if stats['count'] > 0:
            print(f"📌 {checkpoint.upper().replace('_', ' ')}:")
            print(f"   • Average: {stats['average']:.3f}s")
            print(f"   • Range: {stats['min']:.3f}s - {stats['max']:.3f}s")
            print(f"   • Success Rate: {stats['success_rate']:.1%}")
            print(f"   • Count: {stats['count']} operations")
            print()
    
    # Save detailed report
    filename = monitor.save_detailed_report("sample_performance_report.json")
    if filename:
        print(f"💾 Detailed JSON report saved to: {filename}")
    
    # Show practical insights
    print("\n🎯 PRACTICAL PERFORMANCE INSIGHTS:")
    print("-" * 40)
    
    report = monitor.generate_comprehensive_report()
    
    if 'bottleneck_analysis' in report:
        bottlenecks = report['bottleneck_analysis'][:3]
        print("🚨 Top Performance Bottlenecks:")
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"   {i}. {bottleneck['checkpoint']}: {bottleneck['average_time']:.2f}s avg")
            
            # Optimization suggestions
            if 'web_search' in bottleneck['checkpoint']:
                print("      💡 Optimization: Reduce search queries or implement caching")
            elif 'extraction' in bottleneck['checkpoint']:
                print("      💡 Optimization: Implement parallel extraction or improve timeouts")
            elif 'evidence' in bottleneck['checkpoint']:
                print("      💡 Optimization: Optimize text processing algorithms")
            elif 'gemini' in bottleneck['checkpoint']:
                print("      💡 Optimization: Consider prompt optimization or model switching")
    
    # Category performance breakdown
    if 'checkpoint_categories' in report:
        categories = report['checkpoint_categories']
        print("\n📈 Processing Time Distribution:")
        for category, stats in categories.items():
            if 'category_totals' in stats:
                totals = stats['category_totals']
                print(f"   • {category.replace('_', ' ').title()}: "
                      f"{totals['percentage_of_total']:.1f}% of total time")
    
    print("\n✅ DEMONSTRATION COMPLETED")
    print("\nThe checkpoint monitoring system provides comprehensive insights into:")
    print("   🔹 Individual operation timing and success rates")
    print("   🔹 Category-based performance breakdown")  
    print("   🔹 Bottleneck identification and optimization opportunities")
    print("   🔹 Performance trends and claim type analysis")
    print("   🔹 Detailed JSON reports for further analysis")
    print("   🔹 Real-time performance tracking during execution")

if __name__ == "__main__":
    demonstrate_performance_report()