"""
Unit tests for Safety Stock and Reorder Point (ROP) calculations.
Tests all three stochastic scenarios and z-score accuracy.
"""

import pytest
import math
from core.safety_stock import (
    calculate_safety_stock,
    DemandLeadTimeScenario,
    _norm_ppf
)


def test_norm_ppf_benchmarks():
    """Validates inverse normal CDF against standard critical values."""
    assert math.isclose(_norm_ppf(0.50), 0.0, abs_tol=1e-4)
    assert math.isclose(_norm_ppf(0.8413447), 1.0, abs_tol=1e-3)
    assert math.isclose(_norm_ppf(0.90), 1.28155, abs_tol=1e-4)
    assert math.isclose(_norm_ppf(0.95), 1.64485, abs_tol=1e-4)
    assert math.isclose(_norm_ppf(0.975), 1.95996, abs_tol=1e-4)
    assert math.isclose(_norm_ppf(0.99), 2.32635, abs_tol=1e-4)


def test_scenario_1_variable_demand_constant_lead_time():
    """
    Scenario 1:
    d_bar = 100 units/day
    sigma_d = 20 units/day
    L = 4 days
    CSL = 95% -> z ≈ 1.6449
    sigma_DL = 20 * sqrt(4) = 40 units
    SS = 1.6449 * 40 = 65.794 units -> ceil: 66
    ROP = 100 * 4 + 65.794 = 465.794 units -> ceil: 466
    """
    res = calculate_safety_stock(
        scenario=DemandLeadTimeScenario.VAR_DEMAND_CONST_LT,
        service_level=0.95,
        avg_demand=100.0,
        std_demand=20.0,
        avg_lead_time=4.0
    )

    assert math.isclose(res["sigma_lead_time_demand"], 40.0, rel_tol=1e-4)
    assert math.isclose(res["safety_stock"], 65.794, rel_tol=1e-3)
    assert res["safety_stock_rounded"] == 66
    assert math.isclose(res["reorder_point"], 465.794, rel_tol=1e-3)
    assert res["reorder_point_rounded"] == 466


def test_scenario_2_constant_demand_variable_lead_time():
    """
    Scenario 2:
    d = 100 units/day
    L_bar = 4 days
    sigma_L = 1.5 days
    CSL = 95% -> z ≈ 1.6449
    sigma_DL = 100 * 1.5 = 150 units
    SS = 1.6449 * 150 = 246.7275 units -> ceil: 247
    ROP = 100 * 4 + 246.7275 = 646.7275 units -> ceil: 647
    """
    res = calculate_safety_stock(
        scenario=DemandLeadTimeScenario.CONST_DEMAND_VAR_LT,
        service_level=0.95,
        avg_demand=100.0,
        avg_lead_time=4.0,
        std_lead_time=1.5
    )

    assert math.isclose(res["sigma_lead_time_demand"], 150.0, rel_tol=1e-4)
    assert math.isclose(res["safety_stock"], 246.7275, rel_tol=1e-3)
    assert res["safety_stock_rounded"] == 247
    assert math.isclose(res["reorder_point"], 646.7275, rel_tol=1e-3)
    assert res["reorder_point_rounded"] == 647


def test_scenario_3_both_variable():
    """
    Scenario 3:
    d_bar = 100, sigma_d = 20
    L_bar = 4, sigma_L = 1.5
    CSL = 95% -> z ≈ 1.6449
    variance_DL = 4 * (20^2) + (100^2) * (1.5^2) = 1600 + 22500 = 24100
    sigma_DL = sqrt(24100) = 155.2417
    SS = 1.64485 * 155.2417 = 255.349 -> ceil: 256
    ROP = 400 + 255.349 = 655.349 -> ceil: 656
    """
    res = calculate_safety_stock(
        scenario=DemandLeadTimeScenario.BOTH_VARIABLE,
        service_level=0.95,
        avg_demand=100.0,
        std_demand=20.0,
        avg_lead_time=4.0,
        std_lead_time=1.5
    )

    expected_sigma = math.sqrt(4 * (20**2) + (100**2) * (1.5**2))
    assert math.isclose(res["sigma_lead_time_demand"], expected_sigma, rel_tol=1e-4)
    assert math.isclose(res["safety_stock"], 1.64485 * expected_sigma, rel_tol=1e-3)
    assert res["safety_stock_rounded"] == math.ceil(1.64485 * expected_sigma)
