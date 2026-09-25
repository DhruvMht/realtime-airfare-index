"""
Tests for DGCA Benchmark Backtesting and Econometric Verification
"""

import pytest
from apix.database.db import DatabaseManager
from apix.backtest.backtester import DGCABacktester

def test_dgca_90day_backtest_performance():
    """Verify that the 90-day backtest achieves high correlation with DGCA monthly averages."""
    db = DatabaseManager()
    backtester = DGCABacktester(db)
    metrics = backtester.evaluate_90day_backtest()

    assert metrics["status"] != "NO_DATA" if "status" in metrics else True
    assert metrics["pearson_correlation"] >= 0.88
    assert metrics["mape_pct"] <= 5.0
    assert len(metrics["monthly_comparison"]) >= 3
    assert "VALIDATED" in metrics["validation_verdict"]

def test_dgca_monthly_benchmarks_structure():
    from apix.backtest.backtester import DGCA_MONTHLY_BENCHMARKS
    assert "2026-06" in DGCA_MONTHLY_BENCHMARKS
    assert "2026-07" in DGCA_MONTHLY_BENCHMARKS
    assert "2026-08" in DGCA_MONTHLY_BENCHMARKS
    for m, d in DGCA_MONTHLY_BENCHMARKS.items():
        assert "weighted_avg" in d
        assert d["weighted_avg"] > 4000.0
