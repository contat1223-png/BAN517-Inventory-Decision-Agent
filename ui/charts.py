"""
Interactive Plotly Visualizations for Inventory Decision Agent.
High-fidelity charts for ABCD distribution, EOQ cost curves, Quantity Discounts,
Safety Stock normal distributions, and Newsvendor profit profiles.
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

CLASS_COLORS = {
    "A": "#2E7D32",  # Forest Green
    "B": "#1565C0",  # Corporate Blue
    "C": "#F57F17",  # Amber/Orange
    "D": "#C62828"   # Brick Red
}


def plot_multicriteria_scatter(classified_df: pd.DataFrame) -> go.Figure:
    """
    Renders 2D interactive scatter plot of Sales ($) vs Hits,
    stratified by Final ABCD Classification.
    """
    fig = px.scatter(
        classified_df,
        x="Hits",
        y="Sales ($)",
        color="Final Class",
        color_discrete_map=CLASS_COLORS,
        hover_data={
            "Item Number": True,
            "Item Name": True,
            "Sales Class": True,
            "Hits Class": True,
            "Combined Score": ":.2f",
            "Final Class": True,
            "Sales ($)": ":$,.2f",
            "Hits": True
        },
        title="Multicriteria ABCD Distribution: Sales ($) vs. POS Hits",
        labels={"Hits": "POS Hits (Pick Frequency)", "Sales ($)": "Annual Sales ($)"}
    )

    fig.update_traces(marker=dict(size=12, opacity=0.85, line=dict(width=1, color="DarkSlateGrey")))
    fig.update_layout(
        template="plotly_white",
        legend_title="Final Class",
        hovermode="closest",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def plot_dual_pareto(classified_df: pd.DataFrame) -> go.Figure:
    """
    Renders Dual Pareto cumulative curves for Sales ($) and POS Hits,
    displaying 60%, 80%, and 90% class boundary thresholds.
    """
    n_items = len(classified_df)
    sku_pct = np.linspace(100.0 / n_items, 100.0, n_items)

    # Sales cumulative curve
    sales_cum = classified_df["Cumulative Sales (%)"].values

    # Hits cumulative curve
    hits_cum = classified_df["Cumulative Hits (%)"].values

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=sku_pct,
        y=sales_cum,
        mode="lines+markers",
        name="Cumulative Sales (%)",
        line=dict(color="#1565C0", width=3),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=sku_pct,
        y=hits_cum,
        mode="lines+markers",
        name="Cumulative Hits (%)",
        line=dict(color="#E65100", width=3, dash="dot"),
        marker=dict(size=6)
    ))

    # Add threshold reference lines (60%, 80%, 90%)
    fig.add_hline(y=60, line_dash="dash", line_color="#4CAF50", annotation_text="A/B Cutoff (60%)", annotation_position="bottom right")
    fig.add_hline(y=80, line_dash="dash", line_color="#2196F3", annotation_text="B/C Cutoff (80%)", annotation_position="bottom right")
    fig.add_hline(y=90, line_dash="dash", line_color="#FF9800", annotation_text="C/D Cutoff (90%)", annotation_position="bottom right")

    fig.update_layout(
        title="Dual Cumulative Pareto Curves (Sales vs. Hits)",
        xaxis_title="Cumulative % of Inventory Items (SKUs)",
        yaxis_title="Cumulative % of Total Criterion Value",
        yaxis=dict(range=[0, 105]),
        template="plotly_white",
        legend=dict(x=0.02, y=0.98),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def plot_eoq_curves(df_curve: pd.DataFrame, eoq_val: float, min_tic: float) -> go.Figure:
    """
    Renders the canonical Total Cost, Holding Cost, and Ordering Cost curves
    with an optimal Q* marker.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_curve["Order Quantity (Q)"],
        y=df_curve["Annual Ordering Cost ($)"],
        mode="lines",
        name="Annual Ordering Cost",
        line=dict(color="#E53935", width=2, dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=df_curve["Order Quantity (Q)"],
        y=df_curve["Annual Holding Cost ($)"],
        mode="lines",
        name="Annual Holding Cost",
        line=dict(color="#1E88E5", width=2, dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=df_curve["Order Quantity (Q)"],
        y=df_curve["Total Annual Inventory Cost ($)"],
        mode="lines",
        name="Total Inventory Cost (TIC)",
        line=dict(color="#2E7D32", width=3)
    ))

    # Optimal EOQ marker
    fig.add_trace(go.Scatter(
        x=[eoq_val],
        y=[min_tic],
        mode="markers+text",
        name=f"Optimal Q* ({eoq_val:,.1f})",
        marker=dict(color="#FFD700", size=14, line=dict(color="black", width=2)),
        text=[f"Q* = {eoq_val:,.0f}<br>${min_tic:,.2f}"],
        textposition="top center"
    ))

    fig.add_vline(x=eoq_val, line_dash="dot", line_color="#757575")

    fig.update_layout(
        title="EOQ Total Cost Trade-Off Curve",
        xaxis_title="Order Quantity (Q)",
        yaxis_title="Annual Cost ($)",
        template="plotly_white",
        legend=dict(x=0.68, y=0.98),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def plot_quantity_discounts(summary_df: pd.DataFrame, optimal_tier: str) -> go.Figure:
    """
    Renders bar chart comparing Total Annual Cost across discount tiers.
    """
    colors = ["#2E7D32" if t == optimal_tier else "#90CAF9" for t in summary_df["Tier"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=summary_df["Tier"],
        y=summary_df["Total Annual Cost ($)"],
        marker_color=colors,
        text=[f"${v:,.2f}" if v is not None else "Infeasible" for v in summary_df["Total Annual Cost ($)"]],
        textposition="auto"
    ))

    fig.update_layout(
        title="Total Annual Acquisition Cost by Quantity Discount Tier",
        xaxis_title="Discount Bracket / Tier",
        yaxis_title="Total Annual Cost ($)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def plot_safety_stock_distribution(
    mean_lt_demand: float,
    sigma_lt_demand: float,
    safety_stock: float,
    reorder_point: float,
    service_level: float
) -> go.Figure:
    """
    Renders Normal bell curve representing Lead Time Demand with
    Safety Stock cushion and Reorder Point (ROP).
    """
    x_min = max(0, mean_lt_demand - 3.5 * sigma_lt_demand)
    x_max = mean_lt_demand + 3.5 * sigma_lt_demand
    x_vals = np.linspace(x_min, x_max, 300)

    # Normal PDF
    y_vals = (1.0 / (sigma_lt_demand * np.sqrt(2.0 * np.pi))) * np.exp(
        -0.5 * ((x_vals - mean_lt_demand) / sigma_lt_demand) ** 2
    )

    fig = go.Figure()

    # Base curve
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="lines",
        name="Lead Time Demand PDF",
        line=dict(color="#1565C0", width=2.5)
    ))

    # Shaded service level area (x <= ROP)
    mask = x_vals <= reorder_point
    fig.add_trace(go.Scatter(
        x=x_vals[mask],
        y=y_vals[mask],
        fill="tozeroy",
        mode="none",
        name=f"Cycle Service Level ({service_level * 100:.1f}%)",
        fillcolor="rgba(46, 125, 50, 0.3)"
    ))

    # Vertical line at Mean Demand
    fig.add_vline(
        x=mean_lt_demand,
        line_dash="dash",
        line_color="#E65100",
        annotation_text=f"Expected Demand ({mean_lt_demand:,.0f})",
        annotation_position="top left"
    )

    # Vertical line at ROP
    fig.add_vline(
        x=reorder_point,
        line_dash="solid",
        line_color="#2E7D32",
        annotation_text=f"ROP = {reorder_point:,.0f}<br>(SS = +{safety_stock:,.0f})",
        annotation_position="top right"
    )

    fig.update_layout(
        title="Lead-Time Demand Distribution & Safety Stock Cushion",
        xaxis_title="Demand During Lead Time (Units)",
        yaxis_title="Probability Density",
        template="plotly_white",
        legend=dict(x=0.02, y=0.98),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def plot_newsvendor_payoff(
    unit_price: float,
    unit_cost: float,
    salvage_value: float,
    mean_demand: float,
    std_demand: float,
    q_star: float,
    optimal_profit: float
) -> go.Figure:
    """
    Renders Expected Profit curve across order quantities Q in the Newsvendor model.
    """
    q_range = np.linspace(max(10, mean_demand - 2.5 * std_demand), mean_demand + 2.5 * std_demand, 80)
    profits = []

    for q in q_range:
        # Standard normal loss using Python standard library math functions
        z = float((q - mean_demand) / std_demand)
        phi = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * z * z)
        Phi = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        lost_sales = std_demand * (phi - z * (1.0 - Phi))
        leftover = q - mean_demand + lost_sales
        sales = mean_demand - lost_sales
        profit = unit_price * sales + salvage_value * leftover - unit_cost * q
        profits.append(profit)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=q_range,
        y=profits,
        mode="lines",
        name="Expected Profit ($)",
        line=dict(color="#1565C0", width=3)
    ))

    # Mark Q*
    fig.add_trace(go.Scatter(
        x=[q_star],
        y=[optimal_profit],
        mode="markers+text",
        name=f"Optimal Q* ({q_star:,.0f})",
        marker=dict(color="#2E7D32", size=14, line=dict(color="black", width=2)),
        text=[f"Q* = {q_star:,.0f}<br>${optimal_profit:,.2f}"],
        textposition="top center"
    ))

    fig.update_layout(
        title="Newsvendor Expected Profit vs. Order Quantity (Q)",
        xaxis_title="Order Quantity (Q)",
        yaxis_title="Expected Profit ($)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig
