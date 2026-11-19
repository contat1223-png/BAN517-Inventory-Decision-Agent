"""
Safety Stock and Reorder Point (ROP) Engine
Implements continuous review (Q, R) inventory policies under stochastic demand and lead times.
- Supports three canonical inventory risk scenarios:
    1. Variable Demand, Constant Lead Time
    2. Constant Demand, Variable Lead Time
    3. Both Demand and Lead Time Variable (Independent)
- Computes Cycle Service Level (CSL) z-values, safety stock buffers, and reorder triggers.
"""

from enum import Enum
from typing import Dict, Any, Optional
import math

try:
    from scipy.stats import norm
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


class DemandLeadTimeScenario(str, Enum):
    VAR_DEMAND_CONST_LT = "Variable Demand, Constant Lead Time"
    CONST_DEMAND_VAR_LT = "Constant Demand, Variable Lead Time"
    BOTH_VARIABLE = "Both Demand and Lead Time Variable"


def _norm_ppf(p: float) -> float:
    """Calculates inverse standard normal CDF with scipy or Abramowitz & Stegun fallback."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("Service level must be strictly between 0 and 1 (e.g., 0.95 for 95%).")
    if HAVE_SCIPY:
        return float(norm.ppf(p))

    # High-accuracy rational approximation (Acklam's algorithm)
    # Coefficients in rational approximations
    a = [-3.969683028665376e+01,  2.209460984245205e+02,
         -2.759285104469687e+02,  1.383577518672690e+02,
         -3.066479806614716e+01,  2.506628277459239e+00]
    b = [-5.447609879822406e+01,  1.615858368580409e+02,
         -1.556989798598866e+02,  6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
          4.374664141464968e+00,  2.938163982698783e+00]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,
          2.445134137142996e+00,  3.754408661907416e+00]

    q = min(p, 1.0 - p)
    if q > 0.02425:
        r = q - 0.5
        r2 = r * r
        num = (((((a[0]*r2 + a[1])*r2 + a[2])*r2 + a[3])*r2 + a[4])*r2 + a[5])*r
        den = (((((b[0]*r2 + b[1])*r2 + b[2])*r2 + b[3])*r2 + b[4])*r2 + 1.0)
        x = num / den
    else:
        r = math.sqrt(-2.0 * math.log(q))
        num = ((((c[0]*r + c[1])*r + c[2])*r + c[3])*r + c[4])*r + c[5]
        den = ((((d[0]*r + d[1])*r + d[2])*r + d[3])*r + 1.0)
        x = num / den

    return -x if p < 0.5 else x


def calculate_safety_stock(
    scenario: DemandLeadTimeScenario,
    service_level: float,
    avg_demand: float,
    std_demand: Optional[float] = None,
    avg_lead_time: float = 0.0,
    std_lead_time: Optional[float] = None,
    orders_per_year: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes Safety Stock (SS) and Reorder Point (ROP) for specified stochastic scenario.

    Parameters:
        scenario: DemandLeadTimeScenario enum
        service_level: Desired cycle service level fraction (0.50 to 0.9999)
        avg_demand (d_bar): Mean demand per period (> 0)
        std_demand (sigma_d): Standard deviation of demand per period (>= 0)
        avg_lead_time (L_bar): Mean lead time in same periods (> 0)
        std_lead_time (sigma_L): Standard deviation of lead time (>= 0)
        orders_per_year: Optional annual replenishment order frequency to estimate annual risk

    Returns:
        Dictionary with ROP, SS, sigma_DL, z-score, and scenario explanation.
    """
    if service_level <= 0.5 or service_level >= 1.0:
        raise ValueError("Service level must be between 0.50 and 0.9999 (e.g. 0.95 for 95%).")
    if avg_demand <= 0:
        raise ValueError("Average demand must be strictly positive.")
    if avg_lead_time <= 0:
        raise ValueError("Lead time must be strictly positive.")

    z = _norm_ppf(service_level)
    mean_lead_time_demand = avg_demand * avg_lead_time

    if scenario == DemandLeadTimeScenario.VAR_DEMAND_CONST_LT:
        if std_demand is None or std_demand < 0:
            raise ValueError("Standard deviation of demand (sigma_d) must be non-negative.")
        sigma_dl = std_demand * math.sqrt(avg_lead_time)
        formula_used = "SS = z * sigma_d * sqrt(L)"

    elif scenario == DemandLeadTimeScenario.CONST_DEMAND_VAR_LT:
        if std_lead_time is None or std_lead_time < 0:
            raise ValueError("Standard deviation of lead time (sigma_L) must be non-negative.")
        sigma_dl = avg_demand * std_lead_time
        formula_used = "SS = z * d * sigma_L"

    elif scenario == DemandLeadTimeScenario.BOTH_VARIABLE:
        if std_demand is None or std_demand < 0:
            raise ValueError("Standard deviation of demand (sigma_d) must be non-negative.")
        if std_lead_time is None or std_lead_time < 0:
            raise ValueError("Standard deviation of lead time (sigma_L) must be non-negative.")
        # sigma_DL = sqrt(L_bar * sigma_d^2 + d_bar^2 * sigma_L^2)
        variance_dl = (avg_lead_time * (std_demand ** 2)) + ((avg_demand ** 2) * (std_lead_time ** 2))
        sigma_dl = math.sqrt(variance_dl)
        formula_used = "SS = z * sqrt(L_bar * sigma_d^2 + d_bar^2 * sigma_L^2)"

    else:
        raise ValueError(f"Unsupported scenario: {scenario}")

    safety_stock = z * sigma_dl
    reorder_point = mean_lead_time_demand + safety_stock

    cycle_stockout_risk = 1.0 - service_level
    annual_stockouts = (orders_per_year * cycle_stockout_risk) if orders_per_year is not None else None

    return {
        "scenario": scenario.value,
        "service_level": service_level,
        "service_level_pct": service_level * 100.0,
        "z_score": round(z, 4),
        "mean_lead_time_demand": mean_lead_time_demand,
        "sigma_lead_time_demand": sigma_dl,
        "safety_stock": safety_stock,
        "safety_stock_rounded": math.ceil(safety_stock),
        "reorder_point": reorder_point,
        "reorder_point_rounded": math.ceil(reorder_point),
        "formula_used": formula_used,
        "cycle_stockout_risk_pct": round(cycle_stockout_risk * 100.0, 2),
        "expected_stockouts_per_year": round(annual_stockouts, 2) if annual_stockouts is not None else None,
        "assumptions": [
            "Lead time demand follows an approximately Normal distribution.",
            "Continuous inventory tracking (Q, ROP policy).",
            "Independence between successive demand periods.",
            "Independence between demand and supplier lead times."
        ]
    }
