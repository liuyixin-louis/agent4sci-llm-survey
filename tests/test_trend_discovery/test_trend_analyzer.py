"""
Unit tests for Trend Analyzer
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.trend_discovery.trend_analyzer import TrendAnalyzer


class TestTrendAnalyzer:
    """Test suite for trend analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return TrendAnalyzer()
    
    @pytest.fixture
    def sample_papers(self):
        """Create sample papers with temporal data."""
        return [
            # Recent papers (high velocity)
            {'title': 'Paper1', 'year': 2024, 'month': 8},
            {'title': 'Paper2', 'year': 2024, 'month': 8},
            {'title': 'Paper3', 'year': 2024, 'month': 7},
            {'title': 'Paper4', 'year': 2024, 'month': 7},
            {'title': 'Paper5', 'year': 2024, 'month': 6},
            
            # Older papers
            {'title': 'Paper6', 'year': 2024, 'month': 3},
            {'title': 'Paper7', 'year': 2024, 'month': 1},
            {'title': 'Paper8', 'year': 2023, 'month': 12},
            {'title': 'Paper9', 'year': 2023, 'month': 11},
            {'title': 'Paper10', 'year': 2023, 'month': 6},
        ]
    
    @pytest.fixture
    def classifications(self):
        """Create sample classifications."""
        return {
            'Paper1': 'Alignment',
            'Paper2': 'Alignment',
            'Paper3': 'Alignment',
            'Paper4': 'Reasoning',
            'Paper5': 'Reasoning',
            'Paper6': 'Reasoning',
            'Paper7': 'Multimodal Models',
            'Paper8': 'Multimodal Models',
            'Paper9': 'Tools and Code',
            'Paper10': 'Tools and Code',
        }
    
    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer is not None
        assert analyzer.current_year == 2024
        assert analyzer.current_month == 9
    
    def test_calculate_velocity_recent(self, analyzer):
        """Test velocity calculation for recent papers."""
        recent_papers = [
            {'year': 2024, 'month': 9},
            {'year': 2024, 'month': 8},
            {'year': 2024, 'month': 8},
            {'year': 2024, 'month': 7},
        ]
        
        velocity = analyzer.calculate_velocity(recent_papers, window_months=3)
        
        # 4 papers in 3 months = 1.33 papers/month
        assert velocity == pytest.approx(4/3, rel=0.01)
    
    def test_calculate_velocity_empty(self, analyzer):
        """Test velocity with no papers."""
        velocity = analyzer.calculate_velocity([], window_months=6)
        assert velocity == 0.0
    
    def test_calculate_velocity_old_papers(self, analyzer):
        """Test velocity with only old papers."""
        old_papers = [
            {'year': 2020, 'month': 1},
            {'year': 2019, 'month': 12},
        ]
        
        velocity = analyzer.calculate_velocity(old_papers, window_months=6)
        assert velocity == 0.0  # No recent papers
    
    def test_calculate_acceleration_positive(self, analyzer):
        """Test positive acceleration (increasing velocity)."""
        papers = [
            # Recent period: 3 papers
            {'year': 2024, 'month': 9},
            {'year': 2024, 'month': 8},
            {'year': 2024, 'month': 8},
            # Older period: 1 paper
            {'year': 2024, 'month': 5},
        ]
        
        acceleration = analyzer.calculate_acceleration(papers, window_months=3)
        
        # Recent velocity: 3/3 = 1.0
        # Older velocity: 1/3 = 0.33
        # Acceleration: (1.0 - 0.33) / 3 = 0.22
        assert acceleration > 0  # Positive acceleration
    
    def test_calculate_acceleration_negative(self, analyzer):
        """Test negative acceleration (decreasing velocity)."""
        papers = [
            # Recent period: 1 paper
            {'year': 2024, 'month': 8},
            # Older period: 3 papers
            {'year': 2024, 'month': 5},
            {'year': 2024, 'month': 4},
            {'year': 2024, 'month': 4},
        ]
        
        acceleration = analyzer.calculate_acceleration(papers, window_months=3)
        assert acceleration < 0  # Negative acceleration
    
    def test_identify_trends(self, analyzer, sample_papers, classifications):
        """Test trend identification."""
        trends = analyzer.identify_trends(sample_papers, classifications)
        
        assert isinstance(trends, dict)
        assert 'Alignment' in trends
        assert 'Reasoning' in trends
        
        # Check structure of trend metrics
        for category, metrics in trends.items():
            assert 'velocity' in metrics
            assert 'acceleration' in metrics
            assert 'total_papers' in metrics
            assert 'recent_count' in metrics
            assert metrics['total_papers'] > 0
    
    def test_get_hot_topics(self, analyzer, sample_papers, classifications):
        """Test hot topic identification."""
        hot_topics = analyzer.get_hot_topics(sample_papers, classifications, top_n=3)
        
        assert len(hot_topics) <= 3
        for category, metrics in hot_topics:
            assert isinstance(category, str)
            assert isinstance(metrics, dict)
            assert 'velocity' in metrics
    
    def test_generate_trend_report(self, analyzer, sample_papers, classifications):
        """Test comprehensive trend report generation."""
        report = analyzer.generate_trend_report(sample_papers, classifications)
        
        assert 'summary' in report
        assert 'hot_topics' in report
        assert 'category_trends' in report
        assert 'recommendations' in report
        
        # Check summary structure
        summary = report['summary']
        assert 'total_papers_analyzed' in summary
        assert 'recent_papers' in summary
        assert 'categories_identified' in summary
        assert summary['total_papers_analyzed'] == len(sample_papers)
    
    def test_recommendations_generation(self, analyzer):
        """Test recommendation generation."""
        hot_topics = [
            ('Alignment', {'velocity': 2.5, 'acceleration': 0.3, 'recent_count': 15}),
            ('Reasoning', {'velocity': 0.5, 'acceleration': 0.2, 'recent_count': 5}),
            ('Tools', {'velocity': 0.8, 'acceleration': -0.1, 'recent_count': 12}),
        ]
        
        recommendations = analyzer._generate_recommendations(hot_topics)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        assert all(isinstance(r, str) for r in recommendations)
        assert any('Alignment' in r for r in recommendations)
    
    def test_empty_classifications(self, analyzer, sample_papers):
        """Test with empty classifications."""
        empty_classifications = {}
        trends = analyzer.identify_trends(sample_papers, empty_classifications)
        
        assert trends == {}
    
    def test_single_category_dominance(self, analyzer):
        """Test when single category dominates."""
        papers = [
            {'title': f'Paper{i}', 'year': 2024, 'month': 9-i}
            for i in range(5)
        ]
        
        classifications = {f'Paper{i}': 'Alignment' for i in range(5)}
        
        hot_topics = analyzer.get_hot_topics(papers, classifications, top_n=3)
        
        assert len(hot_topics) == 1
        assert hot_topics[0][0] == 'Alignment'
    
    @pytest.mark.parametrize("window_months", [1, 3, 6, 12])
    def test_different_window_sizes(self, analyzer, sample_papers, window_months):
        """Test with different time windows."""
        velocity = analyzer.calculate_velocity(sample_papers, window_months)
        
        assert velocity >= 0
        assert velocity <= len(sample_papers) / window_months


