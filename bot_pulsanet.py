# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet.py
# Developer: frd099 & AI Contributor
# Versi: 18.1 (Critical Startup Fix)
#
# CHANGELOG v18.1:
# - FIX (Kritis): Mengembalikan semua fungsi handler yang hilang (termasuk 
#   `handle_youtube_download_choice`, `handle_media_download`, dll.) yang 
#   menyebabkan `NameError` dan crash saat bot startup.
# - REFACTOR: Semua perbaikan dari v18.0 dipertahankan. Kode ini sekarang 
#   lengkap, stabil, dan siap untuk produksi.
# ============================================

# --- SARAN DEPENDENSI ---
# pip install python-telegram-bot httpx qrcode Pillow yt-dlp phonenumbers pycountry "backports.zoneinfo; python_version < '3.9'" tzdata

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
import sys
import string
import hashlib
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    except ImportError:
        print("❌ CRITICAL: 'zoneinfo' or 'backports.zoneinfo' not found. Please install: pip install backports.zoneinfo tzdata")
        sys.exit(1)

try:
    import qrcode
    from PIL import Image
    import yt_dlp
    import phonenumbers
    from phonenumbers import carrier, geocoder, phonenumberutil
    import pycountry
except ImportError as e:
    print(f"❌ CRITICAL: Missing dependency - {e.name}. Please ensure all required packages are installed.")
    sys.exit(1)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, BadRequest

# Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# ==============================================================================
# ⚙️ KONFIGURASI & VARIABEL GLOBAL
# ==============================================================================
try:
    ADMIN_ID = int(os.environ.get("TELEGRAM_ADMIN_ID"))
except (ValueError, TypeError):
    ADMIN_ID = None

MAX_MESSAGES_TO_TRACK = 50
MAX_MESSAGES_TO_DELETE_PER_BATCH = 30
CHROME_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BASE_DIR = Path(__file__).parent
YOUTUBE_COOKIE_FILE = BASE_DIR / 'youtube_cookies.txt'
GENERIC_COOKIE_FILE = BASE_DIR / 'generic_cookies.txt'

DOWNLOADER_SEMAPHORE = asyncio.Semaphore(3)
DOWNLOAD_ANALYSIS_TIMEOUT = 120.0
MEDIA_DOWNLOAD_TIMEOUT = httpx.Timeout(10.0, read=300.0)
MAX_PHOTO_SIZE = 50 * 1024 * 1024
MAX_VIDEO_SIZE = 1500 * 1024 * 1024
MAX_QR_TEXT_LENGTH = 500

message_tracking_lock = asyncio.Lock()

keyboard_error_back = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]])
keyboard_back_to_tools = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]])

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
def safe_html(text): return html.escape(str(text))

def smart_truncate(text, length=1020, suffix='...'):
    if len(text) <= length: return text
    cut_off = text.rfind(' ', 0, length)
    if cut_off == -1: cut_off = length
    return text[:cut_off] + suffix

def create_package_key(pkg):
    if not isinstance(pkg, dict) or 'name' not in pkg or 'id' not in pkg:
        logger.error(f"Invalid package data provided: {pkg}")
        return None
    name_slug = re.sub(r'[^a-z0-9_]', '', str(pkg['name']).lower().replace(' ', '_'))
    return f"pkg_{pkg['id']}_{name_slug}"

def format_qr_data(text: str) -> str:
    text = text.strip()
    if not re.match(r'^[a-zA-Z]+://', text):
        if re.match(r'^(www\.|[a-zA-Z0-9-]+)\.(com|id|net|org|xyz|co\.id|ac\.id|sch\.id|web\.id|my\.id|io|dev)(/.*)?$', text, re.IGNORECASE):
            return f"https://{text}"
    phone_match = re.match(r'^(\+?62|0)8[0-9]{8,12}$', text.replace(' ', '').replace('-', ''))
    if phone_match:
        number = phone_match.group(0).replace(' ', '').replace('-', '')
        if number.startswith('08'): number = '+62' + number[1:]
        elif number.startswith('62') and not number.startswith('+'): number = '+' + number
        return f"tel:{number}"
    return text

