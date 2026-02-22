from interfaces.data_provider import IDataProvider, PriceData, TechnicalData, NewsItem
from typing import Optional, List
import yfinance as yf
from datetime import datetime, timezone

class YahooConnector(IDataProvider):
    def __init__(self):
        self._cache = {}
        self._last_check = None
    
    def is_available(self) -> bool:
        try:
            yf.Ticker("AAPL").info
            self._last_check = datetime.now()
            return True
        except:
            return False
    
    def get_price(self, ticker: str) -> Optional[PriceData]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            df = stock.history(period="1d")
            
            if df.empty:
                return None
            
            price = df['Close'].iloc[-1]
            currency = info.get('currency', 'USD')
            
            if currency == 'GBp':
                price = price / 100
                currency = 'GBP'
            
            return PriceData(
                ticker=ticker,
                price=price,
                currency=currency,
                timestamp=datetime.now(timezone.utc).isoformat(),
                change_pct=info.get('regularMarketChangePercent', 0)
            )
        except Exception as e:
            print(f"Yahoo price error: {e}")
            return None
    
    def get_technicals(self, ticker: str) -> Optional[TechnicalData]:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo")
            info = stock.info
            
            if len(df) < 50:
                return None
            
            currency = info.get('currency', 'USD')
            convert = lambda v: v / 100 if currency == 'GBp' else v
            
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + gain/loss))
            
            current = convert(df['Close'].iloc[-1])
            sma20 = convert(df['SMA20'].iloc[-1])
            sma50 = convert(df['SMA50'].iloc[-1])
            rsi = df['RSI'].iloc[-1]
            
            return TechnicalData(
                ticker=ticker,
                current=current,
                sma20=sma20,
                sma50=sma50,
                rsi=rsi,
                trend='Bullish' if current > sma50 else 'Bearish',
                support=convert(df['Low'].tail(20).min()),
                resistance=convert(df['High'].tail(20).max()),
                currency='GBP' if currency == 'GBp' else currency,
                symbol='£' if currency == 'GBp' else '$'
            )
        except Exception as e:
            print(f"Yahoo technicals error: {e}")
            return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        return []