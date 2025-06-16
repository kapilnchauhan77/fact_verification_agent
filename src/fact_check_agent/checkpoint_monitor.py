#!/usr/bin/env python3
"""
Comprehensive checkpoint monitoring system for fact-checking pipeline
Tracks detailed timing for each stage of claim processing
"""
import time
import json
import logging
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class CheckpointTiming:
    """Represents timing data for a single checkpoint"""
    name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ClaimProcessingReport:
    """Complete timing report for processing a single claim"""
    claim_id: str
    claim_text: str
    claim_type: str
    total_duration: float
    checkpoints: List[CheckpointTiming]
    success: bool
    timestamp: datetime
    
    def get_checkpoint_duration(self, checkpoint_name: str) -> Optional[float]:
        """Get duration for a specific checkpoint"""
        for cp in self.checkpoints:
            if cp.name == checkpoint_name:
                return cp.duration
        return None
    
    def get_successful_checkpoints(self) -> List[CheckpointTiming]:
        """Get only successful checkpoints"""
        return [cp for cp in self.checkpoints if cp.success]

class CheckpointMonitor:
    """Monitors and tracks performance metrics for fact-checking pipeline"""
    
    def __init__(self):
        self.reports: List[ClaimProcessingReport] = []
        self.current_checkpoints: Dict[str, CheckpointTiming] = {}
        self.session_start = time.time()
        
        # Define checkpoint categories with expected checkpoints
        self.checkpoint_categories = {
            'claim_extraction': [
                'gemini_initialization', 
                'prompt_creation', 
                'gemini_api_call', 
                'response_parsing',
                'claim_validation'
            ],
            'source_search': [
                'search_query_generation', 
                'web_search_execution', 
                'source_prioritization',
                'domain_filtering',
                'result_deduplication'
            ],
            'content_extraction': [
                'url_preprocessing',
                'newspaper3k_extraction', 
                'requests_extraction', 
                'aiohttp_extraction',
                'content_validation'
            ],
            'evidence_analysis': [
                'keyword_matching',
                'evidence_extraction', 
                'contradiction_detection', 
                'relevance_scoring',
                'language_analysis'
            ],
            'final_processing': [
                'authenticity_calculation', 
                'result_compilation',
                'response_formatting'
            ]
        }
    
    def start_checkpoint(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start timing a checkpoint"""
        checkpoint_id = f"{name}_{int(time.time() * 1000)}"
        
        checkpoint = CheckpointTiming(
            name=name,
            start_time=time.time(),
            end_time=0.0,
            duration=0.0,
            success=False,
            metadata=metadata or {}
        )
        
        self.current_checkpoints[checkpoint_id] = checkpoint
        logger.debug(f"🔵 Started checkpoint: {name}")
        return checkpoint_id
    
    def end_checkpoint(self, checkpoint_id: str, success: bool = True, error_message: Optional[str] = None):
        """End timing a checkpoint"""
        if checkpoint_id not in self.current_checkpoints:
            logger.warning(f"⚠️  Checkpoint {checkpoint_id} not found")
            return
        
        checkpoint = self.current_checkpoints[checkpoint_id]
        checkpoint.end_time = time.time()
        checkpoint.duration = checkpoint.end_time - checkpoint.start_time
        checkpoint.success = success
        checkpoint.error_message = error_message
        
        status = "✅" if success else "❌"
        logger.debug(f"{status} Completed checkpoint: {checkpoint.name} in {checkpoint.duration:.3f}s")
    
    def add_claim_report(self, claim_id: str, claim_text: str, claim_type: str, 
                        checkpoints: List[CheckpointTiming], success: bool):
        """Add a complete claim processing report"""
        total_duration = sum(cp.duration for cp in checkpoints)
        
        report = ClaimProcessingReport(
            claim_id=claim_id,
            claim_text=claim_text[:100] + "..." if len(claim_text) > 100 else claim_text,
            claim_type=claim_type,
            total_duration=total_duration,
            checkpoints=checkpoints,
            success=success,
            timestamp=datetime.now()
        )
        
        self.reports.append(report)
        logger.info(f"📊 Added report for claim {claim_id}: {total_duration:.2f}s total")
    
    def get_checkpoint_stats(self, checkpoint_name: str) -> Dict[str, float]:
        """Get statistics for a specific checkpoint across all claims"""
        durations = []
        successes = 0
        total_count = 0
        
        for report in self.reports:
            for cp in report.checkpoints:
                if cp.name == checkpoint_name:
                    durations.append(cp.duration)
                    if cp.success:
                        successes += 1
                    total_count += 1
        
        if not durations:
            return {
                'count': 0, 'average': 0.0, 'min': 0.0, 'max': 0.0, 
                'median': 0.0, 'success_rate': 0.0
            }
        
        return {
            'count': len(durations),
            'average': statistics.mean(durations),
            'min': min(durations),
            'max': max(durations),
            'median': statistics.median(durations),
            'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0.0,
            'success_rate': successes / total_count if total_count > 0 else 0.0
        }
    
    def get_category_stats(self, category: str) -> Dict[str, Any]:
        """Get combined statistics for a checkpoint category"""
        if category not in self.checkpoint_categories:
            return {}
        
        checkpoint_names = self.checkpoint_categories[category]
        category_stats = {}
        total_durations = []
        
        for name in checkpoint_names:
            stats = self.get_checkpoint_stats(name)
            category_stats[name] = stats
            
            # Collect all durations for category totals
            for report in self.reports:
                duration = report.get_checkpoint_duration(name)
                if duration is not None:
                    total_durations.append(duration)
        
        # Calculate category totals
        if total_durations:
            category_stats['category_totals'] = {
                'average': statistics.mean(total_durations),
                'total_time': sum(total_durations),
                'count': len(total_durations),
                'percentage_of_total': 0.0  # Will be calculated in main report
            }
        
        return category_stats
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report with detailed analysis"""
        if not self.reports:
            return {'error': 'No performance data available'}
        
        # Overall statistics
        total_claims = len(self.reports)
        successful_claims = len([r for r in self.reports if r.success])
        total_processing_time = sum(r.total_duration for r in self.reports)
        average_claim_time = total_processing_time / total_claims if total_claims > 0 else 0
        
        # Calculate category statistics and percentages
        checkpoint_stats = {}
        category_totals = {}
        
        for category, checkpoints in self.checkpoint_categories.items():
            category_data = self.get_category_stats(category)
            checkpoint_stats[category] = category_data
            
            if 'category_totals' in category_data:
                category_totals[category] = category_data['category_totals']['total_time']
        
        # Calculate percentages
        total_category_time = sum(category_totals.values())
        for category in checkpoint_stats:
            if 'category_totals' in checkpoint_stats[category]:
                cat_time = category_totals.get(category, 0)
                percentage = (cat_time / total_category_time * 100) if total_category_time > 0 else 0
                checkpoint_stats[category]['category_totals']['percentage_of_total'] = percentage
        
        # Individual checkpoint averages
        individual_stats = {}
        all_checkpoints = set()
        for report in self.reports:
            for cp in report.checkpoints:
                all_checkpoints.add(cp.name)
        
        for checkpoint in all_checkpoints:
            individual_stats[checkpoint] = self.get_checkpoint_stats(checkpoint)
        
        # Performance by claim type
        claim_types = {}
        for report in self.reports:
            if report.claim_type not in claim_types:
                claim_types[report.claim_type] = []
            claim_types[report.claim_type].append(report.total_duration)
        
        type_averages = {
            claim_type: {
                'average': statistics.mean(durations),
                'count': len(durations),
                'min': min(durations),
                'max': max(durations)
            }
            for claim_type, durations in claim_types.items()
        }
        
        # Performance trends (last 10 vs first 10)
        trends = {}
        if total_claims >= 20:
            first_10 = [r.total_duration for r in self.reports[:10]]
            last_10 = [r.total_duration for r in self.reports[-10:]]
            
            trends = {
                'first_10_average': statistics.mean(first_10),
                'last_10_average': statistics.mean(last_10),
                'improvement_percentage': ((statistics.mean(first_10) - statistics.mean(last_10)) / statistics.mean(first_10) * 100) if statistics.mean(first_10) > 0 else 0
            }
        
        # Bottleneck analysis (slowest checkpoints)
        bottlenecks = []
        for checkpoint, stats in individual_stats.items():
            if stats['count'] > 0:
                bottlenecks.append({
                    'checkpoint': checkpoint,
                    'average_time': stats['average'],
                    'max_time': stats['max'],
                    'count': stats['count'],
                    'success_rate': stats['success_rate']
                })
        
        bottlenecks.sort(key=lambda x: x['average_time'], reverse=True)
        
        return {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'session_duration': time.time() - self.session_start,
                'total_claims_processed': total_claims
            },
            'summary': {
                'total_claims_processed': total_claims,
                'successful_claims': successful_claims,
                'failed_claims': total_claims - successful_claims,
                'success_rate': successful_claims / total_claims if total_claims > 0 else 0,
                'total_processing_time': total_processing_time,
                'average_time_per_claim': average_claim_time,
                'throughput_claims_per_minute': (total_claims / (time.time() - self.session_start) * 60) if (time.time() - self.session_start) > 0 else 0
            },
            'checkpoint_categories': checkpoint_stats,
            'individual_checkpoints': individual_stats,
            'performance_by_claim_type': type_averages,
            'performance_trends': trends,
            'bottleneck_analysis': bottlenecks[:10],  # Top 10 bottlenecks
            'recent_claims': [
                {
                    'claim_id': r.claim_id,
                    'claim_text': r.claim_text,
                    'claim_type': r.claim_type,
                    'duration': r.total_duration,
                    'success': r.success,
                    'timestamp': r.timestamp.isoformat(),
                    'checkpoint_count': len(r.checkpoints)
                }
                for r in self.reports[-10:]  # Last 10 claims
            ]
        }
    
    def save_detailed_report(self, filename: str = None) -> str:
        """Save detailed performance report to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"checkpoint_performance_report_{timestamp}.json"
        
        report = self.generate_comprehensive_report()
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"📄 Detailed performance report saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Failed to save report: {str(e)}")
            return None
    
    def print_performance_summary(self):
        """Print formatted performance summary to console"""
        report = self.generate_comprehensive_report()
        
        if 'error' in report:
            print(f"❌ {report['error']}")
            return
        
        print("\n" + "="*90)
        print("🚀 FACT-CHECKING PIPELINE PERFORMANCE REPORT")
        print("="*90)
        
        # Summary section
        summary = report['summary']
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"   • Total Claims Processed: {summary['total_claims_processed']}")
        print(f"   • Successful Claims: {summary['successful_claims']}")
        print(f"   • Failed Claims: {summary['failed_claims']}")
        print(f"   • Success Rate: {summary['success_rate']:.1%}")
        print(f"   • Average Time per Claim: {summary['average_time_per_claim']:.2f}s")
        print(f"   • Processing Throughput: {summary['throughput_claims_per_minute']:.1f} claims/min")
        
        # Checkpoint categories with timing breakdown
        print(f"\n⏱️  CHECKPOINT CATEGORY BREAKDOWN:")
        categories = report['checkpoint_categories']
        
        for category, stats in categories.items():
            if 'category_totals' in stats:
                totals = stats['category_totals']
                print(f"   🔹 {category.upper().replace('_', ' ')}:")
                print(f"      ├─ Average Time: {totals['average']:.3f}s")
                print(f"      ├─ Total Time: {totals['total_time']:.2f}s")
                print(f"      ├─ Operations: {totals['count']}")
                print(f"      └─ % of Total: {totals['percentage_of_total']:.1f}%")
        
        # Performance trends
        if 'performance_trends' in report and report['performance_trends']:
            trends = report['performance_trends']
            print(f"\n📈 PERFORMANCE TRENDS:")
            print(f"   • First 10 Claims Average: {trends['first_10_average']:.2f}s")
            print(f"   • Last 10 Claims Average: {trends['last_10_average']:.2f}s")
            if trends['improvement_percentage'] > 0:
                print(f"   • Performance Improvement: {trends['improvement_percentage']:.1f}% faster")
            else:
                print(f"   • Performance Change: {abs(trends['improvement_percentage']):.1f}% slower")
        
        # Bottleneck analysis
        print(f"\n🚨 TOP PERFORMANCE BOTTLENECKS:")
        bottlenecks = report['bottleneck_analysis'][:5]  # Top 5
        
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"   {i}. {bottleneck['checkpoint']}")
            print(f"      ├─ Average: {bottleneck['average_time']:.3f}s")
            print(f"      ├─ Max: {bottleneck['max_time']:.3f}s")
            print(f"      ├─ Count: {bottleneck['count']}")
            print(f"      └─ Success Rate: {bottleneck['success_rate']:.1%}")
        
        # Performance by claim type
        if 'performance_by_claim_type' in report:
            print(f"\n📋 PERFORMANCE BY CLAIM TYPE:")
            for claim_type, stats in report['performance_by_claim_type'].items():
                print(f"   • {claim_type.upper()}: {stats['average']:.2f}s avg "
                      f"({stats['count']} claims, {stats['min']:.2f}s-{stats['max']:.2f}s range)")
        
        # Recent activity
        print(f"\n🕒 RECENT CLAIMS (Last 5):")
        recent = report['recent_claims'][-5:]
        for claim in recent:
            status = "✅" if claim['success'] else "❌"
            print(f"   {status} {claim['claim_type']}: {claim['duration']:.2f}s - \"{claim['claim_text']}\"")
        
        print("\n" + "="*90 + "\n")

# Global checkpoint monitor instance
global_checkpoint_monitor = CheckpointMonitor()

def get_checkpoint_monitor() -> CheckpointMonitor:
    """Get the global checkpoint monitor instance"""
    return global_checkpoint_monitor

class TimedCheckpoint:
    """Context manager for timing checkpoints"""
    
    def __init__(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata
        self.checkpoint_id = None
        self.monitor = get_checkpoint_monitor()
    
    def __enter__(self):
        self.checkpoint_id = self.monitor.start_checkpoint(self.name, self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        self.monitor.end_checkpoint(self.checkpoint_id, success, error_message)

# Convenience functions for easier integration
def start_checkpoint(name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Start a checkpoint timing"""
    return get_checkpoint_monitor().start_checkpoint(name, metadata)

def end_checkpoint(checkpoint_id: str, success: bool = True, error_message: Optional[str] = None):
    """End a checkpoint timing"""
    get_checkpoint_monitor().end_checkpoint(checkpoint_id, success, error_message)

def add_claim_report(claim_id: str, claim_text: str, claim_type: str, 
                     checkpoints: List[CheckpointTiming], success: bool):
    """Add a completed claim processing report"""
    get_checkpoint_monitor().add_claim_report(claim_id, claim_text, claim_type, checkpoints, success)