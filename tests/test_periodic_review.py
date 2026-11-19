"""
Unit tests for Fixed-Period Review (P-Model / Order-Up-To Level S).
Validates protection interval demand, target S, and dynamic order replenishment Q.
"""

import pytest
import math
from core.periodic_review import calculate_periodic_review_order_up_to


def test_periodic_review_order_up_to_calculation():
    """
    Periodic Review Benchmark:
    T = 7 days (review every week)
    L = 3 days (supplier transit time)
    Protection Interval = T + L = 10 days
    d_bar = 50 units/day
    sigma_d = 10 units/day
    Service Level = 95% -> z ≈ 1.6449

    Mean demand over protection interval = 50 * 10 = 500 units
    sigma_protection = 10 * sqrt(10) = 31.6227766 units
    SS = 1.64485 * 31.6227766 = 52.01469 units
    Target Order-Up-To Level S = 500 + 52.01469 = 552.01469 units -> ceil: 553

    Current Inventory Position:
    On-hand = 120
    On-order = 80
    Backorders = 10
    Inventory Position = 120 + 80 - 10 = 190 units
    Replenishment Order Q = max(0, 552.01469 - 190) = 362.01469 units -> ceil: 363
    """
    res = calculate_periodic_review_order_up_to(
        review_period=7.0,
        lead_time=3.0,
        avg_demand=50.0,
        std_demand=10.0,
        service_level=0.95,
        current_on_hand=120.0,
        current_on_order=80.0,
        backorders=10.0
    )

    assert res["protection_interval"] == 10.0
    assert res["mean_protection_demand"] == 500.0
    assert math.isclose(res["sigma_protection_demand"], 10 * math.sqrt(10), rel_tol=1e-4)
    assert math.isclose(res["safety_stock"], 52.01469, rel_tol=1e-3)
    assert res["safety_stock_rounded"] == 53
    assert math.isclose(res["order_up_to_level_S"], 552.01469, rel_tol=1e-3)
    assert res["order_up_to_level_rounded"] == 553
    assert res["current_inventory_position"] == 190.0
    assert math.isclose(res["order_quantity_Q"], 362.01469, rel_tol=1e-3)
    assert res["order_quantity_rounded"] == 363


def test_periodic_review_order_capped_at_zero():
    """If inventory position exceeds target S, order quantity Q must be zero (no negative order)."""
    res = calculate_periodic_review_order_up_to(
        review_period=5.0,
        lead_time=2.0,
        avg_demand=20.0,
        std_demand=4.0,
        service_level=0.90,
        current_on_hand=300.0,  # Well above target S
        current_on_order=0.0,
        backorders=0.0
    )
    assert res["order_quantity_Q"] == 0.0
    assert res["order_quantity_rounded"] == 0


def test_periodic_review_invalid_inputs():
    """Validates boundary checking for negative review period or lead time."""
    with pytest.raises(ValueError, match="Review period .* must be strictly positive"):
        calculate_periodic_review_order_up_to(
            review_period=0, lead_time=5, avg_demand=10, std_demand=2, service_level=0.95
        )
    with pytest.raises(ValueError, match="Lead time .* cannot be negative"):
        calculate_periodic_review_order_up_to(
            review_period=5, lead_time=-1, avg_demand=10, std_demand=2, service_level=0.95
        )


def test_periodic_review_rounding_rules_and_consistency():
    """
    Validates that:
    1. 'ceil' rule rounds S up to 553, yielding Q = 553 - 190 = 363.
    2. 'round' rule rounds S to nearest 552, yielding Q = 552 - 190 = 362.
    3. Mathematical consistency: S_rounded - I == Q_rounded for both rules.
    """
    # 1. Conservative Ceiling rule
    res_ceil = calculate_periodic_review_order_up_to(
        review_period=7.0, lead_time=3.0, avg_demand=50.0, std_demand=10.0,
        service_level=0.95, current_on_hand=120.0, current_on_order=80.0, backorders=10.0,
        rounding_rule="ceil"
    )
    assert res_ceil["order_up_to_level_rounded"] == 553
    assert res_ceil["order_quantity_rounded"] == 363
    assert res_ceil["order_up_to_level_rounded"] - int(res_ceil["current_inventory_position"]) == res_ceil["order_quantity_rounded"]

    # 2. Nearest Integer Round rule
    res_round = calculate_periodic_review_order_up_to(
        review_period=7.0, lead_time=3.0, avg_demand=50.0, std_demand=10.0,
        service_level=0.95, current_on_hand=120.0, current_on_order=80.0, backorders=10.0,
        rounding_rule="round"
    )
    assert res_round["order_up_to_level_rounded"] == 552
    assert res_round["order_quantity_rounded"] == 362
    assert res_round["order_up_to_level_rounded"] - int(res_round["current_inventory_position"]) == res_round["order_quantity_rounded"]
