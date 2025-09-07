#!/usr/bin/env python3
"""
Simple, ready-to-run example showing the quickest way to use each approach.
"""

import os
from claude_openai_wrapper import (
    AnthropicOpenAIWrapper,
    ClaudeCodeOpenAIAdapter,
    ClaudeCodeCLIWrapper
)


def quickstart():
    """Minimal examples for each approach"""
    
    # Ensure API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
        print("export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    print("Claude OpenAI-Compatible Wrapper Examples\n")
    print("=" * 50)
    
    # ========================================
    # Approach 1: Simple Claude API calls
    # ========================================
    print("\n1. SIMPLE API (No local tools):")
    print("-" * 30)
    
    client = AnthropicOpenAIWrapper()
    response = client.chat_completion(
        messages=[
            {"role": "user", "content": "Say 'Hello World' in Python"}
        ],
        model="claude-3-5-sonnet-20241022"
    )
    print(response.choices[0].message.content)
    
    # ========================================
    # Approach 2: Claude Code with tools
    # ========================================
    print("\n2. CLAUDE CODE SDK (With local tools):")
    print("-" * 30)
    
    # This requires: pip install claude-code-sdk
    try:
        sdk = ClaudeCodeOpenAIAdapter()
        response = sdk.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "user", "content": "List files in current directory"}
            ],
            max_turns=2,
            allowed_tools=["Bash"],  # Enable bash commands
            permission_mode="acceptEdits"
        )
        print(response.choices[0].message.content)
    except ImportError:
        print("Install claude-code-sdk: pip install claude-code-sdk")
    
    # ========================================
    # Approach 3: CLI wrapper
    # ========================================
    print("\n3. CLI WRAPPER (Via subprocess):")
    print("-" * 30)
    
    # This requires: npm install -g @anthropic-ai/claude-code && claude login
    try:
        cli = ClaudeCodeCLIWrapper()
        response = cli.chat_completion(
            messages=[
                {"role": "user", "content": "What is 2+2?"}
            ],
            model="sonnet"
        )
        if "error" not in response:
            print(response["choices"][0]["message"]["content"])
        else:
            print(f"Error: {response['error']['message']}")
    except RuntimeError as e:
        print(f"CLI not available: {e}")
        print("Install: npm install -g @anthropic-ai/claude-code")
        print("Then: claude login")


if __name__ == "__main__":
    quickstart()