"""
Comprehensive tests for evaluation metrics
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.evaluation.metrics import (
    CitationMetrics,
    ContentQualityMetrics,
    PerformanceMetrics,
    ComprehensiveEvaluator
)


class TestCitationMetrics:
    """Test suite for citation metrics"""
    
    @pytest.fixture
    def citation_metrics(self):
        """Create CitationMetrics instance"""
        return CitationMetrics()
    
    @pytest.fixture
    def sample_survey(self):
        """Sample survey with citations"""
        return {
            "sections": [
                {
                    "title": "Introduction",
                    "content": "Recent work [1] shows that LLMs [2] are effective.",
                    "citations": ["Paper1", "Paper2"]
                },
                {
                    "title": "Methods",
                    "content": "We use technique from [3] and improve on [4].",
                    "citations": ["Paper3", "Paper4"]
                }
            ]
        }
    
    @pytest.fixture
    def sample_papers(self):
        """Sample papers for testing"""
        return [
            {"title": "Paper1", "abstract": "About LLMs"},
            {"title": "Paper2", "abstract": "Language models"},
            {"title": "Paper3", "abstract": "Methodology"},
            {"title": "Paper4", "abstract": "Improvements"},
            {"title": "Paper5", "abstract": "Uncited paper"}
        ]
    
    def test_citation_recall(self, citation_metrics, sample_survey, sample_papers):
        """Test citation recall calculation"""
        recall = citation_metrics.calculate_recall(sample_survey, sample_papers)
        
        # 4 out of 5 papers cited
        assert recall == pytest.approx(0.8, rel=1e-3)
    
    def test_citation_precision(self, citation_metrics, sample_survey, sample_papers):
        """Test citation precision calculation"""
        precision = citation_metrics.calculate_precision(sample_survey, sample_papers)
        
        # All 4 citations are valid
        assert precision == 1.0
    
    def test_citation_f1_score(self, citation_metrics, sample_survey, sample_papers):
        """Test F1 score calculation"""
        f1 = citation_metrics.calculate_f1(sample_survey, sample_papers)
        
        # F1 = 2 * (0.8 * 1.0) / (0.8 + 1.0)
        expected_f1 = 2 * 0.8 / 1.8
        assert f1 == pytest.approx(expected_f1, rel=1e-3)
    
    def test_empty_citations(self, citation_metrics):
        """Test metrics with no citations"""
        empty_survey = {"sections": [{"content": "No citations here"}]}
        papers = [{"title": "Paper1"}]
        
        recall = citation_metrics.calculate_recall(empty_survey, papers)
        assert recall == 0.0
        
        precision = citation_metrics.calculate_precision(empty_survey, papers)
        assert precision == 0.0
    
    def test_citation_distribution(self, citation_metrics, sample_survey):
        """Test citation distribution analysis"""
        distribution = citation_metrics.analyze_distribution(sample_survey)
        
        assert distribution["total_citations"] == 4
        assert distribution["sections_with_citations"] == 2
        assert distribution["avg_citations_per_section"] == 2.0
    
    @pytest.mark.parametrize("survey,papers,expected_recall", [
        ({"sections": []}, [{"title": "P1"}], 0.0),
        ({"sections": [{"citations": ["P1"]}]}, [{"title": "P1"}], 1.0),
        ({"sections": [{"citations": ["P1", "P2"]}]}, [{"title": "P1"}, {"title": "P2"}, {"title": "P3"}], 0.667),
    ])
    def test_recall_parametrized(self, citation_metrics, survey, papers, expected_recall):
        """Test recall with various inputs"""
        recall = citation_metrics.calculate_recall(survey, papers)
        assert recall == pytest.approx(expected_recall, rel=1e-2)


class TestContentQualityMetrics:
    """Test suite for content quality metrics"""
    
    @pytest.fixture
    def quality_metrics(self):
        """Create ContentQualityMetrics instance"""
        return ContentQualityMetrics()
    
    @pytest.fixture
    def high_quality_survey(self):
        """High quality survey sample"""
        return {
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This comprehensive introduction provides detailed background on the topic. " * 50,
                    "subsections": ["Background", "Motivation", "Contributions"]
                },
                {
                    "title": "Related Work",
                    "content": "We review extensive prior work in multiple areas. " * 100,
                    "subsections": ["Area 1", "Area 2", "Area 3"]
                }
            ]
        }
    
    @pytest.fixture
    def low_quality_survey(self):
        """Low quality survey sample"""
        return {
            "sections": [
                {
                    "title": "Intro",
                    "content": "Short intro."
                },
                {
                    "title": "Work",
                    "content": "Some work."
                }
            ]
        }
    
    def test_coverage_score(self, quality_metrics, high_quality_survey):
        """Test coverage scoring"""
        score = quality_metrics.calculate_coverage(high_quality_survey)
        
        # High quality survey should have high coverage
        assert score >= 4.0
    
    def test_coherence_score(self, quality_metrics, high_quality_survey):
        """Test coherence scoring"""
        score = quality_metrics.calculate_coherence(high_quality_survey)
        
        # Well-structured survey should have good coherence
        assert score >= 3.5
    
    def test_structure_score(self, quality_metrics, high_quality_survey):
        """Test structure scoring"""
        score = quality_metrics.calculate_structure(high_quality_survey)
        
        # Survey with subsections should have good structure
        assert score >= 4.0
    
    def test_low_quality_scores(self, quality_metrics, low_quality_survey):
        """Test scores for low quality survey"""
        coverage = quality_metrics.calculate_coverage(low_quality_survey)
        coherence = quality_metrics.calculate_coherence(low_quality_survey)
        structure = quality_metrics.calculate_structure(low_quality_survey)
        
        assert coverage < 3.0
        assert coherence < 3.0
        assert structure < 3.0
    
    def test_overall_quality(self, quality_metrics, high_quality_survey):
        """Test overall quality calculation"""
        overall = quality_metrics.calculate_overall(high_quality_survey)
        
        assert overall >= 3.5
        assert overall <= 5.0
    
    def test_quality_dimensions(self, quality_metrics):
        """Test all quality dimensions are evaluated"""
        survey = {"sections": [{"title": "Test", "content": "Test content"}]}
        
        dimensions = quality_metrics.evaluate_all_dimensions(survey)
        
        assert "coverage" in dimensions
        assert "coherence" in dimensions
        assert "structure" in dimensions
        assert "citations" in dimensions
        assert "insights" in dimensions
        assert all(1.0 <= v <= 5.0 for v in dimensions.values())


class TestPerformanceMetrics:
    """Test suite for performance metrics"""
    
    @pytest.fixture
    def performance_metrics(self):
        """Create PerformanceMetrics instance"""
        return PerformanceMetrics()
    
    def test_iteration_tracking(self, performance_metrics):
        """Test iteration tracking"""
        performance_metrics.start_iteration(1)
        import time
        time.sleep(0.1)
        performance_metrics.end_iteration(1, quality_score=3.5)
        
        stats = performance_metrics.get_iteration_stats(1)
        
        assert stats["iteration"] == 1
        assert stats["quality_score"] == 3.5
        assert stats["duration"] >= 0.1
    
    def test_convergence_detection(self, performance_metrics):
        """Test convergence detection"""
        # Simulate iterations with improving scores
        scores = [3.0, 3.5, 3.9, 4.0, 4.05, 4.08, 4.09]
        
        for i, score in enumerate(scores):
            performance_metrics.end_iteration(i, quality_score=score)
        
        converged = performance_metrics.has_converged(threshold=0.05)
        assert converged  # Last iterations show convergence
    
    def test_improvement_rate(self, performance_metrics):
        """Test improvement rate calculation"""
        performance_metrics.end_iteration(0, quality_score=3.0)
        performance_metrics.end_iteration(1, quality_score=3.3)
        performance_metrics.end_iteration(2, quality_score=3.5)
        
        rate = performance_metrics.calculate_improvement_rate()
        
        # (3.5 - 3.0) / 3.0 = 0.167
        assert rate == pytest.approx(0.167, rel=1e-2)
    
    def test_api_call_tracking(self, performance_metrics):
        """Test API call tracking"""
        performance_metrics.record_api_call("haiku", tokens=100, cost=0.001)
        performance_metrics.record_api_call("sonnet", tokens=200, cost=0.004)
        performance_metrics.record_api_call("haiku", tokens=150, cost=0.0015)
        
        stats = performance_metrics.get_api_stats()
        
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] == 450
        assert stats["total_cost"] == pytest.approx(0.0065, rel=1e-4)
        assert stats["by_model"]["haiku"]["calls"] == 2
        assert stats["by_model"]["sonnet"]["calls"] == 1
    
    def test_cache_statistics(self, performance_metrics):
        """Test cache hit/miss tracking"""
        performance_metrics.record_cache_hit()
        performance_metrics.record_cache_hit()
        performance_metrics.record_cache_miss()
        
        stats = performance_metrics.get_cache_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(0.667, rel=1e-2)


class TestComprehensiveEvaluator:
    """Test suite for comprehensive evaluator"""
    
    @pytest.fixture
    def evaluator(self):
        """Create ComprehensiveEvaluator instance"""
        return ComprehensiveEvaluator()
    
    @pytest.fixture
    def mock_wrapper(self):
        """Mock Claude wrapper"""
        wrapper = Mock()
        wrapper.query.return_value = {
            "coverage": 4.0,
            "coherence": 4.2,
            "structure": 3.8,
            "citations": 4.1,
            "insights": 3.9
        }
        return wrapper
    
    def test_full_evaluation(self, evaluator, mock_wrapper):
        """Test full survey evaluation"""
        survey = {"sections": [{"title": "Test", "content": "Content"}]}
        papers = [{"title": "Paper1"}]
        
        with patch.object(evaluator, 'claude_wrapper', mock_wrapper):
            results = evaluator.evaluate(survey, papers)
        
        assert "scores" in results
        assert "overall" in results
        assert "feedback" in results
        assert results["overall"] == pytest.approx(4.0, rel=1e-1)
    
    def test_comparison_evaluation(self, evaluator):
        """Test comparison between surveys"""
        survey1 = {"sections": [{"content": "Short"}]}
        survey2 = {"sections": [{"content": "Much longer and detailed content " * 20}]}
        
        comparison = evaluator.compare_surveys(survey1, survey2)
        
        assert comparison["better_survey"] == 2
        assert comparison["improvement"] > 0
    
    def test_convergence_criteria(self, evaluator):
        """Test convergence criteria checking"""
        # Below threshold
        assert not evaluator.check_convergence(3.5, threshold=4.0)
        
        # Above threshold
        assert evaluator.check_convergence(4.2, threshold=4.0)
        
        # With critical issues
        assert not evaluator.check_convergence(
            4.2, 
            threshold=4.0,
            has_critical_issues=True
        )
    
    @pytest.mark.parametrize("scores,expected_overall", [
        ({"coverage": 5, "coherence": 5, "structure": 5, "citations": 5, "insights": 5}, 5.0),
        ({"coverage": 3, "coherence": 3, "structure": 3, "citations": 3, "insights": 3}, 3.0),
        ({"coverage": 4, "coherence": 3, "structure": 5, "citations": 2, "insights": 4}, 3.55),
    ])
    def test_weighted_scoring(self, evaluator, scores, expected_overall):
        """Test weighted score calculation"""
        overall = evaluator.calculate_weighted_score(scores)
        assert overall == pytest.approx(expected_overall, rel=1e-2)
    
    def test_error_handling(self, evaluator):
        """Test error handling in evaluation"""
        # Invalid survey format
        with pytest.raises(ValueError):
            evaluator.evaluate(None, [])
        
        # Empty survey
        result = evaluator.evaluate({"sections": []}, [])
        assert result["overall"] < 2.0  # Should get low score


@pytest.mark.integration
class TestMetricsIntegration:
    """Integration tests for metrics system"""
    
    def test_full_evaluation_pipeline(self):
        """Test complete evaluation pipeline"""
        evaluator = ComprehensiveEvaluator()
        
        survey = {
            "title": "Test Survey",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is a comprehensive introduction to the topic. " * 20,
                    "citations": ["Ref1", "Ref2"]
                },
                {
                    "title": "Methods",
                    "content": "We describe our methodology in detail. " * 30,
                    "citations": ["Ref3", "Ref4", "Ref5"]
                }
            ]
        }
        
        papers = [
            {"title": "Ref1", "abstract": "Abstract 1"},
            {"title": "Ref2", "abstract": "Abstract 2"},
            {"title": "Ref3", "abstract": "Abstract 3"},
            {"title": "Ref4", "abstract": "Abstract 4"},
            {"title": "Ref5", "abstract": "Abstract 5"},
            {"title": "Uncited", "abstract": "Not cited"}
        ]
        
        # Mock the Claude wrapper
        with patch.object(evaluator, 'claude_wrapper') as mock_wrapper:
            mock_wrapper.query.return_value = {
                "coverage": 4.2,
                "coherence": 4.0,
                "structure": 4.1,
                "citations": 4.3,
                "insights": 3.9
            }
            
            result = evaluator.evaluate(survey, papers)
        
        assert result["overall"] >= 3.5
        assert result["citation_metrics"]["recall"] >= 0.8
        assert len(result["feedback"]) > 0
    
    def test_iterative_improvement_tracking(self):
        """Test tracking improvements across iterations"""
        performance = PerformanceMetrics()
        evaluator = ComprehensiveEvaluator()
        
        # Simulate iterative improvement
        iteration_scores = [3.0, 3.4, 3.7, 3.9, 4.0, 4.05]
        
        for i, score in enumerate(iteration_scores):
            performance.start_iteration(i)
            # Simulate some work
            import time
            time.sleep(0.01)
            performance.end_iteration(i, quality_score=score)
        
        # Check convergence
        assert performance.has_converged(threshold=0.1)
        
        # Check improvement rate
        improvement = performance.calculate_improvement_rate()
        assert improvement > 0.3  # 30% improvement
        
        # Get full statistics
        stats = performance.get_full_statistics()
        assert stats["iterations"] == 6
        assert stats["converged"] == True
        assert stats["final_score"] == 4.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])