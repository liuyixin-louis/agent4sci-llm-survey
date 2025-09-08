# Installation Guide

## Prerequisites

- Python 3.9+
- Claude CLI (optional but recommended)
- Git

## Basic Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent4sci-llm-survey
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if available
   ```

## Optional: Claude CLI Setup

For full functionality with the Claude wrapper:

```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Authenticate (one-time)
claude login
```

## Verify Installation

```bash
# Test data loading (uses cached data)
python -c "from src.data.data_loader import SciMCPDataLoader; loader = SciMCPDataLoader(); print('Data loader works')"

# Test basic API wrapper
python -c "from src.wrappers.claude_wrapper import ClaudeWrapper; print('Claude wrapper imported')"
```

## Configuration

The project can work in several modes:

- **Demo mode**: Uses cached/simulated results (no API calls)
- **Development mode**: Limited API calls for testing
- **Full mode**: Complete experiments (requires API keys)

Most functionality works without API keys for exploration and development.