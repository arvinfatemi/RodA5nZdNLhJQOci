# Smart Bitcoin Trading Bot

## Overview
This project is a fintech initiative to build a **smart Bitcoin trading system** designed to operate with minimal human supervision.  
The bot continuously adapts to changing market conditions by dynamically managing budget allocation, shifting between strategies, and making autonomous trading decisions — all while running 24/7 in the cloud.

The goal is to integrate **long-term accumulation (DCA)** with **short-term active trading (ATR-based stop-loss, opportunistic trades, etc.)**, enhanced with optional **LLM-assisted decision-making**.

---

## Key Objectives
- Accept a configurable trading budget (e.g., $1K – $100K)
- Use **Dollar-Cost Averaging (DCA)** to accumulate more BTC over time
- Implement an **ATR-based stop-loss strategy** to manage losses in active trades
- Switch between trading strategies:
  - Day trading
  - Swing trading
  - Value investing
- Adapt continuously to market conditions
- Run **24/7** in a cloud environment
- Send **Telegram notifications** for each trade
- Send **weekly Gmail reports** every Monday at 9:00 AM

## Phase 1 Objectives
- connect to gsheet and fetch config
- read market data from coinbase advanced trade API - websocket
- read market data from coinbase advanced trade API - rest API
- send messages to Telegram
- send weekly Gmail reports
---

## Strategy Concepts

### Dollar-Cost Averaging (DCA)
Buy small amounts of BTC at regular intervals or after defined percentage drops.  
Helps reduce the impact of volatility and smooths the entry price.

### Average True Range (ATR) Stop-Loss
ATR measures market volatility.  
For active trades: