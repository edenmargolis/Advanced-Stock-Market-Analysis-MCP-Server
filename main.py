from mcp.server.fastmcp import FastMCP
import yfinance as yf
import numpy as np
import sys
import logging
import time
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
try:
    mcp = FastMCP(   
        name="Advanced Stock Market Analysis Server",
        description="A powerful server providing advanced stock market analysis and insights",
        version="1.0.0"
    )
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {str(e)}")
    sys.exit(1)

@mcp.tool()
def get_stock_info(ticker: str) -> dict:
    """Get basic information about a stock.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
        
    Returns:
        Dictionary containing stock information
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "symbol": info.get("symbol"),
            "name": info.get("longName"),
            "current_price": info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "beta": info.get("beta"),
            "profit_margins": info.get("profitMargins"),
            "analyst_target_price": info.get("targetMeanPrice")
        }
    except Exception as e:
        logger.error(f"Error in get_stock_info: {str(e)}")
        return {"error": f"Failed to get stock info: {str(e)}"}

@mcp.tool()
def get_stock_history(ticker: str, period: str = "1mo") -> dict:
    """Get historical data for a stock.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
        period: The time period for historical data (e.g., "1d", "1mo", "1y")
        
    Returns:
        Dictionary containing historical data and status
    """
    try:
        logger.info(f"Fetching historical data for {ticker} over period {period}")
        
        # Input validation
        if not isinstance(ticker, str) or not ticker.strip():
            return {
                "status": "error",
                "message": "Invalid ticker symbol",
                "ticker": ticker,
                "period": period
            }
            
        if period not in ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]:
            period = "1mo"  # Default to 1mo if invalid period
            logger.warning(f"Invalid period provided, defaulting to {period}")
            
        # Add retry logic with exponential backoff
        max_retries = 3
        retry_count = 0
        base_wait_time = 1  # Start with 1 second
        
        while retry_count < max_retries:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(
                    period=period,
                    interval="1d",
                    timeout=20,  # Increased timeout
                    progress=False,  # Disable progress bar
                    show_errors=False  # Suppress yfinance errors
                )
                
                if hist is None or hist.empty:
                    retry_count += 1
                    wait_time = base_wait_time * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Attempt {retry_count}: Empty data received for {ticker}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                    
                # Convert the data to a more manageable format with error handling
                data = []
                try:
                    for date, row in hist.iterrows():
                        entry = {
                            "date": date.strftime("%Y-%m-%d"),
                            "open": float(row.get("Open", 0)),
                            "high": float(row.get("High", 0)),
                            "low": float(row.get("Low", 0)),
                            "close": float(row.get("Close", 0)),
                            "volume": int(row.get("Volume", 0)),
                        }
                        # Calculate change percent safely
                        try:
                            if entry["open"] > 0:
                                entry["change_percent"] = ((entry["close"] - entry["open"]) / entry["open"]) * 100
                            else:
                                entry["change_percent"] = 0
                        except Exception:
                            entry["change_percent"] = 0
                        data.append(entry)
                    
                    return {
                        "status": "success",
                        "ticker": ticker,
                        "period": period,
                        "data_points": len(data),
                        "history": data,
                        "metadata": {
                            "first_date": data[0]["date"] if data else None,
                            "last_date": data[-1]["date"] if data else None,
                            "total_volume": sum(entry["volume"] for entry in data)
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing historical data for {ticker}: {str(e)}")
                    raise
                    
            except Exception as e:
                retry_count += 1
                wait_time = base_wait_time * (2 ** retry_count)
                logger.warning(f"Attempt {retry_count}: Failed to fetch data - {str(e)}, retrying in {wait_time}s")
                if retry_count < max_retries:
                    time.sleep(wait_time)
                else:
                    raise
                
    except Exception as e:
        error_msg = f"Error in get_stock_history for {ticker}: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "ticker": ticker,
            "period": period,
            "error_type": str(type(e).__name__)
        }

@mcp.tool()
def analyze_stock_trend(ticker: str) -> dict:
    """Analyze stock trend using technical indicators.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
        
    Returns:
        Dictionary containing trend analysis
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if len(hist) < 20:
            return {"error": "Not enough historical data for analysis"}
        
        # Calculate moving averages
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA50'] = hist['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # Calculate Bollinger Bands
        hist['BB_middle'] = hist['Close'].rolling(window=20).mean()
        hist['BB_upper'] = hist['BB_middle'] + 2 * hist['Close'].rolling(window=20).std()
        hist['BB_lower'] = hist['BB_middle'] - 2 * hist['Close'].rolling(window=20).std()
        
        # Get latest values
        last_price = hist['Close'].iloc[-1]
        last_ma20 = hist['MA20'].iloc[-1]
        last_ma50 = hist['MA50'].iloc[-1]
        last_rsi = hist['RSI'].iloc[-1]
        last_macd = hist['MACD'].iloc[-1]
        last_signal = hist['Signal_Line'].iloc[-1]
        
        # Advanced trend analysis
        trend_signals = {
            "ma_trend": "Bullish" if last_ma20 > last_ma50 else "Bearish",
            "rsi_signal": "Overbought" if last_rsi > 70 else "Oversold" if last_rsi < 30 else "Neutral",
            "macd_signal": "Buy" if last_macd > last_signal else "Sell",
            "price_vs_ma20": "Above" if last_price > last_ma20 else "Below",
            "price_vs_ma50": "Above" if last_price > last_ma50 else "Below"
        }
        
        # Calculate volatility
        volatility = hist['Close'].pct_change().std() * 100
        
        return {
            "ticker": ticker,
            "current_price": last_price,
            "technical_indicators": {
                "ma20": last_ma20,
                "ma50": last_ma50,
                "rsi": last_rsi,
                "macd": last_macd,
                "macd_signal": last_signal,
                "bollinger_bands": {
                    "upper": hist['BB_upper'].iloc[-1],
                    "middle": hist['BB_middle'].iloc[-1],
                    "lower": hist['BB_lower'].iloc[-1]
                }
            },
            "trend_analysis": trend_signals,
            "volatility": volatility,
        }
    except Exception as e:
        logger.error(f"Error in analyze_stock_trend: {str(e)}")
        return {"error": f"Failed to analyze stock trend: {str(e)}"}

