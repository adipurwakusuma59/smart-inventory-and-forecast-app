import streamlit as st
import pandas as pd
import numpy as np

# 0. Melebarkan tampilan halaman agar lebih lega
st.set_page_config(layout="wide")

# 1. Judul Aplikasi Web
st.title("📦 Smart Inventory Tracker & Forecaster")
st.write("Aplikasi pemantauan stok cerdas untuk efisiensi rantai pasok.")

# 2. Menyiapkan Data 
data_gudang = {
    "Kode Barang": ["BRG-01", "BRG-02", "BRG-03", "BRG-04"],
    "Nama Barang": ["Kain Katun", "Benang Jahit", "Kancing Baju", "Resleting"],
    "Stok Saat Ini": [10237, 5923, 5009, 1002],
    "Batas Aman (ROP)": [10238, 5924, 5009, 1002],
    "Penggunaan Harian": [2000, 500, 100, 200]
}
tabel_inventory = pd.DataFrame(data_gudang)

# 3. Logika Teknik Industri
tabel_inventory['Sisa Hari'] = (tabel_inventory['Stok Saat Ini'] / tabel_inventory['Penggunaan Harian']).round(1)
tabel_inventory['Rekomendasi Waktu'] = np.where(
    tabel_inventory['Sisa Hari'] <= 7, '🚨 KRITIS: Pesan Hari Ini!',
    np.where(tabel_inventory['Sisa Hari'] <= 14, '⚠️ WARNING: Siapkan Dokumen PO', '✅ Aman')
)

# ================= FITUR BARU MULAI DARI SINI =================

# 4. Membuat Sidebar (Menu Samping) untuk Filter Interaktif
st.sidebar.header("⚙️ Panel Kontrol")
st.sidebar.write("Gunakan filter ini untuk menyaring data.")

# Membuat tombol pilihan (selectbox) di sidebar
pilihan_status = st.sidebar.selectbox(
    "Pilih Status Barang yang Ingin Dilihat:",
    ("Semua Barang", "🚨 KRITIS: Pesan Hari Ini!", "⚠️ WARNING: Siapkan Dokumen PO", "✅ Aman")
)

# Logika Filter: Jika user tidak memilih "Semua Barang", potong tabelnya!
if pilihan_status != "Semua Barang":
    tabel_inventory = tabel_inventory[tabel_inventory['Rekomendasi Waktu'] == pilihan_status]

# 5. Membuat Metrik KPI (Key Performance Indicator)
st.markdown("---") # Membuat garis pembatas
col1, col2, col3 = st.columns(3) # Membagi layar jadi 3 kolom

# Menghitung data untuk KPI
jumlah_kritis = len(tabel_inventory[tabel_inventory['Sisa Hari'] <= 7])
rata_rata_hari = tabel_inventory['Sisa Hari'].mean().round(1)

# Menampilkan KPI
col1.metric("Total Item Ditampilkan", len(tabel_inventory), "Jenis Barang")
col2.metric("Total Barang Kritis", jumlah_kritis, "- Segera Tindak Lanjut!", delta_color="inverse")
col3.metric("Rata-rata Ketahanan Stok", f"{rata_rata_hari} Hari")
st.markdown("---")

# ==============================================================

# 6. Menampilkan ke Dashboard Interaktif
st.subheader("📊 Data Persediaan Terkini")
st.dataframe(tabel_inventory, use_container_width=True) 

# 7. Menambahkan Grafik Interaktif
st.subheader("📉 Visualisasi Sisa Hari (Run-out Time)")
grafik_data = tabel_inventory.set_index('Nama Barang')['Sisa Hari']
st.bar_chart(grafik_data)