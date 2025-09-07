"""
Global Iterative Improvement System
Our novel approach using global verification-driven iteration for survey generation.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import pickle

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper
from src.baselines.autosurvey import AutoSurveyBaseline, SurveySection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Results from global verification."""
    overall_score: float  # 1-5 scale
    coverage_score: float
    structure_score: float
    coherence_score: float
    citation_score: float
    insights_score: float
    critical_issues: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    section_scores: Dict[str, float] = field(default_factory=dict)
    
    def meets_convergence_criteria(self) -> bool:
        """Check if survey meets convergence criteria."""
        return (
            self.overall_score >= 4.0 and
            self.citation_score >= 4.0 and
            len(self.critical_issues) == 0
        )


class GlobalVerifier:
    """
    Global verification system for survey quality assessment.
    Uses multi-criteria evaluation across the entire survey.
    """
    
    def __init__(self, claude_wrapper: Optional[EnhancedClaudeWrapper] = None):
        """
        Initialize with a Claude wrapper.
        
        Args:
            claude_wrapper: Optional EnhancedClaudeWrapper instance for LLM interactions.
                          If None, creates a new instance.
        """
        self.claude_wrapper = claude_wrapper or EnhancedClaudeWrapper()
        
    def verify_survey(self, survey: Dict, papers: List[Dict]) -> VerificationResult:
        """
        Perform global verification of survey quality.
        
        Args:
            survey: Survey dictionary with sections
            papers: Papers used for the survey
            
        Returns:
            VerificationResult with scores and issues
        """
        logger.info("Performing global verification")
        
        # Prepare survey text
        survey_text = self._format_survey_for_verification(survey)
        papers_summary = self._format_papers_summary(papers[:20])  # Sample papers
        
        # Multi-criteria evaluation prompt
        messages = [
            {
                "role": "system",
                "content": "You are an expert survey evaluator assessing academic survey quality."
            },
            {
                "role": "user",
                "content": f"""Evaluate this survey globally across multiple criteria.

Survey Topic: {survey.get('topic', 'Unknown')}

Survey Content:
{survey_text}

Reference Papers (sample):
{papers_summary}

Evaluate on a 1-5 scale for each criterion:
1. Coverage: Does the survey comprehensively cover the topic?
2. Structure: Is the survey well-organized with logical flow?
3. Coherence: Are sections connected with smooth transitions?
4. Citations: Are claims properly supported with citations?
5. Insights: Does the survey provide valuable synthesis and insights?

Respond in JSON format:
{{
    "coverage_score": 0.0,
    "structure_score": 0.0,
    "coherence_score": 0.0,
    "citation_score": 0.0,
    "insights_score": 0.0,
    "critical_issues": ["issue1", "issue2"],
    "improvement_suggestions": ["suggestion1", "suggestion2"]
}}"""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="sonnet",  # Use balanced model for verification
            use_cache=False
        )
        
        if "error" in response:
            logger.error(f"Verification error: {response['error']}")
            return self._default_verification_result()
            
        # Parse response
        try:
            content = response["choices"][0]["message"]["content"]
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                scores_data = json.loads(json_match.group())
            else:
                scores_data = {}
                
            # Create verification result
            result = VerificationResult(
                coverage_score=float(scores_data.get('coverage_score', 3.0)),
                structure_score=float(scores_data.get('structure_score', 3.0)),
                coherence_score=float(scores_data.get('coherence_score', 3.0)),
                citation_score=float(scores_data.get('citation_score', 3.0)),
                insights_score=float(scores_data.get('insights_score', 3.0)),
                critical_issues=scores_data.get('critical_issues', []),
                improvement_suggestions=scores_data.get('improvement_suggestions', []),
                overall_score=0.0  # Calculate below
            )
            
            # Calculate overall score (weighted average)
            result.overall_score = (
                result.coverage_score * 0.25 +
                result.structure_score * 0.20 +
                result.coherence_score * 0.20 +
                result.citation_score * 0.20 +
                result.insights_score * 0.15
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing verification response: {e}")
            return self._default_verification_result()
            
    def _format_survey_for_verification(self, survey: Dict) -> str:
        """Format survey for verification prompt."""
        parts = []
        for section in survey.get('sections', []):
            if isinstance(section, SurveySection):
                parts.append(f"\n## {section.title}\n{section.content[:500]}...")
            elif isinstance(section, dict):
                parts.append(f"\n## {section.get('title', 'Untitled')}\n{section.get('content', '')[:500]}...")
        return "\n".join(parts)
        
    def _format_papers_summary(self, papers: List[Dict]) -> str:
        """Format papers summary for context."""
        summary = []
        for i, paper in enumerate(papers, 1):
            summary.append(f"{i}. {paper.get('title', 'Unknown')[:100]}")
        return "\n".join(summary)
        
    def _default_verification_result(self) -> VerificationResult:
        """Return default verification result when verification fails."""
        return VerificationResult(
            overall_score=3.0,
            coverage_score=3.0,
            structure_score=3.0,
            coherence_score=3.0,
            citation_score=3.0,
            insights_score=3.0,
            critical_issues=["Verification failed"],
            improvement_suggestions=["Manual review needed"]
        )


class TargetedImprover:
    """
    Generate targeted improvements based on verification results.
    """
    
    def __init__(self, claude_wrapper: Optional[EnhancedClaudeWrapper] = None):
        """
        Initialize with a Claude wrapper.
        
        Args:
            claude_wrapper: Optional EnhancedClaudeWrapper instance for LLM interactions.
                          If None, creates a new instance.
        """
        self.claude_wrapper = claude_wrapper or EnhancedClaudeWrapper()
        
    def improve_survey(
        self,
        survey: Dict,
        verification: VerificationResult,
        papers: List[Dict]
    ) -> Dict:
        """
        Improve survey based on verification results.
        
        Args:
            survey: Current survey
            verification: Verification results
            papers: Available papers
            
        Returns:
            Improved survey
        """
        logger.info(f"Applying targeted improvements (overall score: {verification.overall_score:.2f})")
        
        # Identify weakest areas
        improvements_needed = self._identify_improvements(verification)
        
        # Apply improvements
        improved_survey = survey.copy()
        
        for improvement_type in improvements_needed:
            if improvement_type == 'coverage':
                improved_survey = self._improve_coverage(improved_survey, papers)
            elif improvement_type == 'coherence':
                improved_survey = self._improve_coherence(improved_survey)
            elif improvement_type == 'citations':
                improved_survey = self._improve_citations(improved_survey, papers)
            elif improvement_type == 'structure':
                improved_survey = self._improve_structure(improved_survey)
                
        return improved_survey
        
    def _identify_improvements(self, verification: VerificationResult) -> List[str]:
        """Identify which improvements to prioritize."""
        improvements = []
        
        # Check each score against threshold
        if verification.coverage_score < 3.5:
            improvements.append('coverage')
        if verification.coherence_score < 3.5:
            improvements.append('coherence')
        if verification.citation_score < 3.5:
            improvements.append('citations')
        if verification.structure_score < 3.5:
            improvements.append('structure')
            
        return improvements
        
    def _improve_coverage(self, survey: Dict, papers: List[Dict]) -> Dict:
        """Improve content coverage."""
        logger.info("Improving coverage")
        
        # Identify missing topics
        survey_text = " ".join([
            s.content if isinstance(s, SurveySection) else s.get('content', '')
            for s in survey.get('sections', [])
        ])
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at identifying gaps in survey coverage."
            },
            {
                "role": "user",
                "content": f"""Identify 2-3 important topics missing from this survey:

Current survey (summary):
{survey_text[:1000]}...

Add 1-2 paragraphs covering the most important missing topics.
Focus on topics that appear in recent papers but aren't well covered."""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="haiku",  # Fast model for improvements
            use_cache=False
        )
        
        if "error" not in response:
            additional_content = response["choices"][0]["message"]["content"]
            # Add to conclusion or create new section
            if survey.get('sections'):
                last_section = survey['sections'][-1]
                if isinstance(last_section, SurveySection):
                    last_section.content += f"\n\n{additional_content}"
                elif isinstance(last_section, dict):
                    last_section['content'] = last_section.get('content', '') + f"\n\n{additional_content}"
                    
        return survey
        
    def _improve_coherence(self, survey: Dict) -> Dict:
        """Improve section transitions and flow."""
        logger.info("Improving coherence")
        
        sections = survey.get('sections', [])
        if len(sections) < 2:
            return survey
            
        # Add transition sentences between sections
        for i in range(len(sections) - 1):
            current = sections[i]
            next_sec = sections[i + 1]
            
            current_title = current.title if isinstance(current, SurveySection) else current.get('title', '')
            next_title = next_sec.title if isinstance(next_sec, SurveySection) else next_sec.get('title', '')
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating smooth transitions."
                },
                {
                    "role": "user",
                    "content": f"""Create a 1-2 sentence transition from "{current_title}" to "{next_title}".
Make it natural and maintain flow."""
                }
            ]
            
            response = self.claude_wrapper.chat_completion(
                messages=messages,
                model="haiku",
                use_cache=True
            )
            
            if "error" not in response:
                transition = response["choices"][0]["message"]["content"]
                if isinstance(current, SurveySection):
                    current.content += f"\n\n{transition}"
                elif isinstance(current, dict):
                    current['content'] = current.get('content', '') + f"\n\n{transition}"
                    
        return survey
        
    def _improve_citations(self, survey: Dict, papers: List[Dict]) -> Dict:
        """Add missing citations."""
        logger.info("Improving citations")
        # Simplified: just ensure sections have some citations mentioned
        # In practice, would do more sophisticated citation matching
        return survey
        
    def _improve_structure(self, survey: Dict) -> Dict:
        """Improve survey organization."""
        logger.info("Improving structure")
        # Simplified: could reorder sections, merge similar ones, etc.
        return survey


