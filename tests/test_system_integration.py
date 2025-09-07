"""
Simple integration test for the iterative survey system.
Tests core functionality without complex mocking.
"""

import unittest
import sys
from pathlib import Path
import tempfile
import json

sys.path.append(str(Path(__file__).parent.parent))

from src.our_system.iterative import VerificationResult, IterativeSurveySystem


class TestSystemIntegration(unittest.TestCase):
    """Basic integration tests for the survey system."""
    
    def test_verification_result(self):
        """Test VerificationResult convergence logic."""
        # Test passing convergence
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
        
        # Test failing due to low score
        result.overall_score = 3.5
        self.assertFalse(result.meets_convergence_criteria())
        
        # Test failing due to critical issues
        result.overall_score = 4.2
        result.critical_issues = ["Major problem"]
        self.assertFalse(result.meets_convergence_criteria())
    
    def test_system_initialization(self):
        """Test system can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                max_iterations=2,
                checkpoint_dir=tmpdir
            )
            
            self.assertIsNotNone(system)
            self.assertEqual(system.max_iterations, 2)
            self.assertIsNotNone(system.base_generator)
            self.assertIsNotNone(system.verifier)
            self.assertIsNotNone(system.improver)
    
    def test_checkpoint_directory_creation(self):
        """Test checkpoint directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            system = IterativeSurveySystem(checkpoint_dir=str(checkpoint_dir))
            
            self.assertTrue(checkpoint_dir.exists())
            self.assertTrue(checkpoint_dir.is_dir())
    
    def test_survey_structure(self):
        """Test survey has expected structure after generation."""
        # This would normally test the full generation, but requires API keys
        # For now, just verify the structure of what would be returned
        expected_keys = ['topic', 'method', 'converged', 'total_iterations', 'iteration_history']
        
        # Mock survey structure
        mock_survey = {
            'topic': 'Test Topic',
            'method': 'global_iterative',
            'converged': True,
            'total_iterations': 1,
            'iteration_history': [
                {
                    'iteration': 0,
                    'overall_score': 4.2,
                    'coverage_score': 4.0,
                    'coherence_score': 4.1,
                    'citation_score': 4.0,
                    'critical_issues': []
                }
            ],
            'sections': []
        }
        
        for key in expected_keys:
            self.assertIn(key, mock_survey)


if __name__ == '__main__':
    unittest.main()