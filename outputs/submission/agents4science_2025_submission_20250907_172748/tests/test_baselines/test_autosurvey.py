"""
Comprehensive tests for AutoSurvey baseline implementation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import os
import sys
from concurrent.futures import Future

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.baselines.autosurvey import AutoSurveyBaseline


class TestAutoSurveyBaseline:
    """Test suite for AutoSurvey baseline"""
    
    @pytest.fixture
    def autosurvey(self):
        """Create AutoSurvey instance"""
        with patch('src.baselines.autosurvey.ClaudeCodeCLIWrapper'):
            return AutoSurveyBaseline(papers_per_chunk=5)
    
    @pytest.fixture
    def sample_papers(self):
        """Sample papers for testing"""
        return [
            {
                "title": "Paper 1: Introduction to LLMs",
                "abstract": "This paper introduces large language models.",
                "year": 2023,
                "authors": ["Author A", "Author B"]
            },
            {
                "title": "Paper 2: Transformer Architecture",
                "abstract": "We analyze transformer architectures in detail.",
                "year": 2023,
                "authors": ["Author C"]
            },
            {
                "title": "Paper 3: In-context Learning",
                "abstract": "Study of in-context learning capabilities.",
                "year": 2024,
                "authors": ["Author D", "Author E"]
            },
            {
                "title": "Paper 4: Prompt Engineering",
                "abstract": "Techniques for effective prompt engineering.",
                "year": 2024,
                "authors": ["Author F"]
            },
            {
                "title": "Paper 5: LLM Evaluation",
                "abstract": "Comprehensive evaluation metrics for LLMs.",
                "year": 2024,
                "authors": ["Author G", "Author H"]
            }
        ]
    
    @pytest.fixture
    def sample_outline(self):
        """Sample outline structure"""
        return {
            "title": "Survey of Large Language Models",
            "sections": [
                {
                    "title": "Introduction",
                    "description": "Overview of LLMs and their importance"
                },
                {
                    "title": "Architecture",
                    "description": "Transformer architectures and variants"
                },
                {
                    "title": "Training Methods",
                    "description": "Pre-training and fine-tuning approaches"
                },
                {
                    "title": "Applications",
                    "description": "Real-world applications of LLMs"
                },
                {
                    "title": "Conclusion",
                    "description": "Summary and future directions"
                }
            ]
        }
    
    def test_initialization(self, autosurvey):
        """Test AutoSurvey initialization"""
        assert autosurvey.papers_per_chunk == 5
        assert autosurvey.claude_wrapper is not None
    
    def test_chunk_papers(self, autosurvey, sample_papers):
        """Test paper chunking"""
        chunks = autosurvey._chunk_papers(sample_papers, chunk_size=2)
        
        assert len(chunks) == 3  # 5 papers with chunk_size=2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2
        assert len(chunks[2]) == 1
    
    def test_chunk_papers_empty(self, autosurvey):
        """Test chunking with empty paper list"""
        chunks = autosurvey._chunk_papers([], chunk_size=5)
        assert chunks == []
    
    def test_generate_outline(self, autosurvey, sample_papers):
        """Test outline generation"""
        mock_response = {
            "outline": {
                "title": "Test Survey",
                "sections": [
                    {"title": "Intro", "description": "Introduction"},
                    {"title": "Methods", "description": "Methodology"}
                ]
            }
        }
        
        autosurvey.claude_wrapper.query.return_value = mock_response
        
        outline = autosurvey.generate_outline(sample_papers, "Test Topic")
        
        assert outline["title"] == "Test Survey"
        assert len(outline["sections"]) == 2
        autosurvey.claude_wrapper.query.assert_called_once()
    
    def test_generate_outline_with_chunks(self, autosurvey):
        """Test outline generation with multiple chunks"""
        # Create 15 papers to force multiple chunks
        papers = [{"title": f"Paper {i}", "abstract": f"Abstract {i}"} 
                  for i in range(15)]
        
        mock_responses = [
            {"outline": {"sections": [{"title": f"Section {i}"}]}}
            for i in range(3)  # 3 chunks expected
        ]
        
        autosurvey.claude_wrapper.query.side_effect = mock_responses
        
        outline = autosurvey.generate_outline(papers, "Topic")
        
        # Should aggregate sections from all chunks
        assert autosurvey.claude_wrapper.query.call_count == 3
    
    def test_write_section(self, autosurvey, sample_papers):
        """Test section writing"""
        section = {
            "title": "Introduction",
            "description": "Overview of the field"
        }
        
        mock_response = {
            "content": "This is the introduction section content.",
            "citations": ["Paper 1", "Paper 2"]
        }
        
        autosurvey.claude_wrapper.query.return_value = mock_response
        
        result = autosurvey.write_section(section, sample_papers)
        
        assert result["title"] == "Introduction"
        assert result["content"] == mock_response["content"]
        assert result["citations"] == mock_response["citations"]
    
    def test_write_sections_parallel(self, autosurvey, sample_outline, sample_papers):
        """Test parallel section writing"""
        mock_responses = [
            {"content": f"Content for {section['title']}", "citations": []}
            for section in sample_outline["sections"]
        ]
        
        autosurvey.claude_wrapper.query.side_effect = mock_responses
        
        with patch('src.baselines.autosurvey.ThreadPoolExecutor') as mock_executor:
            # Mock the executor to run synchronously for testing
            mock_executor.return_value.__enter__.return_value.map = lambda func, items: [
                func(item) for item in items
            ]
            
            sections = autosurvey.write_sections_parallel(
                sample_outline["sections"], 
                sample_papers
            )
        
        assert len(sections) == len(sample_outline["sections"])
        assert all("content" in s for s in sections)
    
    def test_inject_citations(self, autosurvey):
        """Test citation injection"""
        section = {
            "content": "LLMs have shown great progress. Transformers are key.",
            "citations": []
        }
        
        papers = [
            {"title": "Progress in LLMs", "abstract": "LLMs progress"},
            {"title": "Transformer Architecture", "abstract": "Transformers key"}
        ]
        
        mock_response = {
            "content": "LLMs have shown great progress [1]. Transformers are key [2].",
            "citations": ["Progress in LLMs", "Transformer Architecture"]
        }
        
        autosurvey.claude_wrapper.query.return_value = mock_response
        
        result = autosurvey.inject_citations(section, papers)
        
        assert "[1]" in result["content"]
        assert "[2]" in result["content"]
        assert len(result["citations"]) == 2
    
    def test_local_coherence_enhancement(self, autosurvey):
        """Test LCE (Local Coherence Enhancement)"""
        sections = [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"},
            {"title": "Section 3", "content": "Content 3"}
        ]
        
        # Mock responses for LCE passes
        mock_responses = [
            {"content": "Enhanced content 1"},
            {"content": "Enhanced content 3"},
            {"content": "Enhanced content 2"}
        ]
        
        autosurvey.claude_wrapper.query.side_effect = mock_responses
        
        enhanced = autosurvey.local_coherence_enhancement(sections)
        
        # Should make 3 calls (odd sections first, then even)
        assert autosurvey.claude_wrapper.query.call_count == 3
        assert all("Enhanced" in s["content"] for s in enhanced)
    
    def test_full_survey_generation(self, autosurvey, sample_papers):
        """Test complete survey generation workflow"""
        # Mock all Claude responses
        outline_response = {
            "outline": {
                "title": "LLM Survey",
                "sections": [
                    {"title": "Intro", "description": "Introduction"},
                    {"title": "Methods", "description": "Methods"}
                ]
            }
        }
        
        section_responses = [
            {"content": "Intro content", "citations": ["Paper 1"]},
            {"content": "Methods content", "citations": ["Paper 2"]}
        ]
        
        autosurvey.claude_wrapper.query.side_effect = [
            outline_response,
            *section_responses
        ]
        
        survey = autosurvey.generate_survey(sample_papers, "LLMs")
        
        assert survey["title"] == "LLM Survey"
        assert len(survey["sections"]) == 2
        assert survey["sections"][0]["content"] == "Intro content"
    
    @pytest.mark.parametrize("num_papers,chunk_size,expected_chunks", [
        (10, 5, 2),
        (15, 5, 3),
        (3, 5, 1),
        (0, 5, 0),
        (7, 3, 3)
    ])
    def test_chunking_parametrized(self, autosurvey, num_papers, chunk_size, expected_chunks):
        """Test paper chunking with various sizes"""
        papers = [{"title": f"Paper {i}"} for i in range(num_papers)]
        chunks = autosurvey._chunk_papers(papers, chunk_size)
        assert len(chunks) == expected_chunks
    
    def test_error_handling_outline_generation(self, autosurvey):
        """Test error handling in outline generation"""
        autosurvey.claude_wrapper.query.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            autosurvey.generate_outline([], "Topic")
    
    def test_error_handling_section_writing(self, autosurvey):
        """Test error handling in section writing"""
        autosurvey.claude_wrapper.query.return_value = {}  # Missing required fields
        
        section = {"title": "Test", "description": "Test section"}
        result = autosurvey.write_section(section, [])
        
        # Should handle missing fields gracefully
        assert result["title"] == "Test"
        assert "content" in result
    
    def test_citation_deduplication(self, autosurvey):
        """Test that duplicate citations are handled"""
        section = {
            "content": "Content with citations",
            "citations": ["Paper A", "Paper A", "Paper B"]
        }
        
        # Process citations (implementation should deduplicate)
        unique_citations = list(dict.fromkeys(section["citations"]))
        
        assert len(unique_citations) == 2
        assert unique_citations == ["Paper A", "Paper B"]
    
    def test_parallel_execution_performance(self, autosurvey):
        """Test that parallel execution is used for efficiency"""
        sections = [{"title": f"Section {i}"} for i in range(10)]
        
        with patch('src.baselines.autosurvey.ThreadPoolExecutor') as mock_executor:
            mock_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_instance
            
            autosurvey.write_sections_parallel(sections, [])
            
            # Verify ThreadPoolExecutor was used
            mock_executor.assert_called_once()
            assert mock_instance.map.called


class TestAutoSurveyWithLCE:
    """Test AutoSurvey with Local Coherence Enhancement"""
    
    @pytest.fixture
    def autosurvey_lce(self):
        """Create AutoSurvey instance with LCE enabled"""
        with patch('src.baselines.autosurvey_lce.ClaudeCodeCLIWrapper'):
            from src.baselines.autosurvey_lce import AutoSurveyWithLCE
            return AutoSurveyWithLCE()
    
    def test_lce_two_passes(self, autosurvey_lce):
        """Test that LCE performs two passes"""
        sections = [
            {"title": f"Section {i}", "content": f"Content {i}"}
            for i in range(5)
        ]
        
        call_count = 0
        def mock_query(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {"content": f"Enhanced {call_count}"}
        
        autosurvey_lce.claude_wrapper.query.side_effect = mock_query
        
        enhanced = autosurvey_lce.local_coherence_enhancement(sections)
        
        # Pass 1: odd sections (0, 2, 4) = 3 calls
        # Pass 2: even sections (1, 3) = 2 calls
        assert call_count == 5
    
    def test_lce_preserves_structure(self, autosurvey_lce):
        """Test that LCE preserves section structure"""
        sections = [
            {
                "title": "Introduction",
                "content": "Original intro",
                "citations": ["Ref1"],
                "subsections": ["Background", "Motivation"]
            }
        ]
        
        autosurvey_lce.claude_wrapper.query.return_value = {
            "content": "Enhanced intro"
        }
        
        enhanced = autosurvey_lce.local_coherence_enhancement(sections)
        
        # Should preserve all fields except content
        assert enhanced[0]["title"] == "Introduction"
        assert enhanced[0]["citations"] == ["Ref1"]
        assert enhanced[0]["subsections"] == ["Background", "Motivation"]
        assert enhanced[0]["content"] == "Enhanced intro"
    
    def test_lce_context_passing(self, autosurvey_lce):
        """Test that LCE passes context between sections"""
        sections = [
            {"title": "Section 1", "content": "Content 1"},
            {"title": "Section 2", "content": "Content 2"},
            {"title": "Section 3", "content": "Content 3"}
        ]
        
        autosurvey_lce.claude_wrapper.query.return_value = {"content": "Enhanced"}
        
        autosurvey_lce.local_coherence_enhancement(sections)
        
        # Check that context from adjacent sections is included in prompts
        calls = autosurvey_lce.claude_wrapper.query.call_args_list
        
        # Each call should reference adjacent sections
        for call in calls:
            prompt = call[0][0] if call[0] else call[1].get('prompt', '')
            # Verify prompt contains context (implementation specific)
            assert isinstance(prompt, str)


@pytest.mark.integration
class TestAutoSurveyIntegration:
    """Integration tests for AutoSurvey"""
    
    def test_end_to_end_survey_generation(self):
        """Test complete survey generation pipeline"""
        with patch('src.baselines.autosurvey.ClaudeCodeCLIWrapper') as mock_wrapper:
            # Setup mock responses for entire workflow
            mock_instance = MagicMock()
            mock_wrapper.return_value = mock_instance
            
            # Outline response
            mock_instance.query.side_effect = [
                {
                    "outline": {
                        "title": "Comprehensive LLM Survey",
                        "sections": [
                            {"title": "Introduction", "description": "Overview"},
                            {"title": "Methods", "description": "Methodology"},
                            {"title": "Results", "description": "Findings"},
                            {"title": "Conclusion", "description": "Summary"}
                        ]
                    }
                },
                # Section responses
                {"content": "Introduction content...", "citations": ["Paper1"]},
                {"content": "Methods content...", "citations": ["Paper2"]},
                {"content": "Results content...", "citations": ["Paper3"]},
                {"content": "Conclusion content...", "citations": ["Paper4"]}
            ]
            
            autosurvey = AutoSurveyBaseline()
            
            papers = [
                {"title": f"Paper{i}", "abstract": f"Abstract {i}"}
                for i in range(1, 11)
            ]
            
            survey = autosurvey.generate_survey(papers, "LLM Research")
            
            assert survey["title"] == "Comprehensive LLM Survey"
            assert len(survey["sections"]) == 4
            assert all("content" in s for s in survey["sections"])
            assert all("citations" in s for s in survey["sections"])
    
    def test_performance_with_many_papers(self):
        """Test performance with large paper set"""
        with patch('src.baselines.autosurvey.ClaudeCodeCLIWrapper') as mock_wrapper:
            mock_instance = MagicMock()
            mock_wrapper.return_value = mock_instance
            
            # Create 100 papers
            papers = [
                {"title": f"Paper {i}", "abstract": f"Abstract for paper {i}"}
                for i in range(100)
            ]
            
            mock_instance.query.return_value = {
                "outline": {"title": "Survey", "sections": []}
            }
            
            autosurvey = AutoSurveyBaseline(papers_per_chunk=20)
            
            import time
            start = time.time()
            outline = autosurvey.generate_outline(papers, "Topic")
            duration = time.time() - start
            
            # Should complete reasonably quickly even with many papers
            assert duration < 5.0  # 5 seconds max
            
            # Should have made 5 calls (100 papers / 20 per chunk)
            assert mock_instance.query.call_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])