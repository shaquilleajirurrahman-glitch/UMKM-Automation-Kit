"""
sheets_client.py
------------------
Modul shared untuk semua operasi Google Sheets.
Dipakai oleh main_pipeline.py (dan bisa dipakai ulang oleh skrip lain).

Fungsi:
    connect_to_sheet()           -> autentikasi & buka spreadsheet
    write_to_sheet(ss, data_list) -> bulk insert data ke tab Data_Kompetitor
    write_log(ss, status, ...)    -> tulis 1 baris status eksekusi ke Log_Eksekusi
"""

from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1Al6QyTsCu-J76jNe2ju0PoGUBqDIxtc4FXHft_YR-is"  # ID Sheet native Anda (sudah terkonfirmasi jalan)
SHEET_TAB_DATA = "Data_Kompetitor"
SHEET_TAB_LOG = "Log_Eksekusi"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def connect_to_sheet():
    """Autentikasi via Service Account dan kembalikan objek spreadsheet."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)


def write_to_sheet(spreadsheet, data_list):
    """
    Tulis data hasil scraping ke tab Data_Kompetitor secara bulk (1 panggilan API).

    Args:
        spreadsheet: objek hasil connect_to_sheet().
        data_list (list[dict]): output scrape_data(), TANPA Tanggal_Check
                                 (timestamp ditambahkan satu kali di sini,
                                 berlaku untuk seluruh baris dalam batch ini).

    Returns:
        int: jumlah baris yang berhasil ditulis.

    Raises:
        ValueError: kalau data_list kosong -- caller (main_pipeline) wajib
                    menangani kasus ini SEBELUM memanggil fungsi ini,
                    karena ini bukan dianggap "error tak terduga".
    """
    if not data_list:
        raise ValueError("data_list kosong, tidak ada yang bisa ditulis.")

    worksheet = spreadsheet.worksheet(SHEET_TAB_DATA)

    # Satu timestamp untuk SELURUH batch -- bukan per-item.
    # Ini memastikan semua baris dalam satu eksekusi pipeline punya
    # waktu yang sama persis, memudahkan grouping/analisis nanti.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for item in data_list:
        rows.append([
            timestamp,
            item.get("Nama_Produk", ""),
            item.get("Harga_Kompetitor", ""),
            item.get("Harga_Toko_Saya", ""),
            item.get("Selisih", ""),
            item.get("Link_Produk", ""),
        ])

    # append_rows = SATU panggilan API untuk semua baris.
    # Penting: hindari loop append_row() per item -- itu N panggilan API
    # dan bisa kena rate limit kalau data sudah ratusan produk.
    # value_input_option="USER_ENTERED" agar angka & link tetap dikenali
    # sebagai number/link (bukan text mentah) -- ini penting supaya
    # Conditional Formatting (=$E2>0) di Sheet Anda tetap berfungsi benar.
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    return len(rows)


def write_log(spreadsheet, status, jumlah_produk=0, error_message=""):
    """
    Tulis satu baris status eksekusi ke tab Log_Eksekusi.
    Dipanggil baik saat sukses MAUPUN gagal -- jangan pernah dilewati.
    """
    try:
        worksheet = spreadsheet.worksheet(SHEET_TAB_LOG)
        log_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status,
            jumlah_produk,
            error_message,
        ]
        worksheet.append_row(log_row)
    except Exception as log_err:
        # Kalau menulis log pun gagal, minimal tampil di console --
        # jangan sampai exception di sini menutupi error asli yang
        # sedang ditangani oleh caller.
        print(f"⚠️  Gagal menulis log: {log_err}")