"""
app.py
--------
Your Streamlit dashboard. Reads the CSVs and model that pipeline.py
already produced — does NOT connect to SQL Server itself.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import os

st.set_page_config(page_title="Ecommerce Analytics", layout="wide")

# =================================================================
# LOGIN GATE
# =================================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Ecommerce Analytics — Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    login_clicked = st.button("Log in")

    if login_clicked:
        correct_username = st.secrets.get("credentials", {}).get("username", "")
        correct_password = st.secrets.get("credentials", {}).get("password", "")
        if username_input == correct_username and password_input == correct_password:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")

    st.stop()  # nothing below runs until login succeeds

# =================================================================
# LOAD DATA (produced by pipeline.py)
# =================================================================

DATA_DIR = "clean_data"

if not os.path.exists(DATA_DIR):
    st.error("No clean_data/ folder found. Run pipeline.py first.")
    st.stop()

sessions = pd.read_csv(f"{DATA_DIR}/sessions_clean.csv")
sessions["created_at"] = pd.to_datetime(sessions["created_at"])

orders = pd.read_csv(f"{DATA_DIR}/orders_clean.csv")
orders["created_at"] = pd.to_datetime(orders["created_at"])

order_items = pd.read_csv(f"{DATA_DIR}/order_items_clean.csv")
order_items["created_at"] = pd.to_datetime(order_items["created_at"])

products = pd.read_csv(f"{DATA_DIR}/products_clean.csv")

refunds = pd.read_csv(f"{DATA_DIR}/refunds_clean.csv")
refunds["created_at"] = pd.to_datetime(refunds["created_at"])

website_pageviews = pd.read_csv(f"{DATA_DIR}/website_pageviews_clean.csv")

# =================================================================
# SIDEBAR NAVIGATION
# =================================================================

st.sidebar.title("Ecommerce Analytics")
page = st.sidebar.radio("Go to", ["Descriptive", "Diagnostic", "Predictive"])
logout_clicked = st.sidebar.button("Log out")
if logout_clicked:
    st.session_state["logged_in"] = False
    st.rerun()

# =================================================================
# DESCRIPTIVE PAGE
# =================================================================

if page == "Descriptive":
    st.header("Descriptive Analysis")
    st.caption("What happened.")

    total_revenue = order_items['price_usd'].sum()
    total_refund = refunds['refund_amount_usd'].sum()
    net_revenue = total_revenue - total_refund
    total_cogs = order_items['cogs_usd'].sum()
    gross_margin = total_revenue - total_cogs
    gross_margin_pct = gross_margin / total_revenue * 100
    total_orders = orders['order_id'].nunique()
    total_session = sessions['website_session_id'].nunique()
    conversion_rate = total_orders / total_session * 100
    avg_value_order = orders['price_usd'].sum() / total_orders

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Net Revenue", f"${net_revenue:,.2f}")
    col3.metric("Gross Margin %", f"{gross_margin_pct:.1f}%")
    col4.metric("Conversion Rate", f"{conversion_rate:.2f}%")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Total Orders", f"{total_orders:,}")
    col6.metric("Total Sessions", f"{total_session:,}")
    col7.metric("Avg Order Value", f"${avg_value_order:.2f}")
    col8.metric("Total Refunds", f"${total_refund:,.2f}")

    st.divider()

    # Monthly revenue trend
    order_items['months'] = order_items['created_at'].dt.to_period('M').astype(str)
    monthly_revenue = order_items.groupby('months')['price_usd'].sum().reset_index()
    monthly_revenue = monthly_revenue.sort_values('months')

    st.subheader("Monthly Revenue")
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(monthly_revenue['months'], monthly_revenue['price_usd'], marker='o')
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Revenue (USD)")
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    st.divider()

    # Revenue by source
    merged = sessions[['website_session_id', 'utm_source']].merge(
        orders[['order_id', 'website_session_id']], on='website_session_id'
    ).merge(order_items[['order_id', 'price_usd']], on='order_id')
    revenue_by_source = merged.groupby('utm_source').agg(
        orders=('order_id', 'nunique'), revenue=('price_usd', 'sum')
    ).reset_index().sort_values('revenue', ascending=False)

    st.subheader("Revenue by Source")
    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.bar(revenue_by_source['utm_source'], revenue_by_source['revenue'], color='orange')
    ax2.set_xlabel("Source")
    ax2.set_ylabel("Revenue")
    st.pyplot(fig2)

    top_source = revenue_by_source.iloc[0]
    st.markdown(f"**Insight:** {top_source['utm_source']} brings in the most revenue "
                f"(${top_source['revenue']:.2f} from {top_source['orders']} orders).")

    st.divider()

    # Revenue by device
    merged2 = sessions[['website_session_id', 'device_type']].merge(
        orders[['order_id', 'website_session_id']], on='website_session_id'
    ).merge(order_items[['order_id', 'price_usd']], on='order_id')
    revenue_by_device = merged2.groupby('device_type').agg(
        orders=('order_id', 'nunique'), revenue=('price_usd', 'sum')
    ).reset_index().sort_values('revenue', ascending=False)

    st.subheader("Revenue by Device")
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.bar(revenue_by_device['device_type'], revenue_by_device['revenue'], color='pink')
    ax3.set_xlabel("Device")
    ax3.set_ylabel("Revenue")
    st.pyplot(fig3)

    st.divider()

    # Top products
    merged3 = order_items.merge(products, on='product_id')
    top_products = merged3.groupby('product_name').agg(
        units_sold=('order_item_id', 'nunique'), revenue=('price_usd', 'sum')
    ).reset_index().sort_values('revenue', ascending=False)

    st.subheader("Top Products")
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    ax4.bar(top_products['product_name'], top_products['revenue'], color='darkorange')
    ax4.set_xlabel("Product")
    ax4.set_ylabel("Revenue")
    st.pyplot(fig4)

    best_product = top_products.iloc[0]
    st.markdown(f"**Insight:** {best_product['product_name']} is the top seller "
                f"(${best_product['revenue']:.2f} from {best_product['units_sold']} units).")

# =================================================================
# DIAGNOSTIC PAGE
# =================================================================

elif page == "Diagnostic":
    st.header("Diagnostic Analysis")
    st.caption("Why it happened.")

    merged_grp = sessions.merge(orders[['order_id', 'website_session_id']], on='website_session_id', how='left')

    # Conversion by source
    conversion_by_source = merged_grp.groupby('utm_source').agg(
        sessions=('website_session_id', 'nunique'), orders=('order_id', 'nunique')
    ).reset_index()
    conversion_by_source['conversion_rate_pct'] = (
        conversion_by_source['orders'] / conversion_by_source['sessions'] * 100
    ).round(2)
    conversion_by_source = conversion_by_source.sort_values('conversion_rate_pct', ascending=False)

    st.subheader("Conversion Rate by Source")
    fig5, ax5 = plt.subplots(figsize=(7, 4))
    ax5.bar(conversion_by_source['utm_source'], conversion_by_source['conversion_rate_pct'], color='steelblue')
    ax5.set_xlabel("Source")
    ax5.set_ylabel("Conversion Rate (%)")
    st.pyplot(fig5)

    st.divider()

    # Conversion by device
    conversion_by_device = merged_grp.groupby('device_type').agg(
        sessions=('website_session_id', 'nunique'), orders=('order_id', 'nunique')
    ).reset_index()
    conversion_by_device['conversion_rate_pct'] = (
        conversion_by_device['orders'] / conversion_by_device['sessions'] * 100
    ).round(2)
    conversion_by_device = conversion_by_device.sort_values('conversion_rate_pct', ascending=False)

    st.subheader("Conversion Rate by Device")
    fig6, ax6 = plt.subplots(figsize=(6, 4))
    ax6.bar(conversion_by_device['device_type'], conversion_by_device['conversion_rate_pct'], color='seagreen')
    ax6.set_xlabel("Device")
    ax6.set_ylabel("Conversion Rate (%)")
    st.pyplot(fig6)

    st.divider()

    # Refund rate by product
    items_with_product = order_items.merge(products, on='product_id')
    items_with_refund = items_with_product.merge(
        refunds[['order_item_id', 'refund_amount_usd']], on='order_item_id', how='left'
    )
    items_with_refund['was_refunded'] = items_with_refund['refund_amount_usd'].notna()
    refund_rate_by_product = items_with_refund.groupby('product_name').agg(
        units_sold=('order_item_id', 'nunique'), units_refunded=('was_refunded', 'sum')
    ).reset_index()
    refund_rate_by_product['refund_rate_pct'] = (
        refund_rate_by_product['units_refunded'] / refund_rate_by_product['units_sold'] * 100
    ).round(2)
    refund_rate_by_product = refund_rate_by_product.sort_values('refund_rate_pct', ascending=False)

    st.subheader("Refund Rate by Product")
    fig7, ax7 = plt.subplots(figsize=(7, 4))
    ax7.bar(refund_rate_by_product['product_name'], refund_rate_by_product['refund_rate_pct'], color='firebrick')
    ax7.set_xlabel("Product")
    ax7.set_ylabel("Refund Rate (%)")
    st.pyplot(fig7)

    st.divider()

    # Funnel drop-off
    total_session_f = sessions['website_session_id'].nunique()
    sessions_with_pageview = website_pageviews['website_session_id'].nunique()
    sessions_with_order = orders['website_session_id'].nunique()
    funnel = pd.DataFrame({
        'stage': ["Landed", "Viewed page", "Placed order"],
        'sessions': [total_session_f, sessions_with_pageview, sessions_with_order],
    })

    st.subheader("Funnel Drop-off")
    fig8, ax8 = plt.subplots(figsize=(6, 4))
    ax8.bar(funnel['stage'], funnel['sessions'], color='teal')
    ax8.set_xlabel("Stage")
    ax8.set_ylabel("Sessions")
    st.pyplot(fig8)

    st.divider()

    # Correlation
    numeric_cols = ['items_purchased', 'price_usd', 'cogs_usd']
    correlation = orders[numeric_cols].corr().round(3)

    st.subheader("Correlation")
    fig9, ax9 = plt.subplots(figsize=(5, 4))
    im = ax9.imshow(correlation, cmap='coolwarm', vmin=-1, vmax=1)
    ax9.set_xticks(range(len(numeric_cols)))
    ax9.set_xticklabels(numeric_cols, rotation=45)
    ax9.set_yticks(range(len(numeric_cols)))
    ax9.set_yticklabels(numeric_cols)
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            ax9.text(j, i, correlation.iloc[i, j], ha='center', va='center', color='black')
    fig9.colorbar(im, label='Correlation')
    st.pyplot(fig9)

# =================================================================
# PREDICTIVE PAGE
# =================================================================

elif page == "Predictive":
    st.header("Predictive Analysis")
    st.caption("Will this kind of session convert into an order?")

    model_path = "conversion_model.pkl"
    if not os.path.exists(model_path):
        st.error("No conversion_model.pkl found. Run pipeline.py first.")
        st.stop()

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    st.subheader("Predict Session Conversion")

    source_options = sorted(sessions['utm_source'].dropna().unique().tolist())
    device_options = sorted(sessions['device_type'].dropna().unique().tolist())
    campaign_options = sorted(sessions['utm_campaign'].dropna().unique().tolist())

    utm_source_input = st.selectbox("Traffic Source", source_options)
    device_type_input = st.selectbox("Device", device_options)
    utm_campaign_input = st.selectbox("Campaign", campaign_options)
    is_repeat_input = st.radio("Visitor Type", ["New", "Repeat"])
    is_repeat_value = 1 if is_repeat_input == "Repeat" else 0

    predict_clicked = st.button("Predict")

    if predict_clicked:
        input_row = pd.DataFrame([{
            "utm_source": utm_source_input,
            "utm_campaign": utm_campaign_input,
            "device_type": device_type_input,
            "is_repeat_session": is_repeat_value,
        }])
        predicted_class = model.predict(input_row)[0]
        predicted_proba = model.predict_proba(input_row)[0][1]

        st.metric("Predicted Conversion Probability", f"{predicted_proba * 100:.1f}%")
        if predicted_class == 1:
            st.success("This session profile is predicted to CONVERT.")
        else:
            st.warning("This session profile is predicted NOT to convert.")