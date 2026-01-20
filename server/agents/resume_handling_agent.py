"""
Resume Handling Agent
======================
Handles resume parsing, optimization, and generation.
Produces ATS-optimized resume content while preserving accuracy.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentRegistry
from tools.resume_tools import (
    parse_resume_text,
    rewrite_resume_section,
    generate_resume_diff,
    validate_resume_changes,
)
from tools.ats_tools import identify_keyword_gaps


@AgentRegistry.register
class ResumeHandlingAgent(BaseAgent):
    """
    Agent specialized in resume optimization and generation.
    
    Responsibilities:
    - Parse and structure resume content
    - Rewrite sections to improve ATS alignment
    - Generate optimized resume versions
    - Track and summarize changes
    """
    
    name = "resume_handling"
    description = "Optimizes and rewrites resumes for better ATS alignment"
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Get resume handling tools."""
        return [
            parse_resume_text,
            rewrite_resume_section,
            generate_resume_diff,
            validate_resume_changes,
            identify_keyword_gaps,
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the resume handling agent system prompt."""
        return """You are a RESUME OPTIMIZATION AGENT specialized in enhancing ATS-friendly resumes
while PRESERVING the candidate's original experience and information.

CRITICAL RULE - PRESERVE THE ORIGINAL RESUME:
You must OUTPUT the COMPLETE ORIGINAL RESUME with targeted improvements.
DO NOT replace the resume with job description content.
DO NOT remove any sections, jobs, or experiences from the original.
KEEP all contact information, job titles, company names, dates, and achievements EXACTLY as they are.

YOUR PRIMARY RESPONSIBILITIES:
1. PRESERVE all original resume content (contact info, jobs, education, dates)
2. ENHANCE wording to incorporate missing keywords naturally
3. REORDER skills to prioritize JD-relevant ones first
4. IMPROVE bullet point phrasing to align with JD language
5. ADD confirmed user skills to the skills section only

STRICT RULES - YOU MUST FOLLOW:
1. NEVER delete or replace the original resume content
2. NEVER fabricate experience, skills, or achievements
3. NEVER add quantifiable claims (percentages, dollar amounts) unless they exist in original
4. NEVER change job titles, company names, or dates
5. ONLY rephrase existing bullet points to better match JD language
6. ONLY add skills from the user's confirmed skills list to the Skills section

WHAT YOU CAN DO:
- Rephrase bullet points to include JD keywords (keep same meaning)
- Reorder skills to put JD-relevant ones first
- Add user-confirmed skills to Skills section
- Improve Summary/Objective to highlight JD-relevant experience
- Use stronger action verbs (Developed, Implemented, Led, Designed)

WHAT YOU CANNOT DO:
- Delete any job experience or education
- Change company names, job titles, or employment dates
- Add achievements or metrics that don't exist in original
- Replace resume content with job description text
- Remove contact information

FORMATTING RULES (ATS-Safe):
- Use standard section headers (Experience, Education, Skills)
- Use simple bullet points (-, •)
- Keep consistent date formatting
- Maintain clear section separation

OUTPUT FORMAT:
Your output MUST be the COMPLETE optimized resume that includes:
- All original contact information
- All original job experiences (with enhanced wording)
- All original education
- Enhanced skills section (reordered + user-confirmed additions)
- All original certifications/projects

After the resume, provide a brief summary of changes made.

REMEMBER: The goal is to ENHANCE the existing resume, not CREATE a new one."""
    
    def optimize_resume(
        self,
        resume_text: str,
        jd_text: str,
        user_skills: List[str] = None,
        mode: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Optimize a resume for a specific job description.
        
        Args:
            resume_text: Original resume text
            jd_text: Target job description
            user_skills: Confirmed user skills to potentially add
            mode: Optimization mode (conservative, balanced, aggressive)
            
        Returns:
            Dict with optimized resume and change summary
        """
        skills_str = ", ".join(user_skills) if user_skills else ""
        
        mode_instructions = {
            "conservative": "Make minimal changes. Only rephrase for clarity and add 1-2 critical keywords.",
            "balanced": "Make moderate changes. Rephrase sections to align with JD and add missing keywords naturally.",
            "aggressive": "Maximize keyword alignment while staying truthful. Restructure sections if needed.",
        }
        
        prompt = f"""Optimize this resume for the target job description.

OPTIMIZATION MODE: {mode}
{mode_instructions.get(mode, mode_instructions["balanced"])}

ORIGINAL RESUME:
{resume_text}

TARGET JOB DESCRIPTION:
{jd_text}

USER'S CONFIRMED SKILLS (can be added): {skills_str if skills_str else "None provided"}

Please:
1. First parse the resume to understand its structure
2. Identify keyword gaps with the JD
3. Rewrite each section that needs improvement
4. Generate a diff summary of changes
5. Validate that no fabrication occurred

Provide the COMPLETE optimized resume text, followed by a summary of changes."""

        response = self.invoke(prompt)
        
        return {
            "agent": self.name,
            "mode": mode,
            "optimized_content": response,
            "original_length": len(resume_text),
        }
    
    def rewrite_section(
        self,
        section_name: str,
        section_content: str,
        keywords: List[str],
        context: str = ""
    ) -> str:
        """
        Rewrite a specific resume section.
        
        Args:
            section_name: Name of section to rewrite
            section_content: Original section content
            keywords: Keywords to incorporate
            context: Additional context (e.g., job title)
            
        Returns:
            Rewritten section
        """
        prompt = f"""Rewrite this resume section to incorporate the specified keywords naturally.

SECTION: {section_name}
ORIGINAL CONTENT:
{section_content}

KEYWORDS TO INCORPORATE: {', '.join(keywords)}

CONTEXT: {context if context else "General optimization"}

Rules:
- Keep the same factual content
- Only rephrase, don't add new claims
- Incorporate keywords naturally (no stuffing)
- Maintain professional tone

Provide the rewritten section only."""

        return self.invoke(prompt)
    
    def extract_sections(self, resume_text: str) -> Dict[str, str]:
        """
        Extract individual sections from a resume.
        
        Args:
            resume_text: Full resume text
            
        Returns:
            Dict mapping section names to content
        """
        prompt = f"""Parse this resume and extract each section.

RESUME:
{resume_text}

Return a structured breakdown with:
- Contact/Header
- Summary/Objective (if present)
- Experience
- Education
- Skills
- Projects (if present)
- Certifications (if present)

For each section, provide the exact content as it appears."""

        return self.invoke(prompt)
