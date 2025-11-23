# ============================================
# 🤖 Bot Pulsa Net - Enterprise Edition
# File: bot_pro.py
# Developer: frd099
# Version: 19.0 (Architecture Rewrite)
# ============================================

import os
import re
import html
import logging
import asyncio
import sys
import io
import time
import base64
import traceback
import string
import random
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Union, Any

# --- Third Party Imports ---
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

import qrcode
import httpx
import phonenumbers
from phonenumbers import carrier, phonenumberutil
import pycountry
import whois
from cachetools import TTLCache

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    InputFile
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.error import BadRequest, Forbidden

# ==============================================================================
# ⚙️ CONFIGURATION & ENV
# ==============================================================================
class Config:
    """Centralized Configuration"""
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")
    # Jika True, bot hanya merespon Admin (Mode Maintenance)
    MAINTENANCE_MODE = False 
    # Cache untuk API eksternal (Kurs, IP, dll) selama 10 menit
    CACHE_TTL = 600 
    # Rate limit: Max 1 request per detik per user
    RATE_LIMIT_DELAY = 1.0 

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("PulsaNetBot")

if not Config.TOKEN:
    logger.critical("❌ TELEGRAM_BOT_TOKEN tidak ditemukan di Environment Variable!")
    sys.exit(1)

# ==============================================================================
# 🛡️ SECURITY & DECORATORS
# ==============================================================================
def rate_limit(func):
    """Decorator untuk mencegah spamming tombol/command."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        current_time = time.time()
        
        # Ambil data last_interaction user
        last_time = context.user_data.get('last_interaction', 0)
        
        if current_time - last_time < Config.RATE_LIMIT_DELAY:
            # Jika terlalu cepat, abaikan (silent ignore) atau beri warning
            return 
            
        context.user_data['last_interaction'] = current_time
        return await func(update, context, *args, **kwargs)
    return wrapped

def admin_only(func):
    """Decorator khusus fitur admin."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id != str(Config.ADMIN_ID):
            return # Silent ignore
        return await func(update, context, *args, **kwargs)
    return wrapped

