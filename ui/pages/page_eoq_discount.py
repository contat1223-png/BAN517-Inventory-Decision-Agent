"""
EOQ and Quantity Discount Analysis View
Provides lot sizing calculators, trade-off cost curves, and bracket discount optimization.
"""

import streamlit as st
import pandas as pd
from core.eoq import calculate_eoq, calculate_eoq_sensitivity
from core.discounts import analyze_quantity_discounts, DiscountTier
from ui.charts import plot_eoq_curves, plot_quantity_discounts
from ui.styles import render_metric_card


def render_eoq_discount_page(classified_df: pd.DataFrame):
    """Renders the EOQ and Quantity Discount analysis page."""
    st.header("📦 Lot Sizing: EOQ & Quantity Discount Analysis")

    tab_eoq, tab_discount = st.tabs(["Classic Economic Order Quantity (EOQ)", "Quantity Discount Analysis"])

    # ---------------- TAB 1: BASIC EOQ ----------------
    with tab_eoq:
        st.subheader("Classic Economic Order Quantity (Harris-Wilson Model)")

        st.markdown("""
        The **Economic Order Quantity (EOQ)** minimizes the sum of annual ordering setup costs and inventory holding costs:
        $$EOQ = \\sqrt{\\frac{2 D S}{H}}$$
        """)

        # Option to preload parameters from an inventory SKU
        default_demand = 10000.0
        default_cost = 25.0
        if classified_df is not None and not classified_df.empty:
            use_sku = st.checkbox("Pre-fill Annual Demand from an inventory item in uploaded dataset", value=False)
            if use_sku:
                sku_options = classified_df["Item Number"] + " - " + classified_df["Item Name"]
                selected_sku_label = st.selectbox("Select SKU:", sku_options)
                selected_item_num = selected_sku_label.split(" - ")[0]
                item_row = classified_df[classified_df["Item Number"] == selected_item_num].iloc[0]
                # If sales is available, estimate demand
                sales_val = float(item_row["Sales ($)"])
                default_cost = 50.0
                default_demand = max(100.0, round(sales_val / default_cost))

        col_in1, col_in2 = st.columns(2)
        with col_in1:
            annual_demand = st.number_input("Annual Demand (D, units/year):", min_value=1.0, value=float(default_demand), step=100.0)
            order_cost = st.number_input("Order Setup Cost (S, $/order):", min_value=0.01, value=65.0, step=5.0)
            unit_cost = st.number_input("Unit Purchase Cost (C, $/unit):", min_value=0.01, value=float(default_cost), step=1.0)

        with col_in2:
            holding_input_type = st.radio(
                "Holding Cost Specification:",
                ["Holding Cost Rate (h, % of unit cost)", "Fixed Holding Cost ($/unit/year)"]
            )
            if "Rate" in holding_input_type:
                holding_rate_pct = st.slider("Annual Holding Rate (%):", min_value=1.0, max_value=60.0, value=22.0, step=0.5)
                holding_cost_h = (holding_rate_pct / 100.0) * unit_cost
                holding_rate_arg = holding_rate_pct / 100.0
                st.caption(f"Calculated Holding Cost: **${holding_cost_h:.2f}** per unit/year")
            else:
                holding_cost_h = st.number_input("Fixed Holding Cost (H, $/unit/year):", min_value=0.01, value=5.50, step=0.50)
                holding_rate_arg = None

            work_days = st.number_input("Operational Days per Year:", min_value=50, max_value=365, value=250, step=5)

        try:
            eoq_res = calculate_eoq(
                annual_demand=annual_demand,
                order_cost=order_cost,
                holding_cost=holding_cost_h,
                unit_cost=unit_cost,
                work_days_per_year=int(work_days)
            )

            # Display KPI Cards
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                render_metric_card(
                    label="Optimal Order Quantity (Q*)",
                    value=f"{eoq_res['eoq_rounded']:,} units",
                    sub=f"Exact: {eoq_res['eoq']:.1f} units",
                    border_color="#2E7D32"
                )
            with kpi2:
                render_metric_card(
                    label="Total Inventory Cost (TIC)",
                    value=f"${eoq_res['total_inventory_cost']:,.2f}",
                    sub="Holding + Ordering",
                    border_color="#1E88E5"
                )
            with kpi3:
                render_metric_card(
                    label="Orders per Year (N)",
                    value=f"{eoq_res['orders_per_year']:.1f}",
                    sub=f"Cycle: {eoq_res['cycle_time_days']:.1f} workdays",
                    border_color="#E65100"
                )
            with kpi4:
                render_metric_card(
                    label="Total Acquisition Cost (TAC)",
                    value=f"${eoq_res['total_acquisition_cost']:,.2f}",
                    sub=f"Incl. ${eoq_res['purchase_cost']:,.2f} purchase",
                    border_color="#43A047"
                )

            # Interactive Cost Trade-off Chart
            df_curve = calculate_eoq_sensitivity(
                annual_demand=annual_demand,
                order_cost=order_cost,
                holding_cost=holding_cost_h,
                eoq=eoq_res["eoq"]
            )
            fig_eoq = plot_eoq_curves(df_curve, eoq_res["eoq"], eoq_res["total_inventory_cost"])
            st.plotly_chart(fig_eoq, use_container_width=True)

            # Model Assumptions
            with st.expander("📌 Harris-Wilson Model Assumptions & Constraints"):
                for asm in eoq_res["assumptions"]:
                    st.write(f"- {asm}")

        except Exception as e:
            st.error(f"Error in EOQ calculation: {str(e)}")

    # ---------------- TAB 2: QUANTITY DISCOUNTS ----------------
    with tab_discount:
        st.subheader("All-Units Quantity Discount Analysis")
        st.markdown("""
        Suppliers frequently offer tiered pricing based on lot size. The optimal order quantity balances price discounts against increased inventory holding charges:
        $$TAC(Q) = D \\cdot C_i + \\frac{D}{Q}S + \\frac{Q}{2}H_i$$
        """)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            disc_demand = st.number_input("Annual Demand (D):", min_value=1.0, value=5000.0, step=250.0, key="disc_d")
            disc_order_cost = st.number_input("Order Setup Cost (S, $/order):", min_value=0.01, value=49.0, step=5.0, key="disc_s")
        with col_d2:
            disc_holding_rate = st.slider("Holding Cost Rate (h, % of unit price):", min_value=1.0, max_value=60.0, value=20.0, step=0.5, key="disc_h") / 100.0

        st.markdown("**Discount Pricing Brackets Configuration:**")
        st.caption("Adjust the bracket minimum quantities and unit prices below:")

        # Default bracket configuration
        default_tiers_data = [
            {"Tier": "Tier 1 (Base)", "Min Qty": 1.0, "Max Qty": 999.0, "Unit Price ($)": 5.00},
            {"Tier": "Tier 2 (Discount 1)", "Min Qty": 1000.0, "Max Qty": 1999.0, "Unit Price ($)": 4.80},
            {"Tier": "Tier 3 (Discount 2)", "Min Qty": 2000.0, "Max Qty": 999999.0, "Unit Price ($)": 4.75},
        ]

        edited_tiers = st.data_editor(
            pd.DataFrame(default_tiers_data),
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("Evaluate Quantity Discounts", type="primary"):
            try:
                tier_objects = []
                for _, row in edited_tiers.iterrows():
                    tier_objects.append(
                        DiscountTier(
                            tier_name=str(row["Tier"]),
                            min_qty=float(row["Min Qty"]),
                            max_qty=float(row["Max Qty"]),
                            unit_price=float(row["Unit Price ($)"])
                        )
                    )

                disc_res = analyze_quantity_discounts(
                    annual_demand=disc_demand,
                    order_cost=disc_order_cost,
                    tiers=tier_objects,
                    holding_rate=disc_holding_rate
                )

                st.success(f"★ **Optimal Decision:** Order **{disc_res['optimal_quantity']:,.0f} units** at **${disc_res['optimal_price']:.2f}/unit** ({disc_res['optimal_tier']}). Minimizes Total Annual Cost to **${disc_res['optimal_total_cost']:,.2f}**.")

                # Comparative Table
                st.dataframe(disc_res["summary_table"], use_container_width=True, hide_index=True)

                # Bar Chart
                fig_bar = plot_quantity_discounts(disc_res["summary_table"], disc_res["optimal_tier"])
                st.plotly_chart(fig_bar, use_container_width=True)

            except Exception as e:
                st.error(f"Quantity Discount Error: {str(e)}")
