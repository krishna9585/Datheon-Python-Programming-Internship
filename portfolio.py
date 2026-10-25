"""
portfolio.py — Stock Portfolio Performance Tracker
Datheon Internship · Task 2

Run: python portfolio.py
Requires:  pip install yfinance   (optional — for live prices)
Fallback:  sample_prices.csv      (always available, labelled as DEMO data)
"""

import csv
import os
import sys
from datetime import datetime

# ── Optional live-price dependency ──────────────────────────────────────────
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ── Constants ────────────────────────────────────────────────────────────────
SAMPLE_PRICES_FILE = "sample_prices.csv"
OUTPUT_CSV_FILE    = "portfolio_summary.csv"
DEMO_LABEL         = "DEMO (not real-time)"
LIVE_LABEL         = "Live (yfinance)"

# ─────────────────────────────────────────────────────────────────────────────
# INPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def prompt_positive_float(prompt_text: str) -> float:
    """Ask the user for a positive floating-point number; loop until valid."""
    while True:
        raw = input(prompt_text).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("  x Value must be greater than zero. Please try again.")
                continue
            return value
        except ValueError:
            print(f"  x '{raw}' is not a valid number. Please try again.")


def prompt_positive_int(prompt_text: str) -> int:
    """Ask the user for a positive whole-number quantity; loop until valid."""
    while True:
        raw = input(prompt_text).strip()
        try:
            value = int(raw)
            if value <= 0:
                print("  x Quantity must be a positive whole number. Please try again.")
                continue
            return value
        except ValueError:
            print(f"  x '{raw}' is not a valid integer. Please try again.")


def collect_holdings() -> list:
    """
    Interactively collect one or more stock holdings from the user.
    Returns a list of dicts: {ticker, purchase_price, quantity}
    """
    holdings = []
    print("\n" + "=" * 60)
    print("  STOCK PORTFOLIO PERFORMANCE TRACKER")
    print("  Datheon Internship - Task 2")
    print("=" * 60)
    print("  Enter each stock holding below.")
    print("  Type 'done' when finished.\n")

    while True:
        ticker_raw = input("  Ticker symbol (or 'done' to finish): ").strip().upper()

        if ticker_raw.lower() == "done" or ticker_raw == "DONE":
            if not holdings:
                print("  x You must enter at least one holding before finishing.")
                continue
            break

        if not ticker_raw:
            print("  x Ticker cannot be empty.")
            continue

        # Basic sanity check -- tickers are typically 1-5 alphanumeric chars
        if not all(c.isalnum() or c in "-." for c in ticker_raw):
            print("  x Ticker contains invalid characters. Use letters, digits, '-', or '.'.")
            continue

        purchase_price = prompt_positive_float(f"  Purchase price for {ticker_raw} (USD): $")
        quantity       = prompt_positive_int(f"  Number of shares of {ticker_raw}: ")

        holdings.append({
            "ticker":         ticker_raw,
            "purchase_price": purchase_price,
            "quantity":       quantity,
        })
        print(f"  Added {quantity} share(s) of {ticker_raw} @ ${purchase_price:.2f}\n")

    return holdings


# ─────────────────────────────────────────────────────────────────────────────
# PRICE RETRIEVAL
# ─────────────────────────────────────────────────────────────────────────────

def load_sample_prices(filepath: str = SAMPLE_PRICES_FILE) -> dict:
    """
    Load demonstration prices from the CSV file.
    Returns {TICKER: price} or {} if the file is missing / malformed.
    Clearly labels every price as demo data.
    """
    prices = {}
    if not os.path.isfile(filepath):
        print(f"  WARNING: Sample-price file '{filepath}' not found.")
        return prices

    try:
        with open(filepath, newline="", encoding="utf-8") as fh:
            # Filter out comment lines before passing to DictReader.
            # The CSV has '# ...' comments above the actual header row.
            non_comment_lines = (line for line in fh if not line.startswith("#"))
            reader = csv.DictReader(non_comment_lines)
            for row in reader:
                ticker = row.get("ticker", "").strip().upper()
                if not ticker:
                    continue
                try:
                    price = float(row["demo_price"])
                    prices[ticker] = price
                except (KeyError, ValueError):
                    pass  # Skip malformed rows silently
    except OSError as exc:
        print(f"  x Could not read '{filepath}': {exc}")

    return prices


def fetch_live_price(ticker: str) -> tuple:
    """
    Try to fetch the current price via yfinance.
    Returns (price, source_label) or (None, error_description).
    Never substitutes a sample price for a failed live lookup.
    """
    if not YFINANCE_AVAILABLE:
        return None, "yfinance not installed"

    try:
        info  = yf.Ticker(ticker).fast_info
        price = info.last_price
        if price is None or price <= 0:
            return None, "no price returned by yfinance"
        return price, LIVE_LABEL
    except Exception as exc:
        return None, f"yfinance error: {exc}"


