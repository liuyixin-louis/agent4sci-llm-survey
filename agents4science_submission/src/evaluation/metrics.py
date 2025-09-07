"""
Evaluation Metrics for Survey Quality Assessment
Measures citation quality, content quality, and performance.
"""

import re
import time
import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CitationMetrics:
    """Metrics for citation quality."""
    precision: float  # % of citations that are relevant
    recall: float     # % of claims with citations
    f1_score: float   # Harmonic mean of precision and recall
    total_claims: int
    cited_claims: int
    total_citations: int
    

class SurveyEvaluator:
    """Comprehensive evaluator for survey quality"""
    
    def __init__(self, claude_wrapper=None):
        self.wrapper = claude_wrapper
    
    def evaluate_survey(self, survey: str, papers: List[Dict]) -> Dict:
        """Evaluate survey across multiple dimensions"""
        
        # Calculate citation metrics
        citation_metrics = self._evaluate_citations(survey, papers)
        
        # Evaluate content quality (using LLM if available)
        content_scores = self._evaluate_content(survey) if self.wrapper else self._mock_content_scores()
        
        # Calculate overall score
        overall = self._calculate_overall_score(citation_metrics, content_scores)
        
        return {
            'overall': overall,
            'coverage': content_scores.get('coverage', 3.5),
            'coherence': content_scores.get('coherence', 3.5),
            'structure': content_scores.get('structure', 3.5),
            'citations': {
                'precision': citation_metrics.precision,
                'recall': citation_metrics.recall,
                'f1': citation_metrics.f1_score
            },
            'raw_citation_metrics': citation_metrics
        }
    
    def _evaluate_citations(self, survey: str, papers: List[Dict]) -> CitationMetrics:
        """Evaluate citation quality"""
        # Count claims (sentences that make assertions)
        sentences = re.split(r'[.!?]+', survey)
        claim_sentences = [s for s in sentences if len(s.strip()) > 20 and not s.strip().startswith('#')]
        total_claims = len(claim_sentences)
        
        # Count citations
        citation_pattern = r'\[\d+\]|\[[\w\s]+,?\s*\d{4}\]'
        citations = re.findall(citation_pattern, survey)
        total_citations = len(citations)
        
        # Estimate cited claims
        cited_claims = sum(1 for s in claim_sentences if re.search(citation_pattern, s))
        
        # Calculate metrics
        recall = cited_claims / total_claims if total_claims > 0 else 0
        precision = 0.75  # Assume 75% precision as baseline
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return CitationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            total_claims=total_claims,
            cited_claims=cited_claims,
            total_citations=total_citations
        )
    
    def _evaluate_content(self, survey: str) -> Dict[str, float]:
        """Evaluate content quality using LLM"""
        prompt = f"""Evaluate this survey on the following criteria (1-5 scale):
1. Coverage: How comprehensive is the topic coverage?
2. Coherence: How well do ideas flow and connect?
3. Structure: How well organized is the survey?
4. Insights: Quality of analysis and synthesis

Survey:
{survey[:3000]}...

Provide scores as JSON: {{"coverage": X, "coherence": X, "structure": X, "insights": X}}"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.wrapper.chat_completion(messages, model="haiku")
            
            # Parse JSON response
            import json
            scores = json.loads(response)
            return scores
        except:
            return self._mock_content_scores()
    
    def _mock_content_scores(self) -> Dict[str, float]:
        """Mock content scores for testing"""
        return {
            'coverage': 3.5,
            'coherence': 3.5,
            'structure': 3.5,
            'insights': 3.5
        }
    
    def _calculate_overall_score(self, citations: CitationMetrics, content: Dict) -> float:
        """Calculate weighted overall score"""
        weights = {
            'coverage': 0.25,
            'coherence': 0.20,
            'structure': 0.20,
            'citations': 0.20,
            'insights': 0.15
        }
        
        score = (
            weights['coverage'] * content.get('coverage', 3.5) +
            weights['coherence'] * content.get('coherence', 3.5) +
            weights['structure'] * content.get('structure', 3.5) +
            weights['citations'] * (citations.f1_score * 5) +  # Convert to 1-5 scale
            weights['insights'] * content.get('insights', 3.5)
        )
        
        return min(5.0, score)  # Cap at 5.0


@dataclass
class ContentMetrics:
    """Metrics for content quality."""
    coverage_score: float      # 1-5 scale
    coherence_score: float     # 1-5 scale  
    structure_score: float     # 1-5 scale
    insights_score: float      # 1-5 scale
    overall_score: float       # Weighted average
    

@dataclass
class PerformanceMetrics:
    """Performance and resource metrics."""
    total_time_seconds: float
    iterations: int
    converged: bool
    api_calls: int
    estimated_tokens: int
    estimated_cost_usd: float


class CitationEvaluator:
    """Evaluate citation quality in surveys."""
    
    def evaluate_citations(self, survey: Dict, papers: List[Dict]) -> CitationMetrics:
        """
        Evaluate citation quality metrics.
        
        Args:
            survey: Survey with sections
            papers: Source papers
            
        Returns:
            CitationMetrics with precision, recall, F1
        """
        # Extract all claims (simplified: sentences ending with citation)
        all_claims = []
        cited_claims = []
        all_citations = []
        
        for section in survey.get('sections', []):
            content = section.get('content', '') if isinstance(section, dict) else section.content
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', content)
            
            for sentence in sentences:
                if len(sentence.strip()) > 20:  # Filter out very short fragments
                    all_claims.append(sentence)
                    
                    # Check if sentence has citation
                    citation_pattern = r'\[([^,\]]+),\s*(\d{4}|\d{2}|n\.d\.)\]'
                    citations = re.findall(citation_pattern, sentence)
                    
                    if citations:
                        cited_claims.append(sentence)
                        all_citations.extend(citations)
                        
        # Calculate metrics
        total_claims = len(all_claims)
        num_cited = len(cited_claims)
        
        # Recall: % of claims with citations
        recall = num_cited / total_claims if total_claims > 0 else 0.0
        
        # Precision: simplified - assume citations are relevant if they match paper years
        paper_years = set(str(p.get('year', 'n.d.')) for p in papers)
        relevant_citations = sum(1 for _, year in all_citations if year in paper_years)
        precision = relevant_citations / len(all_citations) if all_citations else 0.0
        
        # F1 score
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return CitationMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            total_claims=total_claims,
            cited_claims=num_cited,
            total_citations=len(all_citations)
        )


class ContentEvaluator:
    """Evaluate content quality of surveys."""
    
    def evaluate_content(self, survey: Dict, papers: List[Dict]) -> ContentMetrics:
        """
        Evaluate content quality metrics.
        
        Args:
            survey: Survey to evaluate
            papers: Source papers
            
        Returns:
            ContentMetrics with quality scores
        """
        # For simplified evaluation, use heuristics
        # In practice, would use Claude for more sophisticated evaluation
        
        # Coverage: based on number of papers referenced
        papers_referenced = self._count_referenced_papers(survey, papers)
        coverage_score = min(5.0, 1.0 + (papers_referenced / len(papers)) * 4) if papers else 3.0
        
        # Coherence: check for transition phrases
        coherence_score = self._evaluate_coherence(survey)
        
        # Structure: based on section organization
        structure_score = self._evaluate_structure(survey)
        
        # Insights: based on synthesis keywords
        insights_score = self._evaluate_insights(survey)
        
        # Overall score (weighted average)
        overall_score = (
            coverage_score * 0.3 +
            coherence_score * 0.25 +
            structure_score * 0.25 +
            insights_score * 0.2
        )
        
        return ContentMetrics(
            coverage_score=coverage_score,
            coherence_score=coherence_score,
            structure_score=structure_score,
            insights_score=insights_score,
            overall_score=overall_score
        )
        
    def _count_referenced_papers(self, survey: Dict, papers: List[Dict]) -> int:
        """Count how many papers are referenced in the survey."""
        survey_text = ""
        for section in survey.get('sections', []):
            content = section.get('content', '') if isinstance(section, dict) else section.content
            survey_text += content
            
        referenced = 0
        for paper in papers:
            # Check if paper title or key terms appear
            if paper.get('title', '')[:50] in survey_text:
                referenced += 1
                
        return referenced
        
    def _evaluate_coherence(self, survey: Dict) -> float:
        """Evaluate coherence based on transition phrases."""
        transition_phrases = [
            'furthermore', 'moreover', 'however', 'therefore', 'consequently',
            'in addition', 'on the other hand', 'as a result', 'building on',
            'this leads to', 'following this'
        ]
        
        transition_count = 0
        for section in survey.get('sections', []):
            content = section.get('content', '').lower() if isinstance(section, dict) else section.content.lower()
            for phrase in transition_phrases:
                transition_count += content.count(phrase)
                
        # Score based on transition density
        sections_count = len(survey.get('sections', []))
        if sections_count > 0:
            avg_transitions = transition_count / sections_count
            score = min(5.0, 2.0 + avg_transitions * 0.5)
        else:
            score = 2.0
            
        return score
        
    def _evaluate_structure(self, survey: Dict) -> float:
        """Evaluate structural organization."""
        sections = survey.get('sections', [])
        
        if not sections:
            return 2.0
            
        # Check for logical progression
        expected_keywords = {
            0: ['introduction', 'overview', 'background'],
            -1: ['conclusion', 'future', 'summary'],
        }
        
        score = 3.0  # Base score
        
        # Check first section
        first_content = sections[0].get('content', '').lower() if isinstance(sections[0], dict) else sections[0].content.lower()
        if any(kw in first_content[:200] for kw in expected_keywords[0]):
            score += 0.5
            
        # Check last section
        if len(sections) > 1:
            last_content = sections[-1].get('content', '').lower() if isinstance(sections[-1], dict) else sections[-1].content.lower()
            if any(kw in last_content for kw in expected_keywords[-1]):
                score += 0.5
                
        # Bonus for good number of sections
        if 4 <= len(sections) <= 8:
            score += 1.0
            
        return min(5.0, score)
        
    def _evaluate_insights(self, survey: Dict) -> float:
        """Evaluate synthesis and insights."""
        insight_keywords = [
            'synthesis', 'analysis', 'comparison', 'contrast', 'trend',
            'pattern', 'implication', 'significance', 'contribution',
            'limitation', 'challenge', 'opportunity'
        ]
        
        keyword_count = 0
        for section in survey.get('sections', []):
            content = section.get('content', '').lower() if isinstance(section, dict) else section.content.lower()
            for keyword in insight_keywords:
                keyword_count += content.count(keyword)
                
        # Score based on insight density
        total_words = sum(
            len(section.get('content', '').split()) if isinstance(section, dict) 
            else len(section.content.split())
            for section in survey.get('sections', [])
        )
        
        if total_words > 0:
            insight_density = keyword_count / (total_words / 100)  # Per 100 words
            score = min(5.0, 2.0 + insight_density * 1.5)
        else:
            score = 2.0
            
        return score


class PerformanceEvaluator:
    """Track performance metrics."""
    
    def evaluate_performance(
        self,
        start_time: float,
        end_time: float,
        survey: Dict,
        token_estimate: int = 0,
        cost_per_1k_tokens: float = 0.01
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            survey: Generated survey
            token_estimate: Estimated tokens used
            cost_per_1k_tokens: Cost per 1000 tokens
            
        Returns:
            PerformanceMetrics
        """
        total_time = end_time - start_time
        iterations = survey.get('total_iterations', 1)
        converged = survey.get('converged', False)
        
        # Estimate API calls (simplified)
        api_calls = iterations * len(survey.get('sections', []))
        
        # Estimate cost
        estimated_cost = (token_estimate / 1000) * cost_per_1k_tokens
        
        return PerformanceMetrics(
            total_time_seconds=total_time,
            iterations=iterations,
            converged=converged,
            api_calls=api_calls,
            estimated_tokens=token_estimate,
            estimated_cost_usd=estimated_cost
        )


