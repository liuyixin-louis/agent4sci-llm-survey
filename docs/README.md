# LLM Surveying LLMs - Project Documentation

## Overview

This project explores automated scientific survey generation using Large Language Models, focusing on comparing different approaches for generating comprehensive literature reviews.

## Current Status: Research Prototype

This is a research prototype exploring the concept of using LLMs to generate scientific surveys. The project includes:

- **Conceptual Framework**: Design for global vs local iteration approaches
- **Baseline Implementation**: Basic AutoSurvey reference implementation
- **Data Infrastructure**: Paper loading and indexing capabilities  
- **Evaluation Framework**: Metrics for comparing survey quality
- **Experimental Components**: Tools for running comparative studies

## What's Actually Implemented

### ✅ Working Components
- Data loader for scientific papers (sciMCP integration)
- BM25-based paper search and retrieval
- Claude API wrapper with caching
- Basic AutoSurvey baseline implementation
- Evaluation metrics framework
- Experimental runner scripts
- FastAPI web interface (basic)

### 🚧 In Development
- Global verification-driven iteration system
- Comprehensive baseline comparisons
- Production-scale experiments
- Complete evaluation studies

### ❌ Not Yet Implemented
- Validated performance improvements
- Complete experimental validation
- Production deployment readiness
- Comprehensive test coverage

## Documentation Structure

- [`setup/`](./setup/) - Installation and configuration
- [`architecture/`](./architecture/) - System design and components
- [`development/`](./development/) - Development notes and progress
- [`results/`](./results/) - Experimental findings and analysis

## Quick Start

See [`setup/installation.md`](./setup/installation.md) for setup instructions.

## Contributing

This is a research project. See [`development/status.md`](./development/status.md) for current development status.