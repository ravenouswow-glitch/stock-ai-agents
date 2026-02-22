import streamlit as st
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="4-Agent Stock AI",
    page_icon="📊",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1a73e8; font-weight: bold;}
    .director-box {background: #e3f2fd; padding: 20px; border-radius: 10px; border-left: 5px solid #1a73e8;}
</style>
""", unsafe_allow_html=True)

# Session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = None
if 'show_charts' not in st.session_state:
    st.session_state.show_charts = False

# Header
st.markdown('<p class="main-header">📈 4-Agent Stock AI</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    data_source = st.selectbox("Data Source", ["Yahoo Finance", "Google Finance", "Both"])
    use_chart = st.checkbox("ChartMaster", value=True)
    use_news = st.checkbox("NewsHound", value=True)
    use_signal = st.checkbox("SignalPro", value=True)
    use_director = st.checkbox("Director", value=True)

# Input
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Stock Ticker", value="LLOY.L")
    question = st.text_input("Your Question", value="Technical outlook")
with col2:
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

# Quick select
st.markdown("### ⚡ Quick Select")
cols = st.columns(6)
quick_tickers = ["LLOY.L", "BARC.L", "AAPL", "TSLA", "NVDA", "MSFT"]
for i, col in enumerate(cols):
    with col:
        if st.button(quick_tickers[i], use_container_width=True):
            ticker = quick_tickers[i]
            analyze_btn = True

# Main analysis
if analyze_btn and ticker:
    try:
        with st.spinner('🤖 Running analysis... This may take 30-60 seconds.'):
            # Import modules
            try:
                from connectors.yahoo import YahooConnector
                from connectors.google_finance import GoogleFinanceConnector
                from connectors.news import NewsConnector
                from agents.chart_master import ChartMaster
                from agents.news_hound import NewsHound
                from agents.signal_pro import SignalPro
                from agents.director import Director
                from pipelines.full_analysis import FullAnalysisPipeline
                import asyncio
                import yfinance as yf
            except ImportError as e:
                st.error(f"❌ Import error: {e}")
                st.stop()
            
            # Fetch chart data for optional display
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period="3mo")
                if not df.empty:
                    st.session_state.chart_data = df
            except Exception as e:
                st.session_state.chart_data = None
            
            # Setup providers
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
            
            if not agents:
                st.error("❌ Please select at least one agent")
                st.stop()
            
            # Run pipeline
            try:
                pipeline = FullAnalysisPipeline(data_providers, agents, None)
                result = asyncio.run(pipeline.run(ticker, question))
                st.session_state.analysis_result = result
                
                if result.success:
                    st.success("✅ Analysis complete!")
                else:
                    st.error(f"❌ Analysis failed: {result.error}")
                    
            except Exception as e:
                st.error(f"❌ Pipeline error: {e}")
                
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")

# Display results
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    
    if result.success:
        # Director answer
        if 'Director' in result.outputs:
            st.markdown("### 🎯 Director's Recommendation")
            output = result.outputs['Director'].content
            st.markdown(f'<div class="director-box">{output.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        
        # Metrics
        cols = st.columns(3)
        with cols[0]:
            st.metric("Agents Used", len(result.outputs))
        with cols[1]:
            if 'Director' in result.outputs:
                st.metric("Confidence", f"{result.outputs['Director'].confidence}/10")
        with cols[2]:
            st.metric("Data Source", data_source)
        
        # Agent details
        st.markdown("### 🤖 Agent Details")
        for agent_name, output in result.outputs.items():
            with st.expander(f"{agent_name} Analysis", expanded=False):
                st.write(output.content)
                st.caption(f"Confidence: {output.confidence}/10")
        
        # Charts button
        st.divider()
        if st.session_state.chart_data is not None:
            if st.button("📊 Show Price Chart"):
                st.session_state.show_charts = not st.session_state.show_charts
    
    else:
        st.error(f"❌ Failed: {result.error}")

# Show charts if requested
if st.session_state.get('show_charts', False) and st.session_state.chart_data is not None:
    st.markdown("### 📊 Price Chart")
    df = st.session_state.chart_data
    
    try:
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        )])
        
        fig.update_layout(
            title=f"{ticker} Price Chart",
            height=400,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.warning(f"⚠️ Could not display chart: {e}")

# Footer
st.divider()
st.markdown("<div style='text-align: center; color: #666;'>⚠️ Not financial advice</div>", unsafe_allow_html=True)