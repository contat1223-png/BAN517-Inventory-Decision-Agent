"""
Quantity Discount Analysis Engine
Evaluates All-Units and Incremental quantity discount structures to identify optimal order quantities.
- Evaluates EOQ feasibility within each price break bracket.
- Computes annual purchase, ordering, holding, and total acquisition costs.
- Identifies the globally cost-minimizing order quantity Q*.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import math
import pandas as pd


@dataclass
class DiscountTier:
    tier_name: str
    min_qty: float
    max_qty: float
    unit_price: float


def analyze_quantity_discounts(
    annual_demand: float,
    order_cost: float,
    tiers: List[DiscountTier],
    holding_rate: Optional[float] = None,
    fixed_holding_cost: Optional[float] = None,
    discount_type: str = "all_units"
) -> Dict[str, Any]:
    """
    Performs comprehensive quantity discount analysis.

    Parameters:
        annual_demand (D): Total annual units required (> 0)
        order_cost (S): Order setup cost in $ (> 0)
        tiers: List of DiscountTier objects sorted by min_qty ascending
        holding_rate (h): Holding cost as decimal fraction of unit price (e.g. 0.20) OR
        fixed_holding_cost (H): Fixed holding cost per unit per year
        discount_type: 'all_units' (standard)

    Returns:
        Dictionary containing comparative evaluation table, optimal recommendation, and cost breakdown.
    """
    if annual_demand <= 0:
        raise ValueError("Annual demand must be strictly positive.")
    if order_cost <= 0:
        raise ValueError("Order cost must be strictly positive.")
    if not tiers:
        raise ValueError("At least one discount tier must be provided.")
    if holding_rate is None and fixed_holding_cost is None:
        raise ValueError("Must provide either holding_rate (h) or fixed_holding_cost (H).")

    # Validate tier ranges
    sorted_tiers = sorted(tiers, key=lambda t: t.min_qty)
    for i in range(len(sorted_tiers)):
        if sorted_tiers[i].unit_price <= 0:
            raise ValueError(f"Unit price for tier '{sorted_tiers[i].tier_name}' must be positive.")
        if sorted_tiers[i].min_qty < 0:
            raise ValueError("Minimum quantity cannot be negative.")
        if sorted_tiers[i].max_qty < sorted_tiers[i].min_qty:
            raise ValueError(f"Max quantity cannot be less than min quantity for tier '{sorted_tiers[i].tier_name}'.")

    results = []

    for tier in sorted_tiers:
        price = tier.unit_price
        h_unit = fixed_holding_cost if fixed_holding_cost is not None else (holding_rate * price)

        unconstrained_eoq = math.sqrt((2.0 * annual_demand * order_cost) / h_unit)

        # Feasibility check for All-Units discount:
        # If unconstrained EOQ falls below min_qty, the firm must order min_qty to secure the price.
        # If EOQ falls inside [min_qty, max_qty], it is directly feasible.
        # If EOQ exceeds max_qty, it is typically dominated by higher discount tiers.
        if unconstrained_eoq < tier.min_qty:
            candidate_qty = tier.min_qty
            status = f"Adjusted to Bracket Minimum ({tier.min_qty:,.0f})"
            is_feasible = True
        elif tier.min_qty <= unconstrained_eoq <= tier.max_qty:
            candidate_qty = unconstrained_eoq
            status = "Feasible EOQ"
            is_feasible = True
        else:
            candidate_qty = None
            status = f"Infeasible (EOQ > {tier.max_qty:,.0f})"
            is_feasible = False

        if candidate_qty is not None:
            annual_purchase = annual_demand * price
            annual_order = (annual_demand / candidate_qty) * order_cost
            annual_holding = (candidate_qty / 2.0) * h_unit
            total_cost = annual_purchase + annual_order + annual_holding
        else:
            annual_purchase = None
            annual_order = None
            annual_holding = None
            total_cost = float("inf")

        results.append({
            "Tier": tier.tier_name,
            "Min Qty": tier.min_qty,
            "Max Qty": tier.max_qty if tier.max_qty != float("inf") else "Unlimited",
            "Unit Price ($)": price,
            "Holding Cost/Unit ($)": h_unit,
            "Unconstrained EOQ": round(unconstrained_eoq, 1),
            "Candidate Q": round(candidate_qty, 1) if candidate_qty is not None else "N/A",
            "Annual Purchase Cost ($)": round(annual_purchase, 2) if annual_purchase is not None else None,
            "Annual Order Cost ($)": round(annual_order, 2) if annual_order is not None else None,
            "Annual Holding Cost ($)": round(annual_holding, 2) if annual_holding is not None else None,
            "Total Annual Cost ($)": round(total_cost, 2) if total_cost != float("inf") else None,
            "Feasibility": status,
            "_raw_total_cost": total_cost,
            "_raw_candidate_q": candidate_qty
        })

    # Determine global minimum
    feasible_results = [r for r in results if r["_raw_total_cost"] != float("inf")]
    if not feasible_results:
        raise ValueError("No feasible order quantity found across provided discount tiers.")

    best_option = min(feasible_results, key=lambda r: r["_raw_total_cost"])

    # Mark optimal in table
    for r in results:
        r["Optimal?"] = "★ BEST" if r["Tier"] == best_option["Tier"] else ""

    summary_df = pd.DataFrame(results).drop(columns=["_raw_total_cost", "_raw_candidate_q"])

    return {
        "summary_table": summary_df,
        "optimal_tier": best_option["Tier"],
        "optimal_quantity": best_option["Candidate Q"],
        "optimal_price": best_option["Unit Price ($)"],
        "optimal_total_cost": best_option["Total Annual Cost ($)"],
        "optimal_order_cost": best_option["Annual Order Cost ($)"],
        "optimal_holding_cost": best_option["Annual Holding Cost ($)"],
        "optimal_purchase_cost": best_option["Annual Purchase Cost ($)"]
    }
