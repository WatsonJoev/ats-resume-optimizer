"""LLM Factory for creating language model instances."""

from typing import Optional, List
from langchain_openai import ChatOpenAI

from .settings import Settings


class LLMFactory:
    """Factory for creating LLM instances with OpenRouter."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the LLM factory.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._validate_api_key()
    
    def _validate_api_key(self):
        """Check if API key is configured."""
        if not self.settings.openrouter_api_key:
            print("[WARNING] OPENROUTER_API_KEY not found in environment.")
            print("Please set it in your .env file:")
            print("  OPENROUTER_API_KEY=your_key_here")
    
    def create_llm(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ChatOpenAI:
        """
        Create a ChatOpenAI instance configured for OpenRouter.
        
        Args:
            model_name: Model to use (default from settings)
            temperature: Temperature setting (default from settings)
            
        Returns:
            Configured ChatOpenAI instance
        """
        model = model_name or self.settings.default_model
        print(f"[LLM Factory] Creating LLM with model: {model}")
        
        return ChatOpenAI(
            model=model,
            temperature=temperature or self.settings.default_temperature,
            openai_api_key=self.settings.openrouter_api_key,
            openai_api_base=self.settings.openrouter_base_url,
        )
    
    def get_fallback_model(self, current_model: str) -> Optional[str]:
        """
        Get the next fallback model after the current one.
        Prioritizes free models, then cheapest paid models.
        
        Args:
            current_model: Currently used model
            
        Returns:
            Next fallback model or None if no more fallbacks
        """
        try:
            current_index = self.settings.fallback_models.index(current_model)
            if current_index + 1 < len(self.settings.fallback_models):
                next_model = self.settings.fallback_models[current_index + 1]
                print(f"[LLM Factory] Falling back from {current_model} to {next_model}")
                return next_model
        except ValueError:
            # Current model not in fallback list, return first fallback
            if self.settings.fallback_models:
                first_fallback = self.settings.fallback_models[0]
                print(f"[LLM Factory] Model {current_model} not in fallback list, using {first_fallback}")
                return first_fallback
        
        print(f"[LLM Factory] No more fallback models available after {current_model}")
        return None
    
    def get_free_models(self) -> List[str]:
        """Get list of free models from fallback list."""
        return [m for m in self.settings.fallback_models if ":free" in m]
    
    def get_cheapest_paid_model(self) -> Optional[str]:
        """Get the cheapest paid model from fallback list."""
        paid_models = [m for m in self.settings.fallback_models if ":free" not in m]
        return paid_models[0] if paid_models else None
