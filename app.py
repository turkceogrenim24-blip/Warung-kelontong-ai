import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import json
import os
from datetime import datetime

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Aplikasi Kasir & Profit Warung AI", layout="wide")
st.title("🛒 Aplikasi Kasir, Stok & Laporan Profit Warung AI")
st.write("Kelola stok dengan AI, kasir instan, struk belanja, rekap omzet, dan analisis keuntungan bersih (profit).")

# Nama file cadangan lokal
BACKUP_STOK = "backup_stok_warung.csv"
BACKUP_PENJUALAN = "backup_penjualan_warung.csv"

# Mengambil API Key secara aman dari Streamlit Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ API Key belum diset di Streamlit Secrets! Mohon tambahkan GEMINI_API_KEY di pengaturan dashboard.")
    API_KEY = ""

# --- FUNGSI AUTO-BACKUP ---
def simpan_backup():
    """Menyimpan data stok dan penjualan ke file CSV lokal secara otomatis"""
    if not st.session_state.tabel_stok.empty:
        st.session_state.tabel_stok.to_csv(BACKUP_STOK, index=False)
    if not st.session_state.tabel_penjualan.empty:
        st.session_state.tabel_penjualan.to_csv(BACKUP_PENJUALAN, index=False)

# Inisialisasi session state Stok (Dengan tambahan Harga Modal)
if 'tabel_stok' not in st.session_state:
    if os.path.exists(BACKUP_STOK):
        try:
            st.session_state.tabel_stok = pd.read_csv(BACKUP_STOK)
        except Exception:
            st.session_state.tabel_stok = pd.DataFrame(columns=["Nama Barang", "Kategori", "Harga Modal (Rp)", "Harga Jual (Rp)", "Jumlah Stok"])
    else:
        st.session_state.tabel_stok = pd.DataFrame(columns=["Nama Barang", "Kategori", "Harga Modal (Rp)", "Harga Jual (Rp)", "Jumlah Stok"])

# Pastikan kolom Harga Modal ada jika memuat data lama
if "Harga Modal (Rp)" not in st.session_state.tabel_stok.columns and not st.session_state.tabel_stok.empty:
    st.session_state.tabel_stok["Harga Modal (Rp)"] = st.session_state.tabel_stok["Harga Jual (Rp)"] * 0.8 # Default 80% dari harga jual

# Inisialisasi session state Riwayat Penjualan (Dengan kolom Profit)
if 'tabel_penjualan' not in st.session_state:
    if os.path.exists(BACKUP_PENJUALAN):
        try:
            st.session_state.tabel_penjualan = pd.read_csv(BACKUP_PENJUALAN)
        except Exception:
            st.session_state.tabel_penjualan = pd.DataFrame(columns=["Tanggal", "Jam", "Nama Barang", "Jumlah", "Harga Modal (Rp)", "Harga Jual (Rp)", "Total Bayar (Rp)", "Total Profit (Rp)"])
    else:
        st.session_state.tabel_penjualan = pd.DataFrame(columns=["Tanggal", "Jam", "Nama Barang", "Jumlah", "Harga Modal (Rp)", "Harga Jual (Rp)", "Total Bayar (Rp)", "Total Profit (Rp)"])

# Inisialisasi session state untuk struk terakhir
if 'struk_terakhir' not in st.session_state:
    st.session_state.struk_terakhir = None

# Fungsi pembantu untuk mencatat transaksi penjualan & profit
def catat_transaksi(nama_barang, harga_modal, harga_jual, jumlah):
    sekarang = datetime.now()
    total_bayar = harga_jual * jumlah
    total_modal = harga_modal * jumlah
    total_profit = total_bayar - total_modal
    
    transaksi_baru = pd.DataFrame([{
        "Tanggal": sekarang.strftime("%Y-%m-%d"),
        "Jam": sekarang.strftime("%H:%M:%S"),
        "Nama Barang": nama_barang,
        "Jumlah": jumlah,
        "Harga Modal (Rp)": harga_modal,
        "Harga Jual (Rp)": harga_jual,
        "Total Bayar (Rp)": total_bayar,
        "Total Profit (Rp)": total_profit
    }])
    st.session_state.tabel_penjualan = pd.concat([st.session_state.tabel_penjualan, transaksi_baru], ignore_index=True)
    
    st.session_state.struk_terakhir = {
        "waktu": sekarang.strftime("%d-%m-%Y %H:%M:%S"),
        "nama_barang": nama_barang,
        "harga_jual": harga_jual,
        "jumlah": jumlah,
        "total_bayar": total_bayar,
        "total_profit": total_profit
    }
    simpan_backup()

