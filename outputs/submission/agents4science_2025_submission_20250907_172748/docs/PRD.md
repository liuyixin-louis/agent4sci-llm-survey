# Product Requirements Document (PRD)
## LLM Surveying LLMs: An Agentic Pipeline for Autonomous Scientific Paper Surveying

### Executive Summary
**Project Title**: LLM Surveying LLMs: An Agentic Pipeline for Autonomous Scientific Paper Surveying  
**Conference**: Agents4Science 2025 (Deadline: September 15, 2025)  
**Timeline**: 3 days (September 7-9, 2025)  
**Core Innovation**: Global verification-driven iteration for survey generation, demonstrating AI's capability to autonomously study and improve surveys about AI research

---

## 1. Project Vision & Goals

### 1.1 Vision
Create the first self-evolving survey generation system where LLM agents can:
- Autonomously discover research trends and gaps in AI literature
- Generate comprehensive literature surveys with high citation accuracy
- Iteratively improve quality through global verification
- Converge to publication-quality output

### 1.2 Core Value Propositions
1. **Meta-Recursive Nature**: LLMs studying LLM research creates unique insights
2. **Self-Improvement**: Dynamic iteration until quality threshold reached
3. **Global Optimization**: Holistic survey improvement vs. local coherence only
4. **Transparency**: All decisions traceable and reproducible

### 1.3 Success Metrics
- **Minimum**: Generate surveys with quality score ≥4.0/5, convergence within 10 iterations
- **Target**: 5-10% quality improvement through iteration, discover novel insights
- **Stretch**: 15% improvement over baselines, identify emerging trends

---

## 2. Technical Architecture

### 2.1 System Components

#### Data Layer
- **sciMCP Database**: 474k papers from `/data/yixin/workspace/sciMCP/data/all_papers.parquet`
- **arXiv API**: Real-time access to latest papers (last 30 days)
- **Semantic Scholar API**: Additional paper metadata and abstracts
- **PASA Dataset**: Queries and answers for evaluation
- **BM25 Index**: Fast CPU-based retrieval (no GPU needed)

#### Processing Pipeline
1. **Automated Trend Discovery**
   - Hierarchical topic mining from broad keyword (e.g., "LLM")
   - COLM taxonomy-based categorization (18 categories)
   - Multi-source paper aggregation (sciMCP + arXiv + Semantic Scholar)
   - Temporal trend detection based on publication velocity

2. **Discovery & Planning**
   - Topic clustering and trend detection
   - Hierarchical outline generation
   - Strategy selection (breadth-first, depth-first, chronological)

2. **Generation**
   - Initial survey generation
   - Section writing with RAG
   - Citation management

3. **Verification & Improvement**
   - Global quality verification (multi-criteria)
   - Targeted improvement generation
   - Convergence monitoring
   - Checkpoint management

### 2.2 Claude CLI Integration

Based on `/data2/yixin/workspace/agent4sci-llm-survey/scripts/README.md`:

```python
from claude_openai_wrapper import ClaudeCodeCLIWrapper

class SurveyGenerator:
    def __init__(self):
        self.wrapper = ClaudeCodeCLIWrapper(
            default_cwd="/data2/yixin/workspace/agent4sci-llm-survey"
        )
    
    # Model selection strategy:
    # - haiku: Fast tasks (section writing, simple queries)
    # - sonnet: Balanced tasks (outline, refinement, evaluation)
    # - opus: Complex tasks (verification, deep analysis, improvement)
```

### 2.3 Automated Trend Discovery System