# ==============================================================================
# 📦 DATA MANAGER (DATABASE MOCKUP)
# ==============================================================================
class ProductManager:
    """Mengelola data produk, pencarian, dan filtering."""
    
    def __init__(self):
        # Simulasi database. Di production, ini bisa load dari JSON atau SQL.
        self.raw_data = [
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
        self._data_map = {self.create_key(p): p for p in self.raw_data}

    @staticmethod
    def create_key(pkg):
        name_slug = re.sub(r'[^a-z0-9_]', '', pkg['name'].lower().replace(' ', '_'))
        return f"pkg_{pkg['id']}_{name_slug}"

    def get_by_key(self, key):
        return self._data_map.get(key)

    def filter(self, category=None, type_filter=None, subtype_filter=None):
        results = self.raw_data
        if category:
            results = [p for p in results if p['category'].lower() == category.lower()]
        
        if subtype_filter:
             results = [p for p in results if p['type'].lower() == subtype_filter.lower()]
        elif type_filter:
             # Special case for XL Packet Submenus
             if category and category.lower() == 'xl' and type_filter.lower() == 'paket':
                 excluded = ['akrab', 'bebaspuas', 'circle']
                 results = [p for p in results if p['type'].lower() == 'paket' and p['type'].lower() not in excluded]
             else:
                 results = [p for p in results if p['type'].lower() == type_filter.lower()]
                 
        return sorted(results, key=lambda x: x['price'])

# Initialize Global Managers
db = ProductManager()

# ==============================================================================
# 🛠️ UTILITY SERVICES (WITH CACHING)
# ==============================================================================
class NetworkTools:
    """Mengelola tools jaringan dengan cache untuk performa."""
    
    _cache = TTLCache(maxsize=100, ttl=Config.CACHE_TTL)

    @staticmethod
    def get_provider_info(phone_number_str: str) -> str:
        try:
            # Format number logic
            if not phone_number_str.startswith('+'):
                if phone_number_str.startswith('08'): phone_number_str = '+62' + phone_number_str[1:]
                else: phone_number_str = '+' + phone_number_str
            
            phone_number = phonenumbers.parse(phone_number_str, None)
            if not phonenumbers.is_valid_number(phone_number):
                return f"❌ Nomor <code>{html.escape(phone_number_str)}</code> tidak valid."

            # Data Extraction
            region_code = phonenumberutil.region_code_for_country_code(phone_number.country_code)
            country = pycountry.countries.get(alpha_2=region_code)
            country_name = country.name if country else region_code
            country_flag = country.flag if country and hasattr(country, 'flag') else "❓"
            carrier_name = carrier.name_for_number(phone_number, "en") or "Tidak terdeteksi"
            
            formatted = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            
            return (
                f"📱 <b>Informasi Nomor</b>\n"
                f"╰ <code>{formatted}</code>\n\n"
                f"🏳️ <b>Negara:</b> {country_flag} {country_name} (+{phone_number.country_code})\n"
                f"📡 <b>Operator:</b> {carrier_name}\n"
            )
        except Exception:
            return f"❌ Format nomor <code>{html.escape(phone_number_str)}</code> salah."

    @classmethod
    async def get_currency_rate(cls, amount: float, base: str, target: str) -> str:
        cache_key = f"curr_{base}_{target}"
        
        # Cek Cache
        rate = cls._cache.get(cache_key)
        
        if not rate:
            try:
                api_url = f"https://open.er-api.com/v6/latest/{base}"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(api_url, timeout=10)
                    data = resp.json()
                
                if data['result'] == 'success' and target in data['rates']:
                    rate = data['rates'][target]
                    cls._cache[cache_key] = rate # Simpan ke cache
                else:
                    return f"❌ Gagal menemukan kurs untuk {target}."
            except Exception as e:
                logger.error(f"Currency API Error: {e}")
                return "⚠️ Layanan kurs sedang gangguan."

        converted = amount * rate
        return (
            f"💱 <b>Konversi:</b>\n"
            f"{amount:,.2f} {base} ➡️ <b>{converted:,.2f} {target}</b>\n"
            f"<i>Rate: 1 {base} = {rate:,.4f} {target}</i>"
        )

    @classmethod
    async def get_ip_info(cls, ip_addr: str) -> str:
        cache_key = f"ip_{ip_addr}"
        data = cls._cache.get(cache_key)
        
        if not data:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://ip-api.com/json/{ip_addr}", timeout=10)
                    data = resp.json()
                    if data['status'] == 'success':
                        cls._cache[cache_key] = data
                    else:
                        return f"❌ IP {ip_addr} tidak ditemukan."
            except Exception:
                return "⚠️ Gagal menghubungi server IP info."
        
        lat, lon = data.get('lat'), data.get('lon')
        maps = f"https://www.google.com/maps?q={lat},{lon}"
        
        return (
            f"📍 <b>IP Info:</b> <code>{data.get('query')}</code>\n"
            f"🏙️ <b>Kota:</b> {data.get('city')}, {data.get('countryCode')}\n"
            f"🏢 <b>ISP:</b> {data.get('isp')}\n"
            f"🔗 <a href='{maps}'>Lihat di Peta</a>"
        )

    @staticmethod
    def generate_qr(text: str) -> io.BytesIO:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = io.BytesIO()
        bio.name = 'qrcode.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio

# ==============================================================================
# 🧩 UI COMPONENTS
# ==============================================================================
class UIBuilder:
    """Utility untuk membangun Keyboard dan Pesan"""
    
    @staticmethod
    def get_main_menu_keyboard(user_id):
        kb = [
            [InlineKeyboardButton("📡 Paket Data", callback_data="menu_paket"), InlineKeyboardButton("💵 Pulsa Reguler", callback_data="menu_pulsa")],
            [InlineKeyboardButton("📱 Cek Nomor", callback_data="tool_number"), InlineKeyboardButton("🛠️ Tools Digital", callback_data="menu_tools")],
            [InlineKeyboardButton("📊 Cek Kuota (XL/Axis)", url="https://sidompul.kmsp-store.com/"), InlineKeyboardButton("❓ Bantuan", callback_data="menu_help")],
            [InlineKeyboardButton("🧹 Bersihkan Chat", callback_data="action_clean")],
            [InlineKeyboardButton("🌐 Website Resmi", url="https://pulsanet.kesug.com/beli.html")]
        ]
        return InlineKeyboardMarkup(kb)

    @staticmethod
    def paginate(items: List[InlineKeyboardButton], page: int, prefix: str, cols=1, items_per_page=5):
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        start = page * items_per_page
        end = start + items_per_page
        current_items = items[start:end]
        
        keyboard = []
        # Grid builder
        for i in range(0, len(current_items), cols):
            keyboard.append(current_items[i:i+cols])
            
        # Nav builder
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("◀️", callback_data=f"{prefix}_p{page-1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("▶️", callback_data=f"{prefix}_p{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)
            
        return keyboard

# ==============================================================================
# 🤖 BOT HANDLERS
# ==============================================================================
class BotHandlers:
    
    # --- Start & Menu ---
    @staticmethod
    @rate_limit
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if Config.MAINTENANCE_MODE and str(update.effective_user.id) != Config.ADMIN_ID:
            await update.message.reply_text("🚧 Bot sedang dalam perbaikan. Coba lagi nanti.")
            return

        user = update.effective_user
        hour = datetime.now(ZoneInfo("Asia/Jakarta")).hour
        greeting = "Pagi" if 5 <= hour < 11 else "Siang" if 11 <= hour < 15 else "Sore" if 15 <= hour < 18 else "Malam"
        
        text = (
            f"👋 <b>Selamat {greeting}, {html.escape(user.first_name)}!</b>\n\n"
            f"Selamat datang di <b>Pulsa Net Pro</b>.\n"
            f"Solusi satu pintu untuk kebutuhan digital Anda.\n\n"
            f"🆔 ID Anda: <code>{user.id}</code>\n"
            f"🤖 Status: 🟢 Online"
        )
        
        # Cleanup mechanism: Mark message to delete later
        if update.message:
            context.user_data.setdefault('msgs_to_clean', []).append(update.message.id)
            msg = await update.message.reply_text(text, reply_markup=UIBuilder.get_main_menu_keyboard(user.id), parse_mode=ParseMode.HTML)
            context.user_data['msgs_to_clean'].append(msg.id)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=UIBuilder.get_main_menu_keyboard(user.id), parse_mode=ParseMode.HTML)

    @staticmethod
    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        # --- Navigation Logic ---
        if data == "back_home":
            await BotHandlers.start(update, context)
            
        elif data == "action_clean":
            await BotHandlers.clean_chat(update, context)

        elif data in ["menu_paket", "menu_pulsa"]:
            p_type = "paket" if "paket" in data else "pulsa"
            kb = [
                [InlineKeyboardButton("🔵 XL", callback_data=f"prov_{p_type}_xl"), InlineKeyboardButton("🟣 Axis", callback_data=f"prov_{p_type}_axis")],
                [InlineKeyboardButton("🔴 Tri", callback_data=f"prov_{p_type}_tri"), InlineKeyboardButton("🟡 Indosat", callback_data=f"prov_{p_type}_indosat")],
                [InlineKeyboardButton("🟠 Telkomsel", callback_data=f"prov_{p_type}_telkomsel"), InlineKeyboardButton("⚪ By.U", callback_data=f"prov_{p_type}_by.u")],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_home")]
            ]
            title = "📡 <b>Pilih Provider Data</b>" if p_type == "paket" else "💵 <b>Pilih Provider Pulsa</b>"
            await query.edit_message_text(title, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

        elif data.startswith("prov_"):
            # Format: prov_paket_xl
            _, p_type, provider = data.split("_")
            
            # Special case for XL Paket (Submenu)
            if provider == "xl" and p_type == "paket":
                kb = [
                    [InlineKeyboardButton("🤝 Akrab", callback_data="list_xl_paket_akrab"), InlineKeyboardButton("🥳 Bebas Puas", callback_data="list_xl_paket_bebaspuas")],
                    [InlineKeyboardButton("⭕️ Circle", callback_data="list_xl_paket_circle"), InlineKeyboardButton("🚀 Reguler", callback_data="list_xl_paket_paket")],
                    [InlineKeyboardButton("⬅️ Kembali", callback_data="menu_paket")]
                ]
                await query.edit_message_text("<b>🔵 Pilih Kategori XL:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            else:
                # Direct list for others
                await BotHandlers.show_product_list(update, context, provider, p_type)

        elif data.startswith("list_"):
            # Format: list_xl_paket_akrab OR list_tri_pulsa
            parts = data.split("_")
            provider = parts[1]
            p_type = parts[2]
            subtype = parts[3] if len(parts) > 3 else None
            await BotHandlers.show_product_list(update, context, provider, p_type, subtype)
            
        elif data.startswith("pkg_"):
            # Show Detail
            product = db.get_by_key(data)
            if not product:
                await query.answer("Produk tidak ditemukan!", show_alert=True)
                return
                
            text = (
                f"🏷️ <b>{product['name']}</b>\n"
                f"💰 <b>Harga: Rp {product['price']:,}</b>\n\n"
                f"📝 {html.escape(product['details'])}\n"
                f"⏳ Masa Aktif: {product['validity']}"
            )
            kb = [
                [InlineKeyboardButton("🛒 Beli di Web", url="https://pulsanet.kesug.com/beli.html")],
                [InlineKeyboardButton("⬅️ Kembali", callback_data="back_home")] # Simplified back nav
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

        # --- Tools Handlers ---
        elif data == "menu_tools" or data.startswith("tools_p"):
            page = int(data.split("_p")[1]) if "_p" in data else 0
            tools_map = [
                InlineKeyboardButton("🔳 QR Generator", callback_data="tool_qr"),
                InlineKeyboardButton("💱 Kurs Mata Uang", callback_data="tool_kurs"),
                InlineKeyboardButton("🌍 Whois Lookup", callback_data="tool_whois"),
                InlineKeyboardButton("📍 IP Lookup", callback_data="tool_ip"),
                InlineKeyboardButton("📦 Base64", callback_data="tool_base64"),
                InlineKeyboardButton("🔑 Pass Gen", callback_data="tool_pass"),
                InlineKeyboardButton("🕹️ Mini Game", callback_data="game_menu"),
            ]
            kb = UIBuilder.paginate(tools_map, page, "tools", cols=1)
            kb.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="back_home")])
            await query.edit_message_text("<b>🛠️ Tools Digital</b>\nPilih alat yang ingin digunakan:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            
        elif data.startswith("tool_"):
            tool_type = data.split("_")[1]
            context.user_data['state'] = f'wait_{tool_type}'
            
            prompts = {
                "qr": "Kirim teks/link untuk dijadikan QR Code.",
                "kurs": "Format: `10 USD to IDR`",
                "whois": "Kirim nama domain (ex: google.com)",
                "ip": "Kirim IP Address (ex: 8.8.8.8)",
                "base64": "Kirim teks untuk Encode/Decode.",
                "number": "Kirim Nomor HP (ex: 0812...)",
                "pass": "Membuat password..." # Immediate action
            }
            
            if tool_type == "pass":
                chars = string.ascii_letters + string.digits + "!@#$%^&*"
                pwd = ''.join(random.choice(chars) for _ in range(16))
                await query.edit_message_text(f"🔑 <b>Password:</b> <code>{pwd}</code>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Tools", callback_data="menu_tools")]]))
                del context.user_data['state']
                return

            kb = [[InlineKeyboardButton("❌ Batal", callback_data="menu_tools")]]
            msg = await query.edit_message_text(f"⌨️ <b>Input Mode:</b>\n{prompts.get(tool_type)}", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            context.user_data['prompt_msg_id'] = msg.id

    @staticmethod
    async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE, provider, p_type, subtype=None):
        products = db.filter(category=provider, type_filter=p_type, subtype_filter=subtype)
        
        if not products:
            await update.callback_query.answer("Produk kosong!", show_alert=True)
            return
            
        buttons = []
        for p in products:
            key = db.create_key(p)
            label = f"{p['name'].replace(provider, '').strip()} - Rp{p['price']:,}"
            buttons.append(InlineKeyboardButton(label, callback_data=key))
        
        # Simple pagination for products (manual chunking for simplicity in this example)
        # For full power, use UIBuilder.paginate here too.
        kb = [[b] for b in buttons]
        kb.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="back_home")])
        
        title_str = f"{provider.upper()} {subtype.capitalize() if subtype else p_type.capitalize()}"
        await update.callback_query.edit_message_text(f"📂 <b>{title_str}</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    @staticmethod
    async def clean_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg_ids = context.user_data.get('msgs_to_clean', [])
        chat_id = update.effective_chat.id
        
        await update.callback_query.answer("🧹 Membersihkan...")
        
        # Batch delete
        for mid in msg_ids:
            try:
                await context.bot.delete_message(chat_id, mid)
            except Exception:
                pass # Ignore if already deleted
        
        context.user_data['msgs_to_clean'] = []
        await BotHandlers.start(update, context)

    @staticmethod
    async def input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        state = context.user_data.get('state')
        text = update.message.text
        chat_id = update.effective_chat.id
        
        # Auto clean user input
        context.user_data.setdefault('msgs_to_clean', []).append(update.message.id)
        
        # Remove prompt message if exists
        if 'prompt_msg_id' in context.user_data:
            try:
                await context.bot.delete_message(chat_id, context.user_data['prompt_msg_id'])
            except: pass
        
        if not state:
            return # Ignore random text

        response = "❌ Error."
        
        try:
            if state == 'wait_qr':
                bio = NetworkTools.generate_qr(text)
                msg = await update.message.reply_photo(bio, caption=f"QR untuk: {html.escape(text)}")
                context.user_data['msgs_to_clean'].append(msg.id)
                response = None # Handled
                
            elif state == 'wait_kurs':
                # Regex parse
                m = re.match(r"([\d\.]+)\s*([a-zA-Z]{3})\s*(?:to|TO)?\s*([a-zA-Z]{3})", text)
                if m:
                    amt, base, target = float(m.group(1)), m.group(2).upper(), m.group(3).upper()
                    response = await NetworkTools.get_currency_rate(amt, base, target)
                else:
                    response = "❌ Format salah. Gunakan: `10 USD to IDR`"

            elif state == 'wait_ip':
                response = await NetworkTools.get_ip_info(text.strip())

            elif state == 'wait_whois':
                w = whois.whois(text)
                response = f"🌍 <b>Domain:</b> {w.domain_name}\n📅 Exp: {w.expiration_date}"
            
            elif state == 'wait_base64':
                try:
                    decoded = base64.b64decode(text).decode()
                    response = f"📂 <b>Decoded:</b> `{decoded}`"
                except:
                    encoded = base64.b64encode(text.encode()).decode()
                    response = f"📦 <b>Encoded:</b> `{encoded}`"

            elif state == 'wait_number':
                response = NetworkTools.get_provider_info(text)

        except Exception as e:
            logger.error(f"Input Error: {e}")
            response = f"⚠️ Terjadi kesalahan: {str(e)}"

        if response:
            kb = [[InlineKeyboardButton("🔙 Kembali ke Menu Tools", callback_data="menu_tools")]]
            msg = await update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            context.user_data['msgs_to_clean'].append(msg.id)
            
        # Reset state
        del context.user_data['state']

    # --- Admin Handlers ---
    @staticmethod
    @admin_only
    async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Command: /broadcast pesan"""
        msg = " ".join(context.args)
        if not msg:
            await update.message.reply_text("Gunakan: /broadcast [pesan]")
            return
            
        # Note: Di production, user_ids harus diambil dari database real.
        # Disini kita hanya simulasi log.
        await update.message.reply_text(f"📢 Mengirim broadcast: '{msg}' (Fitur ini perlu database user untuk bekerja penuh)")

    @staticmethod
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error("🔥 Exception:", exc_info=context.error)
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)[-2000:]
        
        if Config.ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=Config.ADMIN_ID,
                    text=f"🚨 <b>BOT ERROR</b>\n<pre>{html.escape(tb_string)}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except: pass

# ==============================================================================
# 🚀 MAIN EXECUTION
# ==============================================================================
def main():
    # Initialize Application
    app = Application.builder().token(Config.TOKEN).build()

    # Add Handlers
    app.add_handler(CommandHandler("start", BotHandlers.start))
    app.add_handler(CommandHandler("broadcast", BotHandlers.broadcast))
    
    # Main Callback Handler (All buttons go here)
    app.add_handler(CallbackQueryHandler(BotHandlers.button_handler))
    
    # Text Input Handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, BotHandlers.input_handler))
    
    # Error Handler
    app.add_error_handler(BotHandlers.error_handler)

    print("🚀 Bot PulsaNet Pro is Running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
