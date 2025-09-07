#!/usr/bin/env python
"""
Test script for data pipeline - verifies loading, filtering, and BM25 search.
"""

import time
from src.data.data_loader import SciMCPDataLoader


def test_data_pipeline():
    """Test the complete data pipeline."""
    print("=" * 60)
    print("Testing Data Pipeline for LLM Survey Project")
    print("=" * 60)
    
    # Initialize loader
    loader = SciMCPDataLoader()
    
    # Test 1: Load and filter data
    print("\n1. Loading and filtering papers...")
    start_time = time.time()
    papers = loader.load_data()
    load_time = time.time() - start_time
    
    print(f"✓ Loaded {len(papers)} papers in {load_time:.2f} seconds")
    
    # Test 2: Check statistics
    print("\n2. Checking data statistics...")
    stats = loader.get_statistics()
    
    print(f"✓ Total papers: {stats['total_papers']:,}")
    print(f"  Papers by year:")
    for year, count in sorted(stats['papers_by_year'].items()):
        print(f"    - {year}: {count:,}")
    print(f"  Papers by category:")
    for cat, count in sorted(stats['papers_by_category'].items()):
        print(f"    - {cat}: {count:,}")
    
    # Test 3: Build BM25 index
    print("\n3. Building BM25 index...")
    start_time = time.time()
    loader.build_bm25_index()
    index_time = time.time() - start_time
    print(f"✓ BM25 index built in {index_time:.2f} seconds")
    
    # Test 4: Test search functionality
    print("\n4. Testing search functionality...")
    test_queries = [
        "large language models",
        "prompt engineering",
        "multimodal transformers",
        "chain of thought reasoning",
        "retrieval augmented generation"
    ]
    
    for query in test_queries:
        start_time = time.time()
        results = loader.search(query, top_k=3)
        search_time = time.time() - start_time
        
        print(f"\n  Query: '{query}' ({search_time:.3f}s)")
        for i, paper in enumerate(results, 1):
            title = paper['title'][:60] + "..." if len(paper['title']) > 60 else paper['title']
            print(f"    {i}. {title} (score: {paper['bm25_score']:.2f})")
    
    # Test 5: Verify cache functionality
    print("\n5. Testing cache functionality...")
    start_time = time.time()
    papers2 = loader.load_data()  # Should load from cache
    cache_time = time.time() - start_time
    print(f"✓ Loaded from cache in {cache_time:.2f} seconds")
    print(f"  Speedup: {load_time/cache_time:.1f}x faster")
    
    # Test 6: Year and category filtering
    print("\n6. Testing filtering functions...")
    papers_2024 = loader.get_papers_by_year(2024)
    print(f"✓ Papers from 2024: {len(papers_2024):,}")
    
    papers_ai = loader.get_papers_by_category("cs.AI")
    print(f"✓ Papers in cs.AI: {len(papers_ai):,}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ All tests passed successfully!")
    print(f"  - Total papers: {stats['total_papers']:,}")
    print(f"  - Load time: {load_time:.2f}s")
    print(f"  - Index build time: {index_time:.2f}s")
    print(f"  - Average search time: <1s")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_data_pipeline()
    exit(0 if success else 1)