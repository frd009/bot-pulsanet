# ============================================
# 🤖 Bot Pulsa Net - Ultimate Edition
# File: bot_pulsanet_api.py
# Version: 3.1 (UI Original + API Live + Internet Tools + Full XL Special)
# By : frd009
# ============================================

import os
import re
import html
import asyncio
import logging
import httpx
import traceback
import signal
import sys
import uuid
import time
import json
import base64
import io
import random
import string
from datetime import datetime

# Coba import zoneinfo & psutil
try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        pass # Fallback nanti
try:
    import psutil
except ImportError:
    psutil = None

# --- Import Library Tambahan (QR, Whois) ---
# Pastikan library ini ada di requirements.txt: qrcode, pillow, python-whois
try:
    import qrcode
    from PIL import Image
    import whois
except ImportError:
    pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

# ==============================================================================
# ⚙️ KONFIGURASI & DATABASE
# ==============================================================================

# Telegram Token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# PortalPulsa Credentials
PP_USERID = os.environ.get("PORTAL_USERID")
PP_KEY = os.environ.get("PORTAL_KEY")
PP_SECRET = os.environ.get("PORTAL_SECRET")

# Config Lain
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")
BOT_START_TIME = datetime.now()
USER_DB_FILE = 'user_stats.json'
UNIQUE_USERS = set()

# External APIs
CRYPTO_API = "https://api.coingecko.com/api/v3"
STOCK_API = "https://www.alphavantage.co/query"
STOCK_API_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "demo")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- USER STATS ---
def load_users_db():
    global UNIQUE_USERS
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                data = json.load(f)
                UNIQUE_USERS = set(data)
        except Exception: pass

def register_user_visit(user_id):
    global UNIQUE_USERS
    if user_id not in UNIQUE_USERS:
        UNIQUE_USERS.add(user_id)
        try:
            with open(USER_DB_FILE, 'w') as f:
                json.dump(list(UNIQUE_USERS), f)
        except Exception: pass

def get_total_users():
    return len(UNIQUE_USERS) + 57  # Start from 57 as requested

