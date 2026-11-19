"""
Multicriteria ABCD Inventory Classification Engine
Implements the exact methodology specified for dual-criterion inventory classification:
- Sales ($) and POS Hits classified independently via cumulative percentage thresholds:
    A: 0% to 60%
    B: above 60% to 80%
    C: above 80% to 90%
    D: above 90% to 100%
- Conversion to discrete scores: A = 4, B = 3, C = 2, D = 1
- Combined weighted score: 0.65 * Sales Score + 0.35 * Hits Score
- Final Class Cutoffs:
    A: score >= 3.25
    B: 2.50 <= score < 3.25
    C: 1.75 <= score < 2.50
    D: score < 1.75
- Documented Tie-Breaking Rule:
    When sorting for Sales:
      1. Primary: Sales ($) descending
      2. Secondary tie-breaker: Hits descending
      3. Tertiary tie-breaker: Item Number ascending (string sort)
    When sorting for Hits:
      1. Primary: Hits descending
      2. Secondary tie-breaker: Sales ($) descending
      3. Tertiary tie-breaker: Item Number ascending (string sort)
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = ["Item Number", "Item Name", "UoM", "Sales ($)", "Hits"]

SCORE_MAP = {"A": 4, "B": 3, "C": 2, "D": 1}
TOLERANCE = 1e-9


def _assign_single_criterion_class(cum_pct: float) -> str:
    """
    Assign A/B/C/D based on cumulative percentage (0.0 to 1.0):
    - A: 0% to 60% (cum_pct <= 0.60)
    - B: above 60% to 80% (0.60 < cum_pct <= 0.80)
    - C: above 80% to 90% (0.80 < cum_pct <= 0.90)
    - D: above 90% to 100% (0.90 < cum_pct <= 1.00)
    """
    if cum_pct <= 0.60 + TOLERANCE:
        return "A"
    elif cum_pct <= 0.80 + TOLERANCE:
        return "B"
    elif cum_pct <= 0.90 + TOLERANCE:
        return "C"
    else:
        return "D"


def _assign_final_class(score: float) -> str:
    """
    Assign final ABCD class based on combined weighted score:
    - A: score >= 3.25
    - B: 2.50 <= score < 3.25
    - C: 1.75 <= score < 2.50
    - D: score < 1.75
    """
    if score >= 3.25 - TOLERANCE:
        return "A"
    elif score >= 2.50 - TOLERANCE:
        return "B"
    elif score >= 1.75 - TOLERANCE:
        return "C"
    else:
        return "D"


def validate_inventory_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates input DataFrame structure, types, and values.
    Returns cleaned copy of DataFrame with proper numeric conversions.
    """
    if df is None or df.empty:
        raise ValueError("The provided inventory dataset is empty.")

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}. Required: {REQUIRED_COLUMNS}")

    df_clean = df.copy()

    # Clean numeric columns (handle potential currency strings or commas)
    for col in ["Sales ($)", "Hits"]:
        if not pd.api.types.is_numeric_dtype(df_clean[col]):
            df_clean[col] = (
                df_clean[col]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

        if df_clean[col].isna().any():
            invalid_rows = df_clean[df_clean[col].isna()].index.tolist()
            raise ValueError(
                f"Column '{col}' contains non-numeric or missing values at row index: {invalid_rows}"
            )

        if (df_clean[col] < 0).any():
            neg_rows = df_clean[df_clean[col] < 0].index.tolist()
            raise ValueError(f"Column '{col}' contains negative values at row index: {neg_rows}")

    total_sales = df_clean["Sales ($)"].sum()
    total_hits = df_clean["Hits"].sum()

    if total_sales <= 0:
        raise ValueError("Total Sales ($) across all items must be strictly greater than 0.")
    if total_hits <= 0:
        raise ValueError("Total Hits across all items must be strictly greater than 0.")

    # Ensure Item Number, Item Name, and UoM are clean stripped strings for stable comparison
    df_clean["Item Number"] = df_clean["Item Number"].astype(str).str.strip()
    df_clean["Item Name"] = df_clean["Item Name"].astype(str).str.strip()
    df_clean["UoM"] = df_clean["UoM"].astype(str).str.strip()

    return df_clean


def classify_multicriteria_abcd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs multicriteria ABCD classification using Sales ($) and POS Hits.

    Returns DataFrame containing original data plus all intermediate audit columns:
    - Sales Rank, Cumulative Sales ($), Cumulative Sales (%), Sales Class, Sales Score
    - Hits Rank, Cumulative Hits, Cumulative Hits (%), Hits Class, Hits Score
    - Combined Score, Final Class
    """
    df_clean = validate_inventory_dataframe(df)

    total_sales = df_clean["Sales ($)"].sum()
    total_hits = df_clean["Hits"].sum()

    # 1. Independent Sales Classification with documented tie-breaking rule:
    #    Primary: Sales ($) desc, Secondary: Hits desc, Tertiary: Item Number asc
    sales_sorted = df_clean.sort_values(
        by=["Sales ($)", "Hits", "Item Number"],
        ascending=[False, False, True]
    ).copy()

    sales_sorted["Sales Rank"] = range(1, len(sales_sorted) + 1)
    sales_sorted["Cumulative Sales ($)"] = sales_sorted["Sales ($)"].cumsum()
    sales_sorted["Cumulative Sales (%)"] = (
        sales_sorted["Cumulative Sales ($)"] / total_sales
    ) * 100.0
    sales_sorted["Sales Class"] = (
        sales_sorted["Cumulative Sales ($)"] / total_sales
    ).apply(_assign_single_criterion_class)
    sales_sorted["Sales Score"] = sales_sorted["Sales Class"].map(SCORE_MAP)

    # 2. Independent Hits Classification with documented tie-breaking rule:
    #    Primary: Hits desc, Secondary: Sales ($) desc, Tertiary: Item Number asc
    hits_sorted = df_clean.sort_values(
        by=["Hits", "Sales ($)", "Item Number"],
        ascending=[False, False, True]
    ).copy()

    hits_sorted["Hits Rank"] = range(1, len(hits_sorted) + 1)
    hits_sorted["Cumulative Hits"] = hits_sorted["Hits"].cumsum()
    hits_sorted["Cumulative Hits (%)"] = (
        hits_sorted["Cumulative Hits"] / total_hits
    ) * 100.0
    hits_sorted["Hits Class"] = (
        hits_sorted["Cumulative Hits"] / total_hits
    ).apply(_assign_single_criterion_class)
    hits_sorted["Hits Score"] = hits_sorted["Hits Class"].map(SCORE_MAP)

    # 3. Merge intermediate results back by Item Number
    # Prepare sales intermediate frame
    sales_cols = [
        "Item Number", "Sales Rank", "Cumulative Sales ($)",
        "Cumulative Sales (%)", "Sales Class", "Sales Score"
    ]
    hits_cols = [
        "Item Number", "Hits Rank", "Cumulative Hits",
        "Cumulative Hits (%)", "Hits Class", "Hits Score"
    ]

    merged = df_clean.merge(sales_sorted[sales_cols], on="Item Number", how="left")
    merged = merged.merge(hits_sorted[hits_cols], on="Item Number", how="left")

    # 4. Calculate Combined Score: 0.65 * Sales Score + 0.35 * Hits Score
    merged["Combined Score"] = np.round(
        0.65 * merged["Sales Score"] + 0.35 * merged["Hits Score"], 4
    )

    # 5. Assign Final Class
    merged["Final Class"] = merged["Combined Score"].apply(_assign_final_class)

    # Sort final output by Sales Rank for clean presentation
    merged = merged.sort_values(by="Sales Rank", ascending=True).reset_index(drop=True)

    return merged


def generate_classification_summary(classified_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a high-level summary table of the ABCD classification results.
    Includes SKU Count, % of SKUs, Total Sales ($), % of Total Sales,
    Total Hits, % of Total Hits, and Average Combined Score for classes A, B, C, D.
    """
    classes = ["A", "B", "C", "D"]
    total_skus = len(classified_df)
    total_sales = classified_df["Sales ($)"].sum()
    total_hits = classified_df["Hits"].sum()

    summary_rows = []
    for cls in classes:
        cls_data = classified_df[classified_df["Final Class"] == cls]
        count = len(cls_data)
        pct_skus = (count / total_skus * 100.0) if total_skus > 0 else 0.0
        sales_sum = cls_data["Sales ($)"].sum()
        pct_sales = (sales_sum / total_sales * 100.0) if total_sales > 0 else 0.0
        hits_sum = cls_data["Hits"].sum()
        pct_hits = (hits_sum / total_hits * 100.0) if total_hits > 0 else 0.0
        avg_score = cls_data["Combined Score"].mean() if count > 0 else 0.0

        summary_rows.append({
            "Class": cls,
            "SKU Count": int(count),
            "% of SKUs": round(pct_skus, 2),
            "Total Sales ($)": round(sales_sum, 2),
            "% of Total Sales": round(pct_sales, 2),
            "Total Hits": int(hits_sum),
            "% of Total Hits": round(pct_hits, 2),
            "Avg Combined Score": round(avg_score, 3)
        })

    summary_df = pd.DataFrame(summary_rows)

    # Add Total / Portfolio row
    total_row = pd.DataFrame([{
        "Class": "Total Portfolio",
        "SKU Count": total_skus,
        "% of SKUs": 100.0,
        "Total Sales ($)": round(total_sales, 2),
        "% of Total Sales": 100.0,
        "Total Hits": int(total_hits),
        "% of Total Hits": 100.0,
        "Avg Combined Score": round(classified_df["Combined Score"].mean(), 3) if total_skus > 0 else 0.0
    }])

    return pd.concat([summary_df, total_row], ignore_index=True)
