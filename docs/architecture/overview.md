# System Architecture

## High-Level Design

The project implements a modular architecture for comparing different approaches to automated survey generation.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Generation      │    │  Evaluation     │
│                 │    │  Approaches      │    │  Framework      │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Paper Loading │    │ • AutoSurvey     │    │ • Quality       │
│ • BM25 Index    │───▶│ • Local Enhance  │───▶│   Metrics       │
│ • Search        │    │ • Global Iter    │    │ • Comparison    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### Data Management (`src/data/`)
- **data_loader.py**: Interface to sciMCP database
- **Paper indexing**: BM25-based search and retrieval
- **Caching**: API call and data operation caching

### Generation Approaches (`src/baselines/`, `src/our_system/`)
- **AutoSurvey**: Baseline implementation
- **Local Enhancement**: Section-by-section improvement
- **Global Iteration**: Holistic survey improvement (in development)

### Evaluation (`src/evaluation/`)
- **metrics.py**: Survey quality assessment
- **Comparison framework**: Side-by-side evaluation

### API Layer (`src/api/`)
- **FastAPI server**: Web interface
- **Real-time updates**: WebSocket support
- **Job management**: Async survey generation

## Research Comparison Framework

The core research question compares:

**Local Approach (AutoSurvey + LCE):**
```
Section 1 → improve transition → Section 2 → improve transition → Section 3
```

**Global Approach (Our System):**
```
while not converged:
    global_assessment = evaluate_entire_survey()
    targeted_improvements = identify_weaknesses()
    survey = improve_globally(survey, targeted_improvements)
```

## Current Implementation Status

- **Data Layer**: ✅ Functional
- **AutoSurvey Baseline**: ✅ Basic implementation
- **Local Enhancement**: ✅ Simple version
- **Global Iteration**: 🚧 Framework exists, needs completion
- **Evaluation**: ✅ Basic metrics, 🚧 comprehensive validation
- **API**: ✅ Basic functionality

## Key Design Decisions

1. **Modular Architecture**: Each approach is isolated for fair comparison
2. **Caching Strategy**: Aggressive caching to reduce API costs during development
3. **Evaluation First**: Metrics framework built before optimization
4. **Real Data**: Uses actual scientific papers, not synthetic data