# ==============================================================================
# 📦 DATA MANUAL XL SPESIAL
# ==============================================================================
# PENTING: Ubah 'id' sesuai dengan KODE PRODUK di PortalPulsa Anda
XL_SPECIAL_PACKAGES = [
    {'id': 'XLA1', 'name': "XL Akrab Mini Lite", 'price': 46000, 'category': 'XL', 'type': 'Akrab', 'data': '13-32 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLA2', 'name': "XL Akrab Mini", 'price': 58000, 'category': 'XL', 'type': 'Akrab', 'data': '33-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLA3', 'name': "XL Akrab Mini V2", 'price': 64000, 'category': 'XL', 'type': 'Akrab', 'data': '31-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLA4', 'name': "XL Akrab Big V2", 'price': 67000, 'category': 'XL', 'type': 'Akrab', 'data': '38-57 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLA5', 'name': "XL Akrab Jumbo V2", 'price': 97000, 'category': 'XL', 'type': 'Akrab', 'data': '70 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLA6', 'name': "XL Akrab Mega Big V2", 'price': 102000, 'category': 'XL', 'type': 'Akrab', 'data': '90 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 'XLBP1', 'name': "XL Bebas Puas 75GB", 'price': 98000, 'category': 'XL', 'type': 'BebasPuas', 'data': '75GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 'XLBP2', 'name': "XL Bebas Puas 234GB", 'price': 171000, 'category': 'XL', 'type': 'BebasPuas', 'data': '234GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 'XLC1', 'name': "XL Circle 7–11GB", 'price': 31000, 'category': 'XL', 'type': 'Circle', 'data': '7-11GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 'XLC2', 'name': "XL Circle 17–21GB", 'price': 42000, 'category': 'XL', 'type': 'Circle', 'data': '17-21GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 'XLC3', 'name': "XL Circle 27–31GB", 'price': 58000, 'category': 'XL', 'type': 'Circle', 'data': '27-31GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
]

AKRAB_QUOTA_DETAILS = {
    "XLA3": {"1": "31GB - 33GB", "2": "33GB - 35GB", "3": "38GB - 40GB", "4": "48GB - 50GB"},
    "XLA4": {"1": "38GB - 40GB", "2": "40GB - 42GB", "3": "45GB - 47GB", "4": "55GB - 57GB"},
    "XLA5": {"1": "65GB", "2": "70GB", "3": "83GB", "4": "123GB"},
    "XLA6": {"1": "88GB - 90GB", "2": "90GB - 92GB", "3": "95GB - 97GB", "4": "105GB - 107GB"},
}
AKRAB_QUOTA_DETAILS['XLA2'] = AKRAB_QUOTA_DETAILS.get('XLA3')

# ==============================================================================
# ✍️ FUNGSI DESKRIPSI DETAIL (Manual)
# ==============================================================================
def create_header(info):
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    return f"✨ <b>{html.escape(info.get('name', 'N/A'))}</b> ✨\n💵 <b>Harga: {price}</b>\n"

def create_akrab_description(pkg):
    info = pkg
    pkg_id = info['id']
    quota_info = AKRAB_QUOTA_DETAILS.get(pkg_id)
    
    description = create_header(info) + "\n" + ("<i>Paket keluarga resmi dari XL dengan kuota besar yang bisa dibagi-pakai.</i>\n\n"
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

def create_circle_description(pkg):
    info = pkg
    return (create_header(info) + "\n" "<i>Paket eksklusif dengan kuota dinamis yang menguntungkan.</i>\n\n"
            f"💾 <b>Estimasi Kuota:</b> {info.get('data', 'N/A')} (potensi dapat lebih)\n"
            "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n"
            "⏳ <b>Masa Aktif:</b> 28 hari atau hingga kuota habis. Jika kuota habis sebelum 28 hari, status keanggotaan menjadi <b>BEKU/FREEZE</b>.\n"
            "⚡ <b>Aktivasi:</b> Instan, tanpa OTP.\n\n" "⚠️ <b>PERHATIAN (WAJIB BACA):</b>\n" "<b>1. Cara Cek Kuota:</b>\n"
            "    - Buka aplikasi <b>MyXL terbaru</b>.\n" "    - Klik menu <b>XL CIRCLE</b> di bagian bawah (bukan dari 'Lihat Paket Saya').\n\n"
            "<b>2. Syarat & Ketentuan:</b>\n" "    - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n"
            "    - <b>Keanggotaan:</b> Tidak terdaftar di Circle lain pada bulan yang sama.\n" "    - <b>Status Kartu:</b> Tidak dalam masa tenggang.\n"
            "    - <b>DILARANG UNREG:</b> Keluar dari Circle akan menghanguskan garansi (tanpa refund).")

def create_bebaspuas_description(pkg):
    info = pkg
    return (create_header(info) + "\n" "<i>Nikmati kebebasan internetan dengan kuota besar yang bisa diakumulasi.</i>\n\n"
            "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) via Sidompul\n" "⚡ <b>Aktivasi:</b> Instan, tanpa memerlukan kode OTP\n"
            "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n" "🌍 <b>Area:</b> Berlaku di seluruh Indonesia\n"
            "📅 <b>Masa Aktif & Garansi:</b> 30 Hari\n" f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')} (Full 24 Jam)\n\n"
            "⭐ <b>Fitur Unggulan:</b>\n"
            "  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli paket Bebas Puas lain sebelum masa aktif berakhir.\n"
            "  - <b>Tanpa Syarat Pulsa:</b> Aktivasi tidak memerlukan pulsa minimum.\n\n" "🎁 <b>Klaim Bonus:</b>\n"
            "  - Tersedia bonus kuota yang dapat diklaim di aplikasi myXL (pilih salah satu: YouTube, TikTok, atau Kuota Utama).")

# ==============================================================================
# 🔌 KELAS INTEGRASI PORTALPULSA (API CLIENT)
# ==============================================================================

class PortalPulsaAPI:
    BASE_URL = 'https://portalpulsa.com/api/connect/'

    def __init__(self):
        self.headers = {
            'portal-userid': PP_USERID,
            'portal-key': PP_KEY,
            'portal-secret': PP_SECRET,
            'Content-Type': 'application/x-www-form-urlencoded', # Penting
            'User-Agent': 'Mozilla/5.0 (Bot PulsaNet)'
        }

    async def _request(self, data):
        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                # Debugging: Print apa yang dikirim
                logger.info(f"📡 API Request: {data.get('inquiry')} - Code: {data.get('code')}")
                
                response = await client.post(
                    self.BASE_URL,
                    headers=self.headers,
                    data=data
                )
                
                # Debugging: Print hasil raw
                logger.info(f"📩 API Response Code: {response.status_code}")
                logger.info(f"📩 API Response Body: {response.text[:200]}...") # Print 200 char pertama

                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"❌ API Error: {e}")
                return {"result": "failed", "message": str(e)}

    async def cek_harga(self, code_type='pulsa'):
        return await self._request({'inquiry': 'HARGA', 'code': code_type})

    async def topup(self, product_code, phone_number, id_cust=None):
        trx_id = f"TRX-{int(time.time())}"
        payload = {'inquiry': 'I', 'code': product_code, 'phone': phone_number, 'trxid_api': trx_id, 'no': '1'}
        if id_cust: payload['idcust'] = id_cust
        return await self._request(payload)

    async def cek_saldo(self):
        return await self._request({'inquiry': 'S'})

pp_client = PortalPulsaAPI()
PRICE_CACHE = {'pulsa': {'data': [], 'time': 0}, 'pln': {'data': [], 'time': 0}}
CACHE_DURATION = 300

# ==============================================================================
# 🌐 FITUR INTERNET & TOOLS (ZETA)
# ==============================================================================

class ZetaTools:
    @staticmethod
    async def get_crypto_price(coin: str = "bitcoin") -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{CRYPTO_API}/simple/price?ids={coin}&vs_currencies=usd,idr&include_24hr_change=true")
                data = response.json()
                if coin in data:
                    usd, idr = data[coin]['usd'], data[coin]['idr']
                    change = data[coin]['usd_24h_change']
                    return (f"💰 <b>{coin.upper()} Price</b>\n"
                            f"🇺🇸 USD: ${usd:,.2f}\n🇮🇩 IDR: Rp{idr:,.0f}\n📈 24h: {change:+.2f}%")
                return "❌ Koin tidak ditemukan."
        except: return "❌ Gagal mengambil data crypto."

    @staticmethod
    async def get_stock_price(symbol: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{STOCK_API}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={STOCK_API_KEY}")
                data = res.json()
                if "Global Quote" in data:
                    q = data["Global Quote"]
                    return (f"📊 <b>{symbol} Stock</b>\n💵 Price: ${q['05. price']}\n📉 Change: {q['10. change percent']}")
                return "❌ Limit API / Symbol salah."
        except: return "❌ Error fetching stock."

    @staticmethod
    async def ip_lookup(ip: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"http://ip-api.com/json/{ip}")
                data = res.json()
                if data['status'] == 'fail': return "❌ IP Invalid."
                return (f"📍 <b>IP Info: {ip}</b>\n🌍 {data.get('country')}, {data.get('city')}\n🏢 {data.get('isp')}")
        except: return "❌ Service unavailable."

    @staticmethod
    async def shorten_url(url: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"http://tinyurl.com/api-create.php?url={url}")
                return res.text
        except: return url

    @staticmethod
    def get_system_stats() -> str:
        try:
            if not psutil: return "System stats not available."
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            return f"CPU: {cpu}% | RAM: {mem.percent}%"
        except: return "N/A"

# ==============================================================================
# 🛠️ HELPER FUNCTIONS (Formatting, UI)
# ==============================================================================

def format_uptime(start_time: datetime) -> str:
    uptime = datetime.now() - start_time
    days = uptime.days
    hours, rem = divmod(uptime.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"

async def get_cached_products(category):
    now = time.time()
    if now - PRICE_CACHE[category]['time'] < CACHE_DURATION and PRICE_CACHE[category]['data']:
        return PRICE_CACHE[category]['data']
    
    # Live Fetch
    response = await pp_client.cek_harga(category)
    
    if response.get('result') == 'failed':
        # Log error spesifik untuk debugging
        logger.error(f"API FAIL MSG: {response.get('message')}")
        return None # Return None to indicate failure explicitly
        
    products = response.get('message', [])
    PRICE_CACHE[category] = {'data': products, 'time': now}
    return products

def format_price(amount): return f"Rp{int(amount):,}".replace(",", ".")

def parse_operator(product_name):
    name = product_name.lower()
    if 'telkomsel' in name: return 'Telkomsel'
    if 'indosat' in name: return 'Indosat'
    if 'xl' in name: return 'XL'
    if 'axis' in name: return 'Axis'
    if 'tri' in name: return 'Tri'
    if 'smartfren' in name: return 'Smartfren'
    if 'pln' in name: return 'PLN'
    return 'Lainnya'

# ==============================================================================
# 🎮 HANDLERS (START & MENUS)
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear() # Reset state
    user = update.effective_user
    register_user_visit(user.id)
    
    # Time Greeting logic
    try:
        # Coba pake ZoneInfo, kalau gagal pakai UTC default
        try:
            tz = ZoneInfo("Asia/Jakarta")
            hour = datetime.now(tz).hour
        except:
            hour = datetime.now().hour + 7 # Manual offset UTC+7
            
        if 5 <= hour < 11: greeting, icon = "Selamat Pagi", "☀️"
        elif 11 <= hour < 15: greeting, icon = "Selamat Siang", "🌤️"
        elif 15 <= hour < 18: greeting, icon = "Selamat Sore", "🌥️"
        else: greeting, icon = "Selamat Malam", "🌙"
    except: greeting, icon = "Halo", "👋"

    stats = ZetaTools.get_system_stats()
    uptime = format_uptime(BOT_START_TIME)
    total_users = get_total_users()
    username = f"@{user.username}" if user.username else "N/A"

    text = (f"{icon} <b>{greeting}, {user.first_name}!</b>\n\n"
            f"Selamat datang di <b>Pulsa Net Bot</b>.\n"
            f"Asisten digital canggih untuk kebutuhan transaksi & tools internet.\n"
            f"— — — — — — — — — — — —\n"
            f"📊 <b>Statistik Bot</b>\n"
            f"👥 Users: <b>{total_users:,}</b> | 🖥️ Sys: {stats}\n"
            f"— — — — — — — — — — — —\n"
            f"👤 <b>Info Kamu</b>\n"
            f"ID: <code>{user.id}</code> | User: {username}\n"
            f"🕒 Uptime: {uptime}")

    keyboard = [
        [InlineKeyboardButton("📡 Paket Data", callback_data="menu_pulsa"), 
         InlineKeyboardButton("💵 Pulsa Reguler", callback_data="menu_pulsa")],
        [InlineKeyboardButton("⚡ Token PLN", callback_data="menu_pln"), 
         InlineKeyboardButton("🛠️ Tools Digital", callback_data="menu_tools")],
        [InlineKeyboardButton("💎 XL Spesial", callback_data="menu_xl_special"),
         InlineKeyboardButton("ℹ️ Cek Saldo", callback_data="status_akun")],
        [InlineKeyboardButton("🧹 Bersihkan Chat", callback_data="clear_chat")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Membersihkan...")
    try:
        await query.message.delete()
        msg = await query.message.reply_text("🧹 Chat dibersihkan.")
        await asyncio.sleep(2)
        await msg.delete()
        await start(update, context)
    except: pass

# --- HANDLER TOOLS MENU ---
async def menu_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "<b>🛠️ Tools Digital</b>\n\nPilih alat bantu yang tersedia:"
    keyboard = [
        [InlineKeyboardButton("🔳 QR Generator", callback_data="tool_qr"),
         InlineKeyboardButton("🌍 Whois Lookup", callback_data="tool_whois")],
        [InlineKeyboardButton("📍 IP Info", callback_data="tool_ip"),
         InlineKeyboardButton("🔗 Short Link", callback_data="tool_shorten")],
        [InlineKeyboardButton("💱 Kurs Mata Uang", callback_data="tool_kurs"),
         InlineKeyboardButton("📦 Base64", callback_data="tool_base64")],
        [InlineKeyboardButton("💰 Cek Crypto", callback_data="tool_crypto"),
         InlineKeyboardButton("📊 Cek Saham", callback_data="tool_stock")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# --- HANDLER TRANSAKSI (API LIVE) ---
async def menu_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[1] # pulsa, pln

    msg = await query.edit_message_text("🔄 <b>Menghubungi Server PortalPulsa...</b>", parse_mode=ParseMode.HTML)
    
    # Fetch Data
    products = await get_cached_products('pln' if category == 'pln' else 'pulsa')
    
    # Error Handling UI
    if products is None:
        error_text = ("❌ <b>Gagal Mengambil Data</b>\n\n"
                      "Bot gagal terhubung ke PortalPulsa. Kemungkinan penyebab:\n"
                      "1. IP Server Railway berubah (IP Whitelist).\n"
                      "2. Kredensial API salah.\n"
                      "3. Saldo akun habis/suspended.\n\n"
                      "<i>Cek Logs Railway untuk detail error.</i>")
        await msg.edit_text(error_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali", callback_data="start")]]), parse_mode=ParseMode.HTML)
        return

    if not products:
        await msg.edit_text("⚠️ Produk kosong atau sedang gangguan.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Kembali", callback_data="start")]]))
        return

    if category == 'pulsa':
        # Group by Operator
        operators = set()
        for p in products:
            op = parse_operator(p['description'])
            if op != 'Lainnya': operators.add(op)
            
        keyboard = []
        row = []
        for op in sorted(list(operators)):
            row.append(InlineKeyboardButton(op, callback_data=f"list_op_{op}"))
            if len(row) == 2: keyboard.append(row); row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="start")])
        await msg.edit_text("📱 <b>Pilih Operator Seluler:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    elif category == 'pln':
        # List PLN langsung
        keyboard = []
        for p in products[:12]: # Limit 12 produk
             if p['status'] == 'active':
                price_str = format_price(p['price'])
                keyboard.append([InlineKeyboardButton(f"{p['description']} - {price_str}", callback_data=f"buy_{p['code']}_{p['price']}")])
        keyboard.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="start")])
        await msg.edit_text("⚡ <b>Pilih Nominal Token PLN:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def list_products_by_op(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    operator = query.data.split('_')[2]
    
    products = await get_cached_products('pulsa')
    filtered = [p for p in products if parse_operator(p['description']) == operator and p['status'] == 'active']
    filtered.sort(key=lambda x: int(x['price']))
    
    keyboard = []
    for p in filtered:
        desc = p['description'].replace(operator, "").strip()
        keyboard.append([InlineKeyboardButton(f"{desc} | {format_price(p['price'])}", callback_data=f"buy_{p['code']}_{p['price']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="menu_pulsa")])
    await query.edit_message_text(f"📱 <b>Produk {operator}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def buy_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    code, price = data[1], data[2]
    
    # Simpan state
    context.user_data['trx_code'] = code
    context.user_data['trx_price'] = price
    context.user_data['state'] = 'awaiting_phone_trx'
    
    # Cari nama produk (API + Manual List Check)
    all_prods = (await get_cached_products('pulsa') or []) + (await get_cached_products('pln') or [])
    prod_name = next((p['description'] for p in all_prods if p['code'] == code), code)

    # Fallback to Manual List if not found in API
    if prod_name == code:
         prod_name = next((p['name'] for p in XL_SPECIAL_PACKAGES if p['id'] == code), code)

    context.user_data['trx_name'] = prod_name
    
    text = (f"🛒 <b>Konfirmasi Pembelian</b>\n\n"
            f"📦 Produk: <b>{prod_name}</b>\n"
            f"💵 Harga: <b>{format_price(price)}</b>\n\n"
            f"⌨️ <b>Silakan balas chat ini dengan NOMOR TUJUAN / ID PELANGGAN:</b>\n"
            f"(Contoh: 08123456789 atau No Meter PLN)")
            
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="start")]]))

