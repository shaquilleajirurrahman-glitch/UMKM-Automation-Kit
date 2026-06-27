"""
test_sheets_connection.py
--------------------------
Tujuan: Menguji autentikasi Service Account ke Google Sheets API
dan menulis 1 baris data dummy + 1 baris log eksekusi.

Sebelum menjalankan ini, pastikan:
1. credentials.json sudah ada di folder yang sama dengan skrip ini.
2. Google Sheet sudah dibuat, punya tab 'Data_Kompetitor' dan 'Log_Eksekusi'.
3. Sheet sudah di-share (akses Editor) ke email yang ada di field
   "client_email" pada credentials.json.
4. SPREADSHEET_ID di bawah sudah diisi sesuai ID sheet Anda.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ====== KONFIGURASI — SESUAIKAN INI ======
CREDENTIALS_FILE = "credentials.json"
SPREADSHEET_ID = "1Al6QyTsCu-J76jNe2ju0PoGUBqDIxtc4FXHft_YR-is"  # hanya ID, bukan URL lengkap
SHEET_TAB_DATA = "Data_Kompetitor"
SHEET_TAB_LOG = "Log_Eksekusi"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def print_diagnostic_info():
    """Tampilkan info kunci untuk debugging sebelum mencoba connect."""
    import json
    with open(CREDENTIALS_FILE, "r") as f:
        cred_data = json.load(f)
    print("---- DIAGNOSTIK ----")
    print(f"Service account email : {cred_data.get('client_email')}")
    print(f"Spreadsheet ID dipakai: {SPREADSHEET_ID}")
    print("---------------------")
    print(">> Pastikan Sheet sudah di-share (akses Editor) ke email di atas.")
    print(">> Pastikan Spreadsheet ID di atas SAMA dengan yang ada di URL sheet Anda.")
    print()


def connect_to_sheet():
    """Autentikasi via Service Account dan kembalikan objek spreadsheet."""
    print_diagnostic_info()
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet


def write_dummy_row(spreadsheet):
    """Tulis 1 baris data dummy ke tab Data_Kompetitor."""
    worksheet = spreadsheet.worksheet(SHEET_TAB_DATA)
    dummy_row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Tanggal_Check
        "Produk Dummy Test",                            # Nama_Produk
        15000,                                           # Harga_Kompetitor
        14000,                                           # Harga_Toko_Saya
        1000,                                             # Selisih
        "https://example.com/produk-dummy",              # Link_Produk
    ]
    worksheet.append_row(dummy_row)
    return dummy_row


def write_log(spreadsheet, status, jumlah_produk=0, error_message=""):
    """Tulis status eksekusi ke tab Log_Eksekusi (selalu dipanggil, sukses/gagal)."""
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
        # Kalau menulis log pun gagal, minimal tampilkan di console
        print(f"⚠️  Gagal menulis log: {log_err}")


def main():
    spreadsheet = None
    try:
        print("🔄 Menghubungkan ke Google Sheets...")
        spreadsheet = connect_to_sheet()
        print("✅ Autentikasi berhasil.")

        print("🔄 Menulis baris dummy...")
        dummy_row = write_dummy_row(spreadsheet)
        print(f"✅ Berhasil menulis baris dummy: {dummy_row}")

        write_log(spreadsheet, status="SUCCESS", jumlah_produk=1)
        print("✅ Log eksekusi tercatat. Tes selesai.")

    except FileNotFoundError:
        msg = f"credentials.json tidak ditemukan di folder ini."
        print(f"❌ ERROR: {msg}")
    except gspread.exceptions.SpreadsheetNotFound:
        msg = "Spreadsheet tidak ditemukan. Cek SPREADSHEET_ID, atau pastikan sheet sudah di-share ke service account."
        print(f"❌ ERROR: {msg}")
        if spreadsheet is None:
            pass  # tidak bisa tulis log karena koneksi gagal total
    except gspread.exceptions.WorksheetNotFound as e:
        msg = f"Tab/worksheet tidak ditemukan: {e}"
        print(f"❌ ERROR: {msg}")
        if spreadsheet:
            write_log(spreadsheet, status="FAILED", error_message=msg)
    except Exception as e:
        msg = f"Error tidak terduga: {e}"
        print(f"❌ ERROR: {msg}")
        if spreadsheet:
            write_log(spreadsheet, status="FAILED", error_message=msg)


if __name__ == "__main__":
    main()