#### Hierarchical Topic Mining
```python
class HierarchicalTopicDiscovery:
    """
    Discover trending subtopics from broad keywords using COLM taxonomy
    """
    def __init__(self):
        # COLM-inspired 18 categories
        self.taxonomy = {
            "alignment": ["RLHF", "DPO", "constitutional AI", "instruction-tuning"],
            "data": ["synthetic data", "data curation", "pre-training data"],
            "evaluation": ["benchmarks", "metrics", "human evaluation"],
            "safety": ["jailbreaking", "hallucination", "adversarial attacks"],
            "efficiency": ["quantization", "distillation", "MoE", "pruning"],
            "inference": ["chain-of-thought", "reasoning", "tool use"],
            "multimodal": ["vision-language", "audio", "video understanding"],
            "applications": ["code generation", "science", "medicine", "education"],
            # ... (18 total categories)
        }
    
    def discover_trends(self, keyword="LLM", lookback_days=30):
        # Step 1: Aggregate papers from multiple sources
        papers = self.get_papers_from_sources(keyword, lookback_days)
        
        # Step 2: Categorize using COLM taxonomy
        categorized = self.categorize_papers(papers)
        
        # Step 3: Identify trends based on temporal patterns
        trends = self.detect_temporal_trends(categorized)
        
        return trends
```

#### Multi-Source Paper Aggregation
```python
def get_papers_from_sources(self, keyword, lookback_days):
    """
    Combine papers from local DB and APIs (no citation data needed)
    """
    # Local sciMCP database
    local_papers = self.query_local_db(keyword)
    
    # arXiv API (recent papers)
    arxiv_papers = self.fetch_arxiv_papers(keyword, lookback_days)
    
    # Semantic Scholar (abstracts only, no citations)
    s2_papers = self.fetch_s2_abstracts(keyword, lookback_days)
    
    # Merge and deduplicate by title similarity
    return self.merge_deduplicate(local_papers, arxiv_papers, s2_papers)
```

#### Temporal Trend Detection (Without Citations)
```python
def detect_temporal_trends(self, categorized_papers):
    """
    Find trends based on publication velocity and acceleration
    """
    trends = []
    
    for category, papers in categorized_papers.items():
        # Calculate publication frequency over time
        weekly_counts = self.calculate_weekly_counts(papers)
        
        # Compute velocity (first derivative)
        velocity = self.calculate_velocity(weekly_counts)
        
        # Compute acceleration (second derivative)
        acceleration = self.calculate_acceleration(weekly_counts)
        
        # LLM-based novelty detection
        novelty_score = self.assess_novelty_with_llm(papers)
        
        # Score based on temporal dynamics only
        trend_score = (
            velocity * 0.4 +           # Recent activity
            acceleration * 0.3 +       # Growing interest
            novelty_score * 0.3        # Novel concepts
        )
        
        if trend_score > threshold:
            trends.append({
                'category': category,
                'papers': papers,
                'velocity': velocity,
                'acceleration': acceleration,
                'score': trend_score
            })
    
    return sorted(trends, key=lambda x: x['score'], reverse=True)
```

### 2.4 Core Algorithms

#### AutoSurvey Baseline (Reproduction)
```python
class AutoSurveyBaseline:
    """
    Faithful reproduction of AutoSurvey approach
    - Chunk-based outline generation
    - Parallel section writing
    - Local Coherence Enhancement (LCE) - 2 passes
    - Citation verification
    """
    def generate(self, topic, papers, use_lce=True):
        # Stage 1: Generate outlines from chunks
        # Stage 2: Merge outlines
        # Stage 3: Write sections with RAG
        # Stage 4: LCE refinement (if enabled)
        # Stage 5: Citation verification
        pass
```

#### Our Innovation: Global Iterative System
```python
class IterativeSurveySystem:
    """
    Global verification-driven iteration
    - Multi-criteria evaluation
    - Dynamic iteration count (3-5 typical)
    - Targeted improvements
    - Convergence tracking
    """
    def generate(self, topic, papers, max_iterations=5):
        # Initial generation
        # Iterative improvement loop:
        #   - Global verification
        #   - Check convergence
        #   - Targeted improvement
        pass
```

---

## 3. Implementation Plan

### Day 1: Infrastructure & Baselines (8 hours)

#### Morning (4 hours)
1. **Data Setup** (1 hour)
   - Load sciMCP parquet (474k papers)
   - Filter for CS.AI, CS.CL, CS.LG papers (2023-2025)
   - Build BM25 index
   - Cache processed data

