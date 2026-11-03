import duckdb
import streamlit as st


st.set_page_config(
    page_title="Stock Detective",
    page_icon="🔎",
    layout="wide",
)


@st.cache_resource
def get_database():
    return duckdb.connect(
        "data/processed/stock_detective.duckdb",
        read_only=True,
    )


database = get_database()


# -----------------------------
# Page title
# -----------------------------

st.title("🔎 Stock Detective")
st.caption(
    "An e-commerce inventory investigation dashboard "
    "for profitable omnichannel decisions."
)


# -----------------------------
# KPI summary
# -----------------------------

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

col1.metric(
    "Products",
    f"{summary[0]:,}",
)

col2.metric(
    "Gross revenue",
    f"{summary[1]:,.2f}",
)

col3.metric(
    "Inventory value",
    f"{summary[2]:,.2f}",
)

col4.metric(
    "Restock cases",
    f"{summary[3]:,}",
)


# -----------------------------
# Business insight
# -----------------------------

st.info(
    f"🔎 The dashboard found {summary[4]:,} products requiring "
    "an overstock investigation. Review low-confidence cases carefully "
    "before taking action."
)


# -----------------------------
# Revenue by category
# -----------------------------

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

category_revenue["category"] = (
    category_revenue["category"]
    .str.replace("_", " ", regex=False)
    .str.title()
)

category_chart = category_revenue.set_index("category")

st.bar_chart(
    category_chart,
    y="revenue",
)


# -----------------------------
# Evidence confidence
# -----------------------------

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

confidence_chart = confidence_summary.set_index(
    "demand_confidence"
)[["product_count"]]

st.bar_chart(confidence_chart)

st.caption(
    "Low-confidence products have fewer than 3 observed units sold. "
    "Treat their recommendations as investigation leads, not final decisions."
)


# -----------------------------
# Recommended action summary
# -----------------------------

st.subheader("📊 Cases by recommended action")

action_summary = database.execute("""
    SELECT
        recommended_action,
        COUNT(*) AS product_count
    FROM product_action_queue
    GROUP BY recommended_action
    ORDER BY product_count DESC
""").fetchdf()

action_chart = action_summary.set_index(
    "recommended_action"
)[["product_count"]]

st.bar_chart(action_chart)


# -----------------------------
# Investigation queue
# -----------------------------

st.subheader("🔎 Investigation queue")

action_options = [
    "Restock soon",
    "Restock carefully and review margin",
    "Discount or reprice",
    "Investigate overstock",
    "Review pricing",
    "Monitor",
]

action_filter = st.multiselect(
    "Show recommended actions",
    options=action_options,
    default=[
        "Restock soon",
        "Restock carefully and review margin",
        "Discount or reprice",
        "Investigate overstock",
        "Review pricing",
    ],
)


if action_filter:
    action_queue = database.execute("""
        SELECT
            product_id,
            category,
            units_sold,
            ROUND(gross_revenue, 2) AS revenue,
            ROUND(estimated_margin_rate * 100, 1)
                AS margin_percent,
            current_stock,
            reorder_point,
            ROUND(inventory_value, 2)
                AS inventory_value,
            recommended_action,
            demand_confidence,
            priority_score
        FROM product_action_queue
        WHERE recommended_action IN (
            SELECT UNNEST(?)
        )
        ORDER BY
            priority_score DESC,
            inventory_value DESC
        LIMIT 100
    """, [action_filter]).fetchdf()

    action_queue["category"] = (
        action_queue["category"]
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    st.dataframe(
        action_queue,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.warning(
        "Select at least one recommended action "
        "to display investigation cases."
    )


# -----------------------------
# Methodology
# -----------------------------

with st.expander("About this dashboard"):
    st.markdown("""
    **Data source:** Brazilian E-Commerce Public Dataset by Olist.

    **Real data:** Orders, products, sellers, payments, freight,
    delivery dates, and reviews.

    **Simulated data:** Inventory levels, supplier lead times,
    unit costs, reorder points, and inventory value.

    **Important limitation:** The recommendations are investigation
    leads, not production inventory decisions. Products with limited
    sales history are explicitly labeled as low confidence.
    """)