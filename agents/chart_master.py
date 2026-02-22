from interfaces.agent import IAgent, AgentInput, AgentOutput
from datetime import datetime
import re

class ChartMaster(IAgent):
    @property
    def name(self) -> str:
        return "ChartMaster"
    
    @property
    def model(self) -> str:
        from config import Config
        return Config.MODELS['fast']
    
    def build_prompt(self, input: AgentInput) -> str:
        tech = input.technical_data
        if not tech:
            return f"No technical data available for {input.ticker}"
        
        return f"""ChartMaster Technical Analysis for {input.ticker}

DATA:
- Current Price: {tech.symbol}{tech.current:.2f} {tech.currency}
- SMA20: {tech.symbol}{tech.sma20:.2f}
- SMA50: {tech.symbol}{tech.sma50:.2f}
- RSI (14): {tech.rsi:.1f}
- Trend: {tech.trend}

QUESTION: {input.question}

FORMAT:
[TIMESTAMP] {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
[SUMMARY] One line technical bias
[CONFIDENCE] 1-10"""
    
    def parse_response(self, response: str) -> AgentOutput:
        conf_match = re.search(r'\[CONFIDENCE\]\s*(\d+)', response, re.IGNORECASE)
        confidence = int(conf_match.group(1)) if conf_match else 5
        
        return AgentOutput(
            agent_name=self.name,
            content=response,
            confidence=confidence,
            metadata={'type': 'technical'},
            success=True
        )