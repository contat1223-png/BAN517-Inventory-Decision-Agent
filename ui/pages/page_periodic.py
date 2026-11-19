"""
Fixed-Period Review (Periodic Review / P-Model) View
Calculates target Order-Up-To Level (S) and current replenishment order (Q).
"""

import streamlit as st
import pandas as pd
from core.periodic_review import calculate_periodic_review_order_up_to
from ui.styles import render_metric_card


def render_periodic_review_page(classified_df: pd.DataFrame):
    """Renders the Fixed-Period Review (T, S) planning interface."""
    st.header("⏱️ Periodic Review: Fixed-Period Order-Up-To System (T, S)")

    st.markdown("""
    In a **Fixed-Period Review system (P-model)**, inventory levels are reviewed at predetermined time intervals $T$.
    Because new orders arrive only every $T$ periods and take $L$ periods to be delivered, the inventory must protect against demand uncertainty over the entire **protection interval $(T + L)$**:
    $$S = \\bar{d}(T + L) + z \\sigma_d \\sqrt{T + L}$$
    $$Q = \\max(0, S - \\text{Inventory Position})$$
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Interval & Demand Dynamics")
        review_period = st.number_input("Review Period Interval (T, e.g. days/weeks):", min_value=1.0, value=7.0, step=1.0)
        lead_time = st.number_input("Supplier Lead Time (L, same time units):", min_value=0.0, value=3.0, step=1.0)
        avg_demand = st.number_input("Average Demand per Period (d̄):", min_value=0.1, value=50.0, step=5.0)
        std_demand = st.number_input("Standard Deviation of Demand (σ_d):", min_value=0.0, value=10.0, step=1.0)
        service_level_pct = st.slider("Target Cycle Service Level (%):", min_value=50.0, max_value=99.9, value=95.0, step=0.5)

    with col2:
        st.subheader("Current Stock Audit (Review Time)")
        on_hand = st.number_input("Physical On-Hand Inventory:", min_value=0.0, value=120.0, step=10.0)
        on_order = st.number_input("Pipeline / On-Order Units (In Transit):", min_value=0.0, value=80.0, step=10.0)
        backorders = st.number_input("Backordered / Unfilled Customer Units:", min_value=0.0, value=10.0, step=5.0)

        st.caption("Inventory Position = On-Hand + On-Order - Backorders")

    st.markdown("**Whole-Unit Rounding Policy Configuration:**")
    rounding_choice = st.radio(
        "Whole-Unit Rounding Policy:",
        [
            "Conservative Buffer (Ceiling) — strictly guarantees service level ≥ target",
            "Nearest Integer (Round) — standard mathematical rounding"
        ],
        horizontal=True,
        help="Determines how fractional safety stock and target order-up-to levels are converted into whole replenishment units."
    )
    rule_code = "ceil" if "Ceiling" in rounding_choice else "round"

    try:
        res = calculate_periodic_review_order_up_to(
            review_period=review_period,
            lead_time=lead_time,
            avg_demand=avg_demand,
            std_demand=std_demand,
            service_level=service_level_pct / 100.0,
            current_on_hand=on_hand,
            current_on_order=on_order,
            backorders=backorders,
            rounding_rule=rule_code
        )

        # KPI Metrics
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            sub_s = (
                f"Exact: {res['order_up_to_level_S']:.3f} (Ceil: +{res['order_up_to_level_ceil'] - res['order_up_to_level_S']:.3f})"
                if rule_code == "ceil"
                else f"Exact: {res['order_up_to_level_S']:.3f} (Nearest: {res['order_up_to_level_round']})"
            )
            render_metric_card(
                label="Target Order-Up-To (S)",
                value=f"{res['order_up_to_level_rounded']:,} units",
                sub=sub_s,
                border_color="#2E7D32"
            )
        with k2:
            render_metric_card(
                label="Place Order Now (Q)",
                value=f"{res['order_quantity_rounded']:,} units",
                sub=f"Target {res['order_up_to_level_rounded']} - Inv {int(res['current_inventory_position'])}",
                border_color="#1E88E5"
            )
        with k3:
            render_metric_card(
                label="Safety Stock Buffer",
                value=f"{res['safety_stock_rounded']:,} units",
                sub=f"Exact: {res['safety_stock']:.3f} units",
                border_color="#8E24AA"
            )
        with k4:
            render_metric_card(
                label="Current Inventory Position",
                value=f"{int(res['current_inventory_position']):,} units",
                sub=f"OH:{int(on_hand)} + OO:{int(on_order)} - BO:{int(backorders)}",
                border_color="#E65100"
            )

        # Mathematical Consistency and Decimal Precision Callout
        rule_desc = "Conservative Ceiling (ceil)" if rule_code == "ceil" else "Nearest Integer (round)"
        st.info(f"""
        🔍 **Mathematical Consistency & Hidden Decimal Precision Audit:**
        - **Exact Theoretical Protection Level:** $S = \\bar{{d}}(T + L) + SS = {res['mean_protection_demand']:.3f} + {res['safety_stock']:.3f} = \\mathbf{{{res['order_up_to_level_S']:.3f}\\text{{ units}}}}$.
        - **Net Inventory Position:** $I = \\text{{On-Hand}} ({int(on_hand)}) + \\text{{On-Order}} ({int(on_order)}) - \\text{{Backorders}} ({int(backorders)}) = \\mathbf{{{int(res['current_inventory_position'])}\\text{{ units}}}}$.
        - **Exact Replenishment Need:** $Q = S - I = {res['order_up_to_level_S']:.3f} - {int(res['current_inventory_position'])} = \\mathbf{{{res['order_quantity_Q']:.3f}\\text{{ units}}}}$.
        - **Whole-Unit Decision ({rule_desc}):**  
          $S_{{whole}} = {res['order_up_to_level_rounded']}$ units $\\implies Q_{{order}} = S_{{whole}} - I = {res['order_up_to_level_rounded']} - {int(res['current_inventory_position'])} = \\mathbf{{{res['order_quantity_rounded']}\\text{{ units}}}}$.
          *(Note: displaying only 1 decimal place previously displayed {res['order_up_to_level_S']:.3f} as "{res['order_up_to_level_S']:.1f}", hiding the fractional units that explain why ceiling produced {res['order_up_to_level_ceil']} units).*
        """)

        # Comparison with Continuous Review
        st.subheader("⚖️ Periodic vs. Continuous Review Trade-Off Analysis")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.info(f"""
            - **Protection Interval:** {res['protection_interval']:.1f} periods ($T + L = {review_period:.1f} + {lead_time:.1f}$)
            - **Periodic Review Safety Stock:** {res['safety_stock']:.1f} units
            - **Equivalent Continuous Review Safety Stock:** {res['continuous_review_ss']:.1f} units
            - **Safety Stock Expansion Factor:** **{res['periodic_vs_continuous_ss_ratio']}x**
            """)
        with col_c2:
            st.markdown("""
            > **Managerial Insight:**  
            > Periodic review systems are operationally simpler (fixed order schedules, coordinated supplier shipping), but require **larger safety stocks** because the system cannot react to demand spikes until the next scheduled review date $T$.
            """)

        with st.expander("📌 Model Assumptions & Operational Notes"):
            for asm in res["assumptions"]:
                st.write(f"- {asm}")

    except Exception as e:
        st.error(f"Error in Periodic Review calculation: {str(e)}")
