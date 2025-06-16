"""
Advanced authenticity scoring system for fact-checked claims
"""
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .config import SCORING_WEIGHTS

logger = logging.getLogger(__name__)

class AuthenticityLevel(Enum):
    """Authenticity levels with score ranges"""
    VERIFIED = "verified"           # 0.8 - 1.0
    LIKELY_TRUE = "likely_true"     # 0.6 - 0.8
    UNCERTAIN = "uncertain"         # 0.4 - 0.6
    LIKELY_FALSE = "likely_false"   # 0.2 - 0.4
    FALSE = "false"                 # 0.0 - 0.2

@dataclass
class ScoringBreakdown:
    """Detailed breakdown of authenticity scoring"""
    source_credibility_score: float
    cross_reference_score: float
    evidence_quality_score: float
    publication_date_score: float
    expert_consensus_score: float
    final_score: float
    authenticity_level: AuthenticityLevel
    confidence_interval: Tuple[float, float]
    explanation: str

class AuthenticityScorer:
    """Advanced authenticity scoring system"""
    
    def __init__(self):
        """Initialize the authenticity scorer"""
        self.weights = SCORING_WEIGHTS
        
        # Source credibility ratings (expanded)
        self.source_credibility_db = {
            # Government and Official Sources
            'who.int': 0.98,
            'cdc.gov': 0.98,
            'nih.gov': 0.98,
            'fda.gov': 0.95,
            'sec.gov': 0.95,
            'federalreserve.gov': 0.95,
            'treasury.gov': 0.95,
            
            # Academic and Scientific
            'nature.com': 0.95,
            'science.org': 0.95,
            'ncbi.nlm.nih.gov': 0.95,
            'pubmed.ncbi.nlm.nih.gov': 0.95,
            'scholar.google.com': 0.90,
            'researchgate.net': 0.85,
            'arxiv.org': 0.80,
            
            # News and Media (Tier 1)
            'reuters.com': 0.92,
            'apnews.com': 0.92,
            'bbc.com': 0.90,
            'npr.org': 0.88,
            'pbs.org': 0.88,
            
            # Fact-Checking Organizations
            'factcheck.org': 0.90,
            'politifact.com': 0.88,
            'snopes.com': 0.85,
            'fullfact.org': 0.87,
            'checkyourfact.com': 0.82,
            
            # Financial News (Tier 1)
            'bloomberg.com': 0.88,
            'wsj.com': 0.87,
            'ft.com': 0.86,
            'marketwatch.com': 0.82,
            
            # Technology News (Tier 1)
            'ieee.org': 0.90,
            'acm.org': 0.88,
            'arstechnica.com': 0.82,
            'wired.com': 0.80,
            
            # Medical Sources
            'mayoclinic.org': 0.90,
            'clevelandclinic.org': 0.88,
            'webmd.com': 0.75,
            'healthline.com': 0.72,
            
            # General credible sources
            'economist.com': 0.85,
            'theguardian.com': 0.82,
            'nytimes.com': 0.82,
            'washingtonpost.com': 0.80,
        }
        
        # Domain-specific expertise weights
        self.domain_expertise = {
            'medical': ['who.int', 'cdc.gov', 'nih.gov', 'mayoclinic.org'],
            'scientific': ['nature.com', 'science.org', 'ncbi.nlm.nih.gov'],
            'political': ['factcheck.org', 'politifact.com', 'apnews.com'],
            'financial': ['sec.gov', 'federalreserve.gov', 'bloomberg.com', 'wsj.com'],
            'technology': ['ieee.org', 'acm.org', 'arstechnica.com']
        }
    
    def calculate_authenticity_score(
        self, 
        claim_text: str,
        claim_type: str,
        sources: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        claim_entities: List[str] = None
    ) -> ScoringBreakdown:
        """
        Calculate comprehensive authenticity score
        
        Args:
            claim_text: The original claim text
            claim_type: Type of claim (medical, political, etc.)
            sources: List of sources that were checked
            evidence: Supporting evidence found
            contradictions: Contradictory evidence found
            claim_entities: Named entities in the claim
            
        Returns:
            ScoringBreakdown with detailed scoring information
        """
        logger.info(f"Calculating authenticity score for {claim_type} claim")
        
        # Calculate individual scoring components
        source_credibility_score = self._calculate_source_credibility_score(
            sources, claim_type
        )
        
        cross_reference_score = self._calculate_cross_reference_score(
            sources, evidence, contradictions
        )
        
        evidence_quality_score = self._calculate_evidence_quality_score(
            evidence, contradictions, claim_text
        )
        
        publication_date_score = self._calculate_publication_date_score(sources)
        
        expert_consensus_score = self._calculate_expert_consensus_score(
            sources, evidence, contradictions, claim_type
        )
        
        # Calculate weighted final score
        final_score = (
            source_credibility_score * self.weights['source_credibility'] +
            cross_reference_score * self.weights['cross_reference_consistency'] +
            evidence_quality_score * self.weights['evidence_quality'] +
            publication_date_score * self.weights['publication_date_relevance'] +
            expert_consensus_score * self.weights['expert_consensus']
        )
        
        # **CRITICAL FIX**: Apply severe penalty for numerical contradictions
        numerical_contradiction_penalty = 0.0
        for contra in contradictions:
            if contra.get('contradiction_type') == 'numerical_contradiction':
                # Numerical contradictions (wrong IDs, numbers) should severely impact score
                # The more credible the source, the bigger the penalty
                source_credibility = contra.get('source_credibility', 0.5)
                numerical_contradiction_penalty += 0.4 * source_credibility  # Up to 0.4 penalty per numerical contradiction
        
        # Apply the numerical contradiction penalty
        final_score -= numerical_contradiction_penalty
        
        # For numerical contradictions, cap the maximum score to "uncertain" level
        if numerical_contradiction_penalty > 0:
            final_score = min(final_score, 0.55)  # Cap at upper "uncertain" range
        
        # Ensure score is within bounds
        final_score = max(0.0, min(1.0, final_score))
        
        # Determine authenticity level
        authenticity_level = self._get_authenticity_level(final_score)
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            final_score, len(sources), len(evidence), len(contradictions)
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_score, authenticity_level, sources, evidence, contradictions
        )
        
        return ScoringBreakdown(
            source_credibility_score=source_credibility_score,
            cross_reference_score=cross_reference_score,
            evidence_quality_score=evidence_quality_score,
            publication_date_score=publication_date_score,
            expert_consensus_score=expert_consensus_score,
            final_score=final_score,
            authenticity_level=authenticity_level,
            confidence_interval=confidence_interval,
            explanation=explanation
        )
    
    def _calculate_source_credibility_score(
        self, 
        sources: List[Dict[str, Any]], 
        claim_type: str
    ) -> float:
        """Calculate score based on source credibility"""
        if not sources:
            return 0.0
        
        total_credibility = 0.0
        domain_expertise_bonus = 0.0
        
        for source in sources:
            domain = source.get('domain', '')
            base_credibility = self.source_credibility_db.get(domain, 0.5)
            
            # Bonus for domain expertise
            if claim_type in self.domain_expertise:
                if domain in self.domain_expertise[claim_type]:
                    base_credibility = min(1.0, base_credibility + 0.05)
                    domain_expertise_bonus += 0.02
            
            total_credibility += base_credibility
        
        avg_credibility = total_credibility / len(sources)
        
        # Apply diminishing returns for multiple sources
        source_count_factor = min(1.0, math.log(len(sources) + 1) / math.log(5))
        
        final_score = avg_credibility * source_count_factor + domain_expertise_bonus
        return min(1.0, final_score)
    
    def _calculate_cross_reference_score(
        self, 
        sources: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]]
    ) -> float:
        """Calculate score based on cross-reference consistency"""
        if len(sources) < 2:
            return 0.3  # Low score for single source
        
        # Base score increases with number of sources
        base_score = min(0.8, len(sources) * 0.15)
        
        # Consistency bonus
        consistency_bonus = 0.0
        if evidence and not contradictions:
            consistency_bonus = 0.2
        elif evidence and contradictions:
            evidence_strength = sum(e.get('relevance_score', 0.5) for e in evidence)
            contradiction_strength = sum(c.get('relevance_score', 0.5) for c in contradictions)
            
            if evidence_strength > contradiction_strength * 1.5:
                consistency_bonus = 0.1
            elif contradiction_strength > evidence_strength * 1.5:
                consistency_bonus = -0.1
        
        # Diversity bonus (different domains)
        unique_domains = len(set(s.get('domain', '') for s in sources))
        diversity_bonus = min(0.15, unique_domains * 0.03)
        
        final_score = base_score + consistency_bonus + diversity_bonus
        return max(0.0, min(1.0, final_score))
    
    def _calculate_evidence_quality_score(
        self, 
        evidence: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        claim_text: str
    ) -> float:
        """Calculate score based on evidence quality"""
        if not evidence and not contradictions:
            return 0.2  # No evidence found
        
        evidence_score = 0.0
        if evidence:
            # Quality based on relevance and source credibility
            for ev in evidence:
                relevance = ev.get('relevance_score', 0.5)
                source_credibility = ev.get('source_credibility', 0.5)
                evidence_score += relevance * source_credibility
            
            evidence_score = evidence_score / len(evidence)
        
        contradiction_penalty = 0.0
        if contradictions:
            for contra in contradictions:
                relevance = contra.get('relevance_score', 0.5)
                source_credibility = contra.get('source_credibility', 0.5)
                base_penalty = relevance * source_credibility
                
                # **CRITICAL FIX**: Numerical contradictions should have severe penalty
                contradiction_type = contra.get('contradiction_type', '')
                if contradiction_type == 'numerical_contradiction':
                    # Numerical contradictions (like wrong ID numbers) are highly damaging
                    base_penalty *= 3.0  # Triple the penalty for numerical contradictions
                elif contradiction_type == 'regulatory_contradiction':
                    # Regulatory contradictions are also serious
                    base_penalty *= 2.5
                elif contradiction_type == 'direct_negation':
                    # Direct negations are serious
                    base_penalty *= 2.0
                
                contradiction_penalty += base_penalty
            
            contradiction_penalty = contradiction_penalty / len(contradictions)
        
        # Evidence specificity bonus
        specificity_bonus = self._calculate_evidence_specificity(evidence, claim_text)
        
        final_score = evidence_score + specificity_bonus - contradiction_penalty
        return max(0.0, min(1.0, final_score))
    
    def _calculate_evidence_specificity(
        self, 
        evidence: List[Dict[str, Any]], 
        claim_text: str
    ) -> float:
        """Calculate bonus for specific, detailed evidence"""
        if not evidence:
            return 0.0
        
        specificity_indicators = [
            'study', 'research', 'data', 'statistics', 'percent', '%',
            'according to', 'found that', 'shows that', 'indicates',
            'published', 'journal', 'peer-reviewed'
        ]
        
        specificity_score = 0.0
        for ev in evidence:
            text = ev.get('text', '').lower()
            matches = sum(1 for indicator in specificity_indicators if indicator in text)
            specificity_score += min(0.1, matches * 0.02)
        
        return min(0.15, specificity_score)
    
    def _calculate_publication_date_score(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate score based on publication date relevance"""
        if not sources:
            return 0.5
        
        current_date = datetime.now()
        total_score = 0.0
        scored_sources = 0
        
        for source in sources:
            pub_date_str = source.get('publication_date')
            if not pub_date_str:
                total_score += 0.5  # Neutral score for unknown date
                scored_sources += 1
                continue
            
            try:
                pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                days_old = (current_date - pub_date).days
                
                # Score based on recency
                if days_old <= 30:
                    score = 1.0  # Very recent
                elif days_old <= 365:
                    score = 0.9  # Recent
                elif days_old <= 365 * 3:
                    score = 0.7  # Somewhat old
                elif days_old <= 365 * 10:
                    score = 0.5  # Old but potentially relevant
                else:
                    score = 0.3  # Very old
                
                total_score += score
                scored_sources += 1
                
            except Exception:
                total_score += 0.5  # Neutral for invalid date
                scored_sources += 1
        
        return total_score / scored_sources if scored_sources > 0 else 0.5
    
    def _calculate_expert_consensus_score(
        self, 
        sources: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        claim_type: str
    ) -> float:
        """Calculate score based on expert consensus"""
        expert_sources = []
        
        # Identify expert sources for the claim type
        for source in sources:
            domain = source.get('domain', '')
            if claim_type in self.domain_expertise:
                if domain in self.domain_expertise[claim_type]:
                    expert_sources.append(source)
            
            # High-credibility sources are considered expert sources
            if self.source_credibility_db.get(domain, 0) >= 0.85:
                expert_sources.append(source)
        
        if not expert_sources:
            return 0.5  # No expert sources, neutral score
        
        # Calculate consensus among expert sources
        supporting_experts = 0
        contradicting_experts = 0
        
        for expert in expert_sources:
            expert_domain = expert.get('domain', '')
            
            # Check if this expert source provided evidence or contradictions
            expert_evidence = [e for e in evidence if expert_domain in e.get('source_url', '')]
            expert_contradictions = [c for c in contradictions if expert_domain in c.get('source_url', '')]
            
            if expert_evidence and not expert_contradictions:
                supporting_experts += 1
            elif expert_contradictions and not expert_evidence:
                contradicting_experts += 1
            # If both or neither, we don't count toward consensus
        
        total_experts = supporting_experts + contradicting_experts
        if total_experts == 0:
            return 0.6  # Experts present but no clear position
        
        # Calculate consensus score
        if supporting_experts > contradicting_experts:
            consensus_ratio = supporting_experts / total_experts
            return min(1.0, 0.5 + consensus_ratio * 0.5)
        elif contradicting_experts > supporting_experts:
            consensus_ratio = contradicting_experts / total_experts
            return max(0.0, 0.5 - consensus_ratio * 0.5)
        else:
            return 0.5  # Split consensus
    
    def _get_authenticity_level(self, score: float) -> AuthenticityLevel:
        """Convert score to authenticity level"""
        if score >= 0.8:
            return AuthenticityLevel.VERIFIED
        elif score >= 0.6:
            return AuthenticityLevel.LIKELY_TRUE
        elif score >= 0.4:
            return AuthenticityLevel.UNCERTAIN
        elif score >= 0.2:
            return AuthenticityLevel.LIKELY_FALSE
        else:
            return AuthenticityLevel.FALSE
    
    def _calculate_confidence_interval(
        self, 
        score: float, 
        num_sources: int, 
        num_evidence: int, 
        num_contradictions: int
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the score"""
        # Confidence increases with more data
        data_points = num_sources + num_evidence + num_contradictions
        
        if data_points == 0:
            margin = 0.5  # Very uncertain
        elif data_points < 3:
            margin = 0.3  # High uncertainty
        elif data_points < 6:
            margin = 0.2  # Moderate uncertainty
        elif data_points < 10:
            margin = 0.15  # Low uncertainty
        else:
            margin = 0.1  # Very confident
        
        lower_bound = max(0.0, score - margin)
        upper_bound = min(1.0, score + margin)
        
        return (lower_bound, upper_bound)
    
    def _generate_explanation(
        self, 
        score: float,
        level: AuthenticityLevel,
        sources: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation of the score"""
        explanations = []
        
        # Overall assessment
        if level == AuthenticityLevel.VERIFIED:
            explanations.append("This claim is highly likely to be accurate.")
        elif level == AuthenticityLevel.LIKELY_TRUE:
            explanations.append("This claim appears to be mostly accurate.")
        elif level == AuthenticityLevel.UNCERTAIN:
            explanations.append("The accuracy of this claim is uncertain.")
        elif level == AuthenticityLevel.LIKELY_FALSE:
            explanations.append("This claim appears to be mostly inaccurate.")
        else:
            explanations.append("This claim is highly likely to be false.")
        
        # Source analysis
        if sources:
            high_credibility_sources = [s for s in sources if self.source_credibility_db.get(s.get('domain', ''), 0) >= 0.8]
            if high_credibility_sources:
                explanations.append(f"Verified by {len(high_credibility_sources)} high-credibility sources.")
            else:
                explanations.append(f"Based on {len(sources)} sources of varying credibility.")
        
        # Evidence analysis with special handling for numerical contradictions
        numerical_contradictions = [c for c in contradictions if c.get('contradiction_type') == 'numerical_contradiction']
        
        if numerical_contradictions:
            # Highlight numerical contradictions as they're very serious
            explanations.append(f"CRITICAL: Found {len(numerical_contradictions)} numerical contradiction(s) with specific numbers/IDs that don't match the claim.")
            if evidence:
                explanations.append(f"Despite {len(evidence)} supporting evidence items, the numerical contradictions significantly impact authenticity.")
        elif evidence and contradictions:
            explanations.append(f"Found {len(evidence)} supporting evidence items and {len(contradictions)} contradictions.")
        elif evidence:
            explanations.append(f"Supported by {len(evidence)} pieces of evidence.")
        elif contradictions:
            explanations.append(f"Contradicted by {len(contradictions)} sources.")
        else:
            explanations.append("Limited evidence available for verification.")
        
        return " ".join(explanations)
    
    def get_score_interpretation(self, score: float) -> Dict[str, Any]:
        """Get interpretation of authenticity score"""
        level = self._get_authenticity_level(score)
        
        interpretation = {
            'score': score,
            'level': level.value,
            'percentage': f"{score * 100:.1f}%",
            'recommendation': self._get_recommendation(level),
            'color_code': self._get_color_code(level)
        }
        
        return interpretation
    
    def _get_recommendation(self, level: AuthenticityLevel) -> str:
        """Get recommendation based on authenticity level"""
        recommendations = {
            AuthenticityLevel.VERIFIED: "Safe to share and cite as accurate information.",
            AuthenticityLevel.LIKELY_TRUE: "Generally reliable, but consider cross-checking with additional sources.",
            AuthenticityLevel.UNCERTAIN: "Requires additional verification before sharing or citing.",
            AuthenticityLevel.LIKELY_FALSE: "Exercise caution - this claim appears to be inaccurate.",
            AuthenticityLevel.FALSE: "Do not share - this claim is likely false or misleading."
        }
        return recommendations[level]
    
    def _get_color_code(self, level: AuthenticityLevel) -> str:
        """Get color code for UI display"""
        colors = {
            AuthenticityLevel.VERIFIED: "#28a745",      # Green
            AuthenticityLevel.LIKELY_TRUE: "#17a2b8",   # Blue
            AuthenticityLevel.UNCERTAIN: "#ffc107",     # Yellow
            AuthenticityLevel.LIKELY_FALSE: "#fd7e14",  # Orange
            AuthenticityLevel.FALSE: "#dc3545"          # Red
        }
        return colors[level]