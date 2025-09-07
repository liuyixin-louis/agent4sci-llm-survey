"""
Main Experiment Runner
Compares AutoSurvey baseline, AutoSurvey+LCE, and our Global Iterative approach.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.data_loader import SciMCPDataLoader
from src.discovery.topic_discovery import HierarchicalTopicDiscovery
from src.baselines.autosurvey import AutoSurveyBaseline, AutoSurveyLCE
from src.our_system.iterative import IterativeSurveySystem
from src.evaluation.metrics import SurveyComparator
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Run comparative experiments on survey generation methods."""
    
    def __init__(
        self,
        output_dir: str = "outputs",
        use_cached_data: bool = True
    ):
        """
        Initialize experiment runner.
        
        Args:
            output_dir: Directory for outputs
            use_cached_data: Whether to use cached data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.surveys_dir = self.output_dir / "surveys"
        self.checkpoints_dir = self.output_dir / "checkpoints"
        self.results_dir = self.output_dir / "results"
        
        for dir_path in [self.surveys_dir, self.checkpoints_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Initialize components
        logger.info("Initializing experiment components...")
        self.data_loader = SciMCPDataLoader()
        self.claude_wrapper = EnhancedClaudeWrapper(
            rate_limit_enabled=True,
            min_delay=2.0  # 2 seconds between calls
        )
        self.comparator = SurveyComparator()
        
        # Load data
        if use_cached_data:
            logger.info("Loading cached data...")
            self.papers_df = self.data_loader.load_data()
            
    def run_experiments(
        self,
        topics: List[str],
        papers_per_topic: int = 30,
        max_iterations: int = 3,
        use_fallback: bool = True
    ) -> Dict:
        """
        Run experiments on specified topics.
        
        Args:
            topics: Topics to generate surveys for
            papers_per_topic: Number of papers per topic
            max_iterations: Max iterations for iterative system
            use_fallback: Use fallback topics if discovery fails
            
        Returns:
            Experiment results
        """
        logger.info(f"Starting experiments on {len(topics)} topics")
        
        # Fallback topics if needed
        if use_fallback and not topics:
            topics = [
                "LLM Agents and Tool Use",
                "In-context Learning"
            ]
            logger.info(f"Using fallback topics: {topics}")
            
        all_results = {}
        
        for topic in topics:
            logger.info(f"\n{'='*60}")
            logger.info(f"Experimenting on topic: {topic}")
            logger.info(f"{'='*60}")
            
            # Get papers for topic
            papers = self._get_papers_for_topic(topic, papers_per_topic)
            logger.info(f"Retrieved {len(papers)} papers for '{topic}'")
            
            if len(papers) < 10:
                logger.warning(f"Not enough papers for topic '{topic}', skipping")
                continue
                
            # Run each method
            topic_results = {}
            timing_data = {}
            
            # 1. AutoSurvey Baseline
            logger.info("\n1. Running AutoSurvey Baseline...")
            start_time = time.time()
            try:
                autosurvey = AutoSurveyBaseline(
                    claude_wrapper=self.claude_wrapper,
                    chunk_size=15,
                    max_workers=2
                )
                baseline_survey = autosurvey.generate_survey(
                    papers=papers,
                    topic=topic,
                    target_sections=5
                )
                end_time = time.time()
                timing_data['autosurvey'] = (start_time, end_time)
                logger.info(f"AutoSurvey completed in {end_time - start_time:.1f}s")
                
                # Save survey
                self._save_survey(baseline_survey, f"{topic}_autosurvey")
                topic_results['autosurvey'] = baseline_survey
                
            except Exception as e:
                logger.error(f"AutoSurvey failed: {e}")
                topic_results['autosurvey'] = self._create_error_survey(topic, str(e))
                
            # 2. AutoSurvey with LCE
            logger.info("\n2. Running AutoSurvey with LCE...")
            start_time = time.time()
            try:
                autosurvey_lce = AutoSurveyLCE(
                    claude_wrapper=self.claude_wrapper,
                    chunk_size=15,
                    max_workers=2
                )
                lce_survey = autosurvey_lce.generate_survey(
                    papers=papers,
                    topic=topic,
                    target_sections=5
                )
                end_time = time.time()
                timing_data['autosurvey_lce'] = (start_time, end_time)
                logger.info(f"AutoSurvey+LCE completed in {end_time - start_time:.1f}s")
                
                # Save survey
                self._save_survey(lce_survey, f"{topic}_autosurvey_lce")
                topic_results['autosurvey_lce'] = lce_survey
                
            except Exception as e:
                logger.error(f"AutoSurvey+LCE failed: {e}")
                topic_results['autosurvey_lce'] = self._create_error_survey(topic, str(e))
                
            # 3. Our Iterative System
            logger.info("\n3. Running Global Iterative System...")
            start_time = time.time()
            try:
                iterative_system = IterativeSurveySystem(
                    max_iterations=max_iterations,
                    checkpoint_dir=str(self.checkpoints_dir)
                )
                iterative_survey = iterative_system.generate_survey_iteratively(
                    papers=papers,
                    topic=topic,
                    target_sections=5
                )
                end_time = time.time()
                timing_data['iterative'] = (start_time, end_time)
                logger.info(f"Iterative system completed in {end_time - start_time:.1f}s")
                logger.info(f"Converged: {iterative_survey.get('converged', False)}")
                logger.info(f"Iterations: {iterative_survey.get('total_iterations', 0)}")
                
                # Save survey
                self._save_survey(iterative_survey, f"{topic}_iterative")
                topic_results['iterative'] = iterative_survey
                
            except Exception as e:
                logger.error(f"Iterative system failed: {e}")
                topic_results['iterative'] = self._create_error_survey(topic, str(e))
                
            # Evaluate and compare
            logger.info("\n4. Evaluating and comparing results...")
            comparison = self.comparator.compare_surveys(
                topic_results,
                papers,
                timing_data
            )
            
            # Print comparison
            print("\n" + self.comparator.generate_comparison_table(comparison))
            
            # Save results
            self._save_results(comparison, topic)
            all_results[topic] = comparison
            
            # Show usage summary
            usage = self.claude_wrapper.get_usage_summary()
            logger.info(f"\nAPI Usage for '{topic}':")
            logger.info(f"  Total calls: {usage['total_calls']}")
            logger.info(f"  Estimated cost: ${usage['estimated_cost_usd']:.2f}")
            
        # Save all results
        self._save_all_results(all_results)
        
        return all_results
        
    def _get_papers_for_topic(self, topic: str, limit: int) -> List[Dict]:
        """Get papers relevant to a topic."""
        # Search using BM25
        search_results = self.data_loader.search(topic, top_k=limit * 2)
        
        # Convert to standard format
        papers = []
        for result in search_results[:limit]:
            papers.append({
                'title': result.get('title', ''),
                'summary': result.get('summary', ''),
                'authors': result.get('authors', []),
                'year': result.get('year', 2024),
                'categories': result.get('categories', [])
            })
            
        return papers
        
    def _save_survey(self, survey: Dict, filename: str):
        """Save survey to file."""
        filepath = self.surveys_dir / f"{filename}.json"
        
        # Convert survey sections to serializable format
        serializable_survey = survey.copy()
        if 'sections' in serializable_survey:
            sections = []
            for section in serializable_survey['sections']:
                if hasattr(section, '__dict__'):
                    sections.append(section.__dict__)
                elif isinstance(section, dict):
                    sections.append(section)
                else:
                    sections.append({'content': str(section)})
            serializable_survey['sections'] = sections
            
        with open(filepath, 'w') as f:
            json.dump(serializable_survey, f, indent=2)
            
        logger.debug(f"Saved survey to {filepath}")
        
    def _save_results(self, results: Dict, topic: str):
        """Save evaluation results."""
        filepath = self.results_dir / f"{topic}_results.json"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        logger.debug(f"Saved results to {filepath}")
        
    def _save_all_results(self, all_results: Dict):
        """Save all experiment results."""
        filepath = self.results_dir / "all_results.json"
        
        # Add metadata
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'topics': list(all_results.keys()),
            'results': all_results
        }
        
        with open(filepath, 'w') as f:
            json.dump(final_results, f, indent=2)
            
        logger.info(f"Saved all results to {filepath}")
        
    def _create_error_survey(self, topic: str, error_msg: str) -> Dict:
        """Create placeholder survey for failed experiments."""
        return {
            'topic': topic,
            'sections': [
                {
                    'title': 'Error',
                    'content': f'Survey generation failed: {error_msg}'
                }
            ],
            'error': True,
            'total_iterations': 0,
            'converged': False
        }


def run_quick_test():
    """Run a quick test experiment."""
    print("Running Quick Test Experiment")
    print("=" * 60)
    
    runner = ExperimentRunner()
    
    # Run on one fallback topic with few papers
    results = runner.run_experiments(
        topics=["Large Language Models"],
        papers_per_topic=10,  # Small dataset for testing
        max_iterations=2,     # Fewer iterations for speed
        use_fallback=False
    )
    
    print("\n" + "=" * 60)
    print("Quick Test Complete!")
    print(f"Results saved to: {runner.results_dir}")
    
    return results


def run_full_experiments():
    """Run full experiments on trending topics."""
    print("Running Full Experiments")
    print("=" * 60)
    
    runner = ExperimentRunner()
    
    # Try to discover trending topics
    try:
        discovery = HierarchicalTopicDiscovery()
        trends = discovery.discover_trends(
            base_keyword="large language model",
            days_back=365,
            top_k=2,
            use_external_sources=False
        )
        topics = [f"{t['category']} in LLMs" for t in trends[:2]]
        logger.info(f"Discovered topics: {topics}")
    except Exception as e:
        logger.warning(f"Topic discovery failed: {e}, using fallback topics")
        topics = []
        
    # Run experiments
    results = runner.run_experiments(
        topics=topics,
        papers_per_topic=30,
        max_iterations=3,
        use_fallback=True
    )
    
    print("\n" + "=" * 60)
    print("Full Experiments Complete!")
    print(f"Results saved to: {runner.results_dir}")
    
    # Generate summary
    if results:
        print("\nSummary of Improvements (Iterative vs AutoSurvey):")
        for topic, comparison in results.items():
            if 'improvement' in comparison:
                print(f"\n{topic}:")
                print(f"  Citation F1: {comparison['improvement'].get('citation_f1', 0):+.1f}%")
                print(f"  Content Overall: {comparison['improvement'].get('content_overall', 0):+.1f}%")
                
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_full_experiments()
    else:
        run_quick_test()