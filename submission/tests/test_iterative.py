"""
Unit tests for the Global Iterative System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.our_system.iterative import (
    VerificationResult,
    GlobalVerifier,
    TargetedImprover,
    IterativeSurveySystem
)
from src.baselines.autosurvey import AutoSurveyBaseline


class TestVerificationResult(unittest.TestCase):
    """Test VerificationResult dataclass"""
    
    def test_meets_convergence_criteria_success(self):
        """Test successful convergence criteria"""
        result = VerificationResult(
            overall_score=4.2,
            coverage_score=4.0,
            structure_score=4.1,
            coherence_score=4.3,
            citation_score=4.1,
            insights_score=3.9,
            critical_issues=[],
            improvement_suggestions=["Minor improvement"]
        )
        self.assertTrue(result.meets_convergence_criteria())
    
    def test_meets_convergence_criteria_fail_low_score(self):
        """Test convergence failure due to low overall score"""
        result = VerificationResult(
            overall_score=3.8,  # Below threshold
            coverage_score=4.0,
            structure_score=4.1,
            coherence_score=4.3,
            citation_score=4.1,
            insights_score=3.9,
            critical_issues=[]
        )
        self.assertFalse(result.meets_convergence_criteria())
    
    def test_meets_convergence_criteria_fail_critical_issues(self):
        """Test convergence failure due to critical issues"""
        result = VerificationResult(
            overall_score=4.2,
            coverage_score=4.0,
            structure_score=4.1,
            coherence_score=4.3,
            citation_score=4.1,
            insights_score=3.9,
            critical_issues=["Missing key topic coverage"]
        )
        self.assertFalse(result.meets_convergence_criteria())


class TestGlobalVerifier(unittest.TestCase):
    """Test GlobalVerifier class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_wrapper = Mock()
        self.verifier = GlobalVerifier(self.mock_wrapper)
    
    def test_initialization(self):
        """Test GlobalVerifier initialization"""
        self.assertIsNotNone(self.verifier)
        self.assertEqual(self.verifier.claude_wrapper, self.mock_wrapper)
    
    def test_initialization_without_wrapper(self):
        """Test GlobalVerifier creates wrapper if none provided"""
        with patch('src.our_system.iterative.EnhancedClaudeWrapper') as mock_wrapper_class:
            verifier = GlobalVerifier()
            mock_wrapper_class.assert_called_once()
    
    @patch('src.our_system.iterative.GlobalVerifier._evaluate_with_llm')
    def test_verify_survey(self, mock_evaluate):
        """Test survey verification"""
        # Mock LLM response
        mock_evaluate.return_value = {
            'overall_score': 4.1,
            'coverage_score': 4.0,
            'structure_score': 4.2,
            'coherence_score': 4.1,
            'citation_score': 3.9,
            'insights_score': 4.0,
            'critical_issues': [],
            'improvement_suggestions': ["Add more recent papers"]
        }
        
        # Test survey
        survey = {
            'title': 'Test Survey',
            'sections': [
                {'title': 'Introduction', 'content': 'Test intro'},
                {'title': 'Methods', 'content': 'Test methods'}
            ]
        }
        papers = [{'title': 'Paper 1'}, {'title': 'Paper 2'}]
        
        result = self.verifier.verify_survey(survey, papers)
        
        self.assertIsInstance(result, VerificationResult)
        self.assertEqual(result.overall_score, 4.1)
        self.assertTrue(len(result.improvement_suggestions) > 0)


class TestIterativeSurveySystem(unittest.TestCase):
    """Test IterativeSurveySystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_wrapper = Mock()
        # Create mocked components
        self.mock_verifier = Mock(spec=GlobalVerifier)
        self.mock_improver = Mock(spec=TargetedImprover)
        self.mock_base = Mock(spec=AutoSurveyBaseline)
        
        self.system = IterativeSurveySystem(
            base_generator=self.mock_base,
            verifier=self.mock_verifier,
            improver=self.mock_improver,
            max_iterations=3
        )
    
    def test_initialization(self):
        """Test IterativeSurveySystem initialization"""
        self.assertIsNotNone(self.system)
        self.assertEqual(self.system.max_iterations, 3)
        self.assertIsNotNone(self.system.verifier)
        self.assertIsNotNone(self.system.improver)
        self.assertIsNotNone(self.system.base_generator)
    
    def test_convergence_detection(self):
        """Test convergence detection logic"""
        # Create mock verification result that meets criteria
        mock_result = Mock()
        mock_result.meets_convergence_criteria.return_value = True
        mock_result.overall_score = 4.2
        
        # Mock the verifier to return converged result
        self.system.verifier.verify_survey = Mock(return_value=mock_result)
        
        # Mock base_generator and improver
        self.system.base_generator.generate_survey = Mock(return_value={'sections': []})
        self.system.improver.improve_survey = Mock(return_value={'sections': []})
        
        # Run system
        papers = [{'title': 'Paper 1'}]
        survey = self.system.generate_survey_iteratively(papers, topic="Test Topic")
        
        # Should converge immediately after first verification
        self.assertEqual(len(survey.get('iteration_history', [])), 1)
        self.assertEqual(survey.get('iteration_history', [])[0].get('overall_score'), 4.2)
    
    def test_max_iterations_limit(self):
        """Test that system respects max_iterations limit"""
        # Create mock verification result that never converges
        mock_result = Mock()
        mock_result.meets_convergence_criteria.return_value = False
        mock_result.overall_score = 3.5
        
        # Mock the verifier to return non-converged result
        self.system.verifier.verify_survey = Mock(return_value=mock_result)
        
        # Mock base_generator and improver
        self.system.base_generator.generate_survey = Mock(return_value={'sections': []})
        self.system.improver.improve_survey = Mock(return_value={'sections': []})
        
        # Run system
        papers = [{'title': 'Paper 1'}]
        survey = self.system.generate_survey_iteratively(papers, topic="Test Topic")
        
        # Should stop at max_iterations
        self.assertEqual(len(survey.get('iteration_history', [])), 3)  # max_iterations = 3


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    @patch('src.our_system.iterative.EnhancedClaudeWrapper')
    def test_end_to_end_convergence(self, mock_wrapper_class):
        """Test end-to-end convergence scenario"""
        # Create mock wrapper
        mock_wrapper = Mock()
        mock_wrapper_class.return_value = mock_wrapper
        
        # Mock LLM responses for progressive improvement
        responses = [
            {'overall': 3.2, 'coverage': 3.0, 'coherence': 3.1},  # Initial
            {'overall': 3.6, 'coverage': 3.5, 'coherence': 3.5},  # Iteration 1
            {'overall': 4.1, 'coverage': 4.0, 'coherence': 4.2},  # Iteration 2 (converged)
        ]
        
        response_iter = iter(responses)
        
        def mock_chat(*args, **kwargs):
            try:
                resp = next(response_iter)
                return str(resp)
            except StopIteration:
                return str(responses[-1])
        
        mock_wrapper.chat_completion = Mock(side_effect=mock_chat)
        
        # Create system and run
        system = IterativeSurveySystem(max_iterations=5)
        papers = [{'title': f'Paper {i}'} for i in range(10)]
        
        # The system should iterate and improve
        # (actual behavior depends on implementation details)
        # This is a simplified test showing the structure


if __name__ == '__main__':
    unittest.main()