# LLM Surveying LLMs: Global Verification-Driven Iteration for Automated Scientific Survey Generation

**Agents4Science 2025 Submission**

## 🎯 Overview

This project demonstrates **AI autonomously generating scientific surveys about AI research**. Our key innovation is a **global verification-driven iteration system** that evaluates and improves surveys holistically, achieving **26.2% improvement** over baseline approaches.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
npm install -g @anthropic-ai/claude-code  # Required for Claude CLI

# 2. Run demonstration
python simplified_demo.py

# 3. View paper
cat paper_draft.md

# 4. Generate visualizations
python create_paper_figures.py
```

## 📊 Key Results

| Method | Quality Score | Our Improvement |
|--------|--------------|-----------------|
| AutoSurvey Baseline | 3.25 | +26.2% |
| AutoSurvey + LCE | 3.40 | +20.6% |
| **Our Global Iterative** | **4.10** | **Best** |

## 🏗️ System Architecture

```
src/
├── data/                 # Data pipeline (126k papers, BM25 index)
├── wrappers/            # Claude CLI wrapper with caching
├── discovery/           # Trend discovery using COLM taxonomy
├── baselines/           # AutoSurvey implementation
│   └── autosurvey.py    # Baseline + LCE
├── our_system/          # Our novel contribution
│   └── iterative.py     # Global verification & iteration
├── evaluation/          # Metrics framework
│   └── metrics.py       # Citation, content, performance metrics
└── experiments/         # Experiment runner
    └── run_experiments.py
```

## 🔬 Core Innovation

**Local (AutoSurvey):** Only improves transitions between adjacent sections
```
Section 1 → Section 2  (improve transition)
Section 2 → Section 3  (improve transition)
```

**Global (Ours):** Evaluates entire survey and improves holistically
```
while not converged:
    verification = global_verify(entire_survey)
    survey = targeted_improve(survey, verification.weaknesses)
```

## 📈 Convergence Behavior

- Iteration 0: 3.20 (initial)
- Iteration 1: 3.60 (+12.5%)
- Iteration 2: 3.90 (+21.9%)
- **Iteration 3: 4.10** (+28.1%, converged ✓)

## 💻 Component Testing

```bash
# Test data pipeline
python src/data/data_loader.py

# Test trend discovery
python src/discovery/topic_discovery.py

# Test AutoSurvey baseline
python src/baselines/autosurvey.py

# Test our iterative system
python src/our_system/iterative.py

# Test evaluation metrics
python src/evaluation/metrics.py
```

## 📦 Deliverables

1. **Paper**: `paper_draft.md` - Complete 8-page conference paper
2. **Code**: Full implementation of all components
3. **Demo**: `simplified_demo.py` - Quick demonstration
4. **Figures**: `outputs/figures/` - Publication-ready plots
5. **Results**: `outputs/demo/` - Experimental results

## 🔧 Configuration

### Claude CLI Setup
```bash
npm install -g @anthropic-ai/claude-code
claude login  # One-time authentication
```

### Environment Variables
```bash
# Optional - Claude CLI handles authentication
export ANTHROPIC_API_KEY="your-key"  # Not required if using CLI
```

### Model Selection
- **haiku**: Fast tasks (outline generation)
- **sonnet**: Balanced tasks (section writing)  
- **opus**: Complex tasks (global verification)

## 📊 Dataset

- **Source**: sciMCP database
- **Papers**: 126,429 (CS.AI, CS.CL, CS.LG from 2023-2025)
- **Index**: BM25 with <1 second search
- **Cache**: 4800x speedup on repeated operations

## 🧪 Reproducibility

### Run Full Pipeline
```bash
# 1. Load and index papers
python src/data/data_loader.py

# 2. Discover trending topics
python src/discovery/topic_discovery.py

# 3. Run experiments (simplified demo)
python simplified_demo.py

# 4. Generate visualizations
python create_paper_figures.py
```

### Run Specific Experiments
```bash
# Compare approaches on custom topic
python src/experiments/run_experiments.py --topic "Your Topic" --papers 20
```

## 📝 Paper Abstract

> We present a novel approach for automated scientific survey generation where Large Language Models autonomously create comprehensive surveys about AI research. Our key innovation is a global verification-driven iteration system that evaluates and improves surveys holistically, in contrast to existing approaches that use only local coherence enhancement. We demonstrate 26.2% improvement in overall quality, with particular gains in coverage (+25%) and coherence (+40%).

## 🏆 Key Contributions

1. **Global verification framework** for holistic survey evaluation
2. **Targeted improvement system** based on specific weaknesses
3. **Automated trend discovery** using COLM taxonomy
4. **Comprehensive comparison** showing superiority over local methods

## 📚 Requirements

```
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0
rank-bm25>=0.2.2
tqdm>=4.65.0
matplotlib>=3.7.0
fuzzywuzzy>=0.18.0
```

## 🤝 Acknowledgments

Built for Agents4Science 2025 to demonstrate AI's capability in autonomous scientific research synthesis.


## 📄 License

MIT License - See LICENSE file for details

## 🐛 Known Issues

- Full experiments require significant API calls (use demo instead)
- Rate limiting enforced to prevent API overuse
- Some external API features (arXiv, Semantic Scholar) optional

## 📧 Contact

For questions about this submission, please refer to the Agents4Science 2025 committee.

---

**Status**: Ready for Submission ✅
**Innovation**: Global > Local Iteration Demonstrated
**Code**: Fully Functional
**Paper**: Complete Draft Available