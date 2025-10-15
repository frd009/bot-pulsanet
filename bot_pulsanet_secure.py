# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet_updated.py
# Developer: frd009
# Versi: 9.3 (Comprehensive Chat Clearing)
#
# CATATAN: Pastikan Anda menginstal semua library yang dibutuhkan
# dengan menjalankan: pip install -r requirements.txt
# ============================================

import os
import re
import html
import warnings
import random
import io
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Tambahan import untuk QR Code ---
import qrcode
from PIL import Image

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Menghilangkan peringatan 'pkg_resources is deprecated'
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# ==============================================================================
# 📦 DATA PRODUK TERKURASI (Tidak ada perubahan di sini)
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

PROVIDER_PREFIXES = {
    "Telkomsel": ["0811", "0812", "0813", "0821", "0822", "0852", "0853", "0823", "0851"],
    "Indosat": ["0814", "0815", "0816", "0855", "0856", "0857", "0858"],
    "XL": ["0817", "0818", "0819", "0859", "0877", "0878"],
    "Axis": ["0838", "0831", "0832", "0833"],
    "Tri": ["0895", "0896", "0897", "0898", "0899"],
    "Smartfren": ["0881", "0882", "0883", "0884", "0885", "0886", "0887", "0888", "0889"],
    "By.U": ["0851"],
}

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
# ✍️ FUNGSI PEMBUAT DESKRIPSI (Tidak ada perubahan)
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
            "   - Buka aplikasi <b>MyXL terbaru</b>.\n" "   - Klik menu <b>XL CIRCLE</b> di bagian bawah (bukan dari 'Lihat Paket Saya').\n\n"
            "<b>2. Syarat & Ketentuan:</b>\n" "   - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n"
            "   - <b>Keanggotaan:</b> Tidak terdaftar di Circle lain pada bulan yang sama.\n" "   - <b>Status Kartu:</b> Tidak dalam masa tenggang.\n"
            "   - <b>DILARANG UNREG:</b> Keluar dari Circle akan menghanguskan garansi (tanpa refund).")

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
PAKET_DESCRIPTIONS["bantuan"] = ("<b>Pusat Bantuan & Informasi</b> ❔\n\n"
                                 "Selamat datang di pusat bantuan Pulsa Net Bot.\n\n"
                                 "Jika Anda mengalami kendala teknis, memiliki pertanyaan seputar produk, atau tertarik untuk menjadi reseller, jangan ragu untuk menghubungi Admin kami.\n\n"
                                 "Gunakan perintah /start untuk kembali ke menu utama kapan saja.\n\n"
                                 "📞 <b>Admin:</b> @hexynos\n" "🌐 <b>Website Resmi:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>")