def format_bytes(size):
    if size is None: return "N/A"
    try: size = float(size)
    except (ValueError, TypeError): return "N/A"
    power, n, power_labels = 1024, 0, {0: 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    if size < power: return f"{int(size)} {power_labels[0]}"
    while size >= power and n < len(power_labels) - 1: size /= power; n += 1
    return f"{int(size)} {power_labels[n]}" if size == int(size) else f"{size:.2f} {power_labels[n]}"

ALL_PACKAGES_DATA = {key: pkg for pkg in ALL_PACKAGES_RAW if (key := create_package_key(pkg)) is not None}
PRICES = {key: data['price'] for key, data in ALL_PACKAGES_DATA.items()}

def get_products(category=None, product_type=None, special_type=None):
    filtered_items = ALL_PACKAGES_DATA.items()
    if category: filtered_items = [i for i in filtered_items if i[1].get('category', '').lower() == category.lower()]
    if special_type: filtered_items = [i for i in filtered_items if i[1].get('type', '').lower() == special_type.lower()]
    elif product_type:
        if category and category.lower() == 'xl' and product_type.lower() == 'paket':
            special_types = ['akrab', 'bebaspuas', 'circle']
            filtered_items = [i for i in filtered_items if i[1].get('type', '').lower() == 'paket' and i[1].get('type').lower() not in special_types]
        else: filtered_items = [i for i in filtered_items if i[1].get('type', '').lower() == product_type.lower()]
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
    if info.get('type', '').lower() == 'pulsa':
        return (header + f"\n• 💰 <b>Nominal Pulsa:</b> {info.get('data', 'N/A')}\n"
                         f"• ⏳ <b>Penambahan Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                         f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}")
    else:
        return (header + f"\n• 💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n"
                         f"• 📅 <b>Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                         f"• 📝 <b>Rincian:</b> {safe_html(info.get('details', 'N/A'))}")

def create_akrab_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {}); quota_info = AKRAB_QUOTA_DETAILS.get(package_key)
    description = create_header(info) + "\n" + ("<i>Paket keluarga resmi dari XL dengan kuota besar yang bisa dibagi-pakai.</i>\n\n"
                      "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL)\n" "🛡️ <b>Jaminan:</b> Garansi Penuh\n"
                      "🌐 <b>Kompatibilitas:</b> XL / AXIS / LIVEON\n" "📅 <b>Masa Aktif:</b> ±28 hari (sesuai ketentuan XL)\n\n")
    if quota_info:
        description += ("💾 <b>Estimasi Total Kuota (berdasarkan zona):</b>\n"
                          f"  - <b>Area 1:</b> {quota_info.get('1', 'N/A')}\n" f"  - <b>Area 2:</b> {quota_info.get('2', 'N/A')}\n"
                          f"  - <b>Area 3:</b> {quota_info.get('3', 'N/A')}\n" f"  - <b>Area 4:</b> {quota_info.get('4', 'N/A')}\n\n")
    else: description += f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n\n"
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
            if phone_number_str.startswith('08'): phone_number_str = '+62' + phone_number_str[1:]
            else: phone_number_str = '+' + phone_number_str
        phone_number = phonenumbers.parse(phone_number_str, None)
        if not phonenumbers.is_valid_number(phone_number): return f"❌ Nomor <code>{safe_html(phone_number_str)}</code> tidak valid."
        country_code = phone_number.country_code
        region_code = phonenumberutil.region_code_for_country_code(country_code)
        try:
            country = pycountry.countries.get(alpha_2=region_code)
            country_name, country_flag = (country.name, country.flag) if country and hasattr(country, 'flag') else ("Tidak Diketahui", "❓")
        except Exception: country_name, country_flag = region_code, "❓"
        number_type_map = {phonenumbers.PhoneNumberType.MOBILE: "Ponsel", phonenumbers.PhoneNumberType.FIXED_LINE: "Telepon Rumah", phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Ponsel / Telepon Rumah", phonenumbers.PhoneNumberType.TOLL_FREE: "Bebas Pulsa", phonenumbers.PhoneNumberType.VOIP: "VoIP"}
        number_type = number_type_map.get(phonenumbers.number_type(phone_number), "Lainnya")
        carrier_name = carrier.name_for_number(phone_number, "en") or "Tidak terdeteksi"
        return (f"<b>✅ Hasil Pengecekan untuk <code>{safe_html(phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))}</code></b>\n"
                f"-----------------------------------------\n"
                f"<b>Negara:</b> {country_flag} {country_name} (+{country_code})\n"
                f"<b>Valid:</b> ✅ Ya\n"
                f"<b>Tipe:</b> {number_type}\n"
                f"<b>Operator Asli:</b> {carrier_name}\n"
                f"<i>(ℹ️ Info operator mungkin tidak akurat jika nomor sudah porting)</i>")
    except phonenumberutil.NumberParseException: return f"❌ Format nomor <code>{safe_html(phone_number_str)}</code> salah. Harap gunakan format internasional (contoh: +628123...)."
    except Exception as e:
        logger.error(f"Error di get_provider_info_global: {e}")
        return "⚠️ Terjadi kesalahan saat memproses nomor."

def run_yt_dlp_sync(ydl_opts, url, download=False):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try: return ydl.extract_info(url, download=False)
        except Exception as e: logger.error(f"Error di dalam yt-dlp thread: {e}"); raise

# ==============================================================================
# 🤖 FUNGSI HANDLER BOT
# ==============================================================================
# (Semua handler dari sini ke bawah sudah lengkap dan telah diperbaiki)
async def send_admin_log(context: ContextTypes.DEFAULT_TYPE, error: Exception, update: Update, from_where: str, custom_message: str = ""):
    if not ADMIN_ID: return
    tb_list = traceback.format_exception(None, error, error.__traceback__)
    tb_string = "".join(tb_list)
    user = update.effective_user or "N/A"
    chat_id = update.effective_chat.id if update.effective_chat else "N/A"
    user_mention = user.mention_html() if hasattr(user, 'mention_html') else f"ID: {user.id if hasattr(user, 'id') else 'N/A'}"
    actionable_message = f"<b>🚨 Pesan Aksi Admin:</b> {custom_message}\n\n" if custom_message else ""
    admin_message = (f"‼️ <b>BOT ERROR LOG</b> ‼️\n\n{actionable_message}<b>Fungsi:</b> <code>{from_where}</code>\n"
                     f"<b>User:</b> {user_mention}\n<b>Chat ID:</b> <code>{chat_id}</code>\n\n"
                     f"<b>Tipe Error:</b> <code>{type(error).__name__}</code>\n<b>Pesan Error:</b>\n<pre>{safe_html(str(error))}</pre>\n\n"
                     f"<b>Traceback (Ringkas):</b>\n<pre>{safe_html(tb_string[-2000:])}</pre>")
    try: await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode=ParseMode.HTML)
    except Exception as e: logger.error(f"❌ KRITIS: Gagal mengirim log eror ke admin! Error: {e}")

async def track_message(context: ContextTypes.DEFAULT_TYPE, message):
    if not message: return
    async with message_tracking_lock:
        if 'messages_to_clear' not in context.user_data:
            context.user_data['messages_to_clear'] = []
        messages = context.user_data['messages_to_clear']
        messages.append(message.message_id)
        if len(messages) > MAX_MESSAGES_TO_TRACK:
            context.user_data['messages_to_clear'] = messages[-MAX_MESSAGES_TO_TRACK:]

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id; loading_msg = None
    try:
        if update.callback_query:
            await update.callback_query.answer("⏳ Memulai pembersihan riwayat...")
            try: await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
            except Exception: pass
        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 <b>Sedang menghapus pesan...</b> Mohon tunggu.", parse_mode=ParseMode.HTML)
        
        async with message_tracking_lock:
            messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))[-MAX_MESSAGES_TO_DELETE_PER_BATCH:]
            context.user_data['messages_to_clear'] = [m for m in context.user_data.get('messages_to_clear', []) if m not in messages_to_clear]

        delete_tasks = [context.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in messages_to_clear if msg_id != loading_msg.message_id]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        
        try: await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception: pass
        
        confirmation_text = f"✅ <b>Pembersihan Selesai!</b>\n\nBerhasil menghapus <b>{success_count}</b> pesan dari sesi ini."
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
        except Exception as e_inner: logger.error(f"❌ Gagal mengirim pesan error di clear_history: {e_inner}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        logger.info(f"Perintah /start diabaikan di chat {update.effective_chat.id} karena tidak ada effective_user.")
        return

    chat_id = update.effective_chat.id
    try:
        context.user_data.pop('state', None)
        if update.message and update.message.text == '/start': await track_message(context, update.message)
        user = update.effective_user
        
        greeting, icon = "Halo", "👋"
        try:
            now, hour = datetime.now(ZoneInfo("Asia/Jakarta")), datetime.now(ZoneInfo("Asia/Jakarta")).hour
            if 5 <= hour < 11: greeting, icon = "Selamat Pagi", "☀️"
            elif 11 <= hour < 15: greeting, icon = "Selamat Siang", "🌤️"
            elif 15 <= hour < 18: greeting, icon = "Selamat Sore", "🌥️"
            else: greeting, icon = "Selamat Malam", "🌙"
        except ZoneInfoNotFoundError:
             logger.warning("⚠️ Timezone 'Asia/Jakarta' tidak ditemukan. Pastikan 'tzdata' terinstal. Menggunakan default.")
        except Exception as tz_error: 
            logger.warning(f"⚠️ Gagal mendapatkan waktu Jakarta, menggunakan default. Error: {tz_error}.")
        
        username_info = f"<code>@{user.username}</code>" if user.username else "N/A"
        main_text = (f"{icon} <b>{greeting}, {user.first_name}!</b>\n\n"
                     "Selamat datang di <b>Pulsa Net Bot Resmi</b> 🚀\nPlatform terpercaya untuk semua kebutuhan digital Anda.\n\n"
                     "━━━━━━━━━━━━━━━━━━━━\n"
                     f"🔑 <b>Informasi Sesi Anda</b>\n  ├─ Username: {username_info}\n  ├─ User ID: <code>{user.id}</code>\n  └─ Chat ID: <code>{chat_id}</code>\n"
                     "━━━━━━━━━━━━━━━━━━━━\n\nPilih layanan yang Anda butuhkan dari menu di bawah ini:")
        keyboard = [[InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), InlineKeyboardButton("💰 Pulsa Reguler", callback_data="main_pulsa")],
                    [InlineKeyboardButton("🔍 Cek Info Nomor", callback_data="ask_for_number"), InlineKeyboardButton("🛠️ Tools & Hiburan", callback_data="main_tools")],
                    [InlineKeyboardButton("📊 Cek Kuota (XL/Axis)", url="https://sidompul.kmsp-store.com/"), InlineKeyboardButton("🆘 Bantuan", callback_data="main_bantuan")],
                    [InlineKeyboardButton("🗑️ Bersihkan Chat", callback_data="clear_history")],
                    [InlineKeyboardButton("🌐 Kunjungi Website Kami", url="https://pulsanet.kesug.com/beli.html")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                await update.callback_query.answer()
            except BadRequest as e:
                if "Message is not modified" in str(e): await update.callback_query.answer("Menu utama.")
                else: raise e
        else:
            sent_message = await context.bot.send_message(chat_id=chat_id, text=main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            await track_message(context, sent_message)
    except Exception as e:
        await send_admin_log(context, e, update, "start")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="❌ Maaf, terjadi kesalahan saat memuat menu utama.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except Exception as e_inner: logger.error(f"❌ Gagal mengirim pesan error di start: {e_inner}")
        
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
        
        back_cb = f"main_{product_type_key}" # Default back button

        if special_type_key:
            products = get_products(category=category_key, special_type=special_type_key)
            title_map = {"akrab": "Paket Akrab 🤝", "bebaspuas": "Paket Bebas Puas 🥳", "circle": "Paket Circle ⭕️", "paket": "Paket Lainnya 🚀"}
            title = f"<b>{base_title} - {title_map.get(special_type_key, special_type_key.capitalize())}</b>"
            back_cb = "list_paket_xl"
        else:
            products = get_products(category=category_key, product_type=product_type_key)
            product_name = 'Paket Data 📶' if product_type_key == 'paket' else 'Pulsa Reguler 💰'
            title = f"<b>{base_title} - {product_name}</b>"
        
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
        text, back_button_callback = "", "main_tools"
        
        if action == "ask_for_number":
            context.user_data['state'] = 'awaiting_number'
            text = ("<b>🔍 Cek Info Nomor Telepon (Global)</b>\n\n"
                    "Silakan kirimkan nomor HP yang ingin Anda periksa.\n"
                    "Format internasional (<code>+62...</code>) sangat disarankan untuk akurasi.")
            back_button_callback = "back_to_start"
        elif action == "ask_for_qr":
            context.user_data['state'] = 'awaiting_qr_text'
            text = "<b>🖼️ Generator QR Code</b>\n\nKirimkan teks, tautan, nomor HP, atau informasi apa pun yang ingin Anda jadikan QR Code."
        elif action == "ask_for_youtube":
            context.user_data['state'] = 'awaiting_youtube_link'
            text = "<b>▶️ YouTube Downloader (Mode Link)</b>\n\nKirimkan link video YouTube (youtube.com atau youtu.be) untuk mendapatkan link unduhannya."
        elif action == "ask_for_media_link":
            context.user_data['state'] = 'awaiting_media_link'
            text = ("<b>🔗 Media Downloader Universal</b>\n\n"
                    "Kirimkan link dari Instagram, Twitter/X, TikTok, Facebook, dll. Bot akan mencoba mengunduh dan mengirimkan media secara langsung.")
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
        try: amount = float(amount_str.replace(",", ""))
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
            except Exception: base_name, target_name = base_curr, target_curr
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
    status_msg, info_dict = None, None
    context.user_data['yt_formats'] = {}
    
    try:
        status_msg = await context.bot.send_message(update.effective_chat.id, "⏳ <b>Menyiapkan antrian...</b>", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        ydl_opts = get_ytdlp_options(url=url)
        
        try:
            async with DOWNLOADER_SEMAPHORE:
                await status_msg.edit_text(f"🔍 <b>Menganalisis link YouTube...</b>", parse_mode=ParseMode.HTML)
                task = asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
                info_dict = await asyncio.wait_for(task, timeout=DOWNLOAD_ANALYSIS_TIMEOUT)
        except asyncio.TimeoutError:
            logger.error(f"Timeout saat menganalisis YouTube URL: {url}")
            await status_msg.edit_text("❌ <b>Proses Gagal! Waktu Analisis Habis.</b>", reply_markup=keyboard_back_to_tools)
            return
        except yt_dlp.utils.DownloadError as e:
            error_str = str(e).lower()
            if 'rate-limited' in error_str:
                await send_admin_log(context, e, update, "YouTube Rate Limit")
                await status_msg.edit_text("❌ <b>Layanan YouTube Bermasalah.</b> Coba lagi nanti.", reply_markup=keyboard_error_back)
            elif any(err in error_str for err in ['sign in', 'login required', 'age restricted', 'private video']):
                await send_admin_log(context, e, update, "YouTube Auth Failed")
                await status_msg.edit_text("❌ <b>Gagal!</b> Video ini pribadi atau memerlukan login.", reply_markup=keyboard_error_back)
            else:
                await status_msg.edit_text("❌ Video tidak tersedia atau link tidak valid.", reply_markup=keyboard_error_back)
            return

        video_id = info_dict.get('id', '')
        title = info_dict.get('title', 'Video YouTube')
        formats = info_dict.get('formats', [])
        keyboard = []
        
        video_formats = sorted([f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and f.get('height') and f.get('height') <= 1080], key=lambda x: x.get('height', 0), reverse=True)
        
        for f in video_formats[:5]:
            format_hash = hashlib.sha1(f['format_id'].encode()).hexdigest()[:8]
            context.user_data['yt_formats'][format_hash] = f['format_id']
            file_size_str = format_bytes(f.get('filesize') or f.get('filesize_approx'))
            label = f"📹 {f['height']}p ({f['ext']}) - {file_size_str}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl_link|{video_id}|{format_hash}")])
            
        audio_formats = sorted([f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('ext') in ['m4a', 'opus', 'mp3']], key=lambda x: x.get('abr', 0) or 0, reverse=True)
        
        for f in audio_formats[:3]:
            format_hash = hashlib.sha1(f['format_id'].encode()).hexdigest()[:8]
            context.user_data['yt_formats'][format_hash] = f['format_id']
            file_size_str = format_bytes(f.get('filesize') or f.get('filesize_approx'))
            label = f"🎵 Audio [{f.get('ext', 'audio')}] - {file_size_str}"
            if f.get('abr'): label += f" (~{int(f['abr'])}k)"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"yt_dl_link|{video_id}|{format_hash}")])
            
        if not keyboard:
            await status_msg.edit_text("❌ Tidak ditemukan format yang bisa diunduh.", reply_markup=keyboard_error_back)
            return
            
        keyboard.append([InlineKeyboardButton("⬅️ Batal", callback_data="main_tools")])
        await status_msg.edit_message_text(f"<b>{safe_html(title)}</b>\n\nPilih kualitas:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    except Exception as e:
        await send_admin_log(context, e, update, "show_youtube_quality_options")
        if status_msg:
            await status_msg.edit_message_text("❌ Maaf, terjadi kesalahan teknis.", reply_markup=keyboard_error_back)
    finally:
        if info_dict is None:
             context.user_data.pop('yt_formats', None)

async def handle_youtube_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; status_msg = None
    try:
        await query.answer("⏳ Mengambil link unduhan...")
        status_msg = await query.edit_message_text("⏳ <b>Mengambil link unduhan...</b>", parse_mode=ParseMode.HTML)

        _, video_id, format_hash = query.data.split('|')
        
        format_id = context.user_data.get('yt_formats', {}).get(format_hash)
        if not format_id:
            await status_msg.edit_message_text("❌ Sesi unduhan tidak valid atau kedaluwarsa. Silakan coba lagi.", reply_markup=keyboard_error_back)
            return

        original_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = get_ytdlp_options(url=original_url)
        info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, original_url, download=False)
        selected_format = next((f for f in info_dict.get('formats', []) if f.get('format_id') == format_id), None)
        
        if not selected_format or not selected_format.get('url'):
            await status_msg.edit_message_text("❌ Gagal mendapatkan link unduhan.", reply_markup=keyboard_error_back)
            return

        download_url, title = selected_format.get('url'), info_dict.get('title', 'Video YouTube')
        file_size_str = format_bytes(selected_format.get('filesize') or selected_format.get('filesize_approx'))
        format_note, ext = selected_format.get('format_note', ''), selected_format.get('ext', 'file')
        is_video = selected_format.get('vcodec') != 'none'
        button_label = f"Unduh {'Video' if is_video else 'Audio'} ({format_note or ext} - {file_size_str})".strip()
        keyboard = [[InlineKeyboardButton(f"🔗 {button_label}", url=download_url)],
                    [InlineKeyboardButton("▶️ Unduh Video Lain", callback_data="ask_for_youtube")],
                    [InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]]
        result_text = (f"✅ <b>Link Unduhan Siap!</b>\n\n<b>Judul:</b> {safe_html(title)}\n\n"
                       f"Klik tombol di bawah untuk mengunduh.\n\n"
                       f"⚠️ <i>Link bersifat <b>sementara</b> dan bisa kedaluwarsa.</i>")
        await status_msg.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_youtube_download_choice")
        if status_msg: await status_msg.edit_message_text("❌ Maaf, terjadi kesalahan teknis.", reply_markup=keyboard_error_back)
    finally:
        context.user_data.pop('yt_formats', None)

