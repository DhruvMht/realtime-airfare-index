"""
Tests for Two-Tier Jevons-Laspeyres Econometric Price Index Engine
"""

import pytest
import math
from apix.index.formulas import IndexFormulas

def test_two_tier_identity():
    """If elementary Jevons prices equal base prices, Two-Tier index must equal 100.0."""
    prices = {("BOM-DEL", 7): 5000.0, ("BLR-DEL", 15): 6000.0}
    base = {("BOM-DEL", 7): 5000.0, ("BLR-DEL", 15): 6000.0}
    weights = {("BOM-DEL", 7): 0.6, ("BLR-DEL", 15): 0.4}

    idx = IndexFormulas.two_tier_jevons_laspeyres_index(prices, base, weights)
    assert idx == 100.0

def test_two_tier_proportionality():
    """If all elementary prices increase uniformly by 20%, Two-Tier index must equal 120.0."""
    base = {("BOM-DEL", 7): 5000.0, ("BLR-DEL", 15): 6000.0}
    current = {("BOM-DEL", 7): 6000.0, ("BLR-DEL", 15): 7200.0}
    weights = {("BOM-DEL", 7): 0.5, ("BLR-DEL", 15): 0.5}

    idx = IndexFormulas.two_tier_jevons_laspeyres_index(current, base, weights)
    assert idx == 120.0

def test_two_tier_dgca_corridor_weighting():
    """Verifies that DGCA passenger traffic volume shares are accurately applied across corridors."""
    base = {("BOM-DEL", 7): 5000.0, ("BLR-DEL", 15): 6000.0}
    # BOM-DEL increased 10%, BLR-DEL increased 20%
    elem_jevons_prices = {("BOM-DEL", 7): 5500.0, ("BLR-DEL", 15): 7200.0}
    dgca_weights = {("BOM-DEL", 7): 0.6, ("BLR-DEL", 15): 0.4}

    idx = IndexFormulas.two_tier_jevons_laspeyres_index(elem_jevons_prices, base, dgca_weights)
    # Expected: 0.6 * (5500/5000) + 0.4 * (7200/6000) = 0.6 * 1.10 + 0.4 * 1.20 = 0.66 + 0.48 = 1.14 * 100 = 114.0
    assert idx == 114.0

def test_two_tier_surge_damping_property():
    """
    Demonstrates axiomatic superiority:
    Tier 1 Jevons geometric mean dampens an extreme holiday surge (+300% on one flight)
    significantly more than an arithmetic mean would, preventing artificial index inflation.
    """
    import numpy as np
    normal_quotes = [5000.0, 5200.0, 4800.0]
    surge_quote = [20000.0]  # Single last-minute surge spike
    all_quotes = normal_quotes + surge_quote

    # Arithmetic Mean (vulnerable to surge)
    arith_mean = np.mean(all_quotes)
    # Geometric Mean (Tier 1 Jevons - resilient)
    geom_mean = np.exp(np.mean(np.log(all_quotes)))

    assert geom_mean < arith_mean
    # Geometric mean suppresses the surge by over 1,500 rupees
    assert (arith_mean - geom_mean) > 1500.0
