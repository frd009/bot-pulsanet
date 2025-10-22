# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet.py
# Developer: frd009
# Versi: 16.22 (Critical Function Fix)
#
# CHANGELOG v16.22:
# - FIX: Menambahkan definisi untuk 12+ fungsi yang hilang
#   (setup_all_cookies, get_ytdlp_options, show_bantuan,
#   show_operator_menu, show_tools_menu, show_xl_paket_submenu,
#   show_product_list, show_package_details, prompt_for_action,
#   show_youtube_quality_options, handle_youtube_download_choice,
#   handle_currency_conversion) untuk mengatasi NameError.
# - FIX: Mengatasi potensi race condition di 'track_message' dan
#   'clear_history' dengan menambahkan asyncio.Lock.
#
# CHANGELOG v16.21:
# - FIX: Mengatasi NameError: name 'handle_media_download' is not defined
#   dengan mengubah urutan definisi fungsi agar 'handle_media_download'
#   didefinisikan sebelum dipanggil oleh 'handle_text_message'.
#
# CHANGELOG v16.20:
# - FIX: Mengatasi NameError: name 'SIGTERM' is not defined dengan memanggil
#   signal.SIGTERM secara benar di dalam fungsi main().
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
import filetype

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
MAX_UPLOAD_FILE_SIZE_MB = 300
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

# --- File Cookie ---
YOUTUBE_COOKIE_FILE = 'youtube_cookies.txt'
GENERIC_COOKIE_FILE = 'generic_cookies.txt'

# --- Sinkronisasi ---
user_data_lock = asyncio.Lock()

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

def setup_all_cookies():
    """Mendekode dan menulis file cookie dari environment variables."""
    youtube_cookie_b64 = os.environ.get('YOUTUBE_COOKIES_BASE64')
    generic_cookie_b64 = os.environ.get('GENERIC_COOKIES_BASE64')
    
    youtube_valid = False
    generic_valid = False

    try:
        if youtube_cookie_b64:
            cookie_data = base64.b64decode(youtube_cookie_b64).decode('utf-8')
            with open(YOUTUBE_COOKIE_FILE, 'w') as f:
                f.write(cookie_data)
            youtube_valid = True
            logger.info("File cookie YouTube berhasil dibuat.")
        else:
            logger.warning("YOUTUBE_COOKIES_BASE64 tidak diatur. Fitur unduh YouTube mungkin terbatas.")
    except Exception as e:
        logger.error(f"Gagal memproses YOUTUBE_COOKIES_BASE64: {e}")

    try:
        if generic_cookie_b64:
            cookie_data = base64.b64decode(generic_cookie_b64).decode('utf-8')
            with open(GENERIC_COOKIE_FILE, 'w') as f:
                f.write(cookie_data)
            generic_valid = True
            logger.info("File cookie generik berhasil dibuat.")
        else:
            logger.warning("GENERIC_COOKIES_BASE64 tidak diatur. Fitur unduh (IG, dll.) mungkin terbatas.")
    except Exception as e:
        logger.error(f"Gagal memproses GENERIC_COOKIES_BASE64: {e}")

    return youtube_valid, generic_valid

def get_ytdlp_options(url: str):
    """Memilih file cookie yang sesuai berdasarkan URL."""
    cookie_file = None
    if 'youtube.com' in url or 'youtu.be' in url:
        if os.path.exists(YOUTUBE_COOKIE_FILE):
            cookie_file = YOUTUBE_COOKIE_FILE
    else:
        if os.path.exists(GENERIC_COOKIE_FILE):
            cookie_file = GENERIC_COOKIE_FILE

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': CHROME_USER_AGENT,
        'http_headers': {'Referer': 'https://www.google.com/'},
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        }],
    }

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file
        logger.info(f"Menggunakan cookie file: {cookie_file} for {url}")
    else:
        logger.warning(f"Tidak ada cookie file yang cocok/tersedia for {url}")

    return ydl_opts

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

