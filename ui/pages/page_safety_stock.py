"""
Safety Stock and Reorder Point (Continuous Review Policy) View
Supports stochastic demand and lead-time variability scenarios.
"""

import streamlit as st
import pandas as pd
from core.safety_stock import calculate_safety_stock, DemandLeadTimeScenario
from ui.charts import plot_safety_stock_distribution
from ui.styles import render_metric_card


def render_safety_stock_page(classified_df: pd.DataFrame):
    """Renders the Continuous Review (Q, ROP) safety stock calculator."""
    st.header("🛡️ Continuous Review: Safety Stock & Reorder Point (ROP)")

    st.markdown("""
    Under continuous review, inventory is monitored continuously. When the inventory position drops to the **Reorder Point (ROP)**, a replenishment order $Q$ is placed:
    $$ROP = \\text{Expected Demand During Lead Time} + \\text{Safety Stock}$$
    """)

    scenario_choice = st.selectbox(
        "Select Stochastic Variability Scenario:",
        [
            DemandLeadTimeScenario.VAR_DEMAND_CONST_LT.value,
            DemandLeadTimeScenario.CONST_DEMAND_VAR_LT.value,
            DemandLeadTimeScenario.BOTH_VARIABLE.value
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Demand & Lead Time Parameters")
        avg_demand = st.number_input("Average Demand per Period (d̄):", min_value=0.1, value=100.0, step=10.0)
        avg_lead_time = st.number_input("Average Supplier Lead Time (L̄, in same periods):", min_value=0.1, value=4.0, step=0.5)

        if scenario_choice in [DemandLeadTimeScenario.VAR_DEMAND_CONST_LT.value, DemandLeadTimeScenario.BOTH_VARIABLE.value]:
            std_demand = st.number_input("Standard Deviation of Demand (σ_d):", min_value=0.0, value=20.0, step=2.0)
        else:
            std_demand = None

        if scenario_choice in [DemandLeadTimeScenario.CONST_DEMAND_VAR_LT.value, DemandLeadTimeScenario.BOTH_VARIABLE.value]:
            std_lead_time = st.number_input("Standard Deviation of Lead Time (σ_L):", min_value=0.0, value=1.5, step=0.2)
        else:
            std_lead_time = None

    with col2:
        st.subheader("Service Level Targets")
        service_level_pct = st.slider(
            "Desired Cycle Service Level (CSL, %):",
            min_value=50.0,
            max_value=99.9,
            value=95.0,
            step=0.5,
            help="Probability that demand will be fully met from inventory during the replenishment lead time."
        )
        service_level = service_level_pct / 100.0

        orders_per_year = st.number_input(
            "Estimated Orders per Year (N, for annual risk):",
            min_value=1.0,
            value=12.0,
            step=1.0
        )

    try:
        scenario_enum = DemandLeadTimeScenario(scenario_choice)
        res = calculate_safety_stock(
            scenario=scenario_enum,
            service_level=service_level,
            avg_demand=avg_demand,
            std_demand=std_demand,
            avg_lead_time=avg_lead_time,
            std_lead_time=std_lead_time,
            orders_per_year=orders_per_year
        )

        st.markdown(f"**Applied Mathematical Model:** `{res['formula_used']}`")

        # KPI Metrics
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            render_metric_card(
                label="Reorder Point (ROP)",
                value=f"{res['reorder_point_rounded']:,} units",
                sub=f"Exact: {res['reorder_point']:.1f}",
                border_color="#2E7D32"
            )
        with kpi2:
            render_metric_card(
                label="Safety Stock (SS)",
                value=f"{res['safety_stock_rounded']:,} units",
                sub=f"Exact: {res['safety_stock']:.1f}",
                border_color="#1E88E5"
            )
        with kpi3:
            render_metric_card(
                label="Normal Z-Factor",
                value=f"{res['z_score']:.4f}",
                sub=f"For {res['service_level_pct']:.1f}% CSL",
                border_color="#8E24AA"
            )
        with kpi4:
            render_metric_card(
                label="Cycle Stockout Risk",
                value=f"{res['cycle_stockout_risk_pct']:.2f}%",
                sub=f"~{res['expected_stockouts_per_year']:.2f} stockouts/yr",
                border_color="#E65100"
            )

        # Bell Curve Visualizer
        fig_bell = plot_safety_stock_distribution(
            mean_lt_demand=res["mean_lead_time_demand"],
            sigma_lt_demand=res["sigma_lead_time_demand"],
            safety_stock=res["safety_stock"],
            reorder_point=res["reorder_point"],
            service_level=service_level
        )
        st.plotly_chart(fig_bell, use_container_width=True)

        with st.expander("📌 Model Assumptions & Operational Notes"):
            for asm in res["assumptions"]:
                st.write(f"- {asm}")

    except Exception as e:
        st.error(f"Error in Safety Stock calculation: {str(e)}")
