"""
ATS Analysis Tools
===================
Tools for analyzing job descriptions and calculating ATS scores.
"""

import json
from typing import List, Dict, Any
from langchain_core.tools import tool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ats_scorer import ATSScorer


# Global scorer instance
_scorer = ATSScorer()


@tool
def analyze_job_description(jd_text: str) -> str:
    """
    Analyze a job description to extract requirements, skills, and keywords.
    
    Args:
        jd_text: The full text of the job description
        
    Returns:
        JSON string with extracted requirements and keywords
    """
    requirements = _scorer.extract_jd_requirements(jd_text)
    keywords = list(_scorer.extract_keywords(jd_text))
    
    result = {
        "requirements": requirements,
        "keywords": keywords[:30],  # Top 30 keywords
        "keyword_count": len(keywords),
    }
    
    return json.dumps(result, indent=2)


@tool
def calculate_ats_score(jd_text: str, resume_text: str, user_skills: str = "") -> str:
    """
    Calculate the ATS compatibility score between a job description and resume.
    
    Args:
        jd_text: The job description text
        resume_text: The resume text
        user_skills: Comma-separated list of additional skills the user has
        
    Returns:
        JSON string with detailed ATS score breakdown
    """
    skills_list = [s.strip() for s in user_skills.split(",") if s.strip()] if user_skills else []
    
    report = _scorer.calculate_score(jd_text, resume_text, skills_list)
    result = _scorer.to_dict(report)
    
    return json.dumps(result, indent=2)


@tool
def identify_keyword_gaps(jd_text: str, resume_text: str) -> str:
    """
    Identify missing keywords that should be added to the resume.
    
    Args:
        jd_text: The job description text
        resume_text: The resume text
        
    Returns:
        JSON string with missing and matched keywords
    """
    analysis = _scorer.analyze_keywords(jd_text, resume_text)
    
    result = {
        "matched_keywords": analysis.matched,
        "missing_keywords": analysis.missing,
        "partial_matches": analysis.partial,
        "match_percentage": analysis.match_percentage,
        "priority_additions": analysis.missing[:10],  # Top 10 to add
    }
    
    return json.dumps(result, indent=2)


@tool
def generate_keyword_map(jd_text: str, resume_text: str) -> str:
    """
    Generate a mapping of JD requirements to resume sections where they should appear.
    
    Args:
        jd_text: The job description text
        resume_text: The resume text
        
    Returns:
        JSON string mapping keywords to recommended resume sections
    """
    requirements = _scorer.extract_jd_requirements(jd_text)
    jd_keywords = _scorer.extract_keywords(jd_text)
    resume_keywords = _scorer.extract_keywords(resume_text)
    
    # Map keywords to sections
    keyword_map = {
        "skills_section": [],
        "experience_section": [],
        "summary_section": [],
        "projects_section": [],
    }
    
    # Technical skills go to skills section
    tech_skills = jd_keywords & _scorer.TECH_SKILLS
    missing_tech = tech_skills - resume_keywords
    keyword_map["skills_section"] = list(missing_tech)
    
    # Responsibilities go to experience
    for resp in requirements.get("responsibilities", []):
        keywords_in_resp = _scorer.extract_keywords(resp)
        missing = keywords_in_resp - resume_keywords
        keyword_map["experience_section"].extend(list(missing)[:3])
    
    # Required skills can go to summary for emphasis
    for skill in requirements.get("required_skills", [])[:5]:
        keywords_in_skill = _scorer.extract_keywords(skill)
        missing = keywords_in_skill - resume_keywords
        keyword_map["summary_section"].extend(list(missing)[:2])
    
    # Deduplicate
    for section in keyword_map:
        keyword_map[section] = list(set(keyword_map[section]))
    
    return json.dumps(keyword_map, indent=2)
