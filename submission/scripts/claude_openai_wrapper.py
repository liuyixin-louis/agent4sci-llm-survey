"""
Claude Code OpenAI-Compatible Wrapper
Provides three different approaches to call Claude/Claude Code with OpenAI-style interfaces
"""

import os
import json
import subprocess
import shlex
import asyncio
from types import SimpleNamespace
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from dataclasses import dataclass


# ============================================================================
# APPROACH 1: OpenAI SDK with Anthropic Endpoint (No Local Tools)
# ============================================================================

def create_anthropic_openai_client():
    """
    Create an OpenAI client that points to Anthropic's API.
    This approach uses OpenAI's SDK but talks to Claude.
    
    Limitations:
    - No access to Claude Code's local tools (Read, Write, Bash, etc.)
    - Some OpenAI-specific parameters are ignored
    - Best for simple model-only interactions
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Please install openai: pip install openai")
    
    return OpenAI(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        base_url="https://api.anthropic.com/v1/"
    )


class AnthropicOpenAIWrapper:
    """Simple wrapper using OpenAI SDK with Anthropic endpoint"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        self.client = OpenAI(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url="https://api.anthropic.com/v1/"
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs
    ):
        """
        Create a chat completion using OpenAI-style interface.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Claude model name
            **kwargs: Additional OpenAI parameters (some may be ignored)
        
        Returns:
            OpenAI ChatCompletion response object
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )


# ============================================================================
# APPROACH 2: Claude Code SDK Wrapper (WITH Local Tools Support)
# ============================================================================

class ClaudeCodeOpenAIAdapter:
    """
    OpenAI-compatible wrapper for Claude Code SDK with local tools support.
    This enables file operations, bash commands, and other Claude Code features.
    """
    
    def __init__(self, **default_options):
        """
        Initialize the adapter with default options.
        
        Args:
            **default_options: Default options for ClaudeCodeOptions
                              (cwd, add_dirs, allowed_tools, etc.)
        """
        self.default_options = default_options
        self.chat = self.Chat(self)
    
    class Chat:
        def __init__(self, outer):
            self.completions = ClaudeCodeOpenAIAdapter.Completions(outer)
    
    class Completions:
        def __init__(self, outer):
            self.outer = outer
        
        def create(
            self,
            model: str,
            messages: List[Dict[str, str]],
            max_turns: int = 1,
            allowed_tools: Optional[List[str]] = None,
            permission_mode: Optional[str] = None,
            stream: bool = False,
            cwd: Optional[str] = None,
            add_dirs: Optional[List[str]] = None,
            **kwargs
        ):
            """
            Create a chat completion with Claude Code capabilities.
            
            Args:
                model: Claude model name
                messages: OpenAI-style messages
                max_turns: Maximum conversation turns for Claude Code
                allowed_tools: List of allowed tools (Read, Write, Bash, etc.)
                permission_mode: Permission mode (acceptEdits, plan, default)
                stream: Whether to stream the response
                cwd: Working directory for Claude Code
                add_dirs: Additional directories to include in context
                **kwargs: Additional parameters
            
            Returns:
                OpenAI-style response object
            """
            try:
                from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
            except ImportError:
                raise ImportError(
                    "Please install claude-code-sdk: pip install claude-code-sdk"
                )
            
            # Extract system prompts
            system_messages = []
            conversation = []
            
            for msg in messages:
                if msg["role"] in ("system", "developer"):
                    system_messages.append(msg["content"])
                elif msg["role"] == "user":
                    conversation.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    conversation.append(f"Assistant: {msg['content']}")
            
            system_prompt = "\n".join(system_messages) if system_messages else None
            prompt = "\n".join(conversation) if conversation else messages[-1]["content"]
            
            async def run():
                options = ClaudeCodeOptions(
                    model=model,
                    append_system_prompt=system_prompt,
                    max_turns=max_turns,
                    allowed_tools=allowed_tools,
                    permission_mode=permission_mode,
                    cwd=cwd or self.outer.default_options.get("cwd"),
                    add_dirs=add_dirs or self.outer.default_options.get("add_dirs"),
                    **{k: v for k, v in self.outer.default_options.items() 
                       if k not in ["cwd", "add_dirs"]}
                )
                
                async with ClaudeSDKClient(options=options) as client:
                    await client.query(prompt)
                    
                    if stream:
                        # Return an async generator for streaming
                        async def stream_generator():
                            async for msg in client.receive_response():
                                if hasattr(msg, "content"):
                                    for block in msg.content:
                                        if hasattr(block, "text"):
                                            yield SimpleNamespace(
                                                choices=[SimpleNamespace(
                                                    delta=SimpleNamespace(
                                                        content=block.text
                                                    ),
                                                    index=0
                                                )]
                                            )
                        return stream_generator()
                    else:
                        # Collect all text for non-streaming response
                        chunks = []
                        async for msg in client.receive_response():
                            if hasattr(msg, "content"):
                                for block in msg.content:
                                    if hasattr(block, "text"):
                                        chunks.append(block.text)
                        
                        return SimpleNamespace(
                            choices=[SimpleNamespace(
                                index=0,
                                message=SimpleNamespace(
                                    role="assistant",
                                    content="".join(chunks)
                                ),
                                finish_reason="stop"
                            )],
                            model=model,
                            usage=SimpleNamespace(
                                prompt_tokens=0,
                                completion_tokens=0,
                                total_tokens=0
                            )
                        )
            
            # Run the async function
            if stream:
                return asyncio.run(run())
            else:
                return asyncio.run(run())
        
        async def acreate(self, **kwargs):
            """Async version of create method"""
            # Similar implementation but without asyncio.run wrapper
            pass


# ============================================================================
# APPROACH 3: CLI-based Wrapper (Subprocess)
# ============================================================================

class ClaudeCodeCLIWrapper:
    """
    Wrapper that calls Claude Code CLI directly via subprocess.
    Requires 'claude' CLI to be installed and configured.
    """
    
    def __init__(self, default_cwd: Optional[str] = None):
        """
        Initialize CLI wrapper.
        
        Args:
            default_cwd: Default working directory for Claude Code
        """
        self.default_cwd = default_cwd
        self._check_cli_available()
    
    def _check_cli_available(self):
        """Check if Claude CLI is available"""
        try:
            subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                check=False
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Please install: npm install -g @anthropic-ai/claude-code"
            )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "sonnet",
        max_turns: int = 1,
        cwd: Optional[str] = None,
        output_format: str = "json",
        allowed_tools: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Claude CLI.
        
        Args:
            messages: OpenAI-style messages
            model: Model shorthand (sonnet, opus, haiku)
            max_turns: Maximum conversation turns
            cwd: Working directory
            output_format: Output format (json, stream-json, text)
            allowed_tools: List of allowed tools
            stream: Whether to stream response
            **kwargs: Additional CLI arguments
        
        Returns:
            Response dictionary
        """
        # Build system prompt
        system_messages = [
            m["content"] for m in messages 
            if m["role"] in ("system", "developer")
        ]
        system_prompt = "\n".join(system_messages) if system_messages else None
        
        # Build conversation
        conversation = []
        for msg in messages:
            if msg["role"] == "user":
                conversation.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                conversation.append(f"Assistant: {msg['content']}")
        
        prompt = "\n".join(conversation) if conversation else messages[-1]["content"]
        
        # Build command - prompt must come right after -p
        cmd = [
            "claude",
            "-p",  # Print mode (non-interactive)
            prompt,  # Prompt must be right after -p
            "--output-format", "stream-json" if stream else output_format,
            "--max-turns", str(max_turns),
            "--model", model
        ]
        
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])
        
        if allowed_tools:
            # Use --allowed-tools with comma-separated list
            cmd.extend(["--allowed-tools", ",".join(allowed_tools)])
        
        # Execute command
        if stream:
            return self._stream_response(cmd, cwd or self.default_cwd)
        else:
            return self._run_command(cmd, cwd or self.default_cwd)
    
    def _run_command(self, cmd: List[str], cwd: Optional[str]) -> Dict[str, Any]:
        """Run command and return parsed response"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON output
            if "--output-format" in cmd and "json" in cmd[cmd.index("--output-format") + 1]:
                payload = json.loads(result.stdout)
                
                # Extract text content
                text = (
                    payload.get("result") or
                    "".join(b.get("text", "") for b in payload.get("content", [])) or
                    payload.get("text", "") or
                    ""
                )
                
                return {
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": text
                        },
                        "finish_reason": "stop"
                    }],
                    "model": cmd[cmd.index("--model") + 1] if "--model" in cmd else "unknown",
                    "raw_response": payload
                }
            else:
                return {
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result.stdout
                        },
                        "finish_reason": "stop"
                    }]
                }
        except subprocess.CalledProcessError as e:
            return {
                "error": {
                    "message": e.stderr,
                    "type": "cli_error",
                    "code": e.returncode
                }
            }
    
    def _stream_response(self, cmd: List[str], cwd: Optional[str]):
        """Stream response from CLI"""
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        def generator():
            for line in process.stdout:
                if line.strip():
                    try:
                        event = json.loads(line)
                        if "text" in event:
                            yield {
                                "choices": [{
                                    "delta": {"content": event["text"]},
                                    "index": 0
                                }]
                            }
                    except json.JSONDecodeError:
                        # Skip non-JSON lines
                        pass
            
            process.wait()
            if process.returncode != 0:
                stderr = process.stderr.read()
                yield {
                    "error": {
                        "message": stderr,
                        "type": "cli_error",
                        "code": process.returncode
                    }
                }
        
        return generator()


# ============================================================================
# Unified Interface
# ============================================================================

class ClaudeOpenAIUnified:
    """
    Unified interface that can use any of the three approaches.
    """
    
    def __init__(self, backend: str = "anthropic", **kwargs):
        """
        Initialize unified wrapper.
        
        Args:
            backend: Which backend to use ('anthropic', 'sdk', 'cli')
            **kwargs: Backend-specific configuration
        """
        self.backend = backend
        
        if backend == "anthropic":
            self.client = AnthropicOpenAIWrapper(**kwargs)
        elif backend == "sdk":
            self.client = ClaudeCodeOpenAIAdapter(**kwargs)
        elif backend == "cli":
            self.client = ClaudeCodeCLIWrapper(**kwargs)
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def create_completion(self, messages: List[Dict[str, str]], **kwargs):
        """Create a completion using the configured backend"""
        if self.backend == "anthropic":
            return self.client.chat_completion(messages, **kwargs)
        elif self.backend == "sdk":
            return self.client.chat.completions.create(
                messages=messages, **kwargs
            )
        elif self.backend == "cli":
            return self.client.chat_completion(messages, **kwargs)


# ============================================================================
# Helper Functions
# ============================================================================

def format_openai_response(text: str, model: str = "claude") -> Dict[str, Any]:
    """
    Format a simple text response in OpenAI response format.
    """
    return {
        "id": f"chatcmpl-{os.urandom(8).hex()}",
        "object": "chat.completion",
        "created": int(asyncio.get_event_loop().time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


def extract_messages_by_role(
    messages: List[Dict[str, str]]
) -> Dict[str, List[str]]:
    """
    Extract messages grouped by role.
    
    Returns:
        Dict with keys 'system', 'user', 'assistant' containing lists of messages
    """
    result = {"system": [], "user": [], "assistant": []}
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role in ("system", "developer"):
            result["system"].append(content)
        elif role == "user":
            result["user"].append(content)
        elif role == "assistant":
            result["assistant"].append(content)
    
    return result