# Scripts Directory Structure

## Main Demo Scripts (For Submission)
- `demo_simple.py` - Simplified demonstration of the system (5-10 papers)
- `demo_full.py` - Full demonstration with 50+ papers
- `demo_trend_discovery.py` - Demonstrates automated trend discovery

## Validation Scripts
- `validation/validate_real_implementation.py` - Validates core system works
- `validation/FINAL_VALIDATION.py` - Final system validation
- `validation/test_*.py` - Component tests

## Experiments
- `experiments/run_real_experiment.py` - Real experiment with full dataset
- `experiments/run_50_paper_experiment.py` - Medium-scale experiment
- `experiments/balanced_experiment.py` - Balanced workload test
- `experiments/practical_validation.py` - Practical validation scenarios

## Utilities
- `create_submission_package.py` - Creates submission package
- `create_paper_figures.py` - Generates figures for paper
- `monitor.sh` - Monitors system resources during runs

## Legacy/Archive
- `claude_openai_wrapper.py` - Old wrapper (deprecated, use src/wrappers/claude_wrapper.py)
- `test_cli_wrapper.py` - Old tests (moved to tests/)
- `example_usage.py` - Old example (replaced by demo scripts)
- `simple_example.py` - Old simple example (replaced by demo_simple.py)

## Usage

### For Quick Demo (Submission)
```bash
python scripts/demo_simple.py
```

### For Full Validation
```bash
python scripts/validation/FINAL_VALIDATION.py
```

### For Creating Submission Package
```bash
python scripts/create_submission_package.py
```