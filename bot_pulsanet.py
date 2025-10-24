# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet.py
# Developer: frd099
# Versi: 17.3 (Perbaikan Stabilitas & Error Handling)
#
# CHANGELOG v17.3 (Fitur Baru & Perbaikan):
# - FIX (Kritis): Memperbaiki `TypeError: '>' not supported between 'int' and 'NoneType'`
#   di `handle_media_download` dengan memastikan semua nilai perbandingan memiliki
#   default numerik dan tidak pernah `None`.
# - FIX (Error Handling): Menambahkan penanganan spesifik untuk error `rate-limit` dari YouTube.
#   Bot sekarang akan memberi tahu pengguna dengan jelas jika server dibatasi oleh YouTube,
#   alih-alih menampilkan error generik.
# - ADD (Stabilitas): Menambahkan asyncio.Semaphore untuk membatasi jumlah proses
#   downloader (yt-dlp) yang berjalan bersamaan.
# - ADD (Stabilitas): Mengimplementasikan asyncio.Timeout pada semua fungsi downloader
#   untuk mencegah bot macet (stuck) saat menganalisis link.
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
# FIX 1: Import Error - ZoneInfo
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Jika zoneinfo tidak tersedia (Python < 3.9), gunakan backports
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        # Logger belum tentu terdefinisi di sini, jadi gunakan print
        print("❌ CRITICAL: 'zoneinfo' or 'backports.zoneinfo' not found. Please install: pip install backports.zoneinfo tzdata")
        sys.exit(1) # Keluar jika tidak ada library timezone
from pathlib import Path

# --- Import library baru ---
import qrcode
from PIL import Image
import yt_dlp
import phonenumbers
from phonenumbers import carrier, geocoder, phonenumberutil
# FIX 2: pycountry perlu di-install terpisah
try:
    import pycountry # SOLUSI: Tambahkan ke requirements.txt atau 'pip install pycountry'
except ImportError:
    print("❌ CRITICAL: 'pycountry' not found. Please install: pip install pycountry")
    sys.exit(1) # Keluar jika pycountry tidak ada

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

# --- File Cookie ---
YOUTUBE_COOKIE_FILE = 'youtube_cookies.txt'
GENERIC_COOKIE_FILE = 'generic_cookies.txt'

# --- Konfigurasi Stabilitas & Performa Downloader ---
DOWNLOADER_SEMAPHORE = asyncio.Semaphore(2)
DOWNLOAD_ANALYSIS_TIMEOUT = 90.0

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
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(bot_application.stop())
                loop.create_task(bot_application.shutdown())
            print("✅ Bot berhasil dihentikan dengan aman")
        except Exception as e:
            print(f"⚠️ Error saat shutdown: {e}")

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
        if re.match(r'^(www\.|[a-zA-Z0-9-]+)\.(com|id|net|org|xyz|co\.id|ac\.id|sch\.id|web\.id|my\.id|io|dev)(/.*)?$', text, re.IGNORECASE):
            return f"https://{text}"
    phone_match = re.match(r'^(\+?62|0)8[0-9]{8,12}$', text.replace(' ', '').replace('-', ''))
    if phone_match:
        number = phone_match.group(0).replace(' ', '').replace('-', '')
        if number.startswith('08'):
            number = '+62' + number[1:]
        elif number.startswith('62') and not number.startswith('+'):
            number = '+' + number
        return f"tel:{number}"
    return text

def format_bytes(size):
    if size is None: return "N/A"
    try:
        size = float(size)
    except (ValueError, TypeError):
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    if size < power:
         return f"{int(size)} {power_labels[0]}"
    while size >= power and n < len(power_labels) - 1:
        size /= power
        n += 1
    if size == int(size):
        return f"{int(size)} {power_labels[n]}"
    else:
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
    try:
        if not phone_number_str.startswith('+'):
            if phone_number_str.startswith('08'):
                 phone_number_str = '+62' + phone_number_str[1:]
            else:
                 phone_number_str = '+' + phone_number_str
        phone_number = phonenumbers.parse(phone_number_str, None)
        if not phonenumbers.is_valid_number(phone_number):
            return f"❌ Nomor <code>{safe_html(phone_number_str)}</code> tidak valid."
        country_code = phone_number.country_code
        region_code = phonenumberutil.region_code_for_country_code(country_code)
        try:
            country = pycountry.countries.get(alpha_2=region_code)
            country_name = country.name if country else "Tidak Diketahui"
            country_flag = country.flag if hasattr(country, 'flag') else "❓"
        except Exception:
             country_name = region_code
             country_flag = "❓"
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
            f"<b>✅ Hasil Pengecekan untuk <code>{safe_html(phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))}</code></b>\n"
            f"-----------------------------------------\n"
            f"<b>Negara:</b> {country_flag} {country_name} (+{country_code})\n"
            f"<b>Valid:</b> ✅ Ya\n"
            f"<b>Tipe:</b> {number_type}\n"
            f"<b>Operator Asli:</b> {carrier_name}\n"
            f"<i>(ℹ️ Info operator mungkin tidak akurat jika nomor sudah porting)</i>"
        )
        return output
    except phonenumberutil.NumberParseException:
        return f"❌ Format nomor <code>{safe_html(phone_number_str)}</code> salah. Harap gunakan format internasional (contoh: +628123...). Pengguna disarankan untuk mengirimkan nomor dalam format internasional."
    except Exception as e:
        logger.error(f"Error di get_provider_info_global: {e}")
        return "⚠️ Terjadi kesalahan saat memproses nomor."

def run_yt_dlp_sync(ydl_opts, url, download=False):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            logger.error(f"Error di dalam yt-dlp thread: {e}")
            raise

# ==============================================================================
# 🤖 FUNGSI HANDLER BOT
# ==============================================================================

keyboard_error_back = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]])
keyboard_back_to_tools = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]])

