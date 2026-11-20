from datetime import datetime
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pencatatan Toko Sederhana", layout="wide")
st.title("📦 Aplikasi Pencatatan & Kasir Toko Sederhana")

FILE_DATA = "data_toko.csv"
FILE_RIWAYAT = "riwayat_penjualan.csv"

KOLOM_TOKO = ["Nama Barang", "Harga (Rp)", "Stok"]
KOLOM_RIWAYAT = [
    "ID Transaksi",
    "Tanggal",
    "Waktu",
    "Nama Barang",
    "Harga Satuan (Rp)",
    "Jumlah",
    "Subtotal (Rp)",
]


def normalisasi_df_toko(df: pd.DataFrame) -> pd.DataFrame:
    df_bersih = df.copy()
    for col in KOLOM_TOKO:
        if col not in df_bersih.columns:
            df_bersih[col] = 0 if col != "Nama Barang" else ""
    df_bersih = df_bersih[KOLOM_TOKO].copy()
    df_bersih["Nama Barang"] = df_bersih["Nama Barang"].fillna("").astype(str).str.strip()
    df_bersih = df_bersih[df_bersih["Nama Barang"] != ""].reset_index(drop=True)
    df_bersih["Harga (Rp)"] = pd.to_numeric(df_bersih["Harga (Rp)"], errors="coerce").fillna(0)
    df_bersih["Stok"] = pd.to_numeric(df_bersih["Stok"], errors="coerce").fillna(0).astype(int)
    return df_bersih


def normalisasi_df_riwayat(df: pd.DataFrame) -> pd.DataFrame:
    df_bersih = df.copy()
    for col in KOLOM_RIWAYAT:
        if col not in df_bersih.columns:
            df_bersih[col] = None
    df_bersih = df_bersih[KOLOM_RIWAYAT].copy()
    df_bersih["Nama Barang"] = df_bersih["Nama Barang"].fillna("").astype(str).str.strip()
    df_bersih["Harga Satuan (Rp)"] = pd.to_numeric(
        df_bersih["Harga Satuan (Rp)"], errors="coerce"
    ).fillna(0)
    df_bersih["Jumlah"] = pd.to_numeric(df_bersih["Jumlah"], errors="coerce").fillna(0).astype(int)
    df_bersih["Subtotal (Rp)"] = pd.to_numeric(
        df_bersih["Subtotal (Rp)"], errors="coerce"
    ).fillna(0)
    return df_bersih


def muat_toko():
    """Memuat data stok toko dari CSV jika tersedia."""
    if os.path.exists(FILE_DATA):
        return normalisasi_df_toko(pd.read_csv(FILE_DATA))
    return pd.DataFrame(columns=KOLOM_TOKO)


def simpan_data():
    """Menyimpan data stok toko ke file CSV."""
    normalisasi_df_toko(st.session_state.tabel_toko).to_csv(FILE_DATA, index=False)


def muat_riwayat():
    """Memuat riwayat transaksi penjualan dari CSV jika tersedia."""
    if os.path.exists(FILE_RIWAYAT):
        return normalisasi_df_riwayat(pd.read_csv(FILE_RIWAYAT))
    return pd.DataFrame(columns=KOLOM_RIWAYAT)


def simpan_riwayat(df_riwayat):
    """Menyimpan riwayat transaksi penjualan ke file CSV."""
    normalisasi_df_riwayat(df_riwayat).to_csv(FILE_RIWAYAT, index=False)


if "tabel_toko" not in st.session_state:
    st.session_state.tabel_toko = muat_toko()

if "riwayat_penjualan" not in st.session_state:
    st.session_state.riwayat_penjualan = muat_riwayat()

if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

menu = st.sidebar.radio(
    "Pilih Menu:",
    [
        "📋 Kelola Stok Barang",
        "💰 Kasir & Penjualan",
        "📅 Riwayat Penjualan",
        "📂 Backup & Muat CSV",
        "📈 Ringkasan & Analisis",
    ],
)

