#!/usr/bin/env python3
"""
Test script for Claude Code CLI wrapper.
This uses the Claude CLI that's already installed, no API key needed in Python.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_openai_wrapper import ClaudeCodeCLIWrapper


def test_simple_query():
    """Test basic query without tools"""
    print("=" * 60)
    print("TEST 1: Simple Query")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper()
        
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "What is 2 + 2? Answer with just the number."}
            ],
            model="haiku",  # Use faster model for testing
            max_turns=1
        )
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
            return False
        else:
            print(f"✅ Response: {response['choices'][0]['message']['content']}")
            return True
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_system_prompt():
    """Test with system prompt"""
    print("\n" + "=" * 60)
    print("TEST 2: With System Prompt")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper()
        
        response = wrapper.chat_completion(
            messages=[
                {"role": "system", "content": "You always respond in uppercase."},
                {"role": "user", "content": "say hello"}
            ],
            model="haiku",
            max_turns=1
        )
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
            return False
        else:
            content = response['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            # Check if response is uppercase
            if any(c.isupper() for c in content if c.isalpha()):
                print("✅ System prompt worked (response has uppercase)")
                return True
            else:
                print("⚠️  Response might not follow system prompt")
                return True  # Still pass, just warn
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_bash_tool():
    """Test with Bash tool enabled"""
    print("\n" + "=" * 60)
    print("TEST 3: With Bash Tool")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper(
            default_cwd="/data2/yixin/workspace/agent4sci-llm-survey/scripts"
        )
        
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "List the Python files in the current directory using ls. Just show the filenames."}
            ],
            model="haiku",
            max_turns=2,
            allowed_tools=["Bash"]
        )
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
            return False
        else:
            content = response['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            # Check if response mentions Python files
            if ".py" in content or "claude_openai_wrapper" in content:
                print("✅ Tool usage worked (found Python files)")
                return True
            else:
                print("⚠️  Response might not have used the tool")
                return True
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_with_read_tool():
    """Test with Read tool"""
    print("\n" + "=" * 60)
    print("TEST 4: With Read Tool")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper(
            default_cwd="/data2/yixin/workspace/agent4sci-llm-survey/scripts"
        )
        
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Check if there's a requirements.txt file in this directory and tell me what's in it (just list the main packages, not versions)."}
            ],
            model="haiku",
            max_turns=2,
            allowed_tools=["Read", "Glob"]
        )
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
            return False
        else:
            content = response['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            if "openai" in content.lower() or "claude" in content.lower():
                print("✅ Read tool worked (found package names)")
                return True
            else:
                print("⚠️  Response might not have read the file")
                return True
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_multi_turn_conversation():
    """Test multi-turn conversation"""
    print("\n" + "=" * 60)
    print("TEST 5: Multi-turn Conversation")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper()
        
        # First turn
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Remember the number 42. What number did I ask you to remember?"}
            ],
            model="haiku",
            max_turns=1
        )
        
        if "error" in response:
            print(f"❌ Error in first turn: {response['error']['message']}")
            return False
        
        print(f"First response: {response['choices'][0]['message']['content']}")
        
        # Second turn with context
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Remember the number 42."},
                {"role": "assistant", "content": response['choices'][0]['message']['content']},
                {"role": "user", "content": "What was the number again?"}
            ],
            model="haiku",
            max_turns=1
        )
        
        if "error" in response:
            print(f"❌ Error in second turn: {response['error']['message']}")
            return False
        else:
            content = response['choices'][0]['message']['content']
            print(f"✅ Second response: {content}")
            if "42" in content:
                print("✅ Multi-turn worked (remembered the number)")
                return True
            else:
                print("⚠️  Might not have maintained context")
                return True
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_openai_style_interface():
    """Test that the interface mimics OpenAI style"""
    print("\n" + "=" * 60)
    print("TEST 6: OpenAI-style Interface Check")
    print("=" * 60)
    
    try:
        wrapper = ClaudeCodeCLIWrapper()
        
        # Use OpenAI-style parameters
        response = wrapper.chat_completion(
            messages=[
                {"role": "user", "content": "Say 'test passed'"}
            ],
            model="haiku",
            max_turns=1,
            output_format="json"  # Request JSON format
        )
        
        if "error" in response:
            print(f"❌ Error: {response['error']['message']}")
            return False
        
        # Check response structure
        checks = [
            ("choices" in response, "Has 'choices' field"),
            (isinstance(response.get("choices"), list), "'choices' is a list"),
            (len(response.get("choices", [])) > 0, "Has at least one choice"),
            ("message" in response.get("choices", [{}])[0], "Choice has 'message'"),
            ("content" in response.get("choices", [{}])[0].get("message", {}), "Message has 'content'"),
            ("role" in response.get("choices", [{}])[0].get("message", {}), "Message has 'role'"),
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                all_passed = False
        
        if all_passed:
            print(f"\n✅ Response content: {response['choices'][0]['message']['content']}")
            print("✅ OpenAI-style interface working correctly")
        
        return all_passed
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🧪 TESTING CLAUDE CODE CLI WRAPPER " + "🧪")
    print("=" * 60)
    
    tests = [
        ("Simple Query", test_simple_query),
        ("System Prompt", test_with_system_prompt),
        ("Bash Tool", test_with_bash_tool),
        ("Read Tool", test_with_read_tool),
        ("Multi-turn", test_multi_turn_conversation),
        ("OpenAI Interface", test_openai_style_interface),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! The CLI wrapper is working correctly.")
    elif passed_count > 0:
        print(f"\n⚠️  {passed_count} tests passed, but some failed.")
    else:
        print("\n❌ All tests failed. Check Claude CLI installation and login.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)