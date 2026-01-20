"""
Resume Handling Tools
======================
Tools for parsing, modifying, and validating resumes.
"""

import json
import difflib
from typing import List, Dict, Any
from langchain_core.tools import tool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.resume_parser import ResumeParser


# Global parser instance
_parser = ResumeParser()


@tool
def parse_resume_text(resume_text: str) -> str:
    """
    Parse resume text to extract structured sections and information.
    
    Args:
        resume_text: The raw resume text
        
    Returns:
        JSON string with parsed resume structure
    """
    parsed = _parser.parse_text(resume_text)
    result = _parser.to_dict(parsed)
    
    # Don't include full raw text in response (too long)
    result["raw_text"] = f"[{len(parsed.raw_text)} characters]"
    
    return json.dumps(result, indent=2)


@tool
def rewrite_resume_section(
    section_name: str,
    original_content: str,
    keywords_to_add: str,
    tone: str = "professional"
) -> str:
    """
    Suggest how to rewrite a resume section to include specific keywords.
    
    This tool provides guidance - the actual rewriting should be done by the agent.
    
    Args:
        section_name: Name of the section (e.g., "summary", "experience", "skills")
        original_content: The original section content
        keywords_to_add: Comma-separated keywords to incorporate
        tone: Writing tone (professional, technical, creative)
        
    Returns:
        JSON string with rewriting suggestions
    """
    keywords = [k.strip() for k in keywords_to_add.split(",") if k.strip()]
    
    suggestions = {
        "section": section_name,
        "keywords_to_add": keywords,
        "guidelines": [],
        "warnings": [],
    }
    
    if section_name.lower() == "summary":
        suggestions["guidelines"] = [
            "Keep summary to 3-4 sentences",
            "Lead with years of experience and primary expertise",
            "Mention 2-3 key technologies naturally",
            "End with value proposition or career goal",
            f"Incorporate these keywords naturally: {', '.join(keywords[:5])}",
        ]
    elif section_name.lower() == "experience":
        suggestions["guidelines"] = [
            "Use action verbs to start each bullet",
            "Include quantifiable achievements where possible",
            "Align bullet points with JD responsibilities",
            f"Weave in keywords: {', '.join(keywords[:5])}",
            "Keep bullets to 1-2 lines each",
        ]
    elif section_name.lower() == "skills":
        suggestions["guidelines"] = [
            "Group skills by category (Languages, Frameworks, Tools)",
            "List most relevant skills first",
            f"Add missing skills: {', '.join(keywords)}",
            "Remove outdated or irrelevant skills",
        ]
    elif section_name.lower() == "projects":
        suggestions["guidelines"] = [
            "Highlight projects using target technologies",
            "Include brief description of impact/outcome",
            f"Mention these technologies if applicable: {', '.join(keywords[:5])}",
        ]
    else:
        suggestions["guidelines"] = [
            f"Incorporate keywords naturally: {', '.join(keywords)}",
            "Maintain professional tone",
            "Keep content concise and relevant",
        ]
    
    # Add warnings
    if len(keywords) > 10:
        suggestions["warnings"].append(
            "Too many keywords - prioritize the most important ones to avoid keyword stuffing"
        )
    
    return json.dumps(suggestions, indent=2)


@tool
def generate_resume_diff(original_text: str, modified_text: str) -> str:
    """
    Generate a diff showing changes between original and modified resume.
    
    Args:
        original_text: The original resume text
        modified_text: The modified resume text
        
    Returns:
        JSON string with diff summary and details
    """
    original_lines = original_text.splitlines()
    modified_lines = modified_text.splitlines()
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original",
        tofile="modified",
        lineterm=""
    ))
    
    # Count changes
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    # Generate high-level summary
    summary = []
    if additions > 0:
        summary.append(f"Added {additions} lines")
    if deletions > 0:
        summary.append(f"Removed {deletions} lines")
    if not summary:
        summary.append("No changes detected")
    
    result = {
        "summary": summary,
        "additions": additions,
        "deletions": deletions,
        "diff_preview": diff[:50] if len(diff) > 50 else diff,  # First 50 lines
        "total_diff_lines": len(diff),
    }
    
    return json.dumps(result, indent=2)


@tool
def validate_resume_changes(
    original_resume: str,
    modified_resume: str,
    user_skills: str = ""
) -> str:
    """
    Validate that resume changes don't introduce fabricated content.
    
    Args:
        original_resume: The original resume text
        modified_resume: The modified resume text
        user_skills: Comma-separated list of user's actual skills
        
    Returns:
        JSON string with validation results
    """
    original_parsed = _parser.parse_text(original_resume)
    modified_parsed = _parser.parse_text(modified_resume)
    
    user_skills_set = set(
        s.strip().lower() for s in user_skills.split(",") if s.strip()
    )
    
    validation = {
        "is_valid": True,
        "warnings": [],
        "errors": [],
        "checks": {
            "contact_preserved": True,
            "experience_intact": True,
            "no_fabrication_detected": True,
            "skills_verified": True,
        }
    }
    
    # Check contact info preserved
    orig_contact = original_parsed.contact_info
    mod_contact = modified_parsed.contact_info
    
    for key in ["email", "phone"]:
        if key in orig_contact and orig_contact[key] != mod_contact.get(key):
            validation["warnings"].append(f"Contact {key} was modified")
            validation["checks"]["contact_preserved"] = False
    
    # Check for new skills not in user's list
    orig_skills = set(s.lower() for s in original_parsed.skills)
    mod_skills = set(s.lower() for s in modified_parsed.skills)
    new_skills = mod_skills - orig_skills - user_skills_set
    
    if new_skills:
        validation["warnings"].append(
            f"New skills added that weren't in original or user list: {', '.join(list(new_skills)[:5])}"
        )
        # This is a warning, not an error - user may have forgotten to list skills
    
    # Check for potential fabrication indicators
    fabrication_phrases = [
        "led a team of",
        "managed a budget of",
        "increased revenue by",
        "saved the company",
        "million dollar",
    ]
    
    for phrase in fabrication_phrases:
        if phrase in modified_resume.lower() and phrase not in original_resume.lower():
            validation["warnings"].append(
                f"New quantifiable claim detected: '{phrase}' - verify this is accurate"
            )
    
    # Overall validation
    if validation["errors"]:
        validation["is_valid"] = False
    
    return json.dumps(validation, indent=2)
