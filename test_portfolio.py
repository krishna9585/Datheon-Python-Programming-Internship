"""
test_portfolio.py — Automated tests for portfolio.py
Datheon Internship · Task 2

Run: python test_portfolio.py
No external libraries required — uses Python's built-in unittest.
"""

import csv
import io
import os
import sys
import tempfile
import unittest

# Add project root to path so we can import portfolio.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the pure-logic functions (no side effects at import time)
from portfolio import (
    calculate_holding,
    build_report_rows,
    load_sample_prices,
    get_prices,
    export_csv,
    fmt_usd,
    fmt_pct,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CALCULATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateHolding(unittest.TestCase):

    def test_basic_gain(self):
        """Buy at $100, now $150, qty 10 => profit $500, +50%."""
        result = calculate_holding(purchase_price=100.0,
                                   quantity=10,
                                   current_price=150.0)
        self.assertAlmostEqual(result["invested"],     1000.0, places=2)
        self.assertAlmostEqual(result["market_value"], 1500.0, places=2)
        self.assertAlmostEqual(result["profit_loss"],   500.0, places=2)
        self.assertAlmostEqual(result["return_pct"],     50.0, places=4)

    def test_basic_loss(self):
        """Buy at $200, now $150, qty 5 => loss -$250, -25%."""
        result = calculate_holding(purchase_price=200.0,
                                   quantity=5,
                                   current_price=150.0)
        self.assertAlmostEqual(result["invested"],      1000.0, places=2)
        self.assertAlmostEqual(result["market_value"],   750.0, places=2)
        self.assertAlmostEqual(result["profit_loss"],   -250.0, places=2)
        self.assertAlmostEqual(result["return_pct"],    -25.0,  places=4)

    def test_breakeven(self):
        """Buy price == current price => 0 profit."""
        result = calculate_holding(purchase_price=75.0,
                                   quantity=4,
                                   current_price=75.0)
        self.assertAlmostEqual(result["profit_loss"], 0.0, places=2)
        self.assertAlmostEqual(result["return_pct"],  0.0, places=4)

    def test_single_share(self):
        """Qty 1 — results equal per-share differences."""
        result = calculate_holding(purchase_price=50.0,
                                   quantity=1,
                                   current_price=60.0)
        self.assertAlmostEqual(result["invested"],     50.0, places=2)
        self.assertAlmostEqual(result["market_value"], 60.0, places=2)
        self.assertAlmostEqual(result["profit_loss"],  10.0, places=2)
        self.assertAlmostEqual(result["return_pct"],   20.0, places=4)

    def test_large_quantity(self):
        """Large quantities compute without overflow."""
        result = calculate_holding(purchase_price=10.0,
                                   quantity=1_000_000,
                                   current_price=11.0)
        self.assertAlmostEqual(result["profit_loss"], 1_000_000.0, places=2)
        self.assertAlmostEqual(result["return_pct"],         10.0,  places=4)

    def test_fractional_price(self):
        """Fractional prices produce accurate results."""
        result = calculate_holding(purchase_price=1.23,
                                   quantity=3,
                                   current_price=4.56)
        self.assertAlmostEqual(result["invested"],     3.69, places=2)
        self.assertAlmostEqual(result["market_value"], 13.68, places=2)
        self.assertAlmostEqual(result["profit_loss"],   9.99, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# 2. BUILD REPORT ROWS TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildReportRows(unittest.TestCase):

    def _make_holdings(self):
        return [
            {"ticker": "AAA", "purchase_price": 100.0, "quantity": 10},
            {"ticker": "BBB", "purchase_price": 200.0, "quantity":  5},
        ]

    def test_all_calculable(self):
        holdings = self._make_holdings()
        prices = {
            "AAA": (150.0, "DEMO"),
            "BBB": (180.0, "DEMO"),
        }
        rows, totals = build_report_rows(holdings, prices)

        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["calculable"])
        self.assertTrue(rows[1]["calculable"])

        # AAA: invested=1000, mktval=1500, P/L=+500
        self.assertAlmostEqual(rows[0]["profit_loss"], 500.0, places=2)
        # BBB: invested=1000, mktval=900, P/L=-100
        self.assertAlmostEqual(rows[1]["profit_loss"], -100.0, places=2)

        # Portfolio totals: invested=2000, mktval=2400, P/L=+400, ret=+20%
        self.assertAlmostEqual(totals["total_invested"],      2000.0, places=2)
        self.assertAlmostEqual(totals["total_market_value"],  2400.0, places=2)
        self.assertAlmostEqual(totals["total_profit_loss"],    400.0, places=2)
        self.assertAlmostEqual(totals["overall_return_pct"],    20.0, places=4)

    def test_missing_price(self):
        """Holding with None price should be non-calculable; totals exclude it."""
        holdings = self._make_holdings()
        prices = {
            "AAA": (150.0, "DEMO"),
            "BBB": (None, "not found"),
        }
        rows, totals = build_report_rows(holdings, prices)

        self.assertFalse(rows[1]["calculable"])
        self.assertIsNone(rows[1]["profit_loss"])

        # Totals should only reflect AAA
        self.assertAlmostEqual(totals["total_invested"],     1000.0, places=2)
        self.assertAlmostEqual(totals["total_market_value"], 1500.0, places=2)
        self.assertAlmostEqual(totals["total_profit_loss"],   500.0, places=2)
        self.assertAlmostEqual(totals["overall_return_pct"],   50.0, places=4)

    def test_no_calculable_holdings(self):
        """All prices missing => totals are all zero."""
        holdings = [{"ticker": "XXX", "purchase_price": 50.0, "quantity": 2}]
        prices = {"XXX": (None, "not found")}
        rows, totals = build_report_rows(holdings, prices)

        self.assertFalse(rows[0]["calculable"])
        self.assertEqual(totals["total_invested"], 0.0)
        self.assertEqual(totals["total_profit_loss"], 0.0)
        self.assertEqual(totals["overall_return_pct"], 0.0)

    def test_duplicate_ticker(self):
        """If user enters the same ticker twice, each row is computed independently."""
        holdings = [
            {"ticker": "AAA", "purchase_price": 100.0, "quantity": 5},
            {"ticker": "AAA", "purchase_price": 120.0, "quantity": 5},
        ]
        prices = {"AAA": (150.0, "DEMO")}
        rows, totals = build_report_rows(holdings, prices)

        self.assertEqual(len(rows), 2)
        # First lot:  invested=500, mktval=750, P/L=+250
        self.assertAlmostEqual(rows[0]["profit_loss"], 250.0, places=2)
        # Second lot: invested=600, mktval=750, P/L=+150
        self.assertAlmostEqual(rows[1]["profit_loss"], 150.0, places=2)
        # Total P/L = 400
        self.assertAlmostEqual(totals["total_profit_loss"], 400.0, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# 3. FORMATTING TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatters(unittest.TestCase):

    def test_fmt_usd_positive(self):
        self.assertEqual(fmt_usd(1234.5), " $1,234.50")

    def test_fmt_usd_negative(self):
        self.assertEqual(fmt_usd(-99.9), "-$99.90")

    def test_fmt_usd_zero(self):
        self.assertEqual(fmt_usd(0.0), " $0.00")

    def test_fmt_usd_none(self):
        self.assertEqual(fmt_usd(None), "N/A")

    def test_fmt_pct_positive(self):
        self.assertEqual(fmt_pct(12.5), "+12.50%")

    def test_fmt_pct_negative(self):
        self.assertEqual(fmt_pct(-5.75), "-5.75%")

    def test_fmt_pct_none(self):
        self.assertEqual(fmt_pct(None), "N/A")


# ─────────────────────────────────────────────────────────────────────────────
# 4. SAMPLE-PRICE LOADING TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadSamplePrices(unittest.TestCase):

    def _write_temp_csv(self, content: str) -> str:
        """Write content to a temp file and return its path."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def test_valid_csv(self):
        path = self._write_temp_csv(
            "ticker,demo_price,note\n"
            "AAPL,150.00,Test\n"
            "MSFT,300.00,Test\n"
        )
        prices = load_sample_prices(path)
        self.assertAlmostEqual(prices["AAPL"], 150.00, places=2)
        self.assertAlmostEqual(prices["MSFT"], 300.00, places=2)
        os.unlink(path)

    def test_missing_file(self):
        prices = load_sample_prices("/nonexistent/path/sample.csv")
        self.assertEqual(prices, {})

    def test_malformed_price_row_skipped(self):
        """Rows with bad price values are skipped; valid rows are kept."""
        path = self._write_temp_csv(
            "ticker,demo_price,note\n"
            "GOOD,50.00,ok\n"
            "BAD,not-a-number,bad\n"
        )
        prices = load_sample_prices(path)
        self.assertIn("GOOD", prices)
        self.assertNotIn("BAD", prices)
        os.unlink(path)

    def test_comment_rows_skipped(self):
        """Rows whose ticker starts with '#' are treated as comments."""
        path = self._write_temp_csv(
            "ticker,demo_price,note\n"
            "# This is a comment,0,ignored\n"
            "REAL,99.00,ok\n"
        )
        prices = load_sample_prices(path)
        self.assertIn("REAL", prices)
        self.assertNotIn("# THIS IS A COMMENT", prices)
        os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# 5. GET_PRICES (SAMPLE MODE) TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestGetPricesSampleMode(unittest.TestCase):
    """Test get_prices in sample mode using the real sample_prices.csv."""

    # Absolute path to the project's sample_prices.csv — works regardless of cwd
    _SAMPLE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "sample_prices.csv")

    def _prices(self, holdings):
        """Wrapper that always supplies the absolute sample CSV path."""
        return get_prices(holdings, use_live=False,
                          sample_file=self._SAMPLE_CSV)

    def test_known_ticker_found(self):
        """AAPL should be in sample_prices.csv."""
        holdings = [{"ticker": "AAPL", "purchase_price": 100.0, "quantity": 1}]
        result = self._prices(holdings)
        price, source = result["AAPL"]
        self.assertIsNotNone(price)
        self.assertGreater(price, 0)
        self.assertIn("DEMO", source)

    def test_unknown_ticker_returns_none(self):
        """A ticker not in the CSV must return None — not a made-up price."""
        holdings = [{"ticker": "ZZZNOTTHERE999", "purchase_price": 1.0, "quantity": 1}]
        result = self._prices(holdings)
        price, source = result["ZZZNOTTHERE999"]
        self.assertIsNone(price)
        self.assertNotIn("DEMO", source)  # Must not silently label as DEMO

    def test_duplicate_ticker_resolved_once(self):
        """Same ticker twice in holdings should resolve to a single price lookup."""
        holdings = [
            {"ticker": "AAPL", "purchase_price": 100.0, "quantity": 1},
            {"ticker": "AAPL", "purchase_price": 120.0, "quantity": 2},
        ]
        result = self._prices(holdings)
        self.assertEqual(len(result), 1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CSV EXPORT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestExportCSV(unittest.TestCase):

    def setUp(self):
        """Build a minimal set of rows and totals for export tests."""
        self.rows = [
            {
                "ticker": "AAPL", "purchase_price": 150.0, "quantity": 10,
                "current_price": 180.0, "invested": 1500.0,
                "market_value": 1800.0, "profit_loss": 300.0,
                "return_pct": 20.0, "source": "DEMO (not real-time)",
                "calculable": True,
            },
            {
                "ticker": "TSLA", "purchase_price": 250.0, "quantity": 4,
                "current_price": None, "invested": 1000.0,
                "market_value": None, "profit_loss": None,
                "return_pct": None, "source": "not found in sample_prices.csv",
                "calculable": False,
            },
        ]
        self.totals = {
            "total_invested": 1500.0,
            "total_market_value": 1800.0,
            "total_profit_loss": 300.0,
            "overall_return_pct": 20.0,
        }
        self.timestamp = "2026-10-25 09:00:00"

    def test_csv_created(self):
        """export_csv should return True and create the file."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        success = export_csv(self.rows, self.totals, self.timestamp,
                             use_live=False, filepath=path)
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(path))
        os.unlink(path)

    def test_csv_contains_header(self):
        """The CSV must contain the expected column headers."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        with open(path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("ticker", content)
        self.assertIn("purchase_price", content)
        self.assertIn("profit_loss", content)
        self.assertIn("return_pct", content)
        self.assertIn("price_source", content)
        os.unlink(path)

    def test_csv_contains_totals_row(self):
        """The CSV must include a TOTAL row at the end."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        with open(path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("TOTAL", content)
        os.unlink(path)

    def test_csv_contains_demo_warning(self):
        """The CSV header comment must warn that prices are not real-time."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        with open(path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("NOT real-time", content)
        os.unlink(path)

    def test_csv_none_price_is_na(self):
        """A holding with no price must appear as 'N/A' not a numeric value."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        # Read back the data rows (skip comment lines starting with #)
        data_lines = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.startswith("#"):
                    data_lines.append(line)

        reader = csv.DictReader(data_lines)
        for row in reader:
            if row["ticker"] == "TSLA":
                self.assertEqual(row["current_price"], "N/A")
                self.assertEqual(row["market_value"],  "N/A")
                self.assertEqual(row["profit_loss"],   "N/A")
                break
        os.unlink(path)

    def test_csv_values_rounded(self):
        """Numeric values in the CSV should be formatted to 2 decimal places."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        data_lines = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if not line.startswith("#"):
                    data_lines.append(line)

        reader = csv.DictReader(data_lines)
        for row in reader:
            if row["ticker"] == "AAPL":
                # These should be exactly 2-decimal strings
                self.assertEqual(row["purchase_price"], "150.00")
                self.assertEqual(row["invested"],       "1500.00")
                self.assertEqual(row["market_value"],   "1800.00")
                self.assertEqual(row["profit_loss"],    "300.00")
                break
        os.unlink(path)

    def test_csv_timestamp_present(self):
        """The timestamp must appear somewhere in the CSV file."""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        export_csv(self.rows, self.totals, self.timestamp,
                   use_live=False, filepath=path)

        with open(path, encoding="utf-8") as fh:
            content = fh.read()

        self.assertIn("2026-10-25", content)
        os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  Datheon Stock Portfolio Tracker — Automated Test Suite")
    print("=" * 65 + "\n")
    unittest.main(verbosity=2)
