# ============================================
# 🤖 Bot Pulsa Net - VERSION COMPLETE
# File: bot_pulsanet_complete.py
# Developer: frd009
# Versi: 16.16.2 (Complete & Fixed)
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
from pathlib import Path

# ==============================================================================
# 🔧 IMPORT DENGAN ERROR HANDLING
# ==============================================================================

try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        import pytz
        class ZoneInfoFallback:
            def __init__(self, zone_name):
                self.zone = pytz.timezone(zone_name)
            def __getattr__(self, name):
                return getattr(self.zone, name)
        ZoneInfo = ZoneInfoFallback

# Import libraries dengan error handling
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("⚠️  qrcode tidak tersedia")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL/Pillow tidak tersedia")

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("❌ yt_dlp tidak tersedia")

try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, phonenumberutil
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    print("❌ phonenumbers tidak tersedia")

try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False
    print("⚠️  pycountry tidak tersedia")

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ChatAction, ParseMode
    from telegram.error import TelegramError, RetryAfter, BadRequest, TimedOut
    from telegram.request import HTTPXRequest
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("❌ python-telegram-bot tidak tersedia")

# ==============================================================================
# ⚙️ KONFIGURASI
# ==============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")
try:
    if ADMIN_ID:
        ADMIN_ID = int(ADMIN_ID.strip())
except ValueError:
    ADMIN_ID = None
    logger.error("TELEGRAM_ADMIN_ID harus berupa angka!")

MAX_MESSAGES_TO_TRACK = 50
MAX_MESSAGES_TO_DELETE_PER_BATCH = 30
CHROME_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
MAX_UPLOAD_FILE_SIZE_MB = 300
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

YOUTUBE_COOKIE_FILE = 'youtube_cookies.txt'
GENERIC_COOKIE_FILE = 'generic_cookies.txt'

# ==============================================================================
# 📦 DATA PRODUK LENGKAP
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
# 🛠️ FUNGSI UTILITAS LENGKAP
# ==============================================================================

def safe_html(text):
    """Escape HTML dengan handling None"""
    if text is None:
        return ""
    return html.escape(str(text))

def create_package_key(pkg):
    """Buat key unik untuk package"""
    name_slug = re.sub(r'[^a-z0-9_]', '', pkg['name'].lower().replace(' ', '_'))
    return f"pkg_{pkg['id']}_{name_slug}"

def format_qr_data(text: str) -> str:
    """Format data untuk QR Code"""
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
    """Format bytes ke readable format"""
    if size is None:
        return "N/A"
    try:
        size = float(size)
        power = 1024
        n = 0
        power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size > power and n < len(power_labels) - 1:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}"
    except (TypeError, ValueError):
        return "N/A"

# Inisialisasi data package
ALL_PACKAGES_DATA = {create_package_key(pkg): pkg for pkg in ALL_PACKAGES_RAW}
PRICES = {key: data['price'] for key, data in ALL_PACKAGES_DATA.items()}

def get_products(category=None, product_type=None, special_type=None):
    """Filter produk berdasarkan kategori dan tipe"""
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