2. **Claude CLI Integration** (1 hour)
   - Set up ClaudeCodeCLIWrapper
   - Test haiku/sonnet/opus models
   - Implement rate limiting (3-5 sec delays)
   - Error handling

3. **AutoSurvey Baseline** (2 hours)
   - Chunk-based outline generation
   - Section writing with RAG
   - Basic pipeline test

#### Afternoon (4 hours)
4. **LCE Implementation** (1 hour)
   - Local coherence refinement
   - Two-pass system (odd/even sections)

5. **Our Iterative System** (2 hours)
   - Global verification system
   - Multi-criteria evaluation
   - Targeted improvement generation
   - Convergence detection

6. **Testing & Debugging** (1 hour)
   - Test on small topic subset
   - Verify all components work
   - Optimize performance

### Day 2: Experiments (8 hours)

#### Morning (4 hours)
**Automated Topic Discovery (Primary Plan)**
- Run trend discovery on "LLM" keyword
- Aggregate papers from sciMCP + arXiv API (last 30 days)
- Categorize using COLM taxonomy
- Select top 2 trending topics based on:
  - Publication velocity (papers/week)
  - Acceleration (growth rate)
  - Novelty score (LLM assessment)

**Fallback Option (if trend discovery takes >1 hour)**
- Use pre-defined topics:
  1. "LLM Agents and Tool Use" - Highly relevant to conference
  2. "In-context Learning" - Well-studied with good baselines
- These topics have sufficient papers in sciMCP database
- Can proceed immediately without API delays

**Run Baselines**
- Use discovered trending topics (or fallback topics)
- Systems to test:
  1. AutoSurvey without LCE
  2. AutoSurvey with LCE
- Collect all metrics

#### Afternoon (4 hours)
**Run Our System**
- Same discovered topics for comparison
- Max 5 iterations
- Track convergence at each iteration
- Save all intermediate results

**Evaluation**
- Citation quality (recall, precision)
- Content quality (coverage, structure, relevance)
- Time and resource usage
- Trend relevance (how well survey captures emerging themes)

### Day 3: Analysis & Paper Writing (8 hours)

#### Morning (4 hours)
1. **Results Analysis**
   - Convergence curves
   - Comparison tables
   - Statistical significance testing

2. **Visualizations**
   - Quality improvement graphs
   - Iteration convergence plots
   - Comparison charts

#### Afternoon (4 hours)
3. **Paper Writing**
   - Methodology section
   - Results presentation
   - Discussion of improvements
   - Abstract and conclusion

4. **Final Polish**
   - Format compliance check
   - Citation verification
   - Submission preparation

---

## 4. Experimental Design

### 4.1 Automated Topic Discovery and Selection

Instead of pre-defined topics, we will automatically discover trending subtopics:

```python
# Start with broad keyword
keyword = "LLM"

# Discover trending topics
discoverer = HierarchicalTopicDiscovery()
trends = discoverer.discover_trends(keyword, lookback_days=30)

# Select top 2 trends for experiments
selected_topics = trends[:2]

# Example discovered topics (will vary based on real-time data):
# 1. "safety:jailbreak_defense" - Papers on defending against prompt attacks
# 2. "efficiency:mixture_of_experts" - Papers on MoE architectures
# 3. "inference:test_time_compute" - Papers on inference-time scaling
```

#### COLM Taxonomy Categories (18 total)
1. **Alignment**: RLHF, DPO, constitutional AI, instruction-tuning
2. **Data**: synthetic data, data curation, pre-training data
3. **Evaluation**: benchmarks, metrics, human evaluation
4. **Safety**: jailbreaking, hallucination, adversarial attacks
5. **Science of LMs**: scaling laws, emergence, interpretability
6. **Efficiency**: quantization, distillation, MoE, pruning
7. **Engineering**: distributed training, hardware optimization
8. **Learning algorithms**: continual learning, meta-learning
9. **Inference**: reasoning, chain-of-thought, planning
10. **Human/Brain/Philosophy**: cognitive modeling, neuroscience
11. **Multilingual**: cross-lingual, low-resource languages
12. **Knowledge/World**: factuality, RAG, commonsense
13. **Multimodal**: vision-language, audio, video
14. **Interaction**: dialogue, multi-agent, collaboration
15. **Tools/Code**: code generation, API integration
16. **Applications**: science, medicine, education, legal
17. **Societal**: bias, fairness, misuse, ethics
18. **Emerging**: dynamically discovered new areas

