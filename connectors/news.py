from interfaces.data_provider import IDataProvider, NewsItem
from typing import List
from datetime import datetime

# Try both import methods for compatibility
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

class NewsConnector(IDataProvider):
    """DuckDuckGo News connector"""
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
    
    def is_available(self) -> bool:
        """Check if DDGS is working"""
        try:
            with DDGS() as ddgs:
                list(ddgs.text("test", max_results=1))
            return True
        except:
            return False
    
    def get_price(self, ticker: str):
        """Not implemented - use YahooConnector"""
        return None
    
    def get_technicals(self, ticker: str):
        """Not implemented - use YahooConnector"""
        return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        """Fetch news from DuckDuckGo"""
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
        """Simple keyword-based sentiment analysis"""
        text = text.lower()
        bullish = sum(1 for w in ['beat', 'upgrade', 'growth', 'gain', 'rise', 'profit'] if w in text)
        bearish = sum(1 for w in ['miss', 'downgrade', 'warning', 'loss', 'fall', 'debt'] if w in text)
        
        if bullish > bearish:
            return 'Bullish'
        elif bearish > bullish:
            return 'Bearish'
        return 'Neutral'