# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet_secure.py
# Developer: Farid Fauzi
# Versi: 4.1 (Perbaikan Error JobQueue)
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from zoneinfo import ZoneInfo
import warnings
import re
import html
import os

# Menghilangkan peringatan 'pkg_resources is deprecated'
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# --- AMANKAN TOKEN BOT ANDA ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("Token bot tidak ditemukan! Silakan set TELEGRAM_BOT_TOKEN di environment variable.")

def safe_html(text):
    """Loloskan karakter khusus HTML: <, >, &"""
    return html.escape(str(text))

# ==============================================================================
# 📦 DATA LENGKAP SEMUA PAKET (DARI beli.html)
# ==============================================================================
ALL_PACKAGES_RAW = [
    # Data dari Tri
    {'id': 1, 'name': "Tri Happy 1.5gb 1 Hari", 'price': 4000, 'category': 'Tri', 'type': 'Paket', 'data': '1.5 GB', 'validity': '1 Hari', 'details': 'Kuota 1.5gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 2, 'name': "Tri Happy 2gb 1 Hari", 'price': 4000, 'category': 'Tri', 'type': 'Paket', 'data': '2 GB', 'validity': '1 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 3, 'name': "Tri Happy 2.5gb 1 Hari", 'price': 6000, 'category': 'Tri', 'type': 'Paket', 'data': '2.5 GB', 'validity': '1 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 28, 'name': "Tri Happy 30GB 30hari (1GB/hari)", 'price': 51000, 'category': 'Tri', 'type': 'Paket', 'data': '30 GB', 'validity': '30 Hari', 'details': 'Kuota 30GB (1GB/hari), Berlaku Nasional'},
    {'id': 49, 'name': "Tri Pulsa 5.000", 'price': 6000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+5 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 50, 'name': "Tri Pulsa 10.000", 'price': 11000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+10 Hari', 'details': 'Pulsa Reguler 10.000'},
    # Data dari Axis
    {'id': 69, 'name': "Axis Paket 500mb 30hari", 'price': 4000, 'category': 'Axis', 'type': 'Paket', 'data': '500 MB', 'validity': '30 Hari', 'details': 'Kuota 500Mb, Berlaku Nasional'},
    {'id': 70, 'name': "Axis Paket 1gb 30hari", 'price': 8000, 'category': 'Axis', 'type': 'Paket', 'data': '1 GB', 'validity': '30 Hari', 'details': 'Kuota 1gb, Berlaku Nasional'},
    {'id': 104, 'name': "Axis Pulsa 5.000", 'price': 6000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 105, 'name': "Axis Pulsa 10.000", 'price': 11000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    # Data dari By.U
    {'id': 120, 'name': "By.U Paket Data Harian 1GB 1Hari", 'price': 5000, 'category': 'By.U', 'type': 'Paket', 'data': '1 GB', 'validity': '1 Hari', 'details': 'Kuota 1GB, Nasional'},
    {'id': 138, 'name': "By.U Pulsa 2.000", 'price': 3000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 2.000', 'validity': 'N/A', 'details': 'Pulsa By.U 2.000'},
    # Data dari Indosat
    {'id': 160, 'name': "Freedom U 5.5GB 30Hari", 'price': 34000, 'category': 'Indosat', 'type': 'Paket', 'data': '5.5 GB', 'validity': '30 Hari', 'details': '1GB Kuota Utama, 2GB Kuota Apps'},
    {'id': 194, 'name': "Indosat Pulsa 5.000", 'price': 7000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    # Data dari XL
    {'id': 217, 'name': "XL Flex S Kuota 3.5GB 21Hari", 'price': 20000, 'category': 'XL', 'type': 'Paket', 'data': '3.5 GB', 'validity': '21 Hari', 'details': '3.5GB Nasional, Hingga 1GB Lokal'},
    {'id': 246, 'name': "XL Pulsa 5.000", 'price': 6000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    # Data dari Telkomsel
    {'id': 262, 'name': "Telkomsel 100mb 7 Hari", 'price': 6000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '100 MB', 'validity': '7 Hari', 'details': '100mb, Semua Zona & Jaringan'},
    {'id': 276, 'name': "Telkomsel Pulsa 2.000", 'price': 3000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 2.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 2.000'},
    # Data XL Akrab, Bebas Puas, Circle yang sudah ada di bot sebelumnya
    {"id": 302, "name": "XL Akrab Mini Lite", "price": 46000, "category": 'XL', "type": "Akrab"},
    {"id": 303, "name": "XL Akrab Mini Lite V2", "price": 46000, "category": 'XL', "type": "Akrab"},
    {"id": 304, "name": "XL Akrab Mini", "price": 58000, "category": 'XL', "type": "Akrab"},
    {"id": 305, "name": "XL Akrab Mini V2", "price": 64000, "category": 'XL', "type": "Akrab"},
    {"id": 306, "name": "XL Akrab Big", "price": 66000, "category": 'XL', "type": "Akrab"},
    {"id": 307, "name": "XL Akrab Big V2", "price": 67000, "category": 'XL', "type": "Akrab"},
    {"id": 308, "name": "XL Akrab Big Extra V2", "price": 80000, "category": 'XL', "type": "Akrab"},
    {"id": 309, "name": "XL Akrab Big Ultimate V2", "price": 84000, "category": 'XL', "type": "Akrab"},
    {"id": 310, "name": "XL Akrab Jumbo Lite", "price": 73000, "category": 'XL', "type": "Akrab"},
    {"id": 311, "name": "XL Akrab Jumbo Lite V2", "price": 76000, "category": 'XL', "type": "Akrab"},
    {"id": 312, "name": "XL Akrab Jumbo", "price": 91000, "category": 'XL', "type": "Akrab"},
    {"id": 313, "name": "XL Akrab Jumbo V2", "price": 97000, "category": 'XL', "type": "Akrab"},
    {"id": 314, "name": "XL Akrab Mega Big", "price": 98000, "category": 'XL', "type": "Akrab"},
    {"id": 315, "name": "XL Akrab Mega Big V2", "price": 102000, "category": 'XL', "type": "Akrab"},
    {"id": 316, "name": "XL Akrab Extra Mega Big V2", "price": 132000, "category": 'XL', "type": "Akrab"},
    {"id": 317, "name": "XL Bebas Puas 75GB", "price": 98000, "category": 'XL', "type": "BebasPuas"},
    {"id": 318, "name": "XL Bebas Puas 234GB", "price": 171000, "category": 'XL', "type": "BebasPuas"},
    {"id": 319, "name": "XL Circle 7–11GB", "price": 31000, "category": 'XL', "type": "Circle"},
    {"id": 320, "name": "XL Circle 12–16GB", "price": 36000, "category": 'XL', "type": "Circle"},
    {"id": 321, "name": "XL Circle 17–21GB", "price": 42000, "category": 'XL', "type": "Circle"},
    {"id": 322, "name": "XL Circle 22–26GB", "price": 51000, "category": 'XL', "type": "Circle"},
    {"id": 323, "name": "XL Circle 27–31GB", "price": 58000, "category": 'XL', "type": "Circle"},
    {"id": 324, "name": "XL Circle 32–36GB", "price": 66000, "category": 'XL', "type": "Circle"},
    {"id": 325, "name": "XL Circle 37–41GB", "price": 76000, "category": 'XL', "type": "Circle"},
]

# --- Fungsi untuk membuat key unik ---
def create_package_key(pkg):
    name_slug = re.sub(r'[^a-z0-9_]', '', pkg['name'].lower().replace(' ', '_'))
    return f"pkg_{pkg['id']}_{name_slug}"

# --- Memproses data mentah menjadi struktur yang bisa digunakan bot ---
ALL_PACKAGES_DATA = {create_package_key(pkg): pkg for pkg in ALL_PACKAGES_RAW}
PRICES = {key: data['price'] for key, data in ALL_PACKAGES_DATA.items()}

# --- Mengelompokkan paket berdasarkan kategori untuk menu ---
def get_packages_by_type(package_type):
    return {key: data['name'] for key, data in ALL_PACKAGES_DATA.items() if data.get('type') == package_type}

def get_packages_by_category(category, exclude_types=None):
    if exclude_types is None:
        exclude_types = []
    return {key: data['name'] for key, data in ALL_PACKAGES_DATA.items() if data.get('category') == category and data.get('type') not in exclude_types}

AKRAB_PACKAGES = get_packages_by_type('Akrab')
BEBAS_PUAS_PACKAGES = get_packages_by_type('BebasPuas')
CIRCLE_PACKAGES = get_packages_by_type('Circle')
TRI_PACKAGES = get_packages_by_category('Tri')
AXIS_PACKAGES = get_packages_by_category('Axis')
BYU_PACKAGES = get_packages_by_category('By.U')
INDOSAT_PACKAGES = get_packages_by_category('Indosat')
TELKOMSEL_PACKAGES = get_packages_by_category('Telkomsel')
XL_OTHER_PACKAGES = get_packages_by_category('XL', exclude_types=['Akrab', 'BebasPuas', 'Circle'])

# --- DETAIL KUOTA PAKET (Struktur data lama untuk deskripsi Akrab) ---
AKRAB_QUOTA_DETAILS = {
    "pkg_305_xl_akrab_mini_v2": {"1": "31GB - 33GB", "2": "33GB - 35GB", "3": "38GB - 40GB", "4": "48GB - 50GB"},
    "pkg_306_xl_akrab_big": {"1": "38 GB - 40 GB", "2": "40 GB - 42 GB", "3": "45 GB - 47 GB", "4": "55 GB - 57 GB"},
    "pkg_307_xl_akrab_big_v2": {"1": "38GB - 40GB", "2": "40GB - 42GB", "3": "45GB - 47GB", "4": "55GB - 57GB"},
    "pkg_308_xl_akrab_big_extra_v2": {"1": "33GB", "2": "36GB", "3": "47GB", "4": "71GB"},
    "pkg_309_xl_akrab_big_ultimate_v2": {"1": "54GB", "2": "56GB", "3": "61GB", "4": "71GB"},
    "pkg_311_xl_akrab_jumbo_lite_v2": {"1": "47GB", "2": "49GB", "3": "54GB", "4": "64GB"},
    "pkg_312_xl_akrab_jumbo": {"1": "65 GB", "2": "70 GB", "3": "83 GB", "4": "123 GB"},
    "pkg_313_xl_akrab_jumbo_v2": {"1": "65GB", "2": "70GB", "3": "83GB", "4": "123GB"},
    "pkg_314_xl_akrab_mega_big": {"1": "88 GB - 90 GB", "2": "90 GB - 92 GB", "3": "95 GB - 97 GB", "4": "105 GB - 107 GB"},
    "pkg_315_xl_akrab_mega_big_v2": {"1": "88GB - 90GB", "2": "90GB - 92GB", "3": "95GB - 97GB", "4": "105GB - 107GB"},
    "pkg_316_xl_akrab_extra_mega_big_v2": {"1": "105GB", "2": "110GB", "3": "123GB", "4": "163GB"}
}
# Menyesuaikan key di AKRAB_QUOTA_DETAILS agar cocok dengan key baru
# (Contoh manual, idealnya dilakukan secara terprogram jika lebih banyak)
AKRAB_QUOTA_DETAILS['pkg_304_xl_akrab_mini'] = AKRAB_QUOTA_DETAILS.get('pkg_305_xl_akrab_mini_v2') # Asumsi kuota sama


# ==============================================================================
# ✍️ Fungsi Pembuat Deskripsi Paket
# ==============================================================================

def create_general_description(package_key):
    """Membuat deskripsi umum untuk paket data atau pulsa."""
    info = ALL_PACKAGES_DATA.get(package_key)
    if not info: return "Deskripsi tidak ditemukan."

    name = info.get('name', "N/A")
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    
    header = f"<b>{safe_html(name)}</b>\n<b>Harga: {price}</b>\n\n"
    
    if info.get('type') == 'Pulsa':
        description = (
            header +
            f"• 💰 <b>Nominal Pulsa:</b> {info.get('data', 'N/A')}\n"
            f"• ⏳ <b>Tambah Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
            f"• 📝 <b>Detail:</b> {safe_html(info.get('details', 'N/A'))}\n"
            f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}"
        )
    else: # Default untuk 'Paket'
        description = (
            header +
            f"• 💾 <b>Kuota:</b> {info.get('data', 'N/A')}\n"
            f"• 📅 <b>Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
            f"• 📝 <b>Rincian:</b> {safe_html(info.get('details', 'N/A'))}\n"
            f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}"
        )
    return description

def create_akrab_description(package_key):
    package_name = ALL_PACKAGES_DATA.get(package_key, {}).get('name', 'Paket Akrab')
    price = PRICES.get(package_key, 0)
    formatted_price = f"Rp{price:,}".replace(",", ".")
    quota_info = AKRAB_QUOTA_DETAILS.get(package_key)
    description = (
        f"<b>{safe_html(package_name)}</b>\n<b>Harga: {formatted_price}</b>\n\n"
        f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL).\n"
        f"• 🛡️ <b>Jaminan:</b> GARANSI FULL.\n"
        f"• 🌐 <b>Kompatibilitas:</b> Bisa untuk XL / AXIS / LIVEON.\n"
        f"• 📅 <b>Masa Aktif:</b> ±28 hari, sesuai ketentuan pihak XL.\n\n"
    )
    if quota_info:
        description += (
            f"• 💾 <b>Kuota 24 Jam (berdasarkan zona):</b>\n"
            f"  - <b>AREA 1:</b> {quota_info.get('1', 'N/A')}\n"
            f"  - <b>AREA 2:</b> {quota_info.get('2', 'N/A')}\n"
            f"  - <b>AREA 3:</b> {quota_info.get('3', 'N/A')}\n"
            f"  - <b>AREA 4:</b> {quota_info.get('4', 'N/A')}\n\n"
        )
    else:
        description += "• 💾 <b>Detail Kuota:</b>\n  - Informasi detail kuota berdasarkan zona untuk paket ini akan segera diperbarui. Hubungi admin untuk informasi lebih lanjut.\n\n"
    description += (
        f"• 📋 <b>Prosedur & Ketentuan:</b>\n"
        f"  - Pastikan kartu SIM terpasang pada perangkat (HP/Modem) untuk deteksi lokasi BTS dan mendapatkan bonus kuota lokal.\n"
        f"  - Apabila kuota MyRewards belum masuk full, tunggu 1x24 jam sebelum laporan ke Admin.\n\n"
        f"• ℹ️ <b>Informasi Tambahan:</b>\n"
        f"  - <a href='http://bit.ly/area_akrab'>Cek Area Anda di sini</a>\n"
        f"  - <a href='https://kmsp-store.com/cara-unreg-paket-akrab-yang-benar'>Panduan Unreg Paket Akrab</a>"
    )
    return description

def create_circle_description(package_key):
    package_name = ALL_PACKAGES_DATA.get(package_key, {}).get('name', 'Paket XL Circle')
    price = PRICES.get(package_key, 0)
    formatted_price = f"Rp{price:,}".replace(",", ".")
    quota_range = package_name.split(" ")[-1]
    description = (
        f"<b>{safe_html(package_name)}</b>\n<b>Harga: {formatted_price}</b>\n\n"
        f"• 💾 <b>Estimasi Kuota:</b> {quota_range} (bisa dapat lebih jika beruntung).\n"
        f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n"
        f"• ⏳ <b>Masa Aktif:</b> 28 hari atau hingga kuota habis. Jika kuota habis sebelum 28 hari, keanggotaan akan masuk kondisi <b>BEKU/FREEZE</b> dan order ulang baru bisa dilakukan bulan depan.\n"
        f"• ⚡ <b>Aktivasi:</b> Instan, tidak menggunakan OTP.\n\n"
        f"⚠️ <b>PERHATIAN (PENTING):</b>\n"
        f"<b>1. Cara Cek Kuota:</b>\n"
        f"   - Buka aplikasi <b>MyXL terbaru</b>.\n"
        f"   - Klik menu <b>XL CIRCLE</b> di bagian bawah layar. (Bukan dari 'Lihat Paket Saya').\n\n"
        f"<b>2. Syarat & Ketentuan:</b>\n"
        f"   - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n"
        f"   - <b>Keanggotaan:</b> Tidak sedang terdaftar/bergabung di Circle lain dalam bulan yang sama.\n"
        f"   - <b>Masa Tenggang:</b> Kartu tidak boleh dalam masa tenggang. Paket ini <b>tidak menambah</b> masa aktif kartu.\n"
        f"   - <b>Isi Ulang Masa Aktif:</b> Jika kartu akan tenggang, disarankan isi paket masa aktif terlebih dahulu.\n"
        f"   - <b>Prioritas Kuota:</b> Jika ada kuota utama lain, kuota tersebut akan dipakai lebih dulu sebelum kuota Circle.\n"
        f"   - <b>Dilarang Unreg:</b> Keluar dari keanggotaan Circle akan menghanguskan garansi tanpa refund dan tidak bisa di-invite ulang.\n"
    )
    return description

def create_bebaspuas_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    name = info.get('name', 'Bebas Puas')
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    kuota = "75GB" if "75" in name else "234GB"
    return (
        f"<b>{safe_html(name)}</b>\n<b>Harga: {price}</b>\n\n"
        f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) jalur Sidompul.\n"
        f"• ⚡ <b>Aktivasi Instan:</b> Tidak memerlukan kode OTP.\n"
        f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n"
        f"• 🌍 <b>Area:</b> Berlaku di semua area.\n"
        f"• 📅 <b>Masa Aktif & Garansi:</b> 30 Hari.\n"
        f"• 💾 <b>Kuota Utama:</b> {kuota}, full reguler 24 jam.\n\n"
        f"• ⭐ <b>Fitur Unggulan:</b>\n"
        f"  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli/menimpa dengan paket Bebas Puas lain.\n"
        f"  - <b>Tanpa Syarat Pulsa:</b> Aktivasi paket tidak memerlukan pulsa minimum.\n\n"
        f"• 🎁 <b>Klaim Bonus:</b>\n"
        f"  - Tersedia bonus kuota (pilih salah satu: YouTube, TikTok, atau Kuota Utama) yang dapat diklaim di aplikasi myXL.\n"
        f"  - Disarankan untuk mengklaim bonus sebelum melakukan pembelian ulang (menimpa paket) untuk memaksimalkan keuntungan."
    )

# --- Kumpulan Semua Deskripsi ---
PAKET_DESCRIPTIONS = {
    # Deskripsi dinamis untuk semua paket umum
    **{key: create_general_description(key) for key in ALL_PACKAGES_DATA},
    # Timpa dengan deskripsi khusus yang lebih detail
    **{key: create_akrab_description(key) for key in AKRAB_PACKAGES},
    **{key: create_circle_description(key) for key in CIRCLE_PACKAGES},
    **{key: create_bebaspuas_description(key) for key in BEBAS_PUAS_PACKAGES},
    "bantuan": (
        "<b>🛒 Bantuan Bot Pulsa Net</b>\n\n"
        "Ketik /start untuk kembali ke menu utama.\n"
        "Hubungi admin jika Anda ingin mendaftar reseller atau melaporkan kendala teknis.\n\n"
        "📞 <b>Admin:</b> @hexynos\n"
        "🌐 <b>Website:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>"
    ),
}

# =============================
# 🏠 Fungsi utama menu
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Paket Akrab XL", callback_data="menu_akrab_category"), InlineKeyboardButton("🔥 XL Bebas Puas", callback_data="menu_bebaspuas_category")],
        [InlineKeyboardButton("🔵 XL Circle", callback_data="menu_circle_category"), InlineKeyboardButton("⚡ Paket XL Lainnya", callback_data="menu_xl_other_category")],
        [InlineKeyboardButton("🟠 Tri", callback_data="menu_tri_category"), InlineKeyboardButton("🟣 Axis", callback_data="menu_axis_category")],
        [InlineKeyboardButton("🔴 Telkomsel", callback_data="menu_telkomsel_category"), InlineKeyboardButton("🟡 Indosat", callback_data="menu_indosat_category")],
        [InlineKeyboardButton("⚫ By.U", callback_data="menu_byu_category")],
        [InlineKeyboardButton("🛒 Bantuan", callback_data="menu_bantuan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "Selamat datang di <b>Pulsa Net</b> 🎉\n\n"
        "Kami menyediakan berbagai pilihan paket data & pulsa dengan harga kompetitif dan aktivasi cepat.\n\n"
        "Silakan pilih kategori di bawah ini 👇"
    )
    
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            # Jika pesan sama, kirim pesan baru untuk menghindari error
            await update.callback_query.message.reply_text(text="<b>Pulsa Net</b> - Menu Utama", reply_markup=reply_markup, parse_mode="HTML")
        await update.callback_query.answer()
    elif update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

# =============================
# 🖱️ Callback Handlers
# =============================
async def category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    category_map = {
        "menu_akrab_category": ("📦 Paket Akrab XL", AKRAB_PACKAGES),
        "menu_bebaspuas_category": ("🔥 XL Bebas Puas", BEBAS_PUAS_PACKAGES),
        "menu_circle_category": ("🔵 XL Circle", CIRCLE_PACKAGES),
        "menu_xl_other_category": ("⚡ Paket XL Lainnya", XL_OTHER_PACKAGES),
        "menu_tri_category": ("🟠 Tri", TRI_PACKAGES),
        "menu_axis_category": ("🟣 Axis", AXIS_PACKAGES),
        "menu_telkomsel_category": ("🔴 Telkomsel", TELKOMSEL_PACKAGES),
        "menu_indosat_category": ("🟡 Indosat", INDOSAT_PACKAGES),
        "menu_byu_category": ("⚫ By.U", BYU_PACKAGES),
    }

    if data not in category_map:
        await query.edit_message_text("Kategori tidak ditemukan.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_start")]]))
        return

    title, packages = category_map[data]

    if not packages:
        await query.edit_message_text(f"Saat ini belum ada produk untuk kategori <b>{title}</b>.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="back_to_start")]]), parse_mode="HTML")
        return

    keyboard = []
    # Urutkan berdasarkan harga termurah
    sorted_keys = sorted(packages.keys(), key=lambda k: PRICES.get(k, float('inf')))
    
    for i in range(0, len(sorted_keys), 2):
        row = []
        key1 = sorted_keys[i]
        name1 = packages[key1]
        price1 = PRICES.get(key1, 0)
        formatted_price1 = f"Rp{price1:,}".replace(",", ".")
        # Menyingkat nama tombol agar tidak terlalu panjang
        short_name1 = name1.replace('Tri ', '').replace('Axis Paket ', '').replace('XL ', '').replace('Telkomsel ','').replace('Indosat ','')
        button_text1 = f"{short_name1} - {formatted_price1}"
        row.append(InlineKeyboardButton(button_text1, callback_data=key1))

        if i + 1 < len(sorted_keys):
            key2 = sorted_keys[i+1]
            name2 = packages[key2]
            price2 = PRICES.get(key2, 0)
            formatted_price2 = f"Rp{price2:,}".replace(",", ".")
            short_name2 = name2.replace('Tri ', '').replace('Axis Paket ', '').replace('XL ', '').replace('Telkomsel ','').replace('Indosat ','')
            button_text2 = f"{short_name2} - {formatted_price2}"
            row.append(InlineKeyboardButton(button_text2, callback_data=key2))
        
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"<b>{title}</b>\n\nSilakan pilih produk yang detailnya ingin Anda lihat:"
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package_key = query.data
    text = PAKET_DESCRIPTIONS.get(package_key, "Deskripsi tidak ditemukan.")
    
    # Menentukan tombol kembali yang tepat berdasarkan kategori paket
    package_info = ALL_PACKAGES_DATA.get(package_key, {})
    category = package_info.get('category')
    pkg_type = package_info.get('type')

    back_to_category_data = "back_to_start" # Default
    if pkg_type == 'Akrab': back_to_category_data = "menu_akrab_category"
    elif pkg_type == 'BebasPuas': back_to_category_data = "menu_bebaspuas_category"
    elif pkg_type == 'Circle': back_to_category_data = "menu_circle_category"
    elif category == 'XL': back_to_category_data = "menu_xl_other_category"
    elif category == 'Tri': back_to_category_data = "menu_tri_category"
    elif category == 'Axis': back_to_category_data = "menu_axis_category"
    elif category == 'Telkomsel': back_to_category_data = "menu_telkomsel_category"
    elif category == 'Indosat': back_to_category_data = "menu_indosat_category"
    elif category == 'By.U': back_to_category_data = "menu_byu_category"

    keyboard = [
        [InlineKeyboardButton("🛒 Beli Produk Ini", url="https://pulsanet.kesug.com/beli.html")],
        [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data=back_to_category_data)],
        [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)

async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = PAKET_DESCRIPTIONS.get("bantuan")
    keyboard = [[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# =============================
# 🚀 Jalankan Bot
# =============================
def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handler untuk /start
    app.add_handler(CommandHandler("start", start))
    
    # Handler untuk menu kategori
    category_pattern = r'^(menu_akrab_category|menu_bebaspuas_category|menu_circle_category|menu_xl_other_category|menu_tri_category|menu_axis_category|menu_telkomsel_category|menu_indosat_category|menu_byu_category)$'
    app.add_handler(CallbackQueryHandler(category_menu, pattern=category_pattern))
    
    # Handler untuk bantuan
    app.add_handler(CallbackQueryHandler(show_bantuan, pattern='^menu_bantuan$'))

    # Handler untuk menampilkan detail semua paket
    all_package_keys_pattern = '|'.join(re.escape(k) for k in ALL_PACKAGES_DATA)
    app.add_handler(CallbackQueryHandler(show_package_details, pattern=f'^({all_package_keys_pattern})$'))
    
    # Handler untuk kembali ke menu utama
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_start$'))

    print("🤖 Bot Pulsa Net (v4.1) sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