async def send_admin_log(context: ContextTypes.DEFAULT_TYPE, error: Exception, update: Update, from_where: str, custom_message: str = ""):
    if not ADMIN_ID:
        logger.warning("⚠️ TELEGRAM_ADMIN_ID tidak diatur. Log eror tidak akan dikirim.")
        return
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)
    user = update.effective_user if update.effective_user else "N/A (Update None)"
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user_mention = user.mention_html() if hasattr(user, 'mention_html') else f"ID: {user.id if hasattr(user, 'id') else 'N/A'}"
    actionable_message = f"<b>🚨 Pesan Aksi Admin:</b> {custom_message}\n\n" if custom_message else ""
    admin_message = (
        f"‼️ <b>BOT ERROR LOG</b> ‼️\n\n"
        f"{actionable_message}"
        f"<b>Fungsi:</b> <code>{from_where}</code>\n"
        f"<b>User:</b> {user_mention}\n"
        f"<b>Chat ID:</b> <code>{chat_id}</code>\n\n"
        f"<b>Tipe Error:</b> <code>{type(error).__name__}</code>\n"
        f"<b>Pesan Error:</b>\n<pre>{safe_html(str(error))}</pre>\n\n"
        f"<b>Traceback (Ringkas):</b>\n<pre>{safe_html(tb_string[-2000:])}</pre>"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"❌ KRITIS: Gagal mengirim log eror ke admin! Error: {e}")

