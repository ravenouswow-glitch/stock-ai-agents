from typing import List, Dict, Any
from interfaces.agent import IAgent, AgentInput, AgentOutput
from interfaces.data_provider import IDataProvider
from interfaces.output_handler import IOutputHandler
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisResult:
    ticker: str
    success: bool
    outputs: Dict[str, AgentOutput]
    error: str = None

class FullAnalysisPipeline:
    def __init__(self, data_providers: List[IDataProvider], agents: List[IAgent], output_handler: IOutputHandler):
        self.data_providers = data_providers
        self.agents = agents
        self.output_handler = output_handler
    
    async def run(self, ticker: str, question: str = "Technical outlook") -> AnalysisResult:
        try:
            price_data = None
            technical_data = None
            news_data = []
            
            for provider in self.data_providers:
                if price_data is None:
                    price_data = provider.get_price(ticker)
                if technical_data is None:
                    technical_data = provider.get_technicals(ticker)
                news_data.extend(provider.get_news(ticker, max_items=5))
            
            if not technical_data:
                return AnalysisResult(ticker=ticker, success=False, outputs={}, error="Could not fetch technical data")
            
            agent_input = AgentInput(
                ticker=ticker,
                question=question,
                price_data=price_data,
                technical_data=technical_data,
                news_data=news_data,
                context={}
            )
            
            outputs = {}
            for agent in self.agents:
                print(f"[{agent.name}] Processing...")
                output = await agent.execute(agent_input)
                outputs[agent.name] = output
                agent_input.context[f"{agent.name.lower()}_analysis"] = output.content
            
            return AnalysisResult(ticker=ticker, success=True, outputs=outputs)
            
        except Exception as e:
            return AnalysisResult(ticker=ticker, success=False, outputs={}, error=str(e))