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
        """Get technical indicators - simplified version"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3mo")
            info = stock.info
            
            if len(df) < 50:
                return None
            
            currency = info.get('currency', 'USD')
            convert = lambda v: v / 100 if currency == 'GBp' else v
            
            # Calculate basic indicators
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Get current values
            current = convert(df['Close'].iloc[-1])
            sma20 = convert(df['SMA20'].iloc[-1])
            sma50 = convert(df['SMA50'].iloc[-1])
            rsi = float(df['RSI'].iloc[-1])
            
            # Handle NaN
            if not rsi or rsi != rsi:  # NaN check
                rsi = 50.0
            
            # Support/Resistance
            support = convert(df['Low'].tail(20).min())
            resistance = convert(df['High'].tail(20).max())
            
            # Trend
            trend = 'Bullish' if current > sma50 else 'Bearish'
            
            return TechnicalData(
                ticker=ticker,
                current=current,
                sma20=sma20,
                sma50=sma50,
                rsi=rsi,
                trend=trend,
                support=support,
                resistance=resistance,
                currency='GBP' if currency == 'GBp' else currency,
                symbol='£' if currency == 'GBp' else '$',
                # Set advanced indicators to None for now
                macd_line=None,
                macd_signal=None,
                macd_histogram=None,
                bb_upper=None,
                bb_middle=None,
                bb_lower=None,
                bb_width=None,
                volume=None,
                volume_sma20=None,
                atr=None,
                stoch_rsi=None
            )
        except Exception as e:
            print(f"Yahoo technicals error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_news(self, ticker: str, max_items: int = 5) -> List[NewsItem]:
        return []