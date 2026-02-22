import streamlit as st
import asyncio
import os
from datetime import datetime

st.set_page_config(page_title="4-Agent Stock AI", page_icon="📊", layout="wide")

st.markdown('<p style="font-size: 2.5rem; color: #1a73e8; font-weight: bold;">📈 4-Agent Stock AI</p>', unsafe_allow_html=True)

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

with st.sidebar:
    st.title("⚙️ Settings")
    data_source = st.selectbox("Data Source", ["Yahoo Finance", "Google Finance", "Both (Auto-Fallback)"])
    use_chart = st.checkbox("ChartMaster", value=True)
    use_news = st.checkbox("NewsHound", value=True)
    use_signal = st.checkbox("SignalPro", value=True)
    use_director = st.checkbox("Director", value=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Stock Ticker", value="AAPL")
    question = st.text_input("Your Question", value="Technical outlook")
with col2:
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

st.markdown("### ⚡ Quick Select")
cols = st.columns(6)
quick_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "LLOY.L"]
for i, col in enumerate(cols):
    with col:
        if st.button(quick_tickers[i], use_container_width=True):
            ticker = quick_tickers[i]

if analyze_btn:
    with st.spinner('🤖 Running analysis... This may take 30-60 seconds.'):
        try:
            # Import connectors
            from connectors.yahoo import YahooConnector
            from connectors.google_finance import GoogleFinanceConnector
            from connectors.news import NewsConnector
            from agents.chart_master import ChartMaster
            from agents.news_hound import NewsHound
            from agents.signal_pro import SignalPro
            from agents.director import Director
            from pipelines.full_analysis import FullAnalysisPipeline
            
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
            
            # Run pipeline
            pipeline = FullAnalysisPipeline(data_providers, agents, None)
            result = await pipeline.run(ticker, question)
            st.session_state.analysis_result = result
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    if result.success:
        st.success("✅ Analysis Complete!")
        
        if 'Director' in result.outputs:
            st.markdown("### 🎯 Director's Recommendation")
            st.info(result.outputs['Director'].content.replace("\n", "\n\n"))
        
        cols = st.columns(4)
        with cols[0]:
            st.metric("Agents Used", len(result.outputs))
        with cols[1]:
            if 'Director' in result.outputs:
                st.metric("Confidence", f"{result.outputs['Director'].confidence}/10")
        with cols[2]:
            st.metric("Data Source", data_source)
        with cols[3]:
            st.metric("Ticker", ticker)
        
        for agent_name, output in result.outputs.items():
            with st.expander(f"{agent_name} Analysis", expanded=False):
                st.write(output.content)
                st.caption(f"Confidence: {output.confidence}/10")
    else:
        st.error(f"❌ Analysis Failed: {result.error}")
        st.info("💡 **Try these:**\n- Use 'Google Finance' instead of Yahoo Finance\n- Try a different ticker (e.g., AAPL, MSFT)\n- Check your internet connection\n- Wait a few minutes and try again (rate limiting)")

st.divider()
st.markdown("<div style='text-align: center; color: #666;'>⚠️ Not financial advice | Data delayed ~15 min</div>", unsafe_allow_html=True)