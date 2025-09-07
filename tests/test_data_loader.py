"""
Tests for the SciMCP Data Loader
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import tempfile
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.data_loader import SciMCPDataLoader


class TestSciMCPDataLoader(unittest.TestCase):
    """Test cases for the SciMCP data loader"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = pd.DataFrame({
            'title': [
                'LLM Agents for Task Planning',
                'Reinforcement Learning in LLMs',
                'Vision-Language Models Survey',
                'Transformer Architecture Analysis',
                'In-Context Learning Methods'
            ],
            'abstract': [
                'We present a framework for LLM agents that can plan complex tasks autonomously.',
                'This paper explores RL techniques for training large language models.',
                'A comprehensive survey of vision-language models and their applications.',
                'Deep analysis of transformer architectures and attention mechanisms.',
                'Novel methods for improving in-context learning in language models.'
            ],
            'authors': [
                'Smith et al.',
                'Jones and Brown',
                'Zhang, Li, Wang',
                'Kumar, Patel',
                'Davis, Wilson, Moore'
            ],
            'category': [
                'cs.AI',
                'cs.LG',
                'cs.CV',
                'cs.CL',
                'cs.CL'
            ],
            'updated': pd.to_datetime([
                '2024-11-15',
                '2024-10-20',
                '2024-09-30',
                '2024-08-15',
                '2024-12-01'
            ])
        })
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_load_data_basic(self, mock_read_parquet):
        """Test basic data loading"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            df = loader.load_data()
        
        self.assertEqual(len(df), 5)
        self.assertIn('title', df.columns)
        self.assertIn('abstract', df.columns)
        mock_read_parquet.assert_called_once()
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_filter_by_category(self, mock_read_parquet):
        """Test filtering by category"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
            filtered = loader.filter_by_category(['cs.CL'])
        
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(cat == 'cs.CL' for cat in filtered['category']))
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_filter_by_date(self, mock_read_parquet):
        """Test filtering by date range"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
            filtered = loader.filter_by_date(
                start_date='2024-10-01',
                end_date='2024-12-31'
            )
        
        self.assertEqual(len(filtered), 3)
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_search_papers(self, mock_read_parquet):
        """Test paper search functionality"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
        
            # Search for LLM-related papers
            results = loader.search_papers('LLM', top_k=3)
        
        self.assertLessEqual(len(results), 3)
        self.assertTrue(any('LLM' in str(paper) for paper in results))
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_get_paper_trends(self, mock_read_parquet):
        """Test trend extraction"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
        
            # Get trends
            trends = loader.get_paper_trends(
                topic='learning',
                window_days=180
            )
        
        self.assertIsInstance(trends, dict)
        self.assertIn('total_papers', trends)
        self.assertIn('recent_papers', trends)
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_empty_search_results(self, mock_read_parquet):
        """Test search with no matches"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
        
            # Search for non-existent term
            results = loader.search_papers('nonexistentterm12345', top_k=5)
        
        # Should return some results based on BM25 scoring even if no exact match
        self.assertIsInstance(results, list)
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_cache_functionality(self, mock_read_parquet):
        """Test that caching works"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
        
            # First load
            df1 = loader.load_data()
        
            # Second load should use cache
            df2 = loader.load_data()
        
        # Should only call read_parquet once due to caching
        mock_read_parquet.assert_called_once()
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_environment_variable_fallback(self):
        """Test that environment variable is used as fallback"""
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': '/test/path.parquet'}):
            with patch('src.data.data_loader.pd.read_parquet') as mock_read:
                mock_read.return_value = self.test_data
                
                loader = SciMCPDataLoader()
                loader.load_data()  # No path provided
                
                # Should use environment variable path
                mock_read.assert_called_with('/test/path.parquet')
    
    @patch('src.data.data_loader.pd.read_parquet')
    def test_invalid_date_format(self, mock_read_parquet):
        """Test handling of invalid date formats"""
        mock_read_parquet.return_value = self.test_data
        
        with patch.dict(os.environ, {'SCIMCP_DATA_PATH': 'dummy.parquet'}):
            loader = SciMCPDataLoader()
            loader.load_data()
        
            # Should handle invalid dates gracefully
            filtered = loader.filter_by_date(
                start_date='invalid-date',
                end_date='2024-12-31'
            )
        
        # Should return original data or handle error
        self.assertIsNotNone(filtered)


if __name__ == '__main__':
    unittest.main()