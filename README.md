# Stock Portfolio Performance Tracker
**Datheon Internship — Task 2**

A beginner-friendly Python 3 command-line program that tracks your stock portfolio, calculates profit/loss metrics, and generates a CSV summary report.

---

## Table of Contents
1. [Requirements](#requirements)
2. [Setup & Installation](#setup--installation)
3. [How to Run](#how-to-run)
4. [Example Input & Output](#example-input--output)
5. [Calculations Explained](#calculations-explained)
6. [Price Modes](#price-modes)
7. [Generated Files](#generated-files)
8. [Limitations](#limitations)
9. [Running the Tests](#running-the-tests)

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.9 or newer |
| yfinance | 0.2.48+ (optional — for live prices only) |

All other modules used (`csv`, `os`, `sys`, `datetime`, `unittest`) are part of the Python standard library and need no installation.

---

## Setup & Installation

### Step 1 — Clone / download the project

Place all project files in one folder, for example:
```
Datheon_stock_tracker/
    portfolio.py
    test_portfolio.py
    sample_prices.csv
    requirements.txt
    README.md
```

### Step 2 — (Optional) Install live-price support

If you want **real-time prices** from the internet, install yfinance:

```bash
pip install -r requirements.txt
```

> **You do NOT need to install anything to use DEMO mode.** `sample_prices.csv` is always available.

---

## How to Run

Open a terminal (PowerShell, CMD, or any shell) in the project folder and run:

```bash
python portfolio.py
```

The program will:
1. Ask whether you want live prices (if yfinance is installed).
2. Prompt you to enter your stock holdings one at a time.
3. Type **`done`** when you've entered all your holdings.
4. Display the portfolio table in the terminal.
5. Save `portfolio_summary.csv` in the same folder.

---

## Example Input & Output

### You type:
```
  Fetch live prices? [y/N]: n

  Ticker symbol (or 'done' to finish): AAPL
  Purchase price for AAPL (USD): $180.00
  Number of shares of AAPL: 10

  Ticker symbol (or 'done' to finish): MSFT
  Purchase price for MSFT (USD): $400.00
  Number of shares of MSFT: 5

  Ticker symbol (or 'done' to finish): done
```

### You see:
```
====================================================================================================
  PORTFOLIO REPORT  |  2026-10-25 09:00:00  |  Source: DEMO prices (sample_prices.csv — NOT real-time)
====================================================================================================
  Ticker    Qty   Buy Price   Cur Price       Invested      Mkt Value  Profit/Loss    Return  Source
  --------------------------------------------------------------------------------------------------
  AAPL       10   $180.00     $227.52      $1,800.00      $2,275.20     +$475.20   +26.40%  DEMO (not real-time)
  MSFT        5   $400.00     $415.30      $2,000.00      $2,076.50      +$76.50    +3.83%  DEMO (not real-time)
  --------------------------------------------------------------------------------------------------
  TOTAL                                   $3,800.00      $4,351.70     +$551.70   +14.52%
====================================================================================================

  WARNING: DEMO MODE — Prices are for illustration only.
  They are NOT real-time market prices.

  Report saved to 'portfolio_summary.csv'
```

---

## Calculations Explained

For each holding:

| Metric | Formula |
|---|---|
| **Total Invested** | `purchase_price × quantity` |
| **Market Value** | `current_price × quantity` |
| **Profit / Loss** | `market_value − total_invested` |
| **Return %** | `(profit_loss ÷ total_invested) × 100` |

For the overall portfolio:

| Metric | Formula |
|---|---|
| **Total Invested** | Sum of all individual invested amounts |
| **Portfolio Value** | Sum of all individual market values |
| **Total P/L** | Sum of all individual profit/losses |
| **Overall Return %** | `(total_profit_loss ÷ total_invested) × 100` |

> Holdings with unavailable prices are **excluded from portfolio totals** but still appear in the report as `N/A`.

---

## Price Modes

### DEMO Mode (default / no internet needed)
- Prices are read from `sample_prices.csv`.
- Every price is clearly labelled **"DEMO (not real-time)"**.
- Available tickers: `AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, BRK-B, JPM`.
- Tickers **not** in the file are reported as `"not found in sample_prices.csv"` — the program will **never** silently substitute a made-up price.

### Live Mode (requires `pip install yfinance`)
- Prices are fetched from Yahoo Finance in real time.
- Each price is labelled **"Live (yfinance)"**.
- If a live lookup fails (network error, invalid ticker, etc.), the failure is clearly reported — the program will **never** silently fall back to sample data.

---

## Generated Files

### `portfolio_summary.csv`
Created automatically after each run. Contains:

| Column | Description |
|---|---|
| `ticker` | Stock ticker symbol |
| `purchase_price` | Your original buy price per share (USD) |
| `quantity` | Number of shares held |
| `current_price` | Price used for calculation (or `N/A`) |
| `invested` | Total amount invested |
| `market_value` | Current market value (or `N/A`) |
| `profit_loss` | Profit or loss in USD (or `N/A`) |
| `return_pct` | Percentage return (or `N/A`) |
| `price_source` | Where the price came from |

The file also includes:
- A metadata header (with generation timestamp and price mode warning).
- A **TOTAL** row at the bottom summarising the whole portfolio.

### `sample_prices.csv`
Provided demonstration prices for 10 popular tickers. Used in DEMO mode. **Not real-time.**

---

## Limitations

1. **DEMO prices are static** — they reflect manually recorded values and are not updated automatically.
2. **yfinance availability** — Yahoo Finance may occasionally be unavailable; the program handles this gracefully without crashing.
3. **No fractional shares** — quantities must be whole numbers (integers).
4. **Currency** — all prices are assumed to be in USD.
5. **No historical data** — only the current price vs. your purchase price is compared.
6. **No persistent storage** — holdings are entered fresh each run; there is no saved portfolio database.

---

## Running the Tests

```bash
python test_portfolio.py
```

The test suite covers:
- Calculation correctness (gain, loss, breakeven, large quantities, fractions)
- Portfolio totals with mixed calculable/non-calculable holdings
- Formatting functions (`fmt_usd`, `fmt_pct`)
- Sample-price CSV loading (valid file, missing file, malformed rows)
- `get_prices` in sample mode (known tickers, unknown tickers, duplicates)
- CSV export (file creation, headers, TOTAL row, N/A values, rounding, timestamps)

No internet connection is required to run the tests.
