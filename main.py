import asyncio
from config import Config

from connectors.yahoo import YahooConnector
from connectors.google_finance import GoogleFinanceConnector
from connectors.news import NewsConnector
from agents.chart_master import ChartMaster
from agents.news_hound import NewsHound
from agents.signal_pro import SignalPro
from agents.director import Director
from pipelines.full_analysis import FullAnalysisPipeline
from outputs.console import ConsoleOutput

async def run_full_analysis():
    print("\n" + "="*60)
    print("FULL 4-AGENT ANALYSIS")
    print("="*60)
    
    data_providers = [YahooConnector(), NewsConnector()]
    agents = [ChartMaster(), NewsHound(), SignalPro(), Director()]
    
    pipeline = FullAnalysisPipeline(data_providers, agents, ConsoleOutput())
    
    ticker = input("\nEnter ticker: ").strip() or "LLOY.L"
    question = input("Your question: ").strip() or "Technical outlook"
    
    result = await pipeline.run(ticker, question)
    
    if result.success:
        print(f"\n✅ Analysis complete for {ticker}")
        ConsoleOutput.print_director_box(result.outputs['Director'].content, ticker)
    else:
        print(f"\n❌ Error: {result.error}")

def main():
    print("\n" + "="*60)
    print("🤖 4-AGENT STOCK AI - MODULAR EDITION")
    print("="*60)
    
    if not Config.validate():
        print("\n⚠️ Configuration error. Check .env file.")
        return
    
    print("\n1. Full Analysis (4 Agents)")
    print("2. Run Streamlit Web App")
    print("3. Exit")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        asyncio.run(run_full_analysis())
    elif choice == "2":
        import os
        os.system("streamlit run presentation/streamlit_app.py")
    elif choice == "3":
        print("\nGoodbye!")
    else:
        print("\nInvalid option")

if __name__ == "__main__":
    main()