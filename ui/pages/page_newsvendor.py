"""
Newsvendor (Single-Period Probabilistic) Analysis View
Solves optimal procurement for perishable, seasonal, or single-lifecycle inventory items.
"""

import streamlit as st
import pandas as pd
from core.newsvendor import calculate_newsvendor
from ui.charts import plot_newsvendor_payoff
from ui.styles import render_metric_card


def render_newsvendor_page(classified_df: pd.DataFrame):
    """Renders the Newsvendor critical ratio optimization interface."""
    st.header("🎲 Single-Period Decision: Newsvendor Model")

    st.markdown("""
    The **Newsvendor Model** determines the optimal order quantity for perishable, seasonal, or fashion goods subject to uncertain demand:
    $$\\text{Critical Fractile } (CR) = \\frac{C_u}{C_u + C_o} = \\frac{P - C + g}{(P - C + g) + (C - V)}$$
    $$Q^* = F^{-1}(CR)$$
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Financial Margins & Cost Structure")
        unit_price = st.number_input("Unit Selling Price (P, $/unit):", min_value=0.01, value=120.0, step=5.0)
        unit_cost = st.number_input("Unit Procurement Cost (C, $/unit):", min_value=0.01, value=70.0, step=5.0)
        salvage_value = st.number_input("Salvage Value / Liquidation (V, $/unit):", min_value=0.0, value=25.0, step=5.0)
        penalty_cost = st.number_input("Lost Sales Goodwill Penalty (g, $/unit):", min_value=0.0, value=0.0, step=1.0)

    with col2:
        st.subheader("Demand Uncertainty Model")
        demand_mode = st.radio("Demand Distribution:", ["Normal Distribution (Parametric)", "Empirical Historical Samples"])

        if "Normal" in demand_mode:
            demand_mean = st.number_input("Expected Demand Mean (μ):", min_value=1.0, value=1000.0, step=50.0)
            demand_std = st.number_input("Demand Standard Deviation (σ):", min_value=0.1, value=250.0, step=10.0)
            samples = None
        else:
            sample_str = st.text_area(
                "Historical Demand Samples (comma-separated):",
                value="650, 720, 800, 850, 920, 980, 1020, 1080, 1150, 1280, 1400"
            )
            samples = [float(x.strip()) for x in sample_str.split(",") if x.strip()]
            demand_mean = None
            demand_std = None

    try:
        res = calculate_newsvendor(
            unit_price=unit_price,
            unit_cost=unit_cost,
            salvage_value=salvage_value,
            penalty_cost=penalty_cost,
            demand_mean=demand_mean,
            demand_std=demand_std,
            empirical_demand_samples=samples
        )

        # KPI Metrics
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_metric_card(
                label="Optimal Order Quantity (Q*)",
                value=f"{int(res['optimal_quantity']):,} units",
                sub=f"Critical Ratio: {res['critical_ratio_pct']:.1f}%",
                border_color="#2E7D32"
            )
        with k2:
            render_metric_card(
                label="Cost of Underage (Cu)",
                value=f"${res['cost_of_underage_Cu']:.2f}",
                sub="Margin lost per stockout",
                border_color="#1E88E5"
            )
        with k3:
            render_metric_card(
                label="Cost of Overage (Co)",
                value=f"${res['cost_of_overage_Co']:.2f}",
                sub="Loss per unsold unit",
                border_color="#E65100"
            )
        with k4:
            if "expected_profit" in res:
                render_metric_card(
                    label="Expected Profit",
                    value=f"${res['expected_profit']:,.2f}",
                    sub=f"EVPI: ${res['evpi']:,.2f}",
                    border_color="#43A047"
                )
            else:
                render_metric_card(
                    label="Sample Size",
                    value=f"{res['sample_size']} observations",
                    sub=f"Mean: {res['sample_mean']:.0f} units",
                    border_color="#43A047"
                )

        if "Normal" in demand_mode:
            # Operational breakdown
            st.subheader("📊 Operational Risk Breakdown at Q*")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Expected Sales", f"{res['expected_sales']:,} units")
            b2.metric("Expected Leftover Stock", f"{res['expected_leftover']:,} units")
            b3.metric("Expected Lost Sales", f"{res['expected_lost_sales']:,} units")
            b4.metric("Total Procurement Spend", f"${res['procurement_cost']:,.2f}")

            # Payoff Curve Chart
            fig_nv = plot_newsvendor_payoff(
                unit_price=unit_price,
                unit_cost=unit_cost,
                salvage_value=salvage_value,
                mean_demand=demand_mean,
                std_demand=demand_std,
                q_star=res["optimal_quantity"],
                optimal_profit=res["expected_profit"]
            )
            st.plotly_chart(fig_nv, use_container_width=True)

        with st.expander("📌 Model Assumptions & Operational Notes"):
            for asm in res["assumptions"]:
                st.write(f"- {asm}")

    except Exception as e:
        st.error(f"Error in Newsvendor calculation: {str(e)}")
