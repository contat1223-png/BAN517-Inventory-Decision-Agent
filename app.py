"""
Inventory Decision Agent - Streamlit Application Entrypoint
Single CSV Uploader architecture, global state management, and multi-tool navigation.
"""

import os
import streamlit as st
import pandas as pd
from ui.styles import apply_custom_styles
from ui.pages.page_abcd import render_abcd_page
from ui.pages.page_eoq_discount import render_eoq_discount_page
from ui.pages.page_safety_stock import render_safety_stock_page
from ui.pages.page_periodic import render_periodic_review_page
from ui.pages.page_newsvendor import render_newsvendor_page
from core.classification import validate_inventory_dataframe, classify_multicriteria_abcd

# Configure Streamlit page
st.set_page_config(
    page_title="Inventory Decision Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply unified CSS styling
apply_custom_styles()

SAMPLE_DATA_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "sample_inventory.csv")


def init_session_state():
    """Initializes global session state for inventory dataset."""
    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = None
    if "classified_df" not in st.session_state:
        st.session_state["classified_df"] = None
    if "data_source" not in st.session_state:
        st.session_state["data_source"] = "None"


init_session_state()

# ---------------- SIDEBAR: GLOBAL CSV UPLOADER & NAVIGATION ----------------
st.sidebar.title("📦 Inventory Agent")
st.sidebar.caption("Enterprise Inventory Optimization & Multicriteria Classification System")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Inventory Data Source")
st.sidebar.markdown("Upload your inventory dataset once; it powers classification and parameter presets across all decision modules.")

uploaded_file = st.sidebar.file_uploader(
    "Upload Inventory CSV:",
    type=["csv"],
    help="CSV must contain: Item Number, Item Name, UoM, Sales ($), Hits"
)

col_btn1, col_btn2 = st.sidebar.columns(2)
with col_btn1:
    load_sample = st.button("Use Sample Data", use_container_width=True)
with col_btn2:
    clear_data = st.button("Clear Data", use_container_width=True)

if clear_data:
    st.session_state["raw_df"] = None
    st.session_state["classified_df"] = None
    st.session_state["data_source"] = "None"
    st.rerun()

if load_sample and os.path.exists(SAMPLE_DATA_PATH):
    try:
        sample_df = pd.read_csv(SAMPLE_DATA_PATH)
        validated_df = validate_inventory_dataframe(sample_df)
        st.session_state["raw_df"] = validated_df
        st.session_state["classified_df"] = classify_multicriteria_abcd(validated_df)
        st.session_state["data_source"] = "Sample Dataset (28 SKUs)"
        st.sidebar.success("Loaded sample inventory data!")
    except Exception as e:
        st.sidebar.error(f"Error loading sample data: {e}")

if uploaded_file is not None:
    try:
        user_df = pd.read_csv(uploaded_file)
        validated_df = validate_inventory_dataframe(user_df)
        st.session_state["raw_df"] = validated_df
        st.session_state["classified_df"] = classify_multicriteria_abcd(validated_df)
        st.session_state["data_source"] = f"Uploaded: {uploaded_file.name}"
        st.sidebar.success(f"✓ {len(validated_df):,} items loaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Upload validation failed: {str(e)}")

# Display data status in sidebar
if st.session_state["raw_df"] is not None:
    st.sidebar.info(f"**Active Dataset:** {st.session_state['data_source']}\n\n**Items:** {len(st.session_state['raw_df']):,}")
else:
    st.sidebar.warning("No data loaded. Use 'Upload CSV' or 'Use Sample Data'.")

st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")
menu = st.sidebar.radio(
    "Select Decision Tool:",
    [
        "1. Multicriteria ABCD Classification",
        "2. EOQ & Quantity Discounts",
        "3. Safety Stock & Reorder Point",
        "4. Fixed-Period Review (T, S)",
        "5. Newsvendor (Single-Period)",
        "6. Methodology & Documentation"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Inventory Decision Agent v1.0.0")

# ---------------- PAGE ROUTING ----------------
current_classified_df = st.session_state.get("classified_df", None)

if menu.startswith("1."):
    render_abcd_page(st.session_state.get("raw_df", None))

elif menu.startswith("2."):
    render_eoq_discount_page(current_classified_df)

elif menu.startswith("3."):
    render_safety_stock_page(current_classified_df)

elif menu.startswith("4."):
    render_periodic_review_page(current_classified_df)

elif menu.startswith("5."):
    render_newsvendor_page(current_classified_df)

elif menu.startswith("6."):
    st.header("📖 Inventory Methodology & User Guide")
    st.markdown("""
    ### 1. Multicriteria ABCD Classification Methodology
    This application applies the professor's exact dual-criteria classification methodology combining **Sales ($)** and **POS Hits**:
    - **Sales ($) Classification:**
      1. Items sorted descending by `Sales ($)`.
      2. **Tie-Breaking Rule:** Equal Sales broken by `Hits` descending, then `Item Number` ascending.
      3. Cumulative Sales percentage cutoffs:
         - **A:** $0\\% \\text{ to } 60\\%$
         - **B:** $\\text{above } 60\\% \\text{ to } 80\\%$
         - **C:** $\\text{above } 80\\% \\text{ to } 90\\%$
         - **D:** $\\text{above } 90\\% \\text{ to } 100\\%$
    - **POS Hits Classification:**
      1. Items sorted independently descending by `Hits`.
      2. **Tie-Breaking Rule:** Equal Hits broken by `Sales ($)` descending, then `Item Number` ascending.
      3. Cumulative Hits percentage cutoffs: **A** (0–60%), **B** (above 60–80%), **C** (above 80–90%), **D** (above 90–100%).
    - **Criterion Scoring:**
      $$\\text{Class A} = 4, \\quad \\text{Class B} = 3, \\quad \\text{Class C} = 2, \\quad \\text{Class D} = 1$$
    - **Combined Score:**
      $$\\text{Combined Score} = 0.65 \\times \\text{Sales Score} + 0.35 \\times \\text{Hits Score}$$
    - **Final Classification Assignment:**
      - **A:** $\\text{Score} \\ge 3.25$
      - **B:** $2.50 \\le \\text{Score} < 3.25$
      - **C:** $1.75 \\le \\text{Score} < 2.50$
      - **D:** $\\text{Score} < 1.75$

    ---

    ### 2. Supported Inventory Decision Models
    - **Economic Order Quantity (EOQ):** Canonical lot sizing balancing order setup and holding charges under constant demand.
    - **Quantity Discounts:** All-units tiered discount evaluator finding the globally minimal Total Acquisition Cost (TAC).
    - **Continuous Review (Q, ROP):** Safety stock and reorder point determination under demand uncertainty, lead time uncertainty, or both.
    - **Fixed-Period Review (T, S):** Periodic review order-up-to level calculation protecting against demand across the full protection interval $(T + L)$.
    - **Newsvendor Model:** Critical fractile decision framework for seasonal or perishable products with underage ($C_u$) and overage ($C_o$) cost asymmetries.
    """)
