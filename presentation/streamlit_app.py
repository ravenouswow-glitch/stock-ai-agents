import streamlit as st
import asyncio
import os
from datetime import datetime

# Direct imports instead of module imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="4-Agent Stock AI", page_icon="📊", layout="wide")

st.markdown('<p style="font-size: 2.5rem; color: #1a73e8; font-weight: bold;">📈 4-Agent Stock AI</p>', unsafe_allow_html=True)

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

with st.sidebar:
    st.title("⚙️ Settings")
    data_source = st.selectbox("Data Source", ["Yahoo Finance", "Google Finance", "Both"])
    use_chart = st.checkbox("ChartMaster", value=True)
    use_news = st.checkbox("NewsHound", value=True)
    use_signal = st.checkbox("SignalPro", value=True)
    use_director = st.checkbox("Director", value=True)

col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Stock Ticker", value="LLOY.L")
    question = st.text_input("Your Question", value="Technical outlook")
with col2:
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

if analyze_btn:
    with st.spinner('🤖 Running analysis...'):
        try:
            # Import here to avoid circular imports
            from connectors.yahoo import YahooConnector
            from connectors.google_finance import GoogleFinanceConnector
            from connectors.news import NewsConnector
            from agents.chart_master import ChartMaster
            from agents.news_hound import NewsHound
            from agents.signal_pro import SignalPro
            from agents.director import Director
            from pipelines.full_analysis import FullAnalysisPipeline
            
            if data_source == "Yahoo Finance":
                data_providers = [YahooConnector(), NewsConnector()]
            elif data_source == "Google Finance":
                data_providers = [GoogleFinanceConnector(), NewsConnector()]
            else:
                data_providers = [YahooConnector(), GoogleFinanceConnector(), NewsConnector()]
            
            agents = []
            if use_chart: agents.append(ChartMaster())
            if use_news: agents.append(NewsHound())
            if use_signal: agents.append(SignalPro())
            if use_director: agents.append(Director())
            
            pipeline = FullAnalysisPipeline(data_providers, agents, None)
            result = asyncio.run(pipeline.run(ticker, question))
            st.session_state.analysis_result = result
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

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
            with st.expander(f"{agent_name} Analysis"):
                st.write(output.content)
    else:
        st.error(f"❌ Analysis Failed: {result.error}")

st.divider()
st.markdown("<div style='text-align: center; color: #666;'>⚠️ Not financial advice | Data delayed ~15 min</div>", unsafe_allow_html=True)