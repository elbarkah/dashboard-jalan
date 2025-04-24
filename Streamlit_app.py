import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import BytesIO
import sqlite3

st.set_page_config(page_title="Dashboard Jalan Desa Jawa Barat", layout="wide")

# ===================== KONEKSI DATABASE =====================
@st.cache_resource(ttl=3600)
def get_connection():
    return sqlite3.connect("jalan_desa.db")

# ===================== LOAD DATA =====================
@st.cache_data(ttl=3600)
def load_data():
    conn = get_connection()
    query = """
    SELECT * FROM data_jalan
    """
    df = pd.read_sql_query(query, conn)
    return df

df = load_data()
if df.empty:
    st.warning("⚠️ Data kosong atau tidak valid.")
    st.stop()

# ===================== CACHING FUNGSI =====================
@st.cache_data(ttl=1800)
def hitung_statistik(df):
    return (
        int(df['BAIK (meter)'].sum()),
        int(df['RUSAK RINGAN (meter)'].sum()),
        int(df['RUSAK SEDANG (meter)'].sum()),
        int(df['RUSAK BERAT (meter)'].sum()),
        df['KABUPATEN'].count()
    )

@st.cache_data(ttl=1800)
def get_summary(df, grouping, cols):
    return df.groupby(grouping)[cols].sum()

# ===================== FILTER =====================
st.title("🛣️ Dashboard Kondisi Jalan Desa - Provinsi Jawa Barat")
st.markdown("Analisis visual interaktif kondisi jalan desa.")

st.markdown("### 🔍 Filter Data")
col1, col2, col3, col4 = st.columns(4)

# Pilih Kabupaten
with col1:
    selected_kab = st.selectbox("📍 Kabupaten", ["Semua"] + sorted(df['KABUPATEN'].dropna().unique()))

# Filter kecamatan berdasarkan kabupaten yang dipilih
with col2:
    if selected_kab == "Semua":
    # Jika "Semua" dipilih, tampilkan "Semua" dan semua kecamatan yang sudah di-sort
        kecamatan_options = ["Semua"] + sorted(df['KECAMATAN'].dropna().unique())
    else:
    # Jika kabupaten dipilih, tampilkan "Semua" dan kecamatan yang sesuai dengan kabupaten tersebut
        kecamatan_options = ["Semua"] + sorted(df[df['KABUPATEN'] == selected_kab]['KECAMATAN'].dropna().unique())

    selected_kec = st.selectbox("🏙️ Kecamatan", kecamatan_options)

# Filter desa berdasarkan kecamatan yang dipilih
with col3:
    if selected_kec == "Semua":
    # Jika "Semua" dipilih, tampilkan "Semua" dan semua desa yang sudah di-sort
        desa_options = ["Semua"] + sorted(df['DESA'].dropna().unique())
    else:
    # Jika kecamatan dipilih, tampilkan "Semua" dan desa yang sesuai dengan kecamatan tersebut
        desa_options = ["Semua"] + sorted(df[df['KECAMATAN'] == selected_kec]['DESA'].dropna().unique())

    selected_desa = st.selectbox("🏘️ Desa", desa_options)
with col4:
    selected_perkerasan = st.selectbox("🚧 Jenis Perkerasan", ["Semua"] + sorted(df['JENIS PERKERASAN'].dropna().unique()))

# Terapkan filter
filtered_df = df.copy()
if selected_kab != "Semua":
    filtered_df = filtered_df[filtered_df['KABUPATEN'] == selected_kab]
if selected_kec != "Semua":
    filtered_df = filtered_df[filtered_df['KECAMATAN'] == selected_kec]
if selected_desa != "Semua":
    filtered_df = filtered_df[filtered_df['DESA'] == selected_desa]
if selected_perkerasan != "Semua":
    filtered_df = filtered_df[filtered_df['JENIS PERKERASAN'] == selected_perkerasan]

# ===================== RINGKASAN =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Ringkasan", "📈 Grafik", "💰 Estimasi Biaya", "🗺️ Peta", "📄 Data Mentah"])

with tab1:
    st.subheader("📊 Statistik Kondisi Jalan")
    total_baik, rusak_ringan, rusak_sedang, rusak_berat, total_ruas = hitung_statistik(filtered_df)
    total_rusak = rusak_ringan + rusak_sedang + rusak_berat
    total_jalan = total_baik + total_rusak
    
    def get_persen(x):
        return (x / total_jalan * 100) if total_jalan else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("✅ Baik", f"{total_baik:,} m", f"{get_persen(total_baik):.1f}%")
    col2.metric("⚠️ Rusak Ringan", f"{rusak_ringan:,} m", f"{get_persen(rusak_ringan):.1f}%")
    col3.metric("⚠️ Rusak Sedang", f"{rusak_sedang:,} m", f"{get_persen(rusak_sedang):.1f}%")
    col4.metric("❌ Rusak Berat", f"{rusak_berat:,} m", f"{get_persen(rusak_berat):.1f}%")

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
    - Total ruas jalan: <b>{total_ruas:,} ruas jalan</b><br>
    - Total panjang jalan: <b>{total_jalan:,} m</b><br>
    - Dalam kondisi baik: <b>{total_baik:,} m</b> ({get_persen(total_baik):.1f}%)<br>
    - Mengalami kerusakan: <b>{total_rusak:,} m</b> ({100 - get_persen(total_baik):.1f}%)
    </div>
    """, unsafe_allow_html=True)

# ===================== GRAFIK =====================
with tab2:
    st.subheader("📈 Grafik Kondisi Jalan")
    agg_cols = ['BAIK (meter)', 'RUSAK RINGAN (meter)', 'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)']
    grouping = 'KABUPATEN'
    if selected_desa != "Semua":
        grouping = 'NAMA RUAS JALAN DESA'
    elif selected_kec != "Semua":
        grouping = 'DESA'
    elif selected_kab != "Semua":
        grouping = 'KECAMATAN'

    summary = get_summary(filtered_df, grouping, agg_cols)
    fig = px.bar(summary, x=summary.index, y=agg_cols, barmode='stack', title=f"Kondisi Jalan per {grouping}")
    st.plotly_chart(fig, use_container_width=True)

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

# ===================== ESTIMASI BIAYA =====================
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

# ===================== PETA =====================
def render_peta(df_map):
    st.subheader("🗺️ Peta Jalan Desa")
    map_df = df_map.dropna(subset=['LAT AWAL', 'LNG AWAL', 'LAT AKHIR', 'LNG AKHIR'])
    if not map_df.empty:
        m = folium.Map(location=[map_df['LAT AWAL'].mean(), map_df['LNG AWAL'].mean()], zoom_start=10)
        for _, row in map_df.iterrows():
            google_maps_directions = f"https://www.google.com/maps/dir/{'LAT AWAL'},{'LNG AWAL'}/{'LAT AKHIR'},{'LNG AKHIR'}"
            folium.PolyLine([(row['LAT AWAL'], row['LNG AWAL']), (row['LAT AKHIR'], row['LNG AKHIR'])], color="red",
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

# Render peta
with tab4:
    render_peta(filtered_df)

# ===================== DATA MENTAH =====================
with tab5:
    st.subheader("📄 Data Mentah")
    st.dataframe(filtered_df, use_container_width=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, sheet_name='Data Jalan Desa', index=False)
    output.seek(0)
    st.download_button("📥 Download Data (Excel)", output, file_name="data_jalan_desa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")