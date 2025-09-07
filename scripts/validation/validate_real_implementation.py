#!/usr/bin/env python3
"""
Validation script for real implementation
Tests the complete system with actual functionality (no mocks)
"""

import sys
import json
import time
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.data.data_loader import SciMCPDataLoader
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper
from src.baselines.autosurvey import AutoSurveyBaseline
from src.our_system.iterative import IterativeSurveySystem
from src.evaluation.metrics import SurveyEvaluator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_implementation(num_papers: int = 5):
    """
    Validate the real implementation with a small set of papers.
    
    Args:
        num_papers: Number of papers to test with (default 5 for quick validation)
    """
    logger.info("="*60)
    logger.info("VALIDATION RUN: Testing Real Implementation")
    logger.info(f"Papers: {num_papers} | Mode: Real (no mocks)")
    logger.info("="*60)
    
    # Initialize components
    logger.info("\n[1/6] Initializing components...")
    
    # Data loader with environment variable support
    data_loader = SciMCPDataLoader()
    
    # Real Claude wrapper
    wrapper = EnhancedClaudeWrapper()
    
    # Real evaluator (no mock fallback)
    evaluator = SurveyEvaluator(wrapper)
    
    logger.info("✓ Components initialized")
    
    # Load and search papers
    logger.info(f"\n[2/6] Fetching {num_papers} papers on LLM Agents...")
    
    try:
        data_loader.load_data()
        data_loader.build_bm25_index()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        logger.info("Please set SCIMCP_DATA_PATH environment variable")
        return None
    
    papers = data_loader.search("LLM agents tool use", top_k=num_papers)
    logger.info(f"✓ Found {len(papers)} papers")
    
    # Save papers for reference
    output_dir = Path("outputs/validation_run")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / f"papers_{num_papers}.json", 'w') as f:
        json.dump(papers, f, indent=2, default=str)
    
    # Test 1: Baseline AutoSurvey
    logger.info("\n[3/6] Running baseline AutoSurvey...")
    start_time = time.time()
    
    baseline = AutoSurveyBaseline(wrapper)
    baseline_survey = baseline.generate_survey(papers, topic="LLM Agents")
    
    baseline_time = time.time() - start_time
    logger.info(f"✓ Baseline completed in {baseline_time:.1f}s")
    
    # Save baseline survey
    with open(output_dir / "baseline_survey.md", 'w') as f:
        if isinstance(baseline_survey, dict):
            sections = baseline_survey.get('sections', [])
            for section in sections:
                f.write(f"## {section.get('title', 'Section')}\n\n")
                f.write(f"{section.get('content', '')}\n\n")
        else:
            f.write(str(baseline_survey))
    
    # Test 2: Our iterative system with real improvements
    logger.info("\n[4/6] Running global iterative system (REAL)...")
    start_time = time.time()
    
    iterative = IterativeSurveySystem(wrapper, max_iterations=2)  # Limit iterations for speed
    iterative_survey, iterations = iterative.generate_iterative_survey(papers, topic="LLM Agents")
    
    iterative_time = time.time() - start_time
    logger.info(f"✓ Iterative completed in {iterative_time:.1f}s")
    logger.info(f"  Iterations: {len(iterations)}")
    
    # Save iterative survey
    with open(output_dir / "iterative_survey.md", 'w') as f:
        if isinstance(iterative_survey, dict):
            sections = iterative_survey.get('sections', [])
            for section in sections:
                f.write(f"## {section.get('title', 'Section')}\n\n")
                f.write(f"{section.get('content', '')}\n\n")
        else:
            f.write(str(iterative_survey))
    
    # Test 3: Evaluate both surveys
    logger.info("\n[5/6] Evaluating surveys with real metrics...")
    
    # Convert surveys to text for evaluation
    def survey_to_text(survey):
        if isinstance(survey, dict):
            sections = survey.get('sections', [])
            text = ""
            for section in sections:
                text += f"## {section.get('title', '')}\n"
                text += f"{section.get('content', '')}\n\n"
            return text
        return str(survey)
    
    baseline_text = survey_to_text(baseline_survey)
    iterative_text = survey_to_text(iterative_survey)
    
    try:
        baseline_metrics = evaluator.evaluate_survey(baseline_text, papers)
        logger.info(f"✓ Baseline metrics: {baseline_metrics['overall']:.2f}")
    except Exception as e:
        logger.error(f"Baseline evaluation failed: {e}")
        baseline_metrics = {'overall': 0, 'error': str(e)}
    
    try:
        iterative_metrics = evaluator.evaluate_survey(iterative_text, papers)
        logger.info(f"✓ Iterative metrics: {iterative_metrics['overall']:.2f}")
    except Exception as e:
        logger.error(f"Iterative evaluation failed: {e}")
        iterative_metrics = {'overall': 0, 'error': str(e)}
    
    # Calculate improvement
    if baseline_metrics['overall'] > 0 and iterative_metrics['overall'] > 0:
        improvement = ((iterative_metrics['overall'] - baseline_metrics['overall']) / 
                      baseline_metrics['overall']) * 100
        logger.info(f"✓ Improvement: {improvement:.1f}%")
    else:
        improvement = 0
        logger.warning("Could not calculate improvement due to evaluation errors")
    
    # Save results
    logger.info("\n[6/6] Saving validation results...")
    
    results = {
        'configuration': {
            'num_papers': num_papers,
            'max_iterations': 2,
            'mode': 'real_implementation'
        },
        'timing': {
            'baseline': baseline_time,
            'iterative': iterative_time
        },
        'metrics': {
            'baseline': baseline_metrics,
            'iterative': iterative_metrics
        },
        'improvement': improvement,
        'iterations': iterations,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(output_dir / f"validation_results_{num_papers}.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Papers processed: {num_papers}")
    logger.info(f"Baseline score: {baseline_metrics.get('overall', 'N/A')}")
    logger.info(f"Iterative score: {iterative_metrics.get('overall', 'N/A')}")
    logger.info(f"Improvement: {improvement:.1f}%")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("="*60)
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate real implementation')
    parser.add_argument('--papers', type=int, default=5,
                       help='Number of papers to test with (default: 5)')
    args = parser.parse_args()
    
    # Check environment
    import os
    if not os.environ.get('ANTHROPIC_API_KEY'):
        logger.warning("ANTHROPIC_API_KEY not set. API calls will fail.")
        logger.info("Set it with: export ANTHROPIC_API_KEY=your-key")
    
    if not os.environ.get('SCIMCP_DATA_PATH'):
        logger.warning("SCIMCP_DATA_PATH not set. Using default path.")
        logger.info("Set it with: export SCIMCP_DATA_PATH=/path/to/all_papers.parquet")
    
    # Run validation
    results = validate_implementation(args.papers)
    
    if results and results['improvement'] > 0:
        logger.info("\n✅ VALIDATION SUCCESSFUL: Real implementation working!")
    else:
        logger.error("\n❌ VALIDATION FAILED: Check logs for errors")
        sys.exit(1)


if __name__ == "__main__":
    main()