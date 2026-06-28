"""
fix_corrupted_links.py
------------------------
Skrip SEKALI PAKAI untuk memperbaiki kolom Link_Produk yang ter-overwrite
jadi teks literal '#ERROR!' akibat bug di Code.gs (lihat riwayat debugging
proyek ini -- processNewData() versi lama menimpa URL asli dengan teks
error saat membaca cell formula yang sedang gagal).

Strategi: scrape ulang books.toscrape.com untuk membangun mapping
{Nama_Produk: URL_asli}, lalu cari baris di Data_Kompetitor yang
Link_Produk-nya rusak (berisi '#ERROR!'), dan timpa dengan URL yang
benar berdasarkan kecocokan judul produk.

Jalankan SATU KALI saja. Setelah selesai dan dikonfirmasi, skrip ini
tidak perlu dijalankan lagi -- bukan bagian dari pipeline harian.
"""

from scrape_data import scrape_data
from sheets_client import connect_to_sheet, SHEET_TAB_DATA

CORRUPTED_MARKERS = ["#ERROR!", "#error!", ""]


def build_title_to_url_map():
    """Scrape ulang untuk mendapatkan mapping judul -> URL yang benar."""
    data = scrape_data(max_pages=1)
    return {item["Nama_Produk"]: item["Link_Produk"] for item in data}


def fix_corrupted_links():
    spreadsheet = connect_to_sheet()
    worksheet = spreadsheet.worksheet(SHEET_TAB_DATA)

    print("🔄 Scraping ulang untuk mendapatkan URL asli...")
    title_to_url = build_title_to_url_map()
    print(f"📚 Mapping siap: {len(title_to_url)} judul produk diketahui.\n")

    all_rows = worksheet.get_all_values()  # baris 1 = header

    fixed_count = 0
    not_found = []

    for row_idx, row in enumerate(all_rows[1:], start=2):
        if len(row) < 6:
            continue
        nama_produk = row[1]
        link_saat_ini = row[5]

        if link_saat_ini in CORRUPTED_MARKERS:
            url_benar = title_to_url.get(nama_produk)
            if url_benar:
                worksheet.update_cell(row_idx, 6, url_benar)  # kolom F = 6
                fixed_count += 1
                print(f"✅ Baris {row_idx} ('{nama_produk}') diperbaiki.")
            else:
                not_found.append((row_idx, nama_produk))

    print(f"\n🏁 Selesai. {fixed_count} baris berhasil diperbaiki.")
    if not_found:
        print(f"\n⚠️  {len(not_found)} baris TIDAK ditemukan mapping-nya (kemungkinan baris dummy test, bukan dari scraping):")
        for row_idx, nama in not_found:
            print(f"   - Baris {row_idx}: '{nama}'")
        print("\nIni wajar untuk baris seperti 'Produk Dummy Test', 'Contoh Buku Mahal', dll --")
        print("baris itu tidak berasal dari scraping asli, jadi perbaiki manual via Sheets")
        print("kalau memang masih dibutuhkan (URL aslinya: https://example.com/produk-dummy).")


if __name__ == "__main__":
    fix_corrupted_links()