@mcp.tool()
def analyze_stock_risk(ticker: str) -> dict:
    """Analyze stock risk metrics and potential returns.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
        
    Returns:
        Dictionary containing risk analysis
    """
    try:
        stock = yf.Ticker(ticker)
        # Get 1 year of daily data
        hist = stock.history(interval="1d", period="1y")
        
        if hist.empty:
            return {"error": "Failed to retrieve historical data"}
        
        logger.info(f"Retrieved {len(hist)} days of historical data for {ticker}")
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        if len(returns) < 200:  # Minimum required trading days
            return {"error": f"Insufficient historical data: only {len(returns)} days available"}
        
        # Calculate risk metrics
        daily_volatility = returns.std()
        annual_volatility = daily_volatility * np.sqrt(252)  # Annualize volatility
        avg_daily_return = returns.mean()
        annual_return = ((1 + avg_daily_return) ** 252) - 1
        sharpe_ratio = (annual_return) / annual_volatility  # Assuming risk-free rate of 0 for simplicity
        
        # Calculate Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)  # 95% VaR
        var_99 = np.percentile(returns, 1)  # 99% VaR
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = cumulative_returns/rolling_max - 1
        max_drawdown = drawdowns.min()
        
        # Calculate beta (market sensitivity)
        try:
            spy = yf.Ticker("SPY").history(period="1y")['Close'].pct_change().dropna()
            common_dates = returns.index.intersection(spy.index)
            if len(common_dates) > 200:
                beta = returns.cov(spy) / spy.var()
            else:
                beta = None
        except Exception as e:
            logger.warning(f"Failed to calculate beta: {str(e)}")
            beta = None
        
        # Current price and historical context
        current_price = hist['Close'].iloc[-1]
        high_52week = hist['High'].max()
        low_52week = hist['Low'].min()
        
        risk_metrics = {
            "ticker": ticker,
            "current_price": current_price,
            "price_metrics": {
                "52_week_high": high_52week,
                "52_week_low": low_52week,
                "distance_from_high": ((high_52week - current_price) / current_price) * 100,
                "distance_from_low": ((current_price - low_52week) / low_52week) * 100
            },
            "return_metrics": {
                "annual_return": annual_return * 100,  # Convert to percentage
                "daily_volatility": daily_volatility * 100,
                "annual_volatility": annual_volatility * 100,
                "sharpe_ratio": sharpe_ratio
            },
            "risk_metrics": {
                "value_at_risk_95": abs(var_95 * 100),  # 95% VaR as percentage
                "value_at_risk_99": abs(var_99 * 100),  # 99% VaR as percentage
                "maximum_drawdown": abs(max_drawdown * 100),
                "beta": beta
            },
            "risk_assessment": {
                "volatility_level": "High" if annual_volatility > 0.3 else "Medium" if annual_volatility > 0.15 else "Low",
                "sharpe_ratio_assessment": "Excellent" if sharpe_ratio > 1.5 else "Good" if sharpe_ratio > 1 else "Poor",
                "beta_assessment": "Aggressive" if beta and beta > 1.2 else "Defensive" if beta and beta < 0.8 else "Market-like" if beta else "Unknown",
                "overall_risk": "High" if annual_volatility > 0.3 or abs(max_drawdown) > 0.3 else "Medium" if annual_volatility > 0.15 or abs(max_drawdown) > 0.2 else "Low"
            }
        }
        
        return risk_metrics
        
    except Exception as e:
        logger.error(f"Error in analyze_stock_risk: {str(e)}")
        return {"error": f"Failed to analyze stock risk: {str(e)}"}

