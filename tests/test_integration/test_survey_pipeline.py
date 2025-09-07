"""
Integration tests for the complete survey generation pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.our_system.iterative import IterativeSurveySystem, VerificationResult
from src.baselines.autosurvey import AutoSurveyBaseline
from src.evaluation.metrics import SurveyEvaluator, CitationMetrics, ContentMetrics
from src.trend_discovery.colm_classifier import COLMTaxonomyClassifier
from src.trend_discovery.trend_analyzer import TrendAnalyzer


class TestSurveyPipelineIntegration:
    """Integration tests for complete survey pipeline."""
    
    @pytest.fixture
    def mock_papers(self):
        """Create mock papers for testing."""
        return [
            {
                'title': 'Attention Is All You Need',
                'abstract': 'We propose the Transformer architecture based on attention mechanisms.',
                'authors': ['Vaswani et al.'],
                'year': 2017,
                'month': 6
            },
            {
                'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
                'abstract': 'BERT improves language understanding through bidirectional training.',
                'authors': ['Devlin et al.'],
                'year': 2018,
                'month': 10
            },
            {
                'title': 'GPT-3: Language Models are Few-Shot Learners',
                'abstract': 'Scaling language models improves few-shot performance.',
                'authors': ['Brown et al.'],
                'year': 2020,
                'month': 5
            },
        ]
    
    @pytest.fixture
    def mock_survey(self):
        """Create mock survey output."""
        return {
            'topic': 'Transformer Models',
            'sections': [
                {
                    'title': 'Introduction',
                    'content': 'Transformers have revolutionized NLP.',
                    'citations': ['Attention Is All You Need']
                },
                {
                    'title': 'Methods',
                    'content': 'BERT and GPT use transformer architecture.',
                    'citations': ['BERT', 'GPT-3']
                }
            ],
            'method': 'test',
            'converged': True,
            'total_iterations': 1
        }
    
    def test_baseline_survey_generation(self, mock_papers):
        """Test AutoSurvey baseline generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = AutoSurveyBaseline(cache_dir=tmpdir)
            
            # Mock the Claude wrapper to avoid API calls
            with patch.object(baseline, 'claude_wrapper') as mock_wrapper:
                mock_wrapper.query.return_value = json.dumps({
                    'sections': [
                        {'title': 'Introduction', 'content': 'Test intro'},
                        {'title': 'Conclusion', 'content': 'Test conclusion'}
                    ]
                })
                
                survey = baseline.generate_survey(
                    papers=mock_papers,
                    topic="Transformers",
                    target_sections=2
                )
                
                assert survey is not None
                assert 'sections' in survey
                assert len(survey['sections']) >= 2
    
    def test_iterative_system_convergence(self, mock_papers):
        """Test iterative system convergence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                max_iterations=3,
                checkpoint_dir=tmpdir
            )
            
            # Mock components to control convergence
            with patch.object(system.base_generator, 'generate_survey') as mock_gen:
                mock_gen.return_value = {
                    'sections': [{'title': 'Test', 'content': 'Content'}]
                }
                
                with patch.object(system.verifier, 'verify_survey') as mock_verify:
                    # First iteration: not converged
                    # Second iteration: converged
                    mock_verify.side_effect = [
                        VerificationResult(
                            overall_score=3.5,
                            coverage_score=3.0,
                            structure_score=3.5,
                            coherence_score=3.5,
                            citation_score=3.5,
                            insights_score=3.5,
                            critical_issues=['Missing coverage'],
                            improvement_suggestions=[]
                        ),
                        VerificationResult(
                            overall_score=4.2,
                            coverage_score=4.0,
                            structure_score=4.1,
                            coherence_score=4.2,
                            citation_score=4.1,
                            insights_score=4.0,
                            critical_issues=[],
                            improvement_suggestions=[]
                        )
                    ]
                    
                    with patch.object(system.improver, 'improve_survey') as mock_improve:
                        mock_improve.return_value = {
                            'sections': [{'title': 'Improved', 'content': 'Better'}]
                        }
                        
                        survey = system.generate_survey_iteratively(
                            papers=mock_papers,
                            topic="Test Topic",
                            target_sections=3
                        )
                        
                        assert survey['converged'] == True
                        assert survey['total_iterations'] == 2
                        assert len(survey['iteration_history']) == 2
    
    def test_evaluation_metrics_calculation(self, mock_survey, mock_papers):
        """Test evaluation metrics calculation."""
        evaluator = SurveyEvaluator()
        
        # Test citation metrics
        citation_metrics = CitationMetrics()
        recall = citation_metrics.calculate_recall(mock_survey, mock_papers)
        assert 0 <= recall <= 1
        
        # Test content metrics
        content_metrics = ContentMetrics()
        coverage = content_metrics.calculate_coverage(mock_survey)
        assert 1 <= coverage <= 5
        
        # Test full evaluation
        with patch.object(evaluator, 'claude_wrapper') as mock_wrapper:
            mock_wrapper.query.return_value = {
                'coverage': 4.0,
                'coherence': 4.1,
                'structure': 3.9,
                'citations': 4.2,
                'insights': 3.8
            }
            
            results = evaluator.evaluate(mock_survey, mock_papers)
            
            assert 'scores' in results
            assert 'overall' in results
            assert results['overall'] > 0
    
    def test_trend_discovery_integration(self, mock_papers):
        """Test trend discovery with survey generation."""
        classifier = COLMTaxonomyClassifier()
        analyzer = TrendAnalyzer()
        
        # Classify papers
        classifications = classifier.classify_papers_batch(mock_papers)
        assert len(classifications) == len(mock_papers)
        
        # Analyze trends
        trends = analyzer.identify_trends(mock_papers, classifications)
        assert isinstance(trends, dict)
        
        # Get hot topics
        hot_topics = analyzer.get_hot_topics(mock_papers, classifications, top_n=2)
        assert len(hot_topics) <= 2
        
        # Generate report
        report = analyzer.generate_trend_report(mock_papers, classifications)
        assert 'summary' in report
        assert 'hot_topics' in report
    
    def test_checkpoint_saving_and_loading(self, mock_papers):
        """Test checkpoint functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                max_iterations=1,
                checkpoint_dir=tmpdir
            )
            
            # Create a mock verification result
            verification = VerificationResult(
                overall_score=3.8,
                coverage_score=3.5,
                structure_score=3.9,
                coherence_score=3.8,
                citation_score=3.7,
                insights_score=3.9,
                critical_issues=[],
                improvement_suggestions=[]
            )
            
            # Save checkpoint
            survey = {'sections': [{'title': 'Test', 'content': 'Test'}]}
            system._save_checkpoint(survey, 1, verification)
            
            # Check checkpoint was created
            checkpoint_files = list(Path(tmpdir).glob("iter_*.pkl"))
            assert len(checkpoint_files) > 0
    
    def test_pipeline_error_handling(self):
        """Test error handling in pipeline."""
        system = IterativeSurveySystem()
        
        # Test with empty papers
        with patch.object(system.base_generator, 'generate_survey') as mock_gen:
            mock_gen.return_value = {'sections': []}
            
            survey = system.generate_survey_iteratively(
                papers=[],
                topic="Empty Test"
            )
            
            assert survey is not None
            assert 'sections' in survey
    
    def test_baseline_vs_iterative_comparison(self, mock_papers):
        """Test comparison between baseline and iterative system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both systems
            baseline = AutoSurveyBaseline(cache_dir=tmpdir)
            iterative = IterativeSurveySystem(
                max_iterations=2,
                checkpoint_dir=tmpdir
            )
            
            # Mock responses
            mock_survey = {
                'sections': [
                    {'title': 'Intro', 'content': 'Introduction'},
                    {'title': 'Methods', 'content': 'Methodology'}
                ]
            }
            
            with patch.object(baseline, 'claude_wrapper') as mock_base_wrapper:
                mock_base_wrapper.query.return_value = json.dumps(mock_survey)
                
                with patch.object(iterative.base_generator, 'generate_survey') as mock_gen:
                    mock_gen.return_value = mock_survey
                    
                    with patch.object(iterative.verifier, 'verify_survey') as mock_verify:
                        mock_verify.return_value = VerificationResult(
                            overall_score=4.5,
                            coverage_score=4.3,
                            structure_score=4.4,
                            coherence_score=4.6,
                            citation_score=4.5,
                            insights_score=4.4,
                            critical_issues=[],
                            improvement_suggestions=[]
                        )
                        
                        # Generate with both systems
                        baseline_survey = baseline.generate_survey(
                            mock_papers, "Test Topic"
                        )
                        iterative_survey = iterative.generate_survey_iteratively(
                            mock_papers, "Test Topic"
                        )
                        
                        # Both should produce valid surveys
                        assert baseline_survey is not None
                        assert iterative_survey is not None
                        
                        # Iterative should have convergence info
                        assert 'converged' in iterative_survey
                        assert 'iteration_history' in iterative_survey


class TestEndToEndScenarios:
    """End-to-end scenario tests."""
    
    def test_complete_workflow_small_dataset(self):
        """Test complete workflow with small dataset."""
        # Create minimal paper set
        papers = [
            {'title': f'Paper {i}', 'abstract': f'Abstract {i}', 'year': 2024, 'month': i}
            for i in range(1, 4)
        ]
        
        # Run trend discovery
        classifier = COLMTaxonomyClassifier()
        analyzer = TrendAnalyzer()
        
        classifications = classifier.classify_papers_batch(papers)
        report = analyzer.generate_trend_report(papers, classifications)
        
        # Create survey system
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                max_iterations=1,
                checkpoint_dir=tmpdir
            )
            
            # Mock to avoid API calls
            with patch.object(system.base_generator, 'generate_survey') as mock_gen:
                mock_gen.return_value = {
                    'sections': [
                        {'title': 'Introduction', 'content': 'Intro'},
                        {'title': 'Conclusion', 'content': 'Conclusion'}
                    ]
                }
                
                with patch.object(system.verifier, 'verify_survey') as mock_verify:
                    mock_verify.return_value = VerificationResult(
                        overall_score=4.1,
                        coverage_score=4.0,
                        structure_score=4.0,
                        coherence_score=4.1,
                        citation_score=4.1,
                        insights_score=4.0,
                        critical_issues=[],
                        improvement_suggestions=[]
                    )
                    
                    # Generate survey based on trending topic
                    if report['hot_topics']:
                        topic = report['hot_topics'][0]['category']
                    else:
                        topic = "General AI Research"
                    
                    survey = system.generate_survey_iteratively(
                        papers=papers,
                        topic=topic,
                        target_sections=3
                    )
                    
                    # Verify complete workflow
                    assert survey is not None
                    assert survey['converged'] == True
                    assert 'sections' in survey
                    assert len(classifications) == len(papers)
                    assert 'recommendations' in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])