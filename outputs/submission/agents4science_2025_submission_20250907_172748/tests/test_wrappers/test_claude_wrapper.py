"""
Comprehensive tests for Claude CLI wrapper
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import hashlib
import time
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.wrappers.claude_wrapper import ClaudeCodeCLIWrapper


class TestClaudeCodeCLIWrapper:
    """Test suite for Claude CLI wrapper"""
    
    @pytest.fixture
    def wrapper(self):
        """Create wrapper instance for testing"""
        return ClaudeCodeCLIWrapper(cache_dir="test_cache")
    
    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess for CLI calls"""
        with patch('src.wrappers.claude_wrapper.subprocess') as mock:
            mock.run.return_value.stdout = json.dumps({
                "response": "Test response",
                "model": "claude-3-haiku"
            })
            mock.run.return_value.stderr = ""
            mock.run.return_value.returncode = 0
            yield mock
    
    def test_initialization(self, wrapper):
        """Test wrapper initialization"""
        assert wrapper.cache_dir == "test_cache"
        assert wrapper.cache == {}
        assert wrapper.last_call_time is None
        assert wrapper.min_delay == 2
    
    def test_model_selection_fast(self, wrapper):
        """Test model selection for fast tasks"""
        model = wrapper._select_model("fast")
        assert model == "haiku"
        
        model = wrapper._select_model("simple")
        assert model == "haiku"
    
    def test_model_selection_balanced(self, wrapper):
        """Test model selection for balanced tasks"""
        model = wrapper._select_model("balanced")
        assert model == "sonnet"
        
        model = wrapper._select_model("generation")
        assert model == "sonnet"
    
    def test_model_selection_complex(self, wrapper):
        """Test model selection for complex tasks"""
        model = wrapper._select_model("complex")
        assert model == "opus"
        
        model = wrapper._select_model("verification")
        assert model == "opus"
    
    def test_cache_key_generation(self, wrapper):
        """Test cache key generation"""
        key = wrapper._get_cache_key("Test prompt", "haiku")
        expected = hashlib.md5("Test prompt:haiku".encode()).hexdigest()
        assert key == expected
        
        # Different prompts should have different keys
        key2 = wrapper._get_cache_key("Different prompt", "haiku")
        assert key != key2
        
        # Different models should have different keys
        key3 = wrapper._get_cache_key("Test prompt", "sonnet")
        assert key != key3
    
    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep, wrapper, mock_subprocess):
        """Test rate limiting between calls"""
        wrapper.last_call_time = time.time() - 1  # 1 second ago
        
        wrapper.query("Test", model_type="fast")
        
        # Should have slept for at least 1 second (2 second min delay - 1 second elapsed)
        mock_sleep.assert_called()
        sleep_time = mock_sleep.call_args[0][0]
        assert sleep_time >= 1
    
    def test_query_with_cache_hit(self, wrapper):
        """Test query with cache hit"""
        cache_key = wrapper._get_cache_key("Test prompt", "haiku")
        wrapper.cache[cache_key] = {"cached": "response"}
        
        result = wrapper.query("Test prompt", model_type="fast")
        
        assert result == {"cached": "response"}
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_query_with_cache_miss(self, mock_run, wrapper):
        """Test query with cache miss"""
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
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_error_handling_non_zero_return(self, mock_run, wrapper):
        """Test error handling for non-zero return code"""
        mock_run.return_value = Mock(
            stdout="",
            stderr="Error message",
            returncode=1
        )
        
        with pytest.raises(RuntimeError, match="Claude CLI error"):
            wrapper.query("Test prompt")
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_error_handling_json_decode(self, mock_run, wrapper):
        """Test error handling for invalid JSON response"""
        mock_run.return_value = Mock(
            stdout="Invalid JSON",
            stderr="",
            returncode=0
        )
        
        result = wrapper.query("Test prompt")
        
        # Should return raw text when JSON decode fails
        assert result == "Invalid JSON"
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_timeout_handling(self, mock_run, wrapper):
        """Test timeout handling"""
        mock_run.side_effect = TimeoutError("Command timed out")
        
        with pytest.raises(TimeoutError):
            wrapper.query("Test prompt", timeout=5)
    
    def test_cache_persistence(self, wrapper, tmp_path):
        """Test cache persistence to disk"""
        wrapper.cache_dir = str(tmp_path)
        cache_file = tmp_path / "cache.json"
        
        # Add to cache
        wrapper.cache["test_key"] = {"test": "data"}
        wrapper._save_cache()
        
        # Check file exists
        assert cache_file.exists()
        
        # Load cache in new instance
        new_wrapper = ClaudeCodeCLIWrapper(cache_dir=str(tmp_path))
        new_wrapper._load_cache()
        
        assert "test_key" in new_wrapper.cache
        assert new_wrapper.cache["test_key"] == {"test": "data"}
    
    @pytest.mark.parametrize("prompt,model_type,expected_model", [
        ("Simple task", "fast", "haiku"),
        ("Generate survey", "balanced", "sonnet"),
        ("Verify quality", "complex", "opus"),
        ("Categorize papers", "categorization", "haiku"),
        ("Improve section", "improvement", "sonnet"),
        ("Evaluate survey", "evaluation", "opus"),
    ])
    def test_model_selection_parametrized(self, wrapper, prompt, model_type, expected_model):
        """Test model selection with various inputs"""
        model = wrapper._select_model(model_type)
        assert model == expected_model
    
    @patch.dict(os.environ, {"CLAUDE_RATE_LIMIT": "5"})
    def test_environment_variable_rate_limit(self):
        """Test rate limit from environment variable"""
        wrapper = ClaudeCodeCLIWrapper()
        assert wrapper.min_delay == 5
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_retry_on_rate_limit(self, mock_run, wrapper):
        """Test retry logic on rate limit errors"""
        # First call fails with rate limit
        mock_run.side_effect = [
            Mock(stdout="", stderr="Rate limit exceeded", returncode=1),
            Mock(stdout=json.dumps({"response": "Success"}), stderr="", returncode=0)
        ]
        
        with patch('time.sleep'):
            result = wrapper.query("Test prompt", max_retries=2)
        
        assert result == {"response": "Success"}
        assert mock_run.call_count == 2
    
    def test_clear_cache(self, wrapper):
        """Test cache clearing"""
        wrapper.cache = {"key1": "value1", "key2": "value2"}
        wrapper.clear_cache()
        
        assert wrapper.cache == {}
    
    @patch('src.wrappers.claude_wrapper.subprocess.run')
    def test_parallel_queries(self, mock_run, wrapper):
        """Test parallel query handling"""
        mock_run.return_value = Mock(
            stdout=json.dumps({"response": "Test"}),
            stderr="",
            returncode=0
        )
        
        # Simulate parallel queries
        from concurrent.futures import ThreadPoolExecutor
        
        def make_query(i):
            return wrapper.query(f"Query {i}", model_type="fast")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_query, i) for i in range(3)]
            results = [f.result() for f in futures]
        
        assert len(results) == 3
        assert all(r == {"response": "Test"} for r in results)
    
    def test_statistics_tracking(self, wrapper, mock_subprocess):
        """Test statistics tracking"""
        # Make some queries
        wrapper.query("Test 1", model_type="fast")
        wrapper.query("Test 2", model_type="balanced")
        wrapper.query("Test 1", model_type="fast")  # Cache hit
        
        stats = wrapper.get_statistics()
        
        assert stats["total_queries"] == 3
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        assert stats["cache_hit_rate"] == 1/3