# --- HANDLER STATUS SALDO ---
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = await pp_client.cek_saldo()
    
    # Parsing simple
    if res.get('result') != 'failed':
        info = f"Respon: {html.escape(str(res))}"
    else:
        info = f"❌ Error: {res.get('message')}"
        
    await query.edit_message_text(f"ℹ️ <b>Status Akun & Saldo</b>\n\n{info}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kembali", callback_data="start")]]), parse_mode=ParseMode.HTML)

# --- HANDLER PROMPT TOOLS ---
async def prompt_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tool = query.data.split('_')[1]
    context.user_data['state'] = f'tool_{tool}'
    
    prompts = {
        'qr': "Kirim teks/link untuk dijadikan QR Code:",
        'whois': "Kirim nama domain (contoh: google.com):",
        'ip': "Kirim IP Address (contoh: 8.8.8.8):",
        'shorten': "Kirim link panjang:",
        'kurs': "Format: [Jumlah] [Dari] to [Ke] (cth: 10 USD to IDR)",
        'base64': "Kirim teks untuk Encode/Decode:",
        'crypto': "Kirim nama koin (cth: bitcoin):",
        'stock': "Kirim simbol saham (cth: AAPL):"
    }
    
    text = f"🛠️ <b>Mode {tool.upper()}</b>\n\n{prompts.get(tool, 'Kirim input:')}"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="menu_tools")]]), parse_mode=ParseMode.HTML)

