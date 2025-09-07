"""
COLM Taxonomy Classifier for Research Papers
Classifies papers into 18 COLM (Conference on Language Modeling) categories
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class COLMTaxonomyClassifier:
    """
    Classifies research papers according to COLM taxonomy.
    18 categories covering all aspects of language modeling research.
    """
    
    COLM_CATEGORIES = [
        "Alignment",
        "Applications",  
        "Data",
        "Evaluation and Analysis",
        "Interpretability and Model Analysis",
        "Linguistic Theory",
        "Multimodal Models",
        "Neuroscience and Cognitive Modeling",
        "Philosophy and Ethics",
        "Pre-training",
        "Prompting and In-context Learning",
        "Reasoning",
        "Retrieval-augmented Models",
        "Safety",
        "Science of LMs",
        "Speech and Audio",
        "Theory",
        "Tools and Code"
    ]
    
    # Keywords for zero-shot classification
    CATEGORY_KEYWORDS = {
        "Alignment": ["alignment", "rlhf", "human feedback", "preference", "instruction following"],
        "Applications": ["application", "use case", "deployment", "product", "industry"],
        "Data": ["dataset", "corpus", "data collection", "annotation", "data quality"],
        "Evaluation and Analysis": ["evaluation", "benchmark", "metric", "analysis", "performance"],
        "Interpretability and Model Analysis": ["interpretability", "explainability", "attention", "probe", "internal"],
        "Linguistic Theory": ["linguistic", "syntax", "semantics", "grammar", "morphology"],
        "Multimodal Models": ["multimodal", "vision", "image", "video", "cross-modal"],
        "Neuroscience and Cognitive Modeling": ["neuroscience", "cognitive", "brain", "neural", "psychology"],
        "Philosophy and Ethics": ["ethics", "philosophy", "bias", "fairness", "values"],
        "Pre-training": ["pre-training", "pretraining", "masked", "autoregressive", "objective"],
        "Prompting and In-context Learning": ["prompting", "in-context", "few-shot", "zero-shot", "chain-of-thought"],
        "Reasoning": ["reasoning", "logic", "inference", "deduction", "problem solving"],
        "Retrieval-augmented Models": ["retrieval", "RAG", "augmented", "search", "knowledge base"],
        "Safety": ["safety", "harmful", "toxic", "adversarial", "robustness"],
        "Science of LMs": ["scaling", "emergence", "capability", "understanding", "science"],
        "Speech and Audio": ["speech", "audio", "voice", "TTS", "ASR", "acoustic"],
        "Theory": ["theory", "theoretical", "complexity", "optimization", "convergence"],
        "Tools and Code": ["tool", "API", "code", "function calling", "agent", "plugin"]
    }
    
    def __init__(self, claude_wrapper=None):
        """
        Initialize classifier.
        
        Args:
            claude_wrapper: Optional Claude wrapper for advanced classification
        """
        self.claude_wrapper = claude_wrapper
        
    def classify_paper(self, paper: Dict) -> str:
        """
        Classify a paper into one of the COLM categories.
        
        Args:
            paper: Paper dict with title, abstract, etc.
            
        Returns:
            Category name
        """
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        text = f"{title} {abstract}"
        
        # Simple keyword-based classification
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[category] = score
        
        # Return category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            if scores[best_category] > 0:
                return best_category
        
        # Default fallback
        return "Applications"
    
    def classify_papers_batch(self, papers: List[Dict]) -> Dict[str, str]:
        """
        Classify multiple papers.
        
        Args:
            papers: List of paper dicts
            
        Returns:
            Dict mapping paper titles to categories
        """
        classifications = {}
        for paper in papers:
            category = self.classify_paper(paper)
            classifications[paper.get('title', 'Unknown')] = category
        
        return classifications
    
    def get_category_distribution(self, papers: List[Dict]) -> Dict[str, int]:
        """
        Get distribution of papers across categories.
        
        Args:
            papers: List of papers
            
        Returns:
            Dict of category counts
        """
        classifications = self.classify_papers_batch(papers)
        
        distribution = {}
        for category in self.COLM_CATEGORIES:
            distribution[category] = sum(1 for c in classifications.values() if c == category)
        
        return distribution
    
    def identify_trending_categories(
        self, 
        papers: List[Dict],
        time_window_months: int = 6
    ) -> List[str]:
        """
        Identify trending categories based on recent activity.
        
        Args:
            papers: List of papers with temporal info
            time_window_months: Window for trend analysis
            
        Returns:
            List of trending category names
        """
        # Simple implementation - classify and count recent papers
        recent_papers = []
        for paper in papers:
            year = paper.get('year', 2024)
            month = paper.get('month', 1)
            # Simple recency check
            if year >= 2023 or (year == 2022 and month >= 7):
                recent_papers.append(paper)
        
        if not recent_papers:
            return []
        
        distribution = self.get_category_distribution(recent_papers)
        
        # Categories with >10% of recent papers are trending
        threshold = len(recent_papers) * 0.1
        trending = [cat for cat, count in distribution.items() if count >= threshold]
        
        return sorted(trending, key=lambda x: distribution[x], reverse=True)[:5]