def get_provider_info_global(phone_number_str: str) -> str:
    """Fungsi canggih untuk mendapatkan info nomor telepon dari seluruh dunia."""
    if not PHONENUMBERS_AVAILABLE:
        return "❌ Fitur cek nomor tidak tersedia. Library 'phonenumbers' tidak terinstall."
    
    try:
        phone_number_str = str(phone_number_str).strip()
        if not phone_number_str:
            return "Nomor telepon tidak boleh kosong."
        
        if not phone_number_str.startswith('+'):
            if phone_number_str.startswith('0'):
                phone_number_str = '+62' + phone_number_str[1:]
            elif phone_number_str.startswith('62'):
                phone_number_str = '+' + phone_number_str
            else:
                phone_number_str = '+' + phone_number_str
        
        phone_number = phonenumbers.parse(phone_number_str, None)
        
        if not phonenumbers.is_valid_number(phone_number):
            return f"❌ Nomor <code>{safe_html(phone_number_str)}</code> tidak valid."
        
        country_code = phone_number.country_code
        region_code = phonenumberutil.region_code_for_country_code(country_code)
        
        country_name = "Tidak Diketahui"
        country_flag = "🏳️"
        if PYCOUNTRY_AVAILABLE:
            try:
                country = pycountry.countries.get(alpha_2=region_code)
                if country:
                    country_name = country.name
                    country_flag = "🇺🇳"
            except Exception:
                pass
        
        number_type_map = {
            phonenumbers.PhoneNumberType.MOBILE: "📱 Ponsel",
            phonenumbers.PhoneNumberType.FIXED_LINE: "🏠 Telepon Rumah",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "📞 Ponsel/Telepon Rumah",
            phonenumbers.PhoneNumberType.TOLL_FREE: "🆓 Bebas Pulsa",
            phonenumbers.PhoneNumberType.VOIP: "💻 VoIP",
        }
        number_type = number_type_map.get(
            phonenumbers.number_type(phone_number), 
            "❓ Lainnya"
        )
        
        carrier_name = carrier.name_for_number(phone_number, "en") or "Tidak terdeteksi"
        
        output = (
            f"<b>📞 Hasil Pengecekan Nomor</b>\n"
            f"────────────────────\n"
            f"<b>Nomor:</b> <code>{safe_html(phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))}</code>\n"
            f"<b>Negara:</b> {country_flag} {country_name} (+{country_code})\n"
            f"<b>Valid:</b> ✅ Ya\n"
            f"<b>Tipe:</b> {number_type}\n"
            f"<b>Operator:</b> {carrier_name}\n"
            f"<i>Info operator mungkin tidak akurat jika nomor sudah porting</i>"
        )
        
        return output
        
    except phonenumberutil.NumberParseException as e:
        return f"❌ Format nomor <code>{safe_html(phone_number_str)}</code> salah. Gunakan format internasional (contoh: +6281234567890)."
    except Exception as e:
        logger.error(f"Error di get_provider_info_global: {e}")
        return "❌ Terjadi kesalahan saat memproses nomor. Pastikan format nomor benar."

def validate_url(url):
    """Validasi URL dengan regex yang komprehensif"""
    if not url or not isinstance(url, str):
        return False
    
    url_patterns = [
        r'https?://[^\s]+',
        r'www\.[^\s]+\.[a-z]{2,}',
        r'youtu\.be/[^\s]+',
        r'tiktok\.com/[^\s]+',
        r'instagram\.com/[^\s]+',
        r'twitter\.com/[^\s]+',
        r'facebook\.com/[^\s]+'
    ]
    
    for pattern in url_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

# ==============================================================================
# 🍪 COOKIE MANAGEMENT LENGKAP
# ==============================================================================

def setup_cookie_files():
    """Setup cookie files dengan error handling"""
    youtube_valid = False
    generic_valid = False
    
    youtube_cookie_b64 = os.environ.get("YOUTUBE_COOKIES_BASE64")
    if youtube_cookie_b64:
        try:
            cookie_data = base64.b64decode(youtube_cookie_b64).decode('utf-8')
            with open(YOUTUBE_COOKIE_FILE, 'w', encoding='utf-8') as f:
                f.write(cookie_data)
            logger.info(f"✅ File {YOUTUBE_COOKIE_FILE} berhasil dibuat")
            youtube_valid = True
        except Exception as e:
            logger.error(f"❌ Gagal setup YouTube cookies: {e}")
    else:
        logger.warning("⚠️ YOUTUBE_COOKIES_BASE64 tidak ditemukan")
    
    generic_cookie_b64 = os.environ.get("GENERIC_COOKIES_BASE64")
    if generic_cookie_b64:
        try:
            cookie_data = base64.b64decode(generic_cookie_b64).decode('utf-8')
            with open(GENERIC_COOKIE_FILE, 'w', encoding='utf-8') as f:
                f.write(cookie_data)
            logger.info(f"✅ File {GENERIC_COOKIE_FILE} berhasil dibuat")
            generic_valid = True
        except Exception as e:
            logger.error(f"❌ Gagal setup generic cookies: {e}")
    else:
        logger.warning("⚠️ GENERIC_COOKIES_BASE64 tidak ditemukan")
    
    return youtube_valid, generic_valid

def get_ytdlp_options(url: str = None):
    """Return yt-dlp options dengan konfigurasi optimal"""
    if not YT_DLP_AVAILABLE:
        return {}
    
    opts = {
        'quiet': True,
        'no_warnings': False,
        'noplaylist': True,
        'rm_cachedir': True,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'http_headers': {'User-Agent': CHROME_USER_AGENT},
        'nocheckcertificate': True,
    }
    
    if url and isinstance(url, str) and validate_url(url):
        cookie_file_to_use = None
        
        if any(domain in url.lower() for domain in ['youtube.com', 'youtu.be']):
            if os.path.exists(YOUTUBE_COOKIE_FILE):
                cookie_file_to_use = YOUTUBE_COOKIE_FILE
        else:
            if os.path.exists(GENERIC_COOKIE_FILE):
                cookie_file_to_use = GENERIC_COOKIE_FILE
        
        if cookie_file_to_use:
            opts['cookiefile'] = cookie_file_to_use
    
    return opts

