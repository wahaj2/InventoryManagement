# Inventory Sales Dashboard

A Streamlit dashboard for sales analysis and demand forecasting across 20 store locations.

## Setup

```bash
pip install -r requirements.txt
```

Place your `data1.csv` in the same folder as `app.py`, then run:

```bash
streamlit run app.py
```

## Data Cleaning Rules Applied

| Rule | Detail |
|------|--------|
| **Valid Sales** | Only moves where `To` = `Partners/Customers` OR `Virtual Locations/Production` |
| **Excluded Products** | All lottery/scratch ticket items (see list below) |
| **Invalid Moves** | `Virtual Locations/Inventory Adjustment`, Repair, Scrap, Inter-warehouse, etc. are excluded |
| **Store Extraction** | Store code extracted from `From` column (e.g. `MARL/Stock` → `MARL`) |

### Excluded Lottery Products
- $1, $2, $3, $4, $5, $7, $10, $20, $30, $50, $100 Scratch & Win
- Lotto Pay Out
- Online Lotto
- VOID SNW

## Dashboard Pages

### 📊 Overview
- KPI cards: total units, transactions, unique products, active stores, avg daily units
- Daily sales trend with 7-day moving average
- Sales by store category (pie chart)
- Day-of-week distribution
- Weekly trend by store category

### 🏪 Store Analysis
- Bar chart: total units per store
- Transactions per store (horizontal bar)
- Unique products per store
- Monthly sales trend per store
- Full summary table

### 📦 Product Analysis
- Top N products by units sold (adjustable slider)
- Top products by transactions
- Products sold in most stores
- Product drilldown: daily trend + per-store breakdown

### 📈 Forecast
- Model selection: **LightGBM**, **XGBoost**, or **ARIMA**
- Forecast horizon: 7–30 days
- Metrics: MSE, RMSE, Forecast Min, Forecast Max
- Chart: actuals + test predictions + future forecast + ±1 RMSE band
- Forecast table with daily values
- Feature importance (tree models only)

## Forecasting Details

### Feature Engineering (LightGBM / XGBoost)
- Calendar: day of week, day of month, month, week of year
- Lag features: lag-1, lag-7, lag-14
- Rolling means: 7-day, 14-day

### ARIMA
- Order: (1, 1, 1) — suitable for short retail time series
- Iterative multi-step forecast

### Eligible Products for Forecast
- At least 60 days of sales history
- At least 50 total units sold
- Top 15 by total volume are shown

## Store Reference

| Code | Store Name | Category |
|------|-----------|----------|
| 1AIR | Walmart Airdrie | Walmart |
| 1RED | Walmart Red Deer | Walmart |
| 1WBR | Walmart Westbrook Mall | Walmart |
| 1ESC | Walmart South Common Edmonton | Walmart |
| 1SHV | Walmart Shawnessy / Shawville | Walmart |
| 1MAR | Walmart Marlborough Mall | Walmart |
| CHKM | Chinook Centre | Kiosk |
| MKML | Market Mall | Inline |
| TNTM | Pacific Place (T&T) | Kiosk |
| SCRM | Southcentre Mall | Inline |
| CIML | Crossiron Mills | Kiosk |
| BVSQ | Bow Valley Square | Kiosk |
| MARL | Marlborough Mall | Inline |
| FTMC | Fort McMurray Peter Pond Mall | Inline |
| METR | Metropolis at Metrotown Burnaby | Inline |
| CENT | Surrey Central City | Inline |
| GUIL | Guilford Town Centre | Inline |
| PKPL | Park Place Mall | Inline |
| C-WH | Warehouse Beltline | Strip Mall |
