"""Tools module for ATS Resume Optimizer agents."""

from .ats_tools import (
    analyze_job_description,
    calculate_ats_score,
    identify_keyword_gaps,
    generate_keyword_map,
)

from .resume_tools import (
    parse_resume_text,
    rewrite_resume_section,
    generate_resume_diff,
    validate_resume_changes,
)

__all__ = [
    # ATS Tools
    "analyze_job_description",
    "calculate_ats_score",
    "identify_keyword_gaps",
    "generate_keyword_map",
    # Resume Tools
    "parse_resume_text",
    "rewrite_resume_section",
    "generate_resume_diff",
    "validate_resume_changes",
]
