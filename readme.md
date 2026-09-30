# Aplikasi Kasir Sederhana (Python POS System)

Aplikasi kasir berbasis Desktop GUI menggunakan Python, Tkinter, SQLite3, dan ReportLab untuk pembuatan laporan penjualan berformat PDF.

---

## 📋 Fitur Utama
- **Manajemen Produk:** Tambah, edit, cari, dan update stok produk secara otomatis.
- **Transaksi Kasir:** Perhitungan total belanja otomatis dan validasi stok.
- **Laporan Penjualan:** Filter laporan berdasarkan rentang hari atau bulan.
- **Cetak PDF:** Ekspor laporan penjualan ke dalam file dokumen PDF.

---

## 🛠️ Persyaratan & Instalasi

### 1. Unduh dan Instal Python
Aplikasi ini membutuhkan **Python versi 3.8** atau yang lebih baru.

#### 🔹 Windows:
1. Unduh installer resmi dari [python.org/downloads](https://www.python.org/downloads/).
2. Jalankan file `.exe` yang sudah diunduh.
3. ⚠️ **PENTING:** Pastikan Anda menyentang opsi **"Add python.exe to PATH"** di bagian bawah jendela installer sebelum menekan tombol *Install Now*.
4. Buka **Command Prompt (cmd)** dan ketik perintah berikut untuk memastikan Python sudah terinstal:
   ```bash
   python --version
   ```

#### 🔹 macOS:
1. Unduh installer dari [python.org/downloads](https://www.python.org/downloads/) atau gunakan Homebrew:
   ```bash
   brew install python
   ```

#### 🔹 Linux (Ubuntu/Debian):
1. Jalankan perintah terminal berikut:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-tk
   ```

---

### 2. Informasi Mengenai SQLite3
> 💡 **Catatan:** Anda **TIDAK PERLU** mengunduh atau menginstal database SQLite3 secara terpisah. Module `sqlite3` sudah menjadi pustaka bawaan (*built-in library*) dari standar Python.

---

### 3. Instal Dependencies (Pustaka Tambahan)

Aplikasi ini menggunakan modul `reportlab` untuk membuat laporan PDF dan `tkinter` untuk antarmuka GUI.

Buka terminal / Command Prompt (cmd) di folder proyek ini, lalu jalankan perintah berikut:

```bash
pip install reportlab
```

---

## 🚀 Cara Menjalankan Aplikasi

1. Buka Terminal / Command Prompt / PowerShell.
2. Masuk ke direktori folder proyek:
   ```bash
   cd "D:\Joki\program py\kasir sederhana"
   ```
3. Jalankan skrip Python:
   ```bash
   python kasir_sederhana.py
   ```

---

## 📂 Struktur File
```text
kasir_sederhana/
│
├── kasir_sederhana.py              # File utama aplikasi
├── kasir.db                        # Database SQLite (otomatis dibuat saat run)
├── .gitignore                      # Mengabaikan file laporan PDF
└── README.md                       # Dokumentasi proyek
```