def detect_media_type(file_path: str) -> str:
    """
    Deteksi apakah file adalah foto atau video menggunakan MIME type.
    Returns: 'photo', 'video', 'document', atau 'unknown'
    """
    try:
        kind = filetype.guess(file_path)
        if kind is not None:
            if kind.mime.startswith('image/'):
                return 'photo'
            elif kind.mime.startswith('video/'):
                return 'video'
        
        ext = Path(file_path).suffix.lower()
        image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
        video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']
        
        if ext in image_exts:
            return 'photo'
        elif ext in video_exts:
            return 'video'
        else:
            return 'document'
            
    except Exception as e:
        logger.error(f"Error detecting media type for {file_path}: {e}")
        return 'unknown'

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
        async with user_data_lock:
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
        
        messages_to_clear = []
        async with user_data_lock:
            messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))
            messages_to_clear = messages_to_clear[-MAX_MESSAGES_TO_DELETE_PER_BATCH:]
            context.user_data['messages_to_clear'] = [] # Hapus di dalam lock
        
        delete_tasks = [context.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in messages_to_clear if msg_id != loading_msg.message_id]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception: pass
        
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
        async with user_data_lock:
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
            sent_message = None
            for attempt in range(3):
                try:
                    sent_message = await context.bot.send_message(
                        chat_id=chat_id,
                        text=main_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                    break
                except TimedOut:
                    logger.warning(f"Attempt {attempt + 1} to send start message timed out. Retrying in 2 seconds...")
                    if attempt < 2:
                        await asyncio.sleep(2)
                except Exception:
                    raise 

            if not sent_message:
                raise TimedOut("Gagal mengirim pesan setelah 3 kali percobaan.")

            await track_message(context, sent_message)
    except Exception as e:
        await send_admin_log(context, e, update, "start")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="Maaf, terjadi kesalahan saat memuat menu utama.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except:
            pass
            
async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan pesan bantuan."""
    query = update.callback_query
    try:
        await query.answer()
        text = PAKET_DESCRIPTIONS.get("bantuan", "Silakan hubungi admin @hexynos untuk bantuan.")
        keyboard = [[InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await send_admin_log(context, e, update, "show_bantuan")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu pilihan operator untuk paket data atau pulsa."""
    query = update.callback_query
    try:
        await query.answer()
        product_type = query.data.split('_')[1] # 'paket' or 'pulsa'
        
        text = f"Silakan pilih operator untuk <b>{product_type.capitalize()}</b>:"
        keyboard = [
            [InlineKeyboardButton("🔵 XL", callback_data=f"list_{product_type}_xl"), InlineKeyboardButton("🔴 Axis", callback_data=f"list_{product_type}_axis")],
            [InlineKeyboardButton("🟡 Indosat", callback_data=f"list_{product_type}_indosat"), InlineKeyboardButton("❤️ Telkomsel", callback_data=f"list_{product_type}_telkomsel")],
            [InlineKeyboardButton("⚫ Tri", callback_data=f"list_{product_type}_tri"), InlineKeyboardButton("🟣 By.U", callback_data=f"list_{product_type}_by.u")],
            [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "show_operator_menu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan submenu khusus untuk paket XL."""
    query = update.callback_query
    try:
        await query.answer()
        text = "Silakan pilih jenis <b>Paket XL</b>:"
        keyboard = [
            [InlineKeyboardButton("🔥 Akrab (Keluarga)", callback_data="list_paket_xl_akrab")],
            [InlineKeyboardButton("✨ Bebas Puas", callback_data="list_paket_xl_bebaspuas")],
            [InlineKeyboardButton("🌀 Circle", callback_data="list_paket_xl_circle")],
            [InlineKeyboardButton("🔄 Paket Lainnya (Flex)", callback_data="list_paket_xl_paket")],
            [InlineKeyboardButton("⬅️ Kembali ke Pilihan Operator", callback_data="main_paket")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "show_xl_paket_submenu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan daftar produk berdasarkan operator dan tipe."""
    query = update.callback_query
    try:
        await query.answer()
        
        parts = query.data.split('_')
        product_type = parts[1] # 'paket' or 'pulsa'
        category = parts[2].lower()
        special_type = parts[3].lower() if len(parts) > 3 else None

        if category == 'xl' and product_type == 'paket' and not special_type:
             await show_xl_paket_submenu(update, context)
             return

        products = get_products(category=category, product_type=product_type, special_type=special_type)
        
        if not products:
            await query.edit_message_text("Maaf, tidak ada produk yang tersedia untuk kategori ini.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return

        keyboard = []
        for key, name in products.items():
            price = f"Rp{PRICES.get(key, 0):,}".replace(",", ".")
            keyboard.append([InlineKeyboardButton(f"{name} ({price})", callback_data=key)])
        
        # Tentukan tombol kembali
        if special_type:
            back_callback = "list_paket_xl" # Kembali ke submenu XL
        else:
            back_callback = f"main_{product_type}" # Kembali ke menu operator
            
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_callback)])

        text = f"Daftar <b>{product_type.capitalize()} {category.upper()}</b>:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    except Exception as e:
        await send_admin_log(context, e, update, "show_product_list")
        await query.edit_message_text("Maaf, terjadi kesalahan saat memuat produk.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan detail paket yang dipilih."""
    query = update.callback_query
    try:
        await query.answer()
        package_key = query.data
        
        description = PAKET_DESCRIPTIONS.get(package_key, "Deskripsi tidak ditemukan.")
        info = ALL_PACKAGES_DATA.get(package_key, {})
        
        product_type = info.get('type', 'paket').lower()
        category = info.get('category', 'xl').lower()
        
        # Tentukan tombol kembali
        if product_type == 'akrab' or product_type == 'bebaspuas' or product_type == 'circle' or (category == 'xl' and product_type == 'paket'):
            back_callback = "list_paket_xl" # Kembali ke submenu XL
        else:
            back_callback = f"list_{product_type}_{category}" # Kembali ke list produk
        
        keyboard = [
            [InlineKeyboardButton("🛒 Beli Sekarang (via Website)", url="https://pulsanet.kesug.com/beli.html")],
            [InlineKeyboardButton("⬅️ Kembali ke Daftar Produk", callback_data=back_callback)]
        ]
        
        await query.edit_message_text(description, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await send_admin_log(context, e, update, "show_package_details")
        await query.edit_message_text("Maaf, terjadi kesalahan saat menampilkan detail.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan menu tools dan hiburan."""
    query = update.callback_query
    try:
        await query.answer()
        text = "<b>🛠️ Menu Tools & Hiburan</b>\n\nPilih alat atau hiburan yang ingin Anda gunakan:"
        keyboard = [
            [InlineKeyboardButton("🎬 Download Video YouTube", callback_data="ask_for_youtube")],
            [InlineKeyboardButton("🖼️ Buat QR Code", callback_data="ask_for_qr")],
            [InlineKeyboardButton("📥 Download Media (IG, X, TikTok)", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("🔐 Buat Password Aman", callback_data="gen_password")],
            [InlineKeyboardButton("🎮 Game (Batu-Gunting-Kertas)", callback_data="main_game")],
            [InlineKeyboardButton("💹 Cek Kurs Mata Uang (Beta)", callback_data="ask_for_currency")],
            [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "show_tools_menu")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def prompt_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Meminta input dari pengguna untuk fitur tertentu."""
    query = update.callback_query
    try:
        await query.answer()
        action = query.data.split('_')[2] # 'number', 'qr', 'youtube', 'currency', 'media_link'
        
        STATE_MAP = {
            'number': {
                'state': 'awaiting_number',
                'text': "Silakan kirimkan <b>satu atau beberapa nomor telepon</b> (maks 3) yang ingin Anda cek. \n\nFormat: <code>+628123456789</code> atau <code>08123456789</code>.",
                'back': 'back_to_start'
            },
            'qr': {
                'state': 'awaiting_qr_text',
                'text': "Silakan kirimkan <b>teks, URL, atau nomor HP</b> yang ingin Anda jadikan QR Code.",
                'back': 'main_tools'
            },
            'youtube': {
                'state': 'awaiting_youtube_link',
                'text': "Silakan kirimkan <b>link video YouTube</b> yang ingin Anda unduh.",
                'back': 'main_tools'
            },
            'currency': {
                'state': 'awaiting_currency',
                'text': "Silakan kirimkan format konversi, contoh:\n<code>100 USD to IDR</code>\n<code>50000 JPY to EUR</code>\n\n<i>(Fitur ini masih dalam tahap beta)</i>",
                'back': 'main_tools'
            },
            'media_link': {
                'state': 'awaiting_media_link',
                'text': "Silakan kirimkan <b>link media</b> dari Instagram, X (Twitter), TikTok, dll.",
                'back': 'main_tools'
            }
        }
        
        prompt = STATE_MAP.get(action)
        
        if prompt:
            async with user_data_lock:
                context.user_data['state'] = prompt['state']
            
            keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data=prompt['back'])]]
            await query.edit_message_text(prompt['text'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text("Aksi tidak diketahui.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        await send_admin_log(context, e, update, "prompt_for_action")
        await query.edit_message_text("Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def show_youtube_quality_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Mengambil info video YouTube dan menampilkan pilihan kualitas."""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("🔎 <b>Menganalisis link YouTube...</b>", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        
        ydl_opts = get_ytdlp_options(url)
        ydl_opts['listformats'] = True
        
        info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
        
        formats = info_dict.get('formats', [])
        video_formats = []
        audio_formats = []

        for f in formats:
            filesize = f.get('filesize') or f.get('filesize_approx')
            if filesize and filesize > MAX_UPLOAD_FILE_SIZE_BYTES:
                continue # Lewati file yang terlalu besar

            ext = f.get('ext')
            note = f.get('format_note', 'N/A')
            format_id = f.get('format_id')
            
            label = f"{note} ({ext}, {format_bytes(filesize)})"
            callback_data = f"yt_dl|{format_id}|{ext}"

            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                # Video dengan audio
                if 'p' in note and ext == 'mp4': # Hanya ambil MP4
                    video_formats.append(InlineKeyboardButton(f"🎬 {label}", callback_data=callback_data))
            elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                # Audio saja
                if ext in ['m4a', 'mp3', 'opus']:
                    audio_formats.append(InlineKeyboardButton(f"🎵 {label}", callback_data=callback_data))

        if not video_formats and not audio_formats:
            await status_msg.edit_text("Maaf, tidak ditemukan format video/audio yang didukung atau ukurannya terlalu besar.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return

        async with user_data_lock:
            context.user_data['youtube_url'] = url
            context.user_data['state'] = None # Hapus state awaiting

        keyboard = []
        if video_formats:
            keyboard.extend([[btn] for btn in video_formats[:5]]) # Ambil 5 video terbaik
        if audio_formats:
            keyboard.extend([[btn] for btn in audio_formats[:3]]) # Ambil 3 audio terbaik
        
        keyboard.append([InlineKeyboardButton("⬅️ Batal (Kembali ke Tools)", callback_data="main_tools")])

        title = info_dict.get('title', 'Video')
        await status_msg.edit_text(
            f"<b>{safe_html(title)}</b>\n\nPilih format yang ingin diunduh:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
        logger.error(f"Error yt-dlp di show_youtube_quality_options: {e}")
        await status_msg.edit_text("Maaf, link YouTube tidak valid atau video tidak dapat diakses.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "show_youtube_quality_options")
        if status_msg:
            await status_msg.edit_text("Maaf, terjadi kesalahan teknis.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def handle_currency_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengkonversi mata uang menggunakan API eksternal (simulasi)."""
    status_msg = None
    try:
        message_text = update.message.text
        # Pola regex sederhana: 100 USD to IDR
        match = re.match(r'^\s*([\d\.]+)\s*([A-Z]{3})\s*to\s*([A-Z]{3})\s*$', message_text, re.IGNORECASE)
        
        if not match:
            sent_msg = await update.message.reply_text("Format salah. Gunakan: <code>100 USD to IDR</code>", parse_mode=ParseMode.HTML)
            await track_message(context, sent_msg)
            return

        amount = float(match.group(1))
        from_currency = match.group(2).upper()
        to_currency = match.group(3).upper()

        status_msg = await update.message.reply_text(f"Menghitung konversi {amount} {from_currency} ke {to_currency}...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)

        # Gunakan API gratis (misal: exchangerate-api)
        api_url = f"https://open.er-api.com/v6/latest/{from_currency}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()

        if data.get('result') == 'error':
            raise ValueError(f"API error: {data.get('error-type')}")

        rates = data.get('rates')
        if not rates or to_currency not in rates:
            raise ValueError(f"Mata uang {to_currency} tidak ditemukan di API.")

        rate = rates[to_currency]
        converted_amount = amount * rate
        
        result_text = (
            f"<b>Hasil Konversi Mata Uang</b> 💹\n\n"
            f"<b>Dari:</b> <code>{amount:,.2f} {from_currency}</code>\n"
            f"<b>Ke:</b> <code>{converted_amount:,.2f} {to_currency}</code>\n\n"
            f"<b>Kurs 1 {from_currency} =</b> <code>{rate:,.4f} {to_currency}</code>\n"
            f"<i>Data kurs diambil pada: {datetime.fromtimestamp(data.get('time_last_update_unix')).strftime('%Y-%m-%d %H:%M:%S')} UTC</i>"
        )
        await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML)

    except httpx.HTTPStatusError as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (API HTTP Error)")
        await status_msg.edit_text(f"Maaf, layanan kurs sedang bermasalah (HTTP {e.response.status_code}). Coba lagi nanti.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except httpx.RequestError as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (API Request Error)")
        await status_msg.edit_text("Maaf, gagal terhubung ke server kurs. Coba lagi nanti.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (General)")
        if status_msg:
            await status_msg.edit_text("Maaf, terjadi kesalahan teknis saat konversi.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """
    FIXED VERSION: Download media (foto & video) dari Instagram, Twitter, TikTok, dll.
    """
    status_msg = None
    downloaded_files = []
    
    try:
        status_msg = await update.message.reply_text(
            "📥 <b>Mengunduh media...</b> Ini mungkin memakan waktu.",
            parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)

        file_path_template = f"media_{update.effective_message.id}_%(id)s.%(ext)s"
        
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
            
            if 'no video formats found' in error_str or 'no formats found' in error_str:
                logger.warning(f"⚠️ No video format found, retrying as photo-only post...")
                
                ydl_opts_retry = get_ytdlp_options(url=url)
                ydl_opts_retry['outtmpl'] = file_path_template
                ydl_opts_retry['format'] = 'best'
                ydl_opts_retry['ignoreerrors'] = True
                
                try:
                    info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts_retry, url, download=True)
                    if not info_dict:
                        raise e
                    logger.info("✅ Berhasil retry sebagai foto!")
                except Exception as retry_error:
                    reply_text = "❌ <b>Gagal!</b> Postingan ini mungkin hanya berisi foto yang tidak dapat diekstrak, atau link sudah dihapus."
                    await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                    return
            
            elif ('unsupported url' in error_str and 'login' in url) or \
                 ('this content is only available for registered users' in error_str) or \
                 ('private' in error_str or 'login required' in error_str):
                reply_text = "❌ <b>Gagal!</b> Konten ini bersifat pribadi atau memerlukan login.\n\n" \
                             "<i>Pastikan Admin telah mengonfigurasi cookies untuk situs ini.</i>"
                admin_alert = f"Gagal mengunduh {url} karena masalah otentikasi. " \
                              f"Pastikan GENERIC_COOKIES_BASE64 sudah diatur dan valid. Error: {e}"
                await send_admin_log(context, e, update, "handle_media_download (Auth Error)", custom_message=admin_alert)
                admin_log_sent = True
            
            elif 'is not a valid url' in error_str:
                reply_text = "❌ <b>Gagal!</b> Link ini tidak valid atau platform tidak didukung."
            elif 'unavailable' in error_str:
                reply_text = "❌ <b>Gagal!</b> Konten ini tidak tersedia atau telah dihapus."
            
            logger.warning(f"yt-dlp error for URL {url}: {e}")

            if not admin_log_sent:
                await send_admin_log(context, e, update, "handle_media_download (DownloadError)", custom_message=f"URL: {url}")

            if status_msg and 'info_dict' not in locals():
                await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                return

        files_to_process = []
        
        if info_dict.get('requested_downloads'):
            files_to_process = info_dict['requested_downloads']
        elif info_dict.get('entries'):
            await status_msg.edit_text(
                f"📥 <b>Album/Carousel terdeteksi.</b> Mengunduh {len(info_dict['entries'])} file...",
                parse_mode=ParseMode.HTML
            )
            for entry in info_dict.get('entries', []):
                if not entry:
                    continue
                if entry.get('filepath') or entry.get('_filename'):
                    files_to_process.append(entry)
                elif entry.get('thumbnail') and not entry.get('url'):
                    logger.warning(f"Entry hanya memiliki thumbnail: {entry.get('id')}")
                    
        elif info_dict.get('filepath') or info_dict.get('_filename'):
            if info_dict.get('_filename') and not info_dict.get('filepath'):
                info_dict['filepath'] = info_dict.get('_filename')
            files_to_process = [info_dict]

        if not files_to_process:
            logger.error(f"❌ files_to_process kosong untuk {url}")
            logger.error(f"info_dict keys: {list(info_dict.keys())}")
            raise ValueError("Tidak ada file yang berhasil diunduh dari metadata yt-dlp.")

        await status_msg.edit_text(
            f"📤 <b>Mengirim {len(files_to_process)} file...</b>",
            parse_mode=ParseMode.HTML
        )
        
        for i, file_info in enumerate(files_to_process):
            file_path = file_info.get('filepath') or file_info.get('_filename')
            
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"⚠️ File path not found for entry {i}, skipping. Info: {file_info.get('id', 'N/A')}")
                continue

            downloaded_files.append(file_path)
            
            title = info_dict.get('title', 'Media')
            uploader = info_dict.get('uploader', 'Tidak diketahui')
            entry_title = file_info.get('title', title)

            if entry_title == 'NA' or entry_title == title or not entry_title:
                caption = f"<b>{safe_html(title)}</b> ({i+1}/{len(files_to_process)})\n"
            else:
                caption = f"<b>{safe_html(entry_title)}</b>\n<i>(dari Album: {safe_html(title)})</i>\n"
            
            caption += f"<i>oleh {safe_html(uploader)}</i>\n\nDiunduh dengan @{context.bot.username}"
            
            media_type = detect_media_type(file_path)
            
            with open(file_path, 'rb') as f:
                if media_type == 'photo':
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
                    sent_file = await context.bot.send_photo(
                        update.effective_chat.id,
                        photo=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                elif media_type == 'video':
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
                    sent_file = await context.bot.send_video(
                        update.effective_chat.id,
                        video=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
                    sent_file = await context.bot.send_document(
                        update.effective_chat.id,
                        document=f,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
            
            await track_message(context, sent_file)
            await asyncio.sleep(1)

        await status_msg.delete()

        keyboard_next = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ])
        next_msg = await context.bot.send_message(
            update.effective_chat.id,
            "✅ Semua media berhasil diunduh.",
            reply_markup=keyboard_next
        )
        await track_message(context, next_msg)
            
    except Exception as e:
        await send_admin_log(context, e, update, "handle_media_download (General)")
        if status_msg:
            try:
                await status_msg.edit_text(
                    "Maaf, terjadi kesalahan teknis yang tidak terduga. Admin telah diberitahu.",
                    reply_markup=keyboard_error_back,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
    finally:
        for f in downloaded_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    logger.error(f"Gagal menghapus file media {f}: {e}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await track_message(context, update.message)
        
        state = None
        async with user_data_lock:
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
            
            async with user_data_lock:
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
            
            async with user_data_lock:
                context.user_data.pop('state', None)
            return
        
        elif state == 'awaiting_media_link':
            if re.search(url_pattern, message_text):
                await handle_media_download(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text("Link tidak valid. Pastikan Anda mengirimkan tautan yang benar.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
                await track_message(context, sent_msg)
            
            async with user_data_lock:
                context.user_data.pop('state', None)
            return

        elif state == 'awaiting_currency':
            await handle_currency_conversion(update, context)
            
            async with user_data_lock:
                context.user_data.pop('state', None)
            
            keyboard = [[InlineKeyboardButton("💹 Hitung Kurs Lain", callback_data="ask_for_currency")],  
                        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
            sent_msg2 = await update.message.reply_text("Apa yang ingin Anda lakukan selanjutnya?", reply_markup=InlineKeyboardMarkup(keyboard))
            await track_message(context, sent_msg2)
            return

        # Deteksi nomor telepon otomatis jika tidak ada state
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
            # Jika tidak ada state dan bukan nomor, jangan balas apa-apa
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

async def handle_youtube_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    status_msg = None
    downloaded_file_path = None
    
    try:
        await query.answer("Memulai proses unduh...")
        
        status_msg = await query.message.reply_text(
            "📥 <b>Sedang mengunduh...</b> Ini mungkin memakan waktu. Harap tunggu.",
            parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)

        _, format_id, ext = query.data.split('|')
        
        url = None
        async with user_data_lock:
            url = context.user_data.get('youtube_url')
        
        if not url:
            await status_msg.edit_text(
                "❌ <b>Sesi kadaluwarsa.</b> URL YouTube tidak ditemukan. Silakan ulangi dari awal.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )
            return

        ydl_opts = get_ytdlp_options(url)
        ydl_opts['format'] = format_id
        ydl_opts['outtmpl'] = f"youtube_dl_{update.effective_chat.id}_{datetime.now().timestamp()}.%(ext)s"
        ydl_opts['max_filesize'] = MAX_UPLOAD_FILE_SIZE_BYTES
        
        try:
            info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=True)
            downloaded_file_path = info_dict.get('filepath') or info_dict.get('_filename')
            
            if not downloaded_file_path or not os.path.exists(downloaded_file_path):
                raise ValueError("File path tidak ditemukan setelah proses unduh.")

        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as e:
            error_str = str(e).lower()
            if 'file is larger than max-filesize' in error_str:
                reply_text = f"❌ <b>Gagal!</b> File video/audio terlalu besar (melebihi {MAX_UPLOAD_FILE_SIZE_MB}MB). Pilih kualitas yang lebih rendah."
            else:
                reply_text = "❌ <b>Gagal!</b> Terjadi kesalahan saat mengunduh format ini. Video mungkin dilindungi atau link tidak valid."
                await send_admin_log(context, e, update, "handle_youtube_download_choice (DownloadError)")
            
            await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            return

        await status_msg.edit_text("📤 <b>Mengirim file...</b>", parse_mode=ParseMode.HTML)
        
        title = info_dict.get('title', 'Video YouTube')
        uploader = info_dict.get('uploader', 'Tidak diketahui')
        caption = f"<b>{safe_html(title)}</b>\n<i>oleh {safe_html(uploader)}</i>\n\nDiunduh dengan @{context.bot.username}"
        
        sent_file = None
        with open(downloaded_file_path, 'rb') as f:
            if ext == 'mp3' or ext == 'm4a' or ext == 'opus' or info_dict.get('vcodec') == 'none':
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_AUDIO)
                sent_file = await context.bot.send_audio(
                    update.effective_chat.id,
                    audio=f,
                    caption=caption,
                    title=title,
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_VIDEO)
                sent_file = await context.bot.send_video(
                    update.effective_chat.id,
                    video=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        
        await track_message(context, sent_file)
        await status_msg.delete()

        keyboard_next = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Unduh YouTube Lain", callback_data="ask_for_youtube")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ])
        next_msg = await context.bot.send_message(
            update.effective_chat.id,
            "✅ File berhasil dikirim.",
            reply_markup=keyboard_next
        )
        await track_message(context, next_msg)
        
    except Exception as e:
        await send_admin_log(context, e, update, "handle_youtube_download_choice (General)")
        if status_msg:
            try:
                await status_msg.edit_text(
                    "Maaf, terjadi kesalahan teknis. Admin telah diberitahu.",
                    reply_markup=keyboard_error_back,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            try:
                os.remove(downloaded_file_path)
            except Exception as e:
                logger.error(f"Gagal menghapus file YouTube {downloaded_file_path}: {e}")

# ==============================================================================
# 🚀 FUNGSI MAIN
# ==============================================================================

def main():
    global bot_application

    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak ditemukan! Atur TELEGRAM_BOT_TOKEN di environment variable.")
    
    if not ADMIN_ID:
        logger.warning("TELEGRAM_ADMIN_ID tidak diatur. Laporan eror tidak akan dikirimkan ke admin.")

    youtube_valid, generic_valid = setup_all_cookies()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("🔧 Registering shutdown handlers...")

    timeout_config = HTTPXRequest(connect_timeout=10.0, read_timeout=20.0, write_timeout=20.0)
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
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    bot_application.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    bot_application.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    bot_application.add_handler(CallbackQueryHandler(handle_youtube_download_choice, pattern=r'^yt_dl\|.+'))
    bot_application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))

    print(f"🤖 Bot Pulsa Net (v16.22 - FIXED) sedang berjalan...")
    
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

    bot_application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
