# LLM Surveying LLMs: Research Prototype

> **Status**: Early research prototype exploring automated scientific survey generation

## What This Project Actually Is

This is a research exploration into using Large Language Models to automatically generate scientific literature surveys. The project compares different approaches for generating comprehensive reviews of AI research literature.

### Current Implementation Status

**✅ Working Components:**
- Data loading and paper indexing (sciMCP integration)
- BM25-based paper search and retrieval
- Claude API wrapper with caching
- Basic AutoSurvey baseline implementation
- Evaluation metrics framework
- FastAPI web interface (basic functionality)

**🚧 In Development:**
- Global vs local iteration comparison
- Comprehensive experimental validation
- Performance benchmarking

**❌ Not Implemented:**
- Validated performance claims
- Production deployment
- Complete test coverage

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test basic functionality (no API keys needed)
python -m src.data.data_loader  # Test data loading
python -m src.evaluation.metrics  # Test evaluation framework

# Run basic API server
python -m src.api.main
```

## Directory Structure

```
src/
├── data/           # Paper loading and indexing
├── wrappers/       # Claude API integration  
├── baselines/      # AutoSurvey implementation
├── our_system/     # Global iteration approach
├── evaluation/     # Metrics and comparison
├── experiments/    # Experimental runners
└── api/           # Web interface

docs/              # Project documentation
agents4science_submission/  # Agents4Science submission package
```

## Documentation

See [`docs/`](./docs/) for detailed documentation including:
- [Installation guide](./docs/setup/installation.md)
- [Architecture overview](./docs/architecture/)
- [Development status](./docs/development/)

## Research Goals

The project explores whether **global verification-driven iteration** can improve automated survey generation compared to existing **local coherence enhancement** approaches. This is currently a research question, not a validated result.

## Contributing

This is an active research project. See [development status](./docs/development/status.md) for current work.

## License

MIT License - see LICENSE file for details.

---

*This project is part of ongoing research into AI-assisted scientific literature review. Results and performance claims should be considered experimental and unvalidated unless otherwise noted.*