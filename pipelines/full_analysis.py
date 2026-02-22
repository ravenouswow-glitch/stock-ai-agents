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
            
            # Try each data provider
            for provider in self.data_providers:
                provider_name = provider.__class__.__name__
                print(f"Trying {provider_name}...")
                
                if price_data is None:
                    try:
                        price_data = provider.get_price(ticker)
                        if price_
                            print(f"✓ Got price from {provider_name}")
                    except Exception as e:
                        print(f"✗ Price failed from {provider_name}: {e}")
                
                if technical_data is None:
                    try:
                        technical_data = provider.get_technicals(ticker)
                        if technical_
                            print(f"✓ Got technicals from {provider_name}")
                    except Exception as e:
                        print(f"✗ Technicals failed from {provider_name}: {e}")
                
                try:
                    provider_news = provider.get_news(ticker, max_items=5)
                    if provider_news:
                        news_data.extend(provider_news)
                        print(f"✓ Got {len(provider_news)} news from {provider_name}")
                except Exception as e:
                    print(f"✗ News failed from {provider_name}: {e}")
            
            # Check if we got data
            if not technical_
                error_msg = "Could not fetch technical data from any source"
                print(f"ERROR: {error_msg}")
                return AnalysisResult(
                    ticker=ticker,
                    success=False,
                    outputs={},
                    error=error_msg
                )
            
            # Build agent input
            agent_input = AgentInput(
                ticker=ticker,
                question=question,
                price_data=price_data,
                technical_data=technical_data,
                news_data=news_data,
                context={}
            )
            
            # Run agents
            outputs = {}
            for agent in self.agents:
                print(f"[{agent.name}] Processing...")
                try:
                    output = await agent.execute(agent_input)
                    outputs[agent.name] = output
                    agent_input.context[f"{agent.name.lower()}_analysis"] = output.content
                    print(f"✓ {agent.name} complete")
                except Exception as e:
                    print(f"✗ {agent.name} failed: {e}")
                    outputs[agent.name] = AgentOutput(
                        agent_name=agent.name,
                        content=f"Error: {str(e)}",
                        confidence=0,
                        metadata={},
                        success=False
                    )
            
            return AnalysisResult(
                ticker=ticker,
                success=True,
                outputs=outputs
            )
            
        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            return AnalysisResult(
                ticker=ticker,
                success=False,
                outputs={},
                error=error_msg
            )