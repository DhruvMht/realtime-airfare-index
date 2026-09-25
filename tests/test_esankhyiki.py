"""
Tests for eSankhyiki MoSPI PSD Integration & CPI Augmentation Module
"""

import pytest
import pandas as pd
from apix.index.esankhyiki import ESankhyikiManager, PSD_WEIGHTS, ESANKHYIKI_OFFICIAL_TRANSPORT_CPI
from apix.database.db import DatabaseManager

def test_psd_weights_structure():
    """Verify Price Statistics Division (PSD) weights conform to national accounts."""
    mgr = ESankhyikiManager()
    assert "transport_communication_weight_pct" in mgr.weights
    assert "airfare_share_in_transport_pct" in mgr.weights
    assert mgr.weights["airfare_share_in_transport_pct"] > 4.0
    assert mgr.weights["base_year"] == "2012=100"

def test_cpi_augmentation_calculation():
    """Verify that replacing manual counter airfare with APIx Two-Tier captures dynamic pricing gap."""
    db = DatabaseManager()
    df = db.get_daily_indices()
    assert not df.empty

    mgr = ESankhyikiManager()
    aug_records = mgr.compute_cpi_augmentation(df)
    assert len(aug_records) >= 3

    for rec in aug_records:
        assert "official_esankhyiki_cpi" in rec
        assert "augmented_transport_cpi" in rec
        assert "transport_gap_bps" in rec
        assert rec["reporting_lead_advantage_days"] == 45
        # During peak online summer demand, augmented CPI is higher than manual counter quotes
        if rec["month"] == "2026-06":
            assert rec["augmented_transport_cpi"] > rec["official_esankhyiki_cpi"]
            assert rec["transport_gap_bps"] > 0

def test_esankhyiki_batch_export_schema():
    """Verify export payload matches MoSPI eSankhyiki data warehouse specifications."""
    db = DatabaseManager()
    df = db.get_daily_indices()
    mgr = ESankhyikiManager()
    feed = mgr.generate_esankhyiki_feed(df)

    assert "metadata" in feed
    assert feed["metadata"]["source_portal"] == "eSankhyiki (National Data Warehouse of Official Statistics)"
    assert feed["metadata"]["custodian_division"] == "Price Statistics Division (PSD)"
    assert feed["metadata"]["division_code"] == "07 - Transport"
    assert "latest_observation" in feed
    assert "two_tier_index" in feed["latest_observation"]
    assert len(feed["dgca_corridor_coverage"]) == 15
    assert len(feed["advance_booking_horizons"]) == 5
