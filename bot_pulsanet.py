# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet.py
# Developer: frd009
# Versi: 16.17 (Professional Photo & Album Downloader)
#
# CHANGELOG v16.17:
# - ADD (PROFESSIONAL): Logika caption yang disempurnakan. Jika mengunduh
#   dari album/carousel, bot akan mencoba menggunakan judul individual
#   file (jika ada) dan merujuk ke judul album utama.
# - FIX (PROFESSIONAL): Memperbaiki logika deteksi file secara total untuk
#   menangani postingan multi-foto (carousel/album) dengan andal.
# - FIX (PROFESSIONAL): Logika sekarang memeriksa `_filename` dan `filepath`
#   di *setiap* item di dalam `info_dict['entries']`, memastikan
#   *semua* foto/video dari carousel ditemukan dan dikirim,
#   tidak hanya file pertama.
#
# CHANGELOG v16.16:
# - UPDATE (PROFESSIONAL): Memastikan SEMUA `DownloadError` (bukan hanya error
#   autentikasi) dari yt-dlp di dalam `handle_media_download`
#   dikirimkan sebagai log ke Admin, sesuai permintaan.
# ... (Changelog v16.15 dipertahankan)
# ============================================

import os
import re
import html
import warnings
import random
import io
import asyncio
import logging
import httpx
import traceback
import base64
import signal
import sys
import string
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# --- Import library baru ---
import qrcode
from PIL import Image
import yt_dlp
import phonenumbers
from phonenumbers import carrier, geocoder, phonenumberutil
import pycountry

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, RetryAfter, BadRequest, TimedOut
from telegram.request import HTTPXRequest

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Menghilangkan peringatan 'pkg_resources is deprecated'
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# ==============================================================================
# ⚙️ KONFIGURASI & VARIABEL GLOBAL
# ==============================================================================
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")
MAX_MESSAGES_TO_TRACK = 50
MAX_MESSAGES_TO_DELETE_PER_BATCH = 30
CHROME_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
MAX_UPLOAD_FILE_SIZE_MB = 300 # New maximum upload size in MB
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

# --- File Cookie ---
YOUTUBE_COOKIE_FILE = 'youtube_cookies.txt'
GENERIC_COOKIE_FILE = 'generic_cookies.txt'

# --- Graceful Shutdown ---
bot_application = None

def signal_handler(sig, frame):
    """
    Handler untuk graceful shutdown saat Ctrl+C atau SIGTERM.
    Memastikan bot stop dengan benar sebelum exit.
    """
    print("\n\n🛑 Menerima signal shutdown...")
    print("🔄 Menghentikan bot dengan aman...")
    
    if bot_application:
        try:
            # Stop bot dengan benar
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Menggunakan bot_application.stop() dan shutdown() yang sudah ada
                loop.create_task(bot_application.stop())
                loop.create_task(bot_application.shutdown())
            print("✅ Bot berhasil dihentikan dengan aman")
        except Exception as e:
            print(f"⚠️  Error saat shutdown: {e}")
    
    print("👋 Goodbye!")
    sys.exit(0)
# --- AKHIR Graceful Shutdown ---

