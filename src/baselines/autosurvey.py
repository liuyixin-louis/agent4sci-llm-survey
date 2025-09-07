"""
AutoSurvey Baseline Implementation
Reproduces key features of AutoSurvey: chunk-based outline, parallel writing, and LCE.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import re

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.wrappers.claude_wrapper import EnhancedClaudeWrapper
from src.data.data_loader import SciMCPDataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SurveySection:
    """Represents a section of the survey."""
    title: str
    content: str
    section_number: int
    citations: List[str] = None
    
    def __post_init__(self) -> None:
        """Post-initialization to set default citations list if not provided."""
        if self.citations is None:
            self.citations = []


class AutoSurveyBaseline:
    """
    Baseline implementation of AutoSurvey approach.
    Key features:
    - Chunk-based outline generation
    - Parallel section writing
    - Citation injection
    """
    
    def __init__(
        self,
        claude_wrapper: Optional[EnhancedClaudeWrapper] = None,
        chunk_size: int = 40,
        max_workers: int = 3
    ):
        """
        Initialize AutoSurvey baseline.
        
        Args:
            claude_wrapper: Claude wrapper for LLM calls
            chunk_size: Number of papers per chunk for outline generation
            max_workers: Maximum parallel workers for section writing
        """
        self.claude_wrapper = claude_wrapper or EnhancedClaudeWrapper()
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        
    def generate_survey(
        self,
        papers: List[Dict],
        topic: str,
        target_sections: int = 6
    ) -> Dict:
        """
        Generate a survey using AutoSurvey approach.
        
        Args:
            papers: List of paper dictionaries
            topic: Survey topic
            target_sections: Target number of sections
            
        Returns:
            Dictionary with survey content and metadata
        """
        logger.info(f"Generating AutoSurvey baseline for '{topic}' with {len(papers)} papers")
        
        # Step 1: Generate outline using chunks
        outline = self._generate_chunked_outline(papers, topic, target_sections)
        logger.info(f"Generated outline with {len(outline)} sections")
        
        # Step 2: Write sections in parallel
        sections = self._write_sections_parallel(papers, topic, outline)
        
        # Step 3: Inject citations
        sections_with_citations = self._inject_citations(sections, papers)
        
        # Compile final survey
        survey = {
            'topic': topic,
            'outline': outline,
            'sections': sections_with_citations,
            'num_papers': len(papers),
            'timestamp': time.time()
        }
        
        return survey
        
    def _generate_chunked_outline(
        self,
        papers: List[Dict],
        topic: str,
        target_sections: int
    ) -> List[str]:
        """Generate outline by processing papers in chunks."""
        outlines = []
        
        # Process papers in chunks
        for i in range(0, len(papers), self.chunk_size):
            chunk = papers[i:i + self.chunk_size]
            chunk_outline = self._generate_chunk_outline(chunk, topic, target_sections)
            outlines.append(chunk_outline)
            
        # Merge outlines
        merged_outline = self._merge_outlines(outlines, target_sections)
        return merged_outline
        
    def _generate_chunk_outline(
        self,
        papers: List[Dict],
        topic: str,
        target_sections: int
    ) -> List[str]:
        """Generate outline for a single chunk of papers."""
        papers_summary = self._format_papers_for_prompt(papers[:10])  # Limit for context
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at creating survey outlines."
            },
            {
                "role": "user",
                "content": f"""Create an outline for a survey on "{topic}" based on these papers:

{papers_summary}

Generate {target_sections} section titles that cover the main themes.
Format: One section title per line, no numbering."""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="sonnet",
            use_cache=True
        )
        
        if "error" in response:
            logger.error(f"Error generating outline: {response['error']}")
            return self._default_outline(target_sections)
            
        # Parse outline
        content = response["choices"][0]["message"]["content"]
        outline = [line.strip() for line in content.split('\n') if line.strip()]
        return outline[:target_sections]
        
    def _merge_outlines(
        self,
        outlines: List[List[str]],
        target_sections: int
    ) -> List[str]:
        """Merge multiple chunk outlines into final outline."""
        if not outlines:
            return self._default_outline(target_sections)
            
        if len(outlines) == 1:
            return outlines[0]
            
        # Collect all section titles
        all_sections = []
        for outline in outlines:
            all_sections.extend(outline)
            
        # Use LLM to merge and deduplicate
        sections_text = "\n".join(f"- {s}" for s in all_sections)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at organizing survey sections."
            },
            {
                "role": "user",
                "content": f"""Merge these section titles into {target_sections} coherent sections:

{sections_text}

