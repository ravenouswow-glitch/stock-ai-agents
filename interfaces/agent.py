from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AgentInput:
    ticker: str
    question: str
    price_data: Any
    technical_data: Any
    news_data: Any
    context: Dict[str, Any]

@dataclass
class AgentOutput:
    agent_name: str
    content: str
    confidence: int
    metadata: Dict[str, Any]
    success: bool

class IAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def model(self) -> str:
        pass
    
    @abstractmethod
    def build_prompt(self, input: AgentInput) -> str:
        pass
    
    @abstractmethod
    def parse_response(self, response: str) -> AgentOutput:
        pass
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        try:
            prompt = self.build_prompt(input)
            response = await self._call_groq(prompt)
            return self.parse_response(response)
        except Exception as e:
            return AgentOutput(
                agent_name=self.name,
                content=f"Error: {str(e)}",
                confidence=0,
                metadata={},
                success=False
            )
    
    async def _call_groq(self, prompt: str) -> str:
        from groq import AsyncGroq
        from config import Config
        
        client = AsyncGroq(api_key=Config.GROQ_API_KEY)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content