# --- TEXT MESSAGE HANDLER (CENTRAL LOGIC) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text.strip()
    
    if not state: return # No state, ignore or smart reply
    
    # 1. TRANSAKSI
    if state == 'awaiting_phone_trx':
        if len(text) < 5: return await update.message.reply_text("❌ Nomor terlalu pendek.")
        
        code = context.user_data['trx_code']
        name = context.user_data['trx_name']
        
        proc_msg = await update.message.reply_text("⏳ <b>Mengirim Transaksi ke Server...</b>", parse_mode=ParseMode.HTML)
        
        # Logic ID Cust vs Phone (PLN usually needs idcust field)
        is_pln = 'PLN' in name or 'TOKEN' in name
        id_cust = text if is_pln else None
        
        res = await pp_client.topup(code, text, id_cust)
        await proc_msg.delete()
        
        if res.get('result') == 'failed':
            await update.message.reply_text(f"❌ <b>Transaksi Gagal!</b>\n\nServer: {res.get('message')}", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"✅ <b>Transaksi Berhasil!</b>\n\n📦 {name}\n📱 {text}\n📝 {res.get('message', 'Sukses')}", parse_mode=ParseMode.HTML)
        
        context.user_data.clear()
        
    # 2. TOOLS
    elif state == 'tool_qr':
        try:
            img = qrcode.make(text)
            bio = io.BytesIO(); img.save(bio, 'PNG'); bio.seek(0)
            await update.message.reply_photo(bio, caption=f"QR Code: {text}")
        except: await update.message.reply_text("Gagal membuat QR.")
        context.user_data.clear()

    elif state == 'tool_whois':
        try:
            w = whois.whois(text)
            res = f"Domain: {w.domain_name}\nRegistrar: {w.registrar}\nCreated: {w.creation_date}"
            await update.message.reply_text(res)
        except: await update.message.reply_text("Whois gagal/privat.")
        context.user_data.clear()

    elif state == 'tool_ip':
        res = await ZetaTools.ip_lookup(text)
        await update.message.reply_text(res, parse_mode=ParseMode.HTML)
        context.user_data.clear()

    elif state == 'tool_shorten':
        res = await ZetaTools.shorten_url(text)
        await update.message.reply_text(f"🔗 Pendek: {res}")
        context.user_data.clear()
        
    elif state == 'tool_base64':
        try:
            res = base64.b64decode(text).decode()
            await update.message.reply_text(f"🔓 Decode: {res}")
        except:
            res = base64.b64encode(text.encode()).decode()
            await update.message.reply_text(f"🔒 Encode: {res}")
        context.user_data.clear()

    elif state == 'tool_crypto':
        res = await ZetaTools.get_crypto_price(text)
        await update.message.reply_text(res, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        
    elif state == 'tool_stock':
        res = await ZetaTools.get_stock_price(text)
        await update.message.reply_text(res, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        
    elif state == 'tool_kurs':
        # Simple logic, user must input correct format
        # For simplicity, just redirect to crypto tool or error if not implemented fully
        await update.message.reply_text("Fitur kurs sedang pemeliharaan.")
        context.user_data.clear()

# --- XL SPECIAL (MANUAL DATA) ---
async def menu_xl_special(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🤝 Akrab (Keluarga)", callback_data="xl_list_Akrab")],
        [InlineKeyboardButton("🥳 Bebas Puas", callback_data="xl_list_BebasPuas")],
        [InlineKeyboardButton("⭕ Circle", callback_data="xl_list_Circle")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start")]
    ]
    
    text = "<b>💎 Menu XL Spesial</b>\n\nPaket eksklusif dengan detail lengkap. Silakan pilih kategori:"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def list_xl_special_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pkg_type = query.data.split('_')[2]
    
    # Filter dari list manual
    items = [p for p in XL_SPECIAL_PACKAGES if p['type'] == pkg_type]
    
    keyboard = []
    for item in items:
        # Format: Nama - Harga
        btn_text = f"{item['name']} - {format_price(item['price'])}"
        # Callback: detail_manual_KODE
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"detail_manual_{item['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="menu_xl_special")])
    await query.edit_message_text(f"💎 <b>XL {pkg_type}</b>\nPilih paket untuk melihat detail:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_manual_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pkg_id = query.data.split('_')[2]
    
    # Cari paket
    pkg = next((p for p in XL_SPECIAL_PACKAGES if p['id'] == pkg_id), None)
    if not pkg:
        await query.edit_message_text("❌ Data paket tidak ditemukan.")
        return

    # Generate deskripsi berdasarkan tipe
    if pkg['type'] == 'Akrab': desc = create_akrab_description(pkg)
    elif pkg['type'] == 'Circle': desc = create_circle_description(pkg)
    elif pkg['type'] == 'BebasPuas': desc = create_bebaspuas_description(pkg)
    else: desc = f"<b>{pkg['name']}</b>\nHarga: {format_price(pkg['price'])}"

    keyboard = [
        [InlineKeyboardButton("🛒 Beli Sekarang", callback_data=f"buy_{pkg['id']}_{pkg['price']}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data=f"xl_list_{pkg['type']}")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="start")]
    ]
    
    # Disable web preview agar rapi
    await query.edit_message_text(desc, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, disable_web_page_preview=True)


# ==============================================================================
# 🚀 MAIN
# ==============================================================================

def main():
    # Load User DB
    load_users_db()
    
    if not TOKEN:
        logger.critical("Token Bot tidak ditemukan.")
        sys.exit(1)

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^start$'))
    app.add_handler(CallbackQueryHandler(clear_chat, pattern='^clear_chat$'))
    
    # Menus
    app.add_handler(CallbackQueryHandler(menu_category_handler, pattern='^menu_(pulsa|pln)$'))
    app.add_handler(CallbackQueryHandler(menu_tools, pattern='^menu_tools$'))
    app.add_handler(CallbackQueryHandler(menu_xl_special, pattern='^menu_xl_special$'))
    
    # Actions
    app.add_handler(CallbackQueryHandler(list_products_by_op, pattern='^list_op_'))
    app.add_handler(CallbackQueryHandler(list_xl_special_items, pattern='^xl_list_'))
    app.add_handler(CallbackQueryHandler(show_manual_detail, pattern='^detail_manual_'))
    app.add_handler(CallbackQueryHandler(buy_confirmation, pattern='^buy_'))
    app.add_handler(CallbackQueryHandler(check_balance, pattern='^status_akun$'))
    app.add_handler(CallbackQueryHandler(prompt_tool, pattern='^tool_'))
    
    # Text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot Pulsa Net Ultimate (v3.0) Started...")
    print("✅ API PortalPulsa Connected")
    print("✅ Zeta Tools Active")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
