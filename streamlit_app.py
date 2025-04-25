import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import BytesIO
import sqlite3

st.set_page_config(page_title="Dashboard Jalan Desa Jawa Barat", layout="wide")

# ===================== KONEKSI DATABASE =====================
def get_connection():
    return sqlite3.connect("jalan_desa.db")

# ===================== LOAD DATA =====================
@st.cache_data(ttl=3600)
def load_data():
    conn = get_connection()
    query = "SELECT * FROM data_jalan"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ===================== RENDER PETA =====================
def render_peta(df_map):
    map_df = df_map.dropna(subset=['LAT AWAL', 'LNG AWAL', 'LAT AKHIR', 'LNG AKHIR'])
    if not map_df.empty:
        m = folium.Map(location=[map_df['LAT AWAL'].mean(), map_df['LNG AWAL'].mean()], zoom_start=10)
        for _, row in map_df.iterrows():
            directions = f"https://www.google.com/maps/dir/{row['LAT AWAL']},{row['LNG AWAL']}/{row['LAT AKHIR']},{row['LNG AKHIR']}"
            folium.PolyLine([(row['LAT AWAL'], row['LNG AWAL']), (row['LAT AKHIR'], row['LNG AKHIR'])], color="red",
                popup=folium.Popup(f"""
                    <b>Desa:</b> {row.get('DESA', '')}<br>
                    <b>Ruas:</b> {row.get('NAMA RUAS JALAN DESA', '')}<br>
                    <b>Perkerasan:</b> {row.get('JENIS PERKERASAN', '')}<br>
                    <b>Panjang:</b> {row.get('TOTAL PANJANG JALAN (meter)', '')} m<br>
                    <a href="{directions}" target="_blank">🛣️ Lihat Rute di Google Maps</a>
                """, max_width=250)
            ).add_to(m)
        st_folium(m, use_container_width=True)
    else:
        st.info("Tidak ada data koordinat untuk ditampilkan.")

# ===================== FILTER FUNCTION =====================
def load_filtered_data(selected_kab, selected_kec, selected_desa, selected_perkerasan):
    conn = get_connection()
    query = "SELECT * FROM data_jalan WHERE 1=1"
    if selected_kab != "Semua":
        query += f" AND KABUPATEN = '{selected_kab}'"
    if selected_kec != "Semua":
        query += f" AND KECAMATAN = '{selected_kec}'"
    if selected_desa != "Semua":
        query += f" AND DESA = '{selected_desa}'"
    if selected_perkerasan != "Semua":
        query += f" AND JENIS_PERKERASAN = '{selected_perkerasan}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ===================== INISIALISASI =====================
df = load_data()
if df.empty:
    st.warning("⚠️ Data kosong atau tidak valid.")
    st.stop()

# ===================== FILTER UI =====================
st.title("🛣️ Dashboard Kondisi Jalan Desa - Provinsi Jawa Barat")
st.markdown("Analisis visual interaktif kondisi jalan desa.")

st.markdown("### 🔍 Filter Data")
col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_kab = st.selectbox("📍 Kabupaten", ["Semua"] + sorted(df['KABUPATEN'].dropna().unique()), key="kabupaten")
with col2:
    kec_options = df[df['KABUPATEN'] == selected_kab]['KECAMATAN'].dropna().unique() if selected_kab != "Semua" else df['KECAMATAN'].dropna().unique()
    selected_kec = st.selectbox("🏙️ Kecamatan", ["Semua"] + sorted(kec_options), key="kecamatan")
with col3:
    desa_options = df[df['KECAMATAN'] == selected_kec]['DESA'].dropna().unique() if selected_kec != "Semua" else df['DESA'].dropna().unique()
    selected_desa = st.selectbox("🏘️ Desa", ["Semua"] + sorted(desa_options), key="desa")
with col4:
    selected_perkerasan = st.selectbox("🚧 Jenis Perkerasan", ["Semua"] + sorted(df['JENIS PERKERASAN'].dropna().unique()), key="perkerasan")

# Tombol tampilkan data
if st.button("Tampilkan Data"):
    st.session_state['show_data'] = True
    st.session_state['filtered_df'] = load_filtered_data(selected_kab, selected_kec, selected_desa, selected_perkerasan)

