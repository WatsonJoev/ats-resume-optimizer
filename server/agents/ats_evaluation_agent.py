"""
ATS Evaluation Agent
=====================
Analyzes job descriptions and evaluates resume-to-job alignment.
Provides detailed ATS scoring and keyword gap analysis.
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentRegistry
from tools.ats_tools import (
    analyze_job_description,
    calculate_ats_score,
    identify_keyword_gaps,
    generate_keyword_map,
)


@AgentRegistry.register
class ATSEvaluationAgent(BaseAgent):
    """
    Agent specialized in ATS (Applicant Tracking System) evaluation.
    
    Responsibilities:
    - Analyze job descriptions to extract requirements
    - Calculate ATS compatibility scores
    - Identify keyword gaps between JD and resume
    - Generate keyword placement recommendations
    """
    
    name = "ats_evaluation"
    description = "Evaluates resume-to-job alignment and calculates ATS scores"
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Get ATS evaluation tools."""
        return [
            analyze_job_description,
            calculate_ats_score,
            identify_keyword_gaps,
            generate_keyword_map,
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the ATS evaluation agent system prompt."""
        return """You are an ADVANCED ATS EVALUATION AGENT specialized in analyzing job descriptions 
and optimizing resumes for 90+ ATS scores in a single pass.

YOUR PRIMARY RESPONSIBILITIES:
1. Extract key requirements, skills, and keywords from job descriptions
2. Calculate ATS compatibility scores targeting 90+ 
3. Identify keyword gaps and provide precise optimization recommendations
4. Generate keyword maps for maximum ATS optimization
2. Calculate ATS compatibility scores using a weighted rubric
3. Identify keyword gaps that could cause ATS rejection
4. Recommend where to place missing keywords in the resume

EVALUATION CRITERIA (Weighted Scoring):
- Keyword Match (35%): Percentage of JD keywords found in resume
- Skills Alignment (25%): Technical and soft skills match
- Experience Relevance (20%): Role responsibilities alignment
- Formatting (10%): ATS-safe structure (headers, bullets, no tables)
- Completeness (10%): Required sections present (contact, summary, experience, education, skills)

WHEN ANALYZING A JOB DESCRIPTION:
1. First use 'analyze_job_description' to extract structured requirements
2. Identify required vs preferred qualifications
3. Note specific technologies, tools, and methodologies mentioned
4. Extract years of experience requirements
5. Identify industry-specific terminology

WHEN EVALUATING A RESUME:
1. Use 'calculate_ats_score' to get the baseline score
2. Use 'identify_keyword_gaps' to find missing keywords
3. Use 'generate_keyword_map' to recommend where keywords should go
4. Provide actionable recommendations for improvement

IMPORTANT RULES:
- Be specific about which keywords are missing and where they should go
- Prioritize high-impact keywords (those mentioned multiple times in JD)
- Flag potential ATS formatting issues (tables, graphics, unusual fonts)
- Never recommend adding skills the candidate doesn't have
- Focus on rephrasing existing experience to match JD language

OUTPUT FORMAT:
When providing analysis, structure your response as:
1. Overall ATS Score and Risk Level
2. Keyword Analysis (matched, missing, partial)
3. Section-by-Section Recommendations
4. Priority Actions (top 3-5 changes to make)

Be thorough but concise. Focus on actionable insights."""
    
    def evaluate(
        self, 
        jd_text: str, 
        resume_text: str,
        user_skills: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform complete ATS evaluation.
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            user_skills: Additional skills the user has
            
        Returns:
            Dict with evaluation results
        """
        skills_str = ", ".join(user_skills) if user_skills else ""
        
        prompt = f"""Perform a complete ATS evaluation for this job application.

JOB DESCRIPTION:
{jd_text}

RESUME:
{resume_text}

USER'S ADDITIONAL SKILLS: {skills_str if skills_str else "None provided"}

Please:
1. Analyze the job description to extract requirements
2. Calculate the ATS score
3. Identify keyword gaps
4. Generate a keyword placement map
5. Provide specific, actionable recommendations

Structure your response with clear sections for each analysis component."""

        response = self.invoke(prompt)
        
        return {
            "agent": self.name,
            "analysis": response,
            "jd_length": len(jd_text),
            "resume_length": len(resume_text),
        }
    
    def quick_score(self, jd_text: str, resume_text: str) -> str:
        """
        Get a quick ATS score without full analysis.
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            
        Returns:
            Quick score summary
        """
        prompt = f"""Calculate the ATS score for this resume against the job description.
Provide only:
1. Overall score (0-100)
2. Top 3 missing keywords
3. One-sentence recommendation

JOB DESCRIPTION:
{jd_text[:2000]}

RESUME:
{resume_text[:3000]}"""

        return self.invoke(prompt)