# ==============================================================================
# 📦 DATA PRODUK
# ==============================================================================
ALL_PACKAGES_RAW = [
    {'id': 302, 'name': "XL Akrab Mini Lite", 'price': 46000, 'category': 'XL', 'type': 'Akrab', 'data': '13-32 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 304, 'name': "XL Akrab Mini", 'price': 58000, 'category': 'XL', 'type': 'Akrab', 'data': '33-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 305, 'name': "XL Akrab Mini V2", 'price': 64000, 'category': 'XL', 'type': 'Akrab', 'data': '31-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 307, 'name': "XL Akrab Big V2", 'price': 67000, 'category': 'XL', 'type': 'Akrab', 'data': '38-57 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 313, 'name': "XL Akrab Jumbo V2", 'price': 97000, 'category': 'XL', 'type': 'Akrab', 'data': '70 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 315, 'name': "XL Akrab Mega Big V2", 'price': 102000, 'category': 'XL', 'type': 'Akrab', 'data': '90 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 317, 'name': "XL Bebas Puas 75GB", 'price': 98000, 'category': 'XL', 'type': 'BebasPuas', 'data': '75GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 318, 'name': "XL Bebas Puas 234GB", 'price': 171000, 'category': 'XL', 'type': 'BebasPuas', 'data': '234GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 319, 'name': "XL Circle 7–11GB", 'price': 31000, 'category': 'XL', 'type': 'Circle', 'data': '7-11GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 321, 'name': "XL Circle 17–21GB", 'price': 42000, 'category': 'XL', 'type': 'Circle', 'data': '17-21GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 323, 'name': "XL Circle 27–31GB", 'price': 58000, 'category': 'XL', 'type': 'Circle', 'data': '27-31GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 219, 'name': "XL Flex S 5GB 28Hari", 'price': 27000, 'category': 'XL', 'type': 'Paket', 'data': '5 GB', 'validity': '28 Hari', 'details': '5GB Nasional, Hingga 3GB Lokal, Nelpon 5 Menit'},
    {'id': 221, 'name': "XL Flex M 10GB 28Hari", 'price': 45000, 'category': 'XL', 'type': 'Paket', 'data': '10 GB', 'validity': '28 Hari', 'details': '10GB Nasional, Hingga 5GB Lokal, Nelpon 5 Menit'},
    {'id': 224, 'name': "XL Flex L Plus 26GB 28Hari", 'price': 75000, 'category': 'XL', 'type': 'Paket', 'data': '26 GB', 'validity': '28 Hari', 'details': '26GB Nasional, Hingga 11GB Lokal, Nelpon 5 Menit'},
    {'id': 18, 'name': "Tri Happy 5gb 7hari", 'price': 20000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '7 Hari', 'details': 'Kuota 5gb, Berlaku Nasional, 1.5gb Lokal'},
    {'id': 26, 'name': "Tri Happy 11gb 28hari", 'price': 46000, 'category': 'Tri', 'type': 'Paket', 'data': '11 GB', 'validity': '28 Hari', 'details': 'Kuota 11gb, Berlaku Nasional, 6gb Lokal'},
    {'id': 30, 'name': "Tri Happy 42gb 28hari", 'price': 71000, 'category': 'Tri', 'type': 'Paket', 'data': '42 GB', 'validity': '28 Hari', 'details': 'Kuota 42gb, Berlaku Nasional, 8gb Lokal'},
    {'id': 71, 'name': "Axis Bronet 2gb 30hari", 'price': 19000, 'category': 'Axis', 'type': 'Paket', 'data': '2 GB', 'validity': '30 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 74, 'name': "Axis Bronet 8gb 30hari", 'price': 39000, 'category': 'Axis', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': 'Kuota 8gb, Berlaku Nasional'},
    {'id': 76, 'name': "Axis Bronet 20gb 30hari", 'price': 73000, 'category': 'Axis', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20gb, Berlaku Nasional'},
    {'id': 181, 'name': "Freedom Internet 6GB 28Hari", 'price': 26000, 'category': 'Indosat', 'type': 'Paket', 'data': '6 GB', 'validity': '28 Hari', 'details': 'Kuota 6GB, Nasional'},
    {'id': 186, 'name': "Freedom Internet 13GB 28Hari", 'price': 52000, 'category': 'Indosat', 'type': 'Paket', 'data': '13 GB', 'validity': '28 Hari', 'details': 'Kuota 13GB, Nasional'},
    {'id': 188, 'name': "Freedom Internet 30GB 28Hari", 'price': 90000, 'category': 'Indosat', 'type': 'Paket', 'data': '30 GB', 'validity': '28 Hari', 'details': 'Kuota 30GB, Nasional'},
    {'id': 266, 'name': "Tsel Promo 3gb 30 Hari", 'price': 26000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '3 GB', 'validity': '30 Hari', 'details': '3gb + Bonus Extra Kuota'},
    {'id': 269, 'name': "Tsel Promo 6.5gb 30 Hari", 'price': 57000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '6.5 GB', 'validity': '30 Hari', 'details': '6.5gb + Bonus Extra Kuota'},
    {'id': 271, 'name': "Tsel 8gb 30 Hari", 'price': 68000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': '8gb + Bonus Extra Kuota'},
    {'id': 129, 'name': "By.U Promo 9GB 30Hari", 'price': 27000, 'category': 'By.U', 'type': 'Paket', 'data': '9 GB', 'validity': '30 Hari', 'details': 'Kuota 9GB, Nasional'},
    {'id': 132, 'name': "By.U Promo 20GB 30Hari", 'price': 47000, 'category': 'By.U', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20GB, Nasional'},
    {'id': 142, 'name': "By.U Promo 20GB 30Hari", 'price': 47000, 'category': 'By.U', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20GB, Nasional'},
    # Pulsa
    {'id': 247, 'name': "XL Pulsa 10.000", 'price': 11000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 249, 'name': "XL Pulsa 25.000", 'price': 25000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 252, 'name': "XL Pulsa 50.000", 'price': 50000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 257, 'name': "XL Pulsa 100.000", 'price': 100000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 50, 'name': "Tri Pulsa 10.000", 'price': 11000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+10 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 53, 'name': "Tri Pulsa 25.000", 'price': 25000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+25 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 56, 'name': "Tri Pulsa 50.000", 'price': 50000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+50 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 62, 'name': "Tri Pulsa 100.000", 'price': 99000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+100 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 105, 'name': "Axis Pulsa 10.000", 'price': 11000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 107, 'name': "Axis Pulsa 25.000", 'price': 25000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 110, 'name': "Axis Pulsa 50.000", 'price': 50000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 115, 'name': "Axis Pulsa 100.000", 'price': 100000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 195, 'name': "Indosat Pulsa 10.000", 'price': 12000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 199, 'name': "Indosat Pulsa 25.000", 'price': 26000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 202, 'name': "Indosat Pulsa 50.000", 'price': 50000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 207, 'name': "Indosat Pulsa 100.000", 'price': 100000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 280, 'name': "Telkomsel Pulsa 10.000", 'price': 11000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 10.000'},
    {'id': 283, 'name': "Telkomsel Pulsa 25.000", 'price': 25000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 25.000'},
    {'id': 288, 'name': "Telkomsel Pulsa 50.000", 'price': 50000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 50.000'},
    {'id': 298, 'name': "Telkomsel Pulsa 100.000", 'price': 99000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 100.000'},
    {'id': 142, 'name': "By.U Pulsa 10.000", 'price': 11000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': 'N/A', 'details': 'Pulsa By.U 10.000'},
    {'id': 145, 'name': "By.U Pulsa 25.000", 'price': 25000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': 'N/A', 'details': 'Pulsa By.U 25.000'},
    {'id': 148, 'name': "By.U Pulsa 50.000", 'price': 50000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': 'N/A', 'details': 'Pulsa By.U 50.000'},
]

# ==============================================================================
# 🛠️ FUNGSI-FUNGSI DATA & UTILITAS
# ==============================================================================

def safe_html(text):
    return html.escape(str(text))

def create_package_key(pkg):
    name_slug = re.sub(r'[^a-z0-9_]', '', pkg['name'].lower().replace(' ', '_'))
    return f"pkg_{pkg['id']}_{name_slug}"

def format_qr_data(text: str) -> str:
    text = text.strip()
    if not re.match(r'^[a-zA-Z]+://', text):
        if re.match(r'^(www\.|[a-zA-Z0-9-]+)\.(com|id|net|org|xyz|co\.id|ac\.id|sch\.id|web\.id|my\.id|io|dev)(/.*)?$', text):
            return f"https://{text}"
    phone_match = re.match(r'^(\+?62|0)8[0-9]{8,12}$', text.replace(' ', '').replace('-', ''))
    if phone_match:
        number = phone_match.group(0).replace(' ', '').replace('-', '')
        if number.startswith('08'):    
            number = '+62' + number[1:]
        elif number.startswith('62'):    
            number = '+' + number
        return f"tel:{number}"
    return text

def format_bytes(size):
    if size is None: return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < len(power_labels) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"

ALL_PACKAGES_DATA = {create_package_key(pkg): pkg for pkg in ALL_PACKAGES_RAW}
PRICES = {key: data['price'] for key, data in ALL_PACKAGES_DATA.items()}

def get_products(category=None, product_type=None, special_type=None):
    filtered_items = ALL_PACKAGES_DATA.items()
    if category:
        filtered_items = [item for item in filtered_items if item[1].get('category', '').lower() == category.lower()]
    if special_type:
        filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == special_type.lower()]
    elif product_type:
        if category and category.lower() == 'xl' and product_type.lower() == 'paket':
            special_types = ['akrab', 'bebaspuas', 'circle']
            filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == 'paket' and item[1].get('type').lower() not in special_types]
        else:
            filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == product_type.lower()]
    return {key: data['name'] for key, data in filtered_items}

AKRAB_QUOTA_DETAILS = {
    "pkg_305_xl_akrab_mini_v2": {"1": "31GB - 33GB", "2": "33GB - 35GB", "3": "38GB - 40GB", "4": "48GB - 50GB"},
    "pkg_307_xl_akrab_big_v2": {"1": "38GB - 40GB", "2": "40GB - 42GB", "3": "45GB - 47GB", "4": "55GB - 57GB"},
    "pkg_313_xl_akrab_jumbo_v2": {"1": "65GB", "2": "70GB", "3": "83GB", "4": "123GB"},
    "pkg_315_xl_akrab_mega_big_v2": {"1": "88GB - 90GB", "2": "90GB - 92GB", "3": "95GB - 97GB", "4": "105GB - 107GB"},
}
AKRAB_QUOTA_DETAILS['pkg_304_xl_akrab_mini'] = AKRAB_QUOTA_DETAILS.get('pkg_305_xl_akrab_mini_v2')

# ==============================================================================
# ✍️ FUNGSI PEMBUAT DESKRIPSI
# ==============================================================================
def create_header(info):
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    return f"✨ <b>{safe_html(info.get('name', 'N/A'))}</b> ✨\n💵 <b>Harga: {price}</b>\n"

def create_general_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    header = create_header(info)
    if info.get('type') == 'Pulsa':
        return (header + f"\n• 💰 <b>Nominal Pulsa:</b> {info.get('data', 'N/A')}\n"
                         f"• ⏳ <b>Penambahan Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                         f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}")
    else:
        return (header + f"\n• 💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n"
                         f"• 📅 <b>Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                         f"• 📝 <b>Rincian:</b> {safe_html(info.get('details', 'N/A'))}")

def create_akrab_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    quota_info = AKRAB_QUOTA_DETAILS.get(package_key)
    description = create_header(info) + "\n"
    description += ("<i>Paket keluarga resmi dari XL dengan kuota besar yang bisa dibagi-pakai.</i>\n\n"
                    "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL)\n" "🛡️ <b>Jaminan:</b> Garansi Penuh\n"
                    "🌐 <b>Kompatibilitas:</b> XL / AXIS / LIVEON\n" "📅 <b>Masa Aktif:</b> ±28 hari (sesuai ketentuan XL)\n\n")
    if quota_info:
        description += ("💾 <b>Estimasi Total Kuota (berdasarkan zona):</b>\n"
                          f"  - <b>Area 1:</b> {quota_info.get('1', 'N/A')}\n" f"  - <b>Area 2:</b> {quota_info.get('2', 'N/A')}\n"
                          f"  - <b>Area 3:</b> {quota_info.get('3', 'N/A')}\n" f"  - <b>Area 4:</b> {quota_info.get('4', 'N/A')}\n\n")
    else:
        description += f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n\n"
    description += ("📋 <b>Prosedur & Ketentuan Penting:</b>\n"
                    "  - Pastikan SIM terpasang di perangkat (HP/Modem) untuk deteksi lokasi BTS dan klaim bonus kuota lokal.\n"
                    "  - Jika kuota MyRewards belum masuk sepenuhnya, mohon tunggu 1x24 jam sebelum melapor ke Admin.\n\n"
                    "ℹ️ <b>Informasi Tambahan:</b>\n" "  - <a href='http://bit.ly/area_akrab'>Cek Pembagian Area Kuota Anda</a>\n"
                    "  - <a href='https://kmsp-store.com/cara-unreg-paket-akrab-yang-benar'>Panduan Unreg Paket Akrab</a>")
    return description

def create_circle_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    return (create_header(info) + "\n" "<i>Paket eksklusif dengan kuota dinamis yang menguntungkan.</i>\n\n"
            f"💾 <b>Estimasi Kuota:</b> {info.get('data', 'N/A')} (potensi dapat lebih)\n"
            "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n"
            "⏳ <b>Masa Aktif:</b> 28 hari atau hingga kuota habis. Jika kuota habis sebelum 28 hari, status keanggotaan menjadi <b>BEKU/FREEZE</b>.\n"
            "⚡ <b>Aktivasi:</b> Instan, tanpa OTP.\n\n" "⚠️ <b>PERHATIAN (WAJIB BACA):</b>\n" "<b>1. Cara Cek Kuota:</b>\n"
            "    - Buka aplikasi <b>MyXL terbaru</b>.\n" "    - Klik menu <b>XL CIRCLE</b> di bagian bawah (bukan dari 'Lihat Paket Saya').\n\n"
            "<b>2. Syarat & Ketentuan:</b>\n" "    - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n"
            "    - <b>Keanggotaan:</b> Tidak terdaftar di Circle lain pada bulan yang sama.\n" "    - <b>Status Kartu:</b> Tidak dalam masa tenggang.\n"
            "    - <b>DILARANG UNREG:</b> Keluar dari Circle akan menghanguskan garansi (tanpa refund).")

def create_bebaspuas_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    return (create_header(info) + "\n" "<i>Nikmati kebebasan internetan dengan kuota besar yang bisa diakumulasi.</i>\n\n"
            "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) via Sidompul\n" "⚡ <b>Aktivasi:</b> Instan, tanpa memerlukan kode OTP\n"
            "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n" "🌍 <b>Area:</b> Berlaku di seluruh Indonesia\n"
            "📅 <b>Masa Aktif & Garansi:</b> 30 Hari\n" f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')} (Full 24 Jam)\n\n"
            "⭐ <b>Fitur Unggulan:</b>\n"
            "  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli paket Bebas Puas lain sebelum masa aktif berakhir.\n"
            "  - <b>Tanpa Syarat Pulsa:</b> Aktivasi tidak memerlukan pulsa minimum.\n\n" "🎁 <b>Klaim Bonus:</b>\n"
            "  - Tersedia bonus kuota yang dapat diklaim di aplikasi myXL (pilih salah satu: YouTube, TikTok, atau Kuota Utama).")

PAKET_DESCRIPTIONS = {key: create_general_description(key) for key in ALL_PACKAGES_DATA}
for key in get_products(special_type='Akrab'): PAKET_DESCRIPTIONS[key] = create_akrab_description(key)
for key in get_products(special_type='Circle'): PAKET_DESCRIPTIONS[key] = create_circle_description(key)
for key in get_products(special_type='BebasPuas'): PAKET_DESCRIPTIONS[key] = create_bebaspuas_description(key)
PAKET_DESCRIPTIONS["bantuan"] = ("<b>Pusat Bantuan & Informasi</b> 🆘\n\n"
                                      "Selamat datang di pusat bantuan Pulsa Net Bot.\n\n"
                                      "Jika Anda mengalami kendala teknis, memiliki pertanyaan seputar produk, atau tertarik untuk menjadi reseller, jangan ragu untuk menghubungi Admin kami.\n\n"
                                      "Gunakan perintah /start untuk kembali ke menu utama kapan saja.\n\n"
                                      "📞 <b>Admin:</b> @hexynos\n" "🌐 <b>Website Resmi:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>")

# ==============================================================================
# FUNGSI-FUNGSI FITUR TOOLS (HELPER FUNCTIONS)
# ==============================================================================

def get_provider_info_global(phone_number_str: str) -> str:
    """Fungsi canggih untuk mendapatkan info nomor telepon dari seluruh dunia."""
    try:
        if not phone_number_str.startswith('+'):
            phone_number_str = '+' + phone_number_str
        phone_number = phonenumbers.parse(phone_number_str, None)
        if not phonenumbers.is_valid_number(phone_number):
            return f"Nomor <code>{safe_html(phone_number_str)}</code> tidak valid."
        country_code = phone_number.country_code
        region_code = phonenumberutil.region_code_for_country_code(country_code)
        country = pycountry.countries.get(alpha_2=region_code)
        country_name = country.name if country else "Tidak Diketahui"
        country_flag = country.flag if hasattr(country, 'flag') else "❓"
        number_type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "Ponsel",
            phonenumbers.PhoneNumberType.FIXED_LINE: "Telepon Rumah",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Ponsel / Telepon Rumah",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Bebas Pulsa",
            phonenumbers.PhoneNumberType.VOIP: "VoIP",
        }
        number_type = number_type_map.get(phonenumbers.number_type(phone_number), "Lainnya")
        carrier_name = carrier.name_for_number(phone_number, "en") or "Tidak terdeteksi"
        output = (
            f"<b>Hasil Pengecekan untuk <code>{safe_html(phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))}</code></b>\n"
            f"-----------------------------------------\n"
            f"<b>Negara:</b> {country_flag} {country_name} (+{country_code})\n"
            f"<b>Valid:</b> ✅ Ya\n"
            f"<b>Tipe:</b> {number_type}\n"
            f"<b>Operator Asli:</b> {carrier_name}\n"
            f"<i>(Info operator mungkin tidak akurat jika nomor sudah porting)</i>"
        )
        return output
    except phonenumberutil.NumberParseException:
        return f"Format nomor <code>{safe_html(phone_number_str)}</code> salah. Harap gunakan format internasional (contoh: +628123...). Pengguna disarankan untuk mengirimkan nomor dalam format internasional."
    except Exception as e:
        logger.error(f"Error di get_provider_info_global: {e}")
        return "Terjadi kesalahan saat memproses nomor."

def run_yt_dlp_sync(ydl_opts, url, download=False):
    """
    PROFESSIONAL FIX: Synchronous wrapper to run yt-dlp.
    This function is designed to be run in a separate thread.
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=download)

# ==============================================================================
# 🤖 FUNGSI HANDLER BOT
# ==============================================================================

keyboard_error_back = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]])

async def send_admin_log(context: ContextTypes.DEFAULT_TYPE, error: Exception, update: Update, from_where: str, custom_message: str = ""):
    """Memformat dan mengirim log eror ke Admin, dengan pesan kustom opsional."""
    if not ADMIN_ID:
        logger.warning("TELEGRAM_ADMIN_ID tidak diatur. Log eror tidak akan dikirim.")
        return

    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)
    user = update.effective_user
    
    actionable_message = f"<b>Pesan Aksi:</b> {custom_message}\n\n" if custom_message else ""

    admin_message = (
        f"🚨 <b>BOT ERROR LOG</b> 🚨\n\n"
        f"{actionable_message}"
        f"<b>Fungsi:</b> <code>{from_where}</code>\n"
        f"<b>User:</b> {user.mention_html()} (ID: <code>{user.id}</code>)\n"
        f"<b>Chat ID:</b> <code>{update.effective_chat.id}</code>\n\n"
        f"<b>Tipe Error:</b> <code>{type(error).__name__}</code>\n"
        f"<b>Pesan Error:</b>\n<pre>{safe_html(str(error))}</pre>\n\n"
        f"<b>Traceback (Ringkas):</b>\n<pre>{safe_html(tb_string[-2000:])}</pre>"
    )

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"KRITIS: Gagal mengirim log eror ke admin! Error: {e}")

async def track_message(context: ContextTypes.DEFAULT_TYPE, message):
    if message:
        if 'messages_to_clear' not in context.user_data:
            context.user_data['messages_to_clear'] = []
        if len(context.user_data['messages_to_clear']) >= MAX_MESSAGES_TO_TRACK:
            context.user_data['messages_to_clear'] = context.user_data['messages_to_clear'][-(MAX_MESSAGES_TO_TRACK-1):]
        context.user_data['messages_to_clear'].append(message.message_id)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if update.callback_query:
            await update.callback_query.answer("Memulai pembersihan riwayat...")
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
            except Exception: pass
        
        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 <b>Sedang menghapus pesan...</b>", parse_mode=ParseMode.HTML)
        messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))
        messages_to_clear = messages_to_clear[-MAX_MESSAGES_TO_DELETE_PER_BATCH:]
        
        delete_tasks = [context.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in messages_to_clear if msg_id != loading_msg.message_id]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception: pass
        
        context.user_data['messages_to_clear'] = []
        
        confirmation_text = (f"✅ <b>Pembersihan Selesai!</b>\n\nBerhasil menghapus <b>{success_count}</b> pesan dari sesi ini.")
        
        try:
            sent_msg = await context.bot.send_message(chat_id=chat_id, text=confirmation_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, sent_msg)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to send confirmation message with identical content in clear_history. Skipping.")
            else:
                raise e
            
    except Exception as e:
        await send_admin_log(context, e, update, "clear_history")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="Maaf, terjadi kesalahan saat membersihkan chat.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except Exception as e_inner:
            logger.error(f"Failed to send error message in clear_history: {e_inner}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        context.user_data.pop('state', None)
        if update.message and update.message.text == '/start':
            await track_message(context, update.message)
        user = update.effective_user
        jakarta_tz = ZoneInfo("Asia/Jakarta")
        now = datetime.now(jakarta_tz)
        hour = now.hour
        if 5 <= hour < 11: greeting, icon = "Selamat Pagi", "☀️"
        elif 11 <= hour < 15: greeting, icon = "Selamat Siang", "🌤️"
        elif 15 <= hour < 18: greeting, icon = "Selamat Sore", "🌥️"
        else: greeting, icon = "Selamat Malam", "🌙"
        username_info = f"<code>@{user.username}</code>" if user.username else "N/A"
        main_text = (
            f"{icon} <b>{greeting}, {user.first_name}!</b>\n\n"
            "Selamat datang di <b>Pulsa Net Bot Resmi</b> 🚀\n"
            "Platform terpercaya untuk semua kebutuhan digital Anda.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Informasi Sesi Anda</b>\n"
            f"  ├─ Username: {username_info}\n"
            f"  ├─ User ID: <code>{user.id}</code>\n"
            f"  └─ Chat ID: <code>{chat_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Pilih layanan yang Anda butuhkan dari menu di bawah ini."
        )
        keyboard = [
            [InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), InlineKeyboardButton("💰 Pulsa Reguler", callback_data="main_pulsa")],
            [InlineKeyboardButton("🔍 Cek Info Nomor", callback_data="ask_for_number"), InlineKeyboardButton("🛠️ Tools & Hiburan", callback_data="main_tools")],
            [InlineKeyboardButton("📊 Cek Kuota (XL/Axis)", url="https://sidompul.kmsp-store.com/"), InlineKeyboardButton("🆘 Bantuan", callback_data="main_bantuan")],
            [InlineKeyboardButton("🗑️ Bersihkan Chat", callback_data="clear_history")],
            [InlineKeyboardButton("🌐 Kunjungi Website Kami", url="https://pulsanet.kesug.com/beli.html")]
        ]
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(main_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
                await update.callback_query.answer()
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Tried to edit message {update.callback_query.message.message_id} with identical content in start. Skipping.")
                    await update.callback_query.answer("Konten tidak berubah.")
                else:
                    raise e
        else:
            # --- Retry untuk TimedOut Error ---
            sent_message = None
            for attempt in range(3): # Coba hingga 3 kali
                try:
                    sent_message = await context.bot.send_message(
                        chat_id=chat_id,
                        text=main_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                    break # Berhasil, keluar dari loop
                except TimedOut:
                    logger.warning(f"Attempt {attempt + 1} to send start message timed out. Retrying in 2 seconds...")
                    if attempt < 2: # Jangan menunggu pada percobaan terakhir
                        await asyncio.sleep(2)
                except Exception: # Tangkap error lain dan langsung hentikan
                    raise 

            if not sent_message:
                # Jika semua percobaan gagal, lempar error agar ditangani oleh blok exception di luar
                raise TimedOut("Gagal mengirim pesan setelah 3 kali percobaan.")

            await track_message(context, sent_message)
            # --- AKHIR Retry ---
    except Exception as e:
        await send_admin_log(context, e, update, "start")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="Maaf, terjadi kesalahan saat memuat menu utama.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except:
            pass

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        product_type_key = query.data.split('_')[1]
        product_type_name = "Paket Data" if product_type_key == "paket" else "Pulsa"
        operators = {"XL": "🌐", "Axis": "🌐", "Tri": "🌐", "Telkomsel": "🌐", "Indosat": "🌐", "By.U": "🌐"}
        op_items = list(operators.items())
        keyboard = []
        for i in range(0, len(op_items), 2):
            row = [InlineKeyboardButton(f"{icon} {op}", callback_data=f"list_{product_type_key}_{op.lower()}") for op, icon in op_items[i:i+2]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
        
        try:
            await query.edit_message_text(f"Anda memilih kategori <b>{product_type_name}</b>.\nSilakan pilih provider:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_operator_menu. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_operator_menu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("🤝 Akrab", callback_data="list_paket_xl_akrab"), InlineKeyboardButton("🥳 Bebas Puas", callback_data="list_paket_xl_bebaspuas")],
            [InlineKeyboardButton("⭕️ Circle", callback_data="list_paket_xl_circle"), InlineKeyboardButton("🚀 Paket Lainnya", callback_data="list_paket_xl_paket")],
            [InlineKeyboardButton("⬅️ Kembali ke Provider", callback_data="main_paket")]
        ]
        try:
            await query.edit_message_text("<b>Pilihan Paket Data XL 🌐</b>\n\nSilakan pilih jenis paket di bawah ini:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_xl_paket_submenu. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_xl_paket_submenu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        data_parts = query.data.split('_')
        await query.answer()
        product_type_key, category_key, special_type_key = data_parts[1], data_parts[2], data_parts[3] if len(data_parts) > 3 else None
        titles = {"tri": "Tri 🌐", "axis": "Axis 🌐", "telkomsel": "Telkomsel 🌐", "indosat": "Indosat 🌐", "by.u": "By.U 🌐", "xl": "XL 🌐"}
        base_title = titles.get(category_key, '')
        if special_type_key:
            products = get_products(category=category_key, special_type=special_type_key)
            title_map = {"akrab": "Paket Akrab", "bebaspuas": "Paket Bebas Puas", "circle": "Paket Circle", "paket": "Paket Lainnya"}
            title = f"<b>{base_title} - {title_map.get(special_type_key)}</b>"
        else:
            products = get_products(category=category_key, product_type=product_type_key)
            product_name = 'Paket Data' if product_type_key == 'paket' else 'Pulsa'
            title = f"<b>{base_title} - {product_name}</b>"
        
        back_cb = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"

        if not products:
            try:
                await query.edit_message_text("Mohon maaf, produk untuk kategori ini belum tersedia.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)]]), parse_mode=ParseMode.HTML)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Tried to edit message {query.message.message_id} with identical content (no products). Skipping.")
                    await query.answer("Konten tidak berubah.")
                else:
                    raise e
            return
        
        sorted_keys = sorted(products.keys(), key=lambda k: PRICES.get(k, 0))
        keyboard = []
        for key in sorted_keys:
            short_name = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', products[key], flags=re.I).replace('Paket ', '')
            button_text = f"{short_name} - Rp{PRICES.get(key, 0):,}".replace(",", ".")
            keyboard.append([InlineKeyboardButton(button_text, callback_data=key)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)])
        
        try:
            await query.edit_message_text(f"{title}\n\nSilakan pilih produk yang Anda inginkan:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_product_list. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_product_list")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        package_key = query.data
        await query.answer()
        info = ALL_PACKAGES_DATA.get(package_key, {})
        category, p_type = info.get('category', '').lower(), info.get('type', '').lower()
        product_type_key = 'pulsa' if p_type == 'pulsa' else 'paket'
        if category == 'xl' and product_type_key == 'paket':
            back_data = f"list_paket_xl_{p_type}" if p_type in ['akrab', 'bebaspuas', 'circle'] else "list_paket_xl_paket"
        else:
            back_data = f"list_{product_type_key}_{category}"
        keyboard = [[InlineKeyboardButton("🛒 Beli Sekarang (Website)", url="https://pulsanet.kesug.com/beli.html")],
                    [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data=back_data)],
                    [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
        
        try:
            await query.edit_message_text(PAKET_DESCRIPTIONS.get(package_key, "Informasi produk tidak ditemukan."), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_package_details. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_package_details")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        try:
            await query.edit_message_text(PAKET_DESCRIPTIONS["bantuan"], reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_bantuan. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_bantuan")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        text = "<b>🛠️ Tools & Hiburan</b>\n\nPilih salah satu alat atau hiburan yang tersedia di bawah ini."
        keyboard = [
            [InlineKeyboardButton("🖼️ Buat QR Code", callback_data="ask_for_qr"), InlineKeyboardButton("💹 Kalkulator Kurs", callback_data="ask_for_currency")],
            [InlineKeyboardButton("▶️ YouTube Downloader", callback_data="ask_for_youtube"), InlineKeyboardButton("🔗 Media Downloader", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("🔐 Buat Password", callback_data="gen_password"), InlineKeyboardButton("🎮 Mini Game", callback_data="main_game")],
            [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]
        ]
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_tools_menu. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_tools_menu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def prompt_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        action = query.data
        text = ""
        back_button_callback = "main_tools"

        if action == "ask_for_number":
            context.user_data['state'] = 'awaiting_number'
            text = ("<b>🔍 Cek Info Nomor Telepon (Global)</b>\n\n"
                    "Silakan kirimkan nomor HP yang ingin Anda periksa, <b>wajib</b> dengan format internasional.\n\n"
                    "Contoh: <code>+6281234567890</code> (Indonesia), <code>+12025550139</code> (USA).")
            back_button_callback = "back_to_start"
        elif action == "ask_for_qr":
            context.user_data['state'] = 'awaiting_qr_text'
            text = ("<b>🖼️ Generator QR Code</b>\n\nKirimkan teks, tautan, atau nomor HP yang ingin Anda jadikan QR Code.")
        elif action == "ask_for_youtube":
            context.user_data['state'] = 'awaiting_youtube_link'
            text = ("<b>▶️ YouTube Downloader</b>\n\nKirimkan link video YouTube yang ingin Anda unduh.")
        elif action == "ask_for_media_link":
            context.user_data['state'] = 'awaiting_media_link'
            text = ("<b>🔗 Media Downloader Universal</b>\n\n"
                    "Kirimkan link dari Instagram, Twitter, TikTok, Facebook, dll. untuk mengunduh video atau gambar.")
        elif action == "ask_for_currency":
            context.user_data['state'] = 'awaiting_currency'
            text = ("<b>💹 Kalkulator Kurs Mata Uang</b>\n\n"
                    "Kirimkan permintaan konversi Anda dalam format:\n"
                    "<code>[jumlah] [kode_asal] to [kode_tujuan]</code>\n\n"
                    "<b>Contoh:</b>\n"
                    "• <code>100 USD to IDR</code>\n"
                    "• <code>50 EUR JPY</code>\n"
                    "• <code>1000000 IDR MYR</code>")
        else:  
            return
            
        keyboard = [[InlineKeyboardButton("⬅️ Batal & Kembali", callback_data=back_button_callback)]]
        
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in prompt_for_action. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "prompt_for_action")
        try:
            await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
        except BadRequest as e_inner:
            if "Message is not modified" in str(e_inner):
                logger.info(f"Tried to edit message {query.message.message_id} to identical error message in prompt_for_action error handler. Skipping.")
            else:
                logger.error(f"Failed to send error message in prompt_for_action error handler: {e_inner}")


async def handle_currency_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = None
    try:
        status_msg = await update.message.reply_text("💱 Menghitung...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        
        text = update.message.text.upper()
        match = re.match(r"([\d\.\,]+)\s*([A-Z]{3})\s*(?:TO|IN|)\s*([A-Z]{3})", text)
        if not match:
            try:
                await status_msg.edit_text("Format salah. Contoh: <code>100 USD to IDR</code>.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} with identical content (bad format). Skipping.")
                else:
                    raise e
            return
        amount_str, base_curr, target_curr = match.groups()
        amount = float(amount_str.replace(",", ""))
        api_url = f"https://open.er-api.com/v6/latest/{base_curr}"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, timeout=10)
            response.raise_for_status()
        data = response.json()
        if data.get("result") == "success" and target_curr in data.get("rates", {}):
            rate = data["rates"][target_curr]
            converted_amount = amount * rate
            try:
                base_country = pycountry.currencies.get(alpha_3=base_curr)
                base_name = base_country.name if base_country else base_curr
                target_country = pycountry.currencies.get(alpha_3=target_curr)
                target_name = target_country.name if target_country else target_curr
            except Exception:
                base_name, target_name = base_curr, target_curr
            result_text = (
                f"✅ <b>Hasil Konversi</b>\n\n"
                f"<b>Dari:</b> {amount:,.2f} {base_curr} ({base_name})\n"
                f"<b>Ke:</b> {converted_amount:,.2f} {target_curr} ({target_name})\n\n"
                f"<i>Kurs 1 {base_curr} = {rate:,.2f} {target_curr}</i>\n"
                f"<a href='https://www.google.com/finance/quote/{base_curr}-{target_curr}'>Sumber data real-time</a>"
            )
            try:
                await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} with identical content (conversion result). Skipping.")
                else:
                    raise e
        else:
            try:
                await status_msg.edit_text(f"Tidak dapat menemukan kurs untuk <b>{target_curr}</b>.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} with identical content (currency not found). Skipping.")
                else:
                    raise e
    except httpx.RequestError as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (RequestError)")
        if status_msg:
            try:
                await status_msg.edit_text("Gagal menghubungi layanan kurs. Coba lagi nanti.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e_inner:
                if "Message is not modified" in str(e_inner):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} to identical error message. Skipping.")
                else:
                    logger.error(f"Failed to send error message in handle_currency_conversion error handler: {e_inner}")
    except Exception as e:
        await send_admin_log(context, e, update, "handle_currency_conversion")
        if status_msg:
            try:
                await status_msg.edit_text("Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e_inner:
                if "Message is not modified" in str(e_inner):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} to identical technical error message. Skipping.")
                else:
                    logger.error(f"Failed to send error message in handle_currency_conversion error handler: {e_inner}")

async def show_youtube_quality_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """
    Enhanced version dengan cookie error detection yang lebih baik.
    """
    status_msg = None
    try:
        status_msg = await context.bot.send_message(
            update.effective_chat.id, 
            "🔍 <b>Menganalisis link...</b>", 
            parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)
        
        # --- FIX: Pass URL to get_ytdlp_options ---
        ydl_opts = get_ytdlp_options(url=url)
        
        try:
            info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
        except yt_dlp.utils.DownloadError as e:
            error_str = str(e).lower()
            
            # Deteksi berbagai jenis cookie error
            cookie_errors = [
                'sign in to confirm', 'no suitable proxies', '410 gone',
                'unable to extract', 'login required', 'this video requires payment',
            ]
            
            if any(err in error_str for err in cookie_errors):
                admin_alert = (
                    "🚨 CRITICAL: YouTube Cookie Authentication Failed!\n\n"
                    f"Error Type: {type(e).__name__}\n"
                    f"Error Message: {str(e)[:200]}\n\n"
                    "ACTIONS REQUIRED:\n"
                    "1. Export fresh cookies dari browser (gunakan extension 'Get cookies.txt LOCALLY')\n"
                    f"2. Convert ke base64: base64 {YOUTUBE_COOKIE_FILE}\n"
                    "3. Update environment variable YOUTUBE_COOKIES_BASE64\n"
                    "4. Restart bot\n\n"
                    "Panduan lengkap: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies"
                )
                await send_admin_log(context, e, update, "YouTube Cookie Auth Failed", custom_message=admin_alert)
                
                user_message = (
                    "❌ <b>Layanan YouTube Downloader sedang bermasalah</b>\n\n"
                    "Sistem autentikasi YouTube memerlukan pembaruan. "
                    "Admin telah diberitahu dan sedang memperbaiki.\n\n"
                    "<i>Error: Cookie authentication expired</i>"
                )
                await status_msg.edit_text(user_message, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                return
            
            # Error lainnya
            raise e

        # --- LOGIKA LAMA UNTUK MENAMPILKAN OPSI KUALITAS ---
        video_id, title, formats = info_dict.get('id', ''), info_dict.get('title', 'Video'), info_dict.get('formats', [])
        keyboard, video_formats = [], []
        
        for f in formats:
            if (f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and 
                f.get('height') and f.get('height') <= 720):
                file_size_bytes = f.get('filesize') or f.get('filesize_approx')
                if not file_size_bytes or file_size_bytes <= MAX_UPLOAD_FILE_SIZE_BYTES:
                    video_formats.append(f)
                else:
                    logger.info(f"Skipping format {f.get('format_id')} due to size {format_bytes(file_size_bytes)} > {format_bytes(MAX_UPLOAD_FILE_SIZE_BYTES)}")
        
        video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
        for f in video_formats[:3]:
            label = f"📹 {f['height']}p ({format_bytes(f.get('filesize') or f.get('filesize_approx'))})"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl|{video_id}|{f['format_id']}")])
        
        audio_formats = sorted([f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and 
                                (not f.get('filesize') or f.get('filesize') <= MAX_UPLOAD_FILE_SIZE_BYTES)],  
                                key=lambda x: x.get('filesize') or x.get('filesize_approx') or 0, reverse=True)
        if audio_formats:
            best_audio = audio_formats[0]
            label = f"🎵 Audio [{best_audio.get('ext', 'audio')}] ({format_bytes(best_audio.get('filesize') or best_audio.get('filesize_approx'))})"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl|{video_id}|{best_audio['format_id']}")])
        
        if not keyboard:
            await status_msg.edit_text(f"Tidak ditemukan format yang cocok untuk diunduh (atau melebihi batas {MAX_UPLOAD_FILE_SIZE_MB} MB).", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        
        keyboard.append([InlineKeyboardButton("⬅️ Batal", callback_data="main_tools")])
        await status_msg.edit_text(
            f"<b>{safe_html(title)}</b>\n\n"
            "Pilih kualitas yang ingin Anda unduh:\n\n"
            f"<i>⚠️ <b>Perhatian:</b> File di atas {MAX_UPLOAD_FILE_SIZE_MB} MB mungkin gagal dikirim karena batasan Telegram Bot.</i>",
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.HTML
        )
        # --- AKHIR LOGIKA LAMA ---

    except Exception as e:
        await send_admin_log(context, e, update, "show_youtube_quality_options_enhanced")
        if status_msg:
            await status_msg.edit_text(
                "Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )

async def handle_youtube_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    file_path = None
    status_msg = None
    
    try:
        await query.answer("Memulai proses unduh...")
        try:
            status_msg = await query.edit_message_text(f"📥 <b>Mengunduh...</b>\n\n<i>Ini mungkin akan memakan waktu.</i>", parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content (downloading...). Skipping.")
                status_msg = query.message
            else:
                raise e
        
        _, video_id, format_id = query.data.split('|')
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        is_video = any('📹' in btn.text for row in query.message.reply_markup.inline_keyboard 
                       for btn in row if hasattr(btn, 'callback_data') and btn.callback_data == query.data)

        file_path_template = f"{video_id}_{format_id}.%(ext)s"
        
        # --- FIX: Pass URL to get_ytdlp_options ---
        ydl_opts = get_ytdlp_options(url=url) 
        ydl_opts['outtmpl'] = file_path_template
        ydl_opts['max_filesize'] = MAX_UPLOAD_FILE_SIZE_BYTES

        if is_video:
            ydl_opts['format'] = f"{format_id}+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
            action = ChatAction.UPLOAD_VIDEO
        else: # is_audio
            ydl_opts['format'] = f"{format_id}/bestaudio/best"
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a', 'preferredquality': '192'}]
            action = ChatAction.UPLOAD_DOCUMENT
        
        info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=True)
        title = info_dict.get('title', 'Video')
        file_path = info_dict.get('_filename')

        if not file_path or not os.path.exists(file_path):  
            expected_ext = 'mp4' if is_video else 'm4a'
            found_files = [f for f in os.listdir('.') if f.startswith(video_id) and f.endswith(f".{expected_ext}")]
            if found_files:
                file_path = found_files[0]
            else:
                raise ValueError("File tidak ditemukan setelah unduh.")
        
        final_file_size = os.path.getsize(file_path)
        if final_file_size > MAX_UPLOAD_FILE_SIZE_BYTES:
            logger.warning(f"File {file_path} terunduh tetapi ukurannya ({format_bytes(final_file_size)}) melebihi batas {MAX_UPLOAD_FILE_SIZE_MB} MB.")
            await send_admin_log(
                context,
                ValueError(f"File downloaded but size ({format_bytes(final_file_size)}) > {MAX_UPLOAD_FILE_SIZE_MB}MB. yt-dlp estimate was inaccurate."),
                update,
                "handle_youtube_download_choice",
                custom_message="File was deleted before upload attempt."
            )
            await status_msg.edit_text(
                f"❌ <b>Gagal!</b> File berhasil diunduh, tetapi ukurannya ({format_bytes(final_file_size)}) melebihi batas unggah bot sebesar {MAX_UPLOAD_FILE_SIZE_MB} MB. Silakan pilih kualitas yang lebih rendah.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )
            return

        try:
            await status_msg.edit_text("📤 <b>Mengirim file...</b>", parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit status_msg {status_msg.message_id} with identical content (sending file...). Skipping.")
            else:
                raise e

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)
        
        caption = f"<b>{safe_html(title)}</b>\n\nDiunduh dengan @{context.bot.username}"
        with open(file_path, 'rb') as f:
            if is_video:
                sent_file = await context.bot.send_video(update.effective_chat.id, video=f, caption=caption,  
                                                          parse_mode=ParseMode.HTML, read_timeout=300, write_timeout=300)
            else:
                sent_file = await context.bot.send_audio(update.effective_chat.id, audio=f, caption=caption,  
                                                          parse_mode=ParseMode.HTML, read_timeout=300, write_timeout=300)
        await track_message(context, sent_file)
        
        try:
            await status_msg.delete()
        except TelegramError as e:
            logger.info(f"Failed to delete status message {status_msg.message_id} in youtube_download: {e}")

        keyboard_next_action = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Unduh Video Lain", callback_data="ask_for_youtube")],
            [InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]
        ])
        next_action_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ Unduhan selesai. Apa yang ingin Anda lakukan selanjutnya?",
            reply_markup=keyboard_next_action,
            parse_mode=ParseMode.HTML
        )
        await track_message(context, next_action_msg)

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e).lower()
        if 'sign in to confirm' in error_str or 'no suitable proxies' in error_str or '410 gone' in error_str:
            admin_alert = ("CRITICAL: YouTube cookie authentication failed during download. The `youtube_cookies.txt` file is likely expired or invalid. "
                           "Please ensure the YOUTUBE_COOKIES_BASE64 environment variable contains fresh cookies. "
                           "See https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies for tips on effectively exporting YouTube cookies.")
            await send_admin_log(context, e, update, "handle_youtube_download_choice (Cookie/Auth Error)", custom_message=admin_alert)
            reply_text = "Maaf, terjadi kendala teknis pada layanan unduh video. Tim kami telah diberitahu. (Authentikasi YouTube gagal)"
        elif 'max filesize' in error_str:
            reply_text = f"❌ <b>Gagal!</b> Ukuran file yang dipilih melebihi batas unduh bot ({MAX_UPLOAD_FILE_SIZE_MB} MB)."
        else:
            await send_admin_log(context, e, update, "handle_youtube_download_choice (DownloadError)")
            reply_text = "Maaf, terjadi kesalahan saat mengunduh file (mungkin video dilindungi hak cipta atau dibatasi)."
        
        if status_msg:
            try:
                await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e_inner:
                if "Message is not modified" in str(e_inner):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} to identical error message. Skipping.")
                else:
                    logger.error(f"Failed to send error message in handle_youtube_download_choice error handler: {e_inner}")
    except Exception as e:
        await send_admin_log(context, e, update, "handle_youtube_download_choice")
        if status_msg:
            try:
                await status_msg.edit_text("Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except BadRequest as e_inner:
                if "Message is not modified" in str(e_inner):
                    logger.info(f"Tried to edit status_msg {status_msg.message_id} to identical technical error message. Skipping.")
                else:
                    logger.error(f"Failed to send error message in handle_youtube_download_choice error handler: {e_inner}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Gagal menghapus file {file_path}: {e}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await track_message(context, update.message)
        state = context.user_data.get('state')
        message_text = update.message.text
        
        phone_pattern = r'(\+?\d{1,3}[\s-]?\d[\d\s-]{7,14})'
        url_pattern = r'https?://[^\s]+'
        
        if state == 'awaiting_number':
            numbers = re.findall(phone_pattern, message_text)
            keyboard_next_action = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Cek Nomor Lain", callback_data="ask_for_number")],
                [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]
            ])
            
            if numbers:
                responses = [get_provider_info_global(num.replace(" ", "").replace("-", "")) for num in numbers]
                sent_msg = await update.message.reply_text("\n\n---\n\n".join(responses), reply_markup=keyboard_next_action, parse_mode=ParseMode.HTML)
            else:
                sent_msg = await update.message.reply_text(
                    "Format nomor telepon tidak valid. Gunakan format internasional: `+kode_negara nomor`.",  
                    reply_markup=keyboard_next_action,
                    parse_mode=ParseMode.HTML
                )
            await track_message(context, sent_msg)
            return

        elif state == 'awaiting_qr_text':
            loading_msg = await update.message.reply_text("⏳ Membuat QR Code...")
            await track_message(context, loading_msg)
            try:
                formatted_text = format_qr_data(message_text)
                img = qrcode.make(formatted_text)
                bio = io.BytesIO()
                bio.name = 'qrcode.png'
                img.save(bio, 'PNG')
                bio.seek(0)
                caption_text = f"✅ <b>QR Code Berhasil Dibuat!</b>\n\n<b>Data Asli:</b> <code>{safe_html(message_text)}</code>"
                if formatted_text != message_text:  
                    caption_text += f"\n<b>Format Aksi:</b> <code>{safe_html(formatted_text)}</code>"
                sent_photo = await update.message.reply_photo(photo=bio, caption=caption_text, parse_mode=ParseMode.HTML)
                await track_message(context, sent_photo)
                
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=loading_msg.message_id)
                except TelegramError as e:
                    logger.info(f"Failed to delete loading message {loading_msg.message_id} in handle_text_message (QR): {e}")

            except Exception as e:
                await send_admin_log(context, e, update, "handle_text_message (QR Code)")
                try:
                    await loading_msg.edit_text("Maaf, terjadi kesalahan saat membuat QR Code.", reply_markup=keyboard_error_back)
                except BadRequest as e_inner:
                    if "Message is not modified" in str(e_inner):
                        logger.info(f"Tried to edit loading_msg {loading_msg.message_id} to identical error message. Skipping.")
                    else:
                        logger.error(f"Failed to send error message in handle_text_message (QR) error handler: {e_inner}")
            context.user_data.pop('state', None)
            keyboard = [[InlineKeyboardButton("🖼️ Buat QR Lain", callback_data="ask_for_qr")],  
                        [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
            sent_msg2 = await update.message.reply_text("Apa yang ingin Anda lakukan selanjutnya?", reply_markup=InlineKeyboardMarkup(keyboard))
            await track_message(context, sent_msg2)
            return
            
        elif state == 'awaiting_youtube_link':
            if re.search(r'(youtube\.com|youtu\.be|m\.youtube\.com)', message_text):
                await show_youtube_quality_options(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text("Link YouTube tidak valid. Pastikan Anda mengirimkan tautan yang benar dari YouTube.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                await track_message(context, sent_msg)
            context.user_data.pop('state', None)
            return
        
        elif state == 'awaiting_media_link':
            if re.search(url_pattern, message_text):
                await handle_media_download(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text("Link tidak valid. Pastikan Anda mengirimkan tautan yang benar.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                await track_message(context, sent_msg)
            context.user_data.pop('state', None)
            return

        elif state == 'awaiting_currency':
            await handle_currency_conversion(update, context)
            context.user_data.pop('state', None)
            keyboard = [[InlineKeyboardButton("💹 Hitung Kurs Lain", callback_data="ask_for_currency")],  
                        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
            sent_msg2 = await update.message.reply_text("Apa yang ingin Anda lakukan selanjutnya?", reply_markup=InlineKeyboardMarkup(keyboard))
            await track_message(context, sent_msg2)
            return

        numbers = re.findall(phone_pattern, message_text)
        if numbers and len(numbers) <= 3:
            responses = [get_provider_info_global(num.replace(" ", "").replace("-", "")) for num in numbers]
            sent_msg = await update.message.reply_text(
                "💡 <b>Info Nomor Terdeteksi Otomatis:</b>\n\n" + "\n\n---\n\n".join(responses) +
                "\n\n<i>Gunakan 'Cek Info Nomor' dari menu /start untuk cek manual.</i>",  
                parse_mode=ParseMode.HTML
            )
            await track_message(context, sent_msg)
        else:
            pass
            
    except Exception as e:
        await send_admin_log(context, e, update, "handle_text_message")
        error_msg = await update.message.reply_text(
            "Maaf, terjadi kesalahan saat memproses pesan Anda.",
            reply_markup=keyboard_error_back,
            parse_mode=ParseMode.HTML
        )
        await track_message(context, error_msg)

async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        keyboard = [[InlineKeyboardButton("Batu 🗿", callback_data="game_play_rock"),
                     InlineKeyboardButton("Gunting ✂️", callback_data="game_play_scissors"),
                     InlineKeyboardButton("Kertas 📄", callback_data="game_play_paper")],
                    [InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]]
        try:
            await query.edit_message_text("<b>🎮 Game Batu-Gunting-Kertas</b>\n\nAyo bermain! Pilih jagoanmu:",
                                          reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in show_game_menu. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_game_menu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        user_choice = query.data.split('_')[2]
        choices = ['rock', 'scissors', 'paper']
        bot_choice = random.choice(choices)
        emoji = {'rock': '🗿', 'scissors': '✂️', 'paper': '📄'}
        result_text = ""
        if user_choice == bot_choice:  
            result_text = "<b>Hasilnya Seri!</b> 🤝"
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'scissors' and bot_choice == 'paper') or \
             (user_choice == 'paper' and bot_choice == 'rock'):
            result_text = "<b>Kamu Menang!</b> 🎉"
        else:  
            result_text = "<b>Kamu Kalah!</b> 🦾"
        text = (f"Pilihanmu: {user_choice.capitalize()} {emoji[user_choice]}\n"
                f"Pilihan Bot: {bot_choice.capitalize()} {emoji[bot_choice]}\n\n{result_text}")
        keyboard = [[InlineKeyboardButton("🔄 Main Lagi", callback_data="main_game")],
                    [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]]
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                logger.info(f"Tried to edit message {query.message.message_id} with identical content in play_game. Skipping.")
                await query.answer("Konten tidak berubah.")
            else:
                raise e
    except Exception as e:
        await send_admin_log(context, e, update, "play_game")
        await query.edit_message_text("Maaf, terjadi kesalahan pada game.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

# --- FITUR BARU: Password Generator ---
async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        
        length = 16
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(length))
        
        text = (
            f"🔐 <b>Password Baru Dibuat</b>\n\n"
            f"Ini adalah password Anda yang aman:\n\n"
            f"<code>{safe_html(password)}</code>\n\n"
            f"<i>Klik pada password untuk menyalinnya. Harap simpan di tempat yang aman.</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Buat Lagi", callback_data="gen_password")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    except Exception as e:
        await send_admin_log(context, e, update, "generate_password")
        await query.edit_message_text("Maaf, terjadi kesalahan saat membuat password.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

# --- FITUR BARU & PERBAIKAN: Media Downloader ---
async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg = None
    downloaded_files = [] # Untuk melacak semua file yang diunduh
    try:
        status_msg = await update.message.reply_text("📥 <b>Mengunduh media...</b> Ini mungkin akan memakan waktu.", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)

        file_path_template = f"media_{update.effective_message.id}_%(id)s.%(ext)s"
        
        # --- FIX: Pass URL to get_ytdlp_options ---
        ydl_opts = get_ytdlp_options(url=url)
        ydl_opts['outtmpl'] = file_path_template
        ydl_opts['max_filesize'] = MAX_UPLOAD_FILE_SIZE_BYTES
        
        info_dict = None
        try:
            info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=True)
            if not info_dict:
                raise yt_dlp.utils.DownloadError("Proses unduh tidak mengembalikan informasi.")

        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            error_str = str(e).lower()
            reply_text = "Maaf, terjadi kesalahan yang tidak diketahui saat mengunduh."
            admin_log_sent = False 
            
            # --- START PERBAIKAN: Penanganan error yang lebih spesifik ---
            if '[instagram]' in error_str and 'no video formats found' in error_str:
                reply_text = (
                    "❌ <b>Gagal Mengunduh.</b>\n\n"
                    "Postingan ini sepertinya tidak mengandung video, mungkin hanya foto. Bot ini sedang difokuskan untuk mengunduh video dari tautan media umum.\n\n"
                    "Penyebab lain bisa jadi karena postingan ini privat atau Instagram baru saja mengubah sistemnya."
                )
                admin_alert = f"Gagal mengunduh dari Instagram ({url}) karena 'No video formats found'. Kemungkinan ini adalah postingan foto, privat, atau extractor yt-dlp perlu diperbarui."
                await send_admin_log(context, e, update, "handle_media_download (Instagram No Video)", custom_message=admin_alert)
                admin_log_sent = True
            # --- AKHIR PERBAIKAN ---

            elif ('unsupported url' in error_str and 'login' in url) or \
               ('this content is only available for registered users' in error_str) or \
               ('private' in error_str or 'login required' in error_str):
                reply_text = "❌ <b>Gagal!</b> Konten ini bersifat pribadi atau memerlukan login.\n\n" \
                             "<i>Pastikan Admin telah mengonfigurasi cookies untuk situs ini (Instagram, Twitter, dll.).</i>"
                admin_alert = f"Gagal mengunduh {url} karena masalah otentikasi. " \
                              f"Pastikan GENERIC_COOKIES_BASE64 sudah diatur dan valid untuk situs ini. Error: {e}"
                await send_admin_log(context, e, update, "handle_media_download (Auth Error)", custom_message=admin_alert)
                admin_log_sent = True
            
            elif 'no video could be found' in error_str or 'no formats' in error_str or 'is not a valid URL' in error_str:
                reply_text = "❌ <b>Gagal!</b> Link ini sepertinya tidak mengandung media (video/gambar) yang dapat diunduh."
            elif 'unavailable' in error_str:
                reply_text = "❌ <b>Gagal!</b> Konten ini tidak tersedia atau telah dihapus."
            
            logger.warning(f"yt-dlp error for URL {url}: {e}")

            if not admin_log_sent:
                admin_alert = f"Gagal mengunduh {url}. Error: {e}"
                await send_admin_log(context, e, update, "handle_media_download (DownloadError)", custom_message=admin_alert)

            if status_msg:
                await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return

        # --- START FIX v16.17: Logika pengambilan file yang lebih profesional ---
        files_to_process = []
        
        # 1. Coba 'requested_downloads' dulu (paling ideal)
        if info_dict.get('requested_downloads'):
            files_to_process = info_dict['requested_downloads']

        # 2. Jika tidak ada, cek 'entries' (carousel/album)
        elif info_dict.get('entries'):
            await status_msg.edit_text(f"📥 <b>Album/Carousel terdeteksi.</b> Mengunduh {len(info_dict['entries'])} file...", parse_mode=ParseMode.HTML)
            # Ambil semua entry yang *memiliki* path file (baik 'filepath' atau '_filename')
            files_to_process = [
                entry for entry in info_dict.get('entries', []) 
                if entry and (entry.get('filepath') or entry.get('_filename'))
            ]

        # 3. Jika bukan 'entries', pasti file tunggal. Cek path di info_dict utama.
        elif info_dict.get('filepath') or info_dict.get('_filename'):
            # Jika _filename ada tapi filepath tidak, salin
            if info_dict.get('_filename') and not info_dict.get('filepath'):
                info_dict['filepath'] = info_dict.get('_filename')
            files_to_process = [info_dict]

        # 4. Jika masih kosong, baru angkat error
        if not files_to_process:
            logger.warning(f"info_dict structure keys for {url}: {list(info_dict.keys())}")
            logger.warning(f"info_dict 'requested_downloads' content: {info_dict.get('requested_downloads')}")
            raise ValueError("Tidak ada file yang berhasil diunduh dari metadata yt-dlp. (files_to_process empty)")
        # --- END FIX v16.17 ---

        await status_msg.edit_text(f"📤 <b>Mengirim {len(files_to_process)} file...</b>", parse_mode=ParseMode.HTML)
        
        for i, file_info in enumerate(files_to_process):
            # --- FIX v16.17: Dapatkan path dari 'filepath' ATAU '_filename' ---
            file_path = file_info.get('filepath') or file_info.get('_filename')
            
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"File path not found for entry {i}, skipping. Info: {file_info}")
                continue

            downloaded_files.append(file_path) # Tambahkan ke daftar untuk dihapus nanti
            
            title = info_dict.get('title', 'Media')
            uploader = info_dict.get('uploader', 'Tidak diketahui')

            # --- FIX v16.17: Tentukan caption yang lebih baik ---
            # Coba dapatkan judul dari entry individual, fallback ke judul utama
            entry_title = file_info.get('title', title)
            # Jika judul entry adalah 'NA' atau sama dengan judul utama, gunakan format sederhana
            if entry_title == 'NA' or entry_title == title or not entry_title:
                caption = f"<b>{safe_html(title)}</b> ({i+1}/{len(files_to_process)})\n"
            else:
                caption = f"<b>{safe_html(entry_title)}</b>\n<i>(dari Album: {safe_html(title)})</i>\n"
            
            caption += f"<i>oleh {safe_html(uploader)}</i>\n\nDiunduh dengan @{context.bot.username}"
            # --- END FIX v16.17 ---
            
            ext = Path(file_path).suffix.lower()
            image_exts = ['.jpg', '.jpeg', '.png', '.webp']
            
            with open(file_path, 'rb') as f:
                if ext in image_exts:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
                    sent_file = await context.bot.send_photo(update.effective_chat.id, photo=f, caption=caption, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
                    sent_file = await context.bot.send_video(update.effective_chat.id, video=f, caption=caption, parse_mode=ParseMode.HTML)
            
            await track_message(context, sent_file)
            await asyncio.sleep(1) # Jeda untuk menghindari rate limit

        await status_msg.delete()

        keyboard_next = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ])
        next_msg = await context.bot.send_message(update.effective_chat.id, "✅ Semua media berhasil diunduh.", reply_markup=keyboard_next)
        await track_message(context, next_msg)
            
    except Exception as e:
        # Menangkap semua error lain yang tidak terduga
        await send_admin_log(context, e, update, "handle_media_download (General)")
        if status_msg:
            try:
                await status_msg.edit_text("Maaf, terjadi kesalahan teknis yang tidak terduga. Admin telah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except Exception:
                pass # Gagal mengedit pesan status, abaikan
    finally:
        for f in downloaded_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    logger.error(f"Gagal menghapus file media {f}: {e}")

# ==============================================================================
# 🚀 FUNGSI UTAMA & FUNGSI BARU UNTUK COOKIES
# ==============================================================================

def validate_cookie_file(cookie_file: str, is_youtube: bool = False) -> bool:
    """
    Validasi file cookies.
    Return True jika valid, False jika ada masalah.
    """
    if not Path(cookie_file).exists():
        logger.error(f"File {cookie_file} tidak ditemukan!")
        return False
    
    try:
        with open(cookie_file, 'r') as f:
            content = f.read()
        
        if not content.strip():
            logger.error(f"File cookie {cookie_file} kosong!")
            return False
            
        # Cek format Netscape
        if '# Netscape HTTP Cookie File' not in content:
            logger.warning(f"⚠️ {cookie_file} bukan format Netscape!")
            logger.warning("Pastikan Anda export dengan extension/tool yang benar")
        
        if not is_youtube:
            # Untuk cookies generik, cek format dan non-empty sudah cukup
            logger.info(f"✅ Validasi dasar {cookie_file} passed")
            return True

        # --- Validasi spesifik YouTube ---
        required_cookies = ['VISITOR_INFO1_LIVE', 'YSC']
        important_cookies = ['LOGIN_INFO', '__Secure-3PSID', '__Secure-3PAPISID']
        
        lines = content.split('\n')
        found_cookies = {cookie: False for cookie in required_cookies + important_cookies}
        expiry_dates = {}
        
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) >= 7:
                cookie_name = parts[5]
                cookie_expiry = parts[4]
                
                if cookie_name in found_cookies:
                    found_cookies[cookie_name] = True
                    try:
                        expiry_dates[cookie_name] = int(cookie_expiry)
                    except ValueError:
                        pass
        
        # Cek cookies wajib
        missing_required = [c for c in required_cookies if not found_cookies[c]]
        if missing_required:
            logger.error(f"❌ Cookies YouTube wajib tidak ditemukan: {', '.join(missing_required)}")
            logger.error("Export ulang cookies dari browser yang sudah login YouTube!")
            return False
        
        # Cek cookies penting (warning saja)
        missing_important = [c for c in important_cookies if not found_cookies[c]]
        if missing_important:
            logger.warning(f"⚠️ Cookies YouTube penting tidak ada: {', '.join(missing_important)}")
            logger.warning("Bot mungkin mengalami masalah dengan video tertentu (age restricted, etc)")
        
        # Cek expiry date
        current_timestamp = int(datetime.now().timestamp())
        for cookie_name, expiry in expiry_dates.items():
            if expiry == 0:  # Session cookie
                continue
                
            if expiry < current_timestamp:
                logger.error(f"❌ Cookie YouTube '{cookie_name}' sudah EXPIRED!")
                logger.error("Export cookies baru dari browser!")
                return False
            
            # Warning jika akan expired dalam 7 hari
            days_remaining = (expiry - current_timestamp) / 86400
            if days_remaining < 7:
                logger.warning(f"⚠️ Cookie YouTube '{cookie_name}' akan expired dalam {days_remaining:.1f} hari!")
                logger.warning("Segera persiapkan cookies baru!")
        
        logger.info(f"✅ Semua validasi cookies {cookie_file} passed")
        return True
        
    except Exception as e:
        logger.error(f"Error saat validasi {cookie_file}: {e}")
        return False

def setup_all_cookies():
    """
    Setup semua cookies (YouTube & Generik) dari environment variables.
    Return (youtube_valid, generic_valid)
    """
    youtube_cookie_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    generic_cookie_b64 = os.environ.get("GENERIC_COOKIES_BASE64")
    
    youtube_valid = False
    generic_valid = False

    # --- Setup YouTube Cookies ---
    if not youtube_cookie_b64:
        logger.error("❌ YOUTUBE_COOKIES_BASE64 tidak ditemukan!")
        logger.error("Fitur Downloader YouTube tidak akan berfungsi.")
    else:
        try:
            cookie_data = base64.b64decode(youtube_cookie_b64).decode('utf-8')
            with open(YOUTUBE_COOKIE_FILE, 'w') as f:
                f.write(cookie_data)
            logger.info(f"✅ File {YOUTUBE_COOKIE_FILE} berhasil dibuat")
            youtube_valid = validate_cookie_file(YOUTUBE_COOKIE_FILE, is_youtube=True)
        except base64.binascii.Error:
            logger.error("❌ YOUTUBE_COOKIES_BASE64 bukan base64 yang valid!")
        except Exception as e:
            logger.error(f"❌ Gagal setup cookies YouTube: {e}")

    # --- Setup Generic Cookies ---
    if not generic_cookie_b64:
        logger.warning("⚠️ GENERIC_COOKIES_BASE64 tidak ditemukan!")
        logger.warning("Fitur Downloader Media (IG, Twitter, dll) mungkin tidak akan berfungsi untuk konten privat.")
    else:
        try:
            cookie_data = base64.b64decode(generic_cookie_b64).decode('utf-8')
            with open(GENERIC_COOKIE_FILE, 'w') as f:
                f.write(cookie_data)
            logger.info(f"✅ File {GENERIC_COOKIE_FILE} berhasil dibuat")
            generic_valid = validate_cookie_file(GENERIC_COOKIE_FILE, is_youtube=False)
        except base64.binascii.Error:
            logger.error("❌ GENERIC_COOKIES_BASE64 bukan base64 yang valid!")
        except Exception as e:
            logger.error(f"❌ Gagal setup cookies generik: {e}")

    return youtube_valid, generic_valid

def get_ytdlp_options(url: str = None):
    """
    Return yt-dlp options dengan konfigurasi optimal.
    Memilih cookie file yang tepat berdasarkan URL.
    """
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False, # Izinkan playlist untuk multi-media
        'rm_cachedir': True,
        'retries': 5,  # Tingkatkan retry
        'fragment_retries': 5,
        'skip_unavailable_fragments': True,  # Skip fragment yang error
        'http_headers': {'User-Agent': CHROME_USER_AGENT},
        'nocheckcertificate': True,
        # Tambahan untuk bypass restriction
        'geo_bypass': True,
        'age_limit': 21,  # Bypass age restriction
    }
    
    # --- START COOKIE LOGIC ---
    cookie_file_to_use = None
    if url:
        if 'youtube.com' in url or 'youtu.be' in url:
            if Path(YOUTUBE_COOKIE_FILE).exists():
                cookie_file_to_use = YOUTUBE_COOKIE_FILE
        else:
            # Untuk semua situs lain (Insta, Twitter, dll.)
            if Path(GENERIC_COOKIE_FILE).exists():
                cookie_file_to_use = GENERIC_COOKIE_FILE

    if cookie_file_to_use:
        opts['cookiefile'] = cookie_file_to_use
        logger.info(f"Menggunakan cookie file: {cookie_file_to_use} for {url}")
    # --- END COOKIE LOGIC ---

    return opts

def main():
    global bot_application

    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak ditemukan! Atur TELEGRAM_BOT_TOKEN di environment variable.")
    
    if not ADMIN_ID:
        logger.warning("TELEGRAM_ADMIN_ID tidak diatur. Laporan eror tidak akan dikirimkan ke admin.")

    # Enhanced cookie setup dengan validasi
    youtube_valid, generic_valid = setup_all_cookies()

    # --- Graceful Shutdown & Timeout ---
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)    # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Kill signal
    print("🔧 Registering shutdown handlers...")

    timeout_config = HTTPXRequest(connect_timeout=10.0, read_timeout=20.0, write_timeout=20.0)
    bot_application = Application.builder().token(TOKEN).request(timeout_config).build()
    # --- AKHIR Graceful Shutdown & Timeout ---
    
    # Tambahkan semua handler ke bot_application
    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
    bot_application.add_handler(CallbackQueryHandler(clear_history, pattern='^clear_history$'))
    bot_application.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan$'))
    bot_application.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)$'))
    bot_application.add_handler(CallbackQueryHandler(show_tools_menu, pattern='^main_tools$'))
    bot_application.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl$'))
    bot_application.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+$'))
    bot_application.add_handler(CallbackQueryHandler(show_package_details, pattern=r'^pkg_\d+_[a-z0-9_]+$'))
    bot_application.add_handler(CallbackQueryHandler(prompt_for_action, pattern=r'^ask_for_(number|qr|youtube|currency|media_link)$'))
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    bot_application.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    bot_application.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    bot_application.add_handler(CallbackQueryHandler(handle_youtube_download_choice, pattern=r'^yt_dl\|.+'))
    bot_application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))


    print(f"🤖 Bot Pulsa Net (v16.17 - Professional Photo & Album Downloader) sedang berjalan...")
    
    # --- Laporan Status Cookie Baru ---
    if youtube_valid:
        print("✅ YouTube Downloader: AKTIF")
    else:
        print("❌ YouTube Downloader: NONAKTIF (YOUTUBE_COOKIES_BASE64 invalid/hilang)")
    
    if generic_valid:
        print("✅ Generic Media Downloader (IG, dll.): AKTIF")
    else:
        print("⚠️ Generic Media Downloader (IG, dll.): MODE TERBATAS (GENERIC_COOKIES_BASE64 invalid/hilang)")

    if not youtube_valid or not generic_valid:
        logger.error("=" * 60)
        logger.error("PERINGATAN: Satu atau lebih fitur unduh media mungkin TIDAK AKAN BEKERJA!")
        logger.error("Segera perbaiki masalah cookies untuk mengaktifkan semua fitur.")
        logger.error("=" * 60)
        
    print("💡 Tekan Ctrl+C untuk shutdown dengan aman")
    print("=" * 60)

    # Menjalankan bot dengan error handling
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
