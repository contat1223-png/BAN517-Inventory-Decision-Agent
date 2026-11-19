# Inventory Decision Agent 📦

An enterprise-grade inventory decision support system built in Python and Streamlit. The application performs multicriteria ABCD inventory classification, optimal lot sizing (EOQ and Quantity Discounts), stochastic safety stock & reorder point analysis (Continuous Review), Fixed-Period Review policies (Order-Up-To Level $S$), and single-period perishable decisions (Newsvendor Model).

---

## 🎯 Key Features

1. **Multicriteria ABCD Inventory Classification**:
   - Implements dual-criteria classification using **Sales ($)** and **POS Hits** (warehouse transaction picks).
   - Independent Pareto cumulative sorting with documented tie-breaking rules.
   - Cumulative percentage boundaries:
     - **Class A:** 0% to 60%
     - **Class B:** above 60% to 80%
     - **Class C:** above 80% to 90%
     - **Class D:** above 90% to 100%
   - Discrete criterion scoring: $A = 4, B = 3, C = 2, D = 1$.
   - Combined weighted score: $\text{Combined Score} = 0.65 \times \text{Sales Score} + 0.35 \times \text{Hits Score}$.
   - Final classification cutoffs:
     - **A:** $\ge 3.25$
     - **B:** $2.50 \le \text{Score} < 3.25$
     - **C:** $1.75 \le \text{Score} < 2.50$
     - **D:** $< 1.75$
   - Full calculation audit trail table with intermediate ranks, cumulative percentages, and scores.

2. **Single Global CSV Uploader**:
   - One uploader in the sidebar powers classification and populates SKU parameters across the application.
   - Built-in sample dataset with 28 realistic industrial SKUs for immediate testing.

3. **Economic Order Quantity (EOQ)**:
   - Evaluates optimal order batch size $Q^*$, Total Inventory Cost (TIC), and Total Acquisition Cost (TAC).
   - Interactive Plotly cost trade-off curve across order quantities.

4. **Quantity Discount Analysis**:
   - All-units tiered price break solver.
   - Checks feasibility of unconstrained EOQs and adjusts to bracket thresholds.
   - Comparative evaluation table and cost step visualization.

5. **Safety Stock & Reorder Point (Continuous Review $Q, ROP$)**:
   - Supports three stochastic uncertainty scenarios:
     1. Variable Demand, Constant Lead Time
     2. Constant Demand, Variable Lead Time
     3. Both Demand and Lead Time Variable
   - Normal distribution visualization highlighting the safety stock buffer.

6. **Fixed-Period Review System ($T, S$)**:
   - Calculates target Order-Up-To level $S$ protecting against demand over interval $(T + L)$.
   - Evaluates net inventory position and computes exact replenishment order $Q$.
   - Quantifies the safety stock expansion factor relative to continuous review.

7. **Newsvendor Model (Single-Period Probabilistic)**:
   - Computes Underage Cost ($C_u$), Overage Cost ($C_o$), and Critical Fractile ($CR$).
   - Evaluates optimal order quantity $Q^*$, expected leftover inventory, lost sales, and Expected Value of Perfect Information (EVPI).

---

## 🏗️ Project Architecture

```text
inventory-decision-agent/
├── app.py                         # Streamlit application entrypoint & routing
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
│
├── core/                          # Pure Python calculation engines (100% tested)
│   ├── __init__.py
│   ├── classification.py          # Multicriteria ABCD classification engine
│   ├── eoq.py                     # Economic Order Quantity
│   ├── discounts.py               # Quantity Discount Analysis
│   ├── safety_stock.py            # Safety Stock and ROP (Continuous Review)
│   ├── periodic_review.py         # Fixed-Period Review (T, S)
│   └── newsvendor.py              # Newsvendor Critical Fractile Model
│
├── ui/                            # Streamlit presentation layer
│   ├── __init__.py
│   ├── styles.py                  # Custom CSS styling and KPI cards
│   ├── charts.py                  # Interactive Plotly visualizers
│   └── pages/                     # Dedicated view modules
│       ├── page_abcd.py           # ABCD Classification & Audit View
│       ├── page_eoq_discount.py   # EOQ & Quantity Discounts View
│       ├── page_safety_stock.py   # Continuous Review Safety Stock View
│       ├── page_periodic.py       # Fixed-Period Review View
│       └── page_newsvendor.py     # Newsvendor Analysis View
│
├── sample_data/
│   └── sample_inventory.csv       # 28-SKU sample inventory dataset
│
└── tests/                         # Comprehensive Pytest automated test suite
    ├── __init__.py
    ├── test_classification.py     # Classification boundaries, ties, scores, validation
    ├── test_eoq.py                # Harris-Wilson benchmarks & sensitivity
    ├── test_discounts.py          # All-units discount feasibility & benchmarks
    ├── test_safety_stock.py       # 3 variability scenarios & z-factor accuracy
    ├── test_periodic_review.py    # Protection interval & order-up-to S
    └── test_newsvendor.py         # Underage/overage, normal loss & empirical samples
```

---

## 🚀 Installation & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Automated Tests
```bash
pytest -v tests/
```

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```

---

## ☁️ Deploying to Streamlit Community Cloud

1. **Push your code to a GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Inventory Decision Agent"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **"New app"**.
   - Select your repository, branch (`main`), and set **Main file path** to `app.py`.
   - Click **"Deploy!"**.
   - Streamlit will automatically read `requirements.txt` and launch your live application.