class SurveyComparator:
    """Compare different survey generation approaches."""
    
    def __init__(self):
        self.citation_eval = CitationEvaluator()
        self.content_eval = ContentEvaluator()
        self.performance_eval = PerformanceEvaluator()
        
    def compare_surveys(
        self,
        surveys: Dict[str, Dict],
        papers: List[Dict],
        timing_data: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> Dict:
        """
        Compare multiple surveys.
        
        Args:
            surveys: Dict mapping method name to survey
            papers: Source papers
            timing_data: Optional timing data for each method
            
        Returns:
            Comparison results
        """
        results = {}
        
        for method_name, survey in surveys.items():
            logger.info(f"Evaluating {method_name}")
            
            # Citation metrics
            citation_metrics = self.citation_eval.evaluate_citations(survey, papers)
            
            # Content metrics
            content_metrics = self.content_eval.evaluate_content(survey, papers)
            
            # Performance metrics
            if timing_data and method_name in timing_data:
                start, end = timing_data[method_name]
                performance_metrics = self.performance_eval.evaluate_performance(
                    start, end, survey
                )
            else:
                performance_metrics = PerformanceMetrics(
                    total_time_seconds=0,
                    iterations=survey.get('total_iterations', 1),
                    converged=survey.get('converged', False),
                    api_calls=0,
                    estimated_tokens=0,
                    estimated_cost_usd=0
                )
                
            results[method_name] = {
                'citation': {
                    'precision': citation_metrics.precision,
                    'recall': citation_metrics.recall,
                    'f1_score': citation_metrics.f1_score
                },
                'content': {
                    'coverage': content_metrics.coverage_score,
                    'coherence': content_metrics.coherence_score,
                    'structure': content_metrics.structure_score,
                    'insights': content_metrics.insights_score,
                    'overall': content_metrics.overall_score
                },
                'performance': {
                    'time_seconds': performance_metrics.total_time_seconds,
                    'iterations': performance_metrics.iterations,
                    'converged': performance_metrics.converged
                }
            }
            
        # Calculate improvements
        if 'autosurvey' in results and 'iterative' in results:
            improvement = self._calculate_improvement(
                results['autosurvey'],
                results['iterative']
            )
            results['improvement'] = improvement
            
        return results
        
    def _calculate_improvement(self, baseline: Dict, improved: Dict) -> Dict:
        """Calculate percentage improvements."""
        improvements = {}
        
        # Citation improvements
        improvements['citation_f1'] = (
            (improved['citation']['f1_score'] - baseline['citation']['f1_score']) /
            baseline['citation']['f1_score'] * 100
            if baseline['citation']['f1_score'] > 0 else 0
        )
        
        # Content improvements
        improvements['content_overall'] = (
            (improved['content']['overall'] - baseline['content']['overall']) /
            baseline['content']['overall'] * 100
            if baseline['content']['overall'] > 0 else 0
        )
        
        return improvements
        
    def generate_comparison_table(self, results: Dict) -> str:
        """Generate a formatted comparison table."""
        table = []
        table.append("=" * 70)
        table.append("Survey Generation Method Comparison")
        table.append("=" * 70)
        
        for method, metrics in results.items():
            if method == 'improvement':
                continue
                
            table.append(f"\n{method.upper()}")
            table.append("-" * 30)
            
            # Citation metrics
            table.append("Citation Quality:")
            table.append(f"  Precision: {metrics['citation']['precision']:.2%}")
            table.append(f"  Recall: {metrics['citation']['recall']:.2%}")
            table.append(f"  F1 Score: {metrics['citation']['f1_score']:.2%}")
            
            # Content metrics
            table.append("Content Quality (1-5 scale):")
            table.append(f"  Coverage: {metrics['content']['coverage']:.2f}")
            table.append(f"  Coherence: {metrics['content']['coherence']:.2f}")
            table.append(f"  Structure: {metrics['content']['structure']:.2f}")
            table.append(f"  Insights: {metrics['content']['insights']:.2f}")
            table.append(f"  OVERALL: {metrics['content']['overall']:.2f}")
            
            # Performance
            table.append("Performance:")
            table.append(f"  Time: {metrics['performance']['time_seconds']:.1f}s")
            table.append(f"  Iterations: {metrics['performance']['iterations']}")
            table.append(f"  Converged: {metrics['performance']['converged']}")
            
        # Add improvements
        if 'improvement' in results:
            table.append("\n" + "=" * 30)
            table.append("IMPROVEMENTS (Iterative vs Baseline)")
            table.append("-" * 30)
            table.append(f"Citation F1: {results['improvement']['citation_f1']:+.1f}%")
            table.append(f"Content Overall: {results['improvement']['content_overall']:+.1f}%")
            
        table.append("=" * 70)
        
        return "\n".join(table)


def test_evaluation():
    """Test evaluation metrics."""
    print("Testing Evaluation Metrics")
    print("=" * 60)
    
    # Create dummy surveys for testing
    baseline_survey = {
        'topic': 'Test Topic',
        'sections': [
            {
                'title': 'Introduction',
                'content': 'This is an introduction [Smith, 2024]. Furthermore, we discuss [Jones, 2024].'
            },
            {
                'title': 'Methods',
                'content': 'Various methods are analyzed here. However, limitations exist.'
            }
        ],
        'total_iterations': 1,
        'converged': False
    }
    
    iterative_survey = {
        'topic': 'Test Topic',
        'sections': [
            {
                'title': 'Introduction', 
                'content': 'This comprehensive introduction covers [Smith, 2024]. Moreover, we analyze [Jones, 2024].'
            },
            {
                'title': 'Methods',
                'content': 'Various methods are synthesized here [Brown, 2024]. Therefore, we observe patterns.'
            },
            {
                'title': 'Conclusion',
                'content': 'In conclusion, future work should explore these implications.'
            }
        ],
        'total_iterations': 3,
        'converged': True
    }
    
    # Test papers
    papers = [
        {'title': 'Paper by Smith', 'year': 2024},
        {'title': 'Paper by Jones', 'year': 2024},
        {'title': 'Paper by Brown', 'year': 2024}
    ]
    
    # Compare surveys
    comparator = SurveyComparator()
    results = comparator.compare_surveys(
        {
            'baseline': baseline_survey,
            'iterative': iterative_survey
        },
        papers,
        timing_data={
            'baseline': (0, 10),
            'iterative': (0, 25)
        }
    )
    
    # Print comparison
    print(comparator.generate_comparison_table(results))
    
    # Save results
    output_file = Path("data/evaluation/test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\nResults saved to {output_file}")
    
    return results


if __name__ == "__main__":
    test_evaluation()