"""Quick test of core functionality"""
import sys
sys.path.insert(0, '.')

try:
    from src.baselines.autosurvey import AutoSurveyBaseline
    from src.our_system.iterative import IterativeSurveySystem
    from src.evaluation.metrics import SurveyEvaluator
    
    print("✅ Imports successful")
    
    # Test instantiation
    baseline = AutoSurveyBaseline()
    iterative = IterativeSurveySystem()
    evaluator = SurveyEvaluator()
    
    print("✅ Objects created")
    
    # Test basic functionality
    sample_papers = [
        {'title': 'Paper 1', 'abstract': 'Abstract 1', 'authors': ['Author 1']},
        {'title': 'Paper 2', 'abstract': 'Abstract 2', 'authors': ['Author 2']}
    ]
    
    sample_survey = {
        'title': 'Test Survey',
        'sections': [
            {'title': 'Introduction', 'content': 'Test content about Paper 1', 'citations': ['Paper 1']}
        ]
    }
    
    scores = evaluator.evaluate_survey(sample_survey, sample_papers)
    print(f"✅ Evaluation works: Overall score = {scores.get('overall', 'N/A')}")
    
    print("\n🎉 Core functionality validated!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
