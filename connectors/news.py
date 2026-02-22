from interfaces.data_provider import IDataProvider, NewsItem
from typing import List
from ddgs import DDGS
from datetime import datetime

class NewsConnector(IDataProvider):
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
    
    def is_available(self) -> bool:
        try:
            with DDGS() as ddgs:
                list(ddgs.text("test", max_results=1))
            return True
        except:
            return False
    
    def get_price(self, ticker: str):
        return None
    
    def get_technicals(self, ticker: str):
        return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        try:
            with DDGS() as ddgs:
                is_uk = ticker.endswith(".L")
                query = f"{ticker} RNS" if is_uk else f"{ticker} stock news"
                results = list(ddgs.text(query, max_results=self.max_results))
                
                news_items = []
                for item in results[:max_items]:
                    sentiment = self._analyze_sentiment(item.get('body', ''))
                    news_items.append(NewsItem(
                        title=item.get('title', '')[:60],
                        source=item.get('href', '').split('/')[2] if '/' in item.get('href', '') else 'Unknown',
                        date=datetime.now().strftime("%Y-%m-%d"),
                        url=item.get('href', ''),
                        sentiment=sentiment
                    ))
                return news_items
        except Exception as e:
            print(f"News error: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        text = text.lower()
        bullish = sum(1 for w in ['beat', 'upgrade', 'growth', 'gain'] if w in text)
        bearish = sum(1 for w in ['miss', 'downgrade', 'warning', 'loss'] if w in text)
        
        if bullish > bearish:
            return 'Bullish'
        elif bearish > bullish:
            return 'Bearish'
        return 'Neutral'