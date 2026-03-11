"""
Master Agent
=============
Reviews and approves optimized resumes.
Ensures quality, accuracy, and no fabrication.
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

from .base import BaseAgent, AgentRegistry
from tools.resume_tools import validate_resume_changes, generate_resume_diff
from tools.ats_tools import calculate_ats_score


@AgentRegistry.register
class MasterAgent(BaseAgent):
    """
    Master agent that reviews and approves resume optimizations.
    
    Responsibilities:
    - Review optimized resumes for quality
    - Ensure no fabricated content
    - Verify ATS score improvement
    - Provide final approval or revision requests
    """
    
    name = "master"
    description = "Reviews and approves resume optimizations for quality and accuracy"
    
    def __init__(
        self,
        ats_agent=None,
        resume_agent=None,
        **kwargs
    ):
        """
        Initialize the master agent.
        
        Args:
            ats_agent: ATS Evaluation agent instance
            resume_agent: Resume Handling agent instance
            **kwargs: Additional arguments for BaseAgent
        """
        self._ats_agent = ats_agent
        self._resume_agent = resume_agent
        super().__init__(**kwargs)
    
    def set_agents(self, ats_agent=None, resume_agent=None):
        """Set the subordinate agents."""
        if ats_agent:
            self._ats_agent = ats_agent
        if resume_agent:
            self._resume_agent = resume_agent
    
    def _get_default_tools(self) -> List[BaseTool]:
        """Get master agent tools."""
        return [
            validate_resume_changes,
            generate_resume_diff,
            calculate_ats_score,
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the master agent system prompt."""
        return """You are the MASTER REVIEW AGENT responsible for quality control of resume optimizations.
You are the final gatekeeper before any optimized resume is delivered to the user.

YOUR PRIMARY RESPONSIBILITIES:
1. Review optimized resumes for quality and accuracy
2. Ensure NO fabricated content exists
3. Verify the optimization improves ATS score
4. Approve or request revisions with specific feedback

QUALITY CHECKLIST - ALL MUST PASS:
□ No fabricated experience or achievements
□ No invented quantifiable claims (percentages, dollar amounts)
□ No changed job titles, companies, or dates
□ Contact information preserved
□ Chronology intact and logical
□ No keyword stuffing (keywords appear naturally)
□ Professional tone maintained
□ ATS-friendly formatting preserved

REVIEW PROCESS:
1. Use 'validate_resume_changes' to check for fabrication
2. Use 'generate_resume_diff' to see what changed
3. Use 'calculate_ats_score' to verify improvement
4. Make approval decision based on checklist

APPROVAL DECISIONS:
- APPROVED: All checks pass, ATS score improved, changes are appropriate
- NEEDS_REVISION: Some issues found, provide specific feedback
- REJECTED: Serious issues (fabrication, major errors), explain why

WHEN PROVIDING FEEDBACK:
- Be specific about what needs to change
- Reference exact sections or phrases
- Explain why the change is needed
- Suggest how to fix the issue

OUTPUT FORMAT:
Your review should include:
1. DECISION: APPROVED / NEEDS_REVISION / REJECTED
2. ATS SCORE: Before → After
3. CHECKLIST RESULTS: Pass/Fail for each item
4. ISSUES FOUND: List any problems
5. RECOMMENDATIONS: Specific fixes if needed
6. FINAL NOTES: Summary of the review

Be strict but fair. The goal is a resume that is both optimized AND truthful."""
    
    def review(
        self,
        original_resume: str,
        optimized_resume: str,
        jd_text: str,
        user_skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Review an optimized resume.
        
        Args:
            original_resume: Original resume text
            optimized_resume: Optimized resume text
            jd_text: Target job description
            user_skills: User's confirmed skills
            
        Returns:
            Dict with review results and decision
        """
        skills_str = ", ".join(user_skills) if user_skills else ""
        
        prompt = f"""Review this resume optimization for quality and accuracy.

ORIGINAL RESUME:
{original_resume}

OPTIMIZED RESUME:
{optimized_resume}

JOB DESCRIPTION:
{jd_text}

USER'S CONFIRMED SKILLS: {skills_str if skills_str else "None provided"}

Please:
1. Validate that no fabrication occurred
2. Generate a diff to see changes
3. Calculate ATS scores before and after
4. Run through the quality checklist
5. Make your approval decision

Provide a comprehensive review with your decision and reasoning."""

        response = self.invoke(prompt)
        
        # Parse decision from response
        decision = "NEEDS_REVISION"  # Default
        if "APPROVED" in response.upper() and "NEEDS_REVISION" not in response.upper():
            decision = "APPROVED"
        elif "REJECTED" in response.upper():
            decision = "REJECTED"
        
        return {
            "agent": self.name,
            "decision": decision,
            "review": response,
        }
    
    def single_shot_optimize(
        self,
        resume_text: str,
        jd_text: str,
        user_skills: Optional[List[str]] = None,
        mode: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Single-shot optimization without review cycles.
        
        Args:
            resume_text: Original resume text
            jd_text: Target job description
            user_skills: User's confirmed skills
            mode: Optimization mode
            
        Returns:
            Dict with final results
        """
        if not self._ats_agent or not self._resume_agent:
            return {
                "error": "ATS and Resume agents must be set before optimization",
                "decision": "ERROR"
            }
        
        print("[Master] Starting single-shot optimization...")
        
        # Step 1: ATS Evaluation
        print("[Master] Analyzing job description and resume...")
        ats_result = self._ats_agent.evaluate(jd_text, resume_text, user_skills)
        
        # Step 2: Resume Optimization
        print("[Master] Optimizing resume for ATS 90+ score...")
        optimization_result = self._resume_agent.optimize_resume(
            resume_text, jd_text, user_skills, mode
        )
        optimized_resume = optimization_result["optimized_content"]
        
        # Step 3: Quick validation
        print("[Master] Validating optimized resume...")
        validation_prompt = f"""Quick validate this optimized resume for ATS optimization:

ORIGINAL RESUME:
{resume_text[:1000]}...

OPTIMIZED RESUME:
{optimized_resume[:1000]}...

JOB DESCRIPTION:
{jd_text[:1000]}...

Check for:
1. No fabricated content
2. Natural keyword integration
3. Professional formatting preserved
4. Target 90+ ATS score

Respond with: APPROVED or NEEDS_REVISION + brief reason if any issues."""
        
        validation = self.invoke(validation_prompt)
        decision = "APPROVED" if "APPROVED" in validation.upper() else "NEEDS_REVISION"
        
        print(f"[Master] Validation: {decision}")
        
        return {
            "decision": decision,
            "final_resume": optimized_resume,
            "iterations": 1,
            "validation": validation,
            "original_resume": resume_text,
            "ats_analysis": ats_result["analysis"][:500] + "..." if "analysis" in ats_result else "ATS analysis complete"
        }
