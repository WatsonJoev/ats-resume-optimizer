"""
Test script to verify the ATS Resume Optimizer setup.
Run this to check if all components are working correctly.
"""

import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from config import get_settings, LLMFactory
        print("  [OK] config module")
    except ImportError as e:
        print(f"  [FAIL] config module: {e}")
        return False
    
    try:
        from services.ats_scorer import ATSScorer
        from services.resume_parser import ResumeParser
        print("  [OK] services module")
    except ImportError as e:
        print(f"  [FAIL] services module: {e}")
        return False
    
    try:
        from tools.ats_tools import analyze_job_description, calculate_ats_score
        from tools.resume_tools import parse_resume_text, validate_resume_changes
        print("  [OK] tools module")
    except ImportError as e:
        print(f"  [FAIL] tools module: {e}")
        return False
    
    try:
        from storage.local_storage import LocalStorage
        print("  [OK] storage module")
    except ImportError as e:
        print(f"  [FAIL] storage module: {e}")
        return False
    
    return True


def test_ats_scorer():
    """Test the ATS scorer with sample data."""
    print("\nTesting ATS Scorer...")
    
    from services.ats_scorer import ATSScorer
    
    scorer = ATSScorer()
    
    sample_jd = """
    Software Engineer - Python
    
    Requirements:
    - 3+ years of Python experience
    - Experience with Django or FastAPI
    - Knowledge of SQL databases (PostgreSQL preferred)
    - Familiarity with AWS services
    - Strong problem-solving skills
    
    Responsibilities:
    - Design and implement backend services
    - Write clean, maintainable code
    - Collaborate with cross-functional teams
    """
    
    sample_resume = """
    John Doe
    john.doe@email.com | 555-123-4567
    
    Summary:
    Software developer with 4 years of experience in Python and web development.
    
    Experience:
    Software Developer at Tech Corp (2020-Present)
    - Developed REST APIs using Python and Flask
    - Managed MySQL databases
    - Deployed applications to cloud infrastructure
    
    Education:
    BS Computer Science, State University
    
    Skills:
    Python, Flask, MySQL, Git, Linux
    """
    
    try:
        report = scorer.calculate_score(sample_jd, sample_resume)
        result = scorer.to_dict(report)
        
        print(f"  Overall Score: {result['overall_score']}/100")
        print(f"  Matched Keywords: {len(result['keyword_analysis']['matched'])}")
        print(f"  Missing Keywords: {len(result['keyword_analysis']['missing'])}")
        print("  [OK] ATS Scorer working")
        return True
    except Exception as e:
        print(f"  [FAIL] ATS Scorer: {e}")
        return False


def test_resume_parser():
    """Test the resume parser."""
    print("\nTesting Resume Parser...")
    
    from services.resume_parser import ResumeParser
    
    parser = ResumeParser()
    
    sample_resume = """
    Jane Smith
    jane.smith@email.com | 555-987-6543 | linkedin.com/in/janesmith
    San Francisco, CA
    
    Summary
    Experienced software engineer specializing in full-stack development.
    
    Experience
    Senior Developer at StartupXYZ (2021-Present)
    - Led development of customer-facing features
    - Mentored junior developers
    
    Education
    MS Computer Science, Tech University
    
    Skills
    JavaScript, React, Node.js, Python, PostgreSQL
    """
    
    try:
        parsed = parser.parse_text(sample_resume)
        
        print(f"  Sections found: {list(parsed.sections.keys())}")
        print(f"  Contact info: {parsed.contact_info}")
        print(f"  Skills extracted: {parsed.skills[:5]}...")
        print("  [OK] Resume Parser working")
        return True
    except Exception as e:
        print(f"  [FAIL] Resume Parser: {e}")
        return False


def test_local_storage():
    """Test local storage functionality."""
    print("\nTesting Local Storage...")
    
    from storage.local_storage import LocalStorage
    
    try:
        storage = LocalStorage()
        
        # Test skills storage
        test_skills = ["Python", "Django", "AWS"]
        storage.save_user_skills(test_skills)
        loaded_skills = storage.get_user_skills()
        
        assert loaded_skills == test_skills, "Skills mismatch"
        print(f"  Skills saved and loaded: {loaded_skills}")
        print("  [OK] Local Storage working")
        return True
    except Exception as e:
        print(f"  [FAIL] Local Storage: {e}")
        return False


def test_api_key():
    """Check if API key is configured."""
    print("\nChecking API Key...")
    
    from config import get_settings
    
    settings = get_settings()
    
    if settings.openrouter_api_key:
        print(f"  API Key found: {settings.openrouter_api_key[:10]}...")
        print("  [OK] API Key configured")
        return True
    else:
        print("  [WARN] No API key found")
        print("  Create a .env file with OPENROUTER_API_KEY=your_key")
        return False


def test_agents_init():
    """Test agent initialization (requires API key)."""
    print("\nTesting Agent Initialization...")
    
    from config import get_settings
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        print("  [SKIP] No API key - skipping agent test")
        return True
    
    try:
        from agents import ATSEvaluationAgent, ResumeHandlingAgent, MasterAgent
        
        print("  Initializing ATS Evaluation Agent...")
        ats_agent = ATSEvaluationAgent()
        print(f"    Model: {ats_agent.model_name}")
        
        print("  Initializing Resume Handling Agent...")
        resume_agent = ResumeHandlingAgent()
        
        print("  Initializing Master Agent...")
        master_agent = MasterAgent()
        master_agent.set_agents(ats_agent, resume_agent)
        
        print("  [OK] All agents initialized")
        return True
    except Exception as e:
        print(f"  [FAIL] Agent initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("ATS Resume Optimizer - Setup Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("ATS Scorer", test_ats_scorer()))
    results.append(("Resume Parser", test_resume_parser()))
    results.append(("Local Storage", test_local_storage()))
    results.append(("API Key", test_api_key()))
    results.append(("Agents", test_agents_init()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\nAll tests passed! You can now run:")
        print("  streamlit run app.py")
    else:
        print("\nSome tests failed. Please check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
