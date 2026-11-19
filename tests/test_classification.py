"""
Unit tests for Multicriteria ABCD Inventory Classification.
Tests:
- Cumulative-percentage boundaries (0-60%, 60-80%, 80-90%, 90-100%)
- Tie-breaking rules for equal Sales and equal Hits
- Input validation (missing columns, negative numbers, non-numeric, zero totals, empty)
- Score conversion (A=4, B=3, C=2, D=1) and weighting (0.65 Sales + 0.35 Hits)
- Final ABCD class assignment against threshold cutoffs (3.25, 2.50, 1.75)
- Intermediate audit columns and summary report generation
"""

import pytest
import pandas as pd
import numpy as np
from core.classification import (
    classify_multicriteria_abcd,
    generate_classification_summary,
    validate_inventory_dataframe,
    _assign_single_criterion_class,
    _assign_final_class
)


def test_single_criterion_boundary_cutoffs():
    """Validates exact threshold cutoffs: A (0-60%), B (60-80%), C (80-90%), D (90-100%)."""
    assert _assign_single_criterion_class(0.0) == "A"
    assert _assign_single_criterion_class(0.30) == "A"
    assert _assign_single_criterion_class(0.60) == "A"  # Exactly 60% is A
    assert _assign_single_criterion_class(0.6000001) == "B"  # Above 60% is B
    assert _assign_single_criterion_class(0.75) == "B"
    assert _assign_single_criterion_class(0.80) == "B"  # Exactly 80% is B
    assert _assign_single_criterion_class(0.8000001) == "C"  # Above 80% is C
    assert _assign_single_criterion_class(0.85) == "C"
    assert _assign_single_criterion_class(0.90) == "C"  # Exactly 90% is C
    assert _assign_single_criterion_class(0.9000001) == "D"  # Above 90% is D
    assert _assign_single_criterion_class(1.00) == "D"


def test_final_class_score_cutoffs():
    """
    Validates final class assignments based on combined score cutoffs:
    A: score >= 3.25
    B: 2.50 <= score < 3.25
    C: 1.75 <= score < 2.50
    D: score < 1.75
    """
    # Boundary: A >= 3.25
    assert _assign_final_class(4.0) == "A"
    assert _assign_final_class(3.35) == "A"
    assert _assign_final_class(3.25) == "A"
    assert _assign_final_class(3.2499) == "B"

    # Boundary: B >= 2.50 and < 3.25
    assert _assign_final_class(3.0) == "B"
    assert _assign_final_class(2.65) == "B"
    assert _assign_final_class(2.50) == "B"
    assert _assign_final_class(2.4999) == "C"

    # Boundary: C >= 1.75 and < 2.50
    assert _assign_final_class(2.35) == "C"
    assert _assign_final_class(2.0) == "C"
    assert _assign_final_class(1.75) == "C"
    assert _assign_final_class(1.7499) == "D"

    # Boundary: D < 1.75
    assert _assign_final_class(1.70) == "D"
    assert _assign_final_class(1.0) == "D"


def test_weighted_score_combinations():
    """
    Tests specific combinations of Sales Class and Hits Class:
    Combined Score = 0.65 * Sales Score + 0.35 * Hits Score
    Using cumulative percentage thresholds:
    A: 0-60%, B: 60-80%, C: 80-90%, D: 90-100%
    """
    # Total Sales = 100, Total Hits = 100
    df = pd.DataFrame([
        # Item 1: Sales 60 (cum 60% -> A), Hits 55 (cum 55% -> A) -> Score = 0.65(4) + 0.35(4) = 4.00 -> Final A
        {"Item Number": "ITM-1", "Item Name": "Item 1", "UoM": "EA", "Sales ($)": 60.0, "Hits": 55.0},
        # Item 2: Sales 15 (cum 75% -> B), Hits 20 (cum 75% -> B) -> Score = 0.65(3) + 0.35(3) = 3.00 -> Final B
        {"Item Number": "ITM-2", "Item Name": "Item 2", "UoM": "EA", "Sales ($)": 15.0, "Hits": 20.0},
        # Item 3: Sales 13 (cum 88% -> C), Hits 13 (cum 88% -> C) -> Score = 0.65(2) + 0.35(2) = 2.00 -> Final C
        {"Item Number": "ITM-3", "Item Name": "Item 3", "UoM": "EA", "Sales ($)": 13.0, "Hits": 13.0},
        # Item 4: Sales 12 (cum 100% -> D), Hits 12 (cum 100% -> D) -> Score = 0.65(1) + 0.35(1) = 1.00 -> Final D
        {"Item Number": "ITM-4", "Item Name": "Item 4", "UoM": "EA", "Sales ($)": 12.0, "Hits": 12.0},
    ])

    classified = classify_multicriteria_abcd(df)
    row1 = classified[classified["Item Number"] == "ITM-1"].iloc[0]
    row2 = classified[classified["Item Number"] == "ITM-2"].iloc[0]
    row3 = classified[classified["Item Number"] == "ITM-3"].iloc[0]
    row4 = classified[classified["Item Number"] == "ITM-4"].iloc[0]

    assert row1["Sales Class"] == "A"
    assert row1["Hits Class"] == "A"
    assert row1["Combined Score"] == 4.0
    assert row1["Final Class"] == "A"

    assert row2["Sales Class"] == "B"
    assert row2["Hits Class"] == "B"
    assert row2["Combined Score"] == 3.0
    assert row2["Final Class"] == "B"

    assert row3["Sales Class"] == "C"
    assert row3["Hits Class"] == "C"
    assert row3["Combined Score"] == 2.0
    assert row3["Final Class"] == "C"

    assert row4["Sales Class"] == "D"
    assert row4["Hits Class"] == "D"
    assert row4["Combined Score"] == 1.0
    assert row4["Final Class"] == "D"


