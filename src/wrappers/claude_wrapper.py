"""
Enhanced Claude CLI Wrapper for LLM Survey Generation
Includes rate limiting, response caching, and robust error handling.
"""

import os
import sys
import json
import time
import hashlib
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import wraps

# Add scripts directory to path to import the base wrapper
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
from claude_openai_wrapper import ClaudeCodeCLIWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with exponential backoff."""
    
    def __init__(self, min_delay: float = 3.0, max_delay: float = 60.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_call_time = 0
        self.consecutive_errors = 0
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        # Calculate delay with exponential backoff for errors
        delay = self.min_delay * (2 ** self.consecutive_errors)
        delay = min(delay, self.max_delay)
        
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            
        self.last_call_time = time.time()
        
    def register_success(self):
        """Reset error counter on successful call."""
        self.consecutive_errors = 0
        
    def register_error(self):
        """Increment error counter for exponential backoff."""
        self.consecutive_errors += 1


class ResponseCache:
    """Cache for Claude responses with TTL support."""
    
    def __init__(self, cache_dir: str = "data/cache/claude", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
    def _get_cache_key(self, messages: List[Dict], model: str, **kwargs) -> str:
        """Generate cache key from request parameters."""
        cache_data = {
            'messages': messages,
            'model': model,
            **kwargs
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
        
    def get(self, messages: List[Dict], model: str, **kwargs) -> Optional[Dict]:
        """Retrieve cached response if available and not expired."""
        cache_key = self._get_cache_key(messages, model, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Check TTL
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.ttl:
                logger.debug(f"Cache expired for key {cache_key[:8]}...")
                try:
                    cache_file.unlink()  # Delete expired cache
                except (PermissionError, OSError) as e:
                    logger.warning(f"Could not delete expired cache: {e}")
                return None
                
            logger.info(f"Cache hit for key {cache_key[:8]}...")
            return cached_data['response']
            
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
            
    def set(self, messages: List[Dict], model: str, response: Dict, **kwargs):
        """Store response in cache."""
        cache_key = self._get_cache_key(messages, model, **kwargs)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            cached_data = {
                'timestamp': datetime.now().isoformat(),
                'response': response,
                'messages': messages,
                'model': model
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
            logger.debug(f"Cached response for key {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
            
    def clear_expired(self):
        """Remove expired cache entries."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cached_time > self.ttl:
                    cache_file.unlink()
                    logger.debug(f"Deleted expired cache: {cache_file.name}")
            except Exception as e:
                logger.warning(f"Error checking cache file {cache_file}: {e}")


class TokenTracker:
    """Track token usage and estimate costs."""
    
    # Approximate token costs (per 1M tokens)
    COSTS = {
        'haiku': {'input': 0.25, 'output': 1.25},
        'sonnet': {'input': 3.00, 'output': 15.00},
        'opus': {'input': 15.00, 'output': 75.00}
    }
    
    def __init__(self):
        self.usage = {
            'haiku': {'input': 0, 'output': 0, 'calls': 0},
            'sonnet': {'input': 0, 'output': 0, 'calls': 0},
            'opus': {'input': 0, 'output': 0, 'calls': 0}
        }
        
    def track(self, model: str, input_text: str, output_text: str):
        """Track token usage for a call."""
        # Rough estimation: 1 token ≈ 4 characters
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        
        if model in self.usage:
            self.usage[model]['input'] += input_tokens
            self.usage[model]['output'] += output_tokens
            self.usage[model]['calls'] += 1
            
    def get_cost_estimate(self) -> float:
        """Calculate estimated cost in USD."""
        total_cost = 0.0
        for model, usage in self.usage.items():
            if model in self.COSTS:
                input_cost = (usage['input'] / 1_000_000) * self.COSTS[model]['input']
                output_cost = (usage['output'] / 1_000_000) * self.COSTS[model]['output']
                total_cost += input_cost + output_cost
        return total_cost
        
    def get_summary(self) -> Dict:
        """Get usage summary with costs."""
        summary = {
            'models': {},
            'total_calls': sum(u['calls'] for u in self.usage.values()),
            'total_input_tokens': sum(u['input'] for u in self.usage.values()),
            'total_output_tokens': sum(u['output'] for u in self.usage.values()),
            'estimated_cost_usd': self.get_cost_estimate()
        }
        
        for model, usage in self.usage.items():
            if usage['calls'] > 0:
                summary['models'][model] = {
                    'calls': usage['calls'],
                    'input_tokens': usage['input'],
                    'output_tokens': usage['output']
                }
                
        return summary


