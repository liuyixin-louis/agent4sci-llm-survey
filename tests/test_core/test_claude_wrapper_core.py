"""
Core tests for claude_wrapper.py to improve coverage
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import subprocess
import time
import tempfile
from pathlib import Path
import sys
import hashlib

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.wrappers.claude_wrapper import ClaudeCodeCLIWrapper, EnhancedClaudeWrapper


class TestClaudeCodeCLIWrapper:
    """Test ClaudeCodeCLIWrapper class."""
    
    @pytest.fixture
    def wrapper(self):
        """Create wrapper instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wrapper = ClaudeCodeCLIWrapper(cache_dir=tmpdir)
            yield wrapper
    
    def test_initialization(self, wrapper):
        """Test wrapper initialization."""
        assert wrapper is not None
        assert wrapper.min_delay == 2
        assert wrapper.cache == {}
        assert wrapper.last_call_time is None
    
    def test_model_selection(self, wrapper):
        """Test model selection logic."""
        # Test fast model selection
        assert wrapper._select_model("fast") == "haiku"
        assert wrapper._select_model("simple") == "haiku"
        assert wrapper._select_model("categorization") == "haiku"
        
        # Test balanced model selection
        assert wrapper._select_model("balanced") == "sonnet"
        assert wrapper._select_model("generation") == "sonnet"
        assert wrapper._select_model("improvement") == "sonnet"
        
        # Test complex model selection
        assert wrapper._select_model("complex") == "opus"
        assert wrapper._select_model("verification") == "opus"
        assert wrapper._select_model("evaluation") == "opus"
        
        # Test default
        assert wrapper._select_model("unknown") == "sonnet"
    
    def test_cache_key_generation(self, wrapper):
        """Test cache key generation."""
        prompt = "Test prompt"
        model = "haiku"
        
        key = wrapper._get_cache_key(prompt, model)
        expected = hashlib.md5(f"{prompt}:{model}".encode()).hexdigest()
        
        assert key == expected
        
        # Different prompts should have different keys
        key2 = wrapper._get_cache_key("Different prompt", model)
        assert key != key2
        
        # Different models should have different keys
        key3 = wrapper._get_cache_key(prompt, "sonnet")
        assert key != key3
    
    def test_query_with_cache_hit(self, wrapper):
        """Test query with cache hit."""
        prompt = "Test prompt"
        model_type = "fast"
        
        # Pre-populate cache
        cache_key = wrapper._get_cache_key(prompt, "haiku")
        cached_response = {"response": "Cached response"}
        wrapper.cache[cache_key] = cached_response
        
        result = wrapper.query(prompt, model_type=model_type)
        
        assert result == cached_response
    
    @patch('subprocess.run')
    def test_query_with_cache_miss(self, mock_run, wrapper):
        """Test query with cache miss."""
        mock_run.return_value = Mock(
            stdout=json.dumps({"response": "New response"}),
            stderr="",
            returncode=0
        )
        
        result = wrapper.query("Test prompt", model_type="fast")
        
        assert result == {"response": "New response"}
        assert mock_run.called
        
        # Check it was cached
        cache_key = wrapper._get_cache_key("Test prompt", "haiku")
        assert cache_key in wrapper.cache
    
    @patch('subprocess.run')
    def test_rate_limiting(self, mock_run, wrapper):
        """Test rate limiting between calls."""
        mock_run.return_value = Mock(
            stdout=json.dumps({"response": "Response"}),
            stderr="",
            returncode=0
        )
        
        # Set last call time to recent
        wrapper.last_call_time = time.time() - 0.5  # 0.5 seconds ago
        
        with patch('time.sleep') as mock_sleep:
            wrapper.query("Test", model_type="fast")
            
            # Should have slept for remaining time
            mock_sleep.assert_called()
            sleep_time = mock_sleep.call_args[0][0]
            assert sleep_time >= 1.5  # At least 1.5 seconds to reach 2 second delay
    
    @patch('subprocess.run')
    def test_error_handling_non_zero_return(self, mock_run, wrapper):
        """Test error handling for non-zero return code."""
        mock_run.return_value = Mock(
            stdout="",
            stderr="Error message",
            returncode=1
        )
        
        with pytest.raises(RuntimeError, match="Claude CLI error"):
            wrapper.query("Test prompt")
    
    @patch('subprocess.run')
    def test_error_handling_json_decode(self, mock_run, wrapper):
        """Test handling of invalid JSON response."""
        mock_run.return_value = Mock(
            stdout="Not valid JSON",
            stderr="",
            returncode=0
        )
        
        result = wrapper.query("Test prompt")
        
        # Should return raw text when JSON decode fails
        assert result == "Not valid JSON"
    
    def test_cache_persistence(self, wrapper):
        """Test cache save and load."""
        # Add to cache
        wrapper.cache["test_key"] = {"test": "data"}
        wrapper._save_cache()
        
        # Create new wrapper with same cache dir
        new_wrapper = ClaudeCodeCLIWrapper(cache_dir=wrapper.cache_dir)
        new_wrapper._load_cache()
        
        assert "test_key" in new_wrapper.cache
        assert new_wrapper.cache["test_key"] == {"test": "data"}
    
    def test_clear_cache(self, wrapper):
        """Test cache clearing."""
        wrapper.cache = {"key1": "value1", "key2": "value2"}
        wrapper.clear_cache()
        
        assert wrapper.cache == {}
    
    def test_get_statistics(self, wrapper):
        """Test statistics tracking."""
        # Make some queries with cache hits and misses
        wrapper.cache["key1"] = {"cached": "response"}
        
        # Cache hit
        wrapper.query_count = 1
        wrapper.cache_hits = 1
        wrapper.cache_misses = 0
        
        stats = wrapper.get_statistics()
        
        assert stats["total_queries"] == 1
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 0
        assert stats["cache_hit_rate"] == 1.0
    
    @patch('subprocess.run')
    def test_retry_on_rate_limit(self, mock_run, wrapper):
        """Test retry logic on rate limit errors."""
        # First call fails with rate limit, second succeeds
        mock_run.side_effect = [
            Mock(stdout="", stderr="Rate limit exceeded", returncode=1),
            Mock(stdout=json.dumps({"response": "Success"}), stderr="", returncode=0)
        ]
        
        with patch('time.sleep'):
            result = wrapper.query("Test prompt", max_retries=2)
        
        assert result == {"response": "Success"}
        assert mock_run.call_count == 2


