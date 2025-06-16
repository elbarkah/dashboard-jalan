import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from io import BytesIO

st.set_page_config(page_title="Dashboard Jalan Desa Jawa Barat", layout="wide")

# ===================== LOAD DATA =====================
@st.cache_data(ttl=3600)
def load_data():
    return pd.read_excel("DATA JALAN DESA.xlsx")

df = load_data()
if df.empty:
    st.warning("⚠️ Data kosong atau tidak valid.")
    st.stop()

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

# ===================== FILTER UI =====================
st.title("🛣️ Dashboard Kondisi Jalan Desa - Provinsi Jawa Barat")
st.markdown("Analisis visual interaktif kondisi jalan desa.")

st.markdown("### 🔍 Filter Data")
col1, col2, col3, col4 = st.columns(4)
with col1:
    selected_kab = st.selectbox("📍 Kabupaten", ["Semua"] + sorted(df['KABUPATEN'].dropna().unique()))
with col2:
    kec_options = df[df['KABUPATEN'] == selected_kab]['KECAMATAN'].dropna().unique() if selected_kab != "Semua" else df['KECAMATAN'].dropna().unique()
    selected_kec = st.selectbox("🏙️ Kecamatan", ["Semua"] + sorted(kec_options))
with col3:
    desa_options = df[df['KECAMATAN'] == selected_kec]['DESA'].dropna().unique() if selected_kec != "Semua" else df['DESA'].dropna().unique()
    selected_desa = st.selectbox("🏘️ Desa", ["Semua"] + sorted(desa_options))
with col4:
    selected_perkerasan = st.selectbox("🚧 Jenis Perkerasan", ["Semua"] + sorted(df['JENIS PERKERASAN'].dropna().unique()))

def apply_filter(df):
    if selected_kab != "Semua":
        df = df[df["KABUPATEN"] == selected_kab]
    if selected_kec != "Semua":
        df = df[df["KECAMATAN"] == selected_kec]
    if selected_desa != "Semua":
        df = df[df["DESA"] == selected_desa]
    if selected_perkerasan != "Semua":
        df = df[df["JENIS PERKERASAN"] == selected_perkerasan]
    return df

if st.button("Tampilkan Data"):
    st.session_state['filtered_df'] = apply_filter(df)

