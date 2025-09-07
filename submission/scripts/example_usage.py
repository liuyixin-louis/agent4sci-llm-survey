"""
Example usage of Claude OpenAI-compatible wrappers.
Demonstrates all three approaches with practical examples.
"""

import os
import asyncio
from claude_openai_wrapper import (
    AnthropicOpenAIWrapper,
    ClaudeCodeOpenAIAdapter,
    ClaudeCodeCLIWrapper,
    ClaudeOpenAIUnified
)


def example_anthropic_openai():
    """
    Example 1: Using OpenAI SDK with Anthropic endpoint.
    This is the simplest approach but has no access to local tools.
    """
    print("=" * 60)
    print("EXAMPLE 1: Anthropic OpenAI Compatibility (No Local Tools)")
    print("=" * 60)
    
    # Make sure to set ANTHROPIC_API_KEY environment variable
    wrapper = AnthropicOpenAIWrapper()
    
    response = wrapper.chat_completion(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain Python decorators in 2 sentences."}
        ],
        model="claude-3-5-sonnet-20241022",
        max_tokens=150
    )
    
    print("Response:", response.choices[0].message.content)
    print()


def example_claude_code_sdk():
    """
    Example 2: Using Claude Code SDK wrapper with local tools.
    This approach gives access to file operations and bash commands.
    """
    print("=" * 60)
    print("EXAMPLE 2: Claude Code SDK (With Local Tools)")
    print("=" * 60)
    
    # Initialize with project context
    adapter = ClaudeCodeOpenAIAdapter(
        cwd="/data2/yixin/workspace/agent4sci-llm-survey",
        add_dirs=["scripts"]  # Include scripts directory in context
    )
    
    # Example 2a: Simple chat without tools
    print("2a. Simple chat:")
    response = adapter.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "user", "content": "What is 2 + 2?"}
        ]
    )
    print("Response:", response.choices[0].message.content)
    print()
    
    # Example 2b: Using local tools to read files
    print("2b. Using Read tool to examine project:")
    response = adapter.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": "You can read local files."},
            {"role": "user", "content": "List the Python files in the scripts directory."}
        ],
        max_turns=2,
        allowed_tools=["Read", "Glob"],
        permission_mode="acceptEdits"
    )
    print("Response:", response.choices[0].message.content)
    print()
    
    # Example 2c: More complex task with multiple tools
    print("2c. Complex task with multiple tools:")
    response = adapter.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": "You are a code analyzer."},
            {"role": "user", "content": "Check if there are any TODO comments in the Python files."}
        ],
        max_turns=3,
        allowed_tools=["Grep", "Read"],
        permission_mode="acceptEdits"
    )
    print("Response:", response.choices[0].message.content)
    print()


def example_cli_wrapper():
    """
    Example 3: Using CLI wrapper (subprocess).
    This requires Claude CLI to be installed and logged in.
    """
    print("=" * 60)
    print("EXAMPLE 3: CLI Wrapper (Subprocess)")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper(
            default_cwd="/data2/yixin/workspace/agent4sci-llm-survey"
        )
        
        # Example 3a: Simple query
        print("3a. Simple query via CLI:")
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ],
            model="sonnet",
            max_turns=1
        )
        
        if "error" in response:
            print("Error:", response["error"]["message"])
        else:
            print("Response:", response["choices"][0]["message"]["content"])
        print()
        
        # Example 3b: With system prompt and tools
        print("3b. CLI with tools:")
        response = wrapper.chat_completion(
            messages=[
                {"role": "system", "content": "You can analyze code files."},
                {"role": "user", "content": "Count the Python files in this project."}
            ],
            model="sonnet",
            max_turns=2,
            allowed_tools=["Glob", "Bash"],
            output_format="json"
        )
        
        if "error" in response:
            print("Error:", response["error"]["message"])
        else:
            print("Response:", response["choices"][0]["message"]["content"])
        print()
        
    except RuntimeError as e:
        print(f"CLI Error: {e}")
        print("Make sure Claude CLI is installed: npm install -g @anthropic-ai/claude-code")
        print("And logged in: claude login")
    print()


