# Advanced Stock Market Analysis Server

A powerful, extensible server for advanced stock market analysis and insights, built using the Model Context Protocol (MCP) and yfinance. This project provides a suite of tools for retrieving, analyzing, and comparing stock data, as well as sector and market sentiment analysis.

## Features

- **Get Stock Info**: Retrieve basic information about any stock (name, price, market cap, P/E, etc.).
- **Get Stock History**: Fetch historical price and volume data for any stock, with robust error handling and retry logic.
- **Analyze Stock Trend**: Technical analysis using moving averages, RSI, MACD, Bollinger Bands, and volatility.
- **Analyze Stock Risk**: Quantitative risk metrics (volatility, Sharpe ratio, beta, VaR, drawdown, etc.).
- **Compare Stocks**: Compare multiple stocks on key metrics and performance.
- **Sector Performance**: Analyze the performance of major market sectors using sector ETFs.
- **Market Sentiment**: Assess overall market sentiment using major indices and the VIX.
- **Get Stock News**: Scrape and retrieve the latest news headlines and URLs for any stock from Finviz, with a recommended agent prompt for sentiment analysis and summary.

## Technology Stack

- **Python 3.8+**
- [yfinance](https://github.com/ranaroussi/yfinance) for stock data
- [fastapi](https://fastapi.tiangolo.com/) (required by MCP server)
- [requests](https://docs.python-requests.org/) and [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) for web scraping
- **MCP (Model Context Protocol)** for tool-based server architecture

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/edenmargolis/Advanced-Stock-Market-Analysis-MCP-Server
   cd Advanced-Stock-Market-Analysis-MCP-Server
   ```
2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

To start the server:
```bash
uv run mcp install main.py
```

You can then interact with the server using any MCP-compatible client or integration (such as Claude, Cursor, or other AI agents that support MCP tool calls).

## Example Tool Calls

- **Get stock info:**
  ```json
  { "ticker": "AAPL" }
  ```
- **Get stock history:**
  ```json
  { "ticker": "MSFT", "period": "1y" }
  ```
- **Analyze stock risk:**
  ```json
  { "ticker": "GOOGL" }
  ```
- **Compare stocks:**
  ```json
  { "tickers": ["AAPL", "MSFT", "GOOGL"] }
  ```
- **Get stock news:**
  ```json
  { "ticker": "TSLA", "count": 4 }
  ```

## Project Structure

- `main.py` — Main server implementation and tool definitions
- `requirements.txt` — Python dependencies
- `README.md` — Project documentation

## Notes
- All stock data is fetched live from Yahoo Finance via yfinance.
- News headlines and URLs are scraped from Finviz for the `get_stock_news` tool.
- Error handling and retry logic are built-in for robust operation.

## Agent Prompt for News Sentiment Analysis

When using the `get_stock_news` tool, use the following prompt for best results with an LLM agent:

```
Get the latest news of {{ticker}} stock. For each article, read the full content, assess whether the sentiment is positive, negative, or neutral, and then write a summary of the overall sentiment and your conclusions about {{ticker}} based on these articles.
```

---

*For questions or contributions, please open an issue or pull request on GitHub.*