@mcp.tool()
def compare_stocks(tickers: list) -> dict:
    """Compare multiple stocks based on key metrics.
    
    Args:
        tickers: List of stock ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        
    Returns:
        Dictionary containing comparison results
    """
    try:
        results = {}
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get historical data for return calculation
            hist = stock.history(period="1y")
            returns = hist['Close'].pct_change()
            annual_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            
            results[ticker] = {
                "name": info.get("longName"),
                "current_price": info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "dividend_yield": info.get("dividendYield"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "beta": info.get("beta"),
                "annual_return": annual_return,
                "volatility": returns.std() * np.sqrt(252) * 100,  # Annualized volatility in percentage
                "analyst_rating": info.get("recommendationKey"),
                "analyst_target_price": info.get("targetMeanPrice")
            }
        
        # Calculate relative metrics
        if len(results) > 1:
            # Find best and worst performers
            annual_returns = {ticker: data["annual_return"] for ticker, data in results.items()}
            best_performer = max(annual_returns.items(), key=lambda x: x[1])[0]
            worst_performer = min(annual_returns.items(), key=lambda x: x[1])[0]
            
            # Add comparison summary
            results["comparison_summary"] = {
                "best_performer": best_performer,
                "worst_performer": worst_performer,
                "highest_pe": max(results.items(), key=lambda x: x[1].get("pe_ratio", 0))[0],
                "lowest_pe": min(results.items(), key=lambda x: x[1].get("pe_ratio", float('inf')))[0],
                "highest_dividend": max(results.items(), key=lambda x: x[1].get("dividend_yield", 0))[0],
                "lowest_risk": min(results.items(), key=lambda x: x[1].get("beta", float('inf')))[0]
            }
        
        return results
    except Exception as e:
        logger.error(f"Error in compare_stocks: {str(e)}")
        return {"error": f"Failed to compare stocks: {str(e)}"}

@mcp.tool()
def get_sector_performance() -> dict:
    """Get performance analysis of different market sectors.
    
    Returns:
        Dictionary containing sector performance data
    """
    try:
        # List of major sector ETFs
        sector_etfs = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financial": "XLF",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Energy": "XLE",
            "Industrial": "XLI",
            "Materials": "XLB",
            "Utilities": "XLU",
            "Real Estate": "XLRE"
        }
        
        performance = {}
        spy = yf.Ticker("SPY").history(period="1mo")  # S&P 500 for reference
        spy_return = ((spy['Close'].iloc[-1] / spy['Close'].iloc[0]) - 1) * 100
        
        for sector, etf in sector_etfs.items():
            stock = yf.Ticker(etf)
            hist = stock.history(period="1mo")
            if not hist.empty:
                monthly_return = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
                performance[sector] = {
                    "current_price": hist['Close'].iloc[-1],
                    "monthly_return": monthly_return,
                    "relative_to_sp500": monthly_return - spy_return,
                    "volatility": hist['Close'].pct_change().std() * 100,
                    "volume_trend": "Up" if hist['Volume'].iloc[-1] > hist['Volume'].mean() else "Down",
                    "momentum": "Strong" if monthly_return > spy_return + 5 else "Weak" if monthly_return < spy_return - 5 else "Neutral"
                }
        
        # Add sector rotation analysis
        performance["sector_rotation"] = {
            "leading_sectors": sorted(performance.items(), key=lambda x: x[1]["monthly_return"], reverse=True)[:3],
            "lagging_sectors": sorted(performance.items(), key=lambda x: x[1]["monthly_return"])[:3],
            "most_volatile": max(performance.items(), key=lambda x: x[1]["volatility"])[0],
            "least_volatile": min(performance.items(), key=lambda x: x[1]["volatility"])[0]
        }
        
        return performance
    except Exception as e:
        logger.error(f"Error in get_sector_performance: {str(e)}")
        return {"error": f"Failed to get sector performance: {str(e)}"}

