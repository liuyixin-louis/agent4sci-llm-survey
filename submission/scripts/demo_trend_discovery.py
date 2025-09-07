#!/usr/bin/env python3
"""
Demonstration of Automated Trend Discovery using COLM Taxonomy
For Agents4Science 2025 Submission
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.trend_discovery.colm_classifier import COLMTaxonomyClassifier
from src.trend_discovery.trend_analyzer import TrendAnalyzer
from collections import Counter
import json


def create_sample_papers():
    """Create sample papers representing different research trends."""
    return [
        # Alignment & Safety Papers
        {
            'title': 'Constitutional AI: Harmlessness from AI Feedback',
            'abstract': 'Training AI systems to be helpful and harmless using AI feedback.',
            'year': 2022,
            'month': 3
        },
        {
            'title': 'RLHF: Training language models to follow instructions',
            'abstract': 'Using reinforcement learning from human feedback for alignment.',
            'year': 2022,
            'month': 6
        },
        
        # Tool Use Papers
        {
            'title': 'Toolformer: Language Models Can Teach Themselves to Use Tools',
            'abstract': 'Teaching LMs to use external tools via self-supervised learning.',
            'year': 2023,
            'month': 2
        },
        {
            'title': 'WebGPT: Browser-assisted question-answering',
            'abstract': 'LLMs using web browsers to answer questions accurately.',
            'year': 2023,
            'month': 4
        },
        
        # Multimodal Papers
        {
            'title': 'CLIP: Learning Transferable Visual Models',
            'abstract': 'Connecting text and images through contrastive learning.',
            'year': 2021,
            'month': 1
        },
        {
            'title': 'Flamingo: A Visual Language Model',
            'abstract': 'Few-shot learning across vision and language tasks.',
            'year': 2022,
            'month': 4
        },
        
        # Reasoning Papers
        {
            'title': 'Chain-of-Thought Prompting Elicits Reasoning',
            'abstract': 'Improving reasoning in LLMs through intermediate reasoning steps.',
            'year': 2022,
            'month': 1
        },
        {
            'title': 'Tree of Thoughts: Deliberate Problem Solving',
            'abstract': 'LLMs exploring multiple reasoning paths for problem solving.',
            'year': 2023,
            'month': 5
        },
        
        # Add more for realistic distribution
        {'title': 'Scaling Laws for Neural Language Models', 'abstract': 'Understanding how model performance scales.', 'year': 2020, 'month': 1},
        {'title': 'GPT-4 Technical Report', 'abstract': 'Multimodal large language model capabilities.', 'year': 2023, 'month': 3},
    ]


def demonstrate_trend_discovery():
    """Demonstrate automated trend discovery."""
    print("=" * 60)
    print("AUTOMATED TREND DISCOVERY DEMONSTRATION")
    print("Using COLM Taxonomy (18 Categories)")
    print("=" * 60)
    
    # Initialize components
    classifier = COLMTaxonomyClassifier()
    analyzer = TrendAnalyzer()
    
    # Get sample papers
    papers = create_sample_papers()
    print(f"\n📚 Analyzing {len(papers)} papers")
    
    # Classify papers
    print("\n🏷️ Classifying papers by COLM taxonomy...")
    classifications = {}
    for paper in papers:
        category = classifier.classify_paper(paper)
        classifications[paper['title']] = category
        print(f"   • {paper['title'][:50]}...")
        print(f"     → {category}")
    
    # Analyze category distribution
    category_counts = Counter(classifications.values())
    print("\n📊 Category Distribution:")
    for category, count in category_counts.most_common():
        pct = (count / len(papers)) * 100
        print(f"   • {category}: {count} papers ({pct:.1f}%)")
    
    # Identify trending topics
    print("\n🔥 Trending Topics (by velocity):")
    trends = analyzer.identify_trends(papers, classifications)
    
    top_trends = sorted(trends.items(), key=lambda x: x[1]['velocity'], reverse=True)[:3]
    for category, metrics in top_trends:
        print(f"   • {category}:")
        print(f"     - Velocity: {metrics['velocity']:.2f} papers/month")
        print(f"     - Acceleration: {metrics['acceleration']:.3f} papers/month²")
        print(f"     - Recent papers: {metrics['recent_count']}")
    
    # Generate insights
    print("\n💡 Key Insights:")
    insights = [
        f"Most active area: {top_trends[0][0]} with {top_trends[0][1]['velocity']:.1f} papers/month",
        f"Fastest growing: Categories with positive acceleration indicate emerging trends",
        f"Total categories covered: {len(category_counts)} out of 18 COLM categories"
    ]
    
    for i, insight in enumerate(insights, 1):
        print(f"   {i}. {insight}")
    
    # Recommend survey topics
    print("\n📝 Recommended Survey Topics:")
    recommendations = []
    
    for category, metrics in top_trends:
        if metrics['velocity'] > 0.5:  # Active area
            rec = {
                'topic': f"Recent Advances in {category}",
                'rationale': f"High activity ({metrics['velocity']:.1f} papers/month)",
                'papers_available': metrics['recent_count']
            }
            recommendations.append(rec)
            print(f"   • {rec['topic']}")
            print(f"     Rationale: {rec['rationale']}")
    
    # Save results
    output_dir = Path("data/trend_discovery")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        'papers_analyzed': len(papers),
        'classifications': classifications,
        'category_distribution': dict(category_counts),
        'trending_topics': {k: v for k, v in top_trends},
        'recommendations': recommendations
    }
    
    with open(output_dir / "trend_discovery_demo.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {output_dir}/trend_discovery_demo.json")
    print("\n✅ TREND DISCOVERY COMPLETE")


if __name__ == "__main__":
    print("Starting Trend Discovery Demo...")
    print("This demonstrates automated research trend identification")
    print("using the COLM taxonomy classification system\n")
    
    try:
        demonstrate_trend_discovery()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)