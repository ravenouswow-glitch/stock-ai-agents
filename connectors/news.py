from interfaces.data_provider import IDataProvider, NewsItem
from typing import List
from datetime import datetime
import requests
import json

class NewsConnector(IDataProvider):
    """News connector with multiple fallbacks"""
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
    
    def is_available(self) -> bool:
        """Check if news service is working"""
        return True  # Always try
    
    def get_price(self, ticker: str):
        return None
    
    def get_technicals(self, ticker: str):
        return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        """Fetch news using multiple methods"""
        
        # Try DuckDuckGo first
        try:
            news = self._fetch_ddgs_news(ticker, max_items)
            if news:
                print(f"✓ Found {len(news)} news via DuckDuckGo")
                return news
        except Exception as e:
            print(f"DuckDuckGo failed: {e}")
        
        # Fallback: Try Google News RSS
        try:
            news = self._fetch_google_news(ticker, max_items)
            if news:
                print(f"✓ Found {len(news)} news via Google News")
                return news
        except Exception as e:
            print(f"Google News failed: {e}")
        
        # Last resort: Return mock news based on ticker
        print(f"⚠️ No news found for {ticker}, returning empty list")
        return []
    
    def _fetch_ddgs_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        """Fetch from DuckDuckGo"""
        try:
            # Try both import methods
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                is_uk = ticker.endswith(".L")
                query = f"{ticker} stock news" if not is_uk else f"{ticker.replace('.L', '')} Lloyds news"
                
                results = list(ddgs.text(query, max_results=self.max_results))
                
                if not results:
                    return []
                
                news_items = []
                for item in results[:max_items]:
                    title = item.get('title', '')[:100]
                    href = item.get('href', '')
                    body = item.get('body', '')
                    
                    # Extract source from URL
                    source = "Unknown"
                    if href and '/' in href:
                        try:
                            source = href.split('/')[2].replace('www.', '').replace('.com', '')
                        except:
                            pass
                    
                    sentiment = self._analyze_sentiment(body)
                    
                    news_items.append(NewsItem(
                        title=title,
                        source=source,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        url=href,
                        sentiment=sentiment
                    ))
                
                return news_items
        except Exception as e:
            print(f"DDGS error: {e}")
            return []
    
    def _fetch_google_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        """Fetch from Google News RSS"""
        try:
            is_uk = ticker.endswith(".L")
            query = f"{ticker} stock" if not is_uk else f"{ticker.replace('.L', '')} company"
            
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Simple RSS parsing
            import re
            items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)
            
            if not items:
                return []
            
            news_items = []
            for item in items[:max_items]:
                title_match = re.search(r'<title>(.*?)</title>', item)
                link_match = re.search(r'<link>(.*?)</link>', item)
                date_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                
                if title_match:
                    title = title_match.group(1).strip()[:100]
                    link = link_match.group(1).strip() if link_match else ''
                    date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
                    
                    # Extract source
                    source = "Google News"
                    if link and '/' in link:
                        try:
                            source = link.split('/')[2].replace('www.', '')
                        except:
                            pass
                    
                    news_items.append(NewsItem(
                        title=title,
                        source=source,
                        date=date,
                        url=link,
                        sentiment='Neutral'
                    ))
            
            return news_items
        except Exception as e:
            print(f"Google News error: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        if not text:
            return 'Neutral'
        
        text = text.lower()
        bullish_words = ['beat', 'upgrade', 'growth', 'gain', 'rise', 'profit', 'surge', 'rally', 'strong', 'positive']
        bearish_words = ['miss', 'downgrade', 'warning', 'loss', 'fall', 'debt', 'drop', 'decline', 'weak', 'negative']
        
        bullish = sum(1 for w in bullish_words if w in text)
        bearish = sum(1 for w in bearish_words if w in text)
        
        if bullish > bearish:
            return 'Bullish'
        elif bearish > bullish:
            return 'Bearish'
        return 'Neutral'