def get_prices(holdings: list, use_live: bool,
               sample_file: str = None) -> dict:
    """
    Retrieve prices for all tickers in holdings.
    Returns {ticker: (price_or_None, source_label)}.

    Rules:
      - If use_live is True:   attempt live lookup first; if it fails, report
                               the failure clearly -- do NOT fall back to sample.
      - If use_live is False:  look up sample_prices.csv only.

    sample_file: override the sample CSV path (used by tests).
    """
    csv_path     = sample_file if sample_file is not None else SAMPLE_PRICES_FILE
    sample_prices = load_sample_prices(csv_path)
    result = {}

    for holding in holdings:
        ticker = holding["ticker"]
        if ticker in result:
            continue  # Already resolved (duplicate tickers are fine)

        if use_live:
            price, source = fetch_live_price(ticker)
            if price is None:
                # Report failure -- do NOT silently substitute sample data
                result[ticker] = (None, f"FAILED live lookup ({source})")
            else:
                result[ticker] = (price, source)
        else:
            # Sample-data mode
            if ticker in sample_prices:
                result[ticker] = (sample_prices[ticker], DEMO_LABEL)
            else:
                result[ticker] = (None, "not found in sample_prices.csv")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_holding(purchase_price: float, quantity: int,
                      current_price: float) -> dict:
    """
    Compute per-holding metrics.
    Returns dict with: invested, market_value, profit_loss, return_pct
    """
    invested      = purchase_price * quantity
    market_value  = current_price  * quantity
    profit_loss   = market_value   - invested
    return_pct    = (profit_loss / invested) * 100 if invested else 0.0

    return {
        "invested":     invested,
        "market_value": market_value,
        "profit_loss":  profit_loss,
        "return_pct":   return_pct,
    }


def build_report_rows(holdings: list, prices: dict) -> tuple:
    """
    Combine holdings + prices into report rows and portfolio totals.
    Returns (rows, totals).
    """
    rows = []

    total_invested     = 0.0
    total_market_value = 0.0
    total_profit_loss  = 0.0

    for h in holdings:
        ticker         = h["ticker"]
        purchase_price = h["purchase_price"]
        quantity       = h["quantity"]
        current_price, source = prices.get(ticker, (None, "unknown"))

        if current_price is None:
            # Cannot calculate -- include in report but mark as N/A
            rows.append({
                "ticker":         ticker,
                "purchase_price": purchase_price,
                "quantity":       quantity,
                "current_price":  None,
                "invested":       purchase_price * quantity,
                "market_value":   None,
                "profit_loss":    None,
                "return_pct":     None,
                "source":         source,
                "calculable":     False,
            })
        else:
            metrics = calculate_holding(purchase_price, quantity, current_price)
            total_invested     += metrics["invested"]
            total_market_value += metrics["market_value"]
            total_profit_loss  += metrics["profit_loss"]

            rows.append({
                "ticker":         ticker,
                "purchase_price": purchase_price,
                "quantity":       quantity,
                "current_price":  current_price,
                "invested":       metrics["invested"],
                "market_value":   metrics["market_value"],
                "profit_loss":    metrics["profit_loss"],
                "return_pct":     metrics["return_pct"],
                "source":         source,
                "calculable":     True,
            })

    overall_return_pct = (
        (total_profit_loss / total_invested) * 100
        if total_invested > 0 else 0.0
    )

    totals = {
        "total_invested":      total_invested,
        "total_market_value":  total_market_value,
        "total_profit_loss":   total_profit_loss,
        "overall_return_pct":  overall_return_pct,
    }

    return rows, totals


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def fmt_usd(value) -> str:
    """Format a number as USD with two decimal places, or 'N/A'."""
    if value is None:
        return "N/A"
    sign = "-" if value < 0 else " "
    return f"{sign}${abs(value):,.2f}"


def fmt_pct(value) -> str:
    """Format a number as a percentage with two decimal places, or 'N/A'."""
    if value is None:
        return "N/A"
    sign = "-" if value < 0 else "+"
    return f"{sign}{abs(value):.2f}%"