# ==============================================================================
# 🤖 FUNGSI HANDLER BOT (VERSI 9.3)
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # --- FITUR BARU: Hapus riwayat untuk tampilan yang bersih ---
    if update.message: # Hanya jalankan jika dari command /start, bukan callback
        # Buat salinan daftar ID untuk di-loop, agar aman
        messages_to_clear = list(context.user_data.get('messages_to_clear', []))
        
        for msg_id in messages_to_clear:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass # Abaikan jika pesan sudah tidak ada atau error lain

        # Coba hapus pesan "/start" dari pengguna.
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        except Exception:
            pass

    user = update.effective_user
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(jakarta_tz)
    hour = now.hour
    if 5 <= hour < 12: greeting = "Selamat Pagi ☀️"
    elif 12 <= hour < 15: greeting = "Selamat Siang 🌤️"
    elif 15 <= hour < 19: greeting = "Selamat Sore 🌥️"
    else: greeting = "Selamat Malam 🌙"

    user_info = f"👤: {user.first_name}"
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f"\n🆔: <code>{user.id}</code>"
    
    keyboard = [
        [InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), InlineKeyboardButton("💰 Pulsa", callback_data="main_pulsa")],
        [InlineKeyboardButton("🔍 Cek Provider", callback_data="ask_for_number"), InlineKeyboardButton("🖼️ Generator QR", callback_data="ask_for_qr")],
        [InlineKeyboardButton("🎮 Game Sederhana", callback_data="main_game"), InlineKeyboardButton("🆘 Bantuan", callback_data="main_bantuan")],
        [InlineKeyboardButton("📊 Cek Kuota (via Bot)", url="https://t.me/dompetpulsabot")],
        [InlineKeyboardButton("🌐 Kunjungi Website Kami", url="https://pulsanet.kesug.com/beli.html")]
    ]
    
    text = (f"{greeting}!\n{user_info}\n\n"
            "Selamat datang di <b>Pulsa Net Bot</b> 🤖, solusi terpercaya untuk kebutuhan pulsa dan paket data Anda.\n\n"
            "Gunakan tombol di bawah untuk membeli produk atau menggunakan fitur lainnya.")
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        await update.callback_query.answer()
    else:
        sent_message = await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        # Mulai ulang daftar pelacakan HANYA dengan ID menu baru ini.
        context.user_data['messages_to_clear'] = [sent_message.message_id]

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_type_key = query.data.split('_')[1]
    product_type_name = "Paket Data" if product_type_key == "paket" else "Pulsa"
    operators = {"XL": "🌐", "Axis": "🌐", "Tri": "🌐", "Telkomsel": "🌐", "Indosat": "🌐", "By.U": "🌐"}
    op_items = list(operators.items())
    keyboard = []
    for i in range(0, len(op_items), 2):
        row = [InlineKeyboardButton(f"{icon} {op}", callback_data=f"list_{product_type_key}_{op.lower()}") for op, icon in op_items[i:i+2]]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
    await query.edit_message_text(f"Anda memilih kategori <b>{product_type_name}</b>.\nSilakan pilih provider yang Anda gunakan:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("🤝 Akrab", callback_data="list_paket_xl_akrab"), InlineKeyboardButton("🥳 Bebas Puas", callback_data="list_paket_xl_bebaspuas")],
        [InlineKeyboardButton("🌀 Circle", callback_data="list_paket_xl_circle"), InlineKeyboardButton("🚀 Paket Lainnya", callback_data="list_paket_xl_paket")],
        [InlineKeyboardButton("⬅️ Kembali ke Provider", callback_data="main_paket")]
    ]
    await update.callback_query.edit_message_text("<b>Pilihan Paket Data XL 💙</b>\n\nKami menyediakan beberapa jenis paket XL yang dapat disesuaikan dengan kebutuhan Anda. Silakan pilih jenis paket di bawah ini:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

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
    else:
        products = get_products(category=category_key, product_type=product_type_key)
        product_name = 'Paket Data' if product_type_key == 'paket' else 'Pulsa'
        title = f"<b>{base_title} - {product_name}</b>"
    if not products:
        back_cb = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"
        await query.edit_message_text("Mohon maaf, produk untuk kategori ini belum tersedia.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)]]))
        return
    sorted_keys = sorted(products.keys(), key=lambda k: PRICES.get(k, 0))
    keyboard = []
    for key in sorted_keys:
        short_name = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', products[key], flags=re.I).replace('Paket ', '')
        button_text = f"{short_name} - Rp{PRICES.get(key, 0):,}".replace(",", ".")
        keyboard.append([InlineKeyboardButton(button_text, callback_data=key)])
    back_cb = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_cb)])
    await query.edit_message_text(f"{title}\n\nSilakan pilih produk yang Anda inginkan:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

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
    keyboard = [[InlineKeyboardButton("🛒 Beli Sekarang (Website)", url="https://pulsanet.kesug.com/beli.html")],
                [InlineKeyboardButton("⬅️ Kembali ke Daftar", callback_data=back_data)],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_start")]]
    await query.edit_message_text(PAKET_DESCRIPTIONS.get(package_key, "Informasi produk tidak ditemukan."), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML", disable_web_page_preview=True)

async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(PAKET_DESCRIPTIONS["bantuan"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]]), parse_mode="HTML", disable_web_page_preview=True)

# ==============================================================================
#  FUNGSI UNTUK FITUR BARU (CEK NOMOR, QR, GAME)
# ==============================================================================

async def prompt_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Meminta input user untuk fitur Cek Provider atau QR Generator."""
    query = update.callback_query
    await query.answer()

    action = query.data
    if action == "ask_for_number":
        context.user_data['state'] = 'awaiting_number'
        text = "<b>🔍 Cek Provider Nomor</b>\n\nSilakan kirimkan satu atau beberapa nomor HP yang ingin Anda periksa."
    elif action == "ask_for_qr":
        context.user_data['state'] = 'awaiting_qr_text'
        text = "<b>🖼️ Generator QR Code</b>\n\nSilakan kirimkan teks atau tautan yang ingin Anda jadikan QR Code."
    else:
        return

    keyboard = [[InlineKeyboardButton("⬅️ Batal & Kembali ke Menu", callback_data="back_to_start")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

def get_provider_info(phone_number: str) -> str:
    cleaned_number = re.sub(r'\D', '', phone_number)
    if cleaned_number.startswith('62'):
        cleaned_number = '0' + cleaned_number[2:]

    if not (cleaned_number.startswith('08') and 10 <= len(cleaned_number) <= 13):
        return f"Nomor <code>{safe_html(phone_number)}</code> sepertinya bukan format valid."

    prefix = cleaned_number[:4]
    provider_found = "Tidak diketahui"
    for provider, prefixes in PROVIDER_PREFIXES.items():
        if prefix in prefixes:
            provider_found = provider
            break
    if provider_found == "Telkomsel" and prefix in PROVIDER_PREFIXES["By.U"]:
        provider_found = "Telkomsel / By.U"

    return (f"Nomor: <code>{safe_html(cleaned_number)}</code>\n"
            f"Provider: <b>{provider_found}</b>")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan teks berdasarkan state (menunggu nomor atau teks QR)."""
    
    def _track_message(msg):
        if msg:
            if 'messages_to_clear' not in context.user_data:
                context.user_data['messages_to_clear'] = []
            context.user_data['messages_to_clear'].append(msg.message_id)

    async def _try_delete_user_message():
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception:
            pass # Gagal jika bot tidak punya izin (misal: di chat pribadi)

    state = context.user_data.get('state')
    message_text = update.message.text
    
    if state == 'awaiting_number':
        await _try_delete_user_message()
        phone_numbers = re.findall(r'(?:\+62|62|0)8[1-9][0-9]{7,11}\b', message_text)
        if phone_numbers:
            responses = [get_provider_info(num) for num in phone_numbers]
            sent_msg = await update.message.reply_text("✅ <b>Hasil Pengecekan:</b>\n\n" + "\n\n".join(responses), parse_mode="HTML")
            _track_message(sent_msg)
        else:
            sent_msg = await update.message.reply_text("Maaf, saya tidak menemukan format nomor HP yang valid di pesan Anda.")
            _track_message(sent_msg)
        
        del context.user_data['state']
        sent_msg_2 = await update.message.reply_text("Gunakan /start untuk kembali ke menu utama.")
        _track_message(sent_msg_2)

    elif state == 'awaiting_qr_text':
        await _try_delete_user_message()
        sent_msg_1 = await update.message.reply_text("⏳ Sedang membuat QR Code...")
        _track_message(sent_msg_1)
        try:
            img = qrcode.make(message_text)
            bio = io.BytesIO()
            bio.name = 'qrcode.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            
            sent_photo = await update.message.reply_photo(
                photo=bio,
                caption=f"✅ <b>QR Code Berhasil Dibuat!</b>\n\n<b>Data:</b> <code>{safe_html(message_text)}</code>",
                parse_mode="HTML"
            )
            _track_message(sent_photo)
        except Exception as e:
            sent_err_msg = await update.message.reply_text(f"Terjadi kesalahan saat membuat QR Code: {e}")
            _track_message(sent_err_msg)

        del context.user_data['state']
        sent_msg_2 = await update.message.reply_text("Gunakan /start untuk kembali ke menu utama.")
        _track_message(sent_msg_2)
        
    else:
        phone_numbers = re.findall(r'(?:\+62|62|0)8[1-9][0-9]{7,11}\b', message_text)
        if phone_numbers:
            responses = [get_provider_info(num) for num in phone_numbers]
            sent_msg = await update.message.reply_text("💡 <b>Provider Terdeteksi:</b>\n\n" + "\n\n".join(responses) + 
                                            "\n\n_Ini adalah fitur deteksi otomatis. Gunakan tombol 'Cek Provider' untuk hasil yang lebih pasti._", 
                                            parse_mode="HTML")
            _track_message(sent_msg)
        else:
            sent_msg = await update.message.reply_text("Saya tidak mengerti. Gunakan /start untuk melihat semua perintah yang tersedia.")
            _track_message(sent_msg)

async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("Batu 🗿", callback_data="game_play_rock"),
                 InlineKeyboardButton("Gunting ✂️", callback_data="game_play_scissors"),
                 InlineKeyboardButton("Kertas 📄", callback_data="game_play_paper")],
                [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]]
    await query.edit_message_text("<b>🎮 Game Batu-Gunting-Kertas</b>\n\nAyo bermain! Pilih jagoanmu:",
                                  reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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
        result_text = "<b>Kamu Kalah!</b> 🤖"
    text = (f"Kamu memilih: {user_choice.capitalize()} {emoji[user_choice]}\n"
            f"Bot memilih: {bot_choice.capitalize()} {emoji[bot_choice]}\n\n{result_text}")
    keyboard = [[InlineKeyboardButton("🔄 Main Lagi", callback_data="main_game")],
                [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# ==============================================================================
# 🚀 FUNGSI UTAMA UNTUK MENJALANKAN BOT
# ==============================================================================

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Token bot tidak ditemukan! Silakan atur TELEGRAM_BOT_TOKEN di environment variable Anda.")

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
    app.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan$'))
    
    app.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)$'))
    app.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl$'))
    app.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+$'))
    
    app.add_handler(CallbackQueryHandler(show_package_details, pattern=f'^({"|".join(re.escape(k) for k in ALL_PACKAGES_DATA)})$'))

    app.add_handler(CallbackQueryHandler(prompt_for_action, pattern=r'^ask_for_(number|qr)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    app.add_handler(CallbackQueryHandler(show_game_menu, pattern='^main_game$'))
    app.add_handler(CallbackQueryHandler(play_game, pattern=r'^game_play_(rock|scissors|paper)$'))
    
    print("🤖 Bot Pulsa Net (v9.3 - Comprehensive Chat Clearing) sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

