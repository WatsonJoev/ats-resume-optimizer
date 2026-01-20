"""Base agent class and registry for the ATS Resume Optimizer multi-agent system."""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings, LLMFactory


class BaseAgent(ABC):
    """
    Base class for all agents in the ATS Resume Optimizer system.
    
    Provides common functionality for:
    - LLM initialization and management
    - Tool registration
    - Message history
    - Retry logic with model fallback
    """
    
    # Class-level attributes to be overridden by subclasses
    name: str = "base_agent"
    description: str = "Base agent class"
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        tools: Optional[List[BaseTool]] = None,
    ):
        """
        Initialize the base agent.
        
        Args:
            model_name: LLM model to use (default from settings)
            temperature: LLM temperature (0.0-1.0)
            tools: List of tools available to the agent
        """
        self.settings = get_settings()
        self.llm_factory = LLMFactory(self.settings)
        
        self.model_name = model_name or self.settings.default_model
        self.temperature = temperature
        
        # Initialize LLM
        self.llm = self.llm_factory.create_llm(
            model_name=self.model_name,
            temperature=self.temperature,
        )
        
        # Initialize tools
        self.tools = tools or self._get_default_tools()
        
        # Chat history for conversational context
        self.chat_history: List[HumanMessage | AIMessage] = []
        
        # Create the agent
        self.agent = self._create_agent()
    
    @abstractmethod
    def _get_default_tools(self) -> List[BaseTool]:
        """
        Get the default tools for this agent.
        Must be implemented by subclasses.
        
        Returns:
            List of tools
        """
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Must be implemented by subclasses.
        
        Returns:
            System prompt string
        """
        pass
    
    def _create_agent(self):
        """Create the LangGraph agent."""
        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self._get_system_prompt(),
        )
    
    def _switch_model(self, new_model: str):
        """
        Switch to a different model.
        
        Args:
            new_model: New model name
        """
        self.model_name = new_model
        self.llm = self.llm_factory.create_llm(
            model_name=new_model,
            temperature=self.temperature,
        )
        self.agent = self._create_agent()
    
    def invoke(self, message: str, use_history: bool = False) -> str:
        """
        Invoke the agent with a message.
        
        Args:
            message: User message
            use_history: Whether to include chat history
            
        Returns:
            Agent response
        """
        from openai import RateLimitError
        import time
        
        messages = []
        if use_history:
            messages.extend(self.chat_history)
        messages.append(HumanMessage(content=message))
        
        last_error = None
        
        for attempt in range(self.settings.max_retries + 1):
            try:
                result = self.agent.invoke({"messages": messages})
                response = result["messages"][-1].content
                
                # Update history if using it
                if use_history:
                    self.chat_history.append(HumanMessage(content=message))
                    self.chat_history.append(AIMessage(content=response))
                
                return response
                
            except RateLimitError as e:
                last_error = e
                if attempt < self.settings.max_retries:
                    wait_time = (attempt + 1) * self.settings.retry_delay_base
                    print(f"[!] Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Try fallback model
                    next_model = self.llm_factory.get_fallback_model(self.model_name)
                    if next_model:
                        print(f"[!] Switching to fallback model: {next_model}")
                        self._switch_model(next_model)
                        result = self.agent.invoke({"messages": messages})
                        response = result["messages"][-1].content
                        
                        if use_history:
                            self.chat_history.append(HumanMessage(content=message))
                            self.chat_history.append(AIMessage(content=response))
                        
                        return response
                    else:
                        raise
            except Exception as e:
                last_error = e
                print(f"[!] Error invoking agent: {e}")
                raise
        
        raise last_error
    
    def invoke_simple(self, message: str) -> str:
        """
        Simple LLM invocation without agent/tools.
        
        Args:
            message: User message
            
        Returns:
            LLM response
        """
        response = self.llm.invoke([HumanMessage(content=message)])
        return response.content
    
    def clear_history(self):
        """Clear the chat history."""
        self.chat_history = []
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dict with agent info
        """
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model_name,
            "tools": [t.name for t in self.tools],
            "history_length": len(self.chat_history),
        }


class AgentRegistry:
    """
    Registry for managing multiple agents.
    Allows dynamic agent creation and lookup.
    """
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _instances: Dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
        """
        Register an agent class.
        Can be used as a decorator.
        
        Args:
            agent_class: Agent class to register
            
        Returns:
            The agent class (for decorator use)
        """
        cls._agents[agent_class.name] = agent_class
        return agent_class
    
    @classmethod
    def get_agent_class(cls, name: str) -> Optional[Type[BaseAgent]]:
        """
        Get an agent class by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent class or None
        """
        return cls._agents.get(name)
    
    @classmethod
    def create_agent(
        cls, 
        name: str, 
        **kwargs
    ) -> Optional[BaseAgent]:
        """
        Create an agent instance.
        
        Args:
            name: Agent name
            **kwargs: Arguments to pass to agent constructor
            
        Returns:
            Agent instance or None
        """
        agent_class = cls._agents.get(name)
        if agent_class:
            instance = agent_class(**kwargs)
            cls._instances[name] = instance
            return instance
        return None
    
    @classmethod
    def get_instance(cls, name: str) -> Optional[BaseAgent]:
        """
        Get an existing agent instance.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None
        """
        return cls._instances.get(name)
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(cls._agents.keys())
    
    @classmethod
    def list_instances(cls) -> List[str]:
        """
        List all active agent instances.
        
        Returns:
            List of instance names
        """
        return list(cls._instances.keys())