def test_tie_breaking_sales_and_hits():
    """
    Validates deterministic tie-breaking:
    1. Equal Sales: sorted by Hits descending, then Item Number ascending.
    2. Equal Hits: sorted by Sales descending, then Item Number ascending.
    """
    df = pd.DataFrame([
        # Two items with identical sales (50.0), but ITM-A has more Hits than ITM-B
        {"Item Number": "ITM-B", "Item Name": "Item B", "UoM": "EA", "Sales ($)": 50.0, "Hits": 20},
        {"Item Number": "ITM-A", "Item Name": "Item A", "UoM": "EA", "Sales ($)": 50.0, "Hits": 80},
    ])

    classified = classify_multicriteria_abcd(df)
    # ITM-A has higher hits, so it must win the tie-break for Sales Rank
    itm_a = classified[classified["Item Number"] == "ITM-A"].iloc[0]
    itm_b = classified[classified["Item Number"] == "ITM-B"].iloc[0]

    assert itm_a["Sales Rank"] == 1
    assert itm_b["Sales Rank"] == 2
    assert itm_a["Hits Rank"] == 1
    assert itm_b["Hits Rank"] == 2


def test_tie_breaking_tertiary_item_number():
    """When both Sales and Hits are identical, Item Number ascending breaks the tie."""
    df = pd.DataFrame([
        {"Item Number": "SKU-999", "Item Name": "Item 999", "UoM": "EA", "Sales ($)": 100.0, "Hits": 50},
        {"Item Number": "SKU-100", "Item Name": "Item 100", "UoM": "EA", "Sales ($)": 100.0, "Hits": 50},
    ])

    classified = classify_multicriteria_abcd(df)
    sku_100 = classified[classified["Item Number"] == "SKU-100"].iloc[0]
    sku_999 = classified[classified["Item Number"] == "SKU-999"].iloc[0]

    assert sku_100["Sales Rank"] == 1
    assert sku_999["Sales Rank"] == 2


def test_deterministic_tie_breaking_multi_item_stability():
    """
    Validates that classification is strictly deterministic and invariant to input row order
    even when multiple items share identical Sales and Hits values.
    """
    items = [
        {"Item Number": "SKU-004", "Item Name": "Item 4", "UoM": "EA", "Sales ($)": 25000.0, "Hits": 150},
        {"Item Number": "SKU-001", "Item Name": "Item 1", "UoM": "EA", "Sales ($)": 25000.0, "Hits": 150},
        {"Item Number": "SKU-003", "Item Name": "Item 3", "UoM": "EA", "Sales ($)": 25000.0, "Hits": 150},
        {"Item Number": "SKU-002", "Item Name": "Item 2", "UoM": "EA", "Sales ($)": 25000.0, "Hits": 150},
    ]

    base_classified = classify_multicriteria_abcd(pd.DataFrame(items))

    # All items have identical Sales (25k) and identical Hits (150).
    # Tertiary tie-breaker (Item Number asc) must deterministically sort them:
    # Rank 1: SKU-001, Rank 2: SKU-002, Rank 3: SKU-003, Rank 4: SKU-004
    assert list(base_classified["Item Number"]) == ["SKU-001", "SKU-002", "SKU-003", "SKU-004"]
    assert list(base_classified["Sales Rank"]) == [1, 2, 3, 4]
    assert list(base_classified["Hits Rank"]) == [1, 2, 3, 4]

    # Test that reversing or permuting row order produces the exact same classification
    reversed_df = pd.DataFrame(items[::-1])
    rev_classified = classify_multicriteria_abcd(reversed_df)

    assert list(rev_classified["Item Number"]) == ["SKU-001", "SKU-002", "SKU-003", "SKU-004"]
    assert list(rev_classified["Final Class"]) == list(base_classified["Final Class"])
    assert list(rev_classified["Combined Score"]) == list(base_classified["Combined Score"])


