import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Inventory Sales Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

EXCLUDE_PRODUCTS = [
    "$1 Scratch & Win", "$2 Scratch & Win", "$3 Scratch & Win",
    "$4 Scratch & Win", "$5 Scratch & Win", "$7 Scratch & Win",
    "$10 Scratch & Win", "$20 Scratch & Win", "$30 Scratch & Win",
    "$50 Scratch & Win", "$100 Scratch & Win",
    "Lotto Pay Out", "Online Lotto", "VOID SNW"
]

VALID_TO = ["Partners/Customers", "Virtual Locations/Production"]

STORE_MAP = {
    "1AIR": "Walmart Airdrie",
    "1RED": "Walmart Red Deer",
    "1WBR": "Walmart Westbrook Mall",
    "1ESC": "Walmart South Common Edmonton",
    "1SHV": "Walmart Shawnessy / Shawville",
    "1MAR": "Walmart Marlborough Mall",
    "CHKM": "Chinook Centre",
    "MKML": "Market Mall",
    "TNTM": "Pacific Place (T&T)",
    "SCRM": "Southcentre Mall",
    "CIML": "Crossiron Mills",
    "BVSQ": "Bow Valley Square",
    "MARL": "Marlborough Mall",
    "FTMC": "Fort McMurray Peter Pond Mall",
    "METR": "Metropolis at Metrotown Burnaby",
    "CENT": "Surrey Central City",
    "GUIL": "Guilford Town Centre",
    "PKPL": "Park Place Mall",
    "C-WH": "Warehouse Beltline",
}

STORE_CATEGORY = {
    "1AIR": "Walmart", "1RED": "Walmart", "1WBR": "Walmart",
    "1ESC": "Walmart", "1SHV": "Walmart", "1MAR": "Walmart",
    "CHKM": "Kiosk", "TNTM": "Kiosk", "CIML": "Kiosk", "BVSQ": "Kiosk",
    "MKML": "Inline", "SCRM": "Inline", "MARL": "Inline", "FTMC": "Inline",
    "METR": "Inline", "CENT": "Inline", "GUIL": "Inline", "PKPL": "Inline",
    "C-WH": "Strip Mall",
}


# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────

@st.cache_data(show_spinner="Loading and cleaning data…")
def load_data(path="data1.csv"):
    df = pd.read_csv(path)
    df.rename(columns={"Unnamed: 0": "row_id"}, inplace=True)

    # Parse datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df.dropna(subset=["Date"], inplace=True)

    # Keep only real sales: Stock → Partners/Customers or Virtual Locations/Production
    df = df[df["To"].isin(VALID_TO)].copy()

    # Exclude lottery / non-sale products
    df = df[~df["Product"].isin(EXCLUDE_PRODUCTS)].copy()

    # Drop rows with missing product or quantity
    df.dropna(subset=["Product", "Quantity"], inplace=True)
    df = df[df["Quantity"] > 0].copy()

    # Extract store code from "From" column  (e.g. "MARL/Stock" → "MARL")
    df["Store_Code"] = df["From"].str.split("/").str[0]
    df["Store_Name"] = df["Store_Code"].map(STORE_MAP).fillna(df["Store_Code"])
    df["Store_Category"] = df["Store_Code"].map(STORE_CATEGORY).fillna("Other")

    # Date parts
    df["Date_Only"] = df["Date"].dt.date
    df["Week"] = df["Date"].dt.to_period("W").dt.start_time
    df["Month"] = df["Date"].dt.to_period("M").dt.start_time
    df["DayOfWeek"] = df["Date"].dt.day_name()
    df["Hour"] = df["Date"].dt.hour

    return df


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/box.png", width=60)
    st.title("Filters")

    data_path = st.text_input("CSV Path", value="data1.csv")
    df_raw = load_data(data_path)

    date_min = df_raw["Date"].min().date()
    date_max = df_raw["Date"].max().date()

    date_range = st.date_input(
        "Date Range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    store_options = ["All"] + sorted(df_raw["Store_Name"].unique().tolist())
    selected_stores = st.multiselect("Stores", store_options, default=["All"])

    category_options = ["All"] + sorted(df_raw["Store_Category"].unique().tolist())
    selected_category = st.selectbox("Store Category", category_options)

    st.markdown("---")
    st.caption(f"Data: {date_min} → {date_max}")
    st.caption(f"Records after cleaning: {len(df_raw):,}")


# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────

df = df_raw.copy()

if len(date_range) == 2:
    df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]

if "All" not in selected_stores and selected_stores:
    df = df[df["Store_Name"].isin(selected_stores)]

if selected_category != "All":
    df = df[df["Store_Category"] == selected_category]


