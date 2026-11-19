"""
Fixed-Period Review (Periodic Review Model / Order-Up-To Level S) Engine
Implements canonical (T, S) periodic inventory policies:
- Review interval T (time between successive inventory reviews).
- Lead time L (supplier transit/production time).
- Protection interval = T + L.
- Target Order-Up-To level S = d_bar * (T + L) + z * sigma_d * sqrt(T + L).
- Dynamic replenishment order quantity Q = max(0, S - Inventory_Position).
"""

from typing import Dict, Any, Optional
import math
from .safety_stock import _norm_ppf


def calculate_periodic_review_order_up_to(
    review_period: float,
    lead_time: float,
    avg_demand: float,
    std_demand: float,
    service_level: float,
    current_on_hand: float = 0.0,
    current_on_order: float = 0.0,
    backorders: float = 0.0,
    rounding_rule: str = "ceil"
) -> Dict[str, Any]:
    """
    Calculates the target Order-Up-To level (S) and current replenishment order (Q) for a Fixed-Period Review system.

    Parameters:
        review_period (T): Time between inventory reviews in periods (> 0)
        lead_time (L): Lead time in the same periods (> 0)
        avg_demand (d_bar): Average demand per period (> 0)
        std_demand (sigma_d): Standard deviation of demand per period (>= 0)
        service_level: Cycle service level fraction (0.50 to 0.9999)
        current_on_hand: Units currently physically in stock (>= 0)
        current_on_order: Units already ordered from supplier but not yet received (>= 0)
        backorders: Unfulfilled customer orders waiting for stock (>= 0)
        rounding_rule: 'ceil' (conservative buffer guaranteeing service level) or 'round' (nearest integer)

    Returns:
        Dictionary with protection interval, target S, safety stock, current inventory position, and order quantity Q.
    """
    if review_period <= 0:
        raise ValueError("Review period (T) must be strictly positive.")
    if lead_time < 0:
        raise ValueError("Lead time (L) cannot be negative.")
    if avg_demand <= 0:
        raise ValueError("Average demand must be strictly positive.")
    if std_demand < 0:
        raise ValueError("Standard deviation of demand must be non-negative.")
    if service_level <= 0.5 or service_level >= 1.0:
        raise ValueError("Service level must be between 0.50 and 0.9999.")

    protection_interval = review_period + lead_time
    mean_protection_demand = avg_demand * protection_interval
    sigma_protection = std_demand * math.sqrt(protection_interval)

    z = _norm_ppf(service_level)
    safety_stock = z * sigma_protection
    order_up_to_level = mean_protection_demand + safety_stock

    # Current inventory position = on_hand + on_order - backorders
    inventory_position = current_on_hand + current_on_order - backorders
    order_quantity = max(0.0, order_up_to_level - inventory_position)

    # Whole-unit rounding evaluations:
    s_ceil = math.ceil(order_up_to_level)
    s_round = round(order_up_to_level)
    ss_ceil = math.ceil(safety_stock)
    ss_round = round(safety_stock)

    # Order quantities derived from rounded S to ensure S_rounded - I = Q_rounded
    inv_pos_int = int(round(inventory_position))
    q_ceil = max(0, s_ceil - inv_pos_int)
    q_round = max(0, s_round - inv_pos_int)

    if rounding_rule == "round":
        s_selected = s_round
        q_selected = q_round
        ss_selected = ss_round
    else:  # default 'ceil'
        s_selected = s_ceil
        q_selected = q_ceil
        ss_selected = ss_ceil

    # Equivalent continuous review safety stock for comparison: z * sigma_d * sqrt(L)
    continuous_ss = z * std_demand * math.sqrt(lead_time) if lead_time > 0 else 0.0
    ss_ratio = (safety_stock / continuous_ss) if continuous_ss > 0 else 1.0

    return {
        "review_period_T": review_period,
        "lead_time_L": lead_time,
        "protection_interval": protection_interval,
        "mean_protection_demand": mean_protection_demand,
        "sigma_protection_demand": sigma_protection,
        "z_score": round(z, 4),
        "rounding_rule": rounding_rule,
        "safety_stock": safety_stock,
        "safety_stock_rounded": ss_selected,
        "safety_stock_ceil": ss_ceil,
        "safety_stock_round": ss_round,
        "order_up_to_level_S": order_up_to_level,
        "order_up_to_level_rounded": s_selected,
        "order_up_to_level_ceil": s_ceil,
        "order_up_to_level_round": s_round,
        "current_on_hand": current_on_hand,
        "current_on_order": current_on_order,
        "backorders": backorders,
        "current_inventory_position": inventory_position,
        "order_quantity_Q": order_quantity,
        "order_quantity_rounded": q_selected,
        "order_quantity_ceil": q_ceil,
        "order_quantity_round": q_round,
        "continuous_review_ss": continuous_ss,
        "periodic_vs_continuous_ss_ratio": round(ss_ratio, 2),
        "assumptions": [
            "Inventory reviews occur strictly at fixed intervals T.",
            "Demand during the protection interval (T + L) is approximately normally distributed.",
            "Replenishment orders arrive L periods after placement.",
            "Stockouts during the protection interval are backordered or lost according to service level."
        ]
    }
