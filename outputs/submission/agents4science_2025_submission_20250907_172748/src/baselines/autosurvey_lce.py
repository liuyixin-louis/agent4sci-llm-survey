"""
AutoSurvey with Local Coherence Enhancement (LCE)
Implements 2-pass refinement for adjacent sections
"""

from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)

class AutoSurveyLCE:
    """AutoSurvey with Local Coherence Enhancement"""
    
    def __init__(self, claude_wrapper):
        self.wrapper = claude_wrapper
        self.baseline = None
        # Import baseline here to avoid circular imports
        from src.baselines.autosurvey import AutoSurveyBaseline
        self.baseline = AutoSurveyBaseline(claude_wrapper)
    
    def generate_survey_with_lce(self, papers: List[Dict], topic: str = None) -> str:
        """Generate survey with Local Coherence Enhancement"""
        
        # Step 1: Generate base survey
        logger.info("Generating base survey...")
        base_survey = self.baseline.generate_survey(papers, topic)
        
        # Step 2: Apply 2-pass Local Coherence Enhancement
        logger.info("Applying Local Coherence Enhancement...")
        enhanced_survey = self._apply_lce(base_survey)
        
        return enhanced_survey
    
    def _apply_lce(self, survey: str) -> str:
        """Apply 2-pass Local Coherence Enhancement"""
        
        # Parse sections
        sections = self._parse_sections(survey)
        
        if len(sections) < 2:
            return survey  # No enhancement needed for single section
        
        # Pass 1: Enhance odd-numbered sections (1, 3, 5, ...)
        logger.info("LCE Pass 1: Enhancing odd sections...")
        for i in range(0, len(sections), 2):
            if i > 0:  # Has previous section
                sections[i] = self._enhance_transition(
                    sections[i-1], 
                    sections[i],
                    sections[i+1] if i+1 < len(sections) else None
                )
        
        # Pass 2: Enhance even-numbered sections (2, 4, 6, ...)
        logger.info("LCE Pass 2: Enhancing even sections...")
        for i in range(1, len(sections), 2):
            sections[i] = self._enhance_transition(
                sections[i-1],
                sections[i],
                sections[i+1] if i+1 < len(sections) else None
            )
        
        # Reconstruct survey
        enhanced_survey = "\n\n".join(sections)
        return enhanced_survey
    
    def _parse_sections(self, survey: str) -> List[str]:
        """Parse survey into sections"""
        # Split by section headers (##)
        pattern = r'(?=^## )'
        sections = re.split(pattern, survey, flags=re.MULTILINE)
        
        # Filter out empty sections
        sections = [s.strip() for s in sections if s.strip()]
        
        # If no sections found, treat as single section
        if not sections:
            return [survey]
        
        return sections
    
    def _enhance_transition(self, prev_section: str, current_section: str, 
                           next_section: str = None) -> str:
        """Enhance transition between sections"""
        
        # Extract section titles
        def get_title(section):
            lines = section.split('\n')
            for line in lines:
                if line.startswith('## '):
                    return line.replace('## ', '').strip()
            return "Section"
        
        prev_title = get_title(prev_section) if prev_section else None
        current_title = get_title(current_section)
        next_title = get_title(next_section) if next_section else None
        
        # Prepare context for enhancement
        context = f"""
Previous section: {prev_title if prev_title else 'Introduction'}
Current section: {current_title}
Next section: {next_title if next_title else 'Conclusion'}

Task: Improve the coherence and flow of the current section by:
1. Adding a smooth transition from the previous section
2. Ensuring logical flow within the section
3. If applicable, setting up the next section

Current section content:
{current_section}

Previous section ending (last 200 chars):
{prev_section[-200:] if prev_section else 'N/A'}
"""
        
        messages = [
            {"role": "user", "content": f"""{context}

Please rewrite the current section with improved transitions and coherence. 
Keep the same structure and content, but improve the flow and connections.
Return ONLY the enhanced section text, starting with the section header."""}
        ]
        
        try:
            response = self.wrapper.chat_completion(messages, model="sonnet")
            enhanced = response.strip()
            
            # Ensure section header is preserved
            if not enhanced.startswith('## '):
                enhanced = current_section  # Fallback to original
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"LCE enhancement failed: {e}")
            return current_section  # Return original on error
    
    def _add_transition_phrases(self, section: str, prev_context: str = None, 
                               next_context: str = None) -> str:
        """Add transition phrases to improve flow"""
        
        transitions = {
            'building': [
                "Building on the previous discussion, ",
                "Extending these concepts, ",
                "Following this foundation, "
            ],
            'contrast': [
                "In contrast to the previous approach, ",
                "However, ",
                "Alternatively, "
            ],
            'continuation': [
                "Furthermore, ",
                "Additionally, ",
                "Moreover, "
            ],
            'conclusion': [
                "In summary, ",
                "To conclude this section, ",
                "These findings suggest that "
            ]
        }
        
        # Simple heuristic to add transitions
        lines = section.split('\n')
        
        # Add opening transition if not present
        if len(lines) > 2 and not any(trans in lines[2] for trans_list in transitions.values() for trans in trans_list):
            # Add after header and blank line
            if prev_context:
                lines.insert(2, transitions['building'][0])
        
        return '\n'.join(lines)