class EnhancedClaudeWrapper:
    """
    Enhanced Claude CLI wrapper with rate limiting, caching, and error handling.
    Optimized for survey generation tasks.
    """
    
    def __init__(
        self,
        default_cwd: Optional[str] = None,
        cache_enabled: bool = True,
        rate_limit_enabled: bool = True,
        min_delay: float = 3.0,
        max_retries: int = 3
    ):
        """
        Initialize enhanced wrapper.
        
        Args:
            default_cwd: Default working directory
            cache_enabled: Enable response caching
            rate_limit_enabled: Enable rate limiting
            min_delay: Minimum delay between API calls (seconds)
            max_retries: Maximum number of retries on error
        """
        self.base_wrapper = ClaudeCodeCLIWrapper(default_cwd)
        self.cache = ResponseCache() if cache_enabled else None
        self.rate_limiter = RateLimiter(min_delay) if rate_limit_enabled else None
        self.token_tracker = TokenTracker()
        self.max_retries = max_retries
        
        # Model selection logic
        self.model_selector = {
            'fast': 'haiku',      # Quick queries, simple tasks
            'balanced': 'sonnet', # Most generation tasks
            'complex': 'opus'     # Complex reasoning, verification
        }
        
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonnet",
        task_type: Optional[str] = None,
        use_cache: bool = True,
        max_turns: int = 1,
        allowed_tools: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Enhanced chat completion with caching and rate limiting.
        
        Args:
            messages: OpenAI-style messages
            model: Model name or task type (fast/balanced/complex)
            task_type: Override model selection based on task
            use_cache: Whether to use cache for this request
            max_turns: Maximum conversation turns
            allowed_tools: List of allowed Claude tools
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary with OpenAI-compatible format
        """
        # Select model based on task type if provided
        if task_type in self.model_selector:
            model = self.model_selector[task_type]
        elif model in self.model_selector:
            model = self.model_selector[model]
            
        # Check cache if enabled
        if self.cache and use_cache:
            cached_response = self.cache.get(messages, model, **kwargs)
            if cached_response:
                return cached_response
                
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()
            
        # Prepare input text for tracking
        input_text = json.dumps(messages)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Call base wrapper
                response = self.base_wrapper.chat_completion(
                    messages=messages,
                    model=model,
                    max_turns=max_turns,
                    allowed_tools=allowed_tools,
                    **kwargs
                )
                
                # Check for errors in response
                if "error" in response:
                    raise Exception(f"API Error: {response['error']}")
                    
                # Track success
                if self.rate_limiter:
                    self.rate_limiter.register_success()
                    
                # Track tokens
                output_text = response["choices"][0]["message"]["content"]
                self.token_tracker.track(model, input_text, output_text)
                
                # Cache successful response
                if self.cache and use_cache:
                    self.cache.set(messages, model, response, **kwargs)
                    
                # Add metadata
                response["metadata"] = {
                    "model_used": model,
                    "attempt": attempt + 1,
                    "cached": False
                }
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if self.rate_limiter:
                    self.rate_limiter.register_error()
                    
                if attempt < self.max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        # All retries failed
        return {
            "error": {
                "message": str(last_error),
                "type": "max_retries_exceeded",
                "attempts": self.max_retries
            }
        }
        
    def generate_survey_section(
        self,
        section_type: str,
        context: Dict[str, Any],
        papers: List[Dict],
        model_override: Optional[str] = None
    ) -> str:
        """
        Generate a specific survey section using appropriate model.
        
        Args:
            section_type: Type of section (intro, method, results, etc.)
            context: Survey context and requirements
            papers: Relevant papers for the section
            model_override: Override default model selection
            
        Returns:
            Generated section text
        """
        # Select model based on section complexity
        model_map = {
            'introduction': 'balanced',
            'abstract': 'balanced',
            'methodology': 'complex',
            'literature_review': 'complex',
            'analysis': 'complex',
            'conclusion': 'balanced',
            'references': 'fast'
        }
        
        model = model_override or self.model_selector.get(
            model_map.get(section_type, 'balanced')
        )
        
        # Format papers for context
        papers_text = self._format_papers_for_context(papers[:10])  # Limit to 10 papers
        
        # Create prompt
        messages = [
            {
                "role": "system",
                "content": "You are an expert academic writer specializing in AI/ML surveys."
            },
            {
                "role": "user",
                "content": f"""Generate a {section_type} section for a survey on "{context.get('topic', 'AI research')}".