Output {target_sections} final section titles, one per line."""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="haiku",  # Fast model for merging
            use_cache=True
        )
        
        if "error" in response:
            # Fallback: take first target_sections unique titles
            seen = set()
            merged = []
            for title in all_sections:
                if title not in seen and len(merged) < target_sections:
                    seen.add(title)
                    merged.append(title)
            return merged
            
        content = response["choices"][0]["message"]["content"]
        merged = [line.strip() for line in content.split('\n') if line.strip()]
        return merged[:target_sections]
        
    def _write_sections_parallel(
        self,
        papers: List[Dict],
        topic: str,
        outline: List[str]
    ) -> List[SurveySection]:
        """Write survey sections in parallel."""
        sections = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all section writing tasks
            futures = {}
            for i, section_title in enumerate(outline):
                future = executor.submit(
                    self._write_section,
                    papers,
                    topic,
                    section_title,
                    i + 1
                )
                futures[future] = i
                
            # Collect results as they complete
            for future in as_completed(futures):
                section_idx = futures[future]
                try:
                    section = future.result()
                    sections.append((section_idx, section))
                except Exception as e:
                    logger.error(f"Error writing section {section_idx}: {e}")
                    # Create placeholder section
                    sections.append((section_idx, SurveySection(
                        title=outline[section_idx],
                        content=f"[Error generating section: {e}]",
                        section_number=section_idx + 1
                    )))
                    
        # Sort sections by index
        sections.sort(key=lambda x: x[0])
        return [s[1] for s in sections]
        
    def _write_section(
        self,
        papers: List[Dict],
        topic: str,
        section_title: str,
        section_number: int
    ) -> SurveySection:
        """Write a single survey section."""
        # Select relevant papers for this section (simplified)
        relevant_papers = self._select_relevant_papers(papers, section_title, limit=10)
        papers_context = self._format_papers_for_prompt(relevant_papers)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert academic writer creating survey sections."
            },
            {
                "role": "user",
                "content": f"""Write section "{section_title}" for a survey on "{topic}".

Relevant papers:
{papers_context}

Write 500-700 words covering key concepts, methods, and findings.
Include [Author, Year] style citations where appropriate."""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="sonnet",
            use_cache=False  # Don't cache section writing
        )
        
        if "error" in response:
            logger.error(f"Error writing section '{section_title}': {response['error']}")
            content = f"[Error generating section: {response['error']}]"
        else:
            content = response["choices"][0]["message"]["content"]
            
        return SurveySection(
            title=section_title,
            content=content,
            section_number=section_number
        )
        
    def _inject_citations(
        self,
        sections: List[SurveySection],
        papers: List[Dict]
    ) -> List[SurveySection]:
        """Inject proper citations into sections."""
        # Build citation index
        citation_map = {}
        for paper in papers:
            # Extract first author's last name
            authors = paper.get('authors')
            if authors is not None:
                # Handle various author formats
                try:
                    if hasattr(authors, '__len__') and len(authors) > 0:
                        first_author = authors[0] if isinstance(authors[0], str) else str(authors[0])
                        # Simple extraction of last name
                        author_name = first_author.split()[-1] if first_author else "Unknown"
                    else:
                        author_name = "Unknown"
                except:
                    author_name = "Unknown"
            else:
                author_name = "Unknown"
                
            year = paper.get('year', 'n.d.')
            citation_key = f"{author_name}, {year}"
            citation_map[citation_key.lower()] = paper
            
        # Process each section
        for section in sections:
            # Find all [Author, Year] patterns
            pattern = r'\[([^,\]]+),\s*(\d{4}|\d{2}|n\.d\.)\]'
            matches = re.findall(pattern, section.content)
            
            for match in matches:
                author, year = match
                citation_key = f"{author}, {year}".lower()
                if citation_key in citation_map:
                    section.citations.append(citation_key)
                    
        return sections
        
    def _select_relevant_papers(
        self,
        papers: List[Dict],
        section_title: str,
        limit: int = 10
    ) -> List[Dict]:
        """Select papers relevant to a section (simplified)."""
        # Simple keyword matching
        keywords = section_title.lower().split()
        scored_papers = []
        
        for paper in papers:
            score = 0
            text = (paper.get('title', '') + ' ' + paper.get('summary', '')).lower()
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                scored_papers.append((score, paper))
                
        # Sort by score and return top papers
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        return [p[1] for p in scored_papers[:limit]]
        
    def _format_papers_for_prompt(self, papers: List[Dict]) -> str:
        """Format papers for inclusion in prompts."""
        formatted = []
        for i, paper in enumerate(papers, 1):
            authors = paper.get('authors', ['Unknown'])
            
            # Handle various author formats safely
            try:
                if authors is not None and hasattr(authors, '__len__') and len(authors) > 0:
                    first_author = authors[0] if isinstance(authors[0], str) else str(authors[0])
                    # Clean up author name
                    first_author = first_author.split()[-1] if first_author else 'Unknown'
                else:
                    first_author = 'Unknown'
            except:
                first_author = 'Unknown'
                
            formatted.append(
                f"{i}. {paper.get('title', 'Unknown Title')} "
                f"({first_author} et al., {paper.get('year', 'n.d.')})"
            )
            
        return "\n".join(formatted)
        
    def _default_outline(self, num_sections: int) -> List[str]:
        """Generate default outline if generation fails."""
        default_sections = [
            "Introduction and Background",
            "Core Methods and Approaches",
            "Key Applications",
            "Evaluation and Benchmarks",
            "Challenges and Limitations",
            "Future Directions and Conclusions"
        ]
        return default_sections[:num_sections]


class AutoSurveyLCE(AutoSurveyBaseline):
    """
    AutoSurvey with Local Coherence Enhancement (LCE).
    Adds 2-pass refinement for better section transitions.
    """
    
    def generate_survey(
        self,
        papers: List[Dict],
        topic: str,
        target_sections: int = 6
    ) -> Dict:
        """Generate survey with LCE enhancement."""
        # Generate base survey
        survey = super().generate_survey(papers, topic, target_sections)
        
        # Apply Local Coherence Enhancement
        logger.info("Applying Local Coherence Enhancement (LCE)")
        enhanced_sections = self._apply_lce(survey['sections'])
        survey['sections'] = enhanced_sections
        survey['lce_applied'] = True
        
        return survey
        
    def _apply_lce(self, sections: List[SurveySection]) -> List[SurveySection]:
        """
        Apply 2-pass Local Coherence Enhancement.
        Pass 1: Refine odd sections based on neighbors
        Pass 2: Refine even sections based on updated neighbors
        """
        if len(sections) < 2:
            return sections
            
        # Pass 1: Refine odd sections
        logger.info("LCE Pass 1: Refining odd sections")
        for i in range(1, len(sections), 2):  # Odd indices (1, 3, 5...)
            sections[i] = self._refine_section(
                sections[i],
                sections[i-1] if i > 0 else None,
                sections[i+1] if i < len(sections)-1 else None
            )
            
        # Pass 2: Refine even sections
        logger.info("LCE Pass 2: Refining even sections")
        for i in range(0, len(sections), 2):  # Even indices (0, 2, 4...)
            sections[i] = self._refine_section(
                sections[i],
                sections[i-1] if i > 0 else None,
                sections[i+1] if i < len(sections)-1 else None
            )
            
        return sections
        
    def _refine_section(
        self,
        section: SurveySection,
        prev_section: Optional[SurveySection],
        next_section: Optional[SurveySection]
    ) -> SurveySection:
        """Refine a section based on its neighbors for coherence."""
        context_parts = []
        
        if prev_section:
            context_parts.append(f"Previous section '{prev_section.title}' ends with: "
                                + prev_section.content[-200:])
        if next_section:
            context_parts.append(f"Next section '{next_section.title}' begins with: "
                                + next_section.content[:200])
            
        if not context_parts:
            return section  # No neighbors to enhance coherence with
            
        context = "\n\n".join(context_parts)
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at improving text coherence and flow."
            },
            {
                "role": "user",
                "content": f"""Refine this section for better coherence with its neighbors:

Section Title: {section.title}
Current Content:
{section.content}

Neighboring Context:
{context}

Improve the transitions and flow while preserving the main content.
Keep the same approximate length."""
            }
        ]
        
        response = self.claude_wrapper.chat_completion(
            messages=messages,
            model="haiku",  # Fast model for refinement
            use_cache=False
        )
        
        if "error" not in response:
            section.content = response["choices"][0]["message"]["content"]
            
        return section


def test_autosurvey():
    """Test AutoSurvey baseline implementation."""
    print("Testing AutoSurvey Baseline")
    print("=" * 60)
    
    # Load test papers
    loader = SciMCPDataLoader()
    papers_df = loader.load_data()
    
    # Get papers on a specific topic
    test_papers = loader.search("transformer attention mechanism", top_k=20)
    
    # Convert to list format
    papers = []
    for paper in test_papers:
        papers.append({
            'title': paper.get('title', ''),
            'summary': paper.get('summary', ''),
            'authors': paper.get('authors', []),
            'year': paper.get('year', 2024)
        })
    
    print(f"Testing with {len(papers)} papers on transformers")
    
    # Test basic AutoSurvey
    print("\n1. Testing Basic AutoSurvey...")
    autosurvey = AutoSurveyBaseline()
    survey = autosurvey.generate_survey(
        papers=papers,
        topic="Transformer Attention Mechanisms",
        target_sections=4
    )
    
    print(f"Generated survey with {len(survey['sections'])} sections:")
    for section in survey['sections']:
        print(f"  - {section.title} ({len(section.content.split())} words)")
        
    # Test AutoSurvey with LCE
    print("\n2. Testing AutoSurvey with LCE...")
    autosurvey_lce = AutoSurveyLCE()
    survey_lce = autosurvey_lce.generate_survey(
        papers=papers,
        topic="Transformer Attention Mechanisms",
        target_sections=4
    )
    
    print(f"LCE applied: {survey_lce.get('lce_applied', False)}")
    
    # Save results
    output_dir = Path("data/surveys")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "autosurvey_test.json", 'w') as f:
        # Convert sections to dict for JSON serialization
        survey_dict = {
            'topic': survey_lce['topic'],
            'num_papers': survey_lce['num_papers'],
            'sections': [
                {
                    'title': s.title,
                    'content': s.content,
                    'section_number': s.section_number,
                    'citations': s.citations
                }
                for s in survey_lce['sections']
            ],
            'lce_applied': survey_lce.get('lce_applied', False)
        }
        json.dump(survey_dict, f, indent=2)
        
    print(f"\nSurvey saved to {output_dir / 'autosurvey_test.json'}")
    
    return survey_lce


if __name__ == "__main__":
    test_autosurvey()