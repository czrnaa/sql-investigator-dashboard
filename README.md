# Stock Detective

An e-commerce inventory investigation dashboard built with DuckDB, SQL, Python, and Streamlit.

## Business problem

E-commerce teams need to balance revenue growth with inventory efficiency. This dashboard identifies products that may require restocking, pricing review, or overstock investigation.

## Questions answered

- Which categories generate the most revenue?
- Which products may be at risk of stockout?
- Which products may have excess inventory?
- Which products have estimated margin risk?
- How reliable is the evidence behind each recommendation?

## Tech stack

- DuckDB for local analytical SQL
- Python for data preparation
- Streamlit for the interactive dashboard
- Pandas and PyArrow for data handling

## Data

The real transaction data comes from the Brazilian E-Commerce Public Dataset by Olist.

The source data contains approximately 100,000 orders from 2016–2018, including products, sellers, payments, freight, delivery information, and reviews.

Inventory, supplier lead time, unit cost, and stock levels are simulated because the source dataset does not include operational inventory records.

## Method

1. Loaded raw CSV files into DuckDB.
2. Joined orders and order-item data.
3. Created a product-level demand table.
4. Added reproducible synthetic inventory assumptions.
5. Calculated stockout, overstock, and margin-risk flags.
6. Added demand-confidence labels.
7. Displayed prioritized actions in Streamlit.

## Important limitations

- Inventory values are simulated, not observed.
- Estimated margin is based on an assumed cost ratio.
- The dashboard identifies investigation leads; it does not replace a production forecasting system.
- Products with fewer than three observed units sold are labeled low confidence.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py