@mcp.tool()
def get_market_sentiment() -> dict:
    """Get overall market sentiment analysis.
    
    Returns:
        Dictionary containing market sentiment data
    """
    try:
        # Get major indices
        indices = {
            "S&P 500": "^GSPC",
            "Nasdaq": "^IXIC",
            "Dow Jones": "^DJI",
            "VIX": "^VIX"
        }
        
        sentiment_data = {}
        
        for name, symbol in indices.items():
            index = yf.Ticker(symbol)
            hist = index.history(period="1mo")
            
            if not hist.empty:
                # Calculate technical indicators
                ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
                ma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
                current_price = hist['Close'].iloc[-1]
                monthly_return = ((current_price / hist['Close'].iloc[0]) - 1) * 100
                
                sentiment_data[name] = {
                    "current_level": current_price,
                    "monthly_return": monthly_return,
                    "trend": "Bullish" if current_price > ma20 > ma50 else "Bearish" if current_price < ma20 < ma50 else "Mixed",
                    "volatility": hist['Close'].pct_change().std() * 100
                }
        
        # Calculate overall market sentiment
        vix_level = sentiment_data["VIX"]["current_level"]
        sp500_trend = sentiment_data["S&P 500"]["trend"]
        
        overall_sentiment = "Bullish" if vix_level < 20 and sp500_trend == "Bullish" else \
                          "Bearish" if vix_level > 30 or sp500_trend == "Bearish" else \
                          "Neutral"
        
        sentiment_data["market_summary"] = {
            "overall_sentiment": overall_sentiment,
            "fear_index": "High" if vix_level > 30 else "Low" if vix_level < 20 else "Moderate",
            "market_condition": "Risk-On" if vix_level < 20 else "Risk-Off" if vix_level > 30 else "Neutral"
        }
        
        return sentiment_data
    except Exception as e:
        logger.error(f"Error in get_market_sentiment: {str(e)}")
        return {"error": f"Failed to get market sentiment: {str(e)}"}

@mcp.tool()
def get_stock_news(ticker: str, count: int = 4) -> dict:
    """
    Scrape the latest news links for a stock from finviz.com.
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
        count: Number of latest news articles to fetch (default: 4)
    Returns:
        Dictionary containing news URLs for the stock

    ---
    # Agent Prompt (recommended for best results)
    Get the latest news of {{ticker}} stock. For each article, read the full content, assess whether the sentiment is positive, negative, or neutral, and then write a summary of the overall sentiment and your conclusions about {{ticker}} based on these articles.
    ---
    """
    try:
        url = f"https://finviz.com/quote.ashx?t="+ticker
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to fetch Finviz page for {ticker}: Status {response.status_code}")
            return {"status": "error", "message": f"Failed to fetch Finviz page: Status {response.status_code}", "ticker": ticker}
        soup = BeautifulSoup(response.text, "html.parser")
        news_table = soup.find("table", id="news-table")
        if not news_table:
            logger.error(f"No news table found for {ticker} on Finviz.")
            return {"status": "error", "message": "No news table found on Finviz.", "ticker": ticker}
        # Handle both cases: with or without <tbody>
        tbody = news_table.find("tbody")
        rows = tbody.find_all("tr") if tbody else news_table.find_all("tr")
        news_links = []
        for tr in rows:
            link_div = tr.find("div", class_="news-link-left")
            if link_div:
                a_tag = link_div.find("a", href=True)
                if a_tag and a_tag["href"]:
                    news_links.append({
                        "title": a_tag.get_text(strip=True),
                        "url": a_tag["href"]
                    })
            if len(news_links) >= count:
                break
        if not news_links:
            return {"status": "error", "message": f"No news links found for {ticker} on Finviz.", "ticker": ticker}
        return {
            "status": "success",
            "ticker": ticker,
            "news_count": len(news_links),
            "news": news_links
        }
    except Exception as e:
        logger.error(f"Error in get_stock_news for {ticker}: {str(e)}")
        return {"status": "error", "message": f"Failed to scrape news: {str(e)}", "ticker": ticker}

if __name__ == "__main__":
    try:
        logger.info("Starting Stock Market Analysis Server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)