# ==========================================
# MENU 1: KELOLA STOK BARANG
# ==========================================
if menu == "📋 Kelola Stok Barang":
    st.subheader("Tambah & Kelola Barang Toko")

    with st.form("form_tambah_barang", clear_on_submit=True):
        nama_barang = st.text_input("Nama Barang").strip()
        harga_barang = st.number_input("Harga Satuan (Rp)", min_value=0, step=500)
        jumlah_stok = st.number_input("Jumlah Stok", min_value=0, step=1)
        submitted = st.form_submit_button("💾 Simpan Barang")

        if submitted:
            if not nama_barang:
                st.warning("⚠️ Nama barang tidak boleh kosong.")
            else:
                tabel = st.session_state.tabel_toko
                if not tabel.empty and nama_barang in tabel["Nama Barang"].values:
                    idx = tabel["Nama Barang"] == nama_barang
                    stok_lama = int(tabel.loc[idx, "Stok"].values[0])
                    tabel.loc[idx, "Stok"] = stok_lama + int(jumlah_stok)
                    tabel.loc[idx, "Harga (Rp)"] = float(harga_barang)
                    st.success(f"✅ Stok '{nama_barang}' berhasil diperbarui!")
                else:
                    barang_baru = pd.DataFrame([
                        {
                            "Nama Barang": nama_barang,
                            "Harga (Rp)": float(harga_barang),
                            "Stok": int(jumlah_stok),
                        }
                    ])
                    st.session_state.tabel_toko = pd.concat(
                        [tabel, barang_baru], ignore_index=True
                    )
                    st.success(f"✅ Barang baru '{nama_barang}' berhasil ditambahkan!")
                simpan_data()
                st.rerun()

    st.markdown("### 📊 Daftar Inventaris & Total Nilai Stok")
    if not st.session_state.tabel_toko.empty:
        df_tampil = st.session_state.tabel_toko.copy()
        df_tampil["Harga (Rp)"] = pd.to_numeric(df_tampil["Harga (Rp)"], errors="coerce").fillna(0)
        df_tampil["Stok"] = pd.to_numeric(df_tampil["Stok"], errors="coerce").fillna(0).astype(int)
        df_tampil["Total Harga Stok (Rp)"] = df_tampil["Harga (Rp)"] * df_tampil["Stok"]

        total_semua_stok = float(df_tampil["Total Harga Stok (Rp)"].sum())
        total_unit_barang = int(df_tampil["Stok"].sum())

        col1, col2 = st.columns(2)
        col1.metric("💰 Total Nilai Seluruh Stok", f"Rp {total_semua_stok:,.0f}".replace(",", "."))
        col2.metric("📦 Total Unit Barang Tersedia", f"{total_unit_barang} pcs")

        tabel_edit = st.data_editor(
            df_tampil[["Nama Barang", "Harga (Rp)", "Stok", "Total Harga Stok (Rp)"]],
            num_rows="dynamic",
            disabled=["Total Harga Stok (Rp)"],
            use_container_width=True,
        )

        tabel_edit["Harga (Rp)"] = pd.to_numeric(tabel_edit["Harga (Rp)"], errors="coerce").fillna(0)
        tabel_edit["Stok"] = pd.to_numeric(tabel_edit["Stok"], errors="coerce").fillna(0).astype(int)
        tabel_edit["Total Harga Stok (Rp)"] = tabel_edit["Harga (Rp)"] * tabel_edit["Stok"]

        st.session_state.tabel_toko = tabel_edit[KOLOM_TOKO].copy()
        simpan_data()

        st.download_button(
            label="📥 Unduh Data Toko (.csv)",
            data=tabel_edit.to_csv(index=False).encode("utf-8"),
            file_name="data_toko.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada data barang. Silakan tambahkan barang di atas.")