# ==========================================
# NAVIGASI SIDEBAR (4 MODE KERJA)
# ==========================================
st.sidebar.title("⚙️ Menu Navigasi")
pilihan_menu = st.sidebar.radio("Pilih Mode Kerja:", [
    "📸 1. Pindai Tambah Stok (Restock)", 
    "🛍️ 2. Kasir Penjualan (Checkout)",
    "📈 3. Laporan Omzet & Profit Bersih",
    "🏆 4. Analisa Produk Laku & Kurang Laku"
])

# ==========================================
# MODE 1: TAMBAH STOK VIA KAMERA AI
# ==========================================
if pilihan_menu == "📸 1. Pindai Tambah Stok (Restock)":
    st.subheader("📸 Pindai Barang Masuk (Restock Stok + Harga Modal)")
    file_gambar = st.file_uploader("Upload Foto Produk Barang Masuk", type=["jpg", "jpeg", "png"], key="restock_upload")

    if file_gambar is not None:
        gambar_barang = Image.open(file_gambar)
        st.image(gambar_barang, caption="Foto Produk Masuk", use_column_width=True)
        
        if st.button("Proses AI & Tambah Stok"):
            if not API_KEY:
                st.error("Mohon konfigurasikan API Key terlebih dahulu di Streamlit Secrets!")
            else:
                with st.spinner("🤖 AI sedang mengenali produk dan memperkirakan harga..."):
                    try:
                        client = genai.Client(api_key=API_KEY)
                        prompt = (
                            "Analisis gambar produk ini untuk inventaris warung kelontong. "
                            "Berikan jawaban HANYA dalam format JSON murni dengan kunci: "
                            "\"nama_barang\", \"kategori\", \"harga_jual_perkiraan\" (angka saja), dan \"harga_modal_perkiraan\" (angka perkiraan harga kulak/grosir modal, biasanya 75-85% dari harga jual)."
                        )
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[gambar_barang, prompt]
                        )
                        teks_bersih = response.text.replace("```json", "").replace("```", "").strip()
                        data_barang = json.loads(teks_bersih)
                        
                        nama_baru = data_barang["nama_barang"]
                        kategori_baru = data_barang["kategori"]
                        harga_jual_baru = int(data_barang["harga_jual_perkiraan"])
                        harga_modal_baru = int(data_barang["harga_modal_perkiraan"])
                        jumlah_tambah = 1
                        
                        tabel = st.session_state.tabel_stok
                        if not tabel.empty and nama_baru in tabel["Nama Barang"].values:
                            tabel.loc[tabel["Nama Barang"] == nama_baru, "Jumlah Stok"] += jumlah_tambah
                            st.success(f"Stok '{nama_baru}' berhasil bertambah 1!")
                        else:
                            barang_baru = {
                                "Nama Barang": nama_baru,
                                "Kategori": kategori_baru,
                                "Harga Modal (Rp)": harga_modal_baru,
                                "Harga Jual (Rp)": harga_jual_baru,
                                "Jumlah Stok": jumlah_tambah
                            }
                            st.session_state.tabel_stok = pd.concat([tabel, pd.DataFrame([barang_baru])], ignore_index=True)
                            st.success(f"Barang baru '{nama_baru}' berhasil dicatat (Modal: Rp {harga_modal_baru:,} | Jual: Rp {harga_jual_baru:,})!".replace(",", "."))
                        
                        simpan_backup()
                    except json.JSONDecodeError:
                        st.warning("⚠️ Foto terlalu buram atau objek tidak dikenali! Silakan ambil ulang foto.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan teknis: {e}")