class TestEnhancedClaudeWrapper:
    """Test EnhancedClaudeWrapper class."""
    
    @pytest.fixture
    def wrapper(self):
        """Create enhanced wrapper instance."""
        return EnhancedClaudeWrapper()
    
    def test_initialization(self, wrapper):
        """Test enhanced wrapper initialization."""
        assert wrapper is not None
        assert hasattr(wrapper, 'cli_wrapper')
        assert isinstance(wrapper.cli_wrapper, ClaudeCodeCLIWrapper)
    
    def test_query_delegation(self, wrapper):
        """Test that queries are delegated to CLI wrapper."""
        with patch.object(wrapper.cli_wrapper, 'query') as mock_query:
            mock_query.return_value = {"response": "Test"}
            
            result = wrapper.query("Test prompt", model_type="fast")
            
            assert result == {"response": "Test"}
            mock_query.assert_called_once_with("Test prompt", model_type="fast")
    
    def test_chat_completion(self, wrapper):
        """Test chat completion method."""
        with patch.object(wrapper.cli_wrapper, 'query') as mock_query:
            mock_query.return_value = {"response": "Chat response"}
            
            result = wrapper.chat_completion("Chat prompt", model="sonnet")
            
            assert result == {"response": "Chat response"}
            mock_query.assert_called_once_with("Chat prompt", model_type="balanced")
    
    def test_clear_cache_delegation(self, wrapper):
        """Test cache clearing delegation."""
        with patch.object(wrapper.cli_wrapper, 'clear_cache') as mock_clear:
            wrapper.clear_cache()
            mock_clear.assert_called_once()
    
    def test_get_statistics_delegation(self, wrapper):
        """Test statistics delegation."""
        with patch.object(wrapper.cli_wrapper, 'get_statistics') as mock_stats:
            mock_stats.return_value = {"total": 10}
            
            stats = wrapper.get_statistics()
            
            assert stats == {"total": 10}
            mock_stats.assert_called_once()


class TestIntegrationScenarios:
    """Integration tests for wrapper scenarios."""
    
    def test_multiple_queries_with_caching(self):
        """Test multiple queries with caching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wrapper = ClaudeCodeCLIWrapper(cache_dir=tmpdir)
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout=json.dumps({"response": "First"}),
                    stderr="",
                    returncode=0
                )
                
                # First query - cache miss
                result1 = wrapper.query("Query 1", model_type="fast")
                assert mock_run.call_count == 1
                
                # Same query - cache hit
                result2 = wrapper.query("Query 1", model_type="fast")
                assert mock_run.call_count == 1  # No additional call
                assert result1 == result2
                
                # Different query - cache miss
                mock_run.return_value = Mock(
                    stdout=json.dumps({"response": "Second"}),
                    stderr="",
                    returncode=0
                )
                result3 = wrapper.query("Query 2", model_type="fast")
                assert mock_run.call_count == 2
    
    def test_model_progression(self):
        """Test progression through model types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            wrapper = ClaudeCodeCLIWrapper(cache_dir=tmpdir)
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    stdout=json.dumps({"response": "Response"}),
                    stderr="",
                    returncode=0
                )
                
                # Fast task
                wrapper.query("Fast task", model_type="fast")
                assert "haiku" in str(mock_run.call_args)
                
                # Balanced task
                wrapper.query("Balanced task", model_type="balanced")
                assert "sonnet" in str(mock_run.call_args)
                
                # Complex task
                wrapper.query("Complex task", model_type="complex")
                assert "opus" in str(mock_run.call_args)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.wrappers.claude_wrapper", "--cov-report=term-missing"])