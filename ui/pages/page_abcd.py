"""
Multicriteria ABCD Inventory Classification Page
Presents professor's exact dual-criteria classification methodology, audit tables, and summaries.
"""

import streamlit as st
import pandas as pd
from core.classification import classify_multicriteria_abcd, generate_classification_summary
from ui.charts import plot_multicriteria_scatter, plot_dual_pareto
from ui.styles import render_metric_card


def render_abcd_page(raw_df: pd.DataFrame):
    """Renders the Multicriteria ABCD Classification view using the globally loaded DataFrame."""
    st.header("📊 Multicriteria ABCD Inventory Classification")

    st.markdown("""
    **Methodology Overview & Mathematical Formulation:**
    1. **Independent Pareto Sorting & Deterministic Tie-Breaking Rules:**
       - **Sales ($) Ranking:**
         - *Primary Criterion:* `Sales ($)` descending
         - *Secondary Tie-Breaker:* `Hits` descending *(prioritizes items with higher pick/transaction activity)*
         - *Tertiary Tie-Breaker:* `Item Number` ascending *(deterministic unique alphanumeric key)*
         Cumulative Sales % assigned to classes: **A** (0–60%), **B** (above 60–80%), **C** (above 80–90%), **D** (above 90–100%).
       - **POS Hits Ranking:**
         - *Primary Criterion:* `Hits` descending
         - *Secondary Tie-Breaker:* `Sales ($)` descending *(prioritizes items with higher dollar revenue)*
         - *Tertiary Tie-Breaker:* `Item Number` ascending *(deterministic unique alphanumeric key)*
         Cumulative Hits % assigned to classes: **A** (0–60%), **B** (above 60–80%), **C** (above 80–90%), **D** (above 90–100%).
    2. **Criterion Scoring:** $\\text{Class A} = 4, \\quad \\text{Class B} = 3, \\quad \\text{Class C} = 2, \\quad \\text{Class D} = 1$.
    3. **Weighted Combined Score:** $\\text{Combined Score} = 0.65 \\times \\text{Sales Score} + 0.35 \\times \\text{Hits Score}$.
    4. **Final Classification Cutoffs:**
       - **Class A:** $\\text{Score} \\ge 3.25$
       - **Class B:** $2.50 \\le \\text{Score} < 3.25$
       - **Class C:** $1.75 \\le \\text{Score} < 2.50$
       - **Class D:** $\\text{Score} < 1.75$
    """)

    if raw_df is None or raw_df.empty:
        st.warning("⚠️ No inventory data available. Please upload a CSV file in the sidebar or load sample data.")
        return

    try:
        classified_df = classify_multicriteria_abcd(raw_df)
        summary_df = generate_classification_summary(classified_df)
        st.session_state["classified_df"] = classified_df
    except Exception as e:
        st.error(f"❌ Classification Error: {str(e)}")
        return

    # High-Level KPI Summary Cards
    portfolio_row = summary_df[summary_df["Class"] == "Total Portfolio"].iloc[0]
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            label="Total Inventory Items",
            value=f"{int(portfolio_row['SKU Count']):,}",
            sub="Unique SKUs evaluated",
            border_color="#1E88E5"
        )
    with col2:
        render_metric_card(
            label="Total Annual Sales",
            value=f"${portfolio_row['Total Sales ($)']:,.2f}",
            sub="100% of portfolio revenue",
            border_color="#2E7D32"
        )
    with col3:
        render_metric_card(
            label="Total Warehouse Hits",
            value=f"{int(portfolio_row['Total Hits']):,}",
            sub="Total pick transaction frequency",
            border_color="#E65100"
        )
    with col4:
        a_row = summary_df[summary_df["Class"] == "A"].iloc[0]
        render_metric_card(
            label="Class A Contribution",
            value=f"{a_row['% of Total Sales']:.1f}% Sales",
            sub=f"{a_row['SKU Count']} items ({a_row['% of SKUs']:.1f}% of SKUs)",
            border_color="#43A047"
        )

    # Classification Summary Table
    st.subheader("📋 Classification Portfolio Summary")
    st.caption("Aggregated item counts, revenue contribution, pick frequency, and average scores per final ABCD category.")

    # Format summary table for professional display
    formatted_summary = summary_df.copy()
    formatted_summary["Total Sales ($)"] = formatted_summary["Total Sales ($)"].apply(lambda x: f"${x:,.2f}")
    formatted_summary["% of Total Sales"] = formatted_summary["% of Total Sales"].apply(lambda x: f"{x:.2f}%")
    formatted_summary["% of SKUs"] = formatted_summary["% of SKUs"].apply(lambda x: f"{x:.2f}%")
    formatted_summary["Total Hits"] = formatted_summary["Total Hits"].apply(lambda x: f"{x:,}")
    formatted_summary["% of Total Hits"] = formatted_summary["% of Total Hits"].apply(lambda x: f"{x:.2f}%")

    st.dataframe(formatted_summary, use_container_width=True, hide_index=True)

    # Visualizations
    st.subheader("📈 Classification Visualizations")
    tab_scatter, tab_pareto = st.tabs(["2D Multicriteria Scatter Matrix", "Dual Pareto Cumulative Curves"])

    with tab_scatter:
        fig_scatter = plot_multicriteria_scatter(classified_df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab_pareto:
        fig_pareto = plot_dual_pareto(classified_df)
        st.plotly_chart(fig_pareto, use_container_width=True)

    # Comprehensive Audit Table
    st.subheader("🔍 Complete Item Classification Audit Table")
    st.caption("Displays original data and all intermediate calculation steps to allow full auditability.")

    # Filter by class
    selected_classes = st.multiselect(
        "Filter by Final Class:",
        options=["A", "B", "C", "D"],
        default=["A", "B", "C", "D"]
    )
    filtered_df = classified_df[classified_df["Final Class"].isin(selected_classes)]

    # Format numeric columns for clean audit display
    display_df = filtered_df.copy()
    display_df["Sales ($)"] = display_df["Sales ($)"].apply(lambda x: f"${x:,.2f}")
    display_df["Cumulative Sales ($)"] = display_df["Cumulative Sales ($)"].apply(lambda x: f"${x:,.2f}")
    display_df["Cumulative Sales (%)"] = display_df["Cumulative Sales (%)"].apply(lambda x: f"{x:.2f}%")
    display_df["Hits"] = display_df["Hits"].apply(lambda x: f"{int(x):,}")
    display_df["Cumulative Hits"] = display_df["Cumulative Hits"].apply(lambda x: f"{int(x):,}")
    display_df["Cumulative Hits (%)"] = display_df["Cumulative Hits (%)"].apply(lambda x: f"{x:.2f}%")
    display_df["Combined Score"] = display_df["Combined Score"].apply(lambda x: f"{x:.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Export Download Button
    csv_bytes = classified_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Full Audited Classification CSV",
        data=csv_bytes,
        file_name="classified_inventory_audit.csv",
        mime="text/csv"
    )
