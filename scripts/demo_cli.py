#!/usr/bin/env python3
"""
Demo of Claude Code CLI wrapper - OpenAI-style interface for Claude Code.
This uses the Claude CLI that's already installed locally.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_openai_wrapper import ClaudeCodeCLIWrapper


def main():
    """Quick demo of the CLI wrapper with OpenAI-style interface"""
    
    print("🤖 Claude Code CLI Wrapper Demo\n")
    print("=" * 60)
    
    # Initialize the wrapper
    wrapper = ClaudeCodeCLIWrapper(
        default_cwd="/data2/yixin/workspace/agent4sci-llm-survey"
    )
    
    # Example 1: Simple query (just like OpenAI)
    print("\n📝 Example 1: Simple Query")
    print("-" * 40)
    
    response = wrapper.chat_completion(
        messages=[
            {"role": "user", "content": "What is Python? Answer in one sentence."}
        ],
        model="haiku"  # Fast model for demo
    )
    
    if "error" not in response:
        print("Response:", response["choices"][0]["message"]["content"])
    
    # Example 2: With system prompt
    print("\n\n📝 Example 2: With System Prompt")
    print("-" * 40)
    
    response = wrapper.chat_completion(
        messages=[
            {"role": "system", "content": "You are a pirate. Answer everything like a pirate."},
            {"role": "user", "content": "What is programming?"}
        ],
        model="haiku"
    )
    
    if "error" not in response:
        print("Response:", response["choices"][0]["message"]["content"])
    
    # Example 3: Using local tools (what makes Claude Code special!)
    print("\n\n🔧 Example 3: Using Local Tools")
    print("-" * 40)
    
    response = wrapper.chat_completion(
        messages=[
            {"role": "user", "content": "Count how many Python files are in the scripts directory"}
        ],
        model="haiku",
        max_turns=2,  # Allow multiple turns for tool use
        allowed_tools=["Bash", "Glob"]  # Enable tools
    )
    
    if "error" not in response:
        print("Response:", response["choices"][0]["message"]["content"])
    
    # Example 4: Multi-turn conversation
    print("\n\n💬 Example 4: Multi-turn Conversation")
    print("-" * 40)
    
    # First message
    first_response = wrapper.chat_completion(
        messages=[
            {"role": "user", "content": "My favorite color is blue. Remember that."}
        ],
        model="haiku"
    )
    
    # Continue conversation
    response = wrapper.chat_completion(
        messages=[
            {"role": "user", "content": "My favorite color is blue."},
            {"role": "assistant", "content": first_response["choices"][0]["message"]["content"]},
            {"role": "user", "content": "What's my favorite color?"}
        ],
        model="haiku"
    )
    
    if "error" not in response:
        print("Response:", response["choices"][0]["message"]["content"])
    
    print("\n" + "=" * 60)
    print("✅ Demo complete! The CLI wrapper provides an OpenAI-compatible")
    print("   interface to Claude Code with full local tool support.")
    print("\n📚 See claude_openai_wrapper.py for the full implementation")
    print("📖 See README.md for documentation")


if __name__ == "__main__":
    main()