"""
ATS Scoring Service
====================
Implements a weighted rubric for scoring resume-to-job alignment.

Scoring Categories (default weights):
- Keyword Match: 35%
- Skills Alignment: 25%
- Experience Relevance: 20%
- Formatting: 10%
- Completeness: 10%
"""

import re
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class KeywordAnalysis:
    """Results of keyword analysis."""
    matched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    partial: List[str] = field(default_factory=list)
    match_percentage: float = 0.0


@dataclass
class SectionScore:
    """Score for a specific section."""
    name: str
    score: float  # 0-100
    max_score: float = 100.0
    feedback: str = ""


@dataclass
class ATSReport:
    """Complete ATS analysis report."""
    overall_score: float  # 0-100
    keyword_analysis: KeywordAnalysis = field(default_factory=KeywordAnalysis)
    section_scores: Dict[str, SectionScore] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    keyword_map: Dict[str, List[str]] = field(default_factory=dict)  # JD requirement -> resume sections


class ATSScorer:
    """
    ATS Scoring service using weighted rubric.
    
    This provides a deterministic baseline score that agents can use
    and refine with their analysis.
    """
    
    # Common technical skills and keywords
    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "git", "ci/cd", "jenkins", "github actions", "gitlab",
        "agile", "scrum", "jira", "confluence",
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "rest api", "graphql", "microservices", "serverless",
    }
    
    # Common soft skills
    SOFT_SKILLS = {
        "leadership", "communication", "teamwork", "problem-solving",
        "analytical", "creative", "detail-oriented", "self-motivated",
        "collaborative", "adaptable", "organized", "proactive",
    }
    
    # Required resume sections
    REQUIRED_SECTIONS = {
        "contact", "summary", "experience", "education", "skills"
    }
    
    def __init__(self, weights: Dict[str, int] = None):
        """
        Initialize the ATS scorer.
        
        Args:
            weights: Custom scoring weights (must sum to 100)
        """
        self.weights = weights or {
            "keyword_match": 35,
            "skills_alignment": 25,
            "experience_relevance": 20,
            "formatting": 10,
            "completeness": 10,
        }
        
        # Validate weights sum to 100
        total = sum(self.weights.values())
        if total != 100:
            raise ValueError(f"Weights must sum to 100, got {total}")
    
    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Set of extracted keywords (lowercase)
        """
        # Normalize text
        text_lower = text.lower()
        
        # Extract multi-word technical terms first
        keywords = set()
        
        # Check for known technical skills
        for skill in self.TECH_SKILLS:
            if skill in text_lower:
                keywords.add(skill)
        
        # Check for soft skills
        for skill in self.SOFT_SKILLS:
            if skill in text_lower:
                keywords.add(skill)
        
        # Extract capitalized terms (likely proper nouns/technologies)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z0-9+#]*(?:\s+[A-Z][a-zA-Z0-9+#]*)*\b', text)
        for term in capitalized:
            if len(term) > 2:  # Skip short acronyms
                keywords.add(term.lower())
        
        # Extract years of experience patterns
        exp_patterns = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', text_lower)
        for years in exp_patterns:
            keywords.add(f"{years}+ years")
        
        return keywords
    
    def extract_jd_requirements(self, jd_text: str) -> Dict[str, List[str]]:
        """
        Extract structured requirements from job description.
        
        Args:
            jd_text: Job description text
            
        Returns:
            Dict with categorized requirements
        """
        requirements = {
            "required_skills": [],
            "preferred_skills": [],
            "experience": [],
            "education": [],
            "responsibilities": [],
        }
        
        text_lower = jd_text.lower()
        lines = jd_text.split('\n')
        
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Detect section headers
            if any(kw in line_lower for kw in ["required", "must have", "requirements"]):
                current_section = "required_skills"
            elif any(kw in line_lower for kw in ["preferred", "nice to have", "bonus"]):
                current_section = "preferred_skills"
            elif any(kw in line_lower for kw in ["experience", "background"]):
                current_section = "experience"
            elif any(kw in line_lower for kw in ["education", "degree", "qualification"]):
                current_section = "education"
            elif any(kw in line_lower for kw in ["responsibilities", "duties", "you will"]):
                current_section = "responsibilities"
            elif line.strip().startswith(('-', '•', '*', '·')) and current_section:
                # Bullet point in current section
                clean_line = re.sub(r'^[-•*·]\s*', '', line.strip())
                if clean_line:
                    requirements[current_section].append(clean_line)
        
        return requirements
    
    def analyze_keywords(
        self, 
        jd_text: str, 
        resume_text: str
    ) -> KeywordAnalysis:
        """
        Analyze keyword match between JD and resume.
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            
        Returns:
            KeywordAnalysis with matched/missing/partial keywords
        """
        jd_keywords = self.extract_keywords(jd_text)
        resume_keywords = self.extract_keywords(resume_text)
        resume_text_lower = resume_text.lower()
        
        matched = []
        missing = []
        partial = []
        
        for keyword in jd_keywords:
            if keyword in resume_keywords:
                matched.append(keyword)
            elif any(word in resume_text_lower for word in keyword.split()):
                partial.append(keyword)
            else:
                missing.append(keyword)
        
        total = len(jd_keywords) if jd_keywords else 1
        match_pct = (len(matched) + 0.5 * len(partial)) / total * 100
        
        return KeywordAnalysis(
            matched=sorted(matched),
            missing=sorted(missing),
            partial=sorted(partial),
            match_percentage=round(match_pct, 1)
        )
    
    def score_keyword_match(
        self, 
        keyword_analysis: KeywordAnalysis
    ) -> Tuple[float, str]:
        """
        Score keyword match (0-100).
        
        Args:
            keyword_analysis: Results from analyze_keywords
            
        Returns:
            Tuple of (score, feedback)
        """
        score = keyword_analysis.match_percentage
        
        if score >= 80:
            feedback = "Excellent keyword alignment with job description."
        elif score >= 60:
            feedback = "Good keyword coverage. Consider adding missing technical terms."
        elif score >= 40:
            feedback = "Moderate keyword match. Resume needs more JD-specific terminology."
        else:
            feedback = "Low keyword match. Significant alignment needed."
        
        return score, feedback
    
    def score_skills_alignment(
        self, 
        jd_text: str, 
        resume_text: str,
        user_skills: List[str] = None
    ) -> Tuple[float, str]:
        """
        Score skills alignment (0-100).
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            user_skills: Additional user-provided skills
            
        Returns:
            Tuple of (score, feedback)
        """
        jd_skills = self.extract_keywords(jd_text) & (self.TECH_SKILLS | self.SOFT_SKILLS)
        resume_skills = self.extract_keywords(resume_text) & (self.TECH_SKILLS | self.SOFT_SKILLS)
        
        # Add user-provided skills
        if user_skills:
            for skill in user_skills:
                resume_skills.add(skill.lower())
        
        if not jd_skills:
            return 100.0, "No specific skills requirements detected."
        
        matched = jd_skills & resume_skills
        score = len(matched) / len(jd_skills) * 100
        
        missing = jd_skills - resume_skills
        if missing:
            feedback = f"Missing skills: {', '.join(sorted(missing)[:5])}"
            if len(missing) > 5:
                feedback += f" (+{len(missing) - 5} more)"
        else:
            feedback = "All required skills present in resume."
        
        return round(score, 1), feedback
    
    def score_formatting(self, resume_text: str) -> Tuple[float, str]:
        """
        Score ATS-friendly formatting (0-100).
        
        Args:
            resume_text: Resume text
            
        Returns:
            Tuple of (score, feedback)
        """
        score = 100.0
        issues = []
        
        # Check for common ATS issues
        lines = resume_text.split('\n')
        
        # Check line length (very long lines can be problematic)
        long_lines = sum(1 for line in lines if len(line) > 150)
        if long_lines > 5:
            score -= 10
            issues.append("Some lines are very long")
        
        # Check for bullet points (good for ATS)
        has_bullets = any(line.strip().startswith(('-', '•', '*', '·')) for line in lines)
        if not has_bullets:
            score -= 15
            issues.append("No bullet points detected")
        
        # Check for section headers
        header_patterns = ['experience', 'education', 'skills', 'summary', 'projects']
        found_headers = sum(1 for h in header_patterns if h in resume_text.lower())
        if found_headers < 3:
            score -= 20
            issues.append("Missing clear section headers")
        
        # Check for contact info patterns
        has_email = bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', resume_text))
        has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text))
        if not has_email:
            score -= 10
            issues.append("No email detected")
        if not has_phone:
            score -= 5
            issues.append("No phone number detected")
        
        feedback = "Good ATS-friendly formatting." if not issues else "; ".join(issues)
        return max(0, score), feedback
    
    def score_completeness(self, resume_text: str) -> Tuple[float, str]:
        """
        Score resume completeness (0-100).
        
        Args:
            resume_text: Resume text
            
        Returns:
            Tuple of (score, feedback)
        """
        text_lower = resume_text.lower()
        
        found_sections = set()
        section_keywords = {
            "contact": ["email", "@", "phone", "linkedin"],
            "summary": ["summary", "objective", "profile", "about"],
            "experience": ["experience", "work history", "employment"],
            "education": ["education", "degree", "university", "college"],
            "skills": ["skills", "technologies", "tools", "competencies"],
        }
        
        for section, keywords in section_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_sections.add(section)
        
        score = len(found_sections) / len(self.REQUIRED_SECTIONS) * 100
        
        missing = self.REQUIRED_SECTIONS - found_sections
        if missing:
            feedback = f"Missing sections: {', '.join(sorted(missing))}"
        else:
            feedback = "All essential sections present."
        
        return round(score, 1), feedback
    
    def calculate_score(
        self,
        jd_text: str,
        resume_text: str,
        user_skills: List[str] = None
    ) -> ATSReport:
        """
        Calculate complete ATS score with detailed analysis.
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            user_skills: Additional user-provided skills
            
        Returns:
            Complete ATSReport
        """
        # Analyze keywords
        keyword_analysis = self.analyze_keywords(jd_text, resume_text)
        
        # Calculate individual scores
        kw_score, kw_feedback = self.score_keyword_match(keyword_analysis)
        skills_score, skills_feedback = self.score_skills_alignment(
            jd_text, resume_text, user_skills
        )
        format_score, format_feedback = self.score_formatting(resume_text)
        complete_score, complete_feedback = self.score_completeness(resume_text)
        
        # Experience relevance is harder to score deterministically
        # We'll use keyword match as a proxy for now (agents will refine)
        exp_score = kw_score * 0.8 + skills_score * 0.2
        exp_feedback = "Based on keyword and skills alignment."
        
        # Store section scores
        section_scores = {
            "keyword_match": SectionScore("Keyword Match", kw_score, feedback=kw_feedback),
            "skills_alignment": SectionScore("Skills Alignment", skills_score, feedback=skills_feedback),
            "experience_relevance": SectionScore("Experience Relevance", exp_score, feedback=exp_feedback),
            "formatting": SectionScore("Formatting", format_score, feedback=format_feedback),
            "completeness": SectionScore("Completeness", complete_score, feedback=complete_feedback),
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            section_scores[key].score * (self.weights[key] / 100)
            for key in self.weights
        )
        
        # Generate recommendations
        recommendations = []
        if keyword_analysis.missing:
            top_missing = keyword_analysis.missing[:5]
            recommendations.append(
                f"Add these keywords: {', '.join(top_missing)}"
            )
        if skills_score < 70:
            recommendations.append(
                "Strengthen skills section with JD-specific technologies"
            )
        if format_score < 80:
            recommendations.append(
                "Improve formatting with clear headers and bullet points"
            )
        if complete_score < 100:
            recommendations.append(
                "Add missing resume sections for completeness"
            )
        
        # Risk flags
        risk_flags = []
        if overall_score < 50:
            risk_flags.append("Low ATS score - significant optimization needed")
        if len(keyword_analysis.missing) > 10:
            risk_flags.append("Many missing keywords - may not pass initial ATS filter")
        
        return ATSReport(
            overall_score=round(overall_score, 1),
            keyword_analysis=keyword_analysis,
            section_scores=section_scores,
            recommendations=recommendations,
            risk_flags=risk_flags,
        )
    
    def to_dict(self, report: ATSReport) -> Dict[str, Any]:
        """Convert ATSReport to dictionary for JSON serialization."""
        return {
            "overall_score": report.overall_score,
            "keyword_analysis": {
                "matched": report.keyword_analysis.matched,
                "missing": report.keyword_analysis.missing,
                "partial": report.keyword_analysis.partial,
                "match_percentage": report.keyword_analysis.match_percentage,
            },
            "section_scores": {
                name: {
                    "score": s.score,
                    "feedback": s.feedback,
                }
                for name, s in report.section_scores.items()
            },
            "recommendations": report.recommendations,
            "risk_flags": report.risk_flags,
        }
