import duckdb
import streamlit as st

st.set_page_config(
    page_title="Stock Detective",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Stock Detective")
st.caption("An e-commerce inventory investigation dashboard")

database = duckdb.connect(
    "data/processed/stock_detective.duckdb",
    read_only=True,
)

summary = database.execute("""
    SELECT
        COUNT(*) AS products,
        ROUND(SUM(gross_revenue), 2) AS revenue,
        ROUND(SUM(inventory_value), 2) AS inventory_value,
        COUNT(*) FILTER (
            WHERE recommended_action = 'Restock soon'
        ) AS restock_cases,
        COUNT(*) FILTER (
            WHERE recommended_action = 'Investigate overstock'
        ) AS overstock_cases
    FROM product_action_queue
""").fetchone()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Products", f"{summary[0]:,}")
col2.metric("Gross revenue", f"{summary[1]:,.2f}")
col3.metric("Inventory value", f"{summary[2]:,.2f}")
col4.metric("Restock cases", f"{summary[3]:,}")

# revenue by product
st.subheader("💰 Revenue by category")

category_revenue = database.execute("""
    SELECT
        category,
        ROUND(SUM(gross_revenue), 2) AS revenue
    FROM product_action_queue
    WHERE category <> 'unknown'
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT 10
""").fetchdf()

st.bar_chart(
    category_revenue.set_index("category"),
    y="revenue",
)

# evidence confidence
st.subheader("📚 Evidence confidence")

confidence_summary = database.execute("""
    SELECT
        demand_confidence,
        COUNT(*) AS product_count
    FROM product_action_queue
    GROUP BY demand_confidence
    ORDER BY
        CASE demand_confidence
            WHEN 'High confidence' THEN 1
            WHEN 'Medium confidence' THEN 2
            WHEN 'Low confidence' THEN 3
        END
""").fetchdf()

st.bar_chart(
    confidence_summary.set_index("demand_confidence"),
    y="product_count",
)

st.caption(
    "Low-confidence products have fewer than 3 observed units sold. "
    "Treat their recommendations as investigation leads, not final decisions."
)

# action-summary chart
st.subheader("📊 Cases by recommended action")

action_summary = database.execute("""
    SELECT
        recommended_action,
        COUNT(*) AS product_count
    FROM product_action_queue
    GROUP BY recommended_action
    ORDER BY product_count DESC
""").fetchdf()

st.bar_chart(
    action_summary.set_index("recommended_action"),
    y="product_count",
)

# investigation queue
st.subheader("Investigation status")
st.write(
    f"The dashboard found {summary[4]:,} products requiring "
    "an overstock investigation."
)

st.subheader("🔎 Investigation queue")

action_filter = st.multiselect(
    "Show recommended actions",
    options=[
        "Restock soon",
        "Restock carefully and review margin",
        "Discount or reprice",
        "Investigate overstock",
        "Review pricing",
        "Monitor",
    ],
    default=[
        "Restock soon",
        "Restock carefully and review margin",
        "Discount or reprice",
        "Investigate overstock",
        "Review pricing",
    ],
)

action_queue = database.execute("""
    SELECT
        product_id,
        category,
        units_sold,
        ROUND(gross_revenue, 2) AS revenue,
        ROUND(estimated_margin_rate * 100, 1) AS margin_percent,
        current_stock,
        reorder_point,
        ROUND(inventory_value, 2) AS inventory_value,
        recommended_action,
        demand_confidence,
        priority_score
    FROM product_action_queue
    WHERE recommended_action IN (SELECT UNNEST(?))
    ORDER BY priority_score DESC, inventory_value DESC
    LIMIT 100
""", [action_filter]).fetchdf()

st.dataframe(
    action_queue,
    use_container_width=True,
    hide_index=True,
)

database.close()