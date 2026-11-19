"""
Unit tests for Economic Order Quantity (EOQ) calculations.
Validates against textbook benchmarks and checks input validation.
"""

import pytest
import math
from core.eoq import calculate_eoq, calculate_eoq_sensitivity


def test_eoq_canonical_textbook_example():
    """
    Standard textbook benchmark:
    D = 10,000 units/year
    S = $50 / order
    H = $2.00 / unit / year
    EOQ = sqrt(2 * 10000 * 50 / 2) = sqrt(500,000) = 707.10678...
    Annual Order Cost = (10000 / 707.10678) * 50 = $707.11
    Annual Holding Cost = (707.10678 / 2) * 2 = $707.11
    Total Inventory Cost = $1414.21
    """
    res = calculate_eoq(annual_demand=10000, order_cost=50, holding_cost=2.0)

    assert math.isclose(res["eoq"], 707.10678, rel_tol=1e-4)
    assert res["eoq_rounded"] == 707
    assert math.isclose(res["annual_order_cost"], 707.10678, rel_tol=1e-4)
    assert math.isclose(res["annual_holding_cost"], 707.10678, rel_tol=1e-4)
    assert math.isclose(res["total_inventory_cost"], 1414.21356, rel_tol=1e-4)
    assert math.isclose(res["orders_per_year"], 14.1421, rel_tol=1e-4)


def test_eoq_with_holding_rate_and_unit_cost():
    """
    Equivalent formulation using holding rate:
    Unit cost C = $10.00
    Holding rate h = 0.20 (20%)
    H = 0.20 * 10 = $2.00
    Total Acquisition Cost = (10000 * 10) + TIC = $101,414.21
    """
    res = calculate_eoq(
        annual_demand=10000,
        order_cost=50,
        holding_rate=0.20,
        unit_cost=10.0
    )
    assert math.isclose(res["eoq"], 707.10678, rel_tol=1e-4)
    assert res["purchase_cost"] == 100000.0
    assert math.isclose(res["total_acquisition_cost"], 101414.21356, rel_tol=1e-4)


def test_eoq_sensitivity_curve():
    """Sensitivity DataFrame has correct columns and order cost decreases as Q increases."""
    df_curve = calculate_eoq_sensitivity(annual_demand=10000, order_cost=50, holding_cost=2.0, eoq=707.1)
    assert "Order Quantity (Q)" in df_curve.columns
    assert "Annual Ordering Cost ($)" in df_curve.columns
    assert "Annual Holding Cost ($)" in df_curve.columns
    assert "Total Annual Inventory Cost ($)" in df_curve.columns
    assert len(df_curve) == 100

    # Ordering cost should strictly decrease with Q
    assert df_curve["Annual Ordering Cost ($)"].iloc[0] > df_curve["Annual Ordering Cost ($)"].iloc[-1]
    # Holding cost should strictly increase with Q
    assert df_curve["Annual Holding Cost ($)"].iloc[0] < df_curve["Annual Holding Cost ($)"].iloc[-1]


def test_eoq_invalid_inputs():
    """Validates exception handling for non-positive demand, order cost, or holding cost."""
    with pytest.raises(ValueError, match="Annual demand .* must be strictly positive"):
        calculate_eoq(annual_demand=0, order_cost=50, holding_cost=2.0)

    with pytest.raises(ValueError, match="Order cost .* must be strictly positive"):
        calculate_eoq(annual_demand=1000, order_cost=-10, holding_cost=2.0)

    with pytest.raises(ValueError, match="Must provide either a positive holding_cost"):
        calculate_eoq(annual_demand=1000, order_cost=50, holding_cost=0)