@pytest.mark.integration
class TestClaudeWrapperIntegration:
    """Integration tests for Claude wrapper"""
    
    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), 
                        reason="Requires ANTHROPIC_API_KEY")
    def test_real_api_call(self):
        """Test real API call (requires API key)"""
        wrapper = ClaudeCodeCLIWrapper()
        result = wrapper.query("What is 2+2?", model_type="fast")
        
        assert result is not None
        assert isinstance(result, (dict, str))
    
    def test_full_workflow(self, tmp_path):
        """Test full workflow with caching"""
        wrapper = ClaudeCodeCLIWrapper(cache_dir=str(tmp_path))
        
        with patch('src.wrappers.claude_wrapper.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout=json.dumps({"response": "Survey generated"}),
                stderr="",
                returncode=0
            )
            
            # First query - cache miss
            result1 = wrapper.query("Generate survey", model_type="balanced")
            assert mock_run.call_count == 1
            
            # Second query - cache hit
            result2 = wrapper.query("Generate survey", model_type="balanced")
            assert mock_run.call_count == 1  # Should not increase
            
            assert result1 == result2
            
            # Save and reload cache
            wrapper._save_cache()
            
            new_wrapper = ClaudeCodeCLIWrapper(cache_dir=str(tmp_path))
            new_wrapper._load_cache()
            
            # Third query with new instance - cache hit from disk
            result3 = new_wrapper.query("Generate survey", model_type="balanced")
            assert mock_run.call_count == 1  # Still should not increase
            
            assert result3 == result1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])