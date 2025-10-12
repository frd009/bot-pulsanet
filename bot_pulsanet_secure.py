# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet_secure.py
# Developer: frd009
# Versi: 7.3 (Enhanced Layout & Better UX)
# ============================================

import os
import re
import html
import warnings
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Menghilangkan peringatan 'pkg_resources is deprecated'
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# ==============================================================================
# 📦 DATA PRODUK TERKURASI
# ==============================================================================
ALL_PACKAGES_RAW = [
    # ============== XL (Paket Spesial dari Awal) ==============
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

    # ============== Paket Data Pilihan Lainnya ==============
    # --- XL ---
    {'id': 219, 'name': "XL Flex S 5GB 28Hari", 'price': 27000, 'category': 'XL', 'type': 'Paket', 'data': '5 GB', 'validity': '28 Hari', 'details': '5GB Nasional, Hingga 3GB Lokal, Nelpon 5 Menit'},
    {'id': 221, 'name': "XL Flex M 10GB 28Hari", 'price': 45000, 'category': 'XL', 'type': 'Paket', 'data': '10 GB', 'validity': '28 Hari', 'details': '10GB Nasional, Hingga 5GB Lokal, Nelpon 5 Menit'},
    {'id': 224, 'name': "XL Flex L Plus 26GB 28Hari", 'price': 75000, 'category': 'XL', 'type': 'Paket', 'data': '26 GB', 'validity': '28 Hari', 'details': '26GB Nasional, Hingga 11GB Lokal, Nelpon 5 Menit'},
    # --- Tri ---
    {'id': 18, 'name': "Tri Happy 5gb 7hari", 'price': 20000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '7 Hari', 'details': 'Kuota 5gb, Berlaku Nasional, 1.5gb Lokal'},
    {'id': 26, 'name': "Tri Happy 11gb 28hari", 'price': 46000, 'category': 'Tri', 'type': 'Paket', 'data': '11 GB', 'validity': '28 Hari', 'details': 'Kuota 11gb, Berlaku Nasional, 6gb Lokal'},
    {'id': 30, 'name': "Tri Happy 42gb 28hari", 'price': 71000, 'category': 'Tri', 'type': 'Paket', 'data': '42 GB', 'validity': '28 Hari', 'details': 'Kuota 42gb, Berlaku Nasional, 8gb Lokal'},
    # --- Axis ---
    {'id': 71, 'name': "Axis Bronet 2gb 30hari", 'price': 19000, 'category': 'Axis', 'type': 'Paket', 'data': '2 GB', 'validity': '30 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 74, 'name': "Axis Bronet 8gb 30hari", 'price': 39000, 'category': 'Axis', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': 'Kuota 8gb, Berlaku Nasional'},
    {'id': 76, 'name': "Axis Bronet 20gb 30hari", 'price': 73000, 'category': 'Axis', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20gb, Berlaku Nasional'},
    # --- Indosat ---
    {'id': 181, 'name': "Freedom Internet 6GB 28Hari", 'price': 26000, 'category': 'Indosat', 'type': 'Paket', 'data': '6 GB', 'validity': '28 Hari', 'details': 'Kuota 6GB, Nasional'},
    {'id': 186, 'name': "Freedom Internet 13GB 28Hari", 'price': 52000, 'category': 'Indosat', 'type': 'Paket', 'data': '13 GB', 'validity': '28 Hari', 'details': 'Kuota 13GB, Nasional'},
    {'id': 188, 'name': "Freedom Internet 30GB 28Hari", 'price': 90000, 'category': 'Indosat', 'type': 'Paket', 'data': '30 GB', 'validity': '28 Hari', 'details': 'Kuota 30GB, Nasional'},
    # --- Telkomsel ---
    {'id': 266, 'name': "Tsel Promo 3gb 30 Hari", 'price': 26000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '3 GB', 'validity': '30 Hari', 'details': '3gb + Bonus Extra Kuota'},
    {'id': 269, 'name': "Tsel Promo 6.5gb 30 Hari", 'price': 57000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '6.5 GB', 'validity': '30 Hari', 'details': '6.5gb + Bonus Extra Kuota'},
    {'id': 271, 'name': "Tsel 8gb 30 Hari", 'price': 68000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': '8gb + Bonus Extra Kuota'},
    # --- By.U ---
    {'id': 129, 'name': "By.U Promo 9GB 30Hari", 'price': 27000, 'category': 'By.U', 'type': 'Paket', 'data': '9 GB', 'validity': '30 Hari', 'details': 'Kuota 9GB, Nasional'},
    {'id': 132, 'name': "By.U Promo 20GB 30Hari", 'price': 47000, 'category': 'By.U', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20GB, Nasional'},

    # ============== Pulsa Pilihan ==============
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

def create_two_column_keyboard(items, callback_prefix="", back_callback=None):
    """
    Membuat keyboard dengan layout 2 kolom yang lebih baik untuk mobile.
    items: list of tuples (text, callback_data) atau list of dicts {'text': ..., 'callback': ...}
    """
    keyboard = []
    
    # Konversi items ke format uniform
    if items and isinstance(items[0], tuple):
        items = [{'text': text, 'callback': callback} for text, callback in items]
    
    # Buat baris dengan 2 kolom
    for i in range(0, len(items), 2):
        row = []
        # Kolom pertama
        item1 = items[i]
        row.append(InlineKeyboardButton(item1['text'], callback_data=item1['callback']))
        
        # Kolom kedua (jika ada)
        if i + 1 < len(items):
            item2 = items[i + 1]
            row.append(InlineKeyboardButton(item2['text'], callback_data=item2['callback']))
        
        keyboard.append(row)
    
    # Tambahkan tombol back jika ada
    if back_callback:
        keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_callback)])
    
    return keyboard

def format_price(price):
    """Format harga menjadi format Rupiah yang lebih readable"""
    return f"Rp{price:,}".replace(",", ".")

def shorten_product_name(name, category):
    """Mempersingkat nama produk untuk tampilan yang lebih baik di mobile"""
    # Hapus nama provider di awal
    name = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', name, flags=re.I)
    # Hapus kata "Paket"
    name = name.replace('Paket ', '').replace('paket ', '')
    return name.strip()

# Data kuota spesifik untuk paket Akrab berdasarkan informasi terbaru
AKRAB_QUOTA_DETAILS = {
    "pkg_305_xl_akrab_mini_v2": {"1": "31GB - 33GB", "2": "33GB - 35GB", "3": "38GB - 40GB", "4": "48GB - 50GB"},
    "pkg_307_xl_akrab_big_v2": {"1": "38GB - 40GB", "2": "40GB - 42GB", "3": "45GB - 47GB", "4": "55GB - 57GB"},
    "pkg_313_xl_akrab_jumbo_v2": {"1": "65GB", "2": "70GB", "3": "83GB", "4": "123GB"},
    "pkg_315_xl_akrab_mega_big_v2": {"1": "88GB - 90GB", "2": "90GB - 92GB", "3": "95GB - 97GB", "4": "105GB - 107GB"},
}
# Alias untuk paket non-V2 agar menggunakan detail yang sama
AKRAB_QUOTA_DETAILS['pkg_304_xl_akrab_mini'] = AKRAB_QUOTA_DETAILS.get('pkg_305_xl_akrab_mini_v2')

# ==============================================================================
# ✍️ FUNGSI PEMBUAT DESKRIPSI (VERSI PROFESIONAL)
# ==============================================================================

def create_header(info):
    price = format_price(info.get('price', 0))
    return f"✨ <b>{safe_html(info.get('name', 'N/A'))}</b> ✨\n💵 <b>Harga: {price}</b>\n"

def create_general_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    header = create_header(info)
    
    if info.get('type') == 'Pulsa':
        return (header +
                f"\n• 💰 <b>Nominal Pulsa:</b> {info.get('data', 'N/A')}\n"
                f"• ⏳ <b>Penambahan Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}")
    else:
        return (header +
                f"\n• 💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n"
                f"• 📅 <b>Masa Aktif:</b> {info.get('validity', 'N/A')}\n"
                f"• 📝 <b>Rincian:</b> {safe_html(info.get('details', 'N/A'))}")

def create_akrab_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    quota_info = AKRAB_QUOTA_DETAILS.get(package_key)
    description = create_header(info) + "\n"
    
    description += (
        "<i>Paket keluarga resmi dari XL dengan kuota besar yang bisa dibagi-pakai.</i>\n\n"
        "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL)\n"
        "🛡️ <b>Jaminan:</b> Garansi Penuh\n"
        "🌐 <b>Kompatibilitas:</b> XL / AXIS / LIVEON\n"
        "📅 <b>Masa Aktif:</b> ±28 hari (sesuai ketentuan XL)\n\n"
    )
    
    if quota_info:
        description += (
            "💾 <b>Estimasi Total Kuota (berdasarkan zona):</b>\n"
            f"  - <b>Area 1:</b> {quota_info.get('1', 'N/A')}\n"
            f"  - <b>Area 2:</b> {quota_info.get('2', 'N/A')}\n"
            f"  - <b>Area 3:</b> {quota_info.get('3', 'N/A')}\n"
            f"  - <b>Area 4:</b> {quota_info.get('4', 'N/A')}\n\n"
        )
    else:
        description += f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')}\n\n"

    description += (
        "📋 <b>Prosedur & Ketentuan Penting:</b>\n"
        "  - Pastikan SIM terpasang di perangkat (HP/Modem) untuk deteksi lokasi BTS dan klaim bonus kuota lokal.\n"
        "  - Jika kuota MyRewards belum masuk sepenuhnya, mohon tunggu 1x24 jam sebelum melapor ke Admin.\n\n"
        "ℹ️ <b>Informasi Tambahan:</b>\n"
        "  - <a href='http://bit.ly/area_akrab'>Cek Pembagian Area Kuota Anda</a>\n"
        "  - <a href='https://kmsp-store.com/cara-unreg-paket-akrab-yang-benar'>Panduan Unreg Paket Akrab</a>"
    )
    return description

def create_circle_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    return (
        create_header(info) + "\n"
        "<i>Paket eksklusif dengan kuota dinamis yang menguntungkan.</i>\n\n"
        f"💾 <b>Estimasi Kuota:</b> {info.get('data', 'N/A')} (potensi dapat lebih)\n"
        "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n"
        "⏳ <b>Masa Aktif:</b> 28 hari atau hingga kuota habis. Jika kuota habis sebelum 28 hari, status keanggotaan menjadi <b>BEKU/FREEZE</b>.\n"
        "⚡ <b>Aktivasi:</b> Instan, tanpa OTP.\n\n"
        "⚠️ <b>PERHATIAN (WAJIB BACA):</b>\n"
        "<b>1. Cara Cek Kuota:</b>\n"
        "   - Buka aplikasi <b>MyXL terbaru</b>.\n"
        "   - Klik menu <b>XL CIRCLE</b> di bagian bawah (bukan dari 'Lihat Paket Saya').\n\n"
        "<b>2. Syarat & Ketentuan:</b>\n"
        "   - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n"
        "   - <b>Keanggotaan:</b> Tidak terdaftar di Circle lain pada bulan yang sama.\n"
        "   - <b>Status Kartu:</b> Tidak dalam masa tenggang.\n"
        "   - <b>DILARANG UNREG:</b> Keluar dari Circle akan menghanguskan garansi (tanpa refund)."
    )

def create_bebaspuas_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    return (
        create_header(info) + "\n"
        "<i>Nikmati kebebasan internetan dengan kuota besar yang bisa diakumulasi.</i>\n\n"
        "✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) via Sidompul\n"
        "⚡ <b>Aktivasi:</b> Instan, tanpa memerlukan kode OTP\n"
        "📱 <b>Kompatibilitas:</b> Khusus XL Prabayar (Prepaid)\n"
        "🌍 <b>Area:</b> Berlaku di seluruh Indonesia\n"
        "📅 <b>Masa Aktif & Garansi:</b> 30 Hari\n"
        f"💾 <b>Kuota Utama:</b> {info.get('data', 'N/A')} (Full 24 Jam)\n\n"
        "⭐ <b>Fitur Unggulan:</b>\n"
        "  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli paket Bebas Puas lain sebelum masa aktif berakhir.\n"
        "  - <b>Tanpa Syarat Pulsa:</b> Aktivasi tidak memerlukan pulsa minimum.\n\n"
        "🎁 <b>Klaim Bonus:</b>\n"
        "  - Tersedia bonus kuota yang dapat diklaim di aplikasi myXL (pilih salah satu: YouTube, TikTok, atau Kuota Utama)."
    )

# Pra-generate semua deskripsi untuk efisiensi
PAKET_DESCRIPTIONS = {key: create_general_description(key) for key in ALL_PACKAGES_DATA}
for key in get_products(special_type='Akrab'): PAKET_DESCRIPTIONS[key] = create_akrab_description(key)
for key in get_products(special_type='Circle'): PAKET_DESCRIPTIONS[key] = create_circle_description(key)
for key in get_products(special_type='BebasPuas'): PAKET_DESCRIPTIONS[key] = create_bebaspuas_description(key)
PAKET_DESCRIPTIONS["bantuan"] = (
    "<b>Pusat Bantuan & Informasi</b> ❔\n\n"
    "Selamat datang di pusat bantuan Pulsa Net Bot.\n\n"
    "Jika Anda mengalami kendala teknis, memiliki pertanyaan seputar produk, atau tertarik untuk menjadi reseller, jangan ragu untuk menghubungi Admin kami.\n\n"
    "Gunakan perintah /start untuk kembali ke menu utama kapan saja.\n\n"
    "📞 <b>Admin:</b> @hexynos\n"
    "🌐 <b>Website Resmi:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>"
)

# ==============================================================================
# 🤖 FUNGSI HANDLER BOT
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(jakarta_tz)
    hour = now.hour
    
    if 5 <= hour < 12: greeting = "Selamat Pagi ☀️"
    elif 12 <= hour < 15: greeting = "Selamat Siang 🌤️"
    elif 15 <= hour < 19: greeting = "Selamat Sore 🌥️"
    else: greeting = "Selamat Malam 🌙"

    keyboard = [
        [InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), 
         InlineKeyboardButton("💰 Pulsa", callback_data="main_pulsa")],
        [InlineKeyboardButton("📊 Cek Kuota", url="https://t.me/dompetpulsabot"), 
         InlineKeyboardButton("❔ Bantuan", callback_data="main_bantuan")],
        [InlineKeyboardButton("🌐 Kunjungi Website", url="https://pulsanet.kesug.com/beli.html")]
    ]
    text = (f"{greeting}, {user.first_name}!\n\n"
            "Selamat datang di <b>Pulsa Net Bot</b> 🤖, solusi terpercaya untuk kebutuhan pulsa dan paket data Anda. "
            "Silakan pilih kategori produk di bawah ini.\n\n"
            "💡 <i>Untuk daftar produk lengkap, kunjungi website kami.</i>")
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_type_key = query.data.split('_')[1]
    product_type_name = "Paket Data" if product_type_key == "paket" else "Pulsa"
    
    operators = [
        {'text': "💙 XL", 'callback': f"list_{product_type_key}_xl"},
        {'text': "💜 Axis", 'callback': f"list_{product_type_key}_axis"},
        {'text': "🧡 Tri", 'callback': f"list_{product_type_key}_tri"},
        {'text': "❤️ Telkomsel", 'callback': f"list_{product_type_key}_telkomsel"},
        {'text': "💛 Indosat", 'callback': f"list_{product_type_key}_indosat"},
        {'text': "🖤 By.U", 'callback': f"list_{product_type_key}_by.u"}
    ]
    
    keyboard = create_two_column_keyboard(operators, back_callback="back_to_start")
    
    await query.edit_message_text(
        f"<b>Pilih Provider {product_type_name}</b> 📱\n\n"
        f"Silakan pilih provider yang Anda gunakan:",
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode="HTML"
    )

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    
    xl_paket_types = [
        {'text': "🤝 Akrab", 'callback': "list_paket_xl_akrab"},
        {'text': "🥳 Bebas Puas", 'callback': "list_paket_xl_bebaspuas"},
        {'text': "🌀 Circle", 'callback': "list_paket_xl_circle"},
        {'text': "🚀 Paket Lainnya", 'callback': "list_paket_xl_paket"}
    ]
    
    keyboard = create_two_column_keyboard(xl_paket_types, back_callback="main_paket")
    
    await update.callback_query.edit_message_text(
        "<b>Pilihan Paket Data XL</b> 💙\n\n"
        "Kami menyediakan beberapa jenis paket XL yang dapat disesuaikan dengan kebutuhan Anda. "
        "Silakan pilih jenis paket di bawah ini:",
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode="HTML"
    )

