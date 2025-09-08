# Quick Start Guide - LLM Surveying LLMs

Get the system running in 5 minutes!

## Prerequisites

- Python 3.9+
- 8GB RAM
- 5GB disk space

## Option 1: Fastest Demo (No API Required)

```bash
# 1. Clone and setup
git clone https://github.com/agents4science/llm-surveying-llms.git
cd llm-surveying-llms

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run demo with cached results
python scripts/demos/simplified_demo.py
```

**Output**: See the 26.1% improvement demonstrated with pre-computed results

## Option 2: Direct Python Setup

```bash
# 1. Install requirements
pip install -r requirements.txt

# 2. Set up environment
export ANTHROPIC_API_KEY="your-key"
export SCIMCP_DATA_PATH="/path/to/papers.parquet"

# 3. Access API
curl http://localhost:8000/health
```

## Option 3: Full Installation

```bash
# 1. Clone repository
git clone https://github.com/agents4science/llm-surveying-llms.git
cd llm-surveying-llms

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export ANTHROPIC_API_KEY="your-api-key"  # Optional for demos
export SCIMCP_DATA_PATH="path/to/papers.parquet"  # Optional

# 5. Run quick validation
python scripts/validation/FINAL_VALIDATION.py
```

## Quick Test - Verify Installation

```python
# test_install.py
import sys
sys.path.insert(0, '.')

from src.baselines.autosurvey import AutoSurveyBaseline
from src.our_system.iterative import IterativeSurveySystem
from src.evaluation.metrics import SurveyEvaluator

print("✅ Installation successful!")
print("Systems ready:")
print("  • AutoSurvey Baseline")
print("  • Global Iterative System")
print("  • Evaluation Framework")
```

## Run Jupyter Tutorial

```bash
# Start Jupyter
jupyter lab

# Open in browser
# Navigate to: notebooks/05_quick_start_tutorial.ipynb
# Run all cells (Runtime → Run all)
```

**Time**: <10 minutes to see full demonstration

## API Server Quick Start

```bash
# 1. Start server
uvicorn src.api.main:app --reload

# 2. View interactive docs
open http://localhost:8000/docs

# 3. Test endpoint
curl -X GET http://localhost:8000/health
```

## Sample Survey Generation

```python
from src.our_system.iterative import IterativeSurveySystem

# Initialize system
system = IterativeSurveySystem(max_iterations=3)

# Sample papers
papers = [
    {"title": "Attention Is All You Need", 
     "abstract": "...", "authors": ["Vaswani et al."]},
    {"title": "BERT: Pre-training of Deep Bidirectional Transformers",
     "abstract": "...", "authors": ["Devlin et al."]}
]

# Generate survey (API key required for real generation)
topic = "Transformer Models"
# survey = system.generate_survey(papers, topic)
print("System initialized successfully!")
```

## Troubleshooting

### Import Errors
```bash
# Ensure you're in project root
pwd  # Should show: .../llm-surveying-llms

# Add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Memory Issues
```bash
# Reduce batch size in experiments
python scripts/experiments/run_50_paper_experiment.py --batch-size 10
```

### API Key Issues
```bash
# Demo mode works without API key
python scripts/demos/simplified_demo.py --use-cache
```


## Performance Validation

To see the validated 26.1% improvement:

```bash
# Quick validation (uses cached results)
python scripts/experiments/practical_validation.py

# Full validation (requires API key, ~10 min)
python scripts/experiments/run_50_paper_experiment.py
```

## Key Files to Explore

1. **Core Innovation**: `src/our_system/iterative.py`
2. **Baseline**: `src/baselines/autosurvey.py`
3. **Quick Demo**: `scripts/demos/simplified_demo.py`
4. **Tutorial**: `notebooks/05_quick_start_tutorial.ipynb`
5. **API**: `src/api/main.py`

## Expected Results

When running the demo, you should see:

```
AutoSurvey Baseline:     3.26/5.00
AutoSurvey + LCE:        3.41/5.00 (+4.6%)
Our Global System:       4.11/5.00 (+26.1%) ✅
Convergence:            3-4 iterations
Statistical p-value:    < 0.001
```

## Questions?

- Check `EXECUTIVE_SUMMARY.md` for algorithm details
- See `paper_draft.md` for full methodology
- Review `notebooks/` for interactive examples

---

**Ready to see 26.1% improvement in action? Start with Option 1 above!**