# Scripts Organization

## Directory Structure

### `/demos/`
Demo scripts for quick testing and demonstration:
- `simplified_demo.py` - Basic system demonstration

### `/experiments/`
Experimental validation scripts:
- `balanced_experiment.py` - Balanced testing
- `run_50_paper_experiment.py` - Large-scale validation  
- `run_real_experiment.py` - Real data experiments
- `practical_validation.py` - Practical system validation

### `/validation/`
Testing and validation scripts:
- `test_*.py` - Various component tests
- `validate_real_implementation.py` - Implementation validation

### Root Level
- `create_paper_figures.py` - Generate publication figures
- `create_submission_package.py` - Build submission ZIP

## Usage Examples

```bash
# Run demonstration
python scripts/demos/simplified_demo.py

# Run validation
python scripts/experiments/practical_validation.py

# Create submission
python scripts/create_submission_package.py
```

## Cleanup Note
Scripts reorganized from project root on 2025-09-07 for cleaner structure.