def test_input_validation_missing_columns():
    """Missing any required column must raise ValueError."""
    bad_df = pd.DataFrame([
        {"Item Number": "SKU-1", "Sales ($)": 100, "Hits": 10}
        # missing Item Name and UoM
    ])
    with pytest.raises(ValueError, match="Missing required columns"):
        classify_multicriteria_abcd(bad_df)


def test_input_validation_negative_values():
    """Negative values in Sales or Hits must raise ValueError."""
    bad_df = pd.DataFrame([
        {"Item Number": "SKU-1", "Item Name": "Item 1", "UoM": "EA", "Sales ($)": -50.0, "Hits": 10}
    ])
    with pytest.raises(ValueError, match="contains negative values"):
        classify_multicriteria_abcd(bad_df)


def test_input_validation_empty_dataset():
    """Empty dataframe must raise ValueError."""
    with pytest.raises(ValueError, match="dataset is empty"):
        classify_multicriteria_abcd(pd.DataFrame())


def test_input_validation_zero_totals():
    """Zero total sales or hits must raise ValueError."""
    zero_df = pd.DataFrame([
        {"Item Number": "SKU-1", "Item Name": "Item 1", "UoM": "EA", "Sales ($)": 0.0, "Hits": 0.0}
    ])
    with pytest.raises(ValueError, match="Total Sales .* must be strictly greater than 0"):
        classify_multicriteria_abcd(zero_df)


def test_currency_string_parsing():
    """Handles strings like '$1,200.50' and numeric strings with spaces."""
    df = pd.DataFrame([
        {"Item Number": "SKU-1", "Item Name": "Item 1", "UoM": "EA", "Sales ($)": "$1,500.00 ", "Hits": " 250 "}
    ])
    cleaned = validate_inventory_dataframe(df)
    assert cleaned["Sales ($)"].iloc[0] == 1500.0
    assert cleaned["Hits"].iloc[0] == 250.0


def test_audit_columns_present():
    """Ensures all original and intermediate audit columns are returned."""
    df = pd.DataFrame([
        {"Item Number": "SKU-1", "Item Name": "Alpha", "UoM": "EA", "Sales ($)": 600.0, "Hits": 100},
        {"Item Number": "SKU-2", "Item Name": "Beta", "UoM": "EA", "Sales ($)": 200.0, "Hits": 50},
        {"Item Number": "SKU-3", "Item Name": "Gamma", "UoM": "EA", "Sales ($)": 100.0, "Hits": 30},
        {"Item Number": "SKU-4", "Item Name": "Delta", "UoM": "EA", "Sales ($)": 100.0, "Hits": 20},
    ])
    classified = classify_multicriteria_abcd(df)

    expected_cols = [
        "Item Number", "Item Name", "UoM",
        "Sales ($)", "Sales Rank", "Cumulative Sales ($)", "Cumulative Sales (%)", "Sales Class", "Sales Score",
        "Hits", "Hits Rank", "Cumulative Hits", "Cumulative Hits (%)", "Hits Class", "Hits Score",
        "Combined Score", "Final Class"
    ]
    for col in expected_cols:
        assert col in classified.columns, f"Missing audit column: {col}"


def test_classification_summary_consistency():
    """Summary table should accurately tally items and percentages across classes."""
    df = pd.DataFrame([
        {"Item Number": "SKU-1", "Item Name": "A1", "UoM": "EA", "Sales ($)": 500.0, "Hits": 500},
        {"Item Number": "SKU-2", "Item Name": "B1", "UoM": "EA", "Sales ($)": 250.0, "Hits": 250},
        {"Item Number": "SKU-3", "Item Name": "C1", "UoM": "EA", "Sales ($)": 150.0, "Hits": 150},
        {"Item Number": "SKU-4", "Item Name": "D1", "UoM": "EA", "Sales ($)": 100.0, "Hits": 100},
    ])
    classified = classify_multicriteria_abcd(df)
    summary = generate_classification_summary(classified)

    assert "Class" in summary.columns
    assert "SKU Count" in summary.columns
    assert "Total Sales ($)" in summary.columns
    assert "Total Hits" in summary.columns

    # Verify Portfolio Total row equals sum of individual classes
    portfolio = summary[summary["Class"] == "Total Portfolio"].iloc[0]
    assert portfolio["SKU Count"] == 4
    assert portfolio["Total Sales ($)"] == 1000.0
    assert portfolio["Total Hits"] == 1000
