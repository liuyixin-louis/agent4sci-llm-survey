"""
Core tests for iterative.py to improve coverage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path
import sys
import pickle

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.our_system.iterative import (
    VerificationResult,
    GlobalVerifier,
    TargetedImprover,
    IterativeSurveySystem,
    SurveySection
)
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper


class TestVerificationResult:
    """Test VerificationResult dataclass."""
    
    def test_verification_result_creation(self):
        """Test creating verification result."""
        result = VerificationResult(
            overall_score=4.0,
            coverage_score=4.1,
            structure_score=3.9,
            coherence_score=4.2,
            citation_score=4.0,
            insights_score=3.8
        )
        
        assert result.overall_score == 4.0
        assert result.coverage_score == 4.1
        assert len(result.critical_issues) == 0
        assert len(result.improvement_suggestions) == 0
    
    def test_convergence_with_high_score(self):
        """Test convergence with high score."""
        result = VerificationResult(
            overall_score=4.5,
            coverage_score=4.3,
            structure_score=4.4,
            coherence_score=4.6,
            citation_score=4.5,
            insights_score=4.4
        )
        assert result.meets_convergence_criteria() == True
    
    def test_no_convergence_with_issues(self):
        """Test no convergence with critical issues."""
        result = VerificationResult(
            overall_score=4.2,
            coverage_score=4.0,
            structure_score=4.1,
            coherence_score=4.3,
            citation_score=4.1,
            insights_score=4.0,
            critical_issues=["Major problem found"]
        )
        assert result.meets_convergence_criteria() == False


class TestGlobalVerifier:
    """Test GlobalVerifier class."""
    
    @pytest.fixture
    def mock_wrapper(self):
        """Create mock Claude wrapper."""
        wrapper = Mock(spec=EnhancedClaudeWrapper)
        wrapper.query.return_value = json.dumps({
            "overall_score": 4.0,
            "coverage_score": 3.9,
            "structure_score": 4.1,
            "coherence_score": 4.0,
            "citation_score": 4.2,
            "insights_score": 3.8,
            "critical_issues": [],
            "improvement_suggestions": ["Add more recent papers"]
        })
        return wrapper
    
    def test_verifier_initialization(self):
        """Test verifier initialization."""
        verifier = GlobalVerifier()
        assert verifier is not None
        assert hasattr(verifier, 'claude_wrapper')
    
    def test_verify_survey_with_mock(self, mock_wrapper):
        """Test survey verification with mocked wrapper."""
        verifier = GlobalVerifier(claude_wrapper=mock_wrapper)
        
        survey = {
            'sections': [
                {'title': 'Introduction', 'content': 'Test intro'},
                {'title': 'Methods', 'content': 'Test methods'}
            ]
        }
        papers = [{'title': 'Paper 1'}, {'title': 'Paper 2'}]
        
        result = verifier.verify_survey(survey, papers)
        
        assert isinstance(result, VerificationResult)
        assert result.overall_score == 4.0
        assert result.coverage_score == 3.9
        assert len(result.improvement_suggestions) == 1
    
    def test_format_survey_for_verification(self):
        """Test survey formatting."""
        verifier = GlobalVerifier()
        
        survey = {
            'sections': [
                {'title': 'Section 1', 'content': 'Content 1'},
                {'title': 'Section 2', 'content': 'Content 2'}
            ]
        }
        
        formatted = verifier._format_survey_for_verification(survey)
        
        assert 'Section 1' in formatted
        assert 'Content 1' in formatted
        assert 'Section 2' in formatted
    
    def test_format_papers_summary(self):
        """Test papers summary formatting."""
        verifier = GlobalVerifier()
        
        papers = [
            {'title': 'Paper A', 'abstract': 'Abstract A'},
            {'title': 'Paper B', 'abstract': 'Abstract B'}
        ]
        
        summary = verifier._format_papers_summary(papers)
        
        assert 'Paper A' in summary
        assert 'Paper B' in summary
    
    def test_default_verification_result(self):
        """Test default verification result."""
        verifier = GlobalVerifier()
        result = verifier._default_verification_result()
        
        assert isinstance(result, VerificationResult)
        assert result.overall_score == 3.5
        assert len(result.critical_issues) == 1


class TestTargetedImprover:
    """Test TargetedImprover class."""
    
    @pytest.fixture
    def mock_wrapper(self):
        """Create mock Claude wrapper."""
        wrapper = Mock(spec=EnhancedClaudeWrapper)
        wrapper.query.return_value = json.dumps({
            "improved_content": "Better content with more details"
        })
        return wrapper
    
    def test_improver_initialization(self):
        """Test improver initialization."""
        improver = TargetedImprover()
        assert improver is not None
        assert hasattr(improver, 'claude_wrapper')
    
    def test_identify_improvements(self):
        """Test identifying improvements from verification."""
        improver = TargetedImprover()
        
        verification = VerificationResult(
            overall_score=3.5,
            coverage_score=3.0,  # Low coverage
            structure_score=4.0,
            coherence_score=3.2,  # Low coherence
            citation_score=3.8,
            insights_score=4.1
        )
        
        improvements = improver._identify_improvements(verification)
        
        assert 'coverage' in improvements
        assert 'coherence' in improvements
        assert 'citations' in improvements  # Always check citations
    
    def test_improve_survey_with_mock(self, mock_wrapper):
        """Test survey improvement with mocked wrapper."""
        improver = TargetedImprover(claude_wrapper=mock_wrapper)
        
        survey = {
            'sections': [
                {'title': 'Intro', 'content': 'Short intro'},
                {'title': 'Methods', 'content': 'Brief methods'}
            ]
        }
        
        verification = VerificationResult(
            overall_score=3.2,
            coverage_score=2.8,
            structure_score=3.5,
            coherence_score=3.0,
            citation_score=3.3,
            insights_score=3.4,
            critical_issues=["Needs more coverage"],
            improvement_suggestions=["Add recent papers"]
        )
        
        papers = [{'title': 'Paper 1', 'abstract': 'Abstract 1'}]
        
        # Mock the improvement methods
        with patch.object(improver, '_improve_coverage') as mock_coverage:
            mock_coverage.return_value = survey
            with patch.object(improver, '_improve_coherence') as mock_coherence:
                mock_coherence.return_value = survey
                with patch.object(improver, '_improve_citations') as mock_citations:
                    mock_citations.return_value = survey
                    
                    improved = improver.improve_survey(survey, verification, papers)
                    
                    assert improved is not None
                    mock_coverage.assert_called_once()
                    mock_coherence.assert_called_once()
                    mock_citations.assert_called_once()


class TestIterativeSurveySystem:
    """Test IterativeSurveySystem class."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components."""
        base_gen = Mock()
        base_gen.generate_survey.return_value = {
            'sections': [
                {'title': 'Introduction', 'content': 'Initial intro'},
                {'title': 'Conclusion', 'content': 'Initial conclusion'}
            ]
        }
        
        verifier = Mock()
        improver = Mock()
        
        return base_gen, verifier, improver
    
    def test_system_initialization(self):
        """Test system initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                max_iterations=3,
                checkpoint_dir=tmpdir
            )
            
            assert system.max_iterations == 3
            assert system.checkpoint_dir.exists()
            assert system.base_generator is not None
            assert system.verifier is not None
            assert system.improver is not None
    
    def test_generate_survey_with_convergence(self, mock_components):
        """Test survey generation with convergence."""
        base_gen, verifier, improver = mock_components
        
        # Set up verification to converge on second iteration
        verifier.verify_survey.side_effect = [
            VerificationResult(
                overall_score=3.5,
                coverage_score=3.3,
                structure_score=3.6,
                coherence_score=3.5,
                citation_score=3.4,
                insights_score=3.5,
                critical_issues=["Needs improvement"]
            ),
            VerificationResult(
                overall_score=4.2,
                coverage_score=4.1,
                structure_score=4.2,
                coherence_score=4.3,
                citation_score=4.1,
                insights_score=4.0,
                critical_issues=[]
            )
        ]
        
        improver.improve_survey.return_value = {
            'sections': [
                {'title': 'Introduction', 'content': 'Improved intro'},
                {'title': 'Conclusion', 'content': 'Improved conclusion'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                base_generator=base_gen,
                verifier=verifier,
                improver=improver,
                max_iterations=5,
                checkpoint_dir=tmpdir
            )
            
            papers = [{'title': 'Paper 1'}]
            survey = system.generate_survey_iteratively(
                papers=papers,
                topic="Test Topic",
                target_sections=2
            )
            
            assert survey['converged'] == True
            assert survey['total_iterations'] == 2
            assert len(survey['iteration_history']) == 2
            assert survey['method'] == 'global_iterative'
    
    def test_checkpoint_saving(self):
        """Test checkpoint saving functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(checkpoint_dir=tmpdir)
            
            survey = {'sections': [{'title': 'Test', 'content': 'Test'}]}
            verification = VerificationResult(
                overall_score=3.8,
                coverage_score=3.7,
                structure_score=3.9,
                coherence_score=3.8,
                citation_score=3.7,
                insights_score=3.8
            )
            
            system._save_checkpoint(survey, 1, verification)
            
            checkpoint_files = list(Path(tmpdir).glob("iter_*.pkl"))
            assert len(checkpoint_files) == 1
            
            # Load and verify checkpoint
            with open(checkpoint_files[0], 'rb') as f:
                checkpoint = pickle.load(f)
                assert checkpoint['iteration'] == 1
                assert checkpoint['survey'] == survey
                assert checkpoint['verification'] == verification
    
    def test_max_iterations_limit(self, mock_components):
        """Test that system respects max iterations."""
        base_gen, verifier, improver = mock_components
        
        # Never converge
        verifier.verify_survey.return_value = VerificationResult(
            overall_score=3.5,
            coverage_score=3.4,
            structure_score=3.5,
            coherence_score=3.5,
            citation_score=3.4,
            insights_score=3.5,
            critical_issues=["Always has issues"]
        )
        
        improver.improve_survey.return_value = {
            'sections': [{'title': 'Test', 'content': 'Content'}]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            system = IterativeSurveySystem(
                base_generator=base_gen,
                verifier=verifier,
                improver=improver,
                max_iterations=2,
                checkpoint_dir=tmpdir
            )
            
            papers = [{'title': 'Paper 1'}]
            survey = system.generate_survey_iteratively(
                papers=papers,
                topic="Test Topic"
            )
            
            assert survey['converged'] == False
            assert survey['total_iterations'] == 2


class TestImproverMethods:
    """Test specific improver methods."""
    
    def test_improve_coverage_logic(self):
        """Test coverage improvement logic."""
        improver = TargetedImprover()
        
        survey = {
            'sections': [
                {'title': 'Introduction', 'content': 'Brief intro.'},
                {'title': 'Methods', 'content': 'Short methods.'}
            ]
        }
        
        papers = [
            {'title': 'Paper A', 'abstract': 'Important findings about X'},
            {'title': 'Paper B', 'abstract': 'Novel approach to Y'}
        ]
        
        # Mock the claude wrapper
        with patch.object(improver, 'claude_wrapper') as mock_wrapper:
            mock_wrapper.query.return_value = json.dumps({
                "expanded_content": "Much more detailed content covering X and Y"
            })
            
            improved = improver._improve_coverage(survey, papers)
            
            assert improved is not None
            # Should have called wrapper for each section
            assert mock_wrapper.query.call_count >= 1
    
    def test_improve_structure_reordering(self):
        """Test structure improvement with section reordering."""
        improver = TargetedImprover()
        
        survey = {
            'sections': [
                {'title': 'Methods', 'content': 'Methods section'},
                {'title': 'Conclusion', 'content': 'Conclusion section'},
                {'title': 'Introduction', 'content': 'Intro section'},
                {'title': 'Results', 'content': 'Results section'}
            ]
        }
        
        improved = improver._improve_structure(survey)
        
        # Introduction should be first
        assert 'introduction' in improved['sections'][0]['title'].lower()
        # Conclusion should be last
        assert 'conclusion' in improved['sections'][-1]['title'].lower()
        # All sections should have numbering
        assert improved['sections'][0]['title'].startswith('1.')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.our_system.iterative", "--cov-report=term-missing"])