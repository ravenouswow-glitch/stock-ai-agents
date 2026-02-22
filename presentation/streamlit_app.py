import streamlit as st
import asyncio
import os
import sys
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Plotly for charts
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Import project modules
from connectors.yahoo import YahooConnector
from connectors.google_finance import GoogleFinanceConnector
from connectors.news import NewsConnector
from agents.chart_master import ChartMaster
from agents.news_hound import NewsHound
from agents.signal_pro import SignalPro
from agents.director import Director
from pipelines.full_analysis import FullAnalysisPipeline

# Page config
st.set_page_config(
    page_title="📈 4-Agent Stock AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #1a73e8; font-weight: bold; margin-bottom: 1rem;}
    .metric-card {background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #1a73e8;}
    .signal-buy {color: #198754; font-weight: bold; font-size: 1.1rem;}
    .signal-sell {color: #dc3545; font-weight: bold; font-size: 1.1rem;}
    .signal-hold {color: #ffc107; font-weight: bold; font-size: 1.1rem;}
    .director-box {background: #e7f1ff; padding: 1.2rem; border-radius: 10px; border-left: 5px solid #1a73e8;}
    .agent-box {background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;}
    st-expander {border: 1px solid #dee2e6;}
</style>
""", unsafe_allow_html=True)

# Session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = None
if 'loading' not in st.session_state:
    st.session_state.loading = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stock-market.png", width=70)
    st.title("⚙️ Settings")
    
    # Data source
    data_source = st.selectbox(
        "Data Source",
        ["Yahoo Finance", "Google Finance", "Both (Fallback)"],
        help="Choose where to fetch stock data"
    )
    
    # Agent selection
    st.subheader("🤖 Active Agents")
    use_chart = st.checkbox("ChartMaster (Technical)", value=True)
    use_news = st.checkbox("NewsHound (News)", value=True)
    use_signal = st.checkbox("SignalPro (Signals)", value=True)
    use_director = st.checkbox("Director (Final)", value=True)
    
    st.divider()
    
    # Chart options
    st.subheader("📊 Chart Options")
    show_sma = st.checkbox("Show SMA20/50", value=True)
    show_bb = st.checkbox("Show Bollinger Bands", value=True)
    show_volume = st.checkbox("Show Volume", value=True)
    show_macd = st.checkbox("Show MACD", value=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    
    st.divider()
    
    # Quick links
    st.markdown("### 🔗 Links")
    st.markdown("[📊 View Google Sheet](#)")
    st.markdown("[📖 Documentation](#)")
    
    # Info box
    st.info("""
    **Free Data Sources:**
    - Yahoo Finance ✅
    - Google Finance ✅
    - DuckDuckGo News ✅
    
    **AI Provider:**
    - Groq API (Free tier)
    """)

# Main header
st.markdown('<p class="main-header">📈 4-Agent Stock AI</p>', unsafe_allow_html=True)
st.markdown("Professional stock analysis powered by AI agents with visual technical charts")

# Input section
col1, col2, col3 = st.columns([3, 2, 1])

with col1:
    ticker = st.text_input(
        "Stock Ticker",
        value="LLOY.L",
        placeholder="e.g., LLOY.L, AAPL, TSLA",
        help="Enter stock ticker symbol"
    )

with col2:
    question = st.text_input(
        "Your Question",
        value="Technical outlook",
        placeholder="What do you want to know?",
        help="Ask specific questions about the stock"
    )

with col3:
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

# Quick tickers
st.markdown("### ⚡ Quick Select")
cols = st.columns(6)
quick_tickers = ["LLOY.L", "BARC.L", "AAPL", "TSLA", "NVDA", "MSFT"]
for i, col in enumerate(cols):
    with col:
        if st.button(quick_tickers[i], use_container_width=True):
            ticker = quick_tickers[i]
            analyze_btn = True

# Function to fetch chart data
def fetch_chart_data(ticker: str):
    """Fetch historical data for charting"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")
        
        if df.empty or len(df) < 50:
            return None
        
        # Calculate indicators for charting
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['SMA20']
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception as e:
        print(f"Chart data error: {e}")
        return None

# Function to create interactive chart
def create_interactive_chart(df, ticker, show_sma=True, show_bb=True, show_volume=True, show_macd=True, show_rsi=True):
    """Create multi-panel interactive chart with Plotly"""
    
    # Count how many subplots we need
    subplot_count = 1  # Price chart always
    if show_volume: subplot_count += 1
    if show_macd: subplot_count += 1
    if show_rsi: subplot_count += 1
    
    # Create subplots
    fig = make_subplots(
        rows=subplot_count, cols=1,
        subplot_titles=[f"{ticker} Price Chart"] + 
                      (["Volume"] if show_volume else []) +
                      (["MACD"] if show_macd else []) +
                      (["RSI"] if show_rsi else []),
        vertical_spacing=0.05,
        row_heights=[0.5] + ([0.15] * (subplot_count - 1))
    )
    
    row_idx = 1
    
    # === PRICE PANEL ===
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=row_idx, col=1
    )
    
    # SMA lines
    if show_sma:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#ff9800', width=1.5), name='SMA20'),
            row=row_idx, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#9c27b0', width=1.5), name='SMA50'),
            row=row_idx, col=1
        )
    
    # Bollinger Bands
    if show_bb and 'BB_Upper' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='#90a4ae', width=1, dash='dot'), name='BB Upper', showlegend=False),
            row=row_idx, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='#90a4ae', width=1, dash='dot'), name='BB Lower', fill='tonexty', fillcolor='rgba(144,164,174,0.1)', showlegend=False),
            row=row_idx, col=1
        )
    
    fig.update_yaxes(title_text="Price", row=row_idx, col=1)
    row_idx += 1
    
    # === VOLUME PANEL ===
    if show_volume:
        colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume', opacity=0.7),
            row=row_idx, col=1
        )
        fig.update_yaxes(title_text="Volume", row=row_idx, col=1)
        row_idx += 1
    
    # === MACD PANEL ===
    if show_macd and 'MACD' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#2196f3', width=1.5), name='MACD'),
            row=row_idx, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#ff9800', width=1.5), name='Signal'),
            row=row_idx, col=1
        )
        # MACD Histogram
        colors_hist = ['#26a69a' if v >= 0 else '#ef5350' for v in df['MACD_Hist']]
        fig.add_trace(
            go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_hist, name='Histogram', opacity=0.5),
            row=row_idx, col=1
        )
        fig.add_hline(y=0, line_dash="dash", line_color="#666", row=row_idx, col=1)
        fig.update_yaxes(title_text="MACD", row=row_idx, col=1)
        row_idx += 1
    
    # === RSI PANEL ===
    if show_rsi and 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#e91e63', width=2), name='RSI'),
            row=row_idx, col=1
        )
        # Overbought/Oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", row=row_idx, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", row=row_idx, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="#ef5350", opacity=0.1, line_width=0, row=row_idx, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="#26a69a", opacity=0.1, line_width=0, row=row_idx, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=row_idx, col=1)
        row_idx += 1
    
    # Layout updates
    fig.update_layout(
        title=f"{ticker} - Technical Analysis Chart",
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        height=200 + (subplot_count * 150),
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    # X-axis for all
    for i in range(1, subplot_count + 1):
        fig.update_xaxes(showgrid=False, row=i, col=1)
    
    return fig

# Analysis execution
if analyze_btn and ticker:
    st.session_state.loading = True
    
    with st.spinner(f'🤖 Analyzing {ticker}...'):
        try:
            # Fetch chart data first
            chart_df = fetch_chart_data(ticker)
            if chart_df is not None:
                st.session_state.chart_data = chart_df
            
            # Setup data providers
            if data_source == "Yahoo Finance":
                data_providers = [YahooConnector(), NewsConnector()]
            elif data_source == "Google Finance":
                data_providers = [GoogleFinanceConnector(), NewsConnector()]
            else:
                data_providers = [YahooConnector(), GoogleFinanceConnector(), NewsConnector()]
            
            # Setup agents
            agents = []
            if use_chart: agents.append(ChartMaster())
            if use_news: agents.append(NewsHound())
            if use_signal: agents.append(SignalPro())
            if use_director: agents.append(Director())
            
            # Create and run pipeline
            pipeline = FullAnalysisPipeline(data_providers, agents, None)
            result = asyncio.run(pipeline.run(ticker, question))
            st.session_state.analysis_result = result
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.session_state.loading = False

# Display Chart (if data available)
if st.session_state.chart_data is not None and not st.session_state.loading:
    st.markdown("### 📊 Interactive Technical Chart")
    
    with st.expander("📈 View/Customize Chart", expanded=True):
        chart = create_interactive_chart(
            st.session_state.chart_data,
            ticker,
            show_sma=show_sma,
            show_bb=show_bb,
            show_volume=show_volume,
            show_macd=show_macd,
            show_rsi=show_rsi
        )
        st.plotly_chart(chart, use_container_width=True)
        
        # Current values summary
        df = st.session_state.chart_data
        latest = df.iloc[-1]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Price", f"${latest['Close']:.2f}")
        with col2:
            st.metric("SMA20", f"${latest['SMA20']:.2f}" if 'SMA20' in df.columns else "N/A")
        with col3:
            st.metric("RSI", f"{latest['RSI']:.1f}" if 'RSI' in df.columns else "N/A")
        with col4:
            if 'MACD_Hist' in df.columns:
                macd_color = "🟢" if latest['MACD_Hist'] > 0 else "🔴"
                st.metric("MACD", f"{macd_color} {latest['MACD_Hist']:.3f}")
        with col5:
            if 'BB_Upper' in df.columns:
                if latest['Close'] > latest['BB_Upper']:
                    st.metric("BB Position", "🔼 Upper")
                elif latest['Close'] < latest['BB_Lower']:
                    st.metric("BB Position", "🔽 Lower")
                else:
                    st.metric("BB Position", "➡️ Middle")

# Display Analysis Results
if st.session_state.analysis_result and not st.session_state.loading:
    result = st.session_state.analysis_result
    
    if result.success:
        st.success("✅ Analysis Complete!")
        
        # Director Answer (Main Result)
        if 'Director' in result.outputs:
            director_output = result.outputs['Director'].content
            st.markdown("### 🎯 Director's Recommendation")
            st.markdown(f'<div class="director-box">{director_output.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'SignalPro' in result.outputs:
                content = result.outputs['SignalPro'].content
                signal = "Buy" if "BUY" in content.upper() else "Sell" if "SELL" in content.upper() else "Hold"
                signal_class = "signal-buy" if signal == "Buy" else "signal-sell" if signal == "Sell" else "signal-hold"
                st.markdown(f'<div class="metric-card"><span class="{signal_class}">{signal}</span><br><small>Signal</small></div>', unsafe_allow_html=True)
        
        with col2:
            if 'Director' in result.outputs:
                conf = result.outputs['Director'].confidence
                st.markdown(f'<div class="metric-card"><b>{conf}/10</b><br><small>Confidence</small></div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'<div class="metric-card"><b>{len(result.outputs)}</b><br><small>Agents Used</small></div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'<div class="metric-card"><b>{data_source}</b><br><small>Data Source</small></div>', unsafe_allow_html=True)
        
        # Individual Agent Outputs
        st.markdown("### 🤖 Agent Details")
        
        for agent_name, output in result.outputs.items():
            with st.expander(f"{agent_name} Analysis", expanded=(agent_name == 'Director')):
                st.markdown(f'<div class="agent-box">{output.content.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                st.caption(f"Confidence: {output.confidence}/10 | Success: {output.success}")
        
        # Export options
        st.divider()
        st.markdown("### 💾 Export Options")
        
        col1, col2 = st.columns(2)
        with col1:
            if result.outputs:
                report_text = "\n\n".join([f"=== {k} ===\n{v.content}" for k, v in result.outputs.items()])
                st.download_button(
                    "📥 Download Report (TXT)",
                    data=report_text,
                    file_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        with col2:
            if st.session_state.chart_data is not None:
                csv = st.session_state.chart_data.to_csv()
                st.download_button(
                    "📊 Download Chart Data (CSV)",
                    data=csv,
                    file_name=f"{ticker}_chart_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    else:
        st.error(f"❌ Analysis Failed: {result.error}")
        st.markdown("### 💡 Try These:")
        st.markdown("""
        - Check ticker symbol is correct (e.g., `LLOY.L` for Lloyds)
        - Try different data source (Yahoo vs Google Finance)
        - Reduce number of active agents
        - Check your internet connection
        """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;'>
    <p>🤖 4-Agent Stock AI | Powered by Groq AI | Free Data Sources</p>
    <p>⚠️ Not financial advice | Data delayed ~15 minutes | For educational purposes only</p>
</div>
""", unsafe_allow_html=True)

# Clear loading state
st.session_state.loading = False