def example_unified_interface():
    """
    Example 4: Using the unified interface to switch between backends.
    """
    print("=" * 60)
    print("EXAMPLE 4: Unified Interface")
    print("=" * 60)
    
    messages = [
        {"role": "system", "content": "You are a Python expert."},
        {"role": "user", "content": "What is a list comprehension?"}
    ]
    
    # Try different backends
    backends = [
        ("anthropic", {}),
        ("sdk", {"allowed_tools": ["Read"]}),
        ("cli", {})
    ]
    
    for backend_name, backend_kwargs in backends:
        try:
            print(f"\nUsing backend: {backend_name}")
            client = ClaudeOpenAIUnified(backend=backend_name, **backend_kwargs)
            
            response = client.create_completion(
                messages=messages,
                model="claude-3-5-sonnet-20241022" if backend_name != "cli" else "sonnet"
            )
            
            if isinstance(response, dict) and "error" in response:
                print(f"Error: {response['error']['message']}")
            else:
                content = (
                    response.choices[0].message.content 
                    if hasattr(response, 'choices') 
                    else response["choices"][0]["message"]["content"]
                )
                print(f"Response preview: {content[:100]}...")
                
        except Exception as e:
            print(f"Backend {backend_name} failed: {e}")
    
    print()


def example_streaming():
    """
    Example 5: Streaming responses (CLI backend).
    """
    print("=" * 60)
    print("EXAMPLE 5: Streaming Responses")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper()
        
        print("Streaming response:")
        stream = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Count from 1 to 5 slowly."}
            ],
            model="sonnet",
            stream=True
        )
        
        for chunk in stream:
            if "error" in chunk:
                print(f"Error: {chunk['error']['message']}")
                break
            elif "choices" in chunk and chunk["choices"][0].get("delta"):
                content = chunk["choices"][0]["delta"].get("content", "")
                print(content, end="", flush=True)
        print("\n")
        
    except RuntimeError as e:
        print(f"Streaming error: {e}")
    print()


def example_advanced_tools():
    """
    Example 6: Advanced tool usage with Claude Code SDK.
    """
    print("=" * 60)
    print("EXAMPLE 6: Advanced Tool Usage")
    print("=" * 60)
    
    adapter = ClaudeCodeOpenAIAdapter(
        cwd="/data2/yixin/workspace/agent4sci-llm-survey"
    )
    
    # Create a file and then read it back
    print("Creating and reading a test file:")
    response = adapter.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {
                "role": "user", 
                "content": (
                    "Create a file called 'test_example.txt' in the scripts directory "
                    "with the content 'Hello from Claude Code!' and then read it back to confirm."
                )
            }
        ],
        max_turns=3,
        allowed_tools=["Write", "Read"],
        permission_mode="acceptEdits"
    )
    print("Response:", response.choices[0].message.content)
    print()
    
    # Run a bash command
    print("Running bash command:")
    response = adapter.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {
                "role": "user",
                "content": "List all Python files in the scripts directory using ls command."
            }
        ],
        max_turns=2,
        allowed_tools=["Bash"],
        permission_mode="acceptEdits"
    )
    print("Response:", response.choices[0].message.content)
    print()


def main():
    """Run all examples"""
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set in environment")
        print("Some examples may not work without it")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        print()
    
    # Run examples based on what's available
    examples = [
        ("1. Anthropic OpenAI Compatibility", example_anthropic_openai),
        ("2. Claude Code SDK", example_claude_code_sdk),
        ("3. CLI Wrapper", example_cli_wrapper),
        ("4. Unified Interface", example_unified_interface),
        ("5. Streaming", example_streaming),
        ("6. Advanced Tools", example_advanced_tools)
    ]
    
    print("Select examples to run:")
    print("0. Run all examples")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("q. Quit")
    
    choice = input("\nEnter choice (0-6 or q): ").strip().lower()
    
    if choice == 'q':
        return
    elif choice == '0':
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"Error in {name}: {e}")
                print()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")


if __name__ == "__main__":
    main()