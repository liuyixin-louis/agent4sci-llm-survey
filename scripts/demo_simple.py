#!/usr/bin/env python3
"""
Simple demonstration of the LLM Survey System
For Agents4Science 2025 Submission
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.our_system.iterative import IterativeSurveySystem
from src.baselines.autosurvey import AutoSurveyBaseline
from src.evaluation.metrics import SurveyEvaluator
import json
import time


def create_demo_papers():
    """Create a small set of demo papers for quick testing."""
    return [
        {
            'title': 'Attention Is All You Need',
            'abstract': 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
            'authors': ['Vaswani et al.'],
            'year': 2017
        },
        {
            'title': 'BERT: Pre-training of Deep Bidirectional Transformers',
            'abstract': 'We introduce BERT, a new language representation model with bidirectional training.',
            'authors': ['Devlin et al.'],
            'year': 2018
        },
        {
            'title': 'GPT-3: Language Models are Few-Shot Learners',
            'abstract': 'We demonstrate that scaling up language models greatly improves task-agnostic, few-shot performance.',
            'authors': ['Brown et al.'],
            'year': 2020
        },
        {
            'title': 'Chain-of-Thought Prompting Elicits Reasoning',
            'abstract': 'We show that chain-of-thought prompting improves reasoning abilities in large language models.',
            'authors': ['Wei et al.'],
            'year': 2022
        },
        {
            'title': 'Constitutional AI: Harmlessness from AI Feedback',
            'abstract': 'We present Constitutional AI, a method for training harmless AI assistants.',
            'authors': ['Bai et al.'],
            'year': 2022
        }
    ]


def run_demo():
    """Run the demonstration."""
    print("=" * 60)
    print("LLM SURVEYING LLMs - DEMONSTRATION")
    print("Global Verification-Driven Iteration")
    print("=" * 60)
    
    # Create demo papers
    papers = create_demo_papers()
    print(f"\n📚 Using {len(papers)} demo papers")
    
    # Topic
    topic = "Large Language Models and Transformers"
    print(f"📝 Topic: {topic}")
    
    # Initialize systems
    print("\n🔧 Initializing systems...")
    baseline = AutoSurveyBaseline()
    our_system = IterativeSurveySystem(max_iterations=2)
    evaluator = SurveyEvaluator()
    
    # Generate baseline survey
    print("\n📊 Generating BASELINE survey (AutoSurvey)...")
    start = time.time()
    baseline_survey = baseline.generate_survey(papers, topic, target_sections=3)
    baseline_time = time.time() - start
    print(f"   ✓ Generated in {baseline_time:.1f}s")
    
    # Evaluate baseline
    if baseline_survey and 'sections' in baseline_survey:
        print("   📈 Evaluating baseline quality...")
        baseline_scores = evaluator.evaluate(baseline_survey, papers)
        print(f"   📊 Baseline Score: {baseline_scores.get('overall', 0):.2f}")
    
    # Generate our survey
    print("\n🚀 Generating OUR survey (Global Iterative)...")
    start = time.time()
    our_survey = our_system.generate_survey_iteratively(papers, topic, target_sections=3)
    our_time = time.time() - start
    print(f"   ✓ Generated in {our_time:.1f}s")
    print(f"   🔄 Iterations: {our_survey.get('total_iterations', 0)}")
    print(f"   ✅ Converged: {our_survey.get('converged', False)}")
    
    # Evaluate our survey
    if our_survey and 'sections' in our_survey:
        print("   📈 Evaluating our quality...")
        our_scores = evaluator.evaluate(our_survey, papers)
        print(f"   📊 Our Score: {our_scores.get('overall', 0):.2f}")
        
        # Show improvement
        if 'overall' in baseline_scores and 'overall' in our_scores:
            improvement = our_scores['overall'] - baseline_scores['overall']
            pct = (improvement / baseline_scores['overall']) * 100
            print(f"\n🎯 IMPROVEMENT: +{improvement:.2f} ({pct:.1f}%)")
    
    # Show iteration history
    if 'iteration_history' in our_survey:
        print("\n📈 Iteration History:")
        for iter_data in our_survey['iteration_history']:
            print(f"   Iteration {iter_data['iteration']}: Score={iter_data.get('overall_score', 0):.2f}")
    
    # Save results
    output_dir = Path("data/demo_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "demo_baseline.json", 'w') as f:
        json.dump(baseline_survey, f, indent=2)
    
    with open(output_dir / "demo_our_system.json", 'w') as f:
        json.dump(our_survey, f, indent=2)
    
    print(f"\n💾 Results saved to {output_dir}/")
    print("\n✅ DEMONSTRATION COMPLETE")


if __name__ == "__main__":
    print("Starting LLM Survey System Demo...")
    print("Note: This uses the Claude API through the CLI wrapper")
    print("Make sure claude-code is installed and configured\n")
    
    try:
        run_demo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure claude-code CLI is installed")
        print("2. Check API keys are configured")
        print("3. Verify network connectivity")
        sys.exit(1)