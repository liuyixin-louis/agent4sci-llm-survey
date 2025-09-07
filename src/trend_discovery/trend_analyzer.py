"""
Trend Analyzer for Research Paper Temporal Patterns
Analyzes publication velocity and acceleration to identify hot topics
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes temporal patterns in research publications.
    Uses velocity (papers/month) and acceleration metrics.
    """
    
    def __init__(self):
        """Initialize trend analyzer."""
        self.current_year = 2024
        self.current_month = 9
        
    def calculate_velocity(
        self,
        papers: List[Dict],
        window_months: int = 6
    ) -> float:
        """
        Calculate publication velocity (papers per month).
        
        Args:
            papers: List of papers with temporal info
            window_months: Time window for calculation
            
        Returns:
            Papers per month rate
        """
        if not papers:
            return 0.0
        
        # Count papers in window
        recent_count = 0
        for paper in papers:
            year = paper.get('year', 0)
            month = paper.get('month', 1)
            
            # Simple recency check
            months_ago = (self.current_year - year) * 12 + (self.current_month - month)
            if months_ago <= window_months:
                recent_count += 1
        
        return recent_count / window_months if window_months > 0 else 0
    
    def calculate_acceleration(
        self,
        papers: List[Dict],
        window_months: int = 3
    ) -> float:
        """
        Calculate publication acceleration (change in velocity).
        
        Args:
            papers: List of papers
            window_months: Window for each velocity calculation
            
        Returns:
            Acceleration in papers/month²
        """
        # Calculate velocity for two periods
        recent_velocity = self.calculate_velocity(papers, window_months)
        
        # Filter for older period
        older_papers = []
        for paper in papers:
            year = paper.get('year', 0)
            month = paper.get('month', 1)
            months_ago = (self.current_year - year) * 12 + (self.current_month - month)
            if window_months < months_ago <= window_months * 2:
                older_papers.append(paper)
        
        older_velocity = len(older_papers) / window_months if window_months > 0 else 0
        
        # Acceleration is change in velocity
        return (recent_velocity - older_velocity) / window_months
    
    def identify_trends(
        self,
        papers: List[Dict],
        classifications: Dict[str, str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Identify trending topics based on velocity and acceleration.
        
        Args:
            papers: List of papers
            classifications: Paper title to category mapping
            
        Returns:
            Dict of category to trend metrics
        """
        # Group papers by category
        category_papers = defaultdict(list)
        for paper in papers:
            title = paper.get('title', '')
            if title in classifications:
                category = classifications[title]
                category_papers[category].append(paper)
        
        # Calculate metrics for each category
        trends = {}
        for category, cat_papers in category_papers.items():
            velocity = self.calculate_velocity(cat_papers, window_months=6)
            acceleration = self.calculate_acceleration(cat_papers, window_months=3)
            
            trends[category] = {
                'velocity': velocity,
                'acceleration': acceleration,
                'total_papers': len(cat_papers),
                'recent_count': sum(1 for p in cat_papers 
                                  if p.get('year', 0) >= self.current_year - 1)
            }
        
        return trends
    
    def get_hot_topics(
        self,
        papers: List[Dict],
        classifications: Dict[str, str],
        top_n: int = 5
    ) -> List[Tuple[str, Dict]]:
        """
        Get the hottest research topics.
        
        Args:
            papers: Papers to analyze
            classifications: Category mappings
            top_n: Number of top topics
            
        Returns:
            List of (category, metrics) tuples
        """
        trends = self.identify_trends(papers, classifications)
        
        # Score based on velocity and positive acceleration
        scored = []
        for category, metrics in trends.items():
            # Higher velocity is better
            # Positive acceleration is a bonus
            score = metrics['velocity'] + max(0, metrics['acceleration'] * 2)
            scored.append((category, metrics, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[2], reverse=True)
        
        return [(cat, metrics) for cat, metrics, _ in scored[:top_n]]
    
    def generate_trend_report(
        self,
        papers: List[Dict],
        classifications: Dict[str, str]
    ) -> Dict:
        """
        Generate comprehensive trend analysis report.
        
        Args:
            papers: Papers to analyze
            classifications: Category mappings
            
        Returns:
            Trend report dict
        """
        trends = self.identify_trends(papers, classifications)
        hot_topics = self.get_hot_topics(papers, classifications, top_n=5)
        
        # Calculate overall statistics
        total_papers = len(papers)
        recent_papers = sum(1 for p in papers 
                          if p.get('year', 0) >= self.current_year - 1)
        
        report = {
            'summary': {
                'total_papers_analyzed': total_papers,
                'recent_papers': recent_papers,
                'categories_identified': len(trends),
                'analysis_date': f"{self.current_year}-{self.current_month:02d}"
            },
            'hot_topics': [
                {
                    'category': cat,
                    'velocity': metrics['velocity'],
                    'acceleration': metrics['acceleration'],
                    'recent_papers': metrics['recent_count']
                }
                for cat, metrics in hot_topics
            ],
            'category_trends': trends,
            'recommendations': self._generate_recommendations(hot_topics)
        }
        
        return report
    
    def _generate_recommendations(
        self,
        hot_topics: List[Tuple[str, Dict]]
    ) -> List[str]:
        """
        Generate survey topic recommendations.
        
        Args:
            hot_topics: List of trending topics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for category, metrics in hot_topics[:3]:
            if metrics['velocity'] > 1.0:
                recommendations.append(
                    f"'{category}' is highly active with {metrics['velocity']:.1f} papers/month - "
                    f"excellent for comprehensive survey"
                )
            elif metrics['acceleration'] > 0.1:
                recommendations.append(
                    f"'{category}' shows rapid growth (acceleration: {metrics['acceleration']:.2f}) - "
                    f"good for emerging trends survey"
                )
            elif metrics['recent_count'] > 10:
                recommendations.append(
                    f"'{category}' has {metrics['recent_count']} recent papers - "
                    f"sufficient for focused survey"
                )
        
        return recommendations