# ==========================================
# MODE 2: KASIR PENJUALAN & CETAK STRUK
# ==========================================
elif pilihan_menu == "🛍️ 2. Kasir Penjualan (Checkout)":
    st.subheader("🛍️ Kasir Penjualan Warung (Checkout & Struk)")
    
    # Tampilkan Struk Belanja jika baru saja transaksi
    if st.session_state.struk_terakhir:
        s = st.session_state.struk_terakhir
        with st.container():
            st.markdown("### 🧾 STRUK BELANJA KELONTONG")
            st.markdown(f"""
            ```text
            ========================================
                 WARUNG KELONTONG BERKAH AI
            ========================================
            Waktu : {s['waktu']}
            ----------------------------------------
            Barang   : {s['nama_barang']}
            Harga    : Rp {s['harga_jual']:,.0f} x {s['jumlah']} pcs
            ----------------------------------------
            TOTAL    : Rp {s['total_bayar']:,.0f}
            ========================================
                 TERIMA KASIH ATAS KUNJUNGANNYA
            ========================================
            ```
            """.replace(",", "."))
            
            if st.button("✖️ Tutup Struk / Transaksi Baru"):
                st.session_state.struk_terakhir = None
                st.rerun()
            st.markdown("---")

    metode_kasir = st.radio("Metode Kasir:", ["🤖 Scan Foto Produk (AI Checkout)", "📝 Pilih Manual dari Daftar"], horizontal=True)
    
    if not st.session_state.tabel_stok.empty:
        # Metode A: Kasir Scan Kamera AI
        if metode_kasir == "🤖 Scan Foto Produk (AI Checkout)":
            file_kasir = st.file_uploader("Foto Produk yang Dibeli Pembeli", type=["jpg", "jpeg", "png"], key="kasir_upload")
            jumlah_beli_ai = st.number_input("Jumlah Beli (pcs):", min_value=1, value=1, step=1, key="qty_ai")
            
            if file_kasir is not None:
                img_kasir = Image.open(file_kasir)
                st.image(img_kasir, caption="Produk yang Dipindai Kasir", use_column_width=True)
                
                if st.button("💰 Proses Checkout AI & Cetak Struk"):
                    if not API_KEY:
                        st.error("API Key belum diset!")
                    else:
                        with st.spinner("🤖 AI mengenali produk untuk kasir..."):
                            try:
                                client = genai.Client(api_key=API_KEY)
                                prompt = (
                                    "Analisis gambar produk ini. Sebutkan HANYA nama barangnya saja dalam format JSON murni "
                                    "dengan kunci \"nama_barang\"."
                                )
                                response = client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=[img_kasir, prompt]
                                )
                                teks_bersih = response.text.replace("```json", "").replace("```", "").strip()
                                hasil_ai = json.loads(teks_bersih)
                                nama_terdeteksi = hasil_ai["nama_barang"]
                                
                                tabel = st.session_state.tabel_stok
                                if nama_terdeteksi in tabel["Nama Barang"].values:
                                    stok_sisa = int(tabel.loc[tabel["Nama Barang"] == nama_terdeteksi, "Jumlah Stok"].values[0])
                                    harga_jual = float(tabel.loc[tabel["Nama Barang"] == nama_terdeteksi, "Harga Jual (Rp)"].values[0])
                                    harga_modal = float(tabel.loc[tabel["Nama Barang"] == nama_terdeteksi, "Harga Modal (Rp)"].values[0])
                                    
                                    if jumlah_beli_ai > stok_sisa:
                                        st.error(f"❌ Stok '{nama_terdeteksi}' tidak cukup! (Sisa stok: {stok_sisa} pcs).")
                                    else:
                                        tabel.loc[tabel["Nama Barang"] == nama_terdeteksi, "Jumlah Stok"] = stok_sisa - jumlah_beli_ai
                                        
                                        # Catat ke riwayat penjualan & profit
                                        catat_transaksi(nama_terdeteksi, harga_modal, harga_jual, jumlah_beli_ai)
                                        st.rerun()
                                else:
                                    st.warning(f"⚠️ Produk '{nama_terdeteksi}' tidak ditemukan di inventaris! Silakan catat dulu via Restock.")
                            except Exception as e:
                                st.error(f"Gagal memproses kasir AI: {e}")

        # Metode B: Kasir Manual Dropdown
        else:
            with st.form("form_kasir_manual"):
                daftar_nama_barang = list(st.session_state.tabel_stok["Nama Barang"].unique())
                barang_pilihan = st.selectbox("Pilih Barang:", daftar_nama_barang)
                jumlah_terjual = st.number_input("Jumlah Terjual (pcs):", min_value=1, value=1, step=1)
                
                submitted_kasir = st.form_submit_button("💰 Bayar, Kurangi Stok & Cetak Struk")
                
                if submitted_kasir:
                    tabel = st.session_state.tabel_stok
                    stok_sekarang = int(tabel.loc[tabel["Nama Barang"] == barang_pilihan, "Jumlah Stok"].values[0])
                    harga_jual = float(tabel.loc[tabel["Nama Barang"] == barang_pilihan, "Harga Jual (Rp)"].values[0])
                    harga_modal = float(tabel.loc[tabel["Nama Barang"] == barang_pilihan, "Harga Modal (Rp)"].values[0])
                    
                    if jumlah_terjual > stok_sekarang:
                        st.error(f"❌ Gagal! Stok '{barang_pilihan}' tidak mencukupi (Sisa: {stok_sekarang} pcs).")
                    else:
                        tabel.loc[tabel["Nama Barang"] == barang_pilihan, "Jumlah Stok"] = stok_sekarang - jumlah_terjual
                        
                        # Catat ke riwayat penjualan & profit
                        catat_transaksi(barang_pilihan, harga_modal, harga_jual, jumlah_terjual)
                        st.rerun()
    else:
        st.info("Inventaris masih kosong. Silakan tambahkan barang terlebih dahulu melalui menu Restock.")

# ==========================================
# MODE 3: LAPORAN OMZET & PROFIT BERSIH
# ==========================================
elif pilihan_menu == "📈 3. Laporan Omzet & Profit Bersih":
    st.subheader("📈 Laporan Rekap Omzet & Keuntungan Bersih (Profit)")
    
    if not st.session_state.tabel_penjualan.empty:
        df_jual = st.session_state.tabel_penjualan.copy()
        df_jual["Total Bayar (Rp)"] = pd.to_numeric(df_jual["Total Bayar (Rp)"], errors='coerce').fillna(0)
        df_jual["Total Profit (Rp)"] = pd.to_numeric(df_jual["Total Profit (Rp)"], errors='coerce').fillna(0)
        df_jual["Jumlah"] = pd.to_numeric(df_jual["Jumlah"], errors='coerce').fillna(0)
        
        # Filter berdasarkan tanggal (Default: Hari ini)
        hari_ini = datetime.now().strftime("%Y-%m-%d")
        daftar_tanggal = ["Semua Tanggal"] + sorted(list(df_jual["Tanggal"].unique()), reverse=True)
        
        index_default = daftar_tanggal.index(hari_ini) if hari_ini in daftar_tanggal else 0
        tanggal_pilihan = st.selectbox("📅 Pilih Tanggal Laporan:", daftar_tanggal, index=index_default)
        
        if tanggal_pilihan == "Semua Tanggal":
            df_laporan = df_jual
        else:
            df_laporan = df_jual[df_jual["Tanggal"] == tanggal_pilihan]
            
        # Kartu Metrik Keuangan
        total_omzet = df_laporan["Total Bayar (Rp)"].sum()
        total_profit = df_laporan["Total Profit (Rp)"].sum()
        total_item_terjual = df_laporan["Jumlah"].sum()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("💵 Total Omzet (Kotor)", f"Rp {total_omzet:,.0f}".replace(",", "."))
        col_m2.metric("💰 Keuntungan Bersih (Profit)", f"Rp {total_profit:,.0f}".replace(",", "."), delta=f"Margin: {int((total_profit/total_omzet)*100) if total_omzet > 0 else 0}%")
        col_m3.metric("🛒 Barang Terjual", f"{int(total_item_terjual)} pcs")
        
        st.markdown("### Rincian Riwayat Transaksi & Profit")
        st.dataframe(df_laporan.iloc[::-1], use_container_width=True)
        
        st.download_button(
            label="📥 Download Laporan Keuangan (.csv)",
            data=df_laporan.to_csv(index=False).encode('utf-8'),
            file_name=f"laporan_profit_{tanggal_pilihan}.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada transaksi penjualan tercatat. Lakukan transaksi di menu Kasir.")

# ==========================================
# MODE 4: ANALISA PRODUK LAKU & KURANG LAKU
# ==========================================
elif pilihan_menu == "🏆 4. Analisa Produk Laku & Kurang Laku":
    st.subheader("🏆 Analisa Performa Produk & Kontribusi Profit")

    if st.session_state.tabel_stok.empty:
        st.info("Data stok masih kosong.")
    else:
        df_stok = st.session_state.tabel_stok[["Nama Barang", "Kategori", "Harga Jual (Rp)", "Jumlah Stok"]].copy()
        
        if not st.session_state.tabel_penjualan.empty:
            df_jual = st.session_state.tabel_penjualan.copy()
            df_jual["Jumlah"] = pd.to_numeric(df_jual["Jumlah"], errors='coerce').fillna(0)
            df_jual["Total Profit (Rp)"] = pd.to_numeric(df_jual["Total Profit (Rp)"], errors='coerce').fillna(0)
            
            rekap_per_barang = df_jual.groupby("Nama Barang", as_index=False).agg(
                Total_Terjual=("Jumlah", "sum"),
                Total_Profit_Kontribusi=("Total Profit (Rp)", "sum")
            )
            df_analisa = pd.merge(df_stok, rekap_per_barang, on="Nama Barang", how="left")
            df_analisa["Total_Terjual"] = df_analisa["Total_Terjual"].fillna(0).astype(int)
            df_analisa["Total_Profit_Kontribusi"] = df_analisa["Total_Profit_Kontribusi"].fillna(0)
        else:
            df_analisa = df_stok.copy()
            df_analisa["Total_Terjual"] = 0
            df_analisa["Total_Profit_Kontribusi"] = 0

        df_terlaris = df_analisa.sort_values(by=["Total_Terjual", "Total_Profit_Kontribusi"], ascending=False)
        
        col_kiri, col_kanan = st.columns(2)
        with col_kiri:
            st.markdown("### 🔥 Top 5 Produk Terlaris")
            top_5 = df_terlaris[df_terlaris["Total_Terjual"] > 0].head(5)
            if not top_5.empty:
                st.bar_chart(data=top_5.set_index("Nama Barang")["Total_Terjual"], color="#28a745")
                st.dataframe(top_5[["Nama Barang", "Total_Terjual", "Total_Profit_Kontribusi"]], use_container_width=True, hide_index=True)
            else:
                st.warning("Belum ada produk terjual.")

        with col_kanan:
            st.markdown("### 🐢 Produk Kurang Laku (Slow-Moving)")
            bottom_5 = df_analisa.sort_values(by="Total_Terjual", ascending=True).head(5)
            st.dataframe(bottom_5[["Nama Barang", "Total_Terjual", "Jumlah Stok", "Kategori"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.dataframe(df_terlaris, use_container_width=True, hide_index=True)

st.markdown("---")

# ==========================================
# BAGIAN BAWAH: RINGKASAN & TABEL STOK UTAMA
# ==========================================
st.subheader("📊 Ringkasan Nilai Aset & Inventaris Warung")

if not st.session_state.tabel_stok.empty:
    tabel_saat_ini = st.session_state.tabel_stok
    tabel_saat_ini["Harga Modal (Rp)"] = pd.to_numeric(tabel_saat_ini["Harga Modal (Rp)"], errors='coerce').fillna(0)
    tabel_saat_ini["Harga Jual (Rp)"] = pd.to_numeric(tabel_saat_ini["Harga Jual (Rp)"], errors='coerce').fillna(0)
    tabel_saat_ini["Jumlah Stok"] = pd.to_numeric(tabel_saat_ini["Jumlah Stok"], errors='coerce').fillna(0)
    
    # Hitung total nilai aset berdasarkan harga modal
    total_modal_aset = (tabel_saat_ini["Harga Modal (Rp)"] * tabel_saat_ini["Jumlah Stok"]).sum()
    total_potensi_penjualan = (tabel_saat_ini["Harga Jual (Rp)"] * tabel_saat_ini["Jumlah Stok"]).sum()
    potensi_profit_aset = total_potensi_penjualan - total_modal_aset
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Modal Inventaris", f"Rp {total_modal_aset:,.0f}".replace(",", "."))
    col2.metric("🏷️ Potensi Pendapatan", f"Rp {total_potensi_penjualan:,.0f}".replace(",", "."))
    col3.metric("💎 Potensi Profit Bersih", f"Rp {potensi_profit_aset:,.0f}".replace(",", "."))
    col4.metric("⚠️ Stok Menipis", f"{len(tabel_saat_ini[tabel_saat_ini['Jumlah Stok'] <= 3])} item")

    col_search, col_filter = st.columns(2)
    with col_search:
        kata_kunci = st.text_input("🔍 Cari Nama Barang:", placeholder="Ketik nama barang...")
    with col_filter:
        daftar_kategori = ["Semua Kategori"] + list(tabel_saat_ini["Kategori"].dropna().unique())
        kategori_pilihan = st.selectbox("📂 Filter Berdasarkan Kategori:", daftar_kategori)
    
    tabel_ditampilkan = tabel_saat_ini if kategori_pilihan == "Semua Kategori" else tabel_saat_ini[tabel_saat_ini["Kategori"] == kategori_pilihan]
    if kata_kunci:
        tabel_ditampilkan = tabel_ditampilkan[tabel_ditampilkan["Nama Barang"].astype(str).str.contains(kata_kunci, case=False, na=False)]

    tabel_terupdate = st.data_editor(tabel_ditampilkan, num_rows="dynamic", use_container_width=True, key="editor_stok")
    
    if not kata_kunci and kategori_pilihan == "Semua Kategori":
        st.session_state.tabel_stok = tabel_terupdate
    else:
        st.session_state.tabel_stok.update(tabel_terupdate)
    
    simpan_backup()
    
    st.download_button(
        label="📥 Download Cadangan Data Stok (.csv)",
        data=st.session_state.tabel_stok.to_csv(index=False).encode('utf-8'),
        file_name="stok_warung_backup.csv",
        mime="text/csv",
    )
else:
    st.info("Inventaris masih kosong. Silakan gunakan menu Restock untuk mulai mendata barang.")
  