Context:
- Target audience: {context.get('audience', 'AI researchers')}
- Survey scope: {context.get('scope', 'comprehensive review')}
- Key themes: {context.get('themes', [])}

Relevant papers:
{papers_text}

Please write a well-structured {section_type} section that:
1. Follows academic writing conventions
2. Properly cites the provided papers
3. Maintains coherent flow and logical structure
4. Is approximately {context.get('section_length', 500)} words

Generate the section:"""
            }
        ]
        
        response = self.chat_completion(
            messages=messages,
            model=model,
            task_type='complex' if section_type in ['methodology', 'analysis'] else 'balanced'
        )
        
        if "error" in response:
            logger.error(f"Failed to generate {section_type}: {response['error']}")
            return f"[Error generating {section_type} section]"
            
        return response["choices"][0]["message"]["content"]
        
    def verify_content(
        self,
        content: str,
        verification_type: str = "coherence"
    ) -> Dict[str, Any]:
        """
        Verify generated content for quality issues.
        
        Args:
            content: Content to verify
            verification_type: Type of verification (coherence, citations, etc.)
            
        Returns:
            Verification results with issues and suggestions
        """
        prompts = {
            'coherence': "Check this text for logical flow and coherence issues",
            'citations': "Verify all citations are properly formatted and referenced",
            'factual': "Check for potential factual errors or inconsistencies",
            'style': "Review academic writing style and suggest improvements"
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert academic editor and fact-checker."
            },
            {
                "role": "user",
                "content": f"""{prompts.get(verification_type, prompts['coherence'])}:

{content}

Provide a structured analysis with:
1. Issues found (if any)
2. Severity (minor/major)
3. Specific suggestions for improvement
4. Overall quality score (1-10)"""
            }
        ]
        
        response = self.chat_completion(
            messages=messages,
            model='sonnet',  # Use balanced model for verification
            task_type='balanced'
        )
        
        if "error" in response:
            return {"error": response["error"]}
            
        return {
            "verification_type": verification_type,
            "analysis": response["choices"][0]["message"]["content"],
            "timestamp": datetime.now().isoformat()
        }
        
    def _format_papers_for_context(self, papers: List[Dict]) -> str:
        """Format papers list for inclusion in prompts."""
        formatted = []
        for i, paper in enumerate(papers, 1):
            formatted.append(
                f"{i}. {paper.get('title', 'Unknown Title')} "
                f"({paper.get('authors', ['Unknown'])[0] if isinstance(paper.get('authors'), list) else 'Unknown'} et al., "
                f"{paper.get('year', 'Unknown Year')})\n"
                f"   Summary: {paper.get('summary', '')[:200]}..."
            )
        return "\n".join(formatted)
        
    def get_usage_summary(self) -> Dict:
        """Get token usage and cost summary."""
        return self.token_tracker.get_summary()
        
    def clear_cache(self):
        """Clear expired cache entries."""
        if self.cache:
            self.cache.clear_expired()


def main():
    """Test the enhanced wrapper."""
    wrapper = EnhancedClaudeWrapper()
    
    # Test basic completion
    response = wrapper.chat_completion(
        messages=[
            {"role": "user", "content": "What is a transformer model in 50 words?"}
        ],
        model="haiku"
    )
    
    if "error" not in response:
        print("Response:", response["choices"][0]["message"]["content"])
        print("\nUsage:", wrapper.get_usage_summary())
    else:
        print("Error:", response["error"])


if __name__ == "__main__":
    main()