### 4.2 Evaluation Metrics

#### Citation Quality (from AutoSurvey)
- **Recall**: % of claims supported by citations
- **Precision**: % of citations that are relevant
- Target: >80% recall, >75% precision

#### Content Quality (1-5 scale)
- **Coverage**: Comprehensiveness of topic treatment
- **Structure**: Logical organization and flow
- **Relevance**: Alignment with topic
- Target: >4.0 average score

### 4.3 Expected Results

| Method | Citation Recall | Citation Precision | Coverage | Structure | Relevance | Avg |
|--------|----------------|-------------------|----------|-----------|-----------|-----|
| AutoSurvey (no LCE) | ~78% | ~72% | 4.4 | 3.9 | 4.8 | 4.37 |
| AutoSurvey (with LCE) | ~82% | ~77% | 4.6 | 4.3 | 4.8 | 4.57 |
| **Our System** | **~84%** | **~78%** | **4.7** | **4.4** | **4.9** | **4.67** |

### 4.4 Ablation Studies (if time permits)
- Without global verification
- Without iterative improvement
- Different iteration counts (1, 3, 5)
- Different model combinations

---

## 5. Key Differentiators

### 5.1 Technical Innovations

| Aspect | AutoSurvey | Our System | Innovation |
|--------|------------|------------|------------|
| **Iteration Scope** | Local (adjacent sections) | Global (entire survey) | Holistic optimization |
| **Iteration Count** | Fixed (2 passes) | Dynamic (3-5 typical) | Convergence-based |
| **Evaluation Criteria** | Coherence only | Multi-criteria | Comprehensive quality |
| **Improvement Target** | Transitions | Identified weaknesses | Targeted refinement |
| **Model Strategy** | Single model | Multi-model (haiku/sonnet/opus) | Task-appropriate selection |

### 5.2 Practical Contributions
1. **Automated trend discovery** from broad keywords using COLM taxonomy
2. **Multi-source aggregation** (sciMCP + arXiv + Semantic Scholar)
3. **First convergence study** for survey generation
4. **Verification-driven improvement** framework
5. **Strategic model selection** for efficiency (haiku/sonnet/opus)
6. **Reproducible pipeline** using Claude CLI only

---

## 6. Risk Management

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Claude rate limits | High | High | 3-5 sec delays, response caching |
| Memory overflow | Medium | High | Chunk processing, streaming |
| Poor convergence | Low | High | Max iteration limit, fallback to best |
| Time overrun | Medium | Medium | Focus on 2 topics, pre-compute Day 1 |

### 6.2 Contingency Plans
- **If iterations too slow**: Reduce to 3 max iterations
- **If 2 topics too much**: Focus on 1 with thorough analysis
- **If Opus too expensive**: Use Sonnet for verification
- **If convergence fails**: Use best iteration as final

---

## 7. Resource Requirements

### 7.1 Data Resources
- sciMCP database (already available)
- PASA dataset (already available)
- No external API calls needed

### 7.2 Compute Resources
- CPU only (BM25 indexing)
- ~16GB RAM for data processing
- Claude CLI access (haiku/sonnet/opus)

### 7.3 Time Budget
- Day 1: 8 hours (infrastructure)
- Day 2: 8 hours (experiments)
- Day 3: 8 hours (analysis & writing)
- Buffer: Use overnight for long runs if needed

---

## 8. Deliverables

