"""
Economic Order Quantity (EOQ) Calculation Engine
Implements canonical Ford W. Harris / Wilson lot-size formula and cost-curve analysis:
- Assumptions:
    1. Demand rate is constant and known with certainty.
    2. Lead time is known and constant.
    3. Inventory arrives in a single replenishment batch (no partial shipments).
    4. No stockouts are permitted.
    5. Cost parameters (Order cost S, Holding cost H, Unit cost C) remain constant.
"""

from typing import Dict, Any, Optional
import math
import numpy as np
import pandas as pd


def calculate_eoq(
    annual_demand: float,
    order_cost: float,
    holding_cost: Optional[float] = None,
    holding_rate: Optional[float] = None,
    unit_cost: Optional[float] = None,
    work_days_per_year: int = 250
) -> Dict[str, Any]:
    """
    Calculates the Economic Order Quantity (EOQ) and associated operational metrics.

    Parameters:
        annual_demand (D): Total annual demand in units (> 0)
        order_cost (S): Fixed cost per replenishment order in $ (> 0)
        holding_cost (H): Annual holding cost per unit in $ (> 0) OR
        holding_rate (h): Holding cost rate (% of unit cost, e.g. 0.20 for 20%)
        unit_cost (C): Unit purchase cost in $ (> 0)
        work_days_per_year: Operational days per year (default 250)

    Returns:
        Dictionary of EOQ metrics including Q*, TIC, TAC, cycle times, and order frequencies.
    """
    if annual_demand <= 0:
        raise ValueError("Annual demand (D) must be strictly positive.")
    if order_cost <= 0:
        raise ValueError("Order cost (S) must be strictly positive.")

    # Determine holding cost H
    if holding_cost is not None and holding_cost > 0:
        h_cost = float(holding_cost)
    elif holding_rate is not None and unit_cost is not None and holding_rate > 0 and unit_cost > 0:
        h_cost = float(holding_rate * unit_cost)
    else:
        raise ValueError(
            "Must provide either a positive holding_cost (H) or both holding_rate (h) and unit_cost (C)."
        )

    # Core EOQ Formula
    eoq_exact = math.sqrt((2.0 * annual_demand * order_cost) / h_cost)
    eoq_rounded = round(eoq_exact)

    # Costs evaluated at exact EOQ
    annual_order_cost = (annual_demand / eoq_exact) * order_cost
    annual_holding_cost = (eoq_exact / 2.0) * h_cost
    total_inventory_cost = annual_order_cost + annual_holding_cost

    # Acquisition cost if unit cost is supplied
    purchase_cost = (annual_demand * unit_cost) if unit_cost is not None else 0.0
    total_acquisition_cost = purchase_cost + total_inventory_cost

    # Operational metrics
    orders_per_year = annual_demand / eoq_exact
    cycle_time_years = eoq_exact / annual_demand
    cycle_time_days = cycle_time_years * work_days_per_year
    daily_demand = annual_demand / work_days_per_year

    return {
        "eoq": eoq_exact,
        "eoq_rounded": eoq_rounded,
        "annual_demand": annual_demand,
        "order_cost": order_cost,
        "holding_cost_per_unit": h_cost,
        "unit_cost": unit_cost,
        "annual_order_cost": annual_order_cost,
        "annual_holding_cost": annual_holding_cost,
        "total_inventory_cost": total_inventory_cost,
        "total_acquisition_cost": total_acquisition_cost,
        "purchase_cost": purchase_cost,
        "orders_per_year": orders_per_year,
        "cycle_time_days": cycle_time_days,
        "daily_demand": daily_demand,
        "assumptions": [
            "Constant, deterministic demand rate.",
            "Instantaneous replenishment upon lead time arrival.",
            "No planned shortages or stockouts.",
            "Fixed order setup cost and inventory holding cost per period."
        ]
    }


def calculate_eoq_sensitivity(
    annual_demand: float,
    order_cost: float,
    holding_cost: float,
    eoq: float,
    points: int = 100
) -> pd.DataFrame:
    """
    Generates cost curves across order quantities ranging from 20% to 250% of EOQ.
    Returns a DataFrame with columns: ['Order Quantity (Q)', 'Ordering Cost', 'Holding Cost', 'Total Cost'].
    """
    min_q = max(1.0, eoq * 0.2)
    max_q = eoq * 2.5
    q_values = np.linspace(min_q, max_q, points)

    order_costs = (annual_demand / q_values) * order_cost
    holding_costs = (q_values / 2.0) * holding_cost
    total_costs = order_costs + holding_costs

    return pd.DataFrame({
        "Order Quantity (Q)": q_values,
        "Annual Ordering Cost ($)": order_costs,
        "Annual Holding Cost ($)": holding_costs,
        "Total Annual Inventory Cost ($)": total_costs
    })
