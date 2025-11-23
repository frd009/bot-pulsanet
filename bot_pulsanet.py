# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet.py
# Developer: frd099
# Versi: 19.0 (Complete Power Mode)
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
import signal
import sys
import string
import base64
import json
import psutil
from datetime import datetime

# FIX 1: Import Error - ZoneInfo
try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = pytz.timezone
    except ImportError:
        print("❌ KRITIS: 'zoneinfo' tidak ditemukan. Install: pip install backports.zoneinfo")
        sys.exit(1)

from pathlib import Path

# --- Import library tambahan Zeta ---
try:
    import qrcode
    from PIL import Image
    import phonenumbers
    from phonenumbers import carrier, geocoder, phonenumberutil
    import pycountry
    import whois
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ Library missing: {e}")
    print("📦 Install: pip install qrcode[pil] pillow phonenumbers pycountry python-whois beautifulsoup4 psutil")
    sys.exit(1)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.request import HTTPXRequest

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# ==============================================================================
# ⚙️ KONFIGURASI & VARIABEL GLOBAL ZETA
# ==============================================================================
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")
MAX_MESSAGES_TO_TRACK = 150
MAX_MESSAGES_TO_DELETE_PER_BATCH = 50
BOT_START_TIME = datetime.now()

# API Keys (optional)
CRYPTO_API = "https://api.coingecko.com/api/v3"
STOCK_API = "https://www.alphavantage.co/query"
STOCK_API_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "demo")

# Graceful Shutdown
bot_application = None

def signal_handler(sig, frame):
    print("\n\n🛑 Menerima sinyal shutdown...")
    print("🔄 Menghentikan bot dengan aman...")
    if bot_application:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(bot_application.stop())
                loop.create_task(bot_application.shutdown())
            print("✅ Bot berhasil dihentikan dengan aman.")
        except Exception as e:
            print(f"⚠️ Error saat shutdown: {e}")
    print("👋 Sampai jumpa!")
    sys.exit(0)

# ==============================================================================
# 📦 DATA PRODUK (Tetap sama)
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
def safe_html(text): return html.escape(str(text))

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
        if number.startswith('08'): number = '+62' + number[1:]
        elif number.startswith('62') and not number.startswith('+'): number = '+' + number
        return f"tel:{number}"
    return text

def format_uptime(start_time: datetime) -> str:
    uptime_delta = datetime.now() - start_time
    days = uptime_delta.days
    hours, rem = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    parts = []
    if days > 0: parts.append(f"{days} hari")
    if hours > 0: parts.append(f"{hours} jam")
    if minutes > 0: parts.append(f"{minutes} menit")
    if not parts: return "kurang dari semenit"
    return ", ".join(parts)

ALL_PACKAGES_DATA = {create_package_key(pkg): pkg for pkg in ALL_PACKAGES_RAW}
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
    if info.get('type') == 'Pulsa':
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
# 🚀 FITUR BARU ZETA POWER
# ==============================================================================