# ===================== TAMPILKAN HASIL JIKA SUDAH DIPENCET =====================
if st.session_state.get("show_data") and st.session_state.get("filtered_df") is not None:
    filtered_df = st.session_state['filtered_df']

    if filtered_df.empty:
        st.warning("⚠️ Tidak ada data yang ditemukan dengan filter yang dipilih.")
    else:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Ringkasan", "📈 Grafik", "💰 Estimasi Biaya", "🗺️ Peta", "📄 Data Mentah"])

        with tab1:
            st.subheader("📊 Statistik Kondisi Jalan")
            total_baik = int(filtered_df['BAIK (meter)'].sum())
            rusak_ringan = int(filtered_df['RUSAK RINGAN (meter)'].sum())
            rusak_sedang = int(filtered_df['RUSAK SEDANG (meter)'].sum())
            rusak_berat = int(filtered_df['RUSAK BERAT (meter)'].sum())
            total_ruas = filtered_df['KABUPATEN'].count()
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
            if not df_rb.empty:
                max_rb = df_rb.loc[df_rb['RUSAK BERAT (meter)'].idxmax()]
                st.markdown(f"""
                <div style='font-size:20px;'>
                <b>DESKRIPSI UMUM:</b><br>
                - Total ruas jalan: <b>{total_ruas:,} ruas jalan</b><br>
                - Total panjang jalan: <b>{total_jalan:,} m</b><br>
                - Dalam kondisi baik: <b>{total_baik:,} m</b> ({get_persen(total_baik):.1f}%)<br>
                - Mengalami kerusakan: <b>{total_rusak:,} m</b> ({100 - get_persen(total_baik):.1f}%)
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style='font-size:20px;'>
                <br><b>Desa dengan Jalan Rusak Berat terpanjang:</b><br>
                -📍 {max_rb['KABUPATEN']} - {max_rb['KECAMATAN']} - {max_rb['DESA']}<br>
                - Ruas jalan: <b>{max_rb['NAMA RUAS JALAN DESA']}</b><br>
                - Panjang rusak berat: <b>{int(max_rb['RUSAK BERAT (meter)']):,} meter</b>
                </div>
                """, unsafe_allow_html=True)

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
            
            summary = filtered_df.groupby(grouping)[agg_cols].sum()
            fig = px.bar(summary, x=summary.index, y=agg_cols, barmode='stack', title=f"Kondisi Jalan per {grouping}")
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("💰 Estimasi Biaya Perbaikan Jalan")
            harga_aspal = st.number_input("💵 Harga per meter (Aspal)", value=350_000)
            harga_beton = st.number_input("💵 Harga per meter (Beton)", value=850_000)
            harga_paving = st.number_input("💵 Harga per meter (Pavingblock)", value=160_000)

            def biaya_box(label, panjang):
                return f"""
                <div style='padding:15px; border-radius:10px; background:#00ff0080;'>
                    <b>{label}</b><br>
                    Panjang: {panjang:,} m<br>
                    Aspal: Rp {panjang * harga_aspal:,.0f}<br>
                    Beton: Rp {panjang * harga_beton:,.0f}<br>
                    Paving: Rp {panjang * harga_paving:,.0f}
                </div>
                """

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.markdown(biaya_box("⚠️ Rusak Ringan", rusak_ringan), unsafe_allow_html=True)
            with col2: st.markdown(biaya_box("⚠️ Rusak Sedang", rusak_sedang), unsafe_allow_html=True)
            with col3: st.markdown(biaya_box("❌ Rusak Berat", rusak_berat), unsafe_allow_html=True)
            with col4: st.markdown(biaya_box("❌ Total Rusak", total_rusak), unsafe_allow_html=True)

        with tab4:
            st.subheader("🗺️ Peta Jalan Desa")
            render_peta(filtered_df)

        with tab5:
            st.subheader("📄 Data Mentah")
            st.dataframe(filtered_df, use_container_width=True)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, sheet_name='Data Jalan Desa', index=False)
            output.seek(0)
            st.download_button("📥 Download Data (Excel)", output, file_name="data_jalan_desa.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
