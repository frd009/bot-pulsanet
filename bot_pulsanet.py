# ============================================
# 🤖 Bot Pulsa Net - PortalPulsa Integrated
# File: bot_pulsanet.py
# Version: 2.1
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
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Telegram Imports ---
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

# ==============================================================================
# ⚙️ KONFIGURASI API & KREDENSIAL
# ==============================================================================

# Telegram Token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# PortalPulsa Credentials (Wajib Diisi di Environment Variable)
PP_USERID = os.environ.get("PORTAL_USERID")
PP_KEY = os.environ.get("PORTAL_KEY")
PP_SECRET = os.environ.get("PORTAL_SECRET")

# Admin ID (Untuk notifikasi error/transaksi)
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")

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

# ==============================================================================
# 📦 DATA MANUAL XL SPESIAL (Sesuai Permintaan)
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
# Mapping alias
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
        if not all([PP_USERID, PP_KEY, PP_SECRET]):
            logger.critical("❌ KREDENSIAL PORTALPULSA BELUM DISETTING DI ENVIRONMENT VARIABLES!")
        
        self.headers = {
            'portal-userid': PP_USERID,
            'portal-key': PP_KEY,
            'portal-secret': PP_SECRET,
        }

    async def _request(self, data):
        """Internal helper for making requests"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # PortalPulsa uses POST for everything
                response = await client.post(
                    self.BASE_URL,
                    headers=self.headers,
                    data=data
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"API Connection Error: {e}")
                return {"result": "failed", "message": "Connection Error"}
            except Exception as e:
                logger.error(f"API Error: {e}")
                return {"result": "failed", "message": str(e)}

    async def cek_harga(self, code_type='pulsa'):
        payload = {'inquiry': 'HARGA', 'code': code_type}
        return await self._request(payload)

    async def topup(self, product_code, phone_number, id_cust=None):
        trx_id = f"TRX-{int(time.time())}-{str(uuid.uuid4())[:4]}"
        payload = {
            'inquiry': 'I',
            'code': product_code,
            'phone': phone_number,
            'trxid_api': trx_id,
            'no': '1'
        }
        if id_cust: payload['idcust'] = id_cust
        logger.info(f"Mengirim request Topup: {payload}")
        return await self._request(payload)

    async def cek_saldo(self):
        payload = {'inquiry': 'S'} 
        return await self._request(payload)

# Inisialisasi API
pp_client = PortalPulsaAPI()

# Cache sederhana
PRICE_CACHE = {'pulsa': {'data': [], 'time': 0}, 'pln': {'data': [], 'time': 0}}
CACHE_DURATION = 300

# ==============================================================================
# 🌐 ZETA INTERNET FEATURES
# ==============================================================================

class ZetaInternetTools:
    @staticmethod
    async def get_crypto_price(coin: str = "bitcoin") -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{CRYPTO_API}/simple/price?ids={coin}&vs_currencies=usd,idr&include_24hr_change=true")
                data = response.json()
                if coin in data:
                    usd, idr = data[coin]['usd'], data[coin]['idr']
                    return (f"💰 <b>{coin.upper()} Price</b>\n🇺🇸 USD: ${usd:,.2f}\n🇮🇩 IDR: Rp{idr:,.0f}")
                return "❌ Koin tidak ditemukan."
        except Exception as e: return f"❌ Error: {e}"

    @staticmethod
    async def get_stock_price(symbol: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{STOCK_API}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={STOCK_API_KEY}")
                data = response.json()
                if "Global Quote" in data:
                    q = data["Global Quote"]
                    return (f"📊 <b>{symbol} Stock</b>\n💵 Price: ${q['05. price']}\n📉 Change: {q['10. change percent']}")
                return "❌ Limit API / Tidak ditemukan."
        except Exception: return "❌ Error fetching stock."

    @staticmethod
    async def ip_lookup(ip_address: str) -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://ip-api.com/json/{ip_address}")
                data = response.json()
                if data['status'] == 'fail': return "❌ IP Invalid."
                return (f"📍 <b>IP Info: {ip_address}</b>\n🌍 Negara: {data.get('country')}\n🏢 ISP: {data.get('isp')}")
        except Exception: return "❌ Service unavailable."

# ==============================================================================
# 🛠️ HELPER FUNCTIONS
# ==============================================================================

async def get_cached_products(category):
    now = time.time()
    if now - PRICE_CACHE[category]['time'] < CACHE_DURATION and PRICE_CACHE[category]['data']:
        return PRICE_CACHE[category]['data']
    response = await pp_client.cek_harga(category)
    products = response.get('message', []) if response.get('result') != 'failed' else []
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
    if 'pln' in name or 'token' in name: return 'PLN'
    return 'Lainnya'

# ==============================================================================
# 🎮 HANDLERS
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"👋 <b>Halo {user.first_name}!</b>\n\n"
            f"Selamat datang di <b>Bot Pulsa Net</b>.\n"
            f"Tersedia paket reguler (otomatis) dan paket spesial XL.\n\n"
            f"Silakan pilih menu:")
    
    keyboard = [
        [InlineKeyboardButton("💎 XL SPESIAL", callback_data="menu_xl_special")],
        [InlineKeyboardButton("📱 Isi Pulsa & Data", callback_data="menu_pulsa"),
         InlineKeyboardButton("⚡ Token PLN", callback_data="menu_pln")],
        [InlineKeyboardButton("💰 Crypto", callback_data="menu_crypto"),
         InlineKeyboardButton("📊 Saham", callback_data="menu_stock"),
         InlineKeyboardButton("📍 Cek IP", callback_data="menu_ip")],
        [InlineKeyboardButton("ℹ️ Status Akun", callback_data="status_akun")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# --- HANDLER KHUSUS XL SPESIAL ---
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

# --- HANDLER UMUM (API) ---
async def menu_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[1]
    
    if category == 'crypto': return await query.edit_message_text("Kirim kode koin (contoh: /crypto bitcoin)", parse_mode=ParseMode.HTML)
    if category == 'stock': return await query.edit_message_text("Kirim kode saham (contoh: /stock AAPL)", parse_mode=ParseMode.HTML)
    if category == 'ip': return await query.edit_message_text("Kirim IP Address (contoh: /ip 8.8.8.8)", parse_mode=ParseMode.HTML)

    msg = await query.edit_message_text("🔄 Mengambil data server...", parse_mode=ParseMode.HTML)
    products = await get_cached_products('pln' if category == 'pln' else 'pulsa')
    
    if not products:
        return await msg.edit_text("❌ Gagal mengambil data.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kembali", callback_data="start")]]))

    if category == 'pulsa':
        operators = set(parse_operator(p['description']) for p in products if parse_operator(p['description']) != 'Lainnya')
        keyboard = []
        row = []
        for op in sorted(list(operators)):
            row.append(InlineKeyboardButton(op, callback_data=f"list_op_{op}"))
            if len(row) == 2: keyboard.append(row); row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="start")])
        await msg.edit_text("📱 <b>Pilih Operator:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
    elif category == 'pln':
        keyboard = []
        for p in products[:10]: 
             if p['status'] == 'active':
                btn_text = f"{p['description']} - {format_price(p['price'])}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{p['code']}_{p['price']}")])
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
    _, code, price = query.data.split('_')
    
    context.user_data['trx_code'] = code
    context.user_data['trx_price'] = price
    context.user_data['state'] = 'awaiting_phone'
    
    # Cek nama produk (bisa dari API atau Manual)
    all_api_prods = (await get_cached_products('pulsa')) + (await get_cached_products('pln'))
    prod_name = next((p['description'] for p in all_api_prods if p['code'] == code), None)
    
    # Jika tidak ada di API, cek di manual list
    if not prod_name:
        prod_name = next((p['name'] for p in XL_SPECIAL_PACKAGES if p['id'] == code), code)

    context.user_data['trx_name'] = prod_name
    text = (f"🛒 <b>Konfirmasi Pembelian</b>\n\n📦 Produk: <b>{prod_name}</b>\n💵 Harga: <b>{format_price(price)}</b>\n\n"
            f"⌨️ <b>Silakan ketik NOMOR HP tujuan:</b>")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="start")]]))

async def process_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    msg_text = update.message.text.strip()
    
    # Commands Zeta
    if msg_text.startswith('/crypto '): return await update.message.reply_text(await ZetaInternetTools.get_crypto_price(msg_text.split(' ')[1]), parse_mode=ParseMode.HTML)
    if msg_text.startswith('/stock '): return await update.message.reply_text(await ZetaInternetTools.get_stock_price(msg_text.split(' ')[1]), parse_mode=ParseMode.HTML)
    if msg_text.startswith('/ip '): return await update.message.reply_text(await ZetaInternetTools.ip_lookup(msg_text.split(' ')[1]), parse_mode=ParseMode.HTML)

    if state == 'awaiting_phone':
        if not re.match(r'^[0-9]+$', msg_text) or len(msg_text) < 9:
            return await update.message.reply_text("❌ Nomor tidak valid.")
            
        code, prod_name = context.user_data['trx_code'], context.user_data['trx_name']
        processing_msg = await update.message.reply_text("⏳ <b>Memproses Transaksi...</b>", parse_mode=ParseMode.HTML)
        
        # Proses ke PortalPulsa
        # ID CUST untuk PLN, selain itu None
        id_cust = msg_text if 'PLN' in prod_name else None
        
        result = await pp_client.topup(code, msg_text, id_cust)
        await processing_msg.delete()
        
        if result.get('result') == 'failed':
            await update.message.reply_text(f"❌ <b>Gagal</b>: {result.get('message', 'Unknown Error')}", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"✅ <b>Sukses!</b>\n\n📦 {prod_name}\n📱 {msg_text}\n📝 {result.get('message', 'Diproses')}", parse_mode=ParseMode.HTML)
        
        context.user_data.clear()

async def cek_status_akun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = await pp_client.cek_saldo()
    saldo_info = str(res) if res.get('result') != 'failed' else "Gagal mengambil data."
    await query.edit_message_text(f"ℹ️ <b>Status Akun</b>\n\nRespon Server: {html.escape(saldo_info)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Kembali", callback_data="start")]]), parse_mode=ParseMode.HTML)

def main():
    if not TOKEN: logger.critical("Token Bot tidak ditemukan."); sys.exit(1)
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^start$'))
    app.add_handler(CallbackQueryHandler(menu_category_handler, pattern='^menu_(pulsa|pln|crypto|stock|ip)$'))
    app.add_handler(CallbackQueryHandler(menu_xl_special, pattern='^menu_xl_special$'))
    app.add_handler(CallbackQueryHandler(list_xl_special_items, pattern='^xl_list_'))
    app.add_handler(CallbackQueryHandler(show_manual_detail, pattern='^detail_manual_'))
    app.add_handler(CallbackQueryHandler(list_products_by_op, pattern='^list_op_'))
    app.add_handler(CallbackQueryHandler(buy_confirmation, pattern='^buy_'))
    app.add_handler(CallbackQueryHandler(cek_status_akun, pattern='^status_akun$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_transaction))

    print("🚀 Bot Pulsa Net API (v2.1) Started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
