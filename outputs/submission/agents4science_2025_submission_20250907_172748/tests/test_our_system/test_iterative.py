"""
Comprehensive tests for Global Iterative System (our core innovation)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import copy
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.our_system.iterative import (
    GlobalVerifier,
    TargetedImprover, 
    GlobalIterativeSystem
)


class TestGlobalVerifier:
    """Test suite for GlobalVerifier"""
    
    @pytest.fixture
    def verifier(self):
        """Create GlobalVerifier instance"""
        with patch('src.our_system.iterative.ClaudeCodeCLIWrapper'):
            return GlobalVerifier()
    
    @pytest.fixture
    def sample_survey(self):
        """Sample survey for testing"""
        return {
            "title": "LLM Survey",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "This is an introduction to LLMs. " * 50,
                    "citations": ["Paper1", "Paper2"]
                },
                {
                    "title": "Methods",
                    "content": "We describe various methods. " * 100,
                    "citations": ["Paper3", "Paper4", "Paper5"]
                },
                {
                    "title": "Results", 
                    "content": "Our findings show that... " * 75,
                    "citations": ["Paper6"]
                },
                {
                    "title": "Conclusion",
                    "content": "In conclusion... " * 30,
                    "citations": ["Paper7", "Paper8"]
                }
            ]
        }
    
    def test_verify_survey_high_quality(self, verifier, sample_survey):
        """Test verification of high-quality survey"""
        mock_response = {
            "scores": {
                "coverage": 4.5,
                "coherence": 4.3,
                "structure": 4.2,
                "citations": 4.4,
                "insights": 4.0
            },
            "issues": [],
            "suggestions": ["Minor improvements possible"]
        }
        
        verifier.claude_wrapper.query.return_value = mock_response
        
        result = verifier.verify(sample_survey)
        
        assert result["overall_score"] >= 4.0
        assert result["meets_criteria"] == True
        assert len(result["issues"]) == 0
    
    def test_verify_survey_low_quality(self, verifier):
        """Test verification of low-quality survey"""
        low_quality_survey = {
            "title": "Bad Survey",
            "sections": [
                {"title": "Intro", "content": "Short intro.", "citations": []},
                {"title": "End", "content": "The end.", "citations": []}
            ]
        }
        
        mock_response = {
            "scores": {
                "coverage": 2.0,
                "coherence": 2.5,
                "structure": 2.2,
                "citations": 1.5,
                "insights": 2.0
            },
            "issues": [
                "Insufficient coverage",
                "Missing citations",
                "Poor structure"
            ],
            "suggestions": [
                "Add more sections",
                "Include citations",
                "Expand content"
            ]
        }
        
        verifier.claude_wrapper.query.return_value = mock_response
        
        result = verifier.verify(low_quality_survey)
        
        assert result["overall_score"] < 3.0
        assert result["meets_criteria"] == False
        assert len(result["issues"]) > 0
    
    def test_weighted_scoring(self, verifier):
        """Test weighted score calculation"""
        scores = {
            "coverage": 4.0,    # Weight: 0.25
            "coherence": 3.0,   # Weight: 0.20
            "structure": 5.0,   # Weight: 0.20
            "citations": 2.0,   # Weight: 0.20
            "insights": 4.0     # Weight: 0.15
        }
        
        expected = (4.0*0.25 + 3.0*0.20 + 5.0*0.20 + 2.0*0.20 + 4.0*0.15)
        calculated = verifier._calculate_weighted_score(scores)
        
        assert calculated == pytest.approx(expected, rel=1e-3)
    
    def test_convergence_criteria(self, verifier):
        """Test convergence criteria checking"""
        # High score, no issues -> converged
        assert verifier._check_convergence(4.2, [])
        
        # High score, but critical issues -> not converged
        assert not verifier._check_convergence(4.2, ["Missing key section"])
        
        # Low score -> not converged
        assert not verifier._check_convergence(3.5, [])
        
        # Exact threshold -> converged
        assert verifier._check_convergence(4.0, [])
    
    @pytest.mark.parametrize("scores,expected_overall", [
        ({"coverage": 5, "coherence": 5, "structure": 5, "citations": 5, "insights": 5}, 5.0),
        ({"coverage": 1, "coherence": 1, "structure": 1, "citations": 1, "insights": 1}, 1.0),
        ({"coverage": 4, "coherence": 4, "structure": 4, "citations": 4, "insights": 4}, 4.0),
    ])
    def test_scoring_parametrized(self, verifier, scores, expected_overall):
        """Test various scoring scenarios"""
        calculated = verifier._calculate_weighted_score(scores)
        assert calculated == pytest.approx(expected_overall, rel=1e-2)
    
    def test_dimension_identification(self, verifier):
        """Test identification of weak dimensions"""
        scores = {
            "coverage": 4.5,
            "coherence": 3.2,  # Weak
            "structure": 4.1,
            "citations": 2.8,  # Weak
            "insights": 4.3
        }
        
        weak_dimensions = verifier._identify_weak_dimensions(scores)
        
        assert "coherence" in weak_dimensions
        assert "citations" in weak_dimensions
        assert "coverage" not in weak_dimensions


class TestTargetedImprover:
    """Test suite for TargetedImprover"""
    
    @pytest.fixture
    def improver(self):
        """Create TargetedImprover instance"""
        with patch('src.our_system.iterative.ClaudeCodeCLIWrapper'):
            return TargetedImprover()
    
    @pytest.fixture
    def verification_result(self):
        """Sample verification result"""
        return {
            "overall_score": 3.5,
            "scores": {
                "coverage": 3.0,
                "coherence": 3.5,
                "structure": 4.0,
                "citations": 3.2,
                "insights": 3.8
            },
            "issues": ["Low coverage", "Missing citations"],
            "suggestions": ["Add more topics", "Include more references"]
        }
    
    def test_improve_coverage(self, improver):
        """Test coverage improvement"""
        survey = {
            "sections": [
                {"title": "Intro", "content": "Short intro"}
            ]
        }
        
        verification = {
            "scores": {"coverage": 2.5},
            "issues": ["Missing key topics"],
            "suggestions": ["Add sections on methods and results"]
        }
        
        mock_response = {
            "sections": [
                {"title": "Intro", "content": "Expanded introduction"},
                {"title": "Methods", "content": "New methods section"},
                {"title": "Results", "content": "New results section"}
            ]
        }
        
        improver.claude_wrapper.query.return_value = mock_response
        
        improved = improver.improve(survey, verification, papers=[])
        
        assert len(improved["sections"]) > len(survey["sections"])
        assert any("Methods" in s["title"] for s in improved["sections"])
    
    def test_improve_coherence(self, improver):
        """Test coherence improvement"""
        survey = {
            "sections": [
                {"title": "A", "content": "Content A"},
                {"title": "B", "content": "Content B"},
                {"title": "C", "content": "Content C"}
            ]
        }
        
        verification = {
            "scores": {"coherence": 2.8},
            "issues": ["Poor transitions between sections"]
        }
        
        mock_response = {
            "sections": [
                {"title": "A", "content": "Content A with transition to B"},
                {"title": "B", "content": "Content B building on A and leading to C"},
                {"title": "C", "content": "Content C concluding A and B"}
            ]
        }
        
        improver.claude_wrapper.query.return_value = mock_response
        
        improved = improver.improve(survey, verification, papers=[])
        
        # Check that content was updated
        assert improved["sections"][0]["content"] != survey["sections"][0]["content"]
        assert "transition" in improved["sections"][0]["content"]
    
    def test_improve_citations(self, improver):
        """Test citation improvement"""
        survey = {
            "sections": [
                {"title": "Methods", "content": "We use various methods", "citations": []}
            ]
        }
        
        papers = [
            {"title": "Method Paper 1", "abstract": "About method 1"},
            {"title": "Method Paper 2", "abstract": "About method 2"}
        ]
        
        verification = {
            "scores": {"citations": 2.5},
            "issues": ["Insufficient citations"]
        }
        
        mock_response = {
            "sections": [
                {
                    "title": "Methods",
                    "content": "We use various methods [1, 2]",
                    "citations": ["Method Paper 1", "Method Paper 2"]
                }
            ]
        }
        
        improver.claude_wrapper.query.return_value = mock_response
        
        improved = improver.improve(survey, verification, papers)
        
        assert len(improved["sections"][0]["citations"]) > 0
        assert "[1" in improved["sections"][0]["content"]
    
    def test_improve_structure(self, improver):
        """Test structure improvement"""
        survey = {
            "sections": [
                {"title": "Everything", "content": "All content in one section" * 100}
            ]
        }
        
        verification = {
            "scores": {"structure": 2.0},
            "issues": ["Poor organization", "Needs subsections"]
        }
        
        mock_response = {
            "sections": [
                {
                    "title": "Introduction",
                    "content": "Intro content",
                    "subsections": ["Background", "Motivation"]
                },
                {
                    "title": "Main Content",
                    "content": "Main content",
                    "subsections": ["Part A", "Part B", "Part C"]
                },
                {
                    "title": "Conclusion",
                    "content": "Conclusion content"
                }
            ]
        }
        
        improver.claude_wrapper.query.return_value = mock_response
        
        improved = improver.improve(survey, verification, papers=[])
        
        assert len(improved["sections"]) > 1
        assert any("subsections" in s for s in improved["sections"])
    
    def test_selective_improvement(self, improver):
        """Test that only weak areas are improved"""
        survey = {"sections": [{"title": "Test", "content": "Content"}]}
        
        verification = {
            "scores": {
                "coverage": 4.5,  # Good
                "coherence": 3.0,  # Needs improvement
                "structure": 4.2,  # Good
                "citations": 2.5,  # Needs improvement
                "insights": 4.0   # Good
            }
        }
        
        improver.improve(survey, verification, papers=[])
        
        # Should only call improvements for weak dimensions
        calls = improver.claude_wrapper.query.call_args_list
        
        # Verify improvements were attempted for weak areas
        prompts = [str(call) for call in calls]
        assert any("coherence" in p.lower() for p in prompts)
        assert any("citation" in p.lower() for p in prompts)


class TestGlobalIterativeSystem:
    """Test suite for complete Global Iterative System"""
    
    @pytest.fixture
    def system(self):
        """Create GlobalIterativeSystem instance"""
        with patch('src.our_system.iterative.ClaudeCodeCLIWrapper'):
            with patch('src.our_system.iterative.AutoSurveyBaseline'):
                return GlobalIterativeSystem(max_iterations=5)
    
    @pytest.fixture
    def sample_papers(self):
        """Sample papers for testing"""
        return [
            {"title": f"Paper {i}", "abstract": f"Abstract {i}"}
            for i in range(20)
        ]
    
    def test_initialization(self, system):
        """Test system initialization"""
        assert system.max_iterations == 5
        assert system.convergence_threshold == 4.0
        assert system.verifier is not None
        assert system.improver is not None
        assert system.baseline is not None
    
    def test_single_iteration_convergence(self, system, sample_papers):
        """Test system that converges in one iteration"""
        # Mock baseline to generate high-quality survey
        initial_survey = {
            "title": "High Quality Survey",
            "sections": [
                {"title": f"Section {i}", "content": f"Content {i}" * 50}
                for i in range(5)
            ]
        }
        system.baseline.generate_survey.return_value = initial_survey
        
        # Mock verifier to return high scores
        system.verifier.verify.return_value = {
            "overall_score": 4.5,
            "meets_criteria": True,
            "issues": [],
            "scores": {
                "coverage": 4.5,
                "coherence": 4.5,
                "structure": 4.5,
                "citations": 4.5,
                "insights": 4.5
            }
        }
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        assert result["converged"] == True
        assert result["iterations"] == 1
        assert result["final_score"] >= 4.0
    
    def test_multiple_iteration_improvement(self, system, sample_papers):
        """Test system that improves over multiple iterations"""
        # Initial low-quality survey
        initial_survey = {
            "title": "Initial Survey",
            "sections": [{"title": "Basic", "content": "Short"}]
        }
        system.baseline.generate_survey.return_value = initial_survey
        
        # Mock progressive improvement
        verification_scores = [3.0, 3.5, 3.8, 4.1]
        improved_surveys = [
            {"sections": [{"title": "Improved 1", "content": "Better"}]},
            {"sections": [{"title": "Improved 2", "content": "Much better"}]},
            {"sections": [{"title": "Improved 3", "content": "Even better"}]},
            {"sections": [{"title": "Final", "content": "Best version"}]}
        ]
        
        system.verifier.verify.side_effect = [
            {
                "overall_score": score,
                "meets_criteria": score >= 4.0,
                "issues": ["Some issues"] if score < 4.0 else [],
                "scores": {"coverage": score, "coherence": score, 
                          "structure": score, "citations": score, "insights": score}
            }
            for score in verification_scores
        ]
        
        system.improver.improve.side_effect = improved_surveys
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        assert result["converged"] == True
        assert result["iterations"] == 4
        assert result["final_score"] >= 4.0
        assert len(result["iteration_history"]) == 4
    
    def test_max_iterations_limit(self, system, sample_papers):
        """Test that system stops at max iterations"""
        initial_survey = {"sections": [{"title": "Test", "content": "Test"}]}
        system.baseline.generate_survey.return_value = initial_survey
        
        # Always return low scores
        system.verifier.verify.return_value = {
            "overall_score": 3.0,
            "meets_criteria": False,
            "issues": ["Persistent issues"],
            "scores": {"coverage": 3, "coherence": 3, "structure": 3, 
                      "citations": 3, "insights": 3}
        }
        
        system.improver.improve.return_value = initial_survey  # No improvement
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        assert result["converged"] == False
        assert result["iterations"] == 5  # Max iterations
        assert result["final_score"] < 4.0
    
    def test_iteration_history_tracking(self, system, sample_papers):
        """Test that iteration history is properly tracked"""
        initial_survey = {"sections": []}
        system.baseline.generate_survey.return_value = initial_survey
        
        scores = [3.2, 3.6, 4.1]
        system.verifier.verify.side_effect = [
            {
                "overall_score": score,
                "meets_criteria": score >= 4.0,
                "issues": [],
                "scores": {"coverage": score, "coherence": score,
                          "structure": score, "citations": score, "insights": score}
            }
            for score in scores
        ]
        
        system.improver.improve.return_value = {"sections": []}
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        history = result["iteration_history"]
        assert len(history) == 3
        assert history[0]["score"] == 3.2
        assert history[1]["score"] == 3.6
        assert history[2]["score"] == 4.1
        assert all("improvements" in h for h in history[1:])
    
    def test_no_improvement_detection(self, system, sample_papers):
        """Test detection of no improvement scenario"""
        initial_survey = {"sections": [{"title": "Static", "content": "Same"}]}
        system.baseline.generate_survey.return_value = initial_survey
        
        # Same score repeatedly
        system.verifier.verify.return_value = {
            "overall_score": 3.5,
            "meets_criteria": False,
            "issues": ["Cannot improve"],
            "scores": {"coverage": 3.5, "coherence": 3.5, "structure": 3.5,
                      "citations": 3.5, "insights": 3.5}
        }
        
        system.improver.improve.return_value = initial_survey
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        # Should detect no improvement and stop early
        assert result["converged"] == False
        assert result["iterations"] <= 5
        assert "no_improvement" in result.get("termination_reason", "")
    
    @pytest.mark.parametrize("initial_score,improvements,expected_iterations", [
        (4.2, [], 1),  # Already good
        (3.0, [3.5, 4.1], 3),  # Gradual improvement
        (2.0, [2.5, 3.0, 3.5, 3.8, 3.9], 5),  # Max iterations
    ])
    def test_convergence_patterns(self, system, sample_papers, initial_score, 
                                  improvements, expected_iterations):
        """Test various convergence patterns"""
        system.baseline.generate_survey.return_value = {"sections": []}
        
        scores = [initial_score] + improvements
        system.verifier.verify.side_effect = [
            {
                "overall_score": score,
                "meets_criteria": score >= 4.0,
                "issues": [],
                "scores": {"coverage": score, "coherence": score,
                          "structure": score, "citations": score, "insights": score}
            }
            for score in scores
        ]
        
        system.improver.improve.return_value = {"sections": []}
        
        result = system.generate_iterative_survey(sample_papers, "Test Topic")
        
        assert result["iterations"] == expected_iterations
    
    def test_error_handling(self, system, sample_papers):
        """Test error handling in iterative system"""
        system.baseline.generate_survey.side_effect = Exception("Baseline error")
        
        with pytest.raises(Exception, match="Baseline error"):
            system.generate_iterative_survey(sample_papers, "Test Topic")
    
    def test_score_improvement_validation(self, system):
        """Test that scores actually improve"""
        history = [
            {"score": 3.0},
            {"score": 3.4},
            {"score": 3.7},
            {"score": 4.0}
        ]
        
        improvements = []
        for i in range(1, len(history)):
            improvement = history[i]["score"] - history[i-1]["score"]
            improvements.append(improvement)
        
        # All improvements should be positive
        assert all(imp > 0 for imp in improvements)
        
        # Total improvement
        total_improvement = history[-1]["score"] - history[0]["score"]
        assert total_improvement == pytest.approx(1.0, rel=1e-2)


@pytest.mark.integration
class TestGlobalIterativeIntegration:
    """Integration tests for Global Iterative System"""
    
    def test_full_iterative_workflow(self):
        """Test complete iterative improvement workflow"""
        with patch('src.our_system.iterative.ClaudeCodeCLIWrapper') as mock_wrapper:
            with patch('src.our_system.iterative.AutoSurveyBaseline') as mock_baseline:
                # Setup mocks
                mock_claude = MagicMock()
                mock_wrapper.return_value = mock_claude
                
                mock_baseline_instance = MagicMock()
                mock_baseline.return_value = mock_baseline_instance
                
                # Initial survey
                mock_baseline_instance.generate_survey.return_value = {
                    "title": "Initial Survey",
                    "sections": [
                        {"title": "Intro", "content": "Basic intro"},
                        {"title": "Methods", "content": "Simple methods"}
                    ]
                }
                
                # Progressive verification scores
                verification_responses = [
                    {"overall_score": 3.2, "meets_criteria": False,
                     "scores": {"coverage": 3.0, "coherence": 3.2, "structure": 3.3,
                               "citations": 3.1, "insights": 3.4}},
                    {"overall_score": 3.7, "meets_criteria": False,
                     "scores": {"coverage": 3.6, "coherence": 3.7, "structure": 3.8,
                               "citations": 3.6, "insights": 3.8}},
                    {"overall_score": 4.2, "meets_criteria": True,
                     "scores": {"coverage": 4.1, "coherence": 4.2, "structure": 4.3,
                               "citations": 4.1, "insights": 4.3}}
                ]
                
                mock_claude.query.side_effect = [
                    verification_responses[0],  # First verification
                    {"sections": [{"title": "Improved", "content": "Better"}]},  # First improvement
                    verification_responses[1],  # Second verification
                    {"sections": [{"title": "More Improved", "content": "Much better"}]},  # Second improvement
                    verification_responses[2],  # Final verification
                ]
                
                system = GlobalIterativeSystem()
                
                papers = [{"title": f"Paper {i}"} for i in range(10)]
                result = system.generate_iterative_survey(papers, "Test Topic")
                
                assert result["converged"] == True
                assert result["iterations"] == 3
                assert result["final_score"] >= 4.0
                assert len(result["iteration_history"]) == 3
                
                # Verify improvement trend
                scores = [h["score"] for h in result["iteration_history"]]
                assert scores == [3.2, 3.7, 4.2]
    
    def test_performance_tracking(self):
        """Test performance metrics during iteration"""
        from src.evaluation.metrics import PerformanceMetrics
        
        with patch('src.our_system.iterative.ClaudeCodeCLIWrapper'):
            with patch('src.our_system.iterative.AutoSurveyBaseline'):
                system = GlobalIterativeSystem()
                system.performance_tracker = PerformanceMetrics()
                
                # Mock simple convergence
                system.baseline.generate_survey.return_value = {"sections": []}
                system.verifier.verify.return_value = {
                    "overall_score": 4.5,
                    "meets_criteria": True,
                    "issues": [],
                    "scores": {"coverage": 4.5, "coherence": 4.5,
                              "structure": 4.5, "citations": 4.5, "insights": 4.5}
                }
                
                import time
                start = time.time()
                result = system.generate_iterative_survey([], "Topic")
                duration = time.time() - start
                
                # Should track performance
                assert result["performance"]["total_time"] >= 0
                assert result["performance"]["iterations"] == 1
                assert "api_calls" in result["performance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])