# ─────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────

pages = ["📊 Overview", "🏪 Store Analysis", "📦 Product Analysis", "📈 Forecast"]
page = st.sidebar.radio("Navigation", pages)


# ═══════════════════════════════════════════════
#  PAGE 1 – OVERVIEW
# ═══════════════════════════════════════════════

if page == "📊 Overview":
    st.title("📊 Sales Overview")

    # KPI cards
    total_qty = df["Quantity"].sum()
    total_txn = len(df)
    unique_products = df["Product"].nunique()
    unique_stores = df["Store_Code"].nunique()
    avg_daily = df.groupby("Date_Only")["Quantity"].sum().mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Units Sold", f"{total_qty:,.0f}")
    c2.metric("Total Transactions", f"{total_txn:,}")
    c3.metric("Unique Products", f"{unique_products:,}")
    c4.metric("Active Stores", f"{unique_stores}")
    c5.metric("Avg Daily Units", f"{avg_daily:,.1f}")

    st.markdown("---")

    # Daily sales trend
    daily = df.groupby("Date_Only").agg(
        Units=("Quantity", "sum"),
        Transactions=("row_id", "count")
    ).reset_index()
    daily["Date_Only"] = pd.to_datetime(daily["Date_Only"])
    daily["7d_MA"] = daily["Units"].rolling(7).mean()

    fig_daily = go.Figure()
    fig_daily.add_trace(go.Bar(x=daily["Date_Only"], y=daily["Units"],
                               name="Daily Units", marker_color="#4C78A8", opacity=0.6))
    fig_daily.add_trace(go.Scatter(x=daily["Date_Only"], y=daily["7d_MA"],
                                   name="7-Day MA", line=dict(color="#E45756", width=2)))
    fig_daily.update_layout(title="Daily Units Sold (with 7-Day Moving Average)",
                            xaxis_title="Date", yaxis_title="Units", legend=dict(x=0, y=1),
                            height=350)
    st.plotly_chart(fig_daily, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Sales by store category
        cat_sales = df.groupby("Store_Category")["Quantity"].sum().reset_index()
        fig_cat = px.pie(cat_sales, names="Store_Category", values="Quantity",
                         title="Units Sold by Store Category",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_cat.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        # Day-of-week distribution
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        dow = df.groupby("DayOfWeek")["Quantity"].sum().reindex(dow_order).reset_index()
        fig_dow = px.bar(dow, x="DayOfWeek", y="Quantity", title="Units Sold by Day of Week",
                         color="Quantity", color_continuous_scale="Blues")
        fig_dow.update_layout(xaxis_title="", yaxis_title="Units", coloraxis_showscale=False)
        st.plotly_chart(fig_dow, use_container_width=True)

    # Weekly trend by store category
    weekly_cat = df.groupby(["Week", "Store_Category"])["Quantity"].sum().reset_index()
    fig_wc = px.line(weekly_cat, x="Week", y="Quantity", color="Store_Category",
                     title="Weekly Sales Trend by Store Category",
                     color_discrete_sequence=px.colors.qualitative.Set1)
    fig_wc.update_layout(height=350, xaxis_title="Week", yaxis_title="Units")
    st.plotly_chart(fig_wc, use_container_width=True)


# ═══════════════════════════════════════════════
#  PAGE 2 – STORE ANALYSIS
# ═══════════════════════════════════════════════

elif page == "🏪 Store Analysis":
    st.title("🏪 Store Analysis")

    # Store summary table
    store_summary = df.groupby(["Store_Code", "Store_Name", "Store_Category"]).agg(
        Total_Units=("Quantity", "sum"),
        Transactions=("row_id", "count"),
        Unique_Products=("Product", "nunique"),
        Avg_Qty_Per_Txn=("Quantity", "mean"),
    ).reset_index().sort_values("Total_Units", ascending=False)

    store_summary["Avg_Qty_Per_Txn"] = store_summary["Avg_Qty_Per_Txn"].round(2)

    # Bar chart
    fig_store = px.bar(
        store_summary, x="Store_Name", y="Total_Units", color="Store_Category",
        title="Total Units Sold per Store", text="Total_Units",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_store.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_store.update_layout(xaxis_tickangle=-45, height=420,
                            xaxis_title="", yaxis_title="Total Units")
    st.plotly_chart(fig_store, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Transactions per store
        fig_txn = px.bar(store_summary.sort_values("Transactions", ascending=True),
                         x="Transactions", y="Store_Name", orientation="h",
                         color="Store_Category", title="Transactions per Store",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_txn.update_layout(height=500, yaxis_title="", xaxis_title="Transactions")
        st.plotly_chart(fig_txn, use_container_width=True)

    with col2:
        # Unique products per store
        fig_up = px.bar(store_summary.sort_values("Unique_Products", ascending=True),
                        x="Unique_Products", y="Store_Name", orientation="h",
                        color="Store_Category", title="Unique Products Sold per Store",
                        color_discrete_sequence=px.colors.qualitative.Set1)
        fig_up.update_layout(height=500, yaxis_title="", xaxis_title="Unique Products")
        st.plotly_chart(fig_up, use_container_width=True)

    # Monthly trend per store
    monthly_store = df.groupby(["Month", "Store_Name"])["Quantity"].sum().reset_index()
    fig_ms = px.line(monthly_store, x="Month", y="Quantity", color="Store_Name",
                     title="Monthly Sales Trend per Store")
    fig_ms.update_layout(height=400)
    st.plotly_chart(fig_ms, use_container_width=True)

    st.markdown("### Store Summary Table")
    st.dataframe(store_summary.reset_index(drop=True), use_container_width=True)


# ═══════════════════════════════════════════════
#  PAGE 3 – PRODUCT ANALYSIS
# ═══════════════════════════════════════════════

elif page == "📦 Product Analysis":
    st.title("📦 Product Analysis")

    top_n = st.slider("Show Top N Products", 10, 50, 20)

    prod_summary = df.groupby("Product").agg(
        Total_Units=("Quantity", "sum"),
        Transactions=("row_id", "count"),
        Avg_Qty_Per_Txn=("Quantity", "mean"),
        Stores=("Store_Code", "nunique"),
        First_Sale=("Date", "min"),
        Last_Sale=("Date", "max"),
    ).reset_index().sort_values("Total_Units", ascending=False)

    prod_summary["Avg_Qty_Per_Txn"] = prod_summary["Avg_Qty_Per_Txn"].round(2)

    top_products = prod_summary.head(top_n)

    fig_prod = px.bar(
        top_products.sort_values("Total_Units"),
        x="Total_Units", y="Product", orientation="h",
        color="Total_Units", color_continuous_scale="Blues",
        title=f"Top {top_n} Products by Units Sold",
        text="Total_Units"
    )
    fig_prod.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_prod.update_layout(height=600, yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig_prod, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Top products by transactions
        fig_t = px.bar(
            top_products.sort_values("Transactions").tail(20),
            x="Transactions", y="Product", orientation="h",
            title="Top Products by Transactions",
            color="Transactions", color_continuous_scale="Greens"
        )
        fig_t.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_t, use_container_width=True)

    with col2:
        # Products sold across most stores
        fig_s = px.bar(
            prod_summary.sort_values("Stores", ascending=False).head(20).sort_values("Stores"),
            x="Stores", y="Product", orientation="h",
            title="Products Sold in Most Stores",
            color="Stores", color_continuous_scale="Oranges"
        )
        fig_s.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_s, use_container_width=True)

    # Product drilldown
    st.markdown("### 🔍 Product Drilldown")
    selected_product = st.selectbox(
        "Select a product",
        options=prod_summary["Product"].tolist()
    )

    prod_df = df[df["Product"] == selected_product].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Units", f"{prod_df['Quantity'].sum():,.0f}")
    c2.metric("Transactions", f"{len(prod_df):,}")
    c3.metric("Stores", f"{prod_df['Store_Code'].nunique()}")

    col1, col2 = st.columns(2)

    with col1:
        # Daily trend for product
        p_daily = prod_df.groupby("Date_Only")["Quantity"].sum().reset_index()
        p_daily["Date_Only"] = pd.to_datetime(p_daily["Date_Only"])
        fig_pd = px.line(p_daily, x="Date_Only", y="Quantity",
                         title=f"Daily Sales: {selected_product}")
        fig_pd.update_layout(height=300)
        st.plotly_chart(fig_pd, use_container_width=True)

    with col2:
        # Store breakdown for product
        p_store = prod_df.groupby("Store_Name")["Quantity"].sum().sort_values(ascending=True).reset_index()
        fig_ps = px.bar(p_store, x="Quantity", y="Store_Name", orientation="h",
                        title=f"Store Breakdown: {selected_product}",
                        color="Quantity", color_continuous_scale="Teal")
        fig_ps.update_layout(height=300, coloraxis_showscale=False)
        st.plotly_chart(fig_ps, use_container_width=True)

    st.markdown("### Product Summary Table")
    st.dataframe(prod_summary.reset_index(drop=True), use_container_width=True)


# ═══════════════════════════════════════════════
#  PAGE 4 – FORECAST
# ═══════════════════════════════════════════════

elif page == "📈 Forecast":
    st.title("📈 Demand Forecast")

    from sklearn.metrics import mean_squared_error
    import lightgbm as lgb
    import xgboost as xgb
    from statsmodels.tsa.arima.model import ARIMA

    st.info(
        "Forecasting daily units sold using **LightGBM**, **XGBoost**, or **ARIMA**. "
        "Only products with sufficient sales history are included."
    )

    # ── Select top 15 forecastable items (exclude lottery already done) ──
    prod_stats = df.groupby("Product").agg(
        total_units=("Quantity", "sum"),
        num_days=("Date_Only", "nunique"),
    ).reset_index()
    # Need at least 60 days of data and 50 units
    forecastable = prod_stats[
        (prod_stats["num_days"] >= 60) & (prod_stats["total_units"] >= 50)
    ].sort_values("total_units", ascending=False).head(15)

    col1, col2, col3 = st.columns(3)
    selected_item = col1.selectbox("Select Product", forecastable["Product"].tolist())
    model_choice = col2.selectbox("Model", ["LightGBM", "XGBoost", "ARIMA"])
    forecast_days = col3.slider("Forecast Days", 7, 30, 14)

    # Build daily time series for selected item
    item_df = df[df["Product"] == selected_item].copy()
    daily_ts = (
        item_df.groupby("Date_Only")["Quantity"]
        .sum()
        .reset_index()
        .rename(columns={"Date_Only": "ds", "Quantity": "y"})
    )
    daily_ts["ds"] = pd.to_datetime(daily_ts["ds"])

    # Fill missing dates with 0
    full_range = pd.date_range(daily_ts["ds"].min(), daily_ts["ds"].max(), freq="D")
    daily_ts = daily_ts.set_index("ds").reindex(full_range, fill_value=0).reset_index()
    daily_ts.columns = ["ds", "y"]

    n = len(daily_ts)
    train_size = int(n * 0.8)
    train = daily_ts.iloc[:train_size]
    test = daily_ts.iloc[train_size:]

    # ── Feature engineering (for tree models) ──
    def make_features(df_in):
        d = df_in.copy()
        d["dayofweek"] = d["ds"].dt.dayofweek
        d["dayofmonth"] = d["ds"].dt.day
        d["month"] = d["ds"].dt.month
        d["weekofyear"] = d["ds"].dt.isocalendar().week.astype(int)
        for lag in [1, 7, 14]:
            d[f"lag_{lag}"] = d["y"].shift(lag)
        for window in [7, 14]:
            d[f"roll_{window}"] = d["y"].shift(1).rolling(window).mean()
        d.dropna(inplace=True)
        return d

    feat_cols = ["dayofweek","dayofmonth","month","weekofyear",
                 "lag_1","lag_7","lag_14","roll_7","roll_14"]

    # ── Train & predict ──
    with st.spinner(f"Training {model_choice}…"):
        try:
            if model_choice in ["LightGBM", "XGBoost"]:
                full_feat = make_features(daily_ts)
                split_idx = full_feat[full_feat["ds"] <= train["ds"].max()].index.max()

                X_train = full_feat.loc[:split_idx, feat_cols]
                y_train = full_feat.loc[:split_idx, "y"]
                X_test  = full_feat.loc[split_idx+1:, feat_cols]
                y_test  = full_feat.loc[split_idx+1:, "y"]
                test_dates = full_feat.loc[split_idx+1:, "ds"]

                if model_choice == "LightGBM":
                    model = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05,
                                               num_leaves=31, random_state=42, verbose=-1)
                else:
                    model = xgb.XGBRegressor(n_estimators=300, learning_rate=0.05,
                                              max_depth=5, random_state=42, verbosity=0)

                model.fit(X_train, y_train)
                test_pred = model.predict(X_test)
                test_pred = np.maximum(test_pred, 0)

                mse = mean_squared_error(y_test, test_pred)
                rmse = np.sqrt(mse)

                # Future forecast (iterative)
                history = daily_ts["y"].tolist()
                future_dates = pd.date_range(daily_ts["ds"].max() + pd.Timedelta(days=1),
                                             periods=forecast_days, freq="D")
                future_preds = []
                for fd in future_dates:
                    row = {
                        "ds": fd,
                        "dayofweek": fd.dayofweek,
                        "dayofmonth": fd.day,
                        "month": fd.month,
                        "weekofyear": fd.isocalendar().week,
                        "lag_1": history[-1],
                        "lag_7": history[-7] if len(history) >= 7 else 0,
                        "lag_14": history[-14] if len(history) >= 14 else 0,
                        "roll_7": np.mean(history[-7:]) if len(history) >= 7 else np.mean(history),
                        "roll_14": np.mean(history[-14:]) if len(history) >= 14 else np.mean(history),
                    }
                    pred = float(model.predict(pd.DataFrame([row])[feat_cols])[0])
                    pred = max(pred, 0)
                    future_preds.append(pred)
                    history.append(pred)

                forecast_df = pd.DataFrame({"ds": future_dates, "yhat": future_preds})

            else:  # ARIMA
                y_train_arr = train["y"].values
                y_test_arr  = test["y"].values

                arima_model = ARIMA(y_train_arr, order=(1, 1, 1))
                arima_fit = arima_model.fit()
                test_pred = arima_fit.forecast(steps=len(y_test_arr))
                test_pred = np.maximum(test_pred, 0)
                test_dates = test["ds"]
                y_test = test["y"]

                mse = mean_squared_error(y_test_arr, test_pred)
                rmse = np.sqrt(mse)

                # Future forecast
                future_preds_arr = arima_fit.forecast(steps=len(y_test_arr) + forecast_days)[-forecast_days:]
                future_preds_arr = np.maximum(future_preds_arr, 0)
                future_dates = pd.date_range(daily_ts["ds"].max() + pd.Timedelta(days=1),
                                             periods=forecast_days, freq="D")
                forecast_df = pd.DataFrame({"ds": future_dates, "yhat": future_preds_arr})

            # ── Metrics ──
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Test MSE", f"{mse:.2f}")
            m2.metric("Test RMSE", f"{rmse:.2f}")
            m3.metric("Forecast Min", f"{forecast_df['yhat'].min():.1f}")
            m4.metric("Forecast Max", f"{forecast_df['yhat'].max():.1f}")

            # ── Chart ──
            fig = go.Figure()

            # Actuals
            fig.add_trace(go.Scatter(
                x=daily_ts["ds"], y=daily_ts["y"],
                mode="lines", name="Actual",
                line=dict(color="#4C78A8", width=1.5)
            ))

            # Test predictions
            fig.add_trace(go.Scatter(
                x=test_dates, y=test_pred,
                mode="lines", name="Test Prediction",
                line=dict(color="#F58518", width=1.5, dash="dot")
            ))

            # Future forecast
            fig.add_trace(go.Scatter(
                x=forecast_df["ds"], y=forecast_df["yhat"],
                mode="lines+markers", name=f"Forecast ({forecast_days}d)",
                line=dict(color="#E45756", width=2),
                marker=dict(size=5)
            ))

            # Confidence band (±1 RMSE)
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df["ds"], forecast_df["ds"][::-1]]),
                y=pd.concat([forecast_df["yhat"] + rmse, (forecast_df["yhat"] - rmse).clip(0)[::-1]]),
                fill="toself", fillcolor="rgba(228,87,86,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="±1 RMSE Band"
            ))

            fig.update_layout(
                title=f"{selected_item} — {model_choice} Forecast",
                xaxis_title="Date", yaxis_title="Daily Units Sold",
                height=480, legend=dict(x=0, y=1),
                shapes=[dict(
                    type="line",
                    x0=daily_ts["ds"].max(), x1=daily_ts["ds"].max(),
                    y0=0, y1=1, yref="paper",
                    line=dict(color="gray", dash="dash", width=1)
                )]
            )
            st.plotly_chart(fig, use_container_width=True)

            # Forecast table
            st.markdown("### Forecast Values")
            fc_display = forecast_df.copy()
            fc_display["yhat"] = fc_display["yhat"].round(2)
            fc_display.columns = ["Date", "Forecasted Units"]
            fc_display["Date"] = fc_display["Date"].dt.strftime("%Y-%m-%d")
            st.dataframe(fc_display, use_container_width=True, hide_index=True)

            # Feature importance (tree models)
            if model_choice in ["LightGBM", "XGBoost"]:
                st.markdown("### Feature Importance")
                importance = pd.DataFrame({
                    "Feature": feat_cols,
                    "Importance": model.feature_importances_
                }).sort_values("Importance", ascending=True)
                fig_fi = px.bar(importance, x="Importance", y="Feature", orientation="h",
                                color="Importance", color_continuous_scale="Viridis",
                                title="Feature Importance")
                fig_fi.update_layout(coloraxis_showscale=False, height=350)
                st.plotly_chart(fig_fi, use_container_width=True)

        except Exception as e:
            st.error(f"Forecasting error: {e}")
            st.exception(e)

    st.markdown("---")
    st.markdown("### All Forecastable Products")
    st.dataframe(forecastable.reset_index(drop=True), use_container_width=True)
