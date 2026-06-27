"""
main_pipeline.py
------------------
Orkestrator utama UMKM Automated Growth Kit.

Alur:
    1. Connect ke Google Sheets
    2. Scrape data kompetitor
    3. Tulis data ke tab Data_Kompetitor (kalau ada hasil)
    4. Tulis status ke tab Log_Eksekusi (SELALU -- sukses ATAU gagal)

Catatan penting:
    scrape_data() mengembalikan list KOSONG (bukan exception) kalau
    scraping gagal total. Karena itu, kasus "list kosong" ditangani
    SECARA EKSPLISIT dengan `if not data`, terpisah dari blok
    try-except yang menangani exception tak terduga lainnya.
    Kalau ini tidak ditangani terpisah, pipeline akan terlihat
    "sukses" walau sebenarnya tidak ada data yang ditulis.
"""

from scrape_data import scrape_data
from sheets_client import connect_to_sheet, write_log, write_to_sheet


def main():
    print("=" * 50)
    print("UMKM Automated Growth Kit — Pipeline Eksekusi")
    print("=" * 50)

    spreadsheet = None

    try:
        # ---- 1. Connect ----
        print("🔄 [1/3] Menghubungkan ke Google Sheets...")
        spreadsheet = connect_to_sheet()
        print("✅ Koneksi berhasil.")

        # ---- 2. Scrape ----
        print("🔄 [2/3] Mengambil data kompetitor...")
        data = scrape_data(max_pages=1)

        if not data:
            # Bukan exception -- scraping "berhasil dijalankan" tapi
            # hasilnya nihil. Ini WAJIB dicatat sebagai FAILED, bukan
            # dilewati diam-diam.
            error_msg = (
                "Scraping menghasilkan 0 produk "
                "(kemungkinan situs down atau struktur HTML berubah)."
            )
            print(f"❌ {error_msg}")
            write_log(spreadsheet, status="FAILED", jumlah_produk=0, error_message=error_msg)
            return

        print(f"✅ {len(data)} produk berhasil di-scrape.")

        # ---- 3. Write ----
        print("🔄 [3/3] Menulis data ke Google Sheets...")
        jumlah_ditulis = write_to_sheet(spreadsheet, data)
        print(f"✅ {jumlah_ditulis} baris berhasil ditulis ke '{spreadsheet.title}'.")

        write_log(spreadsheet, status="SUCCESS", jumlah_produk=jumlah_ditulis)
        print("✅ Pipeline selesai dengan sukses.")

    except FileNotFoundError:
        # credentials.json tidak ada -- gagal total di awal,
        # tidak ada spreadsheet object untuk menulis log.
        print("❌ ERROR FATAL: credentials.json tidak ditemukan.")

    except Exception as e:
        msg = f"Pipeline gagal: {e}"
        print(f"❌ ERROR: {msg}")
        if spreadsheet:
            write_log(spreadsheet, status="FAILED", error_message=msg)
        else:
            print("⚠️  Tidak bisa menulis log -- koneksi ke Sheet juga gagal.")


if __name__ == "__main__":
    main()