"""
Unit tests for Newsvendor (Single-Period Probabilistic) Analysis.
Tests underage/overage cost, critical ratio, normal demand loss function, and profit calculations.
"""

import pytest
import math
from core.newsvendor import calculate_newsvendor


def test_newsvendor_symmetric_benchmark():
    """
    Symmetric Benchmark:
    Price P = $100
    Cost C = $60
    Salvage V = $20
    Cu = 100 - 60 = $40
    Co = 60 - 20 = $40
    Critical Ratio CR = 40 / (40 + 40) = 0.50 -> z* = 0.0

    Demand: Normal(mu = 1000, sigma = 200)
    Optimal Q* = 1000 + 0 * 200 = 1000
    Unit normal loss function at z=0: phi(0) = 1/sqrt(2*pi) ≈ 0.398942
    Expected lost sales = 200 * 0.398942 ≈ 79.79
    Expected leftover = 1000 - 1000 + 79.79 = 79.79 (equal because CR = 0.5)
    Expected sales = 1000 - 79.79 = 920.21
    """
    res = calculate_newsvendor(
        unit_price=100.0,
        unit_cost=60.0,
        salvage_value=20.0,
        penalty_cost=0.0,
        demand_mean=1000.0,
        demand_std=200.0
    )

    assert res["cost_of_underage_Cu"] == 40.0
    assert res["cost_of_overage_Co"] == 40.0
    assert res["critical_ratio"] == 0.50
    assert math.isclose(res["z_star"], 0.0, abs_tol=1e-4)
    assert res["optimal_quantity"] == 1000
    assert math.isclose(res["expected_lost_sales"], 79.79, abs_tol=0.2)
    assert math.isclose(res["expected_leftover"], 79.79, abs_tol=0.2)
    assert math.isclose(res["expected_sales"], 920.21, abs_tol=0.2)


def test_newsvendor_asymmetric_with_penalty():
    """
    Asymmetric case with goodwill penalty:
    P = $150, C = $90, V = $30, penalty g = $20
    Cu = (150 - 90) + 20 = $80
    Co = 90 - 30 = $60
    CR = 80 / (80 + 60) = 80 / 140 = 0.571428...
    Since CR > 0.5, z* > 0 and Q* > mu.
    """
    res = calculate_newsvendor(
        unit_price=150.0,
        unit_cost=90.0,
        salvage_value=30.0,
        penalty_cost=20.0,
        demand_mean=500.0,
        demand_std=100.0
    )

    assert res["cost_of_underage_Cu"] == 80.0
    assert res["cost_of_overage_Co"] == 60.0
    assert math.isclose(res["critical_ratio"], 80 / 140, rel_tol=1e-4)
    assert res["z_star"] > 0
    assert res["optimal_quantity"] > 500


def test_newsvendor_empirical_samples():
    """Empirical discrete demand test."""
    samples = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]
    res = calculate_newsvendor(
        unit_price=10.0,
        unit_cost=6.0,
        salvage_value=2.0,
        empirical_demand_samples=samples
    )
    # Cu = 4, Co = 4, CR = 0.50 -> 50th percentile of 10 samples -> sample index 4 or 5
    assert res["distribution"] == "Empirical"
    assert res["critical_ratio"] == 0.50
    assert res["optimal_quantity"] == 300.0


def test_newsvendor_invalid_inputs():
    """Validates cost > price or salvage > cost."""
    with pytest.raises(ValueError, match="Unit price must exceed unit cost"):
        calculate_newsvendor(unit_price=50, unit_cost=60, salvage_value=10)

    with pytest.raises(ValueError, match="Salvage value cannot exceed unit cost"):
        calculate_newsvendor(unit_price=100, unit_cost=50, salvage_value=60)


def test_newsvendor_payoff_visualization_regression():
    """
    Regression Test:
    Ensures plot_newsvendor_payoff runs without AttributeError ('numpy' has no attribute 'math')
    and returns a valid Plotly Figure with expected traces.
    """
    from ui.charts import plot_newsvendor_payoff
    import plotly.graph_objects as go

    fig = plot_newsvendor_payoff(
        unit_price=120.0,
        unit_cost=70.0,
        salvage_value=25.0,
        mean_demand=1000.0,
        std_demand=250.0,
        q_star=1084.0,
        optimal_profit=39250.0
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # Profit line and Q* marker
    assert fig.data[0].name == "Expected Profit ($)"
    assert "Optimal Q*" in fig.data[1].name
