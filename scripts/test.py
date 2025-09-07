from claude_openai_wrapper import ClaudeCodeCLIWrapper

wrapper = ClaudeCodeCLIWrapper()
response = wrapper.chat_completion(
    messages=[{"role": "user", "content": "How are you"}],
    model="sonnet",  # or "sonnet", "opus"
    allowed_tools=["Read", "Write", "Bash"],  # Enable tools
    max_turns=3  # Allow multiple turns for complex tasks
)
print(response["choices"][0]["message"]["content"].strip())