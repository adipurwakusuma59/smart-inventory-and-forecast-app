import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from difflib import SequenceMatcher
from datetime import datetime

# 0. Setelan Halaman
st.set_page_config(page_title="Enterprise Supply Chain SaaS", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1f77b4;}
    @media print { .stSidebar, button, .stTabs [data-baseweb="tab-list"] {display: none;} }
    .score-high {color: #0f5132; background-color: #d1e7dd; padding: 2px 8px; border-radius: 4px; font-weight: bold;}
    .score-med {color: #664d03; background-color: #fff3cd; padding: 2px 8px; border-radius: 4px; font-weight: bold;}
    .score-low {color: #842029; background-color: #f8d7da; padding: 2px 8px; border-radius: 4px; font-weight: bold;}
    .insight-box {background-color: var(--secondary-background-color); color: var(--text-color); border-left: 5px solid #1f77b4; padding: 15px; margin-top: 15px; border-radius: 4px;}
    .alert-card-kritis {background-color: #ffcccc; color: #cc0000; padding: 10px 15px; border-radius: 6px; font-weight: bold; margin-bottom: 8px; border-left: 5px solid #cc0000;}
    .alert-card-warning {background-color: #fff2cc; color: #cc9900; padding: 10px 15px; border-radius: 6px; font-weight: bold; margin-bottom: 8px; border-left: 5px solid #cc9900;}
    .landing-card {background-color: var(--secondary-background-color); padding: 20px; border-radius: 10px; border-top: 4px solid #1f77b4; height: 100%;}
    </style>
""", unsafe_allow_html=True)

# --- 11 & 12. MEMORI SISTEM UNTUK HISTORY & TEMPLATE ---
if 'tahap_analisis' not in st.session_state: st.session_state.tahap_analisis = False
if 'nama_file_terakhir' not in st.session_state: st.session_state.nama_file_terakhir = ""
if 'history_analisis' not in st.session_state: st.session_state.history_analisis = []
if 'template_mapping' not in st.session_state: st.session_state.template_mapping = {}

KAMUS_ISTILAH = {
    'Nama Barang': ['nama', 'item', 'produk', 'barang', 'description', 'desc', 'koleksi', 'name', 'sku', 'bahan', 'id'],
    'Stok Aktual': ['stok', 'stock', 'qty', 'jumlah', 'fisik', 'sisa', 'on_hand', 'tersedia', 'kuantitas', 'balance'],
    'Safety Stock (ROP)': ['rop', 'min', 'minimum', 'batas', 'safety', 'ambang', 'threshold', 'buffer'],
    'Konsumsi Harian': ['konsumsi', 'penggunaan', 'sales', 'terjual', 'harian', 'daily', 'avg_sales', 'rata'],
    'Harga Satuan': ['harga', 'price', 'cost', 'nilai', 'satuan', 'beli', 'unit_cost', 'hpp']
}

def deteksi_kolom_cerdas(df, peran, keywords):
    kandidat = "-- Lewati (Tidak Ada) --"; best_score = 0
    for col in df.columns:
        col_norm = str(col).lower().replace('_', ' '); score = 0
        if any(kw == col_norm for kw in keywords): score = 100
        elif any(kw in col_norm.split() for kw in keywords): score = 90
        elif any(kw in col_norm for kw in keywords): score = 75
        else:
            max_ratio = max([int(SequenceMatcher(None, kw, col_norm).ratio() * 100) for kw in keywords])
            if max_ratio > 65: score = max_ratio

        if score > 0:
            tipe_data = df[col].dtype
            if peran == 'Nama Barang' and tipe_data == 'object': score = min(score + 10, 100)
            elif peran != 'Nama Barang':
                if pd.api.types.is_numeric_dtype(tipe_data): score = min(score + 15, 100)
                else: score = max(score - 30, 0)
        if score > best_score: best_score = score; kandidat = col
    return kandidat, best_score

st.title("🚀 Enterprise Supply Chain & Prescriptive Platform")

if not st.session_state.tahap_analisis:
    st.sidebar.header("📂 1. Unggah Dataset Persediaan")
    file_unggahan = st.sidebar.file_uploader("Pilih dokumen (Format CSV / Excel)", type=["csv", "xlsx", "xls"])
    
    # --- 11. SIDEBAR RIWAYAT ANALISIS ---
    if st.session_state.history_analisis:
        st.sidebar.markdown("---")
        with st.sidebar.expander("🕒 Riwayat Analisis Sebelumnya", expanded=True):
            for h in reversed(st.session_state.history_analisis[-5:]): # Tampilkan 5 terakhir
                st.markdown(f"**📄 {h['file']}**<br><small>📅 {h['waktu']} | ⭐ Skor: {h['skor']}/100</small>", unsafe_allow_html=True)
                st.markdown("---")

    if file_unggahan is None:
        # --- 10. LANDING PAGE PROFESIONAL ---
        st.markdown("### Transformasi Data Inventori Anda Menjadi Keputusan Strategis.")
        st.write("Platform ini dirancang khusus untuk menganalisis data rantai pasok Anda, mengkategorikan aset, dan memprediksi kebutuhan pemesanan secara otomatis menggunakan kecerdasan buatan.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_lp1, col_lp2, col_lp3 = st.columns(3)
        with col_lp1:
            st.markdown("<div class='landing-card'><h4>📊 Dashboard & ABC Analisis</h4><p>Peta visual kesehatan inventori dan pemilahan otomatis item Kategori A, B, dan C berdasarkan prinsip Pareto.</p></div>", unsafe_allow_html=True)
        with col_lp2:
            st.markdown("<div class='landing-card'><h4>🚚 AI Reorder Advisor</h4><p>Sistem merekomendasikan daftar barang yang harus dibeli hari ini lengkap dengan kuantitasnya untuk mencegah *stockout*.</p></div>", unsafe_allow_html=True)
        with col_lp3:
            st.markdown("<div class='landing-card'><h4>🔬 Risk Simulator</h4><p>Uji ketahanan gudang terhadap skenario terburuk seperti lonjakan permintaan mendadak atau keterlambatan supplier.</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👈 **Mulai Sekarang:** Silakan unggah dataset *inventory* Anda pada panel di sebelah kiri.")

    if file_unggahan is not None:
        if file_unggahan.name != st.session_state.nama_file_terakhir:
            st.session_state.tahap_analisis = False
            st.session_state.nama_file_terakhir = file_unggahan.name

        nama_file = file_unggahan.name
        if nama_file.endswith('.csv'): tabel_mentah = pd.read_csv(file_unggahan)
        elif nama_file.endswith(('.xlsx', '.xls')): tabel_mentah = pd.read_excel(file_unggahan) 
        
        kolom_csv = tabel_mentah.columns.tolist()
        opsi_dropdown = ["-- Lewati (Tidak Ada) --"] + kolom_csv

        st.subheader("🪄 Sistem Deteksi Skema & Kualitas Data (AI Data Profiler)")
        
        # --- 12. FITUR TEMPLATE MAPPING ---
        pilihan_template = "-- Deteksi AI Otomatis --"
        if st.session_state.template_mapping:
            st.write("💡 **Pilih Template Mapping:**")
            pilihan_template = st.selectbox("Gunakan konfigurasi pemetaan yang pernah disimpan:", ["-- Deteksi AI Otomatis --"] + list(st.session_state.template_mapping.keys()))
            st.markdown("---")

        total_sel = tabel_mentah.size; sel_kosong = tabel_mentah.isnull().sum().sum()
        pct_kosong = (sel_kosong / total_sel) * 100 if total_sel > 0 else 0
        pct_lengkap = 100 - pct_kosong
        
        mapping_terpilih = {}; kolom_dikenali = 0; hasil_deteksi = {}
        
        for peran, keywords in KAMUS_ISTILAH.items():
            kandidat_ai, score = deteksi_kolom_cerdas(tabel_mentah, peran, keywords)
            
            # Timpa hasil deteksi AI jika user memilih Template
            if pilihan_template != "-- Deteksi AI Otomatis --":
                kandidat_template = st.session_state.template_mapping[pilihan_template].get(peran, "-- Lewati (Tidak Ada) --")
                if kandidat_template in opsi_dropdown:
                    kandidat_ai = kandidat_template
                    score = 100 # Visual feedback bahwa template berhasil di-apply
            
            hasil_deteksi[peran] = (kandidat_ai, score)
            if score >= 75: kolom_dikenali += 1
            
        dq_score = int((pct_lengkap * 0.5) + ((kolom_dikenali / len(KAMUS_ISTILAH)) * 50))
        
        col_dq1, col_dq2, col_dq3, col_dq4 = st.columns(4)
        col_dq1.metric("🔍 Kolom Terpetakan", f"{kolom_dikenali} dari {len(KAMUS_ISTILAH)}")
        col_dq2.metric("📝 Kelengkapan Data", f"{pct_lengkap:.1f}%")
        col_dq3.metric("⚠️ Missing Values", f"{sel_kosong} Sel ({pct_kosong:.1f}%)")
        col_dq4.metric("⭐ Data Quality Score", f"{dq_score}/100")
        st.markdown("---")
        
        c_h1, c_h2, c_h3, c_h4 = st.columns([2, 3, 2, 3])
        c_h1.markdown("<b>Parameter Sistem</b>", unsafe_allow_html=True); c_h2.markdown("<b>Deteksi Sistem / Template</b>", unsafe_allow_html=True)
        c_h3.markdown("<b>Confidence / Status</b>", unsafe_allow_html=True); c_h4.markdown("<b>Koreksi Manual</b>", unsafe_allow_html=True)

        for peran, (kandidat_ai, score) in hasil_deteksi.items():
            c1, c2, c3, c4 = st.columns([2, 3, 2, 3])
            c1.write(f"**{peran}**"); c2.code(kandidat_ai)
            
            if pilihan_template != "-- Deteksi AI Otomatis --": chip_style = "<span class='score-high'>✅ via Template</span>"
            elif score >= 80: chip_style = f"<span class='score-high'>{score}% (Sangat Yakin)</span>"
            elif score >= 60: chip_style = f"<span class='score-med'>{score}% (Cukup Yakin)</span>"
            else: chip_style = f"<span class='score-low'>{score}% (Ragu / Lewati)</span>"
            c3.markdown(chip_style, unsafe_allow_html=True)
            
            idx_default = opsi_dropdown.index(kandidat_ai) if kandidat_ai in opsi_dropdown else 0
            mapping_terpilih[peran] = c4.selectbox(f"Koreksi {peran}", opsi_dropdown, index=idx_default, label_visibility="collapsed")

        st.markdown("---")
        st.subheader("🚚 Pengaturan Operasional Logistik")
        col_L1, col_L2, col_L3 = st.columns(3)
        lead_time = col_L1.number_input("Lead Time Supplier (Hari):", min_value=1, value=3)
        target_pemenuhan = col_L2.number_input("Target Hari Pemenuhan Stok Ulang:", min_value=7, value=30, step=7)
        metode_forecast = col_L3.selectbox("Metode Forecast:", ["Simulasi Linier Matematika", "Linear Regression (Machine Learning)"])
        kolom_kustom_dipilih = st.multiselect("Pilih Kolom Tambahan untuk Filter / Grouping:", options=[k for k in kolom_csv if k not in mapping_terpilih.values()])

        st.markdown("---")
        # --- 12. SIMPAN TEMPLATE BARU ---
        nama_template_baru = st.text_input("💾 Simpan Konfigurasi Pemetaan Ini Sebagai Template Baru (Opsional):", placeholder="Contoh: Template Data Gudang Pusat")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 KONFIRMASI PEMETAAN & JALANKAN DASHBOARD SEKARANG", type="primary", use_container_width=True):
            if nama_template_baru: st.session_state.template_mapping[nama_template_baru] = mapping_terpilih
            
            # --- 11. CATAT KE HISTORY ---
            st.session_state.history_analisis.append({
                "waktu": datetime.now().strftime("%d %b %Y, %H:%M"),
                "file": nama_file,
                "skor": dq_score
            })
            
            st.session_state.map_final = mapping_terpilih
            st.session_state.lead_time = lead_time
            st.session_state.target_pemenuhan = target_pemenuhan
            st.session_state.metode_forecast = metode_forecast
            st.session_state.kolom_kustom = kolom_kustom_dipilih
            st.session_state.dq_score = dq_score
            st.session_state.df_mentah = tabel_mentah
            st.session_state.tahap_analisis = True
            st.rerun()

# =========================================================================
# LAYAR 2: DASHBOARD UTAMA
# =========================================================================
else:
    st.sidebar.success("✅ Data berhasil dipetakan.")
    if st.sidebar.button("⚙️ Atur Ulang Pemetaan / Ganti File", use_container_width=True):
        st.session_state.tahap_analisis = False; st.rerun()

    m = st.session_state.map_final; tabel_mentah = st.session_state.df_mentah
    tabel_inventory = tabel_mentah.rename(columns={m['Nama Barang']: 'Nama Barang', m['Stok Aktual']: 'Stok Saat Ini'})
    tabel_inventory['Stok Saat Ini'] = pd.to_numeric(tabel_inventory['Stok Saat Ini'], errors='coerce').fillna(0)
    tabel_inventory['Rekomendasi Waktu'] = '✅ AMAN'

    fitur_rop_aktif = False
    if m['Safety Stock (ROP)'] != "-- Lewati (Tidak Ada) --":
        tabel_inventory['Batas Aman (ROP)'] = pd.to_numeric(tabel_mentah[m['Safety Stock (ROP)']], errors='coerce').fillna(0)
        fitur_rop_aktif = True
        tabel_inventory['Rekomendasi Waktu'] = np.where(tabel_inventory['Stok Saat Ini'] < tabel_inventory['Batas Aman (ROP)'], '🚨 KRITIS (Di Bawah ROP)', '✅ AMAN')

    fitur_forecast_aktif = False
    if m['Konsumsi Harian'] != "-- Lewati (Tidak Ada) --":
        tabel_inventory['Penggunaan Harian'] = pd.to_numeric(tabel_mentah[m['Konsumsi Harian']], errors='coerce').fillna(1)
        if st.session_state.metode_forecast == "Linear Regression (Machine Learning)":
            sisa_hari_list = []
            for index, row in tabel_inventory.iterrows():
                X_train = np.array([0, 1, 2, 3, 4]).reshape(-1, 1)
                y_train = np.array([row['Stok Saat Ini'], max(row['Stok Saat Ini'] - row['Penggunaan Harian'], 0), max(row['Stok Saat Ini'] - (row['Penggunaan Harian']*2), 0), max(row['Stok Saat Ini'] - (row['Penggunaan Harian']*3), 0), max(row['Stok Saat Ini'] - (row['Penggunaan Harian']*4), 0)])
                model = LinearRegression().fit(X_train, y_train)
                sisa_hari_list.append(max(round(-model.intercept_ / model.coef_[0], 1), 0) if model.coef_[0] != 0 else 0)
            tabel_inventory['Sisa Hari'] = sisa_hari_list
        else:
            tabel_inventory['Sisa Hari'] = (tabel_inventory['Stok Saat Ini'] / tabel_inventory['Penggunaan Harian']).round(1)
        tabel_inventory['Rekomendasi Waktu'] = np.where(tabel_inventory['Sisa Hari'] <= 7, '🚨 KRITIS (Pesan Sekarang)', np.where(tabel_inventory['Sisa Hari'] <= 14, '⚠️ WARNING (Siapkan PO)', '✅ AMAN'))
        fitur_forecast_aktif = True

    fitur_finansial_aktif = False
    if m['Harga Satuan'] != "-- Lewati (Tidak Ada) --":
        tabel_inventory['Harga Satuan Standar'] = pd.to_numeric(tabel_mentah[m['Harga Satuan']], errors='coerce').fillna(0)
        tabel_inventory['Total Nilai Aset'] = tabel_inventory['Stok Saat Ini'] * tabel_inventory['Harga Satuan Standar']
        fitur_finansial_aktif = True

    total_nilai_gudang = 0
    if fitur_finansial_aktif and len(tabel_inventory) > 0:
        total_nilai_gudang = tabel_inventory['Total Nilai Aset'].sum()
        tabel_inventory = tabel_inventory.sort_values(by='Total Nilai Aset', ascending=False)
        tabel_inventory['Kumulatif_Pct'] = tabel_inventory['Total Nilai Aset'].cumsum() / total_nilai_gudang if total_nilai_gudang > 0 else 0
        tabel_inventory['Analisis ABC'] = np.where(tabel_inventory['Kumulatif_Pct'] <= 0.70, 'Kategori A', np.where(tabel_inventory['Kumulatif_Pct'] <= 0.90, 'Kategori B', 'Kategori C'))
    else:
        tabel_inventory['Analisis ABC'] = 'Butuh Data Finansial'; tabel_inventory['Kumulatif_Pct'] = 0.0

    if fitur_forecast_aktif:
        tabel_inventory['Hari Terbaik Memesan'] = (tabel_inventory['Sisa Hari'] - st.session_state.lead_time).round(1)
        tabel_inventory['Rekomendasi Pembelian'] = np.where(tabel_inventory['Sisa Hari'] <= st.session_state.lead_time, "🚨 Harus Dipesan Hari Ini!", np.where(tabel_inventory['Sisa Hari'] <= (st.session_state.lead_time + 5), "⏳ Jadwalkan dalam " + tabel_inventory['Hari Terbaik Memesan'].astype(str) + " hari", "✅ Belum Perlu Pemesanan"))
        tabel_inventory['Rekomendasi Jumlah Beli (Unit)'] = np.where(tabel_inventory['Sisa Hari'] <= (st.session_state.lead_time + 5), ((tabel_inventory['Penggunaan Harian'] * st.session_state.target_pemenuhan) + (tabel_inventory['Batas Aman (ROP)'] if fitur_rop_aktif else 0) - tabel_inventory['Stok Saat Ini']).round(0), 0).clip(min=0)

    cnt_total = len(tabel_inventory); cnt_kritis = len(tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('KRITIS', na=False)])
    cnt_warning = len(tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('WARNING', na=False)]); cnt_aman = len(tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('AMAN', na=False)])

    health_score = int((cnt_aman / cnt_total) * 100) if cnt_total > 0 else 0
    risk_score = min(int(((cnt_kritis * 1.5 + cnt_warning) / cnt_total) * 100) if cnt_total > 0 else 0, 100)
    forecast_score = st.session_state.dq_score if fitur_forecast_aktif else 0

    # --- 9. MODERNISASI STRUKTUR MENU ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "🚚 Reorder Advisor", 
        "🔍 Item Explorer", 
        "🔬 Risk Simulator", 
        "📈 Forecast Center", 
        "🗄️ Data Explorer"
    ])

    with tab1:
        st.markdown("### 🤖 AI Executive Summary")
        ringkasan = f"Gudang Anda saat ini mengelola **{cnt_total} item**."
        if cnt_kritis > 0:
            item_kritis_nama = tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('KRITIS', na=False)]['Nama Barang'].iloc[0]
            ringkasan += f" ⚠️ **Peringatan Penting:** Terdapat **{cnt_kritis} item dalam kondisi kritis** (salah satunya: *{item_kritis_nama}*). Potensi kekosongan stok (*stockout*) sudah di depan mata."
        else:
            ringkasan += " ✅ Kondisi operasional saat ini **sangat sehat**, tidak ada item yang terancam habis dalam waktu dekat."
        st.info(ringkasan)
        st.markdown("---")

        c_score1, c_score2, c_score3 = st.columns(3)
        c_score1.metric("🏥 Inventory Health Score", f"{health_score}/100", "Indikator Keamanan")
        c_score2.metric("⚠️ Supply Chain Risk Score", f"{risk_score}/100", "-Indikator Risiko", delta_color="inverse")
        c_score3.metric("🔮 Forecast Reliability", f"{forecast_score}/100", "Berdasarkan Data Quality")
        st.markdown("---")

        st.subheader("🔔 Papan Peringatan Cepat (Alert Cards)")
        col_alert1, col_alert2 = st.columns(2)
        with col_alert1:
            if cnt_kritis > 0:
                for idx, row in tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('KRITIS')].head(5).iterrows():
                    sisa_teks = f"Sisa {row['Sisa Hari']} Hari" if fitur_forecast_aktif else "Di Bawah Batas Minimum"
                    st.markdown(f"<div class='alert-card-kritis'>🔴 Kritis: {row['Nama Barang']} – {sisa_teks}</div>", unsafe_allow_html=True)
            else: st.success("🟢 Tidak ada item kritis.")
        with col_alert2:
            if cnt_warning > 0:
                for idx, row in tabel_inventory[tabel_inventory['Rekomendasi Waktu'].str.contains('WARNING')].head(5).iterrows():
                    sisa_teks = f"Sisa {row['Sisa Hari']} Hari" if fitur_forecast_aktif else "Perlu Pemantauan"
                    st.markdown(f"<div class='alert-card-warning'>🟡 Warning: {row['Nama Barang']} – {sisa_teks}</div>", unsafe_allow_html=True)
            else: st.info("🟢 Tidak ada item dalam status warning.")
        if (cnt_kritis + cnt_warning) > 10: st.caption("*Hanya menampilkan 5 peringatan teratas. Lihat tab Data Explorer untuk selengkapnya.*")

        st.markdown("---")
        st.subheader("Peta Status Persediaan (Kuantitas Fisik)")
        warna_grafik = 'Rekomendasi Waktu'
        warna_status = {'🚨 KRITIS (Pesan Sekarang)': '#ef553b', '🚨 KRITIS (Di Bawah ROP)': '#ef553b', '⚠️ WARNING (Siapkan PO)': '#feca28', '✅ AMAN': '#00cc96'}
        if kustom := st.session_state.kolom_kustom: warna_grafik = kustom[0]; warna_status = None
        st.plotly_chart(px.bar(tabel_inventory, x='Nama Barang', y='Stok Saat Ini', color=warna_grafik, color_discrete_map=warna_status, text='Stok Saat Ini').update_traces(textposition='outside'), use_container_width=True)

        if fitur_finansial_aktif:
            st.markdown("---")
            st.subheader("🎯 Klasifikasi Manajemen ABC & Kurva Pareto")
            tabel_inventory['Kumulatif_Pct_100'] = tabel_inventory['Kumulatif_Pct'] * 100
            bar_colors = tabel_inventory['Analisis ABC'].map({'Kategori A': '#1f77b4', 'Kategori B': '#ff7f0e', 'Kategori C': '#2ca02c'}).tolist()
            
            fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
            fig_pareto.add_trace(go.Bar(x=tabel_inventory['Nama Barang'], y=tabel_inventory['Total Nilai Aset'], name="Nilai Aset Item", marker_color=bar_colors), secondary_y=False)
            fig_pareto.add_trace(go.Scatter(x=tabel_inventory['Nama Barang'], y=tabel_inventory['Kumulatif_Pct_100'], name="Kurva Kumulatif (%)", mode="lines+markers", line=dict(color="#ef553b", width=3)), secondary_y=True)
            fig_pareto.update_layout(margin=dict(t=40, b=40))
            st.plotly_chart(fig_pareto, use_container_width=True)
            
            item_a = len(tabel_inventory[tabel_inventory['Analisis ABC'] == 'Kategori A'])
            if total_nilai_gudang > 0:
                pct_a = tabel_inventory[tabel_inventory['Analisis ABC'] == 'Kategori A']['Total Nilai Aset'].sum() / total_nilai_gudang * 100
                st.markdown(f"<div class='insight-box'><b>💡 Insight Pareto Analisis:</b> Sebanyak <b>{item_a} item Kategori A</b> menyumbang <b>{pct_a:.1f}%</b> dari total nilai aset. Fokuskan pengawasan ketat pada item berlabel biru ini.</div>", unsafe_allow_html=True)

    with tab2:
        st.subheader("📋 Rekomendasi Pembelian Barang Otomatis (AI Advisor)")
        if fitur_forecast_aktif:
            kolom_tampil = ['Nama Barang', 'Stok Saat Ini', 'Penggunaan Harian', 'Sisa Hari', 'Hari Terbaik Memesan', 'Rekomendasi Pembelian', 'Rekomendasi Jumlah Beli (Unit)']
            st.dataframe(tabel_inventory[kolom_tampil].style.map(lambda v: 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if v == "🚨 Harus Dipesan Hari Ini!" else ('background-color: #fff2cc; color: #cc9900;' if "⏳ Jadwalkan" in str(v) else ''), subset=['Rekomendasi Pembelian']), use_container_width=True)
            
            item_reorder = len(tabel_inventory[tabel_inventory['Rekomendasi Pembelian'] == "🚨 Harus Dipesan Hari Ini!"])
            if item_reorder > 0:
                st.markdown(f"<div class='insight-box'><b>💡 Insight Operasional:</b> Diperlukan penerbitan Purchase Order (PO) <b>HARI INI JUGA</b> untuk <b>{item_reorder} item</b> agar terhindar dari potensi *stockout* akibat terpotong waktu tunggu (*Lead Time*) pengiriman {st.session_state.lead_time} hari.</div>", unsafe_allow_html=True)

    with tab3:
        st.subheader("🔍 Smart Item Explorer")
        st.write("💡 *Tips: Klik kotak di bawah dan **ketik sebagian nama barang** untuk mencari dengan cepat.*")
        pilihan_barang = st.selectbox("Cari dan Pilih SKU Barang:", tabel_inventory['Nama Barang'].tolist(), index=None, placeholder="Ketik nama item di sini...")
        if pilihan_barang:
            d_item = tabel_inventory[tabel_inventory['Nama Barang'] == pilihan_barang].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Stok Saat Ini", f"{d_item['Stok Saat Ini']} Unit", d_item['Rekomendasi Waktu'])
            if fitur_finansial_aktif: c2.metric("Nilai Aset", f"Rp {d_item['Total Nilai Aset']:,.0f}", d_item['Analisis ABC'])
            if fitur_forecast_aktif: c3.metric("Ketahanan", f"{d_item['Sisa Hari']} Hari", d_item['Rekomendasi Pembelian'])
        else: st.info("Silakan cari dan pilih barang untuk melihat metrik mendalamnya.")

    with tab4:
        st.subheader("🔬 Simulasi Skenario Risiko (What-If Analysis)")
        if fitur_forecast_aktif:
            c_w1, c_w2 = st.columns(2)
            sim_dm = c_w1.slider("Lonjakan Permintaan (%)", 0, 100, 0, 5)
            sim_lt = c_w2.slider("Keterlambatan Pengiriman Supplier (Hari)", 0, 14, 0, 1)
            
            df_sim = tabel_inventory.copy()
            df_sim['Sim_Sisa'] = (df_sim['Stok Saat Ini'] / (df_sim['Penggunaan Harian'] * (1 + (sim_dm/100)))).round(1)
            df_sim['Sim_Status'] = np.where(df_sim['Sim_Sisa'] <= (st.session_state.lead_time + sim_lt), "🚨 KRITIS (Gagal Penuhi Permintaan)!", "✅ Aman")
            st.dataframe(df_sim[['Nama Barang', 'Sisa Hari', 'Sim_Sisa', 'Rekomendasi Pembelian', 'Sim_Status']].style.map(lambda v: 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if "KRITIS" in str(v) else '', subset=['Sim_Status']), use_container_width=True)

    with tab5:
        st.subheader("Simulasi Penurunan Stok Keseluruhan")
        if fitur_forecast_aktif:
            hari = np.arange(0, 31); df_fc = pd.DataFrame({'Hari Ke-': hari})
            for idx, r in tabel_inventory.iterrows(): df_fc[r['Nama Barang']] = np.maximum(r['Stok Saat Ini'] - (r['Penggunaan Harian'] * hari), 0)
            st.plotly_chart(px.line(df_fc.melt(id_vars=['Hari Ke-'], var_name='Nama Barang', value_name='Stok'), x='Hari Ke-', y='Stok', color='Nama Barang', markers=True), use_container_width=True)

    with tab6:
        st.subheader("🗄️ Tabel Data Explorer Terpadu")
        if kustom := st.session_state.kolom_kustom:
            kolom_filter = st.columns(len(kustom))
            for i, col_name in enumerate(kustom):
                with kolom_filter[i]:
                    pilih_unik = ["Semua"] + tabel_mentah[col_name].dropna().astype(str).unique().tolist()
                    filter_val = st.selectbox(f"Saring {col_name.replace('_', ' ')}:", pilih_unik)
                    if filter_val != "Semua": tabel_inventory = tabel_inventory[tabel_mentah[col_name].astype(str) == filter_val]

        def style_status(val):
            if 'KRITIS' in str(val): return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
            elif 'WARNING' in str(val): return 'background-color: #fff2cc; color: #cc9900; font-weight: bold;'
            elif 'AMAN' in str(val): return 'background-color: #d1e7dd; color: #0f5132;'
            return ''
        subset_styling = [c for c in ['Rekomendasi Waktu', 'Rekomendasi Pembelian'] if c in tabel_inventory.columns]
        st.dataframe(tabel_inventory.style.map(style_status, subset=subset_styling), use_container_width=True)