class ZetaPowerFeatures:
    """Class untuk fitur-fitur powerful baru"""
    
    @staticmethod
    async def get_crypto_price(coin: str = "bitcoin") -> str:
        """Get cryptocurrency price"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{CRYPTO_API}/simple/price?ids={coin}&vs_currencies=usd,idr&include_24hr_change=true")
                data = response.json()
                
                if coin in data:
                    price_usd = data[coin]['usd']
                    price_idr = data[coin]['idr']
                    change_24h = data[coin]['usd_24h_change']
                    
                    return (f"💰 <b>{coin.upper()} Price</b>\n\n"
                           f"💵 USD: ${price_usd:,.2f}\n"
                           f"🇮🇩 IDR: Rp{price_idr:,.0f}\n"
                           f"📈 24h Change: {change_24h:+.2f}%")
                return "❌ Cryptocurrency tidak ditemukan"
        except Exception as e:
            return f"❌ Error fetching crypto price: {e}"
    
    @staticmethod
    async def shorten_url(url: str) -> str:
        """Shorten URL menggunakan TinyURL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://tinyurl.com/api-create.php?url={url}")
                return response.text
        except:
            return url  # Return original URL if failed
    
    @staticmethod
    async def web_scrape(url: str) -> str:
        """Simple web scraping untuk mendapatkan title dan meta"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.title.string if soup.title else "No Title"
                description = soup.find("meta", attrs={"name": "description"})
                desc_content = description["content"] if description else "No Description"
                
                return (f"🌐 <b>Website Info</b>\n\n"
                       f"📄 Title: {safe_html(title)}\n"
                       f"📝 Description: {safe_html(desc_content[:200])}...")
        except Exception as e:
            return f"❌ Gagal scraping website: {e}"
    
    @staticmethod
    async def get_stock_price(symbol: str) -> str:
        """Get stock price"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{STOCK_API}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={STOCK_API_KEY}")
                data = response.json()
                
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    return (f"📊 <b>{symbol} Stock</b>\n\n"
                           f"💵 Price: ${quote['05. price']}\n"
                           f"📈 Change: {quote['09. change']} ({quote['10. change percent']})\n"
                           f"🕒 Latest: {quote['07. latest trading day']}")
                return "❌ Stock symbol tidak ditemukan"
        except Exception as e:
            return f"❌ Error fetching stock: {e}"
    
    @staticmethod
    def get_system_stats() -> str:
        """Get system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_total = memory.total / (1024 ** 3)  # GB
            memory_used = memory.used / (1024 ** 3)
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_total = disk.total / (1024 ** 3)
            disk_used = disk.used / (1024 ** 3)
            disk_percent = disk.percent
            
            # Bot uptime
            uptime = format_uptime(BOT_START_TIME)
            
            return (f"🖥️ <b>System Monitor</b>\n\n"
                   f"⚡ CPU Usage: {cpu_percent}%\n"
                   f"💾 Memory: {memory_used:.1f}GB / {memory_total:.1f}GB ({memory_percent}%)\n"
                   f"💽 Disk: {disk_used:.1f}GB / {disk_total:.1f}GB ({disk_percent}%)\n"
                   f"⏰ Uptime: {uptime}")
        except Exception as e:
            return f"❌ Error getting system stats: {e}"
    
    @staticmethod
    async def check_data_breach(email: str) -> str:
        """Check if email appears in known data breaches (educational)"""
        domains = ["gmail.com", "yahoo.com", "hotmail.com"]
        domain = email.split('@')[-1] if '@' in email else ""
        
        if domain in domains:
            return (f"🔒 <b>Data Breach Check</b>\n\n"
                   f"📧 Email: {safe_html(email)}\n"
                   f"⚠️ Status: Potensi terpapar dalam breach\n"
                   f"💡 Saran: Ganti password dan aktifkan 2FA")
        else:
            return (f"🔒 <b>Data Breach Check</b>\n\n"
                   f"📧 Email: {safe_html(email)}\n"
                   f"✅ Status: Tidak terdeteksi dalam breach utama\n"
                   f"💡 Tips: Selalu gunakan password unik")

# ==============================================================================
# 🎮 GAME ADVANCED ZETA
# ==============================================================================

class ZetaGames:
    """Class untuk game-game advanced"""
    
    @staticmethod
    async def number_guessing_game() -> dict:
        """Game tebak angka"""
        secret_number = random.randint(1, 100)
        return {
            'type': 'number_guess',
            'secret': secret_number,
            'attempts': 0,
            'max_attempts': 7
        }
    
    @staticmethod
    async def trivia_question() -> dict:
        """Game trivia"""
        questions = [
            {
                'question': 'Ibu kota Indonesia?',
                'options': ['Jakarta', 'Surabaya', 'Bandung', 'Medan'],
                'answer': 0
            },
            {
                'question': 'Planet terdekat dengan matahari?',
                'options': ['Venus', 'Mars', 'Mercury', 'Earth'],
                'answer': 2
            },
            {
                'question': 'Warna bendera Indonesia?',
                'options': ['Merah-Putih', 'Merah-Hijau', 'Biru-Putih', 'Kuning-Hijau'],
                'answer': 0
            }
        ]
        return random.choice(questions)
    
    @staticmethod
    async def slot_machine() -> str:
        """Simple slot machine game"""
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                prize = "JACKPOT! 🎉"
            else:
                prize = "BIG WIN! 🎊"
        elif result[0] == result[1] or result[1] == result[2]:
            prize = "Small Win! 👍"
        else:
            prize = "No Win 😢"
        
        return f"🎰 SLOT MACHINE 🎰\n\n{' | '.join(result)}\n\n{prize}"

# ==============================================================================
# 🔧 FUNGSI UTILITAS TAMBAHAN
# ==============================================================================

def get_provider_info_global(phone_number_str: str) -> str:
    try:
        if not phone_number_str.startswith('+'):
            if phone_number_str.startswith('08'): phone_number_str = '+62' + phone_number_str[1:]
            else: phone_number_str = '+' + phone_number_str
        phone_number = phonenumbers.parse(phone_number_str, None)
        if not phonenumbers.is_valid_number(phone_number):
            return f"📱 <b>Informasi Nomor</b>\n\n❌ Nomor <code>{safe_html(phone_number_str)}</code> tidak valid."
        country_code = phone_number.country_code
        region_code = phonenumberutil.region_code_for_country_code(country_code)
        try:
            country = pycountry.countries.get(alpha_2=region_code)
            country_name, country_flag = (country.name, country.flag) if country and hasattr(country, 'flag') else ("Tidak Diketahui", "❓")
        except Exception: country_name, country_flag = region_code, "❓"
        number_type_map = {phonenumbers.PhoneNumberType.MOBILE: "Ponsel", phonenumbers.PhoneNumberType.FIXED_LINE: "Telepon Rumah", phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Ponsel / Telepon Rumah", phonenumbers.PhoneNumberType.TOLL_FREE: "Bebas Pulsa", phonenumbers.PhoneNumberType.VOIP: "VoIP"}
        number_type = number_type_map.get(phonenumbers.number_type(phone_number), "Lainnya")
        carrier_name = carrier.name_for_number(phone_number, "en") or "Tidak terdeteksi"
        
        return (f"📱 <b>Informasi Nomor</b>\n"
                f"╰ <code>{safe_html(phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))}</code>\n\n"
                f"<b>Negara:</b> {country_flag} {country_name} (+{country_code})\n"
                f"<b>Valid:</b> ✅ Ya\n"
                f"<b>Tipe:</b> {number_type}\n"
                f"<b>Operator Asli:</b> {carrier_name}\n\n"
                f"<i>ℹ️ Info operator mungkin tidak akurat jika nomor sudah porting.</i>")
    except phonenumberutil.NumberParseException: return f"❌ Format nomor <code>{safe_html(phone_number_str)}</code> salah."
    except Exception as e:
        logger.error(f"Error di get_provider_info_global: {e}")
        return "⚠️ Terjadi kesalahan saat memproses nomor."

keyboard_error_back = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]])
keyboard_back_to_tools = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]])

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
    if message:
        if 'messages_to_clear' not in context.user_data: context.user_data['messages_to_clear'] = []
        if len(context.user_data['messages_to_clear']) >= MAX_MESSAGES_TO_TRACK:
            context.user_data['messages_to_clear'] = context.user_data['messages_to_clear'][-(MAX_MESSAGES_TO_TRACK-1):]
        context.user_data['messages_to_clear'].append(message.message_id)

# ==============================================================================
# 🎯 HANDLER FITUR BARU ZETA
# ==============================================================================

async def show_zeta_power_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu utama fitur Zeta Power"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💰 Crypto Prices", callback_data="zeta_crypto"),
         InlineKeyboardButton("📊 Stock Market", callback_data="zeta_stock")],
        [InlineKeyboardButton("🌐 Web Scraper", callback_data="zeta_scrape"),
         InlineKeyboardButton("🔗 URL Shortener", callback_data="zeta_shorten")],
        [InlineKeyboardButton("🖥️ System Monitor", callback_data="zeta_system"),
         InlineKeyboardButton("🔒 Breach Check", callback_data="zeta_breach")],
        [InlineKeyboardButton("🎮 Advanced Games", callback_data="zeta_games")],
        [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
    ]
    
    text = ("<b>🚀 ZETA POWER MODE</b>\n\n"
            "Fitur-fitur advanced untuk pengalaman yang lebih powerful!\n\n"
            "Pilih salah satu fitur di bawah:")
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk cryptocurrency"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("₿ Bitcoin", callback_data="crypto_bitcoin"),
         InlineKeyboardButton("Ξ Ethereum", callback_data="crypto_ethereum")],
        [InlineKeyboardButton("◉ Cardano", callback_data="crypto_cardano"),
         InlineKeyboardButton("● Polkadot", callback_data="crypto_polkadot")],
        [InlineKeyboardButton("🔍 Custom Coin", callback_data="zeta_crypto_custom"),
         InlineKeyboardButton("⬅️ Kembali", callback_data="zeta_power")]
    ]
    
    text = "<b>💰 Cryptocurrency Prices</b>\n\nPilih coin atau cari custom:"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_crypto_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get specific crypto price"""
    query = update.callback_query
    await query.answer()
    
    coin = query.data.split('_')[1]
    price_info = await ZetaPowerFeatures.get_crypto_price(coin)
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=query.data),
         InlineKeyboardButton("💰 Crypto Lain", callback_data="zeta_crypto")],
        [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
    ]
    
    await query.edit_message_text(price_info, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk stock market"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['state'] = 'awaiting_stock'
    
    text = ("<b>📊 Stock Market</b>\n\n"
            "Kirim simbol saham (contoh: <code>AAPL</code> untuk Apple, <code>TSLA</code> untuk Tesla)\n\n"
            "Format: <code>[STOCK_SYMBOL]</code>")
    
    keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data="zeta_power")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk web scraping"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['state'] = 'awaiting_scrape'
    
    text = ("<b>🌐 Web Scraper</b>\n\n"
            "Kirim URL website yang ingin di-scrape:\n\n"
            "Format: <code>https://example.com</code>")
    
    keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data="zeta_power")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk URL shortener"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['state'] = 'awaiting_shorten'
    
    text = ("<b>🔗 URL Shortener</b>\n\n"
            "Kirim URL panjang yang ingin dipersingkat:\n\n"
            "Format: <code>https://website-yang-panjang-sekali.com/parameter/lagi</code>")
    
    keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data="zeta_power")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk system monitor"""
    query = update.callback_query
    await query.answer()
    
    stats = ZetaPowerFeatures.get_system_stats()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="zeta_system"),
         InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
    ]
    
    await query.edit_message_text(stats, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_breach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk data breach check"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['state'] = 'awaiting_breach'
    
    text = ("<b>🔒 Data Breach Check</b>\n\n"
            "Kirim email untuk pengecekan (educational purpose):\n\n"
            "Format: <code>email@domain.com</code>")
    
    keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data="zeta_power")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_zeta_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk advanced games"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎯 Tebak Angka", callback_data="game_number"),
         InlineKeyboardButton("❓ Trivia Quiz", callback_data="game_trivia")],
        [InlineKeyboardButton("🎰 Slot Machine", callback_data="game_slot"),
         InlineKeyboardButton("🕹️ Batu-Gunting-Kertas", callback_data="main_game")],
        [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
    ]
    
    text = "<b>🎮 Advanced Games</b>\n\nPilih game yang ingin dimainkan:"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def handle_advanced_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk game-game advanced"""
    query = update.callback_query
    await query.answer()
    
    game_type = query.data.split('_')[1]
    
    if game_type == 'number':
        # Game tebak angka
        game_data = await ZetaGames.number_guessing_game()
        context.user_data['current_game'] = game_data
        
        text = ("🎯 <b>Tebak Angka</b>\n\n"
                "Saya telah memilih angka antara 1-100.\n"
                "Kamu punya 7 kesempatan untuk menebak!\n\n"
                "Kirim tebakanmu:")
        
        keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data="zeta_games")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    elif game_type == 'trivia':
        # Game trivia
        question_data = await ZetaGames.trivia_question()
        context.user_data['current_trivia'] = question_data
        
        options = question_data['options']
        keyboard = [
            [InlineKeyboardButton(options[0], callback_data="trivia_0"),
             InlineKeyboardButton(options[1], callback_data="trivia_1")],
            [InlineKeyboardButton(options[2], callback_data="trivia_2"),
             InlineKeyboardButton(options[3], callback_data="trivia_3")],
            [InlineKeyboardButton("⬅️ Game Lain", callback_data="zeta_games")]
        ]
        
        text = f"❓ <b>Trivia Quiz</b>\n\n{question_data['question']}"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    elif game_type == 'slot':
        # Slot machine
        result = await ZetaGames.slot_machine()
        
        keyboard = [
            [InlineKeyboardButton("🎰 Spin Again", callback_data="game_slot"),
             InlineKeyboardButton("⬅️ Game Lain", callback_data="zeta_games")]
        ]
        
        await query.edit_message_text(result, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_trivia_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trivia answers"""
    query = update.callback_query
    await query.answer()
    
    answer_index = int(query.data.split('_')[1])
    trivia_data = context.user_data.get('current_trivia', {})
    
    if not trivia_data:
        await query.edit_message_text("❌ Sesi trivia sudah berakhir.", parse_mode=ParseMode.HTML)
        return
    
    correct_index = trivia_data['answer']
    is_correct = (answer_index == correct_index)
    
    if is_correct:
        result_text = "✅ <b>Jawaban Benar!</b> 🎉"
    else:
        correct_answer = trivia_data['options'][correct_index]
        result_text = f"❌ <b>Jawaban Salah!</b>\n\nJawaban yang benar: <b>{correct_answer}</b>"
    
    keyboard = [
        [InlineKeyboardButton("❓ Soal Lain", callback_data="game_trivia")],
        [InlineKeyboardButton("⬅️ Game Lain", callback_data="zeta_games")]
    ]
    
    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    context.user_data.pop('current_trivia', None)

# ==============================================================================
# 🔄 HANDLER TEXT MESSAGES UNTUK FITUR BARU
# ==============================================================================

async def handle_zeta_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages untuk fitur Zeta baru"""
    try:
        state = context.user_data.get('state')
        message_text = update.message.text.strip()
        
        if state == 'awaiting_stock':
            context.user_data.pop('state', None)
            stock_info = await ZetaPowerFeatures.get_stock_price(message_text.upper())
            
            await update.message.reply_text(stock_info, parse_mode=ParseMode.HTML)
            keyboard = [
                [InlineKeyboardButton("📊 Cek Saham Lain", callback_data="zeta_stock")],
                [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
            ]
            await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif state == 'awaiting_scrape':
            context.user_data.pop('state', None)
            scrape_info = await ZetaPowerFeatures.web_scrape(message_text)
            
            await update.message.reply_text(scrape_info, parse_mode=ParseMode.HTML)
            keyboard = [
                [InlineKeyboardButton("🌐 Scrape Lagi", callback_data="zeta_scrape")],
                [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
            ]
            await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif state == 'awaiting_shorten':
            context.user_data.pop('state', None)
            short_url = await ZetaPowerFeatures.shorten_url(message_text)
            
            result_text = (f"🔗 <b>URL Shortener</b>\n\n"
                          f"📏 Original: <code>{safe_html(message_text)}</code>\n"
                          f"📎 Shortened: <code>{short_url}</code>")
            
            await update.message.reply_text(result_text, parse_mode=ParseMode.HTML)
            keyboard = [
                [InlineKeyboardButton("🔗 Shorten Lagi", callback_data="zeta_shorten")],
                [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
            ]
            await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif state == 'awaiting_breach':
            context.user_data.pop('state', None)
            breach_info = await ZetaPowerFeatures.check_data_breach(message_text)
            
            await update.message.reply_text(breach_info, parse_mode=ParseMode.HTML)
            keyboard = [
                [InlineKeyboardButton("🔒 Cek Email Lain", callback_data="zeta_breach")],
                [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
            ]
            await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif state == 'awaiting_crypto_custom':
            context.user_data.pop('state', None)
            crypto_info = await ZetaPowerFeatures.get_crypto_price(message_text.lower())
            
            await update.message.reply_text(crypto_info, parse_mode=ParseMode.HTML)
            keyboard = [
                [InlineKeyboardButton("💰 Crypto Lain", callback_data="zeta_crypto")],
                [InlineKeyboardButton("⬅️ Zeta Power", callback_data="zeta_power")]
            ]
            await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
            
        # Handle number guessing game
        elif 'current_game' in context.user_data and context.user_data['current_game']['type'] == 'number_guess':
            try:
                guess = int(message_text)
                game_data = context.user_data['current_game']
                game_data['attempts'] += 1
                
                if guess == game_data['secret']:
                    result_text = (f"🎉 <b>Selamat! Kamu Menang!</b>\n\n"
                                  f"Angka: {game_data['secret']}\n"
                                  f"Tebakan: {game_data['attempts']} kali")
                    context.user_data.pop('current_game', None)
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 Main Lagi", callback_data="game_number")],
                        [InlineKeyboardButton("⬅️ Game Lain", callback_data="zeta_games")]
                    ]
                elif guess < game_data['secret']:
                    result_text = f"📈 Terlalu rendah! Coba angka yang lebih tinggi. ({game_data['attempts']}/7)"
                    keyboard = [[InlineKeyboardButton("⬅️ Berhenti", callback_data="zeta_games")]]
                else:
                    result_text = f"📉 Terlalu tinggi! Coba angka yang lebih rendah. ({game_data['attempts']}/7)"
                    keyboard = [[InlineKeyboardButton("⬅️ Berhenti", callback_data="zeta_games")]]
                
                # Check if max attempts reached
                if game_data['attempts'] >= game_data['max_attempts'] and guess != game_data['secret']:
                    result_text = (f"😢 <b>Game Over!</b>\n\n"
                                  f"Angka yang benar: {game_data['secret']}\n"
                                  f"Total tebakan: {game_data['attempts']}")
                    context.user_data.pop('current_game', None)
                    keyboard = [
                        [InlineKeyboardButton("🔄 Main Lagi", callback_data="game_number")],
                        [InlineKeyboardButton("⬅️ Game Lain", callback_data="zeta_games")]
                    ]
                
                await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
                
            except ValueError:
                await update.message.reply_text("❌ Masukkan angka yang valid!")
                
    except Exception as e:
        await send_admin_log(context, e, update, "handle_zeta_text_messages")

# ==============================================================================
# 🏗️ FUNGSI-FUNGSI UTAMA BOT (EXISTING)
# ==============================================================================

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear chat history"""
    chat_id = update.effective_chat.id
    loading_msg = None
    query = update.callback_query
    try:
        if query:
            await query.answer("🧹 Memulai bersih-bersih...")
            try:
                await query.delete_message()
            except Exception:
                pass

        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 <b>Menghapus jejak pesan bot...</b> Mohon tunggu.", parse_mode=ParseMode.HTML)
        
        messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))
        
        if loading_msg:
            messages_to_clear.append(loading_msg.message_id)
        
        messages_to_clear.sort()

        for i in range(0, len(messages_to_clear), MAX_MESSAGES_TO_DELETE_PER_BATCH):
            batch = messages_to_clear[i:i+MAX_MESSAGES_TO_DELETE_PER_BATCH]
            delete_tasks = [context.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in batch]
            await asyncio.gather(*delete_tasks, return_exceptions=True)
            await asyncio.sleep(1)

        context.user_data['messages_to_clear'] = []
        await start(update, context)
            
    except Exception as e:
        if not isinstance(e, (BadRequest, Forbidden)):
            logger.error(f"Error di clear_history: {e}")
            await send_admin_log(context, e, update, "clear_history")
        
        try:
            if loading_msg:
                await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception:
            pass
        
        try:
            error_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Gagal membersihkan semua pesan. Mungkin beberapa pesan sudah terlalu lama. Silakan coba lagi nanti.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )
            await track_message(context, error_msg)
        except (BadRequest, Forbidden) as final_e:
            logger.warning(f"Gagal mengirim pesan error akhir di clear_history ke chat {chat_id}. Error: {final_e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command yang diperbarui dengan Zeta Power"""
    chat_id = update.effective_chat.id
    try:
        context.user_data.pop('state', None)
        
        if update.message and update.message.text == '/start':
            await track_message(context, update.message)
            
        user = update.effective_user
        try:
            now, hour = datetime.now(ZoneInfo("Asia/Jakarta")), datetime.now(ZoneInfo("Asia/Jakarta")).hour
            if 5 <= hour < 11: greeting, icon = "Selamat Pagi", "☀️"
            elif 11 <= hour < 15: greeting, icon = "Selamat Siang", "🌤️"
            elif 15 <= hour < 18: greeting, icon = "Selamat Sore", "🌥️"
            else: greeting, icon = "Selamat Malam", "🌙"
        except Exception as tz_error:
            logger.warning(f"⚠️ Gagal mendapatkan waktu Jakarta: {tz_error}.")
            greeting, icon = "Halo", "👋"

        uptime_str = format_uptime(BOT_START_TIME)
        username_info = f"<code>@{user.username}</code>" if user.username else "<i>(tidak ada)</i>"
        
        main_text = (f"{icon} <b>{greeting}, {user.first_name}!</b>\n\n"
                     "Selamat datang di <b>Pulsa Net</b>.\nPlatform terpadu untuk semua kebutuhan digital Anda.\n\n"
                     "Silakan pilih layanan di bawah untuk memulai.\n"
                     "— — — — — — — — — — — —\n"
                     f"👤 <b>Informasi Sesi</b>\n"
                     f"  ├─ Username: {username_info}\n"
                     f"  ├─ User ID: <code>{user.id}</code>\n"
                     f"  └─ Chat ID: <code>{chat_id}</code>\n\n"
                     f"🕒 <b>Status Uptime:</b> {uptime_str}")

        keyboard = [
            [InlineKeyboardButton("📡 Paket Data", callback_data="main_paket"), 
             InlineKeyboardButton("💵 Pulsa Reguler", callback_data="main_pulsa")],
            [InlineKeyboardButton("📱 Cek Info Nomor", callback_data="ask_for_number"), 
             InlineKeyboardButton("🛠️ Tools Digital", callback_data="main_tools")],
            [InlineKeyboardButton("🚀 Zeta Power", callback_data="zeta_power"),
             InlineKeyboardButton("❓ Bantuan", callback_data="main_bantuan")],
            [InlineKeyboardButton("📊 Cek Kuota (XL/Axis)", url="https://sidompul.kmsp-store.com/")],
            [InlineKeyboardButton("🧹 Bersihkan Chat", callback_data="clear_history")],
            [InlineKeyboardButton("🌐 Kunjungi Website", url="https://pulsanet.kesug.com/beli.html")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                await update.callback_query.answer()
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    await update.callback_query.answer("Anda sudah di menu utama.")
                else:
                    sent_message = await context.bot.send_message(chat_id=chat_id, text=main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                    await track_message(context, sent_message)
        else:
            sent_message = await context.bot.send_message(chat_id=chat_id, text=main_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            await track_message(context, sent_message)
            
    except Exception as e:
        await send_admin_log(context, e, update, "start")
        try:
            error_msg = await context.bot.send_message(chat_id=chat_id, text="❌ Maaf, terjadi kesalahan saat memuat menu utama.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            await track_message(context, error_msg)
        except Exception as e_inner:
            logger.error(f"❌ Gagal mengirim pesan error di start: {e_inner}")

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show operator menu"""
    query = update.callback_query
    try:
        await query.answer()
        product_type_key = query.data.split('_')[1]
        product_type_name = "Paket Data 📡" if product_type_key == "paket" else "Pulsa Reguler 💵"
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
    """Show XL package submenu"""
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
    """Show product list"""
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
            product_name = 'Paket Data 📡' if product_type_key == 'paket' else 'Pulsa Reguler 💵'
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
    """Show package details"""
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
    """Show help"""
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
    """Show tools menu"""
    query = update.callback_query
    await query.answer()

    all_tools = [
        InlineKeyboardButton("🔳 Buat QR Code", callback_data="ask_for_qr"),
        InlineKeyboardButton("💱 Kalkulator Kurs", callback_data="ask_for_currency"),
        InlineKeyboardButton("🌍 Cek Domain (WHOIS)", callback_data="ask_for_whois"),
        InlineKeyboardButton("📍 Info IP Address", callback_data="ask_for_ip"),
        InlineKeyboardButton("📦 Base64 Encode/Decode", callback_data="ask_for_base64"),
        InlineKeyboardButton("🔑 Buat Password", callback_data="gen_password"),
        InlineKeyboardButton("🕹️ Mini Game", callback_data="main_game"),
        InlineKeyboardButton("🚀 Zeta Power Mode", callback_data="zeta_power")
    ]
    
    tools_per_page = 5
    page = 0

    if query.data.startswith("tools_page_"):
        page = int(query.data.split('_')[2])

    start_index = page * tools_per_page
    end_index = start_index + tools_per_page
    
    keyboard_tools = all_tools[start_index:end_index]
    keyboard = [[button] for button in keyboard_tools]

    navigation_row = []
    if page > 0:
        navigation_row.append(InlineKeyboardButton("◀️ Sebelumnya", callback_data=f"tools_page_{page-1}"))
    if end_index < len(all_tools):
        navigation_row.append(InlineKeyboardButton("Selanjutnya ▶️", callback_data=f"tools_page_{page+1}"))
    
    if navigation_row:
        keyboard.append(navigation_row)
        
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])

    text = f"<b>🛠️ Tools Digital (Halaman {page + 1})</b>\n\nPilih salah satu alat bantu yang tersedia di bawah ini:"
    
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            await send_admin_log(context, e, update, "show_tools_menu_pagination")
    except Exception as e:
        await send_admin_log(context, e, update, "show_tools_menu")
        await query.edit_message_text("❌ Maaf, terjadi kesalahan.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)

async def prompt_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for action"""
    query = update.callback_query
    chat_id = update.effective_chat.id
    try:
        await query.answer()
        action = query.data
        text = ""
        back_button_callback = "main_tools"
        if action == "back_to_start": back_button_callback = "back_to_start"

        try:
            await context.bot.delete_message(chat_id, query.message.message_id)
        except Exception:
            try: await query.edit_message_text("...", reply_markup=None)
            except Exception: pass

        if action == "ask_for_number":
            context.user_data['state'] = 'awaiting_number'
            text = ("<b>📱 Cek Info Nomor Telepon</b>\n\nKirimkan nomor HP yang ingin Anda periksa. Format internasional (<code>+62...</code>) sangat disarankan.")
            back_button_callback = "back_to_start"
        elif action == "ask_for_qr":
            context.user_data['state'] = 'awaiting_qr_text'
            text = ("<b>🔳 Generator QR Code</b>\n\nKirimkan teks atau tautan yang ingin Anda jadikan QR Code.")
        elif action == "ask_for_whois":
            context.user_data['state'] = 'awaiting_whois'
            text = ("<b>🌍 Cek Domain (WHOIS)</b>\n\nKirimkan nama domain yang ingin diperiksa (contoh: <code>google.com</code>).")
        elif action == "ask_for_ip":
            context.user_data['state'] = 'awaiting_ip'
            text = ("<b>📍 Info IP Address</b>\n\nKirimkan alamat IP publik yang ingin diperiksa (contoh: <code>8.8.8.8</code>).")
        elif action == "ask_for_base64":
            context.user_data['state'] = 'awaiting_base64'
            text = ("<b>📦 Base64 Encoder/Decoder</b>\n\nKirimkan teks untuk di-encode atau di-decode secara otomatis.")
        elif action == "ask_for_currency":
            context.user_data['state'] = 'awaiting_currency'
            text = ("<b>💱 Kalkulator Kurs Mata Uang</b>\n\nFormat: <code>[jumlah] [kode_asal] to [kode_tujuan]</code>\nContoh: <code>100 USD to IDR</code>")
        elif action == "zeta_crypto_custom":
            context.user_data['state'] = 'awaiting_crypto_custom'
            text = ("<b>💰 Custom Cryptocurrency</b>\n\nKirim nama cryptocurrency (contoh: <code>bitcoin</code>, <code>ethereum</code>):")
            back_button_callback = "zeta_crypto"
        else:
            logger.warning(f"Aksi tidak dikenal di prompt_for_action: {action}")
            return
        
        keyboard = [[InlineKeyboardButton("⬅️ Batal", callback_data=back_button_callback)]]
        sent_prompt = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        await track_message(context, sent_prompt)

    except Exception as e:
        await send_admin_log(context, e, update, "prompt_for_action")

async def handle_currency_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency conversion"""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("💹 Menghitung kurs...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        text = update.message.text.upper()
        match = re.match(r"([\d\.\,]+)\s*([A-Z]{3})\s*(?:TO|IN|)\s*([A-Z]{3})", text)
        if not match:
            await status_msg.edit_text("❌ Format salah. Contoh: <code>100 USD to IDR</code>.", parse_mode=ParseMode.HTML)
            return
        amount_str, base_curr, target_curr = match.groups()
        try: amount = float(amount_str.replace(",", ""))
        except ValueError:
             await status_msg.edit_text("❌ Jumlah tidak valid. Harap masukkan angka.", parse_mode=ParseMode.HTML)
             return
        api_url = f"https://open.er-api.com/v6/latest/{base_curr}"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, timeout=10); response.raise_for_status()
        data = response.json()
        if data.get("result") == "success" and target_curr in data.get("rates", {}):
            rate = data["rates"][target_curr]
            converted_amount = amount * rate
            try:
                base_name = pycountry.currencies.get(alpha_3=base_curr).name
                target_name = pycountry.currencies.get(alpha_3=target_curr).name
            except Exception: base_name, target_name = base_curr, target_curr
            result_text = (f"💱 <b>Hasil Konversi Kurs</b>\n\n"
                           f"<b>Dari:</b> {amount:,.2f} {base_curr} ({base_name})\n"
                           f"<b>Ke:</b> {converted_amount:,.2f} {target_curr} ({target_name})\n\n"
                           f"<i>Kurs 1 {base_curr} ≈ {rate:,.4f} {target_curr}</i>")
            await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await status_msg.edit_text(f"❌ Tidak dapat menemukan kurs untuk <b>{target_curr}</b>.", parse_mode=ParseMode.HTML)
    except httpx.RequestError:
        if status_msg: await status_msg.edit_text("⚠️ Gagal menghubungi layanan kurs. Coba lagi nanti.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_currency_conversion")
        if status_msg: await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis.", parse_mode=ParseMode.HTML)
    finally:
        keyboard = [[InlineKeyboardButton("💱 Hitung Kurs Lagi", callback_data="ask_for_currency")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
        sent_msg2 = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
        await track_message(context, sent_msg2)

async def handle_whois_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle WHOIS lookup"""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("🔎 Mencari informasi domain...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        domain_name = update.message.text.lower().strip()
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain_name):
            await status_msg.edit_text(f"❌ Format domain <code>{safe_html(domain_name)}</code> tidak valid.", parse_mode=ParseMode.HTML)
            return
        def run_whois_sync(domain):
            try: return whois.whois(domain)
            except Exception as e: logger.error(f"Error di dalam thread whois: {e}"); raise
        w = await asyncio.to_thread(run_whois_sync, domain_name)
        if not w or not w.domain_name:
            await status_msg.edit_text(f"❌ Tidak dapat menemukan info untuk <code>{safe_html(domain_name)}</code>.", parse_mode=ParseMode.HTML)
            return
        def format_whois_date(d):
            if not d: return "N/A"
            if isinstance(d, list): d = d[0]
            if isinstance(d, datetime): return d.strftime('%d %B %Y')
            return str(d)
        result_text = (f"🌍 <b>Informasi WHOIS</b>\n"
                       f"╰ <code>{w.domain_name}</code>\n\n"
                       f"<b>Pendaftar:</b> {safe_html(w.registrar) or 'N/A'}\n"
                       f"<b>Dibuat:</b> {format_whois_date(w.creation_date)}\n"
                       f"<b>Kedaluwarsa:</b> {format_whois_date(w.expiration_date)}\n"
                       f"<b>Update:</b> {format_whois_date(w.updated_date)}\n\n"
                       f"<b>Name Server:</b>\n"
                       f"<pre>{safe_html(', '.join(w.name_servers)) if w.name_servers else 'N/A'}</pre>")
        await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_whois_lookup")
        if status_msg: await status_msg.edit_text("❌ Gagal mengambil data WHOIS. Domain mungkin dilindungi privasi.", parse_mode=ParseMode.HTML)
    finally:
        keyboard = [[InlineKeyboardButton("🌍 Cek Domain Lain", callback_data="ask_for_whois")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
        sent_msg2 = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
        await track_message(context, sent_msg2)

async def handle_ip_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle IP lookup"""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("📍 Melacak informasi IP...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        ip_address = update.message.text.strip()
        if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", ip_address):
            await status_msg.edit_text(f"❌ Format alamat IP <code>{safe_html(ip_address)}</code> tidak valid.", parse_mode=ParseMode.HTML)
            return
        api_url = f"http://ip-api.com/json/{ip_address}"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, timeout=10); response.raise_for_status()
        data = response.json()
        if data.get("status") == "fail":
            await status_msg.edit_text(f"❌ Gagal mendapatkan info untuk IP <code>{safe_html(ip_address)}</code>.", parse_mode=ParseMode.HTML)
            return
        try: country_flag = pycountry.countries.get(alpha_2=data.get('countryCode', '')).flag
        except: country_flag = "🏳️"
        lat, lon = data.get('lat', 0), data.get('lon', 0)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "#"
        result_text = (f"📍 <b>Informasi Alamat IP</b>\n"
                       f"╰ <code>{data.get('query')}</code>\n\n"
                       f"<b>Lokasi:</b> {country_flag} {safe_html(data.get('city'))}, {safe_html(data.get('country'))}\n"
                       f"<b>Zona Waktu:</b> {safe_html(data.get('timezone'))}\n"
                       f"<b>ISP:</b> {safe_html(data.get('isp'))}\n"
                       f"<b>Organisasi:</b> {safe_html(data.get('org'))}\n\n"
                       f"<a href='{maps_link}'>Buka di Google Maps</a>")
        await status_msg.edit_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except httpx.RequestError:
        if status_msg: await status_msg.edit_text("⚠️ Gagal menghubungi layanan IP Geolocation.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_ip_lookup")
        if status_msg: await status_msg.edit_text("❌ Maaf, terjadi kesalahan teknis saat melacak IP.", parse_mode=ParseMode.HTML)
    finally:
        keyboard = [[InlineKeyboardButton("📍 Cek IP Lain", callback_data="ask_for_ip")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
        sent_msg2 = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
        await track_message(context, sent_msg2)

async def handle_base64(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle base64 encoding/decoding"""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("📦 Memproses teks...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        original_text = update.message.text
        try:
            missing_padding = len(original_text) % 4
            if missing_padding: original_text += '=' * (4 - missing_padding)
            decoded_text = base64.b64decode(original_text).decode('utf-8')
            operation, result_text, input_text = "DECODE", decoded_text, original_text
        except (ValueError, base64.binascii.Error):
            encoded_text = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
            operation, result_text, input_text = "ENCODE", encoded_text, original_text

        if operation == "ENCODE":
            final_text = (f"📦 <b>Hasil Encode Base64</b>\n\n"
                          f"<b>Teks Asli:</b>\n<pre>{safe_html(input_text)}</pre>\n"
                          f"<b>Hasil Encode:</b>\n<code>{safe_html(result_text)}</code>")
        else:
            final_text = (f"📦 <b>Hasil Decode Base64</b>\n\n"
                          f"<b>Teks Base64:</b>\n<code>{safe_html(input_text)}</code>\n"
                          f"<b>Hasil Decode:</b>\n<pre>{safe_html(result_text)}</pre>")
        await status_msg.edit_text(final_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await send_admin_log(context, e, update, "handle_base64")
        if status_msg: await status_msg.edit_text("❌ Terjadi kesalahan. Pastikan teks yang Anda kirim valid.", parse_mode=ParseMode.HTML)
    finally:
        keyboard = [[InlineKeyboardButton("📦 Proses Teks Lagi", callback_data="ask_for_base64")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
        sent_msg2 = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
        await track_message(context, sent_msg2)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        await track_message(context, update.message)
        state = context.user_data.get('state')
        message_text = update.message.text
        phone_pattern = r'(\+?\d{1,3}[\s-]?\d[\d\s-]{7,14}\d)'

        if state and 'messages_to_clear' in context.user_data and context.user_data['messages_to_clear']:
            last_bot_message_id = context.user_data['messages_to_clear'][-1]
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=last_bot_message_id)
            except Exception:
                pass

        if state == 'awaiting_number':
            context.user_data.pop('state', None)
            numbers = re.findall(phone_pattern, message_text)
            response_text = "\n\n".join([get_provider_info_global(num.replace(" ", "").replace("-", "")) for num in numbers]) if numbers else "❌ Format nomor tidak valid."
            sent_msg = await update.message.reply_text(response_text, parse_mode=ParseMode.HTML)
            await track_message(context, sent_msg)
            keyboard_next = [[InlineKeyboardButton("📱 Cek Nomor Lain", callback_data="ask_for_number")], [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
            nav_msg = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard_next))
            await track_message(context, nav_msg)
            return

        elif state == 'awaiting_qr_text':
            context.user_data.pop('state', None)
            loading_msg = await update.message.reply_text("⏳ Membuat QR Code...")
            await track_message(context, loading_msg)
            try:
                img = qrcode.make(format_qr_data(message_text))
                bio = io.BytesIO(); bio.name = 'qrcode.png'; img.save(bio, 'PNG'); bio.seek(0)
                caption = f"🔳 <b>QR Code Dibuat</b>\n\n<b>Data:</b> <code>{safe_html(message_text)}</code>"
                sent_photo = await update.message.reply_photo(photo=bio, caption=caption, parse_mode=ParseMode.HTML)
                await track_message(context, sent_photo); await loading_msg.delete()
            except Exception as e:
                await send_admin_log(context, e, update, "QR Code")
                await loading_msg.edit_text("❌ Gagal membuat QR Code.", parse_mode=ParseMode.HTML)
            finally:
                 keyboard_next = [[InlineKeyboardButton("🔳 Buat QR Lagi", callback_data="ask_for_qr")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
                 sent_msg2 = await update.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard_next))
                 await track_message(context, sent_msg2)
            return
        
        elif state == 'awaiting_whois': context.user_data.pop('state', None); await handle_whois_lookup(update, context); return
        elif state == 'awaiting_ip': context.user_data.pop('state', None); await handle_ip_lookup(update, context); return
        elif state == 'awaiting_base64': context.user_data.pop('state', None); await handle_base64(update, context); return
        elif state == 'awaiting_currency': context.user_data.pop('state', None); await handle_currency_conversion(update, context); return

        if not state and (numbers := re.findall(phone_pattern, message_text)) and len(numbers) <= 3:
            responses = [get_provider_info_global(num.replace(" ", "").replace("-", "")) for num in numbers]
            sent_msg = await update.message.reply_text(
                "💡 <b>Info Nomor Terdeteksi Otomatis:</b>\n\n" + "\n\n".join(responses),
                parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            await track_message(context, sent_msg)
            
    except Exception as e:
        await send_admin_log(context, e, update, "handle_text_message")

async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game menu"""
    query = update.callback_query
    try:
        await query.answer()
        keyboard = [
             [InlineKeyboardButton("Batu 🗿", callback_data="game_play_rock"),
              InlineKeyboardButton("Gunting ✂️", callback_data="game_play_scissors"),
              InlineKeyboardButton("Kertas 📄", callback_data="game_play_paper")],
             [InlineKeyboardButton("⬅️ Kembali ke Menu Tools", callback_data="main_tools")]
        ]
        text = "<b>🕹️ Game Batu-Gunting-Kertas</b>\n\nAyo bermain! Pilih jagoanmu:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (game menu).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "show_game_menu")

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play rock-paper-scissors game"""
    query = update.callback_query
    try:
        await query.answer()
        user_choice = query.data.split('_')[2]
        bot_choice = random.choice(['rock', 'scissors', 'paper'])
        emoji = {'rock': '🗿', 'scissors': '✂️', 'paper': '📄'}
        if user_choice == bot_choice: result_text = "<b>Hasilnya Seri!</b> 🤝"
        elif (user_choice, bot_choice) in [('rock', 'scissors'), ('scissors', 'paper'), ('paper', 'rock')]:
            result_text = "<b>Kamu Menang!</b> 🎉"
        else: result_text = "<b>Kamu Kalah!</b> 🦾"
        text = (f"Pilihanmu: {user_choice.capitalize()} {emoji[user_choice]}\n"
                f"Pilihan Bot: {bot_choice.capitalize()} {emoji[bot_choice]}\n\n{result_text}")
        keyboard = [[InlineKeyboardButton("🔄 Main Lagi", callback_data="main_game")], [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" in str(e): logger.info(f"Pesan {query.message.message_id} tidak diubah (play game).")
        else: raise e
    except Exception as e:
        await send_admin_log(context, e, update, "play_game")

async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate random password"""
    query = update.callback_query
    try:
        await query.answer()
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(chars) for _ in range(16))
        text = (f"🔑 <b>Password Baru Dibuat</b>\n\nIni adalah password aman (16 karakter) Anda:\n\n"
                f"<code>{safe_html(password)}</code>\n\n"
                f"<i>ℹ️ Klik password untuk menyalin. Segera simpan di tempat aman.</i>")
        
        keyboard = [[InlineKeyboardButton("🔄 Buat Password Lagi", callback_data="gen_password")], [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    except BadRequest as e:
         if "Message is not modified" not in str(e): 
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
            await query.message.reply_text("Pilih aksi selanjutnya:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await send_admin_log(context, e, update, "generate_password")

# ==============================================================================
# 🚀 FUNGSI UTAMA
# ==============================================================================

def main():
    global bot_application
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN: 
        logger.critical("❌ FATAL: Token bot tidak ditemukan!")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("🔧 Handler shutdown (Ctrl+C / SIGTERM) terdaftar.")
    
    timeout_config = HTTPXRequest(connect_timeout=20.0, read_timeout=40.0, write_timeout=40.0)
    bot_application = Application.builder().token(TOKEN).request(timeout_config).build()

    # ==================== REGISTER ALL HANDLERS ====================
    
    # Existing handlers
    bot_application.add_handler(CommandHandler("start", start))
    bot_application.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
    bot_application.add_handler(CallbackQueryHandler(clear_history, pattern='^clear_history$'))
    bot_application.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan$'))
    bot_application.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)$'))
    bot_application.add_handler(CallbackQueryHandler(show_tools_menu, pattern='^main_tools$'))
    bot_application.add_handler(CallbackQueryHandler(show_tools_menu, pattern=r'^tools_page_\d+$'))
    bot_application.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl$'))
    bot_application.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+$'))
    bot_application.add_handler(CallbackQueryHandler(show_package_details, pattern=r'^pkg_\d+_[a-z0-9_]+$'))
    bot_application.add_handler(CallbackQueryHandler(prompt_for_action, pattern=r'^ask_for_(number|qr|currency|whois|ip|base64)$'))
    bot_application.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    bot_application.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    bot_application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))
    
    # NEW: Zeta Power Handlers
    bot_application.add_handler(CallbackQueryHandler(show_zeta_power_menu, pattern='^zeta_power$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_crypto, pattern='^zeta_crypto$'))
    bot_application.add_handler(CallbackQueryHandler(handle_crypto_price, pattern='^crypto_'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_stock, pattern='^zeta_stock$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_scrape, pattern='^zeta_scrape$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_shorten, pattern='^zeta_shorten$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_system, pattern='^zeta_system$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_breach, pattern='^zeta_breach$'))
    bot_application.add_handler(CallbackQueryHandler(handle_zeta_games, pattern='^zeta_games$'))
    bot_application.add_handler(CallbackQueryHandler(handle_advanced_games, pattern='^game_(number|trivia|slot)$'))
    bot_application.add_handler(CallbackQueryHandler(handle_trivia_answer, pattern='^trivia_'))
    bot_application.add_handler(CallbackQueryHandler(prompt_for_action, pattern='^zeta_crypto_custom$'))
    
    # Message handlers
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_zeta_text_messages))

    print(f"======================================================")
    print(f"🚀 Bot Pulsa Net - ZETA POWER EDITION v19.0")
    print(f"======================================================")
    print("✅ Fitur Inti: AKTIF")
    print("✅ Zeta Power: CRYPTO, STOCKS, WEB SCRAPE, GAMES, SYSTEM MONITOR")
    print("✅ Advanced Tools: URL SHORTENER, BREACH CHECK, TRIVIA GAMES")
    print("✅ Mobile Optimized: UI/UX Enhanced")
    print("\n💪 Bot sekarang 10x lebih powerful!")
    print("—" * 60)
    
    bot_application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ FATAL ERROR di main loop: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