def run_yt_dlp_sync(ydl_opts, url, download=False):
    """Synchronous wrapper untuk yt-dlp dengan error handling"""
    if not YT_DLP_AVAILABLE:
        raise ImportError("yt_dlp tidak tersedia")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=download)
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        raise

# ==============================================================================
# 🤖 HANDLER BOT LENGKAP
# ==============================================================================

keyboard_error_back = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]
])

async def send_admin_log(context: ContextTypes.DEFAULT_TYPE, error: Exception, update: Update, from_where: str, custom_message: str = ""):
    """Memformat dan mengirim log error ke Admin"""
    if not ADMIN_ID:
        return

    try:
        tb_list = traceback.format_exception(None, error, error.__traceback__)
        tb_string = "".join(tb_list)
        user = update.effective_user
        
        actionable_message = f"<b>Pesan Aksi:</b> {custom_message}\n\n" if custom_message else ""

        admin_message = (
            f"🚨 <b>BOT ERROR LOG</b> 🚨\n\n"
            f"{actionable_message}"
            f"<b>Fungsi:</b> <code>{from_where}</code>\n"
            f"<b>User:</b> {user.mention_html() if user else 'N/A'} (ID: <code>{user.id if user else 'N/A'}</code>)\n"
            f"<b>Chat ID:</b> <code>{update.effective_chat.id if update.effective_chat else 'N/A'}</code>\n\n"
            f"<b>Tipe Error:</b> <code>{type(error).__name__}</code>\n"
            f"<b>Pesan Error:</b>\n<pre>{safe_html(str(error))}</pre>\n\n"
            f"<b>Traceback (Ringkas):</b>\n<pre>{safe_html(tb_string[-1500:])}</pre>"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=admin_message, 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Gagal mengirim log error ke admin: {e}")

async def track_message(context: ContextTypes.DEFAULT_TYPE, message):
    """Track pesan untuk dibersihkan nanti"""
    if message:
        if 'messages_to_clear' not in context.user_data:
            context.user_data['messages_to_clear'] = []
        if len(context.user_data['messages_to_clear']) >= MAX_MESSAGES_TO_TRACK:
            context.user_data['messages_to_clear'] = context.user_data['messages_to_clear'][-(MAX_MESSAGES_TO_TRACK-1):]
        context.user_data['messages_to_clear'].append(message.message_id)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bersihkan history chat"""
    try:
        chat_id = update.effective_chat.id
        if update.callback_query:
            await update.callback_query.answer("Memulai pembersihan riwayat...")
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
            except Exception:
                pass
        
        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🔄 <b>Sedang menghapus pesan...</b>", parse_mode=ParseMode.HTML)
        messages_to_clear = list(set(context.user_data.get('messages_to_clear', [])))
        messages_to_clear = messages_to_clear[-MAX_MESSAGES_TO_DELETE_PER_BATCH:]
        
        delete_tasks = [context.bot.delete_message(chat_id=chat_id, message_id=msg_id) for msg_id in messages_to_clear if msg_id != loading_msg.message_id]
        results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=loading_msg.message_id)
        except Exception:
            pass
        
        context.user_data['messages_to_clear'] = []
        
        confirmation_text = f"✅ <b>Pembersihan Selesai!</b>\n\nBerhasil menghapus <b>{success_count}</b> pesan dari sesi ini."
        
        sent_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text=confirmation_text, 
            reply_markup=keyboard_error_back, 
            parse_mode=ParseMode.HTML
        )
        await track_message(context, sent_msg)
            
    except Exception as e:
        await send_admin_log(context, e, update, "clear_history")
        try:
            error_msg = await context.bot.send_message(
                chat_id=chat_id, 
                text="Maaf, terjadi kesalahan saat membersihkan chat.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
            await track_message(context, error_msg)
        except Exception as e_inner:
            logger.error(f"Failed to send error message in clear_history: {e_inner}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler command /start"""
    try:
        chat_id = update.effective_chat.id
        context.user_data.pop('state', None)
        
        if update.message and update.message.text == '/start':
            await track_message(context, update.message)
            
        user = update.effective_user
        jakarta_tz = ZoneInfo("Asia/Jakarta")
        now = datetime.now(jakarta_tz)
        hour = now.hour
        
        if 5 <= hour < 11:
            greeting, icon = "Selamat Pagi", "☀️"
        elif 11 <= hour < 15:
            greeting, icon = "Selamat Siang", "🌤️"
        elif 15 <= hour < 18:
            greeting, icon = "Selamat Sore", "🌥️"
        else:
            greeting, icon = "Selamat Malam", "🌙"
            
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
                await update.callback_query.edit_message_text(
                    main_text, 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode=ParseMode.HTML
                )
                await update.callback_query.answer()
            except BadRequest as e:
                if "Message is not modified" in str(e):
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
            error_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="Maaf, terjadi kesalahan saat memuat menu utama.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
            await track_message(context, error_msg)
        except:
            pass

async def show_tools_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu tools dan hiburan"""
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
        
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await send_admin_log(context, e, update, "show_tools_menu")
        await query.edit_message_text(
            "Maaf, terjadi kesalahan.", 
            reply_markup=keyboard_error_back, 
            parse_mode=ParseMode.HTML
        )

async def prompt_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt untuk berbagai aksi"""
    query = update.callback_query
    try:
        await query.answer()
        action = query.data
        text = ""
        back_button_callback = "main_tools"

        if action == "ask_for_number":
            context.user_data['state'] = 'awaiting_number'
            text = (
                "<b>🔍 Cek Info Nomor Telepon (Global)</b>\n\n"
                "Silakan kirimkan nomor HP yang ingin Anda periksa, <b>wajib</b> dengan format internasional.\n\n"
                "Contoh: <code>+6281234567890</code> (Indonesia), <code>+12025550139</code> (USA)."
            )
            back_button_callback = "back_to_start"
        elif action == "ask_for_qr":
            context.user_data['state'] = 'awaiting_qr_text'
            text = "<b>🖼️ Generator QR Code</b>\n\nKirimkan teks, tautan, atau nomor HP yang ingin Anda jadikan QR Code."
        elif action == "ask_for_youtube":
            context.user_data['state'] = 'awaiting_youtube_link'
            text = "<b>▶️ YouTube Downloader</b>\n\nKirimkan link video YouTube yang ingin Anda unduh."
        elif action == "ask_for_media_link":
            context.user_data['state'] = 'awaiting_media_link'
            text = (
                "<b>🔗 Media Downloader Universal</b>\n\n"
                "Kirimkan link dari Instagram, Twitter, TikTok, Facebook, dll. untuk mengunduh video atau gambar."
            )
        elif action == "ask_for_currency":
            context.user_data['state'] = 'awaiting_currency'
            text = (
                "<b>💹 Kalkulator Kurs Mata Uang</b>\n\n"
                "Kirimkan permintaan konversi Anda dalam format:\n"
                "<code>[jumlah] [kode_asal] to [kode_tujuan]</code>\n\n"
                "<b>Contoh:</b>\n"
                "• <code>100 USD to IDR</code>\n"
                "• <code>50 EUR JPY</code>\n"
                "• <code>1000000 IDR MYR</code>"
            )
        else:  
            return
            
        keyboard = [[InlineKeyboardButton("⬅️ Batal & Kembali", callback_data=back_button_callback)]]
        
        await query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await send_admin_log(context, e, update, "prompt_for_action")
        await query.edit_message_text(
            "Maaf, terjadi kesalahan.", 
            reply_markup=keyboard_error_back, 
            parse_mode=ParseMode.HTML
        )

async def handle_currency_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler konversi mata uang"""
    status_msg = None
    try:
        status_msg = await update.message.reply_text("💱 Menghitung...", parse_mode=ParseMode.HTML)
        await track_message(context, status_msg)
        
        text = update.message.text.upper()
        match = re.match(r"([\d\.\,]+)\s*([A-Z]{3})\s*(?:TO|IN|)\s*([A-Z]{3})", text)
        
        if not match:
            await status_msg.edit_text(
                "Format salah. Contoh: <code>100 USD to IDR</code>.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
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
            
            base_name = base_curr
            target_name = target_curr
            
            if PYCOUNTRY_AVAILABLE:
                try:
                    base_country = pycountry.currencies.get(alpha_3=base_curr)
                    base_name = base_country.name if base_country else base_curr
                    target_country = pycountry.currencies.get(alpha_3=target_curr)
                    target_name = target_country.name if target_country else target_curr
                except Exception:
                    pass
            
            result_text = (
                f"✅ <b>Hasil Konversi</b>\n\n"
                f"<b>Dari:</b> {amount:,.2f} {base_curr} ({base_name})\n"
                f"<b>Ke:</b> {converted_amount:,.2f} {target_curr} ({target_name})\n\n"
                f"<i>Kurs 1 {base_curr} = {rate:,.4f} {target_curr}</i>\n"
                f"<a href='https://www.google.com/finance/quote/{base_curr}-{target_curr}'>Sumber data real-time</a>"
            )
            
            await status_msg.edit_text(
                result_text, 
                parse_mode=ParseMode.HTML, 
                disable_web_page_preview=True
            )
        else:
            await status_msg.edit_text(
                f"Tidak dapat menemukan kurs untuk <b>{target_curr}</b>.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
            
    except httpx.RequestError as e:
        await send_admin_log(context, e, update, "handle_currency_conversion (RequestError)")
        if status_msg:
            await status_msg.edit_text(
                "Gagal menghubungi layanan kurs. Coba lagi nanti.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        await send_admin_log(context, e, update, "handle_currency_conversion")
        if status_msg:
            await status_msg.edit_text(
                "Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )

async def handle_media_download(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Handle download media dari berbagai platform"""
    status_msg = None
    downloaded_files = []
    
    try:
        status_msg = await update.message.reply_text(
            "📥 <b>Mengunduh media...</b> Ini mungkin akan memakan waktu.", 
            parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)

        if not validate_url(url):
            await status_msg.edit_text(
                "❌ <b>Link tidak valid!</b>\nPastikan Anda mengirimkan tautan yang benar.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )
            return

        file_path_template = f"media_{update.effective_message.message_id}_%(title)s.%(ext)s"
        ydl_opts = get_ytdlp_options(url=url)
        ydl_opts['outtmpl'] = file_path_template
        ydl_opts['max_filesize'] = MAX_UPLOAD_FILE_SIZE_BYTES
        
        info_dict = await asyncio.to_thread(
            run_yt_dlp_sync, ydl_opts, url, download=True
        )

        file_path = info_dict.get('_filename', '')
        if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
            download_dir = Path('.')
            pattern = f"media_{update.effective_message.message_id}_*"
            matching_files = list(download_dir.glob(pattern))
            
            if matching_files:
                file_path = str(matching_files[0])
            else:
                raise FileNotFoundError("File tidak ditemukan setelah download")

        downloaded_files.append(file_path)
        
        await status_msg.edit_text("📤 <b>Mengirim file...</b>", parse_mode=ParseMode.HTML)
        
        title = info_dict.get('title', 'Media')
        caption = f"<b>{safe_html(title)}</b>\n\nDiunduh dengan @{context.bot.username}"
        
        file_ext = Path(file_path).suffix.lower()
        with open(file_path, 'rb') as f:
            if file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, 
                    action=ChatAction.UPLOAD_PHOTO
                )
                sent_message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, 
                    action=ChatAction.UPLOAD_VIDEO
                )
                sent_message = await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    read_timeout=60,
                    write_timeout=60
                )
        
        await status_msg.delete()
        
        keyboard_next = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Unduh Media Lain", callback_data="ask_for_media_link")],
            [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
        ])
        
        next_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ <b>Unduhan berhasil!</b> Apa yang ingin Anda lakukan selanjutnya?",
            reply_markup=keyboard_next,
            parse_mode=ParseMode.HTML
        )
        await track_message(context, next_msg)
        
    except Exception as e:
        logger.error(f"Error dalam handle_media_download: {e}")
        
        error_message = "❌ <b>Gagal mengunduh media!</b>\n"
        if "Private" in str(e) or "login" in str(e).lower():
            error_message += "Konten ini bersifat privat atau memerlukan login."
        elif "unavailable" in str(e).lower():
            error_message += "Konten tidak tersedia atau telah dihapus."
        elif "too large" in str(e).lower() or "max filesize" in str(e).lower():
            error_message += f"File terlalu besar (max {MAX_UPLOAD_FILE_SIZE_MB}MB)."
        else:
            error_message += "Terjadi kesalahan teknis."
        
        if status_msg:
            try:
                await status_msg.edit_text(
                    error_message,
                    reply_markup=keyboard_error_back,
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                await update.message.reply_text(
                    error_message,
                    reply_markup=keyboard_error_back,
                    parse_mode=ParseMode.HTML
                )
        
        await send_admin_log(context, e, update, "handle_media_download")
    
    finally:
        for file_path in downloaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Gagal menghapus file {file_path}: {e}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk pesan teks"""
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
                sent_msg = await update.message.reply_text(
                    "\n\n---\n\n".join(responses), 
                    reply_markup=keyboard_next_action, 
                    parse_mode=ParseMode.HTML
                )
            else:
                sent_msg = await update.message.reply_text(
                    "Format nomor telepon tidak valid. Gunakan format internasional: `+kode_negara nomor`.",  
                    reply_markup=keyboard_next_action,
                    parse_mode=ParseMode.HTML
                )
            await track_message(context, sent_msg)
            context.user_data.pop('state', None)
            return

        elif state == 'awaiting_qr_text':
            if not QRCODE_AVAILABLE:
                sent_msg = await update.message.reply_text(
                    "❌ Fitur QR Code tidak tersedia. Library 'qrcode' tidak terinstall.",
                    reply_markup=keyboard_error_back,
                    parse_mode=ParseMode.HTML
                )
                await track_message(context, sent_msg)
                context.user_data.pop('state', None)
                return

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
                    
                sent_photo = await update.message.reply_photo(
                    photo=bio, 
                    caption=caption_text, 
                    parse_mode=ParseMode.HTML
                )
                await track_message(context, sent_photo)
                
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id, 
                        message_id=loading_msg.message_id
                    )
                except TelegramError:
                    pass

            except Exception as e:
                await send_admin_log(context, e, update, "handle_text_message (QR Code)")
                try:
                    await loading_msg.edit_text(
                        "Maaf, terjadi kesalahan saat membuat QR Code.", 
                        reply_markup=keyboard_error_back
                    )
                except Exception:
                    pass
                    
            context.user_data.pop('state', None)
            keyboard = [
                [InlineKeyboardButton("🖼️ Buat QR Lain", callback_data="ask_for_qr")],  
                [InlineKeyboardButton("⬅️ Kembali ke Tools", callback_data="main_tools")]
            ]
            sent_msg2 = await update.message.reply_text(
                "Apa yang ingin Anda lakukan selanjutnya?", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await track_message(context, sent_msg2)
            return
            
        elif state == 'awaiting_youtube_link':
            if re.search(r'(youtube\.com|youtu\.be|m\.youtube\.com)', message_text):
                await show_youtube_quality_options(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text(
                    "Link YouTube tidak valid. Pastikan Anda mengirimkan tautan yang benar dari YouTube.", 
                    reply_markup=keyboard_error_back, 
                    parse_mode=ParseMode.HTML
                )
                await track_message(context, sent_msg)
            context.user_data.pop('state', None)
            return
        
        elif state == 'awaiting_media_link':
            if re.search(url_pattern, message_text):
                await handle_media_download(update, context, message_text)
            else:
                sent_msg = await update.message.reply_text(
                    "Link tidak valid. Pastikan Anda mengirimkan tautan yang benar.", 
                    reply_markup=keyboard_error_back, 
                    parse_mode=ParseMode.HTML
                )
                await track_message(context, sent_msg)
            context.user_data.pop('state', None)
            return

        elif state == 'awaiting_currency':
            await handle_currency_conversion(update, context)
            context.user_data.pop('state', None)
            keyboard = [
                [InlineKeyboardButton("💹 Hitung Kurs Lain", callback_data="ask_for_currency")],  
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]
            ]
            sent_msg2 = await update.message.reply_text(
                "Apa yang ingin Anda lakukan selanjutnya?", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
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

async def show_youtube_quality_options(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Tampilkan opsi kualitas YouTube"""
    status_msg = None
    try:
        status_msg = await context.bot.send_message(
            update.effective_chat.id, 
            "🔍 <b>Menganalisis link...</b>", 
            parse_mode=ParseMode.HTML
        )
        await track_message(context, status_msg)
        
        ydl_opts = get_ytdlp_options(url=url)
        
        try:
            info_dict = await asyncio.to_thread(run_yt_dlp_sync, ydl_opts, url, download=False)
        except yt_dlp.utils.DownloadError as e:
            error_str = str(e).lower()
            
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
                    "1. Export fresh cookies dari browser\n"
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
            
            raise e

        video_id, title, formats = info_dict.get('id', ''), info_dict.get('title', 'Video'), info_dict.get('formats', [])
        keyboard, video_formats = [], []
        
        for f in formats:
            if (f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4' and 
                f.get('height') and f.get('height') <= 720):
                file_size_bytes = f.get('filesize') or f.get('filesize_approx')
                if not file_size_bytes or file_size_bytes <= MAX_UPLOAD_FILE_SIZE_BYTES:
                    video_formats.append(f)
        
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
            await status_msg.edit_text(
                f"Tidak ditemukan format yang cocok untuk diunduh (atau melebihi batas {MAX_UPLOAD_FILE_SIZE_MB} MB).", 
                reply_markup=keyboard_error_back, 
                parse_mode=ParseMode.HTML
            )
            return
        
        keyboard.append([InlineKeyboardButton("⬅️ Batal", callback_data="main_tools")])
        await status_msg.edit_text(
            f"<b>{safe_html(title)}</b>\n\n"
            "Pilih kualitas yang ingin Anda unduh:\n\n"
            f"<i>⚠️ <b>Perhatian:</b> File di atas {MAX_UPLOAD_FILE_SIZE_MB} MB mungkin gagal dikirim karena batasan Telegram Bot.</i>",
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await send_admin_log(context, e, update, "show_youtube_quality_options")
        if status_msg:
            await status_msg.edit_text(
                "Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.",
                reply_markup=keyboard_error_back,
                parse_mode=ParseMode.HTML
            )

async def handle_youtube_download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pilihan download YouTube"""
    query = update.callback_query
    file_path = None
    status_msg = None
    
    try:
        await query.answer("Memulai proses unduh...")
        try:
            status_msg = await query.edit_message_text(
                f"📥 <b>Mengunduh...</b>\n\n<i>Ini mungkin akan memakan waktu.</i>", 
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            status_msg = query.message
        
        _, video_id, format_id = query.data.split('|')
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        is_video = any('📹' in btn.text for row in query.message.reply_markup.inline_keyboard 
                       for btn in row if hasattr(btn, 'callback_data') and btn.callback_data == query.data)

        file_path_template = f"{video_id}_{format_id}.%(ext)s"
        
        ydl_opts = get_ytdlp_options(url=url) 
        ydl_opts['outtmpl'] = file_path_template
        ydl_opts['max_filesize'] = MAX_UPLOAD_FILE_SIZE_BYTES

        if is_video:
            ydl_opts['format'] = f"{format_id}+bestaudio/best"
            action = ChatAction.UPLOAD_VIDEO
        else:
            ydl_opts['format'] = f"{format_id}/bestaudio/best"
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
                ValueError(f"File downloaded but size ({format_bytes(final_file_size)}) > {MAX_UPLOAD_FILE_SIZE_MB}MB."),
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

        await status_msg.edit_text("📤 <b>Mengirim file...</b>", parse_mode=ParseMode.HTML)

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=action)
        
        caption = f"<b>{safe_html(title)}</b>\n\nDiunduh dengan @{context.bot.username}"
        with open(file_path, 'rb') as f:
            if is_video:
                sent_file = await context.bot.send_video(
                    update.effective_chat.id, 
                    video=f, 
                    caption=caption,  
                    parse_mode=ParseMode.HTML, 
                    read_timeout=300, 
                    write_timeout=300
                )
            else:
                sent_file = await context.bot.send_audio(
                    update.effective_chat.id, 
                    audio=f, 
                    caption=caption,  
                    parse_mode=ParseMode.HTML, 
                    read_timeout=300, 
                    write_timeout=300
                )
        await track_message(context, sent_file)
        
        try:
            await status_msg.delete()
        except TelegramError:
            pass

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
        
        cookie_errors = [
            'sign in to confirm', 'no suitable proxies', '410 gone',
            'unable to extract', 'login required', 'this video requires payment',
            'private video', 'members only', 'age restricted'
        ]

        if any(err in error_str for err in cookie_errors):
            admin_alert = ("CRITICAL: YouTube cookie authentication failed during download.")
            await send_admin_log(context, e, update, "handle_youtube_download_choice (Cookie/Auth Error)", custom_message=admin_alert)
            reply_text = "Maaf, terjadi kendala teknis pada layanan unduh video. Tim kami telah diberitahu. (Authentikasi YouTube gagal)"
        elif 'max filesize' in error_str:
            reply_text = f"❌ <b>Gagal!</b> Ukuran file yang dipilih melebihi batas unduh bot ({MAX_UPLOAD_FILE_SIZE_MB} MB)."
        elif 'video unavailable' in error_str:
            reply_text = "❌ <b>Gagal!</b> Video tidak tersedia atau telah dihapus."
        elif 'georestricted' in error_str:
            reply_text = "❌ <b>Gagal!</b> Video ini dibatasi secara geografis (geo-restricted)."
        else:
            await send_admin_log(context, e, update, "handle_youtube_download_choice (DownloadError)")
            reply_text = f"Maaf, terjadi kesalahan saat mengunduh file. (Error: {str(e)[:100]}...)"
        
        if status_msg:
            try:
                await status_msg.edit_text(reply_text, reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except Exception:
                pass
    except Exception as e:
        await send_admin_log(context, e, update, "handle_youtube_download_choice")
        if status_msg:
            try:
                await status_msg.edit_text("Maaf, terjadi kesalahan teknis. Tim kami sudah diberitahu.", reply_markup=keyboard_error_back, parse_mode=ParseMode.HTML)
            except Exception:
                pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Gagal menghapus file {file_path}: {e}")

async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate password acak"""
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
        await query.edit_message_text(
            "Maaf, terjadi kesalahan saat membuat password.", 
            reply_markup=keyboard_error_back, 
            parse_mode=ParseMode.HTML
        )

# ==============================================================================
# 🚀 FUNGSI UTAMA LENGKAP
# ==============================================================================

def signal_handler(sig, frame):
    """Handler untuk graceful shutdown"""
    print("\n\n🛑 Menerima signal shutdown...")
    print("👋 Goodbye!")
    sys.exit(0)

def main():
    """Fungsi utama"""
    
    if not TELEGRAM_AVAILABLE:
        print("❌ ERROR: python-telegram-bot tidak terinstall!")
        print("💡 Install dengan: pip install python-telegram-bot")
        sys.exit(1)
    
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN tidak ditemukan!")
        print("💡 Export token Anda: export TELEGRAM_BOT_TOKEN='your_token'")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    youtube_valid, generic_valid = setup_cookie_files()
    
    print("🔧 Status Dependencies:")
    print(f"   ✅ telegram: Terpasang")
    print(f"   ✅ httpx: Terpasang") 
    print(f"   📦 yt-dlp: {'✅ Terpasang' if YT_DLP_AVAILABLE else '❌ Tidak Terpasang'}")
    print(f"   📦 phonenumbers: {'✅ Terpasang' if PHONENUMBERS_AVAILABLE else '❌ Tidak Terpasang'}")
    print(f"   📦 pycountry: {'✅ Terpasang' if PYCOUNTRY_AVAILABLE else '⚠️  Tidak Terpasang'}")
    print(f"   🖼️  qrcode: {'✅ Terpasang' if QRCODE_AVAILABLE else '⚠️  Tidak Terpasang'}")
    print(f"   🍪 YouTube Cookies: {'✅ Valid' if youtube_valid else '❌ Tidak Valid'}")
    print(f"   🍪 Generic Cookies: {'✅ Valid' if generic_valid else '⚠️  Tidak Valid'}")
    
    try:
        request = HTTPXRequest(
            connect_timeout=20.0,
            read_timeout=30.0,
            write_timeout=30.0
        )
        
        application = Application.builder().token(TOKEN).request(request).build()
        
        # Register semua handler
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
        application.add_handler(CallbackQueryHandler(clear_history, pattern='^clear_history$'))
        application.add_handler(CallbackQueryHandler(show_tools_menu, pattern='^main_tools$'))
        application.add_handler(CallbackQueryHandler(prompt_for_action, pattern=r'^ask_for_(number|qr|youtube|currency|media_link)$'))
        application.add_handler(CallbackQueryHandler(handle_youtube_download_choice, pattern=r'^yt_dl\|.+'))
        application.add_handler(CallbackQueryHandler(generate_password, pattern='^gen_password$'))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        
        print(f"\n🤖 Bot Pulsa Net v16.16.2 berhasil diinisialisasi!")
        print("📍 Bot sedang berjalan...")
        print("💡 Tekan Ctrl+C untuk menghentikan bot")
        print("=" * 50)
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error utama: {e}")
        print(f"❌ Gagal menjalankan bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
