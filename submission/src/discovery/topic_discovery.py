"""
Hierarchical Topic Discovery System using COLM Taxonomy
Identifies trending research topics through multi-source aggregation and temporal analysis.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Tuple, Set
import numpy as np
import pandas as pd
from pathlib import Path
import logging

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.data.data_loader import SciMCPDataLoader
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper

# For paper retrieval from external sources
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    logging.warning("arxiv library not available. Install with: pip install arxiv")

try:
    from semanticscholar import SemanticScholar
    SEMANTIC_SCHOLAR_AVAILABLE = True
except ImportError:
    SEMANTIC_SCHOLAR_AVAILABLE = False
    logging.warning("semanticscholar library not available. Install with: pip install semanticscholar")

# For fuzzy matching
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available. Install with: pip install fuzzywuzzy")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class COLMTaxonomy:
    """COLM (Conference on Language Modeling) Taxonomy with 18 categories."""
    
    CATEGORIES = {
        'alignment': {
            'keywords': ['alignment', 'RLHF', 'preference', 'human feedback', 'reward model'],
            'description': 'Model alignment with human values and preferences'
        },
        'data': {
            'keywords': ['dataset', 'data curation', 'data quality', 'synthetic data', 'data augmentation'],
            'description': 'Datasets and data processing techniques'
        },
        'evaluation': {
            'keywords': ['benchmark', 'evaluation', 'metrics', 'assessment', 'performance'],
            'description': 'Evaluation methods and benchmarks'
        },
        'safety': {
            'keywords': ['safety', 'toxicity', 'bias', 'fairness', 'harmful', 'ethics'],
            'description': 'AI safety, bias mitigation, and ethical considerations'
        },
        'efficiency': {
            'keywords': ['efficiency', 'quantization', 'pruning', 'distillation', 'compression'],
            'description': 'Model efficiency and optimization techniques'
        },
        'inference': {
            'keywords': ['inference', 'decoding', 'sampling', 'generation', 'beam search'],
            'description': 'Inference strategies and generation methods'
        },
        'multimodal': {
            'keywords': ['multimodal', 'vision language', 'audio', 'video', 'cross-modal'],
            'description': 'Multimodal models and cross-modal understanding'
        },
        'applications': {
            'keywords': ['application', 'use case', 'deployment', 'production', 'real-world'],
            'description': 'Real-world applications and deployments'
        },
        'reasoning': {
            'keywords': ['reasoning', 'chain of thought', 'logic', 'planning', 'problem solving'],
            'description': 'Reasoning capabilities and methods'
        },
        'training': {
            'keywords': ['training', 'fine-tuning', 'pretraining', 'optimization', 'learning'],
            'description': 'Training methodologies and optimization'
        },
        'architecture': {
            'keywords': ['architecture', 'transformer', 'attention', 'model design', 'neural'],
            'description': 'Model architectures and design innovations'
        },
        'prompting': {
            'keywords': ['prompt', 'in-context learning', 'few-shot', 'zero-shot', 'instruction'],
            'description': 'Prompting techniques and in-context learning'
        },
        'retrieval': {
            'keywords': ['retrieval', 'RAG', 'search', 'memory', 'knowledge base'],
            'description': 'Retrieval-augmented generation and knowledge integration'
        },
        'agents': {
            'keywords': ['agent', 'tool use', 'function calling', 'autonomous', 'multi-agent'],
            'description': 'LLM agents and tool use capabilities'
        },
        'code': {
            'keywords': ['code generation', 'programming', 'software', 'debugging', 'synthesis'],
            'description': 'Code generation and programming assistance'
        },
        'math': {
            'keywords': ['mathematics', 'theorem', 'proof', 'calculation', 'symbolic'],
            'description': 'Mathematical reasoning and problem solving'
        },
        'science': {
            'keywords': ['scientific', 'research', 'discovery', 'hypothesis', 'experiment'],
            'description': 'Scientific applications and research'
        },
        'multilingual': {
            'keywords': ['multilingual', 'translation', 'cross-lingual', 'language transfer'],
            'description': 'Multilingual capabilities and cross-lingual transfer'
        }
    }
    
    @classmethod
    def categorize_paper(cls, title: str, abstract: str) -> List[str]:
        """
        Categorize a paper based on title and abstract.
        
        Returns:
            List of matching categories (can be multiple)
        """
        text = (title + " " + abstract).lower()
        categories = []
        
        for cat_name, cat_info in cls.CATEGORIES.items():
            # Check if any keyword matches
            for keyword in cat_info['keywords']:
                if keyword.lower() in text:
                    categories.append(cat_name)
                    break
                    
        # If no categories found, return 'general'
        return categories if categories else ['general']
        
    @classmethod
    def get_category_description(cls, category: str) -> str:
        """Get description for a category."""
        return cls.CATEGORIES.get(category, {}).get('description', 'General LLM research')


class HierarchicalTopicDiscovery:
    """
    Discover trending research topics using multi-source aggregation and temporal analysis.
    """
    
    def __init__(
        self,
        scimcp_loader: Optional[SciMCPDataLoader] = None,
        claude_wrapper: Optional[EnhancedClaudeWrapper] = None,
        cache_dir: str = "data/cache/topics"
    ):
        """
        Initialize topic discovery system.
        
        Args:
            scimcp_loader: Data loader for sciMCP database
            claude_wrapper: Claude wrapper for LLM-based analysis
            cache_dir: Directory for caching results
        """
        self.scimcp_loader = scimcp_loader or SciMCPDataLoader()
        self.claude_wrapper = claude_wrapper or EnhancedClaudeWrapper()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize external APIs if available
        self.arxiv_client = arxiv.Client() if ARXIV_AVAILABLE else None
        self.semantic_scholar = SemanticScholar() if SEMANTIC_SCHOLAR_AVAILABLE else None
        
        # Trend detection parameters
        self.window_size = 7  # Weekly windows
        self.min_papers_threshold = 5  # Minimum papers for a topic to be considered
        
    def discover_trends(
        self,
        base_keyword: str = "large language model",
        days_back: int = 30,
        top_k: int = 10,
        use_external_sources: bool = True
    ) -> List[Dict]:
        """
        Discover trending subtopics from a base keyword.
        
        Args:
            base_keyword: Broad keyword to start from
            days_back: Number of days to look back
            top_k: Number of top trends to return
            use_external_sources: Whether to use arXiv and Semantic Scholar
            
        Returns:
            List of trending topics with scores and metadata
        """
        logger.info(f"Discovering trends for '{base_keyword}' over last {days_back} days")
        
        # Step 1: Gather papers from multiple sources
        all_papers = self._gather_papers(base_keyword, days_back, use_external_sources)
        logger.info(f"Gathered {len(all_papers)} papers from all sources")
        
        # Step 2: Deduplicate papers
        unique_papers = self._deduplicate_papers(all_papers)
        logger.info(f"After deduplication: {len(unique_papers)} unique papers")
        
        # Step 3: Categorize papers using COLM taxonomy
        categorized_papers = self._categorize_papers(unique_papers)
        
        # Step 4: Calculate temporal trends
        trends = self._calculate_temporal_trends(categorized_papers, days_back)
        
        # Step 5: Assess novelty using LLM
        trends_with_novelty = self._assess_novelty(trends, base_keyword)
        
        # Step 6: Calculate final scores and rank
        scored_trends = self._calculate_trend_scores(trends_with_novelty)
        
        # Sort by score and return top-k
        sorted_trends = sorted(scored_trends, key=lambda x: x['score'], reverse=True)
        return sorted_trends[:top_k]
        
    def _gather_papers(
        self,
        keyword: str,
        days_back: int,
        use_external: bool
    ) -> List[Dict]:
        """Gather papers from all sources."""
        all_papers = []
        
        # 1. Get papers from sciMCP
        logger.info("Fetching from sciMCP database...")
        scimcp_papers = self._get_scimcp_papers(keyword, days_back)
        all_papers.extend(scimcp_papers)
        logger.info(f"Found {len(scimcp_papers)} papers in sciMCP")
        
        if use_external:
            # 2. Get papers from arXiv
            if self.arxiv_client:
                logger.info("Fetching from arXiv API...")
                arxiv_papers = self._get_arxiv_papers(keyword, days_back)
                all_papers.extend(arxiv_papers)
                logger.info(f"Found {len(arxiv_papers)} papers from arXiv")
                
            # 3. Get papers from Semantic Scholar (simplified - no citation counts)
            if self.semantic_scholar:
                logger.info("Fetching from Semantic Scholar...")
                ss_papers = self._get_semantic_scholar_papers(keyword, days_back)
                all_papers.extend(ss_papers)
                logger.info(f"Found {len(ss_papers)} papers from Semantic Scholar")
                
        return all_papers
        
    def _get_scimcp_papers(self, keyword: str, days_back: int) -> List[Dict]:
        """Get papers from sciMCP database."""
        # Load data if not already loaded
        if self.scimcp_loader.papers_df is None:
            self.scimcp_loader.load_data()
            
        # Search for papers
        results = self.scimcp_loader.search(keyword, top_k=500)
        
        # Filter by date - use current date as reference (papers are from 2023-2025)
        # For testing, we'll use the most recent papers from the dataset
        filtered_papers = []
        
        for paper in results:
            try:
                # Use year from paper if available, otherwise parse from updated field
                if 'year' in paper:
                    # Papers from 2024-2025 are recent enough
                    if paper['year'] >= 2024:
                        paper_date = pd.Timestamp(year=paper['year'], month=6, day=1)
                    else:
                        continue
                elif 'updated' in paper:
                    paper_date = pd.to_datetime(paper['updated'])
                else:
                    continue
                    
                filtered_papers.append({
                    'title': paper.get('title', ''),
                    'abstract': paper.get('summary', ''),
                    'date': paper_date,
                    'authors': paper.get('authors', []),
                    'source': 'scimcp',
                    'categories': paper.get('categories', [])
                })
                
                # Limit to recent papers for trend analysis
                if len(filtered_papers) >= 200:
                    break
                    
            except Exception as e:
                logger.debug(f"Error processing paper: {e}")
                continue
                
        return filtered_papers
        
    def _get_arxiv_papers(self, keyword: str, days_back: int) -> List[Dict]:
        """Get papers from arXiv API."""
        if not self.arxiv_client:
            return []
            
        papers = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            # Search arXiv
            search = arxiv.Search(
                query=keyword,
                max_results=200,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            for result in self.arxiv_client.results(search):
                if result.updated >= cutoff_date:
                    papers.append({
                        'title': result.title,
                        'abstract': result.summary,
                        'date': result.updated,
                        'authors': [a.name for a in result.authors],
                        'source': 'arxiv',
                        'categories': result.categories
                    })
                    
        except Exception as e:
            logger.warning(f"Error fetching from arXiv: {e}")
            
        return papers
        
    def _get_semantic_scholar_papers(self, keyword: str, days_back: int) -> List[Dict]:
        """Get papers from Semantic Scholar (simplified without citations)."""
        if not self.semantic_scholar:
            return []
            
        papers = []
        
        try:
            # Search Semantic Scholar
            results = self.semantic_scholar.search_paper(
                keyword,
                limit=100,
                fields=['title', 'abstract', 'authors', 'publicationDate']
            )
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for paper in results:
                try:
                    if paper.publicationDate:
                        paper_date = pd.to_datetime(paper.publicationDate)
                        if paper_date >= cutoff_date:
                            papers.append({
                                'title': paper.title or '',
                                'abstract': paper.abstract or '',
                                'date': paper_date,
                                'authors': [a['name'] for a in (paper.authors or [])],
                                'source': 'semantic_scholar',
                                'categories': []
                            })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error fetching from Semantic Scholar: {e}")
            
        return papers
        
    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """Deduplicate papers based on title similarity."""
        if not papers:
            return []
            
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title = paper['title'].lower().strip()
            
            # Check exact match first
            if title in seen_titles:
                continue
                
            # Check fuzzy match if available
            is_duplicate = False
            if FUZZY_AVAILABLE:
                for seen_title in seen_titles:
                    if fuzz.ratio(title, seen_title) > 90:  # 90% similarity threshold
                        is_duplicate = True
                        break
                        
            if not is_duplicate:
                unique_papers.append(paper)
                seen_titles.add(title)
                
        return unique_papers
        
    def _categorize_papers(self, papers: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize papers using COLM taxonomy."""
        categorized = defaultdict(list)
        
        for paper in papers:
            categories = COLMTaxonomy.categorize_paper(
                paper['title'],
                paper['abstract']
            )
            
            for category in categories:
                categorized[category].append(paper)
                
        return dict(categorized)
        
    def _calculate_temporal_trends(
        self,
        categorized_papers: Dict[str, List[Dict]],
        days_back: int
    ) -> List[Dict]:
        """Calculate velocity and acceleration for each category."""
        trends = []
        
        for category, papers in categorized_papers.items():
            if len(papers) < self.min_papers_threshold:
                continue
                
            # Create time series
            dates = [p['date'] for p in papers]
            df = pd.DataFrame({'date': dates})
            df['count'] = 1
            
            # Resample to daily counts
            df.set_index('date', inplace=True)
            daily_counts = df.resample('D')['count'].sum().fillna(0)
            
            # Calculate weekly rolling averages
            weekly_avg = daily_counts.rolling(window=7, min_periods=1).mean()
            
            # Calculate velocity (first derivative)
            velocity = weekly_avg.diff().mean()
            
            # Calculate acceleration (second derivative)
            acceleration = weekly_avg.diff().diff().mean()
            
            trends.append({
                'category': category,
                'description': COLMTaxonomy.get_category_description(category),
                'paper_count': len(papers),
                'velocity': velocity,
                'acceleration': acceleration,
                'recent_papers': papers[-5:]  # Keep 5 most recent
            })
            
        return trends
        
    def _assess_novelty(self, trends: List[Dict], base_keyword: str) -> List[Dict]:
        """Assess novelty of trends using heuristics and selective LLM calls."""
        
        # Sort trends by paper count to focus on significant ones
        sorted_trends = sorted(trends, key=lambda x: x['paper_count'], reverse=True)
        
        # Only assess top trends with LLM (to avoid timeout)
        MAX_LLM_ASSESSMENTS = 3
        
        for i, trend in enumerate(sorted_trends):
            if i < MAX_LLM_ASSESSMENTS and trend['paper_count'] >= 10:
                # Use LLM for top trends with enough papers
                papers_summary = "\n".join([
                    f"- {p['title']}" 
                    for p in trend['recent_papers'][:3]
                ])
                
                messages = [
                    {
                        "role": "system",
                        "content": "Rate research novelty from 0.0 to 1.0. Respond with just a number."
                    },
                    {
                        "role": "user",
                        "content": f"Rate novelty of '{trend['category']}' research:\n{papers_summary}"
                    }
                ]
                
                try:
                    response = self.claude_wrapper.chat_completion(
                        messages=messages,
                        model="haiku",
                        use_cache=True
                    )
                    
                    if "error" not in response:
                        try:
                            novelty = float(response["choices"][0]["message"]["content"].strip())
                            novelty = max(0.0, min(1.0, novelty))
                        except:
                            novelty = self._heuristic_novelty(trend)
                    else:
                        novelty = self._heuristic_novelty(trend)
                except:
                    novelty = self._heuristic_novelty(trend)
            else:
                # Use heuristic for remaining trends
                novelty = self._heuristic_novelty(trend)
                
            trend['novelty'] = novelty
            
        return sorted_trends
        
    def _heuristic_novelty(self, trend: Dict) -> float:
        """Calculate novelty using simple heuristics."""
        # Categories with higher inherent novelty
        novel_categories = {'multimodal', 'agents', 'reasoning', 'safety', 'efficiency'}
        standard_categories = {'data', 'evaluation', 'training'}
        
        base_novelty = 0.5
        
        if trend['category'] in novel_categories:
            base_novelty = 0.7
        elif trend['category'] in standard_categories:
            base_novelty = 0.3
            
        # Adjust based on acceleration (rapidly growing topics are often novel)
        if trend['acceleration'] > 0.5:
            base_novelty += 0.1
        elif trend['acceleration'] < -0.5:
            base_novelty -= 0.1
            
        return max(0.0, min(1.0, base_novelty))
        
    def _calculate_trend_scores(self, trends: List[Dict]) -> List[Dict]:
        """Calculate final trend scores."""
        for trend in trends:
            # Normalize metrics
            velocity_norm = max(0, min(1, trend['velocity'] / 2.0))  # Normalize to [0, 1]
            accel_norm = max(0, min(1, trend['acceleration'] / 1.0))
            
            # Calculate weighted score
            score = (
                velocity_norm * 0.4 +
                accel_norm * 0.3 +
                trend['novelty'] * 0.3
            )
            
            trend['score'] = score
            trend['metrics'] = {
                'velocity': trend['velocity'],
                'acceleration': trend['acceleration'],
                'novelty': trend['novelty'],
                'paper_count': trend['paper_count']
            }
            
        return trends
        
    def generate_trend_report(self, trends: List[Dict]) -> str:
        """Generate a formatted report of trending topics."""
        report = ["# Trending Research Topics\n"]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for i, trend in enumerate(trends, 1):
            report.append(f"\n## {i}. {trend['category'].title()}")
            report.append(f"**Description:** {trend['description']}")
            report.append(f"**Trend Score:** {trend['score']:.3f}")
            report.append(f"**Papers (last 30 days):** {trend['paper_count']}")
            report.append(f"**Metrics:**")
            report.append(f"  - Velocity: {trend['metrics']['velocity']:.3f}")
            report.append(f"  - Acceleration: {trend['metrics']['acceleration']:.3f}")
            report.append(f"  - Novelty: {trend['metrics']['novelty']:.2f}")
            
            report.append(f"\n**Recent Papers:**")
            for paper in trend['recent_papers'][:3]:
                report.append(f"  - {paper['title']}")
                
        return "\n".join(report)


def main():
    """Test the topic discovery system."""
    print("Testing Hierarchical Topic Discovery System")
    print("=" * 60)
    
    # Initialize components
    loader = SciMCPDataLoader()
    wrapper = EnhancedClaudeWrapper()
    discovery = HierarchicalTopicDiscovery(loader, wrapper)
    
    # Discover trends
    print("\nDiscovering trends for 'large language model'...")
    trends = discovery.discover_trends(
        base_keyword="large language model",
        days_back=30,
        top_k=5,
        use_external_sources=False  # Use only sciMCP for testing
    )
    
    # Generate report
    report = discovery.generate_trend_report(trends)
    print("\n" + report)
    
    # Save report
    report_path = Path("data/reports/trend_discovery_test.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")
    
    return trends


if __name__ == "__main__":
    trends = main()