async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query, data_parts = update.callback_query, update.callback_query.data.split('_')
    await query.answer()
    
    product_type_key, category_key, special_type_key = data_parts[1], data_parts[2], data_parts[3] if len(data_parts) > 3 else None
    
    titles = {"tri": "Tri 🧡", "axis": "Axis 💜", "telkomsel": "Telkomsel ❤️", "indosat": "Indosat 💛", "by.u": "By.U 🖤", "xl": "XL 💙"}
    base_title = titles.get(category_key, '')
    
    if special_type_key:
        products = get_products(category=category_key, special_type=special_type_key)
        title_map = {"akrab": "Paket Akrab", "bebaspuas": "Paket Bebas Puas", "circle": "Paket Circle", "paket": "Paket Lainnya"}
        title = f"<b>{base_title} - {title_map.get(special_type_key)}</b>"
        subtitle = f"Pilih paket {title_map.get(special_type_key, '')} yang sesuai:"
    else:
        products = get_products(category=category_key, product_type=product_type_key)
        product_name = 'Paket Data' if product_type_key == 'paket' else 'Pulsa'
        title = f"<b>{base_title} - {product_name}</b>"
        subtitle = f"Pilih {product_name} yang Anda inginkan:"

    if not products:
        back_cb = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"
        await query.edit_message_text(
            f"Mohon maaf, produk untuk kategori ini belum tersedia.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)]]),
            parse_mode="HTML"
        )
        return

    sorted_keys = sorted(products.keys(), key=lambda k: PRICES.get(k, 0))
    
    # Buat list items untuk keyboard 2 kolom
    product_items = []
    for key in sorted_keys:
        short_name = shorten_product_name(products[key], category_key)
        button_text = f"{short_name}\n{format_price(PRICES.get(key, 0))}"
        product_items.append({'text': button_text, 'callback': key})
    
    back_cb = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"
    keyboard = create_two_column_keyboard(product_items, back_callback=back_cb)
    
    await query.edit_message_text(
        f"{title}\n\n{subtitle}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query, package_key = update.callback_query, update.callback_query.data
    await query.answer()

    info = ALL_PACKAGES_DATA.get(package_key, {})
    category, p_type = info.get('category', '').lower(), info.get('type', '').lower()
    product_type_key = 'pulsa' if p_type == 'pulsa' else 'paket'
    
    if category == 'xl' and product_type_key == 'paket':
        back_data = f"list_paket_xl_{p_type}" if p_type in ['akrab', 'bebaspuas', 'circle'] else "list_paket_xl_paket"
    else:
        back_data = f"list_{product_type_key}_{category}"

    keyboard = [
        [InlineKeyboardButton("🛒 Beli Sekarang", url="https://pulsanet.kesug.com/beli.html")],
        [InlineKeyboardButton("⬅️ Daftar Produk", callback_data=back_data),
         InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]
    ]
    
    await query.edit_message_text(
        PAKET_DESCRIPTIONS.get(package_key, "Informasi produk tidak ditemukan."),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💬 Hubungi Admin", url="https://t.me/hexynos"),
         InlineKeyboardButton("🌐 Website", url="https://pulsanet.kesug.com/")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]
    ]
    
    await query.edit_message_text(
        PAKET_DESCRIPTIONS["bantuan"],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# ==============================================================================
# 🚀 FUNGSI UTAMA UNTUK MENJALANKAN BOT
# ==============================================================================

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak ditemukan! Silakan atur TELEGRAM_BOT_TOKEN di environment variable Anda.")

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^back_to_start))
    app.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan))
    app.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)))
    app.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl))
    app.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+))
    app.add_handler(CallbackQueryHandler(show_package_details, pattern=f'^({ "|".join(re.escape(k) for k in ALL_PACKAGES_DATA) })))
    
    print("🤖 Bot Pulsa Net (v7.3 - Enhanced UI) sedang berjalan...")
    print("✅ Fitur baru: Layout 2 kolom untuk mobile, UI yang lebih baik")
    app.run_polling()

if __name__ == "__main__":
    main()
