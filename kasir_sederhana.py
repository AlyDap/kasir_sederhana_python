import datetime
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# Modul untuk Generate PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


class Database:

    def __init__(self, db_name="kasir.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabel Produk
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS produk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                harga REAL NOT NULL,
                stok INTEGER NOT NULL
            )
        """
        )
        # Tabel Transaksi
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT NOT NULL,
                total_harga REAL NOT NULL
            )
        """
        )
	 # Tabel detail transaksi
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS detail_transaksi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaksi_id INTEGER,
                produk_id INTEGER,
                jumlah INTEGER,
                subtotal REAL,
                FOREIGN KEY(transaksi_id) REFERENCES transaksi(id),
                FOREIGN KEY(produk_id) REFERENCES produk(id)
            )
        """
        )
        self.conn.commit()

    def tambah_produk_awal(self):
        self.cursor.execute("SELECT COUNT(*) FROM produk")
        if self.cursor.fetchone()[0] == 0:
            produk_awal = [
                ("Minyak Goreng 1L", 18000, 20),
                ("Gula Pasir 1kg", 15000, 30),
                ("Beras 5kg", 65000, 15),
                ("Kopi Sachet", 2500, 100),
                ("Mie Instan", 3000, 80),
            ]
            self.cursor.executemany(
                "INSERT INTO produk (nama, harga, stok) VALUES (?, ?, ?)",
                produk_awal,
            )
            self.conn.commit()

    def ambil_semua_produk(self, keyword=""):
        if keyword:
            query = "SELECT * FROM produk WHERE nama LIKE ?"
            self.cursor.execute(query, (f"%{keyword}%",))
        else:
            self.cursor.execute("SELECT * FROM produk")
        return self.cursor.fetchall()

    def tambah_produk(self, nama, harga, stok):
        self.cursor.execute(
            "INSERT INTO produk (nama, harga, stok) VALUES (?, ?, ?)",
            (nama, harga, stok),
        )
        self.conn.commit()

    def update_produk(self, produk_id, nama, harga, stok):
        self.cursor.execute(
            "UPDATE produk SET nama = ?, harga = ?, stok = ? WHERE id = ?",
            (nama, harga, stok, produk_id),
        )
        self.conn.commit()

    def update_stok(self, produk_id, jumlah_beli):
        self.cursor.execute(
            "UPDATE produk SET stok = stok - ? WHERE id = ?",
            (jumlah_beli, produk_id),
        )
        self.conn.commit()

    def simpan_transaksi(self, total_harga, keranjang):
        tgl_sekarang = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO transaksi (tanggal, total_harga) VALUES (?, ?)",
            (tgl_sekarang, total_harga),
        )
        transaksi_id = self.cursor.lastrowid
        for item in keranjang:
        # item = (produk_id, nama, harga, jumlah, subtotal)
            self.cursor.execute(
                "INSERT INTO detail_transaksi (transaksi_id, produk_id, jumlah, subtotal) VALUES (?, ?, ?, ?)",
                (transaksi_id, item[0], item[3], item[4])
            )
            self.conn.commit()

    def ambil_laporan_harian(self, tgl_mulai, tgl_selesai):
        query = """
            SELECT id, tanggal, total_harga 
            FROM transaksi 
            WHERE date(tanggal) >= date(?) AND date(tanggal) <= date(?)
            ORDER BY tanggal DESC
        """
        self.cursor.execute(query, (tgl_mulai, tgl_selesai))
        return self.cursor.fetchall()

    def ambil_laporan_bulanan(self, tahun, bulan):
        format_bulan = f"{tahun}-{int(bulan):02d}"
        query = """
            SELECT id, tanggal, total_harga 
            FROM transaksi 
            WHERE strftime('%Y-%m', tanggal) = ?
            ORDER BY tanggal DESC
        """
        self.cursor.execute(query, (format_bulan,))
        return self.cursor.fetchall()

    def ambil_detail_laporan_harian(self, tgl_mulai, tgl_selesai, sort_by_item=False):
        order_clause = "p.id ASC, t.tanggal DESC" if sort_by_item else "t.tanggal DESC, t.id DESC"
        query = f"""
            SELECT t.id, t.tanggal, p.nama, p.harga, dt.jumlah, dt.subtotal, p.id
            FROM detail_transaksi dt
            JOIN transaksi t ON dt.transaksi_id = t.id
            JOIN produk p ON dt.produk_id = p.id
            WHERE date(t.tanggal) >= date(?) AND date(t.tanggal) <= date(?)
            ORDER BY {order_clause}
        """
        self.cursor.execute(query, (tgl_mulai, tgl_selesai))
        return self.cursor.fetchall()

    def ambil_detail_laporan_bulanan(self, tahun, bulan, sort_by_item=False):
        format_bulan = f"{tahun}-{int(bulan):02d}"
        order_clause = "p.id ASC, t.tanggal DESC" if sort_by_item else "t.tanggal DESC, t.id DESC"
        query = f"""
            SELECT t.id, t.tanggal, p.nama, p.harga, dt.jumlah, dt.subtotal, p.id
            FROM detail_transaksi dt
            JOIN transaksi t ON dt.transaksi_id = t.id
            JOIN produk p ON dt.produk_id = p.id
            WHERE strftime('%Y-%m', t.tanggal) = ?
            ORDER BY {order_clause}
        """
        self.cursor.execute(query, (format_bulan,))
        return self.cursor.fetchall()


class FormProdukDialog:
    """Popup Dialog untuk Tambah / Edit Produk"""

    def __init__(self, parent, title, nama="", harga="", stok=""):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry("300x220")
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self.result = None

        tk.Label(self.top, text="Nama Produk:").pack(
            anchor="w", padx=15, pady=(10, 0)
        )
        self.ent_nama = tk.Entry(self.top)
        self.ent_nama.pack(fill=tk.X, padx=15)
        self.ent_nama.insert(0, nama)

        tk.Label(self.top, text="Harga (Rp):").pack(
            anchor="w", padx=15, pady=(5, 0)
        )
        self.ent_harga = tk.Entry(self.top)
        self.ent_harga.pack(fill=tk.X, padx=15)
        self.ent_harga.insert(0, str(harga) if harga != "" else "")

        tk.Label(self.top, text="Stok:").pack(anchor="w", padx=15, pady=(5, 0))
        self.ent_stok = tk.Entry(self.top)
        self.ent_stok.pack(fill=tk.X, padx=15)
        self.ent_stok.insert(0, str(stok) if stok != "" else "")

        btn_frame = tk.Frame(self.top, pady=15)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame,
            text="Simpan",
            bg="#28a745",
            fg="white",
            width=10,
            command=self.simpan,
        ).pack(side=tk.LEFT, padx=15)
        tk.Button(
            btn_frame,
            text="Batal",
            bg="#dc3545",
            fg="white",
            width=10,
            command=self.top.destroy,
        ).pack(side=tk.RIGHT, padx=15)

    def simpan(self):
        nama = self.ent_nama.get().strip()
        try:
            harga = float(self.ent_harga.get())
            stok = int(self.ent_stok.get())
            if not nama or harga < 0 or stok < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error Input",
                "Mohon isi semua field dengan benar!",
                parent=self.top,
            )
            return

        self.result = (nama, harga, stok)
        self.top.destroy()


class LaporanWindow:
    """Jendela Laporan Penjualan Detail & Ekspor PDF"""

    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Laporan Penjualan Detail")
        self.top.geometry("900x550")
        self.top.transient(parent)
        self.top.grab_set()

        self.db = db
        self.data_laporan = []

        self.setup_ui()

    def setup_ui(self):
        # Frame Filter
        frame_filter = tk.LabelFrame(self.top, text=" Filter Laporan ", padx=10, pady=10)
        frame_filter.pack(fill=tk.X, padx=10, pady=5)

        self.jenis_filter = tk.StringVar(value="harian")
        self.var_sort_barang = tk.BooleanVar(value=False)

        rb_harian = tk.Radiobutton(
            frame_filter,
            text="Rentang Hari",
            variable=self.jenis_filter,
            value="harian",
            command=self.toggle_filter,
        )
        rb_harian.grid(row=0, column=0, sticky="w")

        rb_bulanan = tk.Radiobutton(
            frame_filter,
            text="Per Bulan",
            variable=self.jenis_filter,
            value="bulanan",
            command=self.toggle_filter,
        )
        rb_bulanan.grid(row=0, column=3, sticky="w", padx=(20, 0))

        # Checkbox Sort Barang
        cb_sort = tk.Checkbutton(
            frame_filter,
            text="Sort Barang (by ID)",
            variable=self.var_sort_barang,
            command=self.muat_laporan,
        )
        cb_sort.grid(row=0, column=5, sticky="e", padx=(20, 0))

        # Inputs Harian
        tgl_hari_ini = datetime.date.today().strftime("%Y-%m-%d")
        
        self.lbl_tgl_mulai = tk.Label(frame_filter, text="Mulai (YYYY-MM-DD):")
        self.lbl_tgl_mulai.grid(row=1, column=0, sticky="w", pady=5)
        self.ent_tgl_mulai = tk.Entry(frame_filter, width=12)
        self.ent_tgl_mulai.insert(0, tgl_hari_ini)
        self.ent_tgl_mulai.grid(row=1, column=1, padx=5)

        self.lbl_tgl_selesai = tk.Label(frame_filter, text="Selesai:")
        self.lbl_tgl_selesai.grid(row=1, column=2, sticky="w")
        self.ent_tgl_selesai = tk.Entry(frame_filter, width=12)
        self.ent_tgl_selesai.insert(0, tgl_hari_ini)
        self.ent_tgl_selesai.grid(row=1, column=3, padx=5)

        # Inputs Bulanan
        self.lbl_tahun = tk.Label(frame_filter, text="Tahun:")
        self.ent_tahun = tk.Entry(frame_filter, width=8)
        self.ent_tahun.insert(0, str(datetime.date.today().year))

        self.lbl_bulan = tk.Label(frame_filter, text="Bulan (1-12):")
        self.ent_bulan = tk.Entry(frame_filter, width=6)
        self.ent_bulan.insert(0, str(datetime.date.today().month))

        btn_tampilkan = tk.Button(
            frame_filter,
            text="Tampilkan",
            bg="#0275d8",
            fg="white",
            command=self.muat_laporan,
        )
        btn_tampilkan.grid(row=1, column=5, padx=15)

        # Tabel Laporan (Format Baru)
        columns = ("ID Transaksi", "Tanggal", "Nama Barang", "Harga", "Jumlah", "Subtotal")
        self.tree_laporan = ttk.Treeview(
            self.top, columns=columns, show="headings", height=12
        )
        
        self.tree_laporan.heading("ID Transaksi", text="ID Transaksi")
        self.tree_laporan.heading("Tanggal", text="Tanggal")
        self.tree_laporan.heading("Nama Barang", text="Nama Barang")
        self.tree_laporan.heading("Harga", text="Harga")
        self.tree_laporan.heading("Jumlah", text="Jumlah")
        self.tree_laporan.heading("Subtotal", text="Subtotal")

        self.tree_laporan.column("ID Transaksi", width=80, anchor="center")
        self.tree_laporan.column("Tanggal", width=180, anchor="center")
        self.tree_laporan.column("Nama Barang", width=180, anchor="w")
        self.tree_laporan.column("Harga", width=100, anchor="e")
        self.tree_laporan.column("Jumlah", width=60, anchor="center")
        self.tree_laporan.column("Subtotal", width=110, anchor="e")

        self.tree_laporan.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Bottom Frame
        frame_bottom = tk.Frame(self.top, padx=10, pady=10)
        frame_bottom.pack(fill=tk.X)

        self.lbl_total_omset = tk.Label(
            frame_bottom,
            text="Total Penjualan: Rp 0",
            font=("Arial", 12, "bold"),
            fg="#28a745",
        )
        self.lbl_total_omset.pack(side=tk.LEFT)

        btn_pdf = tk.Button(
            frame_bottom,
            text="Unduh / Cetak PDF",
            bg="#dc3545",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.export_pdf,
        )
        btn_pdf.pack(side=tk.RIGHT)

        self.toggle_filter()
        self.muat_laporan()

    def format_tanggal_indo(self, str_datetime):
        """Mengubah '2026-09-30 11:01:00' menjadi 'Rabu 30 Sept 2026 11:01'"""
        hari_map = {
            "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
            "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
        }
        bulan_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Juni",
            7: "Juli", 8: "Agust", 9: "Sept", 10: "Okt", 11: "Nov", 12: "Des"
        }
        try:
            dt = datetime.datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")
            nama_hari = hari_map.get(dt.strftime("%A"), dt.strftime("%A"))
            nama_bulan = bulan_map.get(dt.month, str(dt.month))
            return f"{nama_hari} {dt.day} {nama_bulan} {dt.year} {dt.strftime('%H:%M')}"
        except Exception:
            return str_datetime

    def toggle_filter(self):
        if self.jenis_filter.get() == "harian":
            self.lbl_tgl_mulai.grid()
            self.ent_tgl_mulai.grid()
            self.lbl_tgl_selesai.grid()
            self.ent_tgl_selesai.grid()

            self.lbl_tahun.grid_remove()
            self.ent_tahun.grid_remove()
            self.lbl_bulan.grid_remove()
            self.ent_bulan.grid_remove()
        else:
            self.lbl_tgl_mulai.grid_remove()
            self.ent_tgl_mulai.grid_remove()
            self.lbl_tgl_selesai.grid_remove()
            self.ent_tgl_selesai.grid_remove()

            self.lbl_tahun.grid(row=1, column=0, sticky="w", pady=5)
            self.ent_tahun.grid(row=1, column=1, padx=5)
            self.lbl_bulan.grid(row=1, column=2, sticky="w")
            self.ent_bulan.grid(row=1, column=3, padx=5)

    def muat_laporan(self):
        for item in self.tree_laporan.get_children():
            self.tree_laporan.delete(item)

        sort_barang = self.var_sort_barang.get()

        if self.jenis_filter.get() == "harian":
            tgl_mulai = self.ent_tgl_mulai.get().strip()
            tgl_selesai = self.ent_tgl_selesai.get().strip()
            self.data_laporan = self.db.ambil_detail_laporan_harian(tgl_mulai, tgl_selesai, sort_barang)
        else:
            tahun = self.ent_tahun.get().strip()
            bulan = self.ent_bulan.get().strip()
            self.data_laporan = self.db.ambil_detail_laporan_bulanan(tahun, bulan, sort_barang)

        total_omset = 0
        for row in self.data_laporan:
            # row: (id_transaksi, tanggal, nama_produk, harga, jumlah, subtotal, produk_id)
            tgl_formatted = self.format_tanggal_indo(row[1])
            subtotal = row[5]
            total_omset += subtotal

            self.tree_laporan.insert(
                "",
                tk.END,
                values=(
                    row[0],
                    tgl_formatted,
                    row[2],
                    f"Rp {row[3]:,.0f}",
                    row[4],
                    f"Rp {subtotal:,.0f}",
                ),
            )

        self.lbl_total_omset.config(text=f"Total Penjualan: Rp {total_omset:,.0f}")

    def export_pdf(self):
        if not self.data_laporan:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk dicetak!", parent=self.top)
            return

        nama_file = f"Laporan_Penjualan_Detail_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(nama_file, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("<b>LAPORAN PENJUALAN DETAIL</b>", styles["Title"]))
        elements.append(Spacer(1, 10))

        if self.jenis_filter.get() == "harian":
            periode_str = f"Periode: {self.ent_tgl_mulai.get()} s/d {self.ent_tgl_selesai.get()}"
        else:
            periode_str = f"Periode Bulan: {self.ent_bulan.get()} / {self.ent_tahun.get()}"
        
        elements.append(Paragraph(periode_str, styles["Normal"]))
        elements.append(Spacer(1, 12))

        table_data = [["ID Trans.", "Tanggal", "Nama Barang", "Harga", "Qty", "Subtotal"]]
        total_omset = 0

        for row in self.data_laporan:
            tgl_formatted = self.format_tanggal_indo(row[1])
            subtotal = row[5]
            total_omset += subtotal
            table_data.append([
                str(row[0]),
                tgl_formatted,
                str(row[2]),
                f"Rp {row[3]:,.0f}",
                str(row[4]),
                f"Rp {subtotal:,.0f}",
            ])

        table_data.append(["TOTAL PENJUALAN", "", "", "", "", f"Rp {total_omset:,.0f}"])

        t = Table(table_data, colWidths=[55, 140, 130, 75, 40, 80])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0275d8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (2, 1), (2, -1), "LEFT"),  # Nama barang rata kiri
                    ("ALIGN", (3, 1), (3, -1), "RIGHT"), # Harga rata kanan
                    ("ALIGN", (5, 1), (5, -1), "RIGHT"), # Subtotal rata kanan
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LINEBELOW", (0, -1), (-1, -1), 1.5, colors.black),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )

        elements.append(t)
        doc.build(elements)

        messagebox.showinfo(
            "PDF Berhasil dibuat",
            f"Laporan berhasil disimpan dengan nama file:\n{nama_file}",
            parent=self.top,
        )

class AplikasiKasir:

    def __init__(self, root):
        self.root = root
        self.root.title("Aplikasi Kasir Sederhana")
        self.root.geometry("950x620")

        self.db = Database()
        self.db.tambah_produk_awal()

        self.keranjang = []  # Menyimpan [(id, nama, harga, jumlah, subtotal)]

        self.setup_ui()
        self.muat_data_produk()

    def setup_ui(self):
        # ---------------- HEADER MENU ----------------
        frame_header = tk.Frame(self.root, bg="#343a40", padx=10, pady=8)
        frame_header.pack(fill=tk.X)

        lbl_title = tk.Label(
            frame_header,
            text="SISTEM KASIR POS",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#343a40",
        )
        lbl_title.pack(side=tk.LEFT)

        btn_laporan = tk.Button(
            frame_header,
            text="📊 Laporan Penjualan",
            bg="#6c757d",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.buka_laporan,
        )
        btn_laporan.pack(side=tk.RIGHT)

        # ---------------- FRAME KIRI: DAFTAR PRODUK ----------------
        frame_kiri = tk.Frame(self.root, padx=10, pady=10)
        frame_kiri.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            frame_kiri, text="Daftar Produk", font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))

        # Filter / Cari Produk
        frame_cari = tk.Frame(frame_kiri)
        frame_cari.pack(fill=tk.X, pady=(0, 5))

        tk.Label(frame_cari, text="Cari Produk:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_cari = tk.Entry(frame_cari)
        self.entry_cari.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_cari.bind("<KeyRelease>", lambda e: self.muat_data_produk())

        # Tabel Produk
        columns_produk = ("ID", "Nama Produk", "Harga", "Stok")
        self.tree_produk = ttk.Treeview(
            frame_kiri, columns=columns_produk, show="headings", height=12
        )
        for col in columns_produk:
            self.tree_produk.heading(col, text=col)
            self.tree_produk.column(col, width=70, anchor="center")
        self.tree_produk.column("Nama Produk", width=150, anchor="w")
        self.tree_produk.pack(fill=tk.BOTH, expand=True)

        # Tombol Kelola Produk
        frame_kelola = tk.Frame(frame_kiri, pady=5)
        frame_kelola.pack(fill=tk.X)

        btn_tambah_produk = tk.Button(
            frame_kelola,
            text="+ Produk Baru",
            bg="#17a2b8",
            fg="white",
            command=self.tambah_produk_dialog,
        )
        btn_tambah_produk.pack(side=tk.LEFT, padx=(0, 5))

        btn_edit_produk = tk.Button(
            frame_kelola,
            text="Edit Produk",
            bg="#ffc107",
            fg="black",
            command=self.edit_produk_dialog,
        )
        btn_edit_produk.pack(side=tk.LEFT)

        # Panel Input Jumlah Beli
        frame_input = tk.Frame(frame_kiri, pady=10)
        frame_input.pack(fill=tk.X)

        tk.Label(frame_input, text="Jumlah Beli:").pack(side=tk.LEFT, padx=5)
        self.entry_jumlah = tk.Entry(frame_input, width=8)
        self.entry_jumlah.insert(0, "1")
        self.entry_jumlah.pack(side=tk.LEFT, padx=5)

        btn_tambah_keranjang = tk.Button(
            frame_input,
            text="+ ke Keranjang",
            bg="#28a745",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.tambah_ke_keranjang,
        )
        btn_tambah_keranjang.pack(side=tk.LEFT, padx=10)

        # ---------------- FRAME KANAN: KERANJANG & PEMBAYARAN ----------------
        frame_kanan = tk.Frame(self.root, padx=10, pady=10)
        frame_kanan.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            frame_kanan, text="Keranjang Belanja", font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))

        columns_keranjang = ("Nama", "Harga", "Jumlah", "Subtotal")
        self.tree_keranjang = ttk.Treeview(
            frame_kanan, columns=columns_keranjang, show="headings", height=12
        )
        for col in columns_keranjang:
            self.tree_keranjang.heading(col, text=col)
            self.tree_keranjang.column(col, width=85, anchor="center")
        self.tree_keranjang.column("Nama", width=120, anchor="w")
        self.tree_keranjang.pack(fill=tk.BOTH, expand=True)

        # Tombol Hapus Produk dari Keranjang
        btn_hapus_keranjang = tk.Button(
            frame_kanan,
            text="Hapus Item Pilihan",
            bg="#dc3545",
            fg="white",
            command=self.hapus_dari_keranjang,
        )
        btn_hapus_keranjang.pack(anchor="e", pady=5)

        # Total dan Tombol Bayar
        self.lbl_total = tk.Label(
            frame_kanan,
            text="Total: Rp 0",
            font=("Arial", 14, "bold"),
            fg="#d9534f",
        )
        self.lbl_total.pack(pady=5)

        btn_bayar = tk.Button(
            frame_kanan,
            text="Proses Transaksi",
            font=("Arial", 11, "bold"),
            bg="#0275d8",
            fg="white",
            height=2,
            command=self.proses_bayar,
        )
        btn_bayar.pack(fill=tk.X, pady=5)

    def muat_data_produk(self):
        keyword = self.entry_cari.get().strip()
        for item in self.tree_produk.get_children():
            self.tree_produk.delete(item)

        produk_list = self.db.ambil_semua_produk(keyword)
        for p in produk_list:
            self.tree_produk.insert(
                "",
                tk.END,
                values=(p[0], p[1], f"Rp {p[2]:,.0f}", p[3]),
            )

    def tambah_produk_dialog(self):
        dialog = FormProdukDialog(self.root, "Tambah Produk Baru")
        self.root.wait_window(dialog.top)

        if dialog.result:
            nama, harga, stok = dialog.result
            self.db.tambah_produk(nama, harga, stok)
            messagebox.showinfo("Sukses", f"Produk '{nama}' berhasil ditambahkan!")
            self.muat_data_produk()

    def edit_produk_dialog(self):
        selected_item = self.tree_produk.selection()
        if not selected_item:
            messagebox.showwarning("Peringatan", "Pilih produk yang ingin di-edit!")
            return

        produk_values = self.tree_produk.item(selected_item)["values"]
        p_id = produk_values[0]
        nama_lama = produk_values[1]
        harga_lama = float(str(produk_values[2]).replace("Rp ", "").replace(",", ""))
        stok_lama = int(produk_values[3])

        dialog = FormProdukDialog(
            self.root,
            "Edit Produk",
            nama=nama_lama,
            harga=harga_lama,
            stok=stok_lama,
        )
        self.root.wait_window(dialog.top)

        if dialog.result:
            nama, harga, stok = dialog.result
            self.db.update_produk(p_id, nama, harga, stok)
            messagebox.showinfo("Sukses", f"Produk '{nama}' berhasil diperbarui!")
            self.muat_data_produk()

    def tambah_ke_keranjang(self):
        selected_item = self.tree_produk.selection()
        if not selected_item:
            messagebox.showwarning("Peringatan", "Pilih produk terlebih dahulu!")
            return

        try:
            jumlah_input = int(self.entry_jumlah.get())
            if jumlah_input <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error", "Masukkan jumlah beli yang valid (angka > 0)."
            )
            return

        produk_values = self.tree_produk.item(selected_item)["values"]
        produk_id = produk_values[0]
        nama = produk_values[1]
        harga = float(str(produk_values[2]).replace("Rp ", "").replace(",", ""))
        stok_tersedia = int(produk_values[3])

        # Hitung jumlah total jika produk sudah ada di keranjang
        jumlah_di_keranjang = sum(
            item[3] for item in self.keranjang if item[0] == produk_id
        )
        if (jumlah_di_keranjang + jumlah_input) > stok_tersedia:
            messagebox.showerror(
                "Stok Kurang",
                f"Stok tidak mencukupi! Stok tersisa: {stok_tersedia}",
            )
            return

        # Cek apakah produk sudah ada di keranjang -> perbarui jumlahnya
        ditemukan = False
        for idx, item in enumerate(self.keranjang):
            if item[0] == produk_id:
                jumlah_baru = item[3] + jumlah_input
                subtotal_baru = harga * jumlah_baru
                self.keranjang[idx] = (
                    produk_id,
                    nama,
                    harga,
                    jumlah_baru,
                    subtotal_baru,
                )
                ditemukan = True
                break

        if not ditemukan:
            subtotal = harga * jumlah_input
            self.keranjang.append(
                (produk_id, nama, harga, jumlah_input, subtotal)
            )

        self.muat_ulang_keranjang_ui()

    def hapus_dari_keranjang(self):
        selected_item = self.tree_keranjang.selection()
        if not selected_item:
            messagebox.showwarning(
                "Peringatan", "Pilih item di keranjang yang ingin dihapus!"
            )
            return

        index_pilihan = self.tree_keranjang.index(selected_item[0])
        del self.keranjang[index_pilihan]
        self.muat_ulang_keranjang_ui()

    def muat_ulang_keranjang_ui(self):
        for item in self.tree_keranjang.get_children():
            self.tree_keranjang.delete(item)

        for item in self.keranjang:
            _, nama, harga, jumlah, subtotal = item
            self.tree_keranjang.insert(
                "",
                tk.END,
                values=(
                    nama,
                    f"Rp {harga:,.0f}",
                    jumlah,
                    f"Rp {subtotal:,.0f}",
                ),
            )
        self.update_total()

    def update_total(self):
        total = sum(item[4] for item in self.keranjang)
        self.lbl_total.config(text=f"Total: Rp {total:,.0f}")

    def proses_bayar(self):
        if not self.keranjang:
            messagebox.showwarning("Peringatan", "Keranjang masih kosong!")
            return

        total_harga = sum(item[4] for item in self.keranjang)

        self.db.simpan_transaksi(total_harga, self.keranjang)

        for item in self.keranjang:
            p_id, _, _, jumlah, _ = item
            self.db.update_stok(p_id, jumlah)

        messagebox.showinfo(
            "Berhasil",
            f"Transaksi Berhasil!\nTotal Pembayaran: Rp {total_harga:,.0f}",
        )

        self.keranjang.clear()
        self.muat_ulang_keranjang_ui()
        self.muat_data_produk()

    def buka_laporan(self):
        LaporanWindow(self.root, self.db)


if __name__ == "__main__":
    root = tk.Tk()
    app = AplikasiKasir(root)
    root.mainloop()