async def track_message(context: ContextTypes.DEFAULT_TYPE, message):
    if message:
        if 'messages_to_clear' not in context.user_data:
            context.user_data['messages_to_clear'] = []
        if len(context.user_data['messages_to_clear']) >= MAX_MESSAGES_TO_TRACK:
            context.user_data['messages_to_clear'] = context.user_data['messages_to_clear'][-(MAX_MESSAGES_TO_TRACK-1):]
        context.user_data['messages_to_clear'].append(message.message_id)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    loading_msg = None
    try:
        if update.callback_query:
            await update.callback_query.answer("⏳ Memulai pembersihan riwayat...")
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
            except Exception: pass
        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 <b>Sedang menghapus pesan...</b> Mohon tunggu.", parse_mode=ParseMode.HTML)
        messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))
        messages_to_clear = messages_to_clear[-MAX_MESSAGES_TO_DELETE_PER_BATCH:]
        delete_tasks = []
        for msg_id in messages_to_clear:
            if msg_id != loading_msg.message_id:
                 delete_tasks.append(context.bot.delete_message(chat_id=chat_id, message_id=msg_id))
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        fail_count = len(results) - success_count
        if fail_count > 0:
             logger.warning(f"Gagal menghapus {fail_count} pesan di chat {chat_id}.")
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception: pass
        context.user_data['messages_to_clear'] = []
        confirmation_text = (f"✅ <b>Pembersihan Selesai!</b>\n\nBerhasil menghapus <b>{success_count}</b> pesan dari sesi ini.")
        sent_msg = await context.bot.send_message(chat_id=chat_id, text=confirmation_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
        await track_message(context, sent_msg)
    except Exception as e:
        await send_admin_log(context, e, update, "clear_history")
        if loading_msg:
             try: await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
             except Exception: pass
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="❌ Maaf, terjadi kesalahan saat membersihkan chat.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except Exception as e_inner:
            logger.error(f"❌ Gagal mengirim pesan error di clear_history: {e_inner}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sent_message = None
    try:
        context.user_data.pop('state', None)
        if update.message and update.message.text == '/start':
            await track_message(context, update.message)
        user = update.effective_user
        try:
            jakarta_tz = ZoneInfo("Asia/Jakarta")
            now = datetime.now(jakarta_tz)
            hour = now.hour
            if 5 <= hour < 11: greeting, icon = "Selamat Pagi", "☀️"
            elif 11 <= hour < 15: greeting, icon = "Selamat Siang", "🌤️"
            elif 15 <= hour < 18: greeting, icon = "Selamat Sore", "🌥️"
            else: greeting, icon = "Selamat Malam", "🌙"
        except Exception as tz_error:
             logger.warning(f"⚠️ Gagal mendapatkan waktu Jakarta: {tz_error}. Menggunakan sapaan default.")
             greeting, icon = "Halo", "👋"
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
            "Pilih layanan yang Anda butuhkan dari menu di bawah ini:"
        )
        keyboard = [
            [InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), InlineKeyboardButton("💰 Pulsa Reguler", callback_data="main_pulsa")],
            [InlineKeyboardButton("🔍 Cek Info Nomor", callback_data="ask_for_number"), InlineKeyboardButton("🛠️ Tools & Hiburan", callback_data="main_tools")],
            [InlineKeyboardButton("📊 Cek Kuota (XL/Axis)", url="https://sidompul.kmsp-store.com/"), InlineKeyboardButton("🆘 Bantuan", callback_data="main_bantuan")],
            [InlineKeyboardButton("🗑️ Bersihkan Chat", callback_data="clear_history")],
            [InlineKeyboardButton("🌐 Kunjungi Website Kami", url="https://pulsanet.kesug.com/beli.html")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                await update.callback_query.answer()
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    logger.info(f"Pesan {update.callback_query.message.message_id} tidak diubah (start).")
                    await update.callback_query.answer("Menu utama.")
                else:
                    raise e
        else:
            for attempt in range(3):
                try:
                    sent_message = await context.bot.send_message(
                        chat_id=chat_id, text=main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
                    )
                    await track_message(context, sent_message)
                    break
                except TimedOut:
                    logger.warning(f"⚠️ Percobaan {attempt + 1} mengirim menu start timeout. Mencoba lagi...")
                    if attempt < 2: await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Error mengirim menu start (percobaan {attempt+1}): {e}")
                    if attempt == 2: raise
            if not sent_message:
                raise TimedOut("❌ Gagal mengirim menu utama setelah 3 kali percobaan.")
    except Exception as e:
        await send_admin_log(context, e, update, "start")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="❌ Maaf, terjadi kesalahan saat memuat menu utama.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except Exception as e_inner:
             logger.error(f"❌ Gagal mengirim pesan error di start: {e_inner}")

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        product_type_key = query.data.split('_')[1]
        product_type_name = "Paket Data 📶" if product_type_key == "paket" else "Pulsa Reguler 💰"
        operators = {"XL": "🔵", "Axis": "🟣", "Tri": "🔴", "Telkomsel": "🟠", "Indosat": "🟡", "By.U": "⚪"}
        op_items = list(operators.items())
        keyboard = []
        for i in range(0, len(op_items), 2):
            row = [InlineKeyboardButton(f"{icon} {op}", callback_data=f"list_{product_type_key}_{op.lower()}") for op, icon in op_items[i:i+2]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
        text = f"Anda memilih kategori <b>{product_type_name}</b>.\nSilakan pilih provider:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (operator menu).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_operator_menu")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("🤝 Akrab", callback_data="list_paket_xl_akrab"), InlineKeyboardButton("🥳 Bebas Puas", callback_data="list_paket_xl_bebaspuas")],
            [InlineKeyboardButton("⭕️ Circle", callback_data="list_paket_xl_circle"), InlineKeyboardButton("🚀 Paket Lainnya", callback_data="list_paket_xl_paket")],
            [InlineKeyboardButton("⬅️ Kembali ke Provider", callback_data="main_paket")]
        ]
        text = "<b>Pilihan Paket Data XL 🔵</b>\n\nSilakan pilih jenis paket di bawah ini:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (XL submenu).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_xl_paket_submenu")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        data_parts = query.data.split('_')
        await query.answer()
        product_type_key = data_parts[1]
        category_key = data_parts[2]
        special_type_key = data_parts[3] if len(data_parts) > 3 else None
        titles = {"tri": "Tri 🔴", "axis": "Axis 🟣", "telkomsel": "Telkomsel 🟠", "indosat": "Indosat 🟡", "by.u": "By.U ⚪", "xl": "XL 🔵"}
        base_title = titles.get(category_key, category_key.capitalize())
        if special_type_key:
            products = get_products(category=category_key, special_type=special_type_key)
            title_map = {"akrab": "Paket Akrab 🤝", "bebaspuas": "Paket Bebas Puas 🥳", "circle": "Paket Circle ⭕️", "paket": "Paket Lainnya 🚀"}
            title = f"<b>{base_title} - {title_map.get(special_type_key, special_type_key.capitalize())}</b>"
            back_cb = "list_paket_xl"
        else:
            products = get_products(category=category_key, product_type=product_type_key)
            product_name = 'Paket Data 📶' if product_type_key == 'paket' else 'Pulsa Reguler 💰'
            title = f"<b>{base_title} - {product_name}</b>"
            back_cb = f"main_{product_type_key}"
        if not products:
            text = "ℹ️ Mohon maaf, produk untuk kategori ini belum tersedia."
            keyboard = [[InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            return
        sorted_keys = sorted(products.keys(), key=lambda k: PRICES.get(k, 0))
        keyboard = []
        for key in sorted_keys:
            short_name = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', products[key], flags=re.I).replace('Paket ', '')
            price_str = f"Rp{PRICES.get(key, 0):,}".replace(",", ".")
            button_text = f"{short_name} - {price_str}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=key)])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)])
        text = f"{title}\n\nSilakan pilih produk yang Anda inginkan:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (product list).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_product_list")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        package_key = query.data
        await query.answer()
        info = ALL_PACKAGES_DATA.get(package_key, {})
        category = info.get('category', '').lower()
        p_type = info.get('type', '').lower()
        product_type_key = 'pulsa' if p_type == 'pulsa' else 'paket'
        if category == 'xl' and product_type_key == 'paket':
            back_data = f"list_paket_xl_{p_type}" if p_type in ['akrab', 'bebaspuas', 'circle'] else "list_paket_xl_paket"
        else:
            back_data = f"list_{product_type_key}_{category}"
        keyboard = [
            [InlineKeyboardButton("🛒 Beli Sekarang (Website)", url="https://pulsanet.kesug.com/beli.html")],
            [InlineKeyboardButton("⬅️ Kembali ke Daftar Produk", callback_data=back_data)],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]
        ]
        description = PAKET_DESCRIPTIONS.get(package_key, "ℹ️ Informasi produk tidak ditemukan.")
        await query.edit_message_text(description, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (package details).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_package_details")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        await query.edit_message_text(PAKET_DESCRIPTIONS["bantuan"], reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (bantuan).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_bantuan")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        text = "<b>🛠️ Tools & Hiburan</b>\n\nPilih salah satu alat atau hiburan yang tersedia di bawah ini:"
        keyboard = [
            [InlineKeyboardButton("🖼️ Buat QR Code", callback_data="ask_for_qr"), InlineKeyboardButton("💹 Kalkulator Kurs", callback_data="ask_for_currency")],
            [InlineKeyboardButton("▶️ YouTube Downloader", callback_data="ask_for_youtube"), InlineKeyboardButton("🔗 Media Downloader", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("🔐 Buat Password", callback_data="gen_password"), InlineKeyboardButton("🎮 Mini Game", callback_data="main_game")],
            [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (tools menu).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_tools_menu")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

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
                    "Silakan kirimkan nomor HP yang ingin Anda periksa.\n"
                    "Format internasional (<code>+62...</code>) sangat disarankan untuk akurasi.")
            back_button_callback = "back_to_start"
        elif action == "ask_for_qr":
            context.user_data['state'] = 'awaiting_qr_text'
            text = ("<b>🖼️ Generator QR Code</b>\n\nKirimkan teks, tautan, nomor HP, atau informasi apa pun yang ingin Anda jadikan QR Code.")
        elif action == "ask_for_youtube":
            context.user_data['state'] = 'awaiting_youtube_link'
            text = ("<b>▶️ YouTube Downloader (Mode Link)</b>\n\nKirimkan link video YouTube (youtube.com atau youtu.be) untuk mendapatkan link unduhannya.")
        elif action == "ask_for_media_link":
            context.user_data['state'] = 'awaiting_media_link'
            text = ("<b>🔗 Media Downloader Universal (Mode Link)</b>\n\n"
                    "Kirimkan link dari Instagram, Twitter/X, TikTok, Facebook, dll. untuk mendapatkan link unduhan video atau gambar.")
        elif action == "ask_for_currency":
            context.user_data['state'] = 'awaiting_currency'
            text = ("<b>💹 Kalkulator Kurs Mata Uang</b>\n\n"
                    "Kirimkan permintaan konversi Anda dalam format:\n"
                    "<code>[jumlah] [kode_asal] to [kode_tujuan]</code>\n\n"
                    "<b>Contoh:</b>\n"
                    "• <code>100 USD to IDR</code>\n"
                    "• <code>50 EUR JPY</code> (tanpa 'to' juga bisa)\n"
                    "• <code>1000000 IDR MYR</code>")
        else:
            logger.warning(f"Aksi tidak dikenal di prompt_for_action: {action}")
            return
        keyboard = [[InlineKeyboardButton("⬅️ Batal & Kembali", callback_data=back_button_callback)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (prompt).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "prompt_for_action")
        try:
            await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
        except Exception as e_inner:
             logger.error(f"❌ Gagal mengirim pesan error di prompt_for_action: {e_inner}")

async def handle_currency_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = None
    try:
        status_msg = await update.message.reply_text("💹 Menghitung kurs...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        text = update.message.text.upper()
        match = re.match(r"([\d\.\,]+)\s*([A-Z]{3})\s*(?:TO|IN|)\s*([A-Z]{3})", text)
        if not match:
            await status_msg.edit_text("❌ Format salah. Contoh: <code>100 USD to IDR</code>.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        amount_str, base_curr, target_curr = match.groups()
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
             await status_msg.edit_text("❌ Jumlah tidak valid. Harap masukkan angka.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
             return
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
                f"<i>Kurs 1 {base_curr} ≈ {rate:,.4f} {target_curr}</i>\n"
                f"<a href='https://www.google.com/finance/quote/{base_curr}-{target_curr}'>Sumber data (mungkin sedikit berbeda)</a>"
            )
            await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await status_msg.edit_text(f"❌ Tidak dapat menemukan kurs untuk <b>{target_curr}</b>. Pastikan kode mata uang valid.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except httpx.RequestError as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (RequestError)")
        if status_msg: await status_msg.edit_text("⚠️ Gagal menghubungi layanan kurs. Coba lagi nanti.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_currency_conversion")
        if status_msg: await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_youtube_quality_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg = None
    try:
        status_msg = await context.bot.send_message(
            update.effective_chat.id, "⏳ <b>Menyiapkan antrian...</b>", parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)
        ydl_opts = get_ytdlp_options(url=url)
        info_dict = None
        try:
            async with DOWNLOADER_SEMAPHORE:
                await status_msg.edit_text(
                    "🔍 <b>Menganalisis link YouTube...</b> (Bisa memakan waktu hingga 90 detik)",
                    parse_mode=ParseMode.HTML
                )
                task = asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
                info_dict = await asyncio.wait_for(task, timeout=DOWNLOAD_ANALYSIS_TIMEOUT)
        except asyncio.TimeoutError:
            logger.error(f"Timeout ({DOWNLOAD_ANALYSIS_TIMEOUT}s) saat menganalisis YouTube URL: {url}")
            await status_msg.edit_text(
                "❌ <b>Proses Gagal!</b>\n\nWaktu analisis link habis (timeout).",
                reply_markup=keyboard_back_to_tools, parse_mode=ParseMode.HTML
            )
            return
        except yt_dlp.utils.DownloadError as e:
            error_str = str(e).lower()
            # PERBAIKAN: Tangani error "rate-limited" secara spesifik
            if 'rate-limited' in error_str:
                user_message = ("❌ <b>Layanan YouTube Bermasalah</b>\n\n"
                                "Server kami untuk sementara dibatasi oleh YouTube karena terlalu banyak permintaan. "
                                "Silakan coba lagi nanti (biasanya setelah 1 jam). Admin telah diberitahu.")
                admin_alert = "CRITICAL: YouTube Rate Limit Hit! Server IP is temporarily blocked."
                await send_admin_log(context, e, update, "YouTube Rate Limit", custom_message=admin_alert)
                await status_msg.edit_text(user_message, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                return

            cookie_errors = ['sign in to confirm', 'no suitable proxies', '410 gone', 'unable to extract', 'login required', 'this video requires payment', 'age restricted', 'private video']
            if any(err in error_str for err in cookie_errors):
                admin_alert = "CRITICAL: YouTube Cookie Auth Failed during analysis. Check YOUTUBE_COOKIES_BASE64."
                await send_admin_log(context, e, update, "YouTube Cookie Auth Failed (Analysis)", custom_message=admin_alert)
                user_message = ("❌ <b>Layanan YouTube Downloader bermasalah</b>\n\nAutentikasi YouTube gagal atau video ini memerlukan login/pembayaran/dibatasi usia. Pastikan cookies valid. Admin telah diberitahu.")
                await status_msg.edit_text(user_message, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                return
            elif 'video unavailable' in error_str:
                 await status_msg.edit_text("❌ Video tidak tersedia atau telah dihapus.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                 return
            elif 'georestricted' in error_str:
                 await status_msg.edit_text("❌ Video ini dibatasi secara geografis (tidak tersedia di lokasi server).", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                 return
            raise e
        video_id = info_dict.get('id', '')
        title = info_dict.get('title', 'Video YouTube')
        formats = info_dict.get('formats', [])
        keyboard = []
        video_formats = []
        for f in formats:
            if (f.get('vcodec') != 'none' and f.get('acodec') != 'none' and
                f.get('ext') == 'mp4' and f.get('height') and f.get('height') <= 1080):
                 video_formats.append(f)
        video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
        for f in video_formats[:5]:
            file_size_str = format_bytes(f.get('filesize') or f.get('filesize_approx'))
            label = f"📹 {f['height']}p ({f['ext']}) - {file_size_str}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl_link|{video_id}|{f['format_id']}")])
        audio_formats = []
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('ext') in ['m4a', 'opus', 'mp3']:
                 audio_formats.append(f)
        audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
        for f in audio_formats[:3]:
             file_size_str = format_bytes(f.get('filesize') or f.get('filesize_approx'))
             label = f"🎵 Audio [{f.get('ext', 'audio')}] - {file_size_str}"
             if f.get('abr'):
                 label += f" (~{int(f['abr'])}k)"
             keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl_link|{video_id}|{f['format_id']}")])
        if not keyboard:
            await status_msg.edit_text("❌ Tidak ditemukan format video/audio MP4/M4A yang bisa diunduh untuk link ini.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        keyboard.append([InlineKeyboardButton("⬅️ Batal & Kembali ke Tools", callback_data="main_tools")])
        await status_msg.edit_text(
            f"<b>{safe_html(title)}</b>\n\n✅ Pilih kualitas di bawah ini untuk mendapatkan link unduhan:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await send_admin_log(context, e, update, "show_youtube_quality_options")
        if status_msg:
            await status_msg.edit_text(
                "❌ Maaf, terjadi kesalahan teknis saat menganalisis link YouTube. Tim kami sudah diberitahu.",
                reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML
            )

async def handle_youtube_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    status_msg = None
    try:
        await query.answer("⏳ Mengambil link unduhan...")
        try:
            status_msg = await query.edit_message_text(f"⏳ <b>Mengambil link unduhan...</b>", parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" in str(e): status_msg = query.message
            else: raise e
        _, video_id, format_id = query.data.split('|')
        original_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = get_ytdlp_options(url=original_url)
        info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, original_url, download=False)
        selected_format = None
        for f in info_dict.get('formats', []):
            if f.get('format_id') == format_id:
                selected_format = f
                break
        if not selected_format or not selected_format.get('url'):
            logger.error(f"Format ID {format_id} tidak ditemukan atau tidak memiliki URL di info_dict untuk {video_id}")
            await status_msg.edit_text("❌ Gagal mendapatkan link unduhan untuk format yang dipilih.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        download_url = selected_format.get('url')
        title = info_dict.get('title', 'Video YouTube')
        file_size_str = format_bytes(selected_format.get('filesize') or selected_format.get('filesize_approx'))
        format_note = selected_format.get('format_note', '')
        ext = selected_format.get('ext', 'file')
        is_video = selected_format.get('vcodec') != 'none'
        button_label = f"Unduh {'Video' if is_video else 'Audio'} ({format_note or ext} - {file_size_str})".strip()
        keyboard = [[InlineKeyboardButton(f"🔗 {button_label}", url=download_url)]]
        keyboard.append([InlineKeyboardButton("▶️ Unduh Video Lain", callback_data="ask_for_youtube")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")])
        result_text = (
            f"✅ <b>Link Unduhan Siap!</b>\n\n"
            f"<b>Judul:</b> {safe_html(title)}\n\n"
            f"Klik tombol di bawah untuk mengunduh.\n\n"
            f"⚠️ <i><b>Penting:</b> Link unduhan ini bersifat <b>sementara</b> dan mungkin akan kedaluwarsa setelah beberapa waktu. Segera unduh file Anda.</i>"
        )
        await status_msg.edit_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e).lower()
        cookie_errors = [
            'sign in to confirm', 'no suitable proxies', '410 gone',
            'unable to extract', 'login required', 'this video requires payment',
            'private video', 'members only', 'age restricted'
        ]
        reply_text = f"❌ Error unduh: {str(e)[:100]}..."
        if any(err in error_str for err in cookie_errors):
            admin_alert = ("CRITICAL: YouTube cookie auth failed when getting download link. Check YOUTUBE_COOKIES_BASE64.")
            await send_admin_log(context, e, update, "handle_youtube_download_choice (Cookie/Auth Error)", custom_message=admin_alert)
            reply_text = "❌ Maaf, terjadi kendala teknis (Authentikasi YouTube gagal saat mengambil link)."
        elif 'video unavailable' in error_str:
            reply_text = "❌ Video tidak tersedia atau telah dihapus."
        elif 'georestricted' in error_str:
            reply_text = "❌ Video ini dibatasi secara geografis."
        if status_msg:
             await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
        else:
             await query.message.reply_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_youtube_download_choice")
        if status_msg:
            await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis yang tidak terduga. Tim kami sudah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
        else:
             await query.message.reply_text("❌ Maaf, terjadi kesalahan teknis.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await track_message(context, update.message)
        state = context.user_data.get('state')
        message_text = update.message.text
        phone_pattern = r'(\+?\d{1,3}[\s-]?\d[\d\s-]{7,14}\d)'
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
                    "❌ Format nomor telepon tidak valid atau tidak ditemukan. Gunakan format internasional: `+kode_negara nomor`.",
                    reply_markup=keyboard_next_action, parse_mode=ParseMode.HTML
                )
            await track_message(context, sent_msg)
            context.user_data.pop('state', None)
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
                await loading_msg.delete()
            except Exception as e:
                await send_admin_log(context, e, update, "handle_text_message (QR Code)")
                await loading_msg.edit_text("❌ Maaf, terjadi kesalahan saat membuat QR Code.", reply_markup=keyboard_back_to_tools)
            finally:
                 context.user_data.pop('state', None)
                 keyboard_next = InlineKeyboardMarkup([
                     [InlineKeyboardButton("🖼️ Buat QR Lain", callback_data="ask_for_qr")],
                     [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]])
                 sent_msg2 = await update.message.reply_text("Apa yang ingin Anda lakukan selanjutnya?", reply_markup=keyboard_next)
                 await track_message(context, sent_msg2)
            return
        elif state == 'awaiting_youtube_link':
            if re.search(r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)', message_text):
                await show_youtube_quality_options(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text("❌ Link YouTube tidak valid. Pastikan link mengarah ke video (termasuk Shorts).", reply_markup=keyboard_back_to_tools, parse_mode=ParseMode.HTML)
                await track_message(context, sent_msg)
                return
            context.user_data.pop('state', None)
            return
        elif state == 'awaiting_media_link':
            url_match = re.search(url_pattern, message_text)
            if url_match:
                await handle_media_download(update, context, url_match.group(0))
            else:
                sent_msg = await update.message.reply_text("❌ Link tidak valid. Pastikan Anda mengirimkan tautan (URL) yang benar.", reply_markup=keyboard_back_to_tools, parse_mode=ParseMode.HTML)
                await track_message(context, sent_msg)
                return
            context.user_data.pop('state', None)
            return
        elif state == 'awaiting_currency':
            await handle_currency_conversion(update, context)
            context.user_data.pop('state', None)
            keyboard_next = InlineKeyboardMarkup([
                [InlineKeyboardButton("💹 Hitung Kurs Lain", callback_data="ask_for_currency")],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]])
            sent_msg2 = await update.message.reply_text("Apa yang ingin Anda lakukan selanjutnya?", reply_markup=keyboard_next)
            await track_message(context, sent_msg2)
            return
        numbers = re.findall(phone_pattern, message_text)
        if numbers and len(numbers) <= 3:
            responses = [get_provider_info_global(num.replace(" ", "").replace("-", "")) for num in numbers]
            sent_msg = await update.message.reply_text(
                "💡 <b>Info Nomor Terdeteksi Otomatis:</b>\n\n" + "\n\n---\n\n".join(responses) +
                "\n\n<i>Gunakan '🔍 Cek Info Nomor' dari menu /start untuk cek manual.</i>",
                parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            await track_message(context, sent_msg)
        else:
             pass
    except Exception as e:
        await send_admin_log(context, e, update, "handle_text_message")
        try:
            error_msg = await update.message.reply_text(
                "❌ Maaf, terjadi kesalahan saat memproses pesan Anda.",
                reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML
            )
            await track_message(context, error_msg)
        except Exception as e_inner:
             logger.error(f"❌ Gagal mengirim pesan error di handle_text_message: {e_inner}")

async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        keyboard = [
             [InlineKeyboardButton("Batu 🗿", callback_data="game_play_rock"),
              InlineKeyboardButton("Gunting ✂️", callback_data="game_play_scissors"),
              InlineKeyboardButton("Kertas 📄", callback_data="game_play_paper")],
             [InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]
        ]
        text = "<b>🎮 Game Batu-Gunting-Kertas</b>\n\nAyo bermain! Pilih jagoanmu:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (game menu).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_game_menu")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

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
        keyboard = [
            [InlineKeyboardButton("🔄 Main Lagi", callback_data="main_game")],
            [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (play game).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "play_game")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan pada game.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
        length = 16
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(length))
        text = (
            f"🔐 <b>Password Baru Dibuat</b>\n\n"
            f"Ini adalah password Anda yang aman (16 karakter):\n\n"
            f"<code>{safe_html(password)}</code>\n\n"
            f"<i>ℹ️ Klik pada password untuk menyalinnya. Harap simpan di tempat yang aman dan jangan bagikan kepada siapa pun.</i>"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Buat Lagi", callback_data="gen_password")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
         if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (password gen).")
         else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "generate_password")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan saat membuat password.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg = None
    try:
        status_msg = await update.message.reply_text("⏳ <b>Menyiapkan antrian...</b>", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        ydl_opts = get_ytdlp_options(url=url)
        ydl_opts.pop('outtmpl', None)
        info_dict = None
        try:
            async with DOWNLOADER_SEMAPHORE:
                await status_msg.edit_text(
                    "⏳ <b>Menganalisis link media...</b> (Proses ini bisa memakan waktu hingga 90 detik)",
                    parse_mode=ParseMode.HTML
                )
                task = asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
                info_dict = await asyncio.wait_for(task, timeout=DOWNLOAD_ANALYSIS_TIMEOUT)
            if not info_dict:
                raise yt_dlp.utils.DownloadError("❌ Gagal mendapatkan informasi dari link (hasil kosong).")
        except asyncio.TimeoutError:
            logger.error(f"Timeout ({DOWNLOAD_ANALYSIS_TIMEOUT}s) saat menganalisis URL: {url}")
            await status_msg.edit_text(
                "❌ <b>Proses Gagal!</b>\n\nWaktu analisis link habis (timeout). Ini bisa terjadi jika:\n"
                "  - Situs target sangat lambat merespons.\n"
                "  - Link dilindungi oleh anti-bot yang kuat.\n"
                "  - Koneksi ke server situs bermasalah.",
                reply_markup=keyboard_back_to_tools, parse_mode=ParseMode.HTML
            )
            return
        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            error_str = str(e).lower()
            reply_text = "❌ Maaf, terjadi kesalahan saat menganalisis link."
            if ('unsupported url' in error_str and 'login' in url) or \
               ('this content is only available for registered users' in error_str) or \
               ('private account' in error_str or 'login required' in error_str):
                reply_text = "❌ <b>Gagal!</b> Konten ini bersifat pribadi atau memerlukan login.\n\n" \
                             "<i>Pastikan Admin telah mengonfigurasi cookies (GENERIC_COOKIES_BASE64) untuk situs ini.</i>"
                admin_alert = f"Gagal menganalisis {url} karena masalah otentikasi. Check GENERIC_COOKIES_BASE64. Error: {e}"
                await send_admin_log(context, e, update, "handle_media_download (Auth Error)", custom_message=admin_alert)
            elif 'no media found' in error_str or 'no video could be found' in error_str or 'no formats' in error_str or 'is not a valid URL' in error_str:
                reply_text = "❌ <b>Gagal!</b> Link ini sepertinya tidak valid atau tidak mengandung media (video/gambar) yang dapat diunduh."
            elif 'unavailable' in error_str:
                reply_text = "❌ <b>Gagal!</b> Konten ini tidak tersedia atau telah dihapus."
            logger.warning(f"⚠️ yt-dlp error for URL {url}: {e}")
            if status_msg: await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        media_links = []
        items_to_process = info_dict.get('entries', [info_dict])
        if len(items_to_process) > 1 and all(items_to_process):
            await status_msg.edit_text(f"⏳ <b>Postingan multi-media terdeteksi ({len(items_to_process)} item).</b> Mengambil link...", parse_mode=ParseMode.HTML)
        for i, item in enumerate(items_to_process):
            if not item: continue
            media_url, media_type, file_size_str = None, "Media", "N/A"
            valid_formats = [f for f in item.get('formats', []) if f.get('url') and 'manifest' not in f.get('protocol', '')]
            if valid_formats:
                # PERBAIKAN: Pastikan semua nilai perbandingan adalah angka untuk mencegah TypeError
                best_format = max(valid_formats, key=lambda f: (
                    f.get('preference') or -1,
                    f.get('height') or 0,
                    f.get('width') or 0,
                    f.get('tbr') or 0,
                    (f.get('filesize') or f.get('filesize_approx') or 0)
                ), default=None)
                if best_format:
                    media_url = best_format.get('url')
                    media_type = "Video" if best_format.get('vcodec') != 'none' else "Audio"
                    file_size_str = format_bytes(best_format.get('filesize') or best_format.get('filesize_approx'))
            if not media_url and item.get('url'):
                ext = item.get('ext')
                if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    media_url, media_type, file_size_str = item.get('url'), "Gambar", format_bytes(item.get('filesize'))
                else:
                    media_url, media_type, file_size_str = item.get('url'), "Gambar", format_bytes(item.get('filesize'))
            if not media_url and item.get('thumbnail'):
                media_url, media_type = item.get('thumbnail'), "Gambar (Thumbnail)"
            if media_url:
                item_number = f" {i+1}" if len(items_to_process) > 1 else ""
                label = f"Unduh {media_type}{item_number}"
                if file_size_str != "N/A": label += f" ({file_size_str})"
                media_links.append({'label': label, 'url': media_url})
        if not media_links:
            logger.warning(f"⚠️ Tidak ditemukan link media yang bisa diekstrak dari info_dict untuk {url}")
            await status_msg.edit_text("❌ Tidak dapat menemukan link unduhan media dari URL ini.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return
        keyboard = []
        for link_info in media_links[:10]:
            keyboard.append([InlineKeyboardButton(f"🔗 {link_info['label']}", url=link_info['url'])])
        keyboard.append([InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")])
        keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")])
        title = info_dict.get('title', 'Media')
        uploader = info_dict.get('uploader', 'Tidak diketahui')
        result_text = (
            f"✅ <b>Link Unduhan Siap ({len(media_links)} item)!</b>\n\n"
            f"<b>Judul/Deskripsi:</b> {safe_html(title)}\n"
            f"<b>Oleh:</b> {safe_html(uploader)}\n\n"
            f"Klik tombol di bawah untuk mengunduh.\n\n"
            f"⚠️ <i><b>Penting:</b> Link unduhan bersifat <b>sementara</b> dan bisa kedaluwarsa. Segera unduh file Anda.</i>"
        )
        await status_msg.edit_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_media_download (General)")
        if status_msg:
            await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis yang tidak terduga. Admin telah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

# ==============================================================================
# 🚀 FUNGSI UTAMA & SETUP COOKIES
# ==============================================================================

def validate_cookie_file(cookie_file: str, is_youtube: bool = False) -> bool:
    path = Path(cookie_file)
    if not path.exists():
        logger.error(f"❌ File cookie {cookie_file} tidak ditemukan!")
        return False
    try:
        content = path.read_text(encoding='utf-8')
        if not content.strip():
            logger.error(f"❌ File cookie {cookie_file} kosong!")
            return False
        if '# Netscape HTTP Cookie File' not in content and '# HTTP Cookie File' not in content:
            logger.warning(f"⚠️ {cookie_file} mungkin bukan format Netscape standar.")
        if not is_youtube:
            logger.info(f"✅ Validasi dasar {cookie_file} berhasil.")
            return True
        required_cookies, important_cookies = ['VISITOR_INFO1_LIVE', 'YSC'], ['LOGIN_INFO', '__Secure-3PSID', '__Secure-3PAPISID']
        found_cookies = {cookie: False for cookie in required_cookies + important_cookies}
        current_timestamp = int(datetime.now().timestamp())
        expired_found, near_expiry_found = False, False
        for line in content.splitlines():
            if line.startswith('#') or not line.strip(): continue
            try:
                parts = line.split('\t')
                if len(parts) >= 7:
                    expiry_timestamp, cookie_name = int(parts[4]), parts[5]
                    if cookie_name in found_cookies:
                        found_cookies[cookie_name] = True
                        if expiry_timestamp != 0:
                             if expiry_timestamp < current_timestamp:
                                 logger.error(f"❌ Cookie YouTube '{cookie_name}' sudah EXPIRED!")
                                 expired_found = True
                             else:
                                 days_remaining = (expiry_timestamp - current_timestamp) / 86400
                                 if days_remaining < 7:
                                     logger.warning(f"⚠️ Cookie YouTube '{cookie_name}' akan expired dalam {days_remaining:.1f} hari!")
                                     near_expiry_found = True
            except (ValueError, IndexError):
                 logger.warning(f"⚠️ Baris cookie tidak valid di {cookie_file}: {line[:50]}...")
                 continue
        missing_required = [c for c in required_cookies if not found_cookies[c]]
        if missing_required:
            logger.error(f"❌ Cookies YouTube wajib tidak ditemukan di {cookie_file}: {', '.join(missing_required)}")
            logger.error("   Pastikan export cookies dari youtube.com setelah login.")
            return False
        missing_important = [c for c in important_cookies if not found_cookies[c]]
        if missing_important:
            logger.warning(f"⚠️ Cookies YouTube penting (untuk login) tidak ada: {', '.join(missing_important)}")
            logger.warning("   Fitur untuk video restricted/private mungkin tidak berfungsi.")
        if expired_found:
             logger.error("❌ Ditemukan cookie YouTube yang sudah expired. Harap export ulang!")
             return False
        if near_expiry_found:
             logger.warning("⚠️ Beberapa cookie YouTube akan segera expired. Siapkan cookies baru.")
        logger.info(f"✅ Validasi cookies YouTube ({cookie_file}) berhasil.")
        return True
    except Exception as e:
        logger.error(f"❌ Error saat validasi {cookie_file}: {e}")
        return False

def setup_all_cookies():
    youtube_cookie_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    generic_cookie_b64 = os.environ.get("GENERIC_COOKIES_BASE64")
    youtube_valid, generic_valid = False, False
    if not youtube_cookie_b64:
        logger.error("❌ YOUTUBE_COOKIES_BASE64 tidak ditemukan!")
        logger.error("   Fitur YouTube Downloader tidak akan berfungsi optimal.")
    else:
        try:
            cookie_data = base64.b64decode(youtube_cookie_b64).decode('utf-8')
            with open(YOUTUBE_COOKIE_FILE, 'w', encoding='utf-8') as f: f.write(cookie_data)
            logger.info(f"✅ File {YOUTUBE_COOKIE_FILE} berhasil dibuat/ditulis ulang.")
            youtube_valid = validate_cookie_file(YOUTUBE_COOKIE_FILE, is_youtube=True)
        except (base64.binascii.Error, ValueError):
            logger.error("❌ YOUTUBE_COOKIES_BASE64 bukan format base64 yang valid!")
        except Exception as e:
            logger.error(f"❌ Gagal setup cookies YouTube: {e}")
    if not generic_cookie_b64:
        logger.warning("⚠️ GENERIC_COOKIES_BASE64 tidak ditemukan.")
        logger.warning("   Fitur Media Downloader (IG, dll.) mungkin tidak berfungsi untuk konten private/login.")
    else:
        try:
            cookie_data = base64.b64decode(generic_cookie_b64).decode('utf-8')
            with open(GENERIC_COOKIE_FILE, 'w', encoding='utf-8') as f: f.write(cookie_data)
            logger.info(f"✅ File {GENERIC_COOKIE_FILE} berhasil dibuat/ditulis ulang.")
            generic_valid = validate_cookie_file(GENERIC_COOKIE_FILE, is_youtube=False)
        except (base64.binascii.Error, ValueError):
            logger.error("❌ GENERIC_COOKIES_BASE64 bukan format base64 yang valid!")
        except Exception as e:
            logger.error(f"❌ Gagal setup cookies generik: {e}")
    return youtube_valid, generic_valid

def get_ytdlp_options(url: str = None):
    opts = {
        'quiet': True, 'no_warnings': True, 'noplaylist': False, 'extract_flat': False,
        'rm_cachedir': True, 'retries': 5, 'fragment_retries': 5, 'skip_unavailable_fragments': True,
        'http_headers': {'User-Agent': CHROME_USER_AGENT}, 'nocheckcertificate': True,
        'geo_bypass': True, 'age_limit': 99,
    }
    cookie_file_to_use = None
    if url and isinstance(url, str):
        if 'youtube.com' in url or 'youtu.be' in url:
            if Path(YOUTUBE_COOKIE_FILE).exists():
                cookie_file_to_use = YOUTUBE_COOKIE_FILE
                logger.debug(f"Menggunakan cookie YouTube untuk: {url[:50]}...")
        else:
            if Path(GENERIC_COOKIE_FILE).exists():
                cookie_file_to_use = GENERIC_COOKIE_FILE
                logger.debug(f"Menggunakan cookie generik untuk: {url[:50]}...")
    if cookie_file_to_use:
        opts['cookiefile'] = cookie_file_to_use
    return opts

def main():
    global bot_application
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.critical("❌ FATAL: Token bot tidak ditemukan! Atur TELEGRAM_BOT_TOKEN di environment variable.")
        sys.exit(1)
    if not ADMIN_ID:
        logger.warning("⚠️ TELEGRAM_ADMIN_ID tidak diatur. Laporan error tidak akan dikirim ke admin.")
    youtube_valid, generic_valid = setup_all_cookies()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("🔧 Handler shutdown (Ctrl+C / SIGTERM) terdaftar.")
    timeout_config = HTTPXRequest(connect_timeout=15.0, read_timeout=30.0, write_timeout=30.0)
    bot_application = Application.builder().token(TOKEN).request(timeout_config).build()

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
    bot_application.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    bot_application.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    bot_application.add_handler(CallbackQueryHandler(handle_youtube_download_choice, pattern=r'^yt_dl_link\|.+'))
    bot_application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print(f"============================================")
    print(f"🚀 Bot Pulsa Net (v17.3 - Perbaikan Stabilitas)")
    print(f"============================================")
    if youtube_valid: print("✅ YouTube Downloader: AKTIF (Cookies Valid)")
    else: print("❌ YouTube Downloader: MODE TERBATAS / NONAKTIF (Masalah Cookies YouTube)")
    if generic_valid: print("✅ Generic Media Downloader (IG, dll.): AKTIF (Cookies Valid)")
    else: print("⚠️ Generic Media Downloader (IG, dll.): MODE TERBATAS (Masalah Cookies Generik)")
    if not youtube_valid or not generic_valid:
        logger.error("-" * 60)
        logger.error("‼️ PERINGATAN: Satu atau lebih fitur unduh media mungkin TIDAK berfungsi optimal!")
        logger.error("   Pastikan variabel YOUTUBE_COOKIES_BASE64 dan/atau GENERIC_COOKIES_BASE64")
        logger.error("   berisi data cookies base64 yang valid dan terbaru.")
        logger.error("-" * 60)
    print("\n💡 Bot sedang berjalan. Tekan Ctrl+C untuk berhenti dengan aman.")
    print("-" * 60)
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ FATAL ERROR di main loop: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