### 8.1 Code Deliverables
```
src/
├── wrappers/
│   └── claude_wrapper.py        # Claude CLI integration
├── baselines/
│   ├── autosurvey.py           # AutoSurvey reproduction
│   └── autosurvey_lce.py       # With LCE refinement
├── our_system/
│   ├── iterative.py            # Main iterative system
│   ├── verifier.py             # Global verification
│   └── improver.py             # Targeted improvement
├── evaluation/
│   ├── metrics.py              # Citation & content metrics
│   └── comparator.py           # Comparison framework
├── experiments/
│   ├── run_experiments.py      # Main experiment runner
│   └── analyze_results.py      # Result analysis
└── data/
    ├── processed_papers.pkl     # Cached processed data
    └── bm25_index.pkl          # Pre-built index
```

### 8.2 Paper Deliverables
- 8-page conference paper (Agents4Science format)
- All experimental results and data
- Reproducible code and instructions

### 8.3 Expected Outputs
```
outputs/
├── surveys/
│   ├── baseline_llm_agents.txt
│   ├── baseline_lce_llm_agents.txt
│   ├── iterative_llm_agents.txt
│   ├── baseline_icl.txt
│   ├── baseline_lce_icl.txt
│   └── iterative_icl.txt
├── metrics/
│   ├── comparison_table.csv
│   ├── convergence_data.json
│   └── ablation_results.json
└── figures/
    ├── convergence_plot.png
    ├── quality_comparison.png
    └── pipeline_diagram.png
```

---

## 9. Success Criteria

### 9.1 Minimum Viable Success (Must Have)
- [ ] AutoSurvey baseline implemented and working
- [ ] Our iterative system implemented and working
- [ ] At least 1 topic fully evaluated
- [ ] Show measurable improvement over baseline
- [ ] Paper draft completed

### 9.2 Target Success (Should Have)
- [ ] 2 topics fully evaluated
- [ ] 5-10% improvement in quality metrics
- [ ] Clear convergence demonstration
- [ ] Statistical significance shown
- [ ] Ablation study completed

### 9.3 Stretch Goals (Nice to Have)
- [ ] 3+ topics evaluated
- [ ] 15%+ improvement achieved
- [ ] Novel insights discovered
- [ ] Emerging trends identified
- [ ] Code released publicly

---

## 10. Paper Outline (8 pages)

### Structure
1. **Abstract** (0.5 page)
   - Problem statement
   - Our approach
   - Key results

2. **Introduction** (1 page)
   - Motivation (AI studying AI)
   - Challenges in survey generation
   - Our contributions

3. **Related Work** (0.5 page)
   - AutoSurvey
   - PASA
   - IMO25 iterative approaches

4. **Methodology** (2 pages)
   - System architecture
   - Iterative improvement framework
   - Verification system

5. **Experiments** (2 pages)
   - Setup and datasets
   - Baseline comparisons
   - Ablation studies

6. **Results** (1.5 pages)
   - Comparison tables
   - Convergence analysis
   - Statistical significance

7. **Discussion** (1 page)
   - When iteration helps most
   - Limitations
   - Future work

8. **Conclusion** (0.5 page)
   - Summary of contributions
   - Impact and implications

---

## Appendix A: Technical Details

### A.1 Prompt Templates

#### Outline Generation (Sonnet)
```python
OUTLINE_PROMPT = """
You are an expert survey writer. Generate a comprehensive outline for a survey on {topic}.
Include 6-8 main sections with descriptions.
Papers: {papers[:30]}
"""
```

#### Section Writing (Haiku)
```python
SECTION_PROMPT = """
Write section "{section_name}" for a survey on {topic}.
Requirements: 500-700 words, include [Author, Year] citations, academic tone.
Relevant papers: {papers}
"""
```

#### Verification (Opus)
```python
VERIFY_PROMPT = """
Evaluate this survey section critically.
Score (1-5) on: Coverage, Structure, Citations, Coherence, Insights
Identify specific issues and improvements needed.
Survey: {survey}
"""
```

### A.2 Model Selection Strategy

| Task | Model | Rationale |
|------|-------|-----------|
| Outline generation | Sonnet | Balance of quality and speed |
| Section writing | Haiku | Fast, bulk content generation |
| Local refinement | Sonnet | Good quality for coherence |
| Global verification | Opus | Complex analysis needed |
| Improvement generation | Sonnet | Balance for targeted edits |
| Final evaluation | Opus | Most accurate assessment |

