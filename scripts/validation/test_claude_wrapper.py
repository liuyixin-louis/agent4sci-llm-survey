#!/usr/bin/env python
"""
Test script for Enhanced Claude CLI Wrapper
"""

import sys
import time
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper
from src.data.data_loader import SciMCPDataLoader


def test_claude_wrapper():
    """Test the enhanced Claude wrapper functionality."""
    print("=" * 60)
    print("Testing Enhanced Claude CLI Wrapper")
    print("=" * 60)
    
    # Initialize wrapper
    wrapper = EnhancedClaudeWrapper(
        cache_enabled=True,
        rate_limit_enabled=True,
        min_delay=2.0  # 2 seconds between calls for testing
    )
    
    # Test 1: Basic completion with haiku (fast model)
    print("\n1. Testing basic completion with haiku model...")
    try:
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Explain transformers in exactly 30 words."}
            ],
            model="haiku"
        )
        
        if "error" not in response:
            content = response["choices"][0]["message"]["content"]
            print(f"✓ Response received ({len(content.split())} words)")
            print(f"  Content: {content[:100]}...")
        else:
            print(f"✗ Error: {response['error']}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False
    
    # Test 2: System prompt with sonnet (balanced model)
    print("\n2. Testing system prompt with sonnet model...")
    try:
        response = wrapper.chat_completion(
            messages=[
                {"role": "system", "content": "You are a concise AI researcher. Answer in one sentence."},
                {"role": "user", "content": "What is RLHF?"}
            ],
            model="sonnet"
        )
        
        if "error" not in response:
            content = response["choices"][0]["message"]["content"]
            print(f"✓ Response received")
            print(f"  Content: {content}")
        else:
            print(f"✗ Error: {response['error']}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 3: Cache functionality
    print("\n3. Testing cache functionality...")
    try:
        # First call (should be cached)
        start_time = time.time()
        response1 = wrapper.chat_completion(
            messages=[{"role": "user", "content": "What is attention mechanism?"}],
            model="haiku",
            use_cache=True
        )
        time1 = time.time() - start_time
        
        # Second call (should be from cache)
        start_time = time.time()
        response2 = wrapper.chat_completion(
            messages=[{"role": "user", "content": "What is attention mechanism?"}],
            model="haiku",
            use_cache=True
        )
        time2 = time.time() - start_time
        
        if "error" not in response1 and "error" not in response2:
            print(f"✓ Cache working")
            print(f"  First call: {time1:.2f}s")
            print(f"  Cached call: {time2:.2f}s (should be faster)")
            if time2 < time1 / 2:  # Cached should be at least 2x faster
                print(f"  Cache speedup: {time1/time2:.1f}x")
        else:
            print(f"✗ Error in responses")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 4: Survey section generation
    print("\n4. Testing survey section generation...")
    try:
        # Load some sample papers
        loader = SciMCPDataLoader()
        papers = loader.load_data()
        sample_papers = papers.head(5).to_dict('records')
        
        context = {
            'topic': 'Large Language Models',
            'audience': 'AI researchers',
            'scope': 'Recent advances in 2024',
            'section_length': 200
        }
        
        section = wrapper.generate_survey_section(
            section_type='introduction',
            context=context,
            papers=sample_papers
        )
        
        if section and not section.startswith("[Error"):
            print(f"✓ Generated introduction section")
            print(f"  Length: {len(section.split())} words")
            print(f"  Preview: {section[:150]}...")
        else:
            print(f"✗ Failed to generate section")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 5: Content verification
    print("\n5. Testing content verification...")
    try:
        test_content = """
        Transformers are neural network architectures that use self-attention mechanisms.
        They were introduced in the paper "Attention is All You Need" by Vaswani et al. (2017).
        """
        
        verification = wrapper.verify_content(
            content=test_content,
            verification_type="coherence"
        )
        
        if "error" not in verification:
            print(f"✓ Content verified")
            print(f"  Analysis preview: {str(verification['analysis'])[:150]}...")
        else:
            print(f"✗ Verification failed")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    usage = wrapper.get_usage_summary()
    print(f"Total API calls: {usage['total_calls']}")
    print(f"Estimated tokens: {usage['total_input_tokens'] + usage['total_output_tokens']}")
    print(f"Estimated cost: ${usage['estimated_cost_usd']:.4f}")
    
    if usage['models']:
        print("\nModel usage:")
        for model, stats in usage['models'].items():
            print(f"  {model}: {stats['calls']} calls")
    
    return True


if __name__ == "__main__":
    print("Note: This test requires Claude CLI to be installed and configured.")
    print("If you haven't set it up, run: npm install -g @anthropic-ai/claude-code && claude login\n")
    
    try:
        success = test_claude_wrapper()
        if success:
            print("\n✓ All tests completed!")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        sys.exit(1)