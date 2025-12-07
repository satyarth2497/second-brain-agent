from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ===== 1. Define Real-Time Data Models =====


class StockPrice(BaseModel):
    symbol: str = Field(description="Stock ticker symbol")
    price: float = Field(description="Current stock price")
    change_percent: float = Field(description="Percentage change")
    timestamp: str = Field(description="Time of price update")

class AlertOutput(BaseModel):
    alert_triggered: bool = Field(description="Whether an alert should be triggered")
    alert_message: str = Field(description="Alert message for the user")
    recommendation: str = Field(description="Trading recommendation")

class AnalysisOutput(BaseModel):
    trend: str = Field(description="Current trend (uptrend/downtrend/stable)")
    volatility: str = Field(description="Volatility level (low/medium/high)")
    summary: str = Field(description="Summary analysis of the stock")

# ===== 2. Define Dependency Context =====

@dataclass
class StockContext:
    current_price: float
    previous_price: float
    threshold: float = 5.0  # Alert threshold in percentage

# ===== 3. Create Real-Time Monitoring Agent =====

alert_agent = Agent[StockContext, AlertOutput](
    model="groq:openai/gpt-oss-120b",
    deps_type=StockContext,
    output_type=AlertOutput,
    instructions="""
    You are a real-time stock alert agent.
    Monitor stock price changes and trigger alerts based on thresholds.
    
    Rules:
    - If price change > threshold%, trigger HIGH ALERT
    - If price change 2-5%, trigger MEDIUM ALERT
    - Recommend BUY if downtrend, SELL if uptrend
    """,
)

# ===== 4. Create Real-Time Analysis Agent =====

analysis_agent = Agent[StockContext, AnalysisOutput](
    model="groq:openai/gpt-oss-120b",
    deps_type=StockContext,
    output_type=AnalysisOutput,
    instructions="""
    You are a real-time stock analysis agent.
    Analyze price movements and provide trend analysis.
    
    Analyze:
    - Price direction (uptrend if price increased, downtrend if decreased)
    - Volatility based on price change magnitude
    - Provide brief technical summary
    """,
)

# ===== 5. Define Real-Time Data Stream (Simulation) =====

async def stock_price_stream(stock_symbol: str):
    """Simulates real-time stock price updates"""
    prices = [100.0, 102.5, 101.8, 105.3, 108.2, 106.9, 110.5]
    
    for i, price in enumerate(prices):
        yield StockPrice(
            symbol=stock_symbol,
            price=price,
            change_percent=((price - prices[0]) / prices[0]) * 100,
            timestamp=datetime.now().isoformat()
        )
        await asyncio.sleep(1)  # Simulate real-time delay

# ===== 6. Real-Time Processing Function =====

async def process_real_time_stock(stock_symbol: str, threshold: float = 5.0):
    """Process real-time stock data and generate alerts & analysis"""
    
    print(f"\n{'='*60}")
    print(f"Real-Time Stock Monitoring: {stock_symbol}")
    print(f"{'='*60}\n")
    
    previous_price = 100.0
    
    async for stock_update in stock_price_stream(stock_symbol):
        print(f"\n[{stock_update.timestamp}] Price Update: ${stock_update.price}")
        print(f"Change: {stock_update.change_percent:.2f}%")
        
        # Create context for agents
        context = StockContext(
            current_price=stock_update.price,
            previous_price=previous_price,
            threshold=threshold
        )
        
        # Run Alert Agent
        alert_result = await alert_agent.run(
            f"Current price: ${stock_update.price}, Previous price: ${previous_price}, Change: {stock_update.change_percent:.2f}%",
            deps=context
        )
        
        # Run Analysis Agent
        analysis_result = await analysis_agent.run(
            f"Current price: ${stock_update.price}, Previous price: ${previous_price}, Change: {stock_update.change_percent:.2f}%",
            deps=context
        )
        
        # Display Results
        print("\n--- ALERT AGENT ---")
        print(f"Alert Triggered: {alert_result.output.alert_triggered}")
        print(f"Message: {alert_result.output.alert_message}")
        print(f"Recommendation: {alert_result.output.recommendation}")
        
        print("\n--- ANALYSIS AGENT ---")
        print(f"Trend: {analysis_result.output.trend}")
        print(f"Volatility: {analysis_result.output.volatility}")
        print(f"Summary: {analysis_result.output.summary}")
        
        print(f"\n{'-'*60}")
        
        previous_price = stock_update.price

# ===== 7. Run Real-Time Agent =====

import nest_asyncio
nest_asyncio.apply()

# Execute real-time monitoring
asyncio.run(process_real_time_stock("AAPL", threshold=5.0))