### A.3 Convergence Criteria

Survey is considered converged when:
1. Overall quality score > 4.5/5.0
2. Citation recall > 80%
3. No critical issues identified
4. Verified 3 times consistently

---

## Appendix B: Trend Discovery Implementation

### B.1 Simplified Approach (Without Citations)

```python
class SimplifiedTrendDiscovery:
    """
    Discover trends using temporal patterns only (no citation data)
    """
    
    def fetch_arxiv_papers(self, keyword, days=30):
        """
        Get recent papers from arXiv API
        """
        import arxiv
        
        search = arxiv.Search(
            query=f"ti:{keyword} OR abs:{keyword}",
            max_results=500,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        cutoff = datetime.now() - timedelta(days=days)
        
        for result in arxiv.Client().results(search):
            if result.published < cutoff:
                break
            papers.append({
                'title': result.title,
                'abstract': result.summary,
                'published': result.published,
                'categories': result.categories
            })
        
        return papers
    
    def calculate_trend_score(self, papers):
        """
        Score based on temporal dynamics only
        """
        # Group by week
        weekly = defaultdict(list)
        for p in papers:
            week = p['published'].isocalendar()[1]
            weekly[week].append(p)
        
        # Calculate velocity (papers per week growth)
        counts = [len(weekly[w]) for w in sorted(weekly.keys())]
        if len(counts) >= 2:
            velocity = (counts[-1] - counts[0]) / len(counts)
            acceleration = np.diff(counts).mean() if len(counts) > 2 else 0
        else:
            velocity = acceleration = 0
        
        return {
            'velocity': velocity,
            'acceleration': acceleration,
            'total_papers': len(papers),
            'recent_papers': len(weekly[max(weekly.keys())]) if weekly else 0
        }
    
    def categorize_with_llm(self, papers, taxonomy):
        """
        Use Claude to categorize papers into COLM taxonomy
        """
        prompt = f"""
        Categorize these papers into the following categories:
        {json.dumps(list(taxonomy.keys()))}
        
        Papers (showing title only):
        {[p['title'] for p in papers[:30]]}
        
        Return JSON mapping paper index to category.
        """
        
        response = self.claude.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="haiku"  # Fast model for categorization
        )
        
        return json.loads(response["choices"][0]["message"]["content"])
```

### B.2 Example Discovered Trends

Based on current research landscape (Sept 2025), the system might discover:

```json
{
  "discovered_trends": [
    {
      "name": "safety:constitutional_jailbreaking",
      "category": "safety",
      "metrics": {
        "velocity": 3.2,
        "acceleration": 0.8,
        "paper_count": 47,
        "recent_7_days": 12
      },
      "description": "Research on constitutional AI approaches to prevent jailbreaking"
    },
    {
      "name": "efficiency:speculative_decoding",
      "category": "efficiency",
      "metrics": {
        "velocity": 2.8,
        "acceleration": 0.6,
        "paper_count": 38,
        "recent_7_days": 9
      },
      "description": "Accelerating LLM inference through speculative execution"
    },
    {
      "name": "multimodal:video_understanding",
      "category": "multimodal",
      "metrics": {
        "velocity": 2.5,
        "acceleration": 0.5,
        "paper_count": 31,
        "recent_7_days": 8
      },
      "description": "Video-LLMs for temporal reasoning and understanding"
    }
  ]
}
```

## Appendix C: Reference Materials

### Key Papers
1. **AutoSurvey** (2406.10252): Baseline approach with LCE
2. **PASA** (2501.10120): Agent-based paper search
3. **IMO25** (2507.15855): Iterative verification approach
4. **LitSearch** (2407.18940): Literature search baselines

### Conference Requirements
- AI authorship required
- 8-page limit
- September 15 deadline
- Transparency about AI involvement

### Available Resources
- sciMCP: 474k papers database
- Claude CLI wrapper documentation
- Reference implementations
- Evaluation datasets

---

*Last Updated: September 7, 2025*