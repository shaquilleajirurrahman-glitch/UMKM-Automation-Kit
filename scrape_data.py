"""
scrape_data.py
----------------
Modul untuk scraping data buku dari books.toscrape.com sebagai
simulasi data kompetitor untuk UMKM Automated Growth Kit.

Kontrak output (sesuai skema Data_Kompetitor):
    Nama_Produk      -> Judul buku
    Harga_Kompetitor -> Harga buku, sudah dibersihkan jadi float
    Harga_Toko_Saya  -> Nilai dummy/hardcoded (lihat TODO di bawah)
    Selisih          -> Harga_Kompetitor - Harga_Toko_Saya
    Link_Produk      -> URL absolut ke halaman detail buku

Catatan: Tanggal_Check TIDAK dihasilkan di sini. Timestamp
ditambahkan satu kali per batch saat data ditulis ke Sheet
(tanggung jawab fungsi write_to_sheet, bukan scrape_data),
supaya semua baris dalam satu eksekusi punya waktu yang konsisten.
"""

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL_TEMPLATE = "https://books.toscrape.com/catalogue/page-{}.html"

# TODO: Ini adalah nilai SIMULASI, bukan data riil toko Anda.
# Ganti dengan logika nyata (misal: lookup dari database produk Anda)
# saat sistem ini dipakai untuk produk UMKM yang sebenarnya.
HARGA_TOKO_SAYA_DUMMY = 30.00

REQUEST_TIMEOUT = 10  # detik
DELAY_BETWEEN_PAGES = 1.0  # detik, sopan terhadap server

# Beberapa server menolak User-Agent default python-requests (terdeteksi sebagai bot).
# Header ini membuat request terlihat seperti browser biasa.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def clean_price(price_text):
    """
    Bersihkan simbol mata uang dan karakter non-numerik dari teks harga.
    '£51.77' -> 51.77
    'Â£51.77' (encoding rusak) -> 51.77 (tetap aman karena regex strip semua non-digit)

    Return None kalau hasil tidak bisa dikonversi ke float.
    """
    if not price_text:
        return None
    cleaned = re.sub(r"[^\d.]", "", price_text)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _scrape_single_page(page_num):
    """
    Scrape satu halaman katalog. Return (list_produk, ada_halaman_berikutnya).
    list_produk kosong [] kalau halaman gagal diakses atau tidak ada produk.
    """
    url = CATALOGUE_URL_TEMPLATE.format(page_num)

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout saat mengakses halaman {page_num}. Melewati.")
        return [], False
    except requests.exceptions.HTTPError as e:
        # Halaman tidak ada (misal sudah lewat halaman terakhir) -> berhenti normal
        print(f"ℹ️  Halaman {page_num} tidak tersedia ({e}). Pagination berhenti.")
        return [], False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Gagal mengakses halaman {page_num}: {e}")
        return [], False

    soup = BeautifulSoup(response.content, "html.parser")
    book_elements = soup.find_all("article", class_="product_pod")

    if not book_elements:
        print(f"ℹ️  Tidak ada produk di halaman {page_num}. Pagination berhenti.")
        return [], False

    products = []
    for book in book_elements:
        try:
            title_tag = book.find("h3").find("a")
            nama_produk = title_tag["title"].strip()

            relative_link = title_tag["href"]
            link_produk = urljoin(url, relative_link)

            price_tag = book.find("p", class_="price_color")
            harga_kompetitor = clean_price(price_tag.text if price_tag else None)

            if harga_kompetitor is None:
                print(f"⚠️  Lewati '{nama_produk}': harga tidak bisa diparse.")
                continue

            selisih = round(harga_kompetitor - HARGA_TOKO_SAYA_DUMMY, 2)

            products.append({
                "Nama_Produk": nama_produk,
                "Harga_Kompetitor": harga_kompetitor,
                "Harga_Toko_Saya": HARGA_TOKO_SAYA_DUMMY,
                "Selisih": selisih,
                "Link_Produk": link_produk,
            })

        except (AttributeError, KeyError, TypeError) as e:
            # Satu item gagal di-parse (struktur HTML tak terduga) -> lewati,
            # jangan sampai satu item rusak menggagalkan seluruh batch.
            print(f"⚠️  Lewati 1 item karena struktur HTML tidak sesuai: {e}")
            continue

    return products, True


def scrape_data(max_pages=1, delay=DELAY_BETWEEN_PAGES):
    """
    Scrape data buku dari books.toscrape.com untuk beberapa halaman katalog.

    Args:
        max_pages (int): jumlah halaman katalog yang di-scrape (1 halaman ≈ 20 buku).
        delay (float): jeda antar request halaman, dalam detik.

    Returns:
        list[dict]: daftar produk. List kosong [] jika scraping gagal total
                    (bukan exception -> caller wajib cek len() == 0).
    """
    all_products = []

    for page_num in range(1, max_pages + 1):
        products, should_continue = _scrape_single_page(page_num)
        all_products.extend(products)

        if not should_continue:
            break

        if page_num < max_pages:
            time.sleep(delay)

    return all_products


if __name__ == "__main__":
    print("🔄 Memulai scraping dari books.toscrape.com...")
    data = scrape_data(max_pages=1)

    if not data:
        print("❌ Tidak ada data yang berhasil di-scrape.")
    else:
        print(f"✅ Total {len(data)} produk berhasil di-scrape.\n")
        for item in data[:5]:
            print(item)
        if len(data) > 5:
            print(f"... dan {len(data) - 5} produk lainnya.")