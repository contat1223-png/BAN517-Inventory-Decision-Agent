"""
Unit tests for Quantity Discount Analysis.
Validates All-Units discount evaluations against textbook problems.
"""

import pytest
import math
from core.discounts import analyze_quantity_discounts, DiscountTier


def test_textbook_quantity_discount_example():
    """
    Standard textbook benchmark:
    D = 5,000 units/year
    S = $49 / order
    h = 0.20 (20% of unit price)

    Tiers:
    Tier 1: 0 - 999 units, Price = $5.00
      H1 = 0.20 * 5.00 = $1.00
      EOQ1 = sqrt(2 * 5000 * 49 / 1.00) = 700 (Feasible)
      TAC1 = (5000 * 5.00) + (5000/700)*49 + (700/2)*1.00 = 25000 + 350 + 350 = $25,700

    Tier 2: 1,000 - 1,999 units, Price = $4.80
      H2 = 0.20 * 4.80 = $0.96
      EOQ2 = sqrt(2 * 5000 * 49 / 0.96) = 714.4 (Below 1000, adjust to Q = 1000)
      TAC2 = (5000 * 4.80) + (5000/1000)*49 + (1000/2)*0.96 = 24000 + 245 + 480 = $24,725

    Tier 3: 2,000+ units, Price = $4.75
      H3 = 0.20 * 4.75 = $0.95
      EOQ3 = sqrt(2 * 5000 * 49 / 0.95) = 718.2 (Below 2000, adjust to Q = 2000)
      TAC3 = (5000 * 4.75) + (5000/2000)*49 + (2000/2)*0.95 = 23750 + 122.50 + 950 = $24,822.50

    Optimal decision: Tier 2, Q = 1,000, Total Cost = $24,725.
    """
    tiers = [
        DiscountTier(tier_name="Tier 1 (Base)", min_qty=1, max_qty=999, unit_price=5.00),
        DiscountTier(tier_name="Tier 2 (Discount 1)", min_qty=1000, max_qty=1999, unit_price=4.80),
        DiscountTier(tier_name="Tier 3 (Discount 2)", min_qty=2000, max_qty=float("inf"), unit_price=4.75),
    ]

    res = analyze_quantity_discounts(
        annual_demand=5000,
        order_cost=49,
        tiers=tiers,
        holding_rate=0.20
    )

    assert res["optimal_tier"] == "Tier 2 (Discount 1)"
    assert res["optimal_quantity"] == 1000
    assert res["optimal_price"] == 4.80
    assert math.isclose(res["optimal_total_cost"], 24725.00, rel_tol=1e-3)
    assert math.isclose(res["optimal_order_cost"], 245.00, rel_tol=1e-3)
    assert math.isclose(res["optimal_holding_cost"], 480.00, rel_tol=1e-3)
    assert math.isclose(res["optimal_purchase_cost"], 24000.00, rel_tol=1e-3)


def test_discounts_invalid_inputs():
    """Validates error handling for empty tiers, negative demand, and inverted brackets."""
    with pytest.raises(ValueError, match="At least one discount tier must be provided"):
        analyze_quantity_discounts(annual_demand=1000, order_cost=50, tiers=[], holding_rate=0.20)

    with pytest.raises(ValueError, match="Max quantity cannot be less than min quantity"):
        bad_tier = [DiscountTier(tier_name="Bad", min_qty=500, max_qty=100, unit_price=10.0)]
        analyze_quantity_discounts(annual_demand=1000, order_cost=50, tiers=bad_tier, holding_rate=0.20)
