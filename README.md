# Market Lens — Stock Analysis Dashboard

Market Lens is a full-stack stock analysis dashboard that lets users search for stocks, explore historical price data, compare companies, and evaluate technical indicators through an interactive web interface.

## Live Demo

- Frontend: **GitHub Pages**
- Backend API: **Render**
- GitHub: **https://github.com/tenn-1/Market-Lens**
- Accessible at **https://tenn-1.github.io/Market-Lens/**

## Features

- Search for stocks and add them to a personal watchlist
- View historical price data across 1M, 6M, 1Y, 2Y, and 3Y timeframes
- Compare multiple stocks on the same price chart
- Display 20-day and 200-day moving averages
- Detect and display Golden Cross and Death Cross signals
- View Bollinger Bands, RSI (14), and MACD indicators
- Visualize trading volume and daily returns
- Screen watchlist stocks using a composite technical score based on trend, momentum, and RSI
- Automatically fetch market data from the backend and fall back to simulated data when the API is unavailable

## Tech Stack

**Frontend**
- HTML/CSS
- JavaScript
- Chart.js

**Backend**
- Python
- REST API
- yfinance

**Deployment / Tools**
- GitHub
- GitHub Pages
- Render

## Architecture

```text
User
  ↓
GitHub Pages Frontend
  ↓
JavaScript / REST API Requests
  ↓
Python Backend on Render
  ↓
yfinance
  ↓
Market Data
  ↓
Technical Analysis
  ↓
JSON Response
  ↓
Interactive Charts / Screener
```

The frontend requests stock data from the Python backend. The backend retrieves market data and returns the values needed by the dashboard, including prices, volume, moving averages, Bollinger Bands, and RSI. The frontend renders the results with Chart.js and performs additional calculations such as MACD, cross detection, and screener scoring.

## Technical Analysis

Market Lens calculates and displays several commonly used technical indicators:

- **MA-20:** 20-trading-day moving average
- **MA-200:** 200-trading-day moving average
- **Golden Cross:** Detects when MA-20 crosses above MA-200
- **Death Cross:** Detects when MA-20 crosses below MA-200
- **RSI (14):** Momentum indicator
- **MACD:** Uses 12-day and 26-day exponential moving averages with a 9-day signal line
- **Bollinger Bands:** Uses the 20-day moving average and a two-standard-deviation range

## Screener

The screener ranks stocks currently in the watchlist using a simple composite technical score. The score considers:

- Current MA-20 / MA-200 trend state
- One-month price momentum
- RSI positioning
- Recent Golden Cross activity

Stocks are grouped into **Promising**, **Watch**, and **Weak** categories based on the resulting score.

The screener is intended as an educational technical-analysis tool and is **not investment advice**.

## Deployment

The frontend is hosted through GitHub, while the Python backend is deployed on Render.

The frontend communicates with the deployed backend through REST API requests to retrieve market data and analysis results.


## Project Structure

```text
market-lens/                 
├── index.html            
├── README.md
└── backend/
    ├── app.py
    ├── requirements.txt
    ├── runtime.txt
    └── Procfile
```

Market Lens is an educational project. Market data availability depends on the external data provider.