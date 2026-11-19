"""
Newsvendor (Single-Period Probabilistic) Analysis Engine
Implements the canonical critical fractile model for perishable, seasonal, or single-lifecycle inventory:
- Underage Cost Cu = Price - Cost + Penalty
- Overage Cost Co = Cost - Salvage
- Critical Ratio CR = Cu / (Cu + Co)
- Optimal Order Quantity Q*
- Expected Sales, Expected Leftover Inventory, Expected Lost Sales, and Expected Profit.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np
from .safety_stock import _norm_ppf

try:
    from scipy.stats import norm
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def _standard_normal_pdf(z: float) -> float:
    """Standard normal probability density function phi(z)."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * z * z)


def _standard_normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function Phi(z)."""
    if HAVE_SCIPY:
        return float(norm.cdf(z))
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _unit_loss_function(z: float) -> float:
    """
    Standard normal unit normal loss function L(z) = phi(z) - z * (1 - Phi(z)).
    Represents E[max(0, Z - z)].
    """
    phi = _standard_normal_pdf(z)
    Phi = _standard_normal_cdf(z)
    return phi - z * (1.0 - Phi)


def calculate_newsvendor(
    unit_price: float,
    unit_cost: float,
    salvage_value: float,
    penalty_cost: float = 0.0,
    demand_mean: Optional[float] = None,
    demand_std: Optional[float] = None,
    empirical_demand_samples: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Solves the Newsvendor problem for either Normal demand or empirical discrete demand.

    Parameters:
        unit_price (P): Revenue per unit sold (> unit_cost)
        unit_cost (C): Purchase or production cost per unit (> 0)
        salvage_value (V): Net recovery value per unsold unit (<= unit_cost)
        penalty_cost (g): Goodwill penalty per unit of unmet customer demand (>= 0)
        demand_mean (mu): Expected demand (> 0)
        demand_std (sigma): Standard deviation of demand (> 0)
        empirical_demand_samples: Optional array of historical discrete demand numbers

    Returns:
        Dictionary containing Cu, Co, Critical Ratio, Q*, Expected Profit, and Loss Metrics.
    """
    if unit_price <= 0:
        raise ValueError("Unit price must be positive.")
    if unit_cost <= 0:
        raise ValueError("Unit cost must be positive.")
    if unit_cost >= unit_price:
        raise ValueError("Unit price must exceed unit cost to make procurement profitable.")
    if salvage_value > unit_cost:
        raise ValueError("Salvage value cannot exceed unit cost (otherwise overage cost would be negative).")
    if penalty_cost < 0:
        raise ValueError("Penalty cost cannot be negative.")

    # Cost of Underage and Overage
    c_u = (unit_price - unit_cost) + penalty_cost
    c_o = unit_cost - salvage_value

    if (c_u + c_o) <= 0:
        raise ValueError("Sum of Cu and Co must be strictly positive.")

    critical_ratio = c_u / (c_u + c_o)

    # 1. Normal Demand Distribution
    if demand_mean is not None and demand_std is not None:
        if demand_mean <= 0:
            raise ValueError("Mean demand must be strictly positive.")
        if demand_std <= 0:
            raise ValueError("Standard deviation of demand must be strictly positive.")

        z_star = _norm_ppf(critical_ratio)
        q_star_exact = demand_mean + z_star * demand_std
        q_star_rounded = max(0, round(q_star_exact))

        # Expected metrics evaluated at exact optimal Q*
        loss_val = _unit_loss_function(z_star)
        expected_lost_sales = demand_std * loss_val
        expected_leftover = q_star_exact - demand_mean + expected_lost_sales
        expected_sales = demand_mean - expected_lost_sales

        # Expected Profit
        expected_revenue = unit_price * expected_sales
        expected_salvage = salvage_value * expected_leftover
        procurement_cost = unit_cost * q_star_exact
        penalty_total = penalty_cost * expected_lost_sales
        expected_profit = expected_revenue + expected_salvage - procurement_cost - penalty_total

        # Expected Value of Perfect Information (EVPI)
        perfect_info_profit = (unit_price - unit_cost) * demand_mean
        evpi = max(0.0, perfect_info_profit - expected_profit)

        return {
            "distribution": "Normal",
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "salvage_value": salvage_value,
            "penalty_cost": penalty_cost,
            "cost_of_underage_Cu": round(c_u, 2),
            "cost_of_overage_Co": round(c_o, 2),
            "critical_ratio": round(critical_ratio, 4),
            "critical_ratio_pct": round(critical_ratio * 100.0, 2),
            "z_star": round(z_star, 4),
            "optimal_quantity_exact": q_star_exact,
            "optimal_quantity": q_star_rounded,
            "demand_mean": demand_mean,
            "demand_std": demand_std,
            "expected_sales": round(expected_sales, 1),
            "expected_leftover": round(expected_leftover, 1),
            "expected_lost_sales": round(expected_lost_sales, 1),
            "expected_profit": round(expected_profit, 2),
            "expected_revenue": round(expected_revenue, 2),
            "procurement_cost": round(procurement_cost, 2),
            "evpi": round(evpi, 2),
            "assumptions": [
                "Single procurement decision prior to uncertain demand realization.",
                "Demand is normally distributed with mean and standard deviation.",
                "Unsold inventory is salvaged at the salvage value V at end of season.",
                "Unmet demand represents lost sales with margin loss Cu."
            ]
        }

    # 2. Empirical Discrete Demand
    elif empirical_demand_samples:
        clean_samples = [float(x) for x in empirical_demand_samples if x >= 0]
        if not clean_samples:
            raise ValueError("Empirical demand sample list cannot be empty.")
        clean_samples.sort()

        # Empirical percentile matching
        index = int(math.ceil(critical_ratio * len(clean_samples))) - 1
        index = max(0, min(index, len(clean_samples) - 1))
        q_star_empirical = clean_samples[index]

        return {
            "distribution": "Empirical",
            "cost_of_underage_Cu": round(c_u, 2),
            "cost_of_overage_Co": round(c_o, 2),
            "critical_ratio": round(critical_ratio, 4),
            "critical_ratio_pct": round(critical_ratio * 100.0, 2),
            "optimal_quantity": q_star_empirical,
            "sample_size": len(clean_samples),
            "sample_min": min(clean_samples),
            "sample_max": max(clean_samples),
            "sample_mean": round(float(np.mean(clean_samples)), 2)
        }

    else:
        raise ValueError("Must provide either (demand_mean and demand_std) or empirical_demand_samples.")
