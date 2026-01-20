"""Application settings and configuration for ATS Resume Optimizer."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT.parent / "data"
BASELINE_DIR = DATA_DIR / "baseline"
JOBS_DIR = DATA_DIR / "jobs"


@dataclass
class Settings:
    """Application settings."""
    
    # API Configuration
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Default model settings - must support tool/function calling
    # Note: Many free models don't support tools, so we use cheap paid models that do
    default_model: str = field(default_factory=lambda: os.getenv(
        "DEFAULT_MODEL", 
        "google/gemini-2.0-flash-001"  # Cheap, supports tools, reliable
    ))
    default_temperature: float = 0.7
    
    # Fallback models that SUPPORT TOOL USE (function calling)
    # Important: Free models often don't support tools, so we prioritize cheap paid models
    fallback_models: List[str] = field(default_factory=lambda: [
        # Cheapest models that support tool use
        "google/gemini-2.0-flash-001",               # ~$0.0001/1K - supports tools
        "google/gemini-flash-1.5",                   # ~$0.000075/1K - supports tools
        "openai/gpt-4o-mini",                        # ~$0.00015/1K - supports tools
        "anthropic/claude-3-haiku",                  # ~$0.00025/1K - supports tools
        "mistralai/mistral-small-24b-instruct-2501", # ~$0.0001/1K - supports tools
    ])
    
    # Retry settings
    max_retries: int = 2
    retry_delay_base: int = 5  # seconds
    
    # Server settings
    server_host: str = "127.0.0.1"
    server_port: int = 5002
    
    # Paths
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    baseline_dir: Path = field(default_factory=lambda: BASELINE_DIR)
    jobs_dir: Path = field(default_factory=lambda: JOBS_DIR)
    
    # ATS Scoring Weights (must sum to 100)
    ats_weights: dict = field(default_factory=lambda: {
        "keyword_match": 35,      # % of JD keywords found in resume
        "skills_alignment": 25,   # Hard skills + tools match
        "experience_relevance": 20,  # Role responsibilities alignment
        "formatting": 10,         # ATS-safe structure
        "completeness": 10,       # Contact info, sections present
    })
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """Validate required settings."""
        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. "
                "Please set it in your .env file."
            )
        return True


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