class IterativeSurveySystem:
    """
    Main system for iterative survey generation with global verification.
    Our novel contribution - uses global assessment and targeted improvement.
    """
    
    def __init__(
        self,
        base_generator: Optional[AutoSurveyBaseline] = None,
        verifier: Optional[GlobalVerifier] = None,
        improver: Optional[TargetedImprover] = None,
        max_iterations: int = 5,
        checkpoint_dir: str = "data/checkpoints"
    ):
        """
        Initialize iterative system.
        
        Args:
            base_generator: Base survey generator (AutoSurvey)
            verifier: Global verifier
            improver: Targeted improver
            max_iterations: Maximum iterations before stopping
            checkpoint_dir: Directory for saving checkpoints
        """
        self.base_generator = base_generator or AutoSurveyBaseline()
        self.verifier = verifier or GlobalVerifier()
        self.improver = improver or TargetedImprover()
        self.max_iterations = max_iterations
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_survey_iteratively(
        self,
        papers: List[Dict],
        topic: str,
        target_sections: int = 6
    ) -> Dict:
        """
        Generate survey with iterative global improvement.
        
        Args:
            papers: Papers for the survey
            topic: Survey topic
            target_sections: Number of sections
            
        Returns:
            Final survey with iteration history
        """
        logger.info(f"Starting iterative survey generation for '{topic}'")
        
        # Generate initial survey
        logger.info("Iteration 0: Generating base survey")
        current_survey = self.base_generator.generate_survey(
            papers, topic, target_sections
        )
        
        iteration_history = []
        converged = False
        
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\nIteration {iteration}/{self.max_iterations}")
            
            # Global verification
            verification = self.verifier.verify_survey(current_survey, papers)
            logger.info(f"Verification score: {verification.overall_score:.2f}")
            
            # Save checkpoint
            self._save_checkpoint(current_survey, iteration, verification)
            
            # Record iteration
            iteration_history.append({
                'iteration': iteration,
                'overall_score': verification.overall_score,
                'coverage_score': verification.coverage_score,
                'coherence_score': verification.coherence_score,
                'citation_score': verification.citation_score,
                'critical_issues': verification.critical_issues
            })
            
            # Check convergence
            if verification.meets_convergence_criteria():
                logger.info(f"Converged at iteration {iteration}!")
                converged = True
                break
                
            # Apply targeted improvements
            current_survey = self.improver.improve_survey(
                current_survey, verification, papers
            )
            
        # Final survey with metadata
        final_survey = current_survey
        final_survey['iteration_history'] = iteration_history
        final_survey['converged'] = converged
        final_survey['total_iterations'] = len(iteration_history)
        final_survey['method'] = 'global_iterative'
        
        return final_survey
        
    def _save_checkpoint(
        self,
        survey: Dict,
        iteration: int,
        verification: VerificationResult
    ):
        """Save iteration checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"iter_{iteration}_{time.time()}.pkl"
        checkpoint_data = {
            'survey': survey,
            'iteration': iteration,
            'verification': verification,
            'timestamp': time.time()
        }
        
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        logger.debug(f"Saved checkpoint to {checkpoint_file}")


def test_iterative_system():
    """Test the iterative survey system."""
    print("Testing Global Iterative Survey System")
    print("=" * 60)
    
    # Create simple test papers
    test_papers = [
        {
            'title': f'Paper {i}: Study on Transformers',
            'summary': f'This paper discusses transformer architecture aspect {i}',
            'authors': [f'Author{i}'],
            'year': 2024
        }
        for i in range(1, 11)
    ]
    
    # Initialize system
    system = IterativeSurveySystem(max_iterations=3)
    
    # Generate survey iteratively
    print("\nGenerating survey with global iteration...")
    survey = system.generate_survey_iteratively(
        papers=test_papers,
        topic="Transformer Architectures",
        target_sections=4
    )
    
    # Show results
    print(f"\nCompleted in {survey['total_iterations']} iterations")
    print(f"Converged: {survey['converged']}")
    
    print("\nIteration history:")
    for iter_data in survey['iteration_history']:
        print(f"  Iteration {iter_data['iteration']}: "
              f"Score={iter_data['overall_score']:.2f}, "
              f"Issues={len(iter_data['critical_issues'])}")
        
    # Save result
    output_file = Path("data/surveys/iterative_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert for JSON serialization
    json_survey = {
        'topic': survey['topic'],
        'method': survey['method'],
        'converged': survey['converged'],
        'total_iterations': survey['total_iterations'],
        'iteration_history': survey['iteration_history'],
        'num_sections': len(survey.get('sections', []))
    }
    
    with open(output_file, 'w') as f:
        json.dump(json_survey, f, indent=2)
        
    print(f"\nResults saved to {output_file}")
    
    return survey


if __name__ == "__main__":
    test_iterative_system()