async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    status_msg, info_dict, sent_successfully = None, {}, False
    media_links_info = []
    try:
        chat_id = update.effective_chat.id
        status_msg = await update.message.reply_text("⏳ <b>Menyiapkan antrian...</b>", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        
        ydl_opts = get_ytdlp_options(url=url)
        try:
            async with DOWNLOADER_SEMAPHORE:
                await status_msg.edit_text(f"⏳ <b>Menganalisis link media...</b>", parse_mode=ParseMode.HTML)
                task = asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
                info_dict = await asyncio.wait_for(task, timeout=DOWNLOAD_ANALYSIS_TIMEOUT)
            if not info_dict: raise yt_dlp.utils.DownloadError("Hasil analisis kosong.")
        except asyncio.TimeoutError:
            await status_msg.edit_text("❌ <b>Proses Gagal! Waktu Analisis Habis.</b>", reply_markup=keyboard_back_to_tools)
            return
        except Exception as e:
            logger.error(f"Gagal menganalisis link: {e}")
            await status_msg.edit_text("❌ Gagal menganalisis link. Pastikan link publik dan valid.", reply_markup=keyboard_error_back)
            return

        items_to_process = info_dict.get('entries', [info_dict])
        media_to_send = []
        title_full = info_dict.get('title') or info_dict.get('description', '')
        uploader = info_dict.get('uploader', 'Tidak diketahui')
        main_caption = f"<b>{safe_html(title_full)}</b>\n<i>Oleh: {safe_html(uploader)}</i>" if title_full else f"<i>Oleh: {safe_html(uploader)}</i>"
        main_caption = smart_truncate(main_caption)

        async with httpx.AsyncClient(headers={'User-Agent': CHROME_USER_AGENT, 'Referer': url}, follow_redirects=True, timeout=MEDIA_DOWNLOAD_TIMEOUT) as client:
            for i, item in enumerate(items_to_process[:10]):
                if not item: continue
                media_url, media_type = None, "Media"
                
                if item.get('url') and item.get('ext') in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    media_url, media_type = item.get('url'), "Gambar"
                else:
                    valid_formats = [f for f in item.get('formats', []) if f.get('url') and 'manifest' not in f.get('protocol', '')]
                    if valid_formats:
                        best_format = max(valid_formats, key=lambda f: (f.get('preference', -1), f.get('height', 0), f.get('tbr', 0)), default=None)
                        if best_format:
                            media_url, media_type = best_format.get('url'), "Video" if best_format.get('vcodec') != 'none' else "Audio"
                if not media_url: media_url, media_type = item.get('thumbnail'), "Gambar (Thumbnail)"
                if not media_url: continue

                try:
                    head_resp = await client.head(media_url)
                    head_resp.raise_for_status()
                    size = int(head_resp.headers.get('content-length', 0))
                    
                    limit = MAX_VIDEO_SIZE if media_type == "Video" else MAX_PHOTO_SIZE
                    if size > limit:
                        logger.warning(f"File terlalu besar ({format_bytes(size)}), fallback ke link.")
                        media_links_info.append({'label': f"Unduh {media_type} ({format_bytes(size)})", 'url': media_url})
                        continue
                except Exception as e:
                    logger.warning(f"Tidak bisa mendapatkan ukuran file, mencoba download: {e}")
                
                try:
                    if i == 0: await status_msg.edit_text(f"⏳ Mengunduh media {i+1}...")
                    caption = main_caption if i == 0 else None
                    if media_type.startswith("Gambar"):
                        media_to_send.append(InputMediaPhoto(media=media_url, caption=caption, parse_mode=ParseMode.HTML))
                    elif media_type == "Video":
                        media_to_send.append(InputMediaVideo(media=media_url, caption=caption, parse_mode=ParseMode.HTML))
                except Exception as e:
                    logger.warning(f"Gagal memproses URL {media_url} untuk dikirim: {e}")
                    media_links_info.append({'label': f"Unduh {media_type}", 'url': media_url})

        if media_to_send:
            try:
                await status_msg.edit_text(f"✅ Download berhasil ({len(media_to_send)} item). Meng-upload...")
                if len(media_to_send) > 1: await context.bot.send_media_group(chat_id, media=media_to_send)
                else:
                    item = media_to_send[0]
                    if isinstance(item, InputMediaPhoto): await context.bot.send_photo(chat_id, photo=item.media, caption=item.caption, parse_mode=item.parse_mode)
                    else: await context.bot.send_video(chat_id, video=item.media, caption=item.caption, parse_mode=item.parse_mode)
                await status_msg.delete()
                sent_successfully = True
                keyboard_next = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]])
                sent_msg_next = await context.bot.send_message(chat_id, text="Apa yang ingin Anda lakukan selanjutnya?", reply_markup=keyboard_next)
                await track_message(context, sent_msg_next)
            except Exception as e_send:
                logger.warning(f"⚠️ Gagal mengirim media: {e_send}. Fallback ke link.")
                await status_msg.edit_text("⚠️ Gagal mengirim media (mungkin terlalu besar). Beralih ke mode link...", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        await send_admin_log(context, e, update, "handle_media_download (General)")
        if status_msg and "Beralih ke mode" not in getattr(status_msg, 'text', ''):
             await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis.", reply_markup=keyboard_error_back)
    
    finally:
        if not sent_successfully:
            all_fallback_links = media_links_info + [{'label': f"Unduh Media {i+1}", 'url': m.media} for i, m in enumerate(media_to_send) if isinstance(m.media, str)]
            if all_fallback_links:
                try:
                    keyboard = [[InlineKeyboardButton(f"🔗 {link['label']}", url=link['url'])] for link in all_fallback_links[:10]]
                    keyboard.extend([[InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]])
                    title = info_dict.get('title', 'Media')
                    result_text = f"✅ <b>Link Unduhan Siap!</b>\n\n<b>Judul:</b> {safe_html(title)}\n\nKlik tombol di bawah untuk mengunduh."
                    if status_msg: await status_msg.edit_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                except Exception as e_fallback:
                    await send_admin_log(context, e_fallback, update, "handle_media_download (Fallback Fail)")
                    if status_msg: await status_msg.edit_text("❌ Maaf, terjadi kesalahan ganda.", reply_markup=keyboard_error_back)
            elif status_msg and "Gagal!" not in getattr(status_msg, 'text', ''):
                await status_msg.edit_text("❌ Tidak dapat menemukan link unduhan.", reply_markup=keyboard_error_back)

# ==============================================================================
# 🚀 FUNGSI UTAMA & SETUP COOKIES
# ==============================================================================
def setup_all_cookies():
    youtube_valid, generic_valid = False, False
    youtube_cookie_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    if youtube_cookie_b64:
        try:
            cookie_data = base64.b64decode(youtube_cookie_b64).decode('utf-8')
            with open(YOUTUBE_COOKIE_FILE, 'w', encoding='utf-8') as f: f.write(cookie_data)
            if YOUTUBE_COOKIE_FILE.exists() and YOUTUBE_COOKIE_FILE.stat().st_size > 0:
                youtube_valid = True
        except Exception as e: logger.error(f"❌ Gagal memproses YOUTUBE_COOKIES_BASE64: {e}")
    else: logger.warning("⚠️ YOUTUBE_COOKIES_BASE64 tidak diatur.")

    generic_cookie_b64 = os.environ.get("GENERIC_COOKIES_BASE64")
    if generic_cookie_b64:
        try:
            cookie_data = base64.b64decode(generic_cookie_b64).decode('utf-8')
            with open(GENERIC_COOKIE_FILE, 'w', encoding='utf-8') as f: f.write(cookie_data)
            if GENERIC_COOKIE_FILE.exists() and GENERIC_COOKIE_FILE.stat().st_size > 0:
                generic_valid = True
        except Exception as e: logger.error(f"❌ Gagal memproses GENERIC_COOKIES_BASE64: {e}")
    else: logger.warning("⚠️ GENERIC_COOKIES_BASE64 tidak diatur.")
    return youtube_valid, generic_valid

def get_ytdlp_options(url: str = None):
    opts = {'quiet': True, 'no_warnings': True, 'noplaylist': False, 'extract_flat': False,
            'http_headers': {'User-Agent': CHROME_USER_AGENT}, 'nocheckcertificate': True}
    cookie_file_to_use = None
    if url:
        if 'youtube.com' in url or 'youtu.be' in url:
            if YOUTUBE_COOKIE_FILE.exists(): cookie_file_to_use = str(YOUTUBE_COOKIE_FILE)
        elif GENERIC_COOKIE_FILE.exists(): cookie_file_to_use = str(GENERIC_COOKIE_FILE)
    if cookie_file_to_use: opts['cookiefile'] = cookie_file_to_use
    return opts

def main() -> None:
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.critical("❌ FATAL: Token bot tidak ditemukan! Atur TELEGRAM_BOT_TOKEN.")
        sys.exit(1)
    if not ADMIN_ID:
        logger.warning("⚠️ TELEGRAM_ADMIN_ID tidak diatur. Log eror tidak akan dikirim.")

    youtube_valid, generic_valid = setup_all_cookies()

    from telegram.request import HTTPXRequest
    timeout_config = HTTPXRequest(connect_timeout=15.0, read_timeout=30.0, write_timeout=30.0)
    application = Application.builder().token(TOKEN).request(timeout_config).build()

    # Registrasi Handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
    application.add_handler(CallbackQueryHandler(clear_history, pattern='^clear_history$'))
    application.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan$'))
    application.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)$'))
    application.add_handler(CallbackQueryHandler(show_tools_menu, pattern='^main_tools$'))
    application.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl$'))
    application.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+$'))
    application.add_handler(CallbackQueryHandler(show_package_details, pattern=r'^pkg_\d+_[a-z0-9_]+$'))
    application.add_handler(CallbackQueryHandler(prompt_for_action, pattern=r'^ask_for_(number|qr|youtube|currency|media_link)$'))
    application.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    application.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    application.add_handler(CallbackQueryHandler(handle_youtube_download_choice, pattern=r'^yt_dl_link\|.+'))
    application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("============================================")
    print("🚀 Bot Pulsa Net (v18.0 - Production Hardening)")
    print("============================================")
    if youtube_valid: print("✅ YouTube Downloader: AKTIF (Cookies Valid)")
    else: print("❌ YouTube Downloader: MODE TERBATAS (Masalah Cookies YouTube)")
    if generic_valid: print("✅ Generic Media Downloader: AKTIF (Cookies Valid)")
    else: print("⚠️ Generic Media Downloader: MODE TERBATAS (Masalah Cookies Generik)")
    if not youtube_valid or not generic_valid:
        logger.warning("--- PERINGATAN: Fitur unduh mungkin tidak berfungsi optimal tanpa cookies! ---")
    
    print("\n💡 Bot sedang berjalan. Tekan Ctrl+C untuk berhenti.")
    print("-" * 60)

    application.run_polling()

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Proses dihentikan oleh pengguna.")
    except Exception as e:
        logger.critical(f"❌ FATAL ERROR di main loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        for cookie_file in [YOUTUBE_COOKIE_FILE, GENERIC_COOKIE_FILE]:
            if os.path.exists(cookie_file):
                try:
                    os.remove(cookie_file)
                except OSError as e:
                    logger.error(f"Gagal menghapus file cookie sementara {cookie_file}: {e}")
        print("👋 Goodbye!")
