from interfaces.data_provider import IDataProvider, NewsItem
from typing import List, Optional
from datetime import datetime
import requests
import re

class NewsConnector(IDataProvider):
    """
    News connector with multiple fallbacks:
    1. DuckDuckGo Search (primary)
    2. Google News RSS (fallback)
    3. Smart filtering to avoid false matches
    """
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
    
    def is_available(self) -> bool:
        """Check if news service is working"""
        return True
    
    def get_price(self, ticker: str) -> Optional[any]:
        """Not implemented - use YahooConnector"""
        return None
    
    def get_technicals(self, ticker: str) -> Optional[any]:
        """Not implemented - use YahooConnector"""
        return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        """Fetch news using multiple methods with smart filtering"""
        
        # Try DuckDuckGo first
        try:
            news = self._fetch_ddgs_news(ticker, max_items)
            if news:
                print(f"✓ Found {len(news)} news via DuckDuckGo for {ticker}")
                return news
        except Exception as e:
            print(f"DuckDuckGo failed for {ticker}: {e}")
        
        # Fallback: Try Google News RSS
        try:
            news = self._fetch_google_news(ticker, max_items)
            if news:
                print(f"✓ Found {len(news)} news via Google News for {ticker}")
                return news
        except Exception as e:
            print(f"Google News failed for {ticker}: {e}")
        
        # Last resort: Return empty list
        print(f"⚠️ No news found for {ticker}")
        return []
    
    def _fetch_ddgs_news(self, ticker: str, max_items: int) -> List[NewsItem]:
        """Fetch news from DuckDuckGo Search"""
        try:
            # Try both import methods for compatibility
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                # Build smarter query
                query = self._build_search_query(ticker)
                
                results = list(ddgs.text(query, max_results=self.max_results))
                
                if not results:
                    return []
                
                news_items = []
                for item in results[:max_items]:
                    title = item.get('title', '')[:100]
                    href = item.get('href', '')
                    body = item.get('body', '')
                    
                    # Extract source from URL
                    source = self._extract_source(href)
                    
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
        """Fetch news from Google News RSS with smart filtering"""
        try:
            # Build specific query to avoid false matches
            query = self._build_search_query(ticker)
            
            rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return []
            
            # Parse RSS items
            items = re.findall(r'<item>(.*?)</item>', response.text, re.DOTALL)
            
            if not items:
                return []
            
            # Keywords to filter OUT irrelevant results
            exclude_keywords = self._get_exclude_keywords(ticker)
            include_keywords = self._get_include_keywords(ticker)
            
            news_items = []
            for item in items[:max_items * 3]:  # Get extra to filter
                title_match = re.search(r'<title>(.*?)</title>', item)
                link_match = re.search(r'<link>(.*?)</link>', item)
                date_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                
                if not title_match:
                    continue
                
                title = title_match.group(1).strip()
                title_lower = title.lower()
                
                # Skip if title contains exclude keywords
                if any(kw in title_lower for kw in exclude_keywords):
                    continue
                
                # For financial stocks, require finance-related keywords
                if include_keywords and not any(kw in title_lower for kw in include_keywords):
                    continue
                
                link = link_match.group(1).strip() if link_match else ''
                date = date_match.group(1).strip() if date_match else datetime.now().strftime("%Y-%m-%d")
                
                # Extract source
                source = self._extract_source(link)
                
                news_items.append(NewsItem(
                    title=title[:100],
                    source=source,
                    date=date,
                    url=link,
                    sentiment=self._analyze_sentiment(title)
                ))
                
                if len(news_items) >= max_items:
                    break
            
            return news_items
        except Exception as e:
            print(f"Google News error: {e}")
            return []
    
    def _build_search_query(self, ticker: str) -> str:
        """Build smart search query to avoid false matches"""
        
        # Specific mappings for ambiguous tickers
        ticker_queries = {
            "LLOY.L": "Lloyds Banking Group stock",
            "BARC.L": "Barclays bank stock",
            "HSBA.L": "HSBC Holdings stock",
            "VOD.L": "Vodafone Group stock",
            "BP.L": "BP plc oil stock",
            "SHEL.L": "Shell plc stock",
            "AZN.L": "AstraZeneca pharmaceutical stock",
            "GSK.L": "GSK pharmaceutical stock",
            "RIO.L": "Rio Tinto mining stock",
            "BHP.L": "BHP mining stock",
        }
        
        if ticker in ticker_queries:
            return ticker_queries[ticker]
        
        # Default handling
        is_uk = ticker.endswith(".L")
        clean_ticker = ticker.replace(".L", "").replace(".TO", "").replace(".DE", "")
        
        if is_uk:
            return f"{clean_ticker} London Stock Exchange stock"
        elif ticker.endswith(".TO"):
            return f"{clean_ticker} Toronto Stock Exchange"
        elif ticker.endswith(".DE"):
            return f"{clean_ticker} Frankfurt stock"
        else:
            return f"{ticker} stock news"
    
    def _get_exclude_keywords(self, ticker: str) -> List[str]:
        """Get keywords to exclude from news results"""
        
        # Exclude keywords for specific tickers
        exclude_map = {
            "LLOY.L": [
                'hapag-lloyd', 'jamie lloyd', 'lloyd webber', 'lloyd insurance',
                'lloyds of london', 'shipping company', 'theater', 'broadway',
                'maritime', 'container ship'
            ],
            "BARC.L": ['barclays center', 'barclays arena', 'sports venue'],
            "BP.L": ['bp gas station', 'bp america retail', 'bp convenience'],
        }
        
        return exclude_map.get(ticker, [])
    
    def _get_include_keywords(self, ticker: str) -> List[str]:
        """Get keywords that MUST appear for financial stocks"""
        
        # For bank/financial stocks, require finance-related terms
        financial_tickers = ["LLOY.L", "BARC.L", "HSBA.L", "STAN.L", "CBK.L"]
        
        if ticker in financial_tickers:
            return [
                'bank', 'banking', 'shares', 'stock', 'earnings', 'profit',
                'dividend', 'rate', 'financial', 'revenue', 'quarter',
                'analyst', 'upgrade', 'downgrade', 'target price'
            ]
        
        return []
    
    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        if not url or '/' not in url:
            return "Unknown"
        
        try:
            domain = url.split('/')[2].lower()
            domain = domain.replace('www.', '').replace('.com', '').replace('.co.uk', '')
            return domain.title()
        except:
            return "Google News"
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment analysis"""
        if not text:
            return 'Neutral'
        
        text = text.lower()
        
        bullish_words = [
            'beat', 'upgrade', 'growth', 'gain', 'rise', 'profit', 'surge',
            'rally', 'strong', 'positive', 'outperform', 'buy', 'bullish',
            'record', 'increase', 'higher', 'improve', 'success'
        ]
        
        bearish_words = [
            'miss', 'downgrade', 'warning', 'loss', 'fall', 'debt', 'drop',
            'decline', 'weak', 'negative', 'underperform', 'sell', 'bearish',
            'low', 'decrease', 'lower', 'worsen', 'failure', 'crisis'
        ]
        
        bullish = sum(1 for w in bullish_words if w in text)
        bearish = sum(1 for w in bearish_words if w in text)
        
        if bullish > bearish + 1:
            return 'Bullish'
        elif bearish > bullish + 1:
            return 'Bearish'
        return 'Neutral'