# ==========================================
# MENU 2: KASIR MULTI-PRODUK (KERANJANG)
# ==========================================
elif menu == "💰 Kasir & Penjualan":
    st.subheader("🛒 Kasir Penjualan (Multi-Produk)")
    tabel = st.session_state.tabel_toko

    if tabel.empty:
        st.warning("Inventaris masih kosong. Tambahkan barang terlebih dahulu di menu Kelola Stok.")
    else:
        daftar_barang = tabel["Nama Barang"].tolist()

        with st.form("form_tambah_keranjang", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                pilihan_barang = st.selectbox("Pilih Produk", daftar_barang)
            with col2:
                jumlah_beli = st.number_input("Jumlah (pcs)", min_value=1, value=1, step=1)

            tambah_item = st.form_submit_button("➕ Masukkan ke Keranjang")

            if tambah_item:
                idx_barang = tabel["Nama Barang"] == pilihan_barang
                stok_tersedia = int(tabel.loc[idx_barang, "Stok"].values[0])
                harga_satuan = float(tabel.loc[idx_barang, "Harga (Rp)"].values[0])

                jumlah_di_keranjang = sum(
                    int(item["Jumlah"])
                    for item in st.session_state.keranjang
                    if item["Nama Barang"] == pilihan_barang
                )

                if jumlah_di_keranjang + int(jumlah_beli) > stok_tersedia:
                    st.error(
                        f"❌ Stok tidak cukup! Tersedia {stok_tersedia} pcs, di keranjang sudah {jumlah_di_keranjang} pcs."
                    )
                else:
                    sudah_ada = False
                    for item in st.session_state.keranjang:
                        if item["Nama Barang"] == pilihan_barang:
                            item["Jumlah"] = int(item["Jumlah"]) + int(jumlah_beli)
                            item["Subtotal (Rp)"] = float(item["Harga Satuan (Rp)"]) * int(item["Jumlah"])
                            sudah_ada = True
                            break

                    if not sudah_ada:
                        st.session_state.keranjang.append({
                            "Nama Barang": pilihan_barang,
                            "Harga Satuan (Rp)": harga_satuan,
                            "Jumlah": int(jumlah_beli),
                            "Subtotal (Rp)": harga_satuan * int(jumlah_beli),
                        })

                    st.success(f"✅ '{pilihan_barang}' ({jumlah_beli} pcs) masuk ke keranjang.")
                    st.rerun()

        st.markdown("### 🧾 Daftar Belanja Saat Ini")
        if st.session_state.keranjang:
            df_keranjang = pd.DataFrame(st.session_state.keranjang)
            st.dataframe(df_keranjang, use_container_width=True)

            total_transaksi = float(df_keranjang["Subtotal (Rp)"].sum())
            st.markdown(f"### 💵 Total Tagihan: **Rp {total_transaksi:,.0f}**".replace(",", "."))

            col_bayar, col_batal = st.columns(2)
            with col_bayar:
                if st.button("✅ Selesaikan Pembayaran & Potong Stok", type="primary"):
                    stok_aman = True
                    for item in st.session_state.keranjang:
                        stok_kini = int(
                            tabel.loc[tabel["Nama Barang"] == item["Nama Barang"], "Stok"].values[0]
                        )
                        if int(item["Jumlah"]) > stok_kini:
                            st.error(
                                f"❌ Stok '{item['Nama Barang']}' berubah/kurang (sisa {stok_kini} pcs)."
                            )
                            stok_aman = False
                            break

                    if stok_aman:
                        waktu_sekarang = datetime.now()
                        id_transaksi = waktu_sekarang.strftime("TRX-%Y%m%d-%H%M%S")
                        tanggal_str = waktu_sekarang.strftime("%Y-%m-%d")
                        jam_str = waktu_sekarang.strftime("%H:%M:%S")

                        baris_transaksi_baru = []
                        for item in st.session_state.keranjang:
                            idx = tabel["Nama Barang"] == item["Nama Barang"]
                            stok_kini = int(tabel.loc[idx, "Stok"].values[0])
                            jumlah_item = int(item["Jumlah"])
                            tabel.loc[idx, "Stok"] = stok_kini - jumlah_item

                            baris_transaksi_baru.append({
                                "ID Transaksi": id_transaksi,
                                "Tanggal": tanggal_str,
                                "Waktu": jam_str,
                                "Nama Barang": item["Nama Barang"],
                                "Harga Satuan (Rp)": float(item["Harga Satuan (Rp)"]),
                                "Jumlah": jumlah_item,
                                "Subtotal (Rp)": float(item["Subtotal (Rp)"]),
                            })

                        simpan_data()

                        df_baru = pd.DataFrame(baris_transaksi_baru, columns=KOLOM_RIWAYAT)
                        st.session_state.riwayat_penjualan = pd.concat(
                            [st.session_state.riwayat_penjualan, df_baru],
                            ignore_index=True,
                        )
                        simpan_riwayat(st.session_state.riwayat_penjualan)

                        st.session_state.keranjang = []
                        st.success(
                            f"✅ Transaksi `{id_transaksi}` selesai! Total dibayar: **Rp {total_transaksi:,.0f}**".replace(
                                ",", "."
                            )
                        )
                        st.rerun()

            with col_batal:
                if st.button("🗑️ Kosongkan Keranjang"):
                    st.session_state.keranjang = []
                    st.rerun()
        else:
            st.info("Keranjang masih kosong. Pilih produk di atas lalu klik *Masukkan ke Keranjang*.")

# ==========================================
# MENU 3: RIWAYAT PENJUALAN HARIAN
# ==========================================
elif menu == "📅 Riwayat Penjualan":
    st.subheader("📅 Rekap & Riwayat Penjualan Harian")
    df_log = st.session_state.riwayat_penjualan.copy()

    if not df_log.empty:
        tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
        daftar_tanggal = sorted(df_log["Tanggal"].dropna().unique().tolist(), reverse=True)
        default_idx = daftar_tanggal.index(tanggal_hari_ini) if tanggal_hari_ini in daftar_tanggal else 0

        tanggal_pilih = st.selectbox("Pilih Tanggal Laporan", daftar_tanggal, index=default_idx)
        df_harian = df_log[df_log["Tanggal"] == tanggal_pilih].copy()

        omzet_harian = float(
            pd.to_numeric(df_harian["Subtotal (Rp)"], errors="coerce").fillna(0).sum()
        )
        jumlah_struk = int(df_harian["ID Transaksi"].nunique())
        total_item_terjual = int(
            pd.to_numeric(df_harian["Jumlah"], errors="coerce").fillna(0).sum()
        )

        k1, k2, k3 = st.columns(3)
        k1.metric("💵 Omzet Harian", f"Rp {omzet_harian:,.0f}".replace(",", "."))
        k2.metric("🧾 Jumlah Transaksi", f"{jumlah_struk} struk")
        k3.metric("📦 Item Terjual", f"{total_item_terjual} pcs")

        st.dataframe(df_harian, use_container_width=True)

        st.download_button(
            label=f"📥 Unduh Riwayat ({tanggal_pilih}).csv",
            data=df_harian.to_csv(index=False).encode("utf-8"),
            file_name=f"penjualan_{tanggal_pilih}.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada transaksi yang tercatat di `riwayat_penjualan.csv`.")

# ==========================================
# MENU 4: BACKUP & MUAT ULANG CSV DARI HP
# ==========================================
elif menu == "📂 Backup & Muat CSV":
    st.subheader("📂 Simpan & Muat Ulang File CSV dari Penyimpanan HP")
    st.caption(
        "Unduh file CSV ke HP secara berkala sebagai arsip lokal, lalu unggah kembali di sini jika aplikasi baru di-restart."
    )

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 Unduh Stok Toko (data_toko.csv)",
            data=normalisasi_df_toko(st.session_state.tabel_toko).to_csv(index=False).encode("utf-8"),
            file_name=FILE_DATA,
            mime="text/csv",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            label="📥 Unduh Riwayat Penjualan (riwayat_penjualan.csv)",
            data=normalisasi_df_riwayat(st.session_state.riwayat_penjualan)
            .to_csv(index=False)
            .encode("utf-8"),
            file_name=FILE_RIWAYAT,
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### ⬆️ Muat Ulang Stok Barang (`data_toko.csv`) dari HP")
    file_stok_upload = st.file_uploader(
        "Pilih file CSV stok dari penyimpanan HP",
        type=["csv"],
        key="upload_stok_csv",
    )
    if file_stok_upload is not None:
        try:
            df_stok_baru = normalisasi_df_toko(pd.read_csv(file_stok_upload))
            st.dataframe(df_stok_baru.head(10), use_container_width=True)
            mode_stok = st.radio(
                "Mode pemuatan stok:",
                ["Timpa data stok saat ini", "Gabungkan / tambahkan dengan stok saat ini"],
                key="mode_stok_radio",
            )
            if st.button("✅ Terapkan Data Stok CSV", type="primary"):
                if mode_stok == "Timpa data stok saat ini":
                    st.session_state.tabel_toko = df_stok_baru
                else:
                    gabungan = pd.concat(
                        [st.session_state.tabel_toko, df_stok_baru], ignore_index=True
                    )
                    gabungan = gabungan.groupby("Nama Barang", as_index=False).agg({
                        "Harga (Rp)": "last",
                        "Stok": "sum",
                    })
                    st.session_state.tabel_toko = normalisasi_df_toko(gabungan)

                st.session_state.keranjang = []
                simpan_data()
                st.success("✅ Data stok toko berhasil dimuat dan disimpan!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Gagal membaca file CSV stok: {e}")

    st.markdown("---")
    st.markdown("### ⬆️ Muat Ulang Riwayat Penjualan (`riwayat_penjualan.csv`) dari HP")
    file_riwayat_upload = st.file_uploader(
        "Pilih file CSV riwayat penjualan dari penyimpanan HP",
        type=["csv"],
        key="upload_riwayat_csv",
    )
    if file_riwayat_upload is not None:
        try:
            df_riwayat_baru = normalisasi_df_riwayat(pd.read_csv(file_riwayat_upload))
            st.dataframe(df_riwayat_baru.head(10), use_container_width=True)
            mode_riwayat = st.radio(
                "Mode pemuatan riwayat:",
                ["Gabungkan (tanpa duplikat ID Transaksi & barang)", "Timpa seluruh riwayat saat ini"],
                key="mode_riwayat_radio",
            )
            if st.button("✅ Terapkan Riwayat Penjualan CSV", type="primary"):
                if mode_riwayat.startswith("Gabungkan"):
                    gabungan_log = pd.concat(
                        [st.session_state.riwayat_penjualan, df_riwayat_baru],
                        ignore_index=True,
                    )
                    gabungan_log = gabungan_log.drop_duplicates(
                        subset=["ID Transaksi", "Nama Barang", "Jumlah", "Subtotal (Rp)"],
                        keep="last",
                    ).reset_index(drop=True)
                    st.session_state.riwayat_penjualan = normalisasi_df_riwayat(gabungan_log)
                else:
                    st.session_state.riwayat_penjualan = df_riwayat_baru

                simpan_riwayat(st.session_state.riwayat_penjualan)
                st.success("✅ Riwayat penjualan berhasil dimuat dan disimpan!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Gagal membaca file CSV riwayat: {e}")

# ==========================================
# MENU 5: RINGKASAN & ANALISIS
# ==========================================
elif menu == "📈 Ringkasan & Analisis":
    st.subheader("📈 Ringkasan Stok & Penjualan")

    df_stok = st.session_state.tabel_toko.copy()
    df_log = st.session_state.riwayat_penjualan.copy()

    nilai_stok = 0.0
    if not df_stok.empty:
        harga = pd.to_numeric(df_stok["Harga (Rp)"], errors="coerce").fillna(0)
        stok = pd.to_numeric(df_stok["Stok"], errors="coerce").fillna(0)
        nilai_stok = float((harga * stok).sum())

    total_omzet = 0.0
    total_struk = 0
    if not df_log.empty:
        total_omzet = float(
            pd.to_numeric(df_log["Subtotal (Rp)"], errors="coerce").fillna(0).sum()
        )
        total_struk = int(df_log["ID Transaksi"].nunique())

    r1, r2, r3 = st.columns(3)
    r1.metric("💰 Nilai Stok Saat Ini", f"Rp {nilai_stok:,.0f}".replace(",", "."))
    r2.metric("💵 Total Omzet Tercatat", f"Rp {total_omzet:,.0f}".replace(",", "."))
    r3.metric("🧾 Total Struk Tercatat", f"{total_struk} transaksi")

    if not df_log.empty:
        st.markdown("### 🏆 Produk Terlaris (Berdasarkan Jumlah Terjual)")
        rekap_produk = (
            df_log.groupby("Nama Barang", as_index=False)
            .agg({"Jumlah": "sum", "Subtotal (Rp)": "sum"})
            .sort_values("Jumlah", ascending=False)
        )
        st.dataframe(rekap_produk, use_container_width=True)
    else:
        st.info("Belum ada data penjualan untuk dianalisis.")
