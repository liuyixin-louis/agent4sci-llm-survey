"""
Data loader for sciMCP database with BM25 index support.
Loads and filters CS.AI, CS.CL, CS.LG papers from 2023-2025.
"""

import os
import pickle
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import pyarrow.parquet as pq
from rank_bm25 import BM25Okapi
import numpy as np
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SciMCPDataLoader:
    """Load and process sciMCP papers with BM25 indexing."""
    
    def __init__(self, 
                 parquet_path: str = None,
                 cache_dir: str = "data/processed",
                 categories: List[str] = ["cs.AI", "cs.CL", "cs.LG"],
                 start_year: int = 2023,
                 end_year: int = 2025):
        """
        Initialize data loader.
        
        Args:
            parquet_path: Path to sciMCP parquet file (defaults to SCIMCP_DATA_PATH env var)
            cache_dir: Directory for cached processed data
            categories: arXiv categories to filter
            start_year: Start year for filtering
            end_year: End year for filtering
        """
        # Use environment variable if path not provided
        if parquet_path is None:
            parquet_path = os.environ.get(
                'SCIMCP_DATA_PATH',
                '/data/yixin/workspace/sciMCP/data/all_papers.parquet'
            )
        self.parquet_path = parquet_path
        self.cache_dir = cache_dir
        self.categories = categories
        self.start_year = start_year
        self.end_year = end_year
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache file paths
        self.papers_cache_path = os.path.join(cache_dir, "processed_papers.pkl")
        self.bm25_cache_path = os.path.join(cache_dir, "bm25_index.pkl")
        self.metadata_cache_path = os.path.join(cache_dir, "metadata.json")
        
        # Data containers
        self.papers_df = None
        self.bm25_index = None
        self.tokenized_corpus = None
        
    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load papers from parquet or cache.
        
        Args:
            force_reload: Force reload from source instead of cache
            
        Returns:
            DataFrame with filtered papers
        """
        # Try loading from cache first
        if not force_reload and self._load_from_cache():
            logger.info(f"Loaded {len(self.papers_df)} papers from cache")
            return self.papers_df
            
        # Load from parquet file
        logger.info(f"Loading papers from {self.parquet_path}")
        
        # Load in chunks for memory efficiency
        parquet_file = pq.ParquetFile(self.parquet_path)
        
        filtered_papers = []
        total_processed = 0
        
        for batch in tqdm(parquet_file.iter_batches(batch_size=10000), 
                         desc="Processing batches"):
            batch_df = batch.to_pandas()
            total_processed += len(batch_df)
            
            # Filter by categories and date
            filtered_batch = self._filter_papers(batch_df)
            if not filtered_batch.empty:
                filtered_papers.append(filtered_batch)
                
        # Combine all filtered batches
        self.papers_df = pd.concat(filtered_papers, ignore_index=True)
        
        logger.info(f"Filtered {len(self.papers_df)} papers from {total_processed} total")
        
        # Save to cache
        self._save_to_cache()
        
        return self.papers_df
        
    def _filter_papers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter papers by categories and date range.
        
        Args:
            df: DataFrame with papers
            
        Returns:
            Filtered DataFrame
        """
        # Filter by categories (handle both primary and cross-listed)
        # Categories can be a list or string, handle both
        def check_categories(cats):
            if isinstance(cats, list):
                cats_str = ' '.join(cats).lower()
            else:
                cats_str = str(cats).lower()
            return any(cat.lower() in cats_str for cat in self.categories)
        
        category_mask = df['categories'].apply(check_categories)
        
        # Parse dates and filter by year (use 'updated' column)
        df['year'] = pd.to_datetime(df['updated'], errors='coerce').dt.year
        date_mask = (df['year'] >= self.start_year) & (df['year'] <= self.end_year)
        
        # Apply both filters
        filtered = df[category_mask & date_mask].copy()
        
        # Add processed text field for BM25 (use 'summary' instead of 'abstract')
        filtered['processed_text'] = (
            filtered['title'].fillna('') + ' ' + 
            filtered['summary'].fillna('')
        )
        
        return filtered
        
    def build_bm25_index(self, force_rebuild: bool = False) -> BM25Okapi:
        """
        Build or load BM25 index for fast retrieval.
        
        Args:
            force_rebuild: Force rebuild of index
            
        Returns:
            BM25 index object
        """
        # Try loading from cache
        if not force_rebuild and os.path.exists(self.bm25_cache_path):
            logger.info("Loading BM25 index from cache")
            with open(self.bm25_cache_path, 'rb') as f:
                cache_data = pickle.load(f)
                self.bm25_index = cache_data['index']
                self.tokenized_corpus = cache_data['corpus']
            return self.bm25_index
            
        # Ensure papers are loaded
        if self.papers_df is None:
            self.load_data()
            
        logger.info("Building BM25 index...")
        
        # Tokenize corpus
        self.tokenized_corpus = [
            doc.lower().split() 
            for doc in tqdm(self.papers_df['processed_text'].values,
                           desc="Tokenizing documents")
        ]
        
        # Build BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        
        # Save to cache
        logger.info("Saving BM25 index to cache")
        with open(self.bm25_cache_path, 'wb') as f:
            pickle.dump({
                'index': self.bm25_index,
                'corpus': self.tokenized_corpus
            }, f)
            
        return self.bm25_index
        
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search papers using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of paper dictionaries with scores
        """
        # Ensure index is built
        if self.bm25_index is None:
            self.build_bm25_index()
            
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get scores
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        # Prepare results
        results = []
        for idx in top_indices:
            paper = self.papers_df.iloc[idx].to_dict()
            paper['bm25_score'] = scores[idx]
            results.append(paper)
            
        return results
        
    def get_papers_by_year(self, year: int) -> pd.DataFrame:
        """Get papers from a specific year."""
        if self.papers_df is None:
            self.load_data()
        return self.papers_df[self.papers_df['year'] == year]
        
    def get_papers_by_category(self, category: str) -> pd.DataFrame:
        """Get papers from a specific category."""
        if self.papers_df is None:
            self.load_data()
        mask = self.papers_df['categories'].apply(
            lambda x: category.lower() in str(x).lower()
        )
        return self.papers_df[mask]
        
    def get_statistics(self) -> Dict:
        """Get statistics about the loaded papers."""
        if self.papers_df is None:
            self.load_data()
            
        stats = {
            'total_papers': len(self.papers_df),
            'papers_by_year': self.papers_df['year'].value_counts().to_dict(),
            'papers_by_category': {}
        }
        
        # Count papers per category
        for cat in self.categories:
            mask = self.papers_df['categories'].apply(
                lambda x: cat.lower() in str(x).lower()
            )
            stats['papers_by_category'][cat] = mask.sum()
            
        return stats
        
    def _load_from_cache(self) -> bool:
        """
        Load data from cache if available.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not os.path.exists(self.papers_cache_path):
            return False
            
        try:
            # Check metadata to see if cache is valid
            if os.path.exists(self.metadata_cache_path):
                with open(self.metadata_cache_path, 'r') as f:
                    metadata = json.load(f)
                    
                # Validate cache parameters
                if (metadata.get('categories') != self.categories or
                    metadata.get('start_year') != self.start_year or
                    metadata.get('end_year') != self.end_year):
                    logger.info("Cache parameters mismatch, reloading data")
                    return False
                    
            # Load cached data
            with open(self.papers_cache_path, 'rb') as f:
                self.papers_df = pickle.load(f)
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False
            
    def _save_to_cache(self):
        """Save processed data to cache."""
        try:
            # Save papers
            with open(self.papers_cache_path, 'wb') as f:
                pickle.dump(self.papers_df, f)
                
            # Save metadata
            metadata = {
                'categories': self.categories,
                'start_year': self.start_year,
                'end_year': self.end_year,
                'num_papers': len(self.papers_df),
                'cached_at': datetime.now().isoformat()
            }
            with open(self.metadata_cache_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Saved {len(self.papers_df)} papers to cache")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


def main():
    """Test the data loader."""
    loader = SciMCPDataLoader()
    
    # Load data
    papers = loader.load_data()
    print(f"Loaded {len(papers)} papers")
    
    # Get statistics
    stats = loader.get_statistics()
    print("\nStatistics:")
    print(f"Total papers: {stats['total_papers']}")
    print(f"Papers by year: {stats['papers_by_year']}")
    print(f"Papers by category: {stats['papers_by_category']}")
    
    # Build BM25 index
    loader.build_bm25_index()
    
    # Test search
    results = loader.search("large language models", top_k=5)
    print(f"\nTop 5 results for 'large language models':")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']} (score: {paper['bm25_score']:.2f})")


if __name__ == "__main__":
    main()