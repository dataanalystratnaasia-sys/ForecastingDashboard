import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Forecast Dashboard",
    layout="wide"
)

# =====================================================
# LOAD DATA
# =====================================================

EXCEL_FILE = "forecast_database.xlsx"

@st.cache_data
def load_data():
    historical = pd.read_excel(EXCEL_FILE, sheet_name="HISTORICAL_RAW")
    metadata = pd.read_excel(EXCEL_FILE, sheet_name="METADATA")
    prediction_test = pd.read_excel(EXCEL_FILE, sheet_name="PREDICTION_TEST")
    forecast = pd.read_excel(EXCEL_FILE, sheet_name="FORECAST")
    return historical, metadata, prediction_test, forecast

historical, metadata, prediction_test, forecast = load_data()

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Forecast Dashboard")

brand_list = sorted(historical["Merek"].dropna().unique())
selected_brand = st.sidebar.selectbox("Pilih Brand", brand_list)

kategori_list = sorted(
    historical[historical["Merek"] == selected_brand]["Kategori Barang"].dropna().unique()
)
selected_kategori = st.sidebar.selectbox("Pilih Kategori", kategori_list)

# =====================================================
# FILTER DATA
# =====================================================

hist_row = historical[
    (historical["Merek"] == selected_brand) &
    (historical["Kategori Barang"] == selected_kategori)
]

meta_row = metadata[
    (metadata["MEREK"] == selected_brand) &
    (metadata["KATEGORI"] == selected_kategori)
]

pred_df = prediction_test[
    (prediction_test["MEREK"] == selected_brand) &
    (prediction_test["KATEGORI BARANG"] == selected_kategori)
]

forecast_row = forecast[
    (forecast["MEREK"] == selected_brand) &
    (forecast["KATEGORI BARANG"] == selected_kategori)
]

# =====================================================
# KPI DATA
# =====================================================

week_cols = [c for c in historical.columns if str(c).startswith("Minggu")]

if not hist_row.empty:
    qty_series = hist_row[week_cols].iloc[0].fillna(0).astype(float)
    total_data = len(qty_series)
    total_qty = qty_series.sum()
else:
    total_data = 0
    total_qty = 0

def get_meta(col):
    if meta_row.empty:
        return "-"
    value = meta_row.iloc[0][col]
    if pd.isna(value):
        return "-"
    return value

# =====================================================
# KPI CARDS DI SIDEBAR
# =====================================================

st.sidebar.markdown("---")
st.sidebar.metric("Total Data", total_data)
st.sidebar.metric("Total Qty", f"{int(total_qty):,}")
st.sidebar.metric("Model", get_meta("MODEL"))
st.sidebar.metric("Best Lag", get_meta("Best Lag"))
st.sidebar.markdown("---")
st.sidebar.metric("MAE", get_meta("MAE"))
st.sidebar.metric("RMSE", get_meta("RMSE"))
st.sidebar.metric("MAPE (%)", get_meta("MAPE (%)"))
st.sidebar.metric("Correlation", get_meta("Correlation"))

# =====================================================
# HEADER
# =====================================================

st.title("Forecast Dashboard")
st.markdown(f"### {selected_brand} - {selected_kategori}")

# Keterangan akurasi di bawah header
mape_val = get_meta("MAPE (%)")
if mape_val != "-":
    try:
        mape_num = float(str(mape_val).replace(",", ".").replace("%", ""))
        akurasi = round(100 - mape_num, 2)
        st.info(f"Persentase keakuratan prediksi adalah **{akurasi}%**")
    except ValueError:
        st.info("Prediksi untuk kategori produk ini belum tersedia")
else:
    st.info("Prediksi untuk kategori produk ini belum tersedia")

# =====================================================
# TABS
# =====================================================

tab1, tab2 = st.tabs(["Actual vs Prediksi", "Forecast"])

# =====================================================
# TAB 1
# =====================================================

with tab1:
    st.subheader("Grafik Actual vs Prediksi")

    valid_pred = pred_df.dropna(subset=["AKTUAL", "PREDIKSI"])

    if len(valid_pred) > 0:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=valid_pred["PERIODE TEST"],
            y=valid_pred["AKTUAL"],
            mode="lines+markers",
            name="Aktual"
        ))

        fig.add_trace(go.Scatter(
            x=valid_pred["PERIODE TEST"],
            y=valid_pred["PREDIKSI"],
            mode="lines+markers",
            name="Prediksi"
        ))

        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Belum ada data prediction test.")

    st.subheader("Data Prediction Test")
    st.dataframe(pred_df, use_container_width=True)

# =====================================================
# TAB 2
# =====================================================

with tab2:
    st.subheader("Forecast 12 Minggu Ke Depan")

    if not forecast_row.empty:
        forecast_cols = [c for c in forecast_row.columns if str(c).startswith("F+")]
        forecast_values = forecast_row[forecast_cols].iloc[0]
        valid_forecast = forecast_values.dropna()

        if len(valid_forecast) > 0:
            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
                x=valid_forecast.index,
                y=valid_forecast.values,
                mode="lines+markers",
                name="Forecast"
            ))

            fig2.update_layout(height=500)
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("Belum ada hasil forecast.")

        st.subheader("Tabel Forecast")
        st.dataframe(forecast_row, use_container_width=True)