def print_report(rows: list, totals: dict, timestamp: str,
                 use_live: bool) -> None:
    """Print the formatted console table."""
    mode_label = (
        "LIVE prices (yfinance)"
        if use_live
        else "DEMO prices (sample_prices.csv — NOT real-time)"
    )

    print("\n" + "=" * 100)
    print(f"  PORTFOLIO REPORT  |  {timestamp}  |  Source: {mode_label}")
    print("=" * 100)

    # Column widths
    w = {"ticker": 8, "qty": 6, "buy": 11, "cur": 11,
         "invested": 13, "mktval": 13, "pl": 13, "ret": 10}

    # Header
    header = (
        f"  {'Ticker':<{w['ticker']}}"
        f"{'Qty':>{w['qty']}}"
        f"{'Buy Price':>{w['buy']}}"
        f"{'Cur Price':>{w['cur']}}"
        f"{'Invested':>{w['invested']}}"
        f"{'Mkt Value':>{w['mktval']}}"
        f"{'Profit/Loss':>{w['pl']}}"
        f"{'Return':>{w['ret']}}"
        f"  Source"
    )
    print(header)
    print("  " + "-" * 98)

    for row in rows:
        pl_val  = row["profit_loss"]
        ret_val = row["return_pct"]

        line = (
            f"  {row['ticker']:<{w['ticker']}}"
            f"{row['quantity']:>{w['qty']}}"
            f"{fmt_usd(row['purchase_price']):>{w['buy']}}"
            f"{fmt_usd(row['current_price']):>{w['cur']}}"
            f"{fmt_usd(row['invested']):>{w['invested']}}"
            f"{fmt_usd(row['market_value']):>{w['mktval']}}"
            f"{fmt_usd(pl_val):>{w['pl']}}"
            f"{fmt_pct(ret_val):>{w['ret']}}"
            f"  {row['source']}"
        )
        print(line)

    print("  " + "-" * 98)

    # Totals row (only for calculable holdings)
    t_pl  = totals["total_profit_loss"]
    t_ret = totals["overall_return_pct"]
    totals_line = (
        f"  {'TOTAL':<{w['ticker']}}"
        f"{'':>{w['qty']}}"
        f"{'':>{w['buy']}}"
        f"{'':>{w['cur']}}"
        f"{fmt_usd(totals['total_invested']):>{w['invested']}}"
        f"{fmt_usd(totals['total_market_value']):>{w['mktval']}}"
        f"{fmt_usd(t_pl):>{w['pl']}}"
        f"{fmt_pct(t_ret):>{w['ret']}}"
    )
    print(totals_line)
    print("=" * 100)

    if not use_live:
        print("\n  WARNING: DEMO MODE — Prices are for illustration only.")
        print("  They are NOT real-time market prices.")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# CSV EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def export_csv(rows: list, totals: dict, timestamp: str,
               use_live: bool, filepath: str = OUTPUT_CSV_FILE) -> bool:
    """
    Write portfolio_summary.csv using Python's built-in csv module.
    Returns True on success, False on failure.
    """
    fieldnames = [
        "ticker", "purchase_price", "quantity", "current_price",
        "invested", "market_value", "profit_loss", "return_pct",
        "price_source",
    ]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            # Metadata header comments
            fh.write("# Datheon Stock Portfolio Performance Tracker\n")
            fh.write(f"# Generated: {timestamp}\n")
            mode = "LIVE (yfinance)" if use_live else "DEMO (sample_prices.csv — NOT real-time)"
            fh.write(f"# Price source mode: {mode}\n")
            if not use_live:
                fh.write("# WARNING: DEMO prices are NOT real-time market prices.\n")
            fh.write("#\n")

            # Data rows
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                writer.writerow({
                    "ticker":         row["ticker"],
                    "purchase_price": f"{row['purchase_price']:.2f}",
                    "quantity":       row["quantity"],
                    "current_price":  (
                        f"{row['current_price']:.2f}"
                        if row["current_price"] is not None else "N/A"
                    ),
                    "invested":       f"{row['invested']:.2f}",
                    "market_value":   (
                        f"{row['market_value']:.2f}"
                        if row["market_value"] is not None else "N/A"
                    ),
                    "profit_loss":    (
                        f"{row['profit_loss']:.2f}"
                        if row["profit_loss"] is not None else "N/A"
                    ),
                    "return_pct":     (
                        f"{row['return_pct']:.4f}"
                        if row["return_pct"] is not None else "N/A"
                    ),
                    "price_source":   row["source"],
                })

            # Totals row
            writer.writerow({
                "ticker":         "TOTAL",
                "purchase_price": "",
                "quantity":       "",
                "current_price":  "",
                "invested":       f"{totals['total_invested']:.2f}",
                "market_value":   f"{totals['total_market_value']:.2f}",
                "profit_loss":    f"{totals['total_profit_loss']:.2f}",
                "return_pct":     f"{totals['overall_return_pct']:.4f}",
                "price_source":   "",
            })

        return True

    except OSError as exc:
        print(f"  x Could not write '{filepath}': {exc}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Entry point: collect holdings, fetch prices, display report, export CSV."""

    # 1. Decide price mode
    if YFINANCE_AVAILABLE:
        print("\n  yfinance is installed. Would you like to fetch LIVE prices?")
        print("  (If you choose No, DEMO prices from sample_prices.csv will be used.)\n")
        choice = input("  Fetch live prices? [y/N]: ").strip().lower()
        use_live = choice == "y"
    else:
        print("\n  yfinance is NOT installed -- running in DEMO mode.")
        print("  Install it with:  pip install yfinance\n")
        use_live = False

    # 2. Collect holdings
    try:
        holdings = collect_holdings()
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user. Exiting.")
        sys.exit(0)

    # 3. Fetch prices
    print("\n  Fetching prices... ", end="", flush=True)
    prices = get_prices(holdings, use_live)
    print("done.\n")

    # 4. Build report rows
    rows, totals = build_report_rows(holdings, prices)

    # 5. Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 6. Display console table
    print_report(rows, totals, timestamp, use_live)

    # 7. Export CSV
    success = export_csv(rows, totals, timestamp, use_live)
    if success:
        print(f"  Report saved to '{OUTPUT_CSV_FILE}'")
    else:
        print(f"  Failed to save report to '{OUTPUT_CSV_FILE}'")

    print()


if __name__ == "__main__":
    main()