class TestTrendAnalyzerIntegration:
    """Integration tests for trend analyzer."""
    
    def test_full_analysis_workflow(self):
        """Test complete trend analysis workflow."""
        analyzer = TrendAnalyzer()
        
        # Create realistic paper distribution
        papers = []
        categories = ['Alignment', 'Reasoning', 'Tools and Code', 'Multimodal Models']
        
        for month in range(1, 10):
            for cat_idx, category in enumerate(categories):
                # Varying publication rates
                count = (4 - cat_idx) if month >= 6 else 1
                for _ in range(count):
                    papers.append({
                        'title': f'{category}_Paper_{month}_{_}',
                        'year': 2024,
                        'month': month
                    })
        
        # Create classifications
        classifications = {
            paper['title']: paper['title'].split('_')[0]
            for paper in papers
        }
        
        # Generate full report
        report = analyzer.generate_trend_report(papers, classifications)
        
        assert report['summary']['total_papers_analyzed'] == len(papers)
        assert len(report['hot_topics']) > 0
        assert len(report['recommendations']) > 0
        
        # Verify Alignment is top trending (highest publication rate)
        top_topic = report['hot_topics'][0]
        assert top_topic['category'] == 'Alignment'
        assert top_topic['velocity'] > 0
    
    def test_temporal_pattern_detection(self):
        """Test detection of temporal patterns."""
        analyzer = TrendAnalyzer()
        
        # Create papers with clear temporal pattern
        # Surge in month 7-9, quiet in 1-6
        papers = []
        for month in range(1, 10):
            count = 5 if month >= 7 else 1
            for i in range(count):
                papers.append({
                    'title': f'Paper_{month}_{i}',
                    'year': 2024,
                    'month': month
                })
        
        classifications = {p['title']: 'TestCategory' for p in papers}
        
        trends = analyzer.identify_trends(papers, classifications)
        
        # Should detect high recent velocity
        assert trends['TestCategory']['velocity'] > 1.0
        # Should detect positive acceleration
        assert trends['TestCategory']['acceleration'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])