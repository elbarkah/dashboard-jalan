import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import BytesIO
import os

st.set_page_config(page_title="Dashboard Jalan Desa Jawa Barat", layout="wide")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data():
    cols = [
        'KABUPATEN', 'KECAMATAN', 'DESA', 'NAMA RUAS JALAN DESA',
        'JENIS PERKERASAN', 'BAIK (meter)', 'RUSAK RINGAN (meter)',
        'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)',
        'TOTAL PANJANG JALAN (meter)', 'LAT AWAL', 'LNG AWAL',
        'LAT AKHIR', 'LNG AKHIR'
    ]
    if not os.path.exists("DATA_JALAN_DESA.parquet"):
        st.error("❌ File DATA_JALAN_DESA.parquet tidak ditemukan. Pastikan file tersedia di direktori yang sama dengan app.py.")
        return pd.DataFrame(columns=cols)
    try:
        return pd.read_parquet("DATA_JALAN_DESA.parquet").loc[:, cols]
    except Exception as e:
        st.error(f"❌ Gagal membaca file: {e}")
        return pd.DataFrame(columns=cols)

df = load_data()
if df.empty:
    st.warning("⚠️ Data kosong. Silakan pastikan file DATA_JALAN_DESA.parquet valid dan memiliki kolom yang sesuai.")
    st.stop()

@st.cache_data
def hitung_statistik(df):
    total_baik = int(df['BAIK (meter)'].sum())
    rusak_ringan = int(df['RUSAK RINGAN (meter)'].sum())
    rusak_sedang = int(df['RUSAK SEDANG (meter)'].sum())
    rusak_berat = int(df['RUSAK BERAT (meter)'].sum())
    total_ruas = df['KABUPATEN'].count()
    return total_baik, rusak_ringan, rusak_sedang, rusak_berat, total_ruas

@st.cache_data
def get_summary(df, grouping, cols):
    return df.groupby(grouping)[cols].sum()

df = load_data()

# ===================== HEADER =====================
st.title("🛣️ Dashboard Kondisi Jalan Desa - Provinsi Jawa Barat")
st.markdown("Analisis visual interaktif kondisi jalan desa berdasarkan kategori: Baik, Rusak Ringan, Rusak Sedang, dan Rusak Berat.")

# ===================== FILTER =====================
st.markdown("### 🔍 Filter Data")
col1, col2, col3, col4 = st.columns(4)

# Pilih Kabupaten
with col1:
    selected_kab = st.selectbox("📍 Kabupaten", ["Semua"] + sorted(df['KABUPATEN'].dropna().unique()))

# Filter kecamatan berdasarkan kabupaten yang dipilih
with col2:
    if selected_kab == "Semua":
        selected_kec = st.selectbox("🏙️ Kecamatan", ["Semua"] + sorted(df['KECAMATAN'].dropna().unique()))
    else:
        kecamatan_kab = sorted(df[df['KABUPATEN'] == selected_kab]['KECAMATAN'].dropna().unique())
        selected_kec = st.selectbox("🏙️ Kecamatan", ["Semua"] + kecamatan_kab)

# Filter desa berdasarkan kecamatan yang dipilih
with col3:
    if selected_kec == "Semua":
        selected_desa = st.selectbox("🏘️ Desa", ["Semua"] + sorted(df['DESA'].dropna().unique()))
    else:
        desa_kec = sorted(df[df['KECAMATAN'] == selected_kec]['DESA'].dropna().unique())
        selected_desa = st.selectbox("🏘️ Desa", ["Semua"] + desa_kec)

# Pilih Jenis Perkerasan
with col4:
    selected_perkerasan = st.selectbox("🚧 Jenis Perkerasan", ["Semua"] + sorted(df['JENIS PERKERASAN'].dropna().unique()))

# Terapkan filter berdasarkan pilihan yang ada
filtered_df = df.copy()

if selected_kab != "Semua":
    filtered_df = filtered_df[filtered_df['KABUPATEN'] == selected_kab]
if selected_kec != "Semua":
    filtered_df = filtered_df[filtered_df['KECAMATAN'] == selected_kec]
if selected_desa != "Semua":
    filtered_df = filtered_df[filtered_df['DESA'] == selected_desa]
if selected_perkerasan != "Semua":
    filtered_df = filtered_df[filtered_df['JENIS PERKERASAN'] == selected_perkerasan]
    
# ===================== WARNA =====================
warna_tema = {
    "baik": "#5837ed" if st.get_option("theme.base") == "light" else "#65d7db",
    "rr": "#fff3cd" if st.get_option("theme.base") == "light" else "#e8d797",
    "rs": "#ffeeba" if st.get_option("theme.base") == "light" else "#edc547",
    "rb": "#f8d7da" if st.get_option("theme.base") == "light" else "#ed7979"
}

def kondisi_box(label, panjang, persen, warna):
    st.markdown(f"""
    <div style='background-color:{warna}; padding:20px; border-radius:10px; text-align:center;'>
        <div style='font-size:20px;'><b>{label}</b></div>
        <div style='font-size:26px;'><b>{panjang:,} m</b></div>
        <div style='font-size:22px;'>{persen:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# ===================== TABS =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Ringkasan", "📈 Grafik", "💰 Estimasi Biaya", "🗺️ Peta", "📄 Data Mentah"])

# ===================== TAB 1: RINGKASAN =====================
with tab1:
    st.subheader("📊 Statistik Kondisi Jalan")

    total_baik, rusak_ringan, rusak_sedang, rusak_berat, total_ruas = hitung_statistik(filtered_df)
    total_rusak = rusak_ringan + rusak_sedang + rusak_berat
    total_jalan = total_baik + total_rusak
    get_persen = lambda x: (x / total_jalan * 100) if total_jalan else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kondisi_box("✅ Baik", total_baik, get_persen(total_baik), warna_tema['baik'])
    with col2:
        kondisi_box("⚠️ Rusak Ringan", rusak_ringan, get_persen(rusak_ringan), warna_tema['rr'])
    with col3:
        kondisi_box("⚠️ Rusak Sedang", rusak_sedang, get_persen(rusak_sedang), warna_tema['rs'])
    with col4:
        kondisi_box("❌ Rusak Berat", rusak_berat, get_persen(rusak_berat), warna_tema['rb'])

    df_rb = filtered_df.dropna(subset=['RUSAK BERAT (meter)', 'TOTAL PANJANG JALAN (meter)'])
    df_rb = df_rb[df_rb['TOTAL PANJANG JALAN (meter)'] > 0]
    df_rb['PERSENTASE RUSAK BERAT'] = df_rb['RUSAK BERAT (meter)'] / df_rb['TOTAL PANJANG JALAN (meter)'] * 100

    if not df_rb.empty:
        max_rb = df_rb.loc[df_rb['RUSAK BERAT (meter)'].idxmax()]
        st.markdown(f"""
        <div style='font-size:20px;'>
        <br>📍 <b>Desa dengan Jalan Rusak Berat terpanjang:</b><br>
        - Lokasi: <b>{max_rb['KABUPATEN']} - {max_rb['KECAMATAN']} - {max_rb['DESA']}</b><br>
        - Ruas jalan: <b>{max_rb['NAMA RUAS JALAN DESA']}</b><br>
        - Panjang rusak berat: <b>{int(max_rb['RUSAK BERAT (meter)']):,} meter</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:20px;'>
    <br>DESKRIPSI UMUM:<br>
    - Total ruas jalan: <b>{total_ruas:,}</b><br>
    - Total panjang jalan: <b>{total_jalan:,} m</b><br>
    - Dalam kondisi baik: <b>{total_baik:,} m</b> ({get_persen(total_baik):.1f}%)<br>
    - Mengalami kerusakan: <b>{total_rusak:,} m</b> ({100 - get_persen(total_baik):.1f}%)
    </div>
    """, unsafe_allow_html=True)

# ===================== TAB 2: GRAFIK =====================
def render_grafik(df):
    st.subheader("📈 Grafik Kondisi Jalan")
    agg_cols = ['BAIK (meter)', 'RUSAK RINGAN (meter)', 'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)']
    grouping = 'KABUPATEN'
    if selected_desa != "Semua":
        grouping = 'NAMA RUAS JALAN DESA'
    elif selected_kec != "Semua":
        grouping = 'DESA'
    elif selected_kab != "Semua":
        grouping = 'KECAMATAN'

    if grouping in df.columns:
        summary = get_summary(df, grouping, agg_cols)
        fig1 = px.bar(summary, x=summary.index, y=agg_cols, barmode='stack',
                      title=f"Panjang Jalan Berdasarkan Kondisi per {grouping}",
                      labels={'value': 'Panjang (m)', 'index': grouping},
                      template='simple_white',
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

        percent_df = summary.div(summary.sum(axis=1), axis=0) * 100
        fig2 = px.bar(percent_df, x=percent_df.index, y=agg_cols, barmode='stack',
                      title=f"Persentase Kondisi Jalan per {grouping}",
                      labels={'value': 'Persentase (%)', 'index': grouping},
                      template='simple_white',
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    render_grafik(filtered_df)

# ===================== TAB 3: ESTIMASI BIAYA =====================
with tab3:
    st.subheader("💰 Estimasi Biaya Perbaikan Jalan")
    harga_aspal = st.number_input("💵 Harga per meter (Aspal)", value=350_000, step=5000)
    harga_beton = st.number_input("💵 Harga per meter (Beton)", value=850_000, step=5000)
    harga_paving = st.number_input("💵 Harga per meter (Pavingblock)", value=160_000, step=5000)

    def biaya_box(label, panjang, warna):
        return f"""
        <div style='background-color:{warna}; padding:20px; border-radius:12px; margin-bottom:15px;'>
            <div style='font-size:20px; font-weight:600;'>{label}</div>
            <div style='font-size:18px;'>Panjang: <b>{panjang:,} m</b></div>
            <ul style='margin-top:10px; font-size:16px;'>
                <li>Aspal: <b>Rp {panjang * harga_aspal:,.0f}</b></li>
                <li>Beton: <b>Rp {panjang * harga_beton:,.0f}</b></li>
                <li>Pavingblock: <b>Rp {panjang * harga_paving:,.0f}</b></li>
            </ul>
        </div>
        """

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(biaya_box("⚠️ Rusak Ringan", rusak_ringan, warna_tema['rr']), unsafe_allow_html=True)
    with col2:
        st.markdown(biaya_box("⚠️ Rusak Sedang", rusak_sedang, warna_tema['rs']), unsafe_allow_html=True)
    with col3:
        st.markdown(biaya_box("❌ Rusak Berat", rusak_berat, warna_tema['rb']), unsafe_allow_html=True)
    with col4:
        st.markdown(biaya_box("❌ Total Rusak", total_rusak, warna_tema['baik']), unsafe_allow_html=True)

# ===================== TAB 4: PETA =====================
def render_peta(df_map):
    st.subheader("🗺️ Peta Jalan Desa (Garis Koordinat)")
    coord_cols = ['LAT AWAL', 'LNG AWAL', 'LAT AKHIR', 'LNG AKHIR']
    df_map = df_map.dropna(subset=coord_cols)

    if not df_map.empty:
        m = folium.Map(location=[df_map['LAT AWAL'].mean(), df_map['LNG AWAL'].mean()],
                       zoom_start=11, tiles="OpenStreetMap")

        for _, row in df_map.iterrows():
            lat_awal = row['LAT AWAL']
            lng_awal = row['LNG AWAL']
            lat_akhir = row['LAT AKHIR']
            lng_akhir = row['LNG AKHIR']
            google_maps_directions = f"https://www.google.com/maps/dir/{lat_awal},{lng_awal}/{lat_akhir},{lng_akhir}"
            
            folium.PolyLine(
                [(row['LAT AWAL'], row['LNG AWAL']), (row['LAT AKHIR'], row['LNG AKHIR'])],
                color="red", weight=4,
                popup=folium.Popup(f"""
                <b>Desa:</b> {row.get('DESA', '')}<br>
                <b>Ruas:</b> {row.get('NAMA RUAS JALAN DESA', '')}<br>
                <b>Perkerasan:</b> {row.get('JENIS PERKERASAN', '')}<br>
                <b>Panjang:</b> {row.get('TOTAL PANJANG JALAN (meter)', '')} m<br>
                <a href="{google_maps_directions}" target="_blank">🛣️ Lihat Rute di Google Maps</a>
                """, max_width=250)
            ).add_to(m)
        st_folium(m, use_container_width=True)
    else:
        st.info("Tidak ada data koordinat untuk ditampilkan.")

with tab4:
    render_peta(filtered_df)

# ===================== TAB 5: DATA MENTAH =====================
with tab5:
    st.subheader("📄 Data Mentah")
    st.dataframe(filtered_df, use_container_width=True, height=400)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, sheet_name='Data Jalan Desa', index=False)
    output.seek(0)

    st.download_button(
        label="📥 Download Data (Excel)",
        data=output,
        file_name="data_jalan_desa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("📌 Sumber data: DATA_JALAN_DESA.parquet")