if "filtered_df" in st.session_state:
    filtered_df = st.session_state['filtered_df']
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Ringkasan", "📈 Grafik", "💰 Estimasi Biaya", "🗺️ Peta", "📄 Data Mentah"])

    with tab1:
        df_metrics = filtered_df.copy().fillna(0)
        
        # Hitungan dasar
        total_ruas = df_metrics[df_metrics['JENIS PERKERASAN'].str.upper() != "TIDAK ADA"].shape[0]
        total_panjang = df_metrics['TOTAL PANJANG JALAN DESA (meter)'].sum()
        total_baik = df_metrics['BAIK (meter)'].sum()
        rusak_ringan = df_metrics['RUSAK RINGAN (meter)'].sum()
        rusak_sedang = df_metrics['RUSAK SEDANG (meter)'].sum()
        rusak_berat = df_metrics['RUSAK BERAT (meter)'].sum()
        total_rusak = rusak_ringan + rusak_sedang + rusak_berat

        def persen(x): return f"{(x / total_panjang * 100):.1f}%" if total_panjang else "0.0%"

        # Desa dengan rusak berat terpanjang
        df_rb = df_metrics[df_metrics['RUSAK BERAT (meter)'] == df_metrics['RUSAK BERAT (meter)'].max()]
        rb_row = df_rb.iloc[0] if not df_rb.empty else None

        # ========== CSS & Ringkasan Umum ==========
        st.markdown(f"""
        <style>
        .ringkasan-box {{
            background-color: #f0f4f8;
            padding: 30px 20px;
            border-radius: 12px;
            box-shadow: 2px 4px 8px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }}

        .ringkasan-box h3 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}

        .ringkasan-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}

        .card {{
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-size: 18px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.08);
        }}

        .bg1 {{ background-color: #e1f5fe; }}
        .bg2 {{ background-color: #e8f5e9; }}
        .bg3 {{ background-color: #fff3e0; }}
        .bg4 {{ background-color: #ffebee; }}
        .bg5 {{ background-color: #ede7f6; }}

        .card-value {{
            font-size: 30px;
            font-weight: bold;
            color: #333;
        }}

        .card-header {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #444;
        }}
        </style>

        <div class="ringkasan-box">
            <h3>DESKRIPSI UMUM</h3>
            <div class="ringkasan-grid">
                <div class="card bg1">
                    <div class="card-header">Jumlah Ruas Jalan</div>
                    <div class="card-value">{total_ruas:,}</div>
                </div>
                <div class="card bg1">
                    <div class="card-header">Total Panjang Jalan</div>
                    <div class="card-value">{int(total_panjang):,} m</div>
                </div>
                <div class="card bg1">
                    <div class="card-header">Kondisi Baik</div>
                    <div class="card-value">{int(total_baik):,} m ({persen(total_baik)})</div>
                </div>
                <div class="card bg1">
                    <div class="card-header">Total Jalan Rusak</div>
                    <div class="card-value">{int(total_rusak):,} m ({persen(total_rusak)})</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ========== Desa dengan Rusak Berat Terpanjang ==========
        if rb_row is not None:
            st.markdown(f"""
            <div class="ringkasan-box">
                <h3>DESA DENGAN JALAN RUSAK BERAT TERPANJANG</h3>
                <div class="ringkasan-grid">
                    <div class="card bg2">
                        <div class="card-header">Lokasi</div>
                        <div class="card-value">{rb_row['KABUPATEN']} - {rb_row['KECAMATAN']} - {rb_row['DESA']}</div>
                    </div>
                    <div class="card bg2">
                        <div class="card-header">Nama Ruas</div>
                        <div class="card-value">{rb_row['NAMA RUAS JALAN DESA']}</div>
                    </div>
                    <div class="card bg2">
                        <div class="card-header">Panjang Rusak Berat</div>
                        <div class="card-value">{int(rb_row['RUSAK BERAT (meter)']):,} m</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ======= RINGKASAN KONDISI TOTAL (DISPLAY BOX HORIZONTAL) =======
        st.markdown("""
        <div class="ringkasan-box">
            <h3>JALAN BERDASARKAN KONDISI</h3>
            <div class="ringkasan-grid">
                <div class="card bg5">
                    <div class="card-header">Kondisi Baik</div>
                    <div class="card-value">{:,} m ({})</div>
                </div>
                <div class="card bg5">
                    <div class="card-header">Rusak Ringan</div>
                    <div class="card-value">{:,} m ({})</div>
                </div>
                <div class="card bg5">
                    <div class="card-header">Rusak Sedang</div>
                    <div class="card-value">{:,} m ({})</div>
                </div>
                <div class="card bg5">
                    <div class="card-header">Rusak Berat</div>
                    <div class="card-value">{:,} m ({})</div>
                </div>
            </div>
        </div>
        """.format(
            int(total_baik), persen(total_baik),
            int(rusak_ringan), persen(rusak_ringan),
            int(rusak_sedang), persen(rusak_sedang),
            int(rusak_berat), persen(rusak_berat)
        ), unsafe_allow_html=True)

        # ========== Ringkasan Kondisi Jalan ==========
        st.subheader("📋 Ringkasan Kondisi Jalan per Desa")

        summary = df_metrics.groupby(["KABUPATEN", "KECAMATAN", "DESA"])[
                ["BAIK (meter)", "RUSAK RINGAN (meter)", "RUSAK SEDANG (meter)", "RUSAK BERAT (meter)"]
            ].sum().reset_index()

            # Tambah baris total
        total_row = summary.iloc[:, 3:].sum().to_dict()
        total_row.update({
                "KABUPATEN": "TOTAL",
                "KECAMATAN": "",
                "DESA": ""
            })
        summary.loc[len(summary.index)] = total_row

        st.dataframe(summary, use_container_width=True)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            summary.to_excel(writer, sheet_name="Ringkasan Kondisi", index=False)
        buffer.seek(0)
        st.download_button("📥 Download Ringkasan Kondisi Jalan", buffer, file_name="ringkasan_kondisi_jalan.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab2:
    st.subheader("📈 Grafik Kondisi Jalan")

    agg_cols = ['BAIK (meter)', 'RUSAK RINGAN (meter)', 'RUSAK SEDANG (meter)', 'RUSAK BERAT (meter)']
    for col in agg_cols:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

    # Tentukan grouping level
    grouping = 'KABUPATEN'
    if selected_desa != "Semua":
        grouping = 'NAMA RUAS JALAN DESA'
    elif selected_kec != "Semua":
        grouping = 'DESA'
    elif selected_kab != "Semua":
        grouping = 'KECAMATAN'

    summary = filtered_df.groupby(grouping)[agg_cols].sum().reset_index()
    total_per_group = summary[agg_cols].sum(axis=1)
    total_semua = total_per_group.sum()

    summary_long = pd.melt(summary, id_vars=[grouping], value_vars=agg_cols, 
                           var_name='Kondisi', value_name='Panjang (meter)')

    # Hitung persentase dari total keseluruhan untuk setiap bar
    summary_long["Persentase (%)"] = summary_long["Panjang (meter)"] / total_semua * 100

    fig = px.bar(
    summary_long,
    x=grouping,
    y="Panjang (meter)",
    color="Kondisi",
    barmode="stack",
    title=f"Kondisi Jalan per {grouping}",
    hover_data={
        "Panjang (meter)": ":,.0f",
        "Persentase (%)": ":.2f",
        grouping: True,
        "Kondisi": True
    }
)
    # Default hover: hanya yang ditunjuk
    st.plotly_chart(fig, use_container_width=True)


    # ==================== GRAFIK BERDASARKAN JENIS PERKERASAN ====================
    st.subheader("📈 Grafik Kondisi Jalan berdasarkan Jenis Perkerasan")
    df_plot = df_metrics.groupby("JENIS PERKERASAN")[agg_cols].sum().reset_index()
    df_plot_melted = df_plot.melt(id_vars="JENIS PERKERASAN", var_name="Kondisi", value_name="Panjang (meter)")
    total_jenis = df_plot_melted["Panjang (meter)"].sum()
    df_plot_melted["Persentase (%)"] = df_plot_melted["Panjang (meter)"] / total_jenis * 100

    fig2 = px.bar(
    df_plot_melted,
    x="JENIS PERKERASAN",
    y="Panjang (meter)",
    color="Kondisi",
    barmode="stack",
    title="Kondisi Jalan berdasarkan Jenis Perkerasan",
    hover_data={
        "Panjang (meter)": ":,.0f",
        "Persentase (%)": ":.2f",
        "JENIS PERKERASAN": True,
        "Kondisi": True
    }
)
    # Tidak pakai hovermode unified
    st.plotly_chart(fig2, use_container_width=True)



    with tab3:
        st.subheader("💰 Estimasi Biaya Perbaikan Jalan")

        harga_aspal = st.number_input("💵 Harga per meter (Aspal)", value=350_000)
        harga_beton = st.number_input("💵 Harga per meter (Beton)", value=850_000)
        harga_paving = st.number_input("💵 Harga per meter (Pavingblock)", value=160_000)

        def estimasi_card(judul, panjang):
            return f"""
            <div style='
                padding:20px;
                border-radius:12px;
                background:#e3f2fd;
                text-align:center;
                font-size:18px;
                box-shadow: 1px 2px 6px rgba(0,0,0,0.1);'>
                <div style='font-weight:bold;font-size:20px'>{judul}</div><br>
                <div><b>Panjang:</b> {int(panjang):,} m</div>
                <div>Aspal: Rp {int(panjang * harga_aspal):,}</div>
                <div>Beton: Rp {int(panjang * harga_beton):,}</div>
                <div>Paving: Rp {int(panjang * harga_paving):,}</div>
            </div>
            """

        c1, c2, c3 = st.columns(3)
        c1.markdown(estimasi_card("⚠️ Rusak Ringan", rusak_ringan), unsafe_allow_html=True)
        c2.markdown(estimasi_card("⚠️ Rusak Sedang", rusak_sedang), unsafe_allow_html=True)
        c3.markdown(estimasi_card("❌ Rusak Berat", rusak_berat), unsafe_allow_html=True)


    with tab4:
        st.subheader("🗺️ Peta Jalan Desa")
        render_peta(filtered_df)

with tab5:
    st.subheader("📄 Data Mentah")

    # Buat salinan dataframe dan tambahkan kolom nomor urut manual
    df_display = filtered_df.copy().reset_index(drop=True)
    df_display.index = df_display.index + 1  # Mulai dari 1
    
    # Tampilkan hanya 2 kolom untuk nomor: "No" (manual) dan "NO" (data asli)
    st.dataframe(df_display, use_container_width=True)

    # Export ke Excel
    raw = BytesIO()
    with pd.ExcelWriter(raw, engine="xlsxwriter") as writer:
        df_display.to_excel(writer, sheet_name="Data Mentah", index=False)
    raw.seek(0)

    st.download_button(
        "📥 Download Data Mentah",
        raw,
        file_name="data_mentah_jalan_desa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


