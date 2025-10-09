# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet_secure.py
# Developer: Farid Fauzi
# Versi: 5.4 (Perbaikan Bug Filter & Kelengkapan Data)
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
    # Tri
    {'id': 1, 'name': "Tri Happy 1.5gb 1 Hari", 'price': 4000, 'category': 'Tri', 'type': 'Paket', 'data': '1.5 GB', 'validity': '1 Hari', 'details': 'Kuota 1.5gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 2, 'name': "Tri Happy 2gb 1 Hari", 'price': 4000, 'category': 'Tri', 'type': 'Paket', 'data': '2 GB', 'validity': '1 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 3, 'name': "Tri Happy 2.5gb 1 Hari", 'price': 6000, 'category': 'Tri', 'type': 'Paket', 'data': '2.5 GB', 'validity': '1 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 4, 'name': "Tri Happy 3gb 1 Hari", 'price': 7000, 'category': 'Tri', 'type': 'Paket', 'data': '3 GB', 'validity': '1 Hari', 'details': 'Kuota 3gb, Berlaku Nasional'},
    {'id': 5, 'name': "Tri Happy 1gb 3hari", 'price': 8000, 'category': 'Tri', 'type': 'Paket', 'data': '1 GB', 'validity': '3 Hari', 'details': 'Kuota 1gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 6, 'name': "Tri Happy 5gb 2 Hari", 'price': 9000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '2 Hari', 'details': 'Kuota 5gb, Berlaku Nasional'},
    {'id': 7, 'name': "Tri Happy 1.5gb 7hari", 'price': 10000, 'category': 'Tri', 'type': 'Paket', 'data': '1.5 GB', 'validity': '7 Hari', 'details': 'Kuota 1.5gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 8, 'name': "Tri Happy 5gb 1hari", 'price': 10000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '1 Hari', 'details': 'Kuota 5gb, Berlaku Nasional, 2gb Lokal'},
    {'id': 9, 'name': "Tri Happy 3gb 2hari", 'price': 11000, 'category': 'Tri', 'type': 'Paket', 'data': '3 GB', 'validity': '2 Hari', 'details': 'Kuota 3gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 10, 'name': "Tri Happy 3gb 3hari", 'price': 11000, 'category': 'Tri', 'type': 'Paket', 'data': '3 GB', 'validity': '3 Hari', 'details': 'Kuota 3gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 11, 'name': "Tri Happy 2gb 5hari", 'price': 11000, 'category': 'Tri', 'type': 'Paket', 'data': '2 GB', 'validity': '5 Hari', 'details': 'Kuota 2gb, Berlaku Nasional, 0.5gb Lokal'},
    {'id': 12, 'name': "Tri Happy 6gb 3 Hari", 'price': 14000, 'category': 'Tri', 'type': 'Paket', 'data': '6 GB', 'validity': '3 Hari', 'details': 'Kuota 6gb, Berlaku Nasional'},
    {'id': 13, 'name': "Tri Happy 5gb 3hari", 'price': 15000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '3 Hari', 'details': 'Kuota 5gb, Berlaku Nasional, 1.5gb Lokal'},
    {'id': 14, 'name': "Tri Happy 3.5gb 5hari", 'price': 16000, 'category': 'Tri', 'type': 'Paket', 'data': '3.5 GB', 'validity': '5 Hari', 'details': 'Kuota 3.5gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 15, 'name': "Tri Happy 3gb 7hari", 'price': 16000, 'category': 'Tri', 'type': 'Paket', 'data': '3 GB', 'validity': '7 Hari', 'details': 'Kuota 3gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 16, 'name': "Tri Happy 4.5GB 5hari", 'price': 16000, 'category': 'Tri', 'type': 'Paket', 'data': '4.5 GB', 'validity': '5 Hari', 'details': 'Kuota 4.5gb, Berlaku Nasional'},
    {'id': 17, 'name': "Tri Happy 6gb 5hari", 'price': 20000, 'category': 'Tri', 'type': 'Paket', 'data': '6 GB', 'validity': '5 Hari', 'details': 'Kuota 6gb, Berlaku Nasional, 2gb Lokal'},
    {'id': 18, 'name': "Tri Happy 5gb 7hari", 'price': 20000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': '7 Hari', 'details': 'Kuota 5gb, Berlaku Nasional, 1.5gb Lokal'},
    {'id': 19, 'name': "Tri Happy 3gb 14hari New", 'price': 21000, 'category': 'Tri', 'type': 'Paket', 'data': '3 GB', 'validity': '14 Hari', 'details': 'Kuota 3gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 20, 'name': "Tri Happy 10gb 7 Hari", 'price': 23000, 'category': 'Tri', 'type': 'Paket', 'data': '10 GB', 'validity': '7 Hari', 'details': 'Kuota 10gb, Berlaku Nasional'},
    {'id': 21, 'name': "Tri Happy 6gb 30hari New", 'price': 26000, 'category': 'Tri', 'type': 'Paket', 'data': '6 GB', 'validity': '30 Hari', 'details': 'Kuota 6gb, Berlaku Nasional, 2gb Lokal'},
    {'id': 22, 'name': "Tri Happy 15gb 7 Hari", 'price': 28000, 'category': 'Tri', 'type': 'Paket', 'data': '15 GB', 'validity': '7 Hari', 'details': 'Kuota 15gb, Berlaku Nasional'},
    {'id': 23, 'name': "Tri Happy 7gb 28hari", 'price': 30000, 'category': 'Tri', 'type': 'Paket', 'data': '7 GB', 'validity': '28 Hari', 'details': 'Kuota 7gb, Berlaku Nasional, 2gb Lokal'},
    {'id': 24, 'name': "Tri Happy 9gb 10hari", 'price': 30000, 'category': 'Tri', 'type': 'Paket', 'data': '9 GB', 'validity': '10 Hari', 'details': 'Kuota 9gb, Berlaku Nasional, 1gb Lokal'},
    {'id': 25, 'name': "Tri Happy 10gb 28hari", 'price': 35000, 'category': 'Tri', 'type': 'Paket', 'data': '10 GB', 'validity': '28 Hari', 'details': 'Kuota 10gb, Berlaku Nasional'},
    {'id': 26, 'name': "Tri Happy 11gb 28hari", 'price': 46000, 'category': 'Tri', 'type': 'Paket', 'data': '11 GB', 'validity': '28 Hari', 'details': 'Kuota 11gb, Berlaku Nasional, 6gb Lokal'},
    {'id': 27, 'name': "Tri Happy 15gb 28hari", 'price': 49000, 'category': 'Tri', 'type': 'Paket', 'data': '15 GB', 'validity': '28 Hari', 'details': 'Kuota 15gb, Berlaku Nasional'},
    {'id': 28, 'name': "Tri Happy 30GB 30hari (1GB/hari)", 'price': 51000, 'category': 'Tri', 'type': 'Paket', 'data': '30 GB', 'validity': '30 Hari', 'details': 'Kuota 30GB (1GB/hari), Berlaku Nasional'},
    {'id': 29, 'name': "Tri Happy 18gb 30hari", 'price': 63000, 'category': 'Tri', 'type': 'Paket', 'data': '18 GB', 'validity': '30 Hari', 'details': 'Kuota 18gb, Berlaku Nasional, 10gb Lokal'},
    {'id': 30, 'name': "Tri Happy 42gb 28hari", 'price': 71000, 'category': 'Tri', 'type': 'Paket', 'data': '42 GB', 'validity': '28 Hari', 'details': 'Kuota 42gb, Berlaku Nasional, 8gb Lokal'},
    {'id': 31, 'name': "Tri Happy 60GB 30hari (2GB/hari)", 'price': 84000, 'category': 'Tri', 'type': 'Paket', 'data': '60 GB', 'validity': '30 Hari', 'details': 'Kuota 60GB (2GB/hari), Berlaku Nasional'},
    {'id': 32, 'name': "Tri Happy 45GB 28hari", 'price': 91000, 'category': 'Tri', 'type': 'Paket', 'data': '45 GB', 'validity': '28 Hari', 'details': 'Kuota 45gb, Berlaku Nasional, 5gb Lokal'},
    {'id': 33, 'name': "Tri Happy 55gb 60hari", 'price': 98000, 'category': 'Tri', 'type': 'Paket', 'data': '55 GB', 'validity': '60 Hari', 'details': 'Kuota 55gb, Berlaku Nasional, 10gb Lokal'},
    {'id': 34, 'name': "Tri Happy 150GB 30hari (5GB/hari)", 'price': 109000, 'category': 'Tri', 'type': 'Paket', 'data': '150 GB', 'validity': '30 Hari', 'details': 'Kuota 150GB (5GB/hari), Berlaku Nasional'},
    {'id': 35, 'name': "Tri Happy 100gb 30hari", 'price': 119000, 'category': 'Tri', 'type': 'Paket', 'data': '100 GB', 'validity': '30 Hari', 'details': 'Kuota 100gb, Berlaku Nasional, 20gb Lokal'},
    {'id': 36, 'name': "Tri Happy 300GB (150GB + 150GB Malam)", 'price': 129000, 'category': 'Tri', 'type': 'Paket', 'data': '300 GB', 'validity': '30 Hari', 'details': 'Kuota 150GB + 150GB Kuota Malam (01-06)'},
    {'id': 37, 'name': "Tri Data 1GB 30Hari", 'price': 7000, 'category': 'Tri', 'type': 'Paket', 'data': '1 GB', 'validity': '30 Hari', 'details': 'Kuota 1GB, Berlaku Nasional'},
    {'id': 38, 'name': "Tri Data 1.5GB 30Hari", 'price': 10000, 'category': 'Tri', 'type': 'Paket', 'data': '1.5 GB', 'validity': '30 Hari', 'details': 'Kuota 1.5GB, Berlaku Nasional'},
    {'id': 39, 'name': "Tri Data 2GB 30Hari", 'price': 13000, 'category': 'Tri', 'type': 'Paket', 'data': '2 GB', 'validity': '30 Hari', 'details': 'Kuota 2GB, Berlaku Nasional'},
    {'id': 40, 'name': "Tri Data 2.5gb 30hari", 'price': 16000, 'category': 'Tri', 'type': 'Paket', 'data': '2.5 GB', 'validity': '30 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional'},
    {'id': 41, 'name': "Tri Always On 3.5GB", 'price': 24000, 'category': 'Tri', 'type': 'Paket', 'data': '3.5 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 3.5GB, Masa Aktif Mengikuti Kartu'},
    {'id': 42, 'name': "Tri Always On 4GB (New)", 'price': 26000, 'category': 'Tri', 'type': 'Paket', 'data': '4 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 4GB, Masa Aktif Mengikuti Kartu'},
    {'id': 43, 'name': "Tri Always On 5GB (New)", 'price': 28000, 'category': 'Tri', 'type': 'Paket', 'data': '5 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 5GB, Masa Aktif Mengikuti Kartu'},
    {'id': 44, 'name': "Tri Always On 6GB", 'price': 31000, 'category': 'Tri', 'type': 'Paket', 'data': '6 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 6GB, Masa Aktif Mengikuti Kartu'},
    {'id': 45, 'name': "Tri Always On 9GB", 'price': 44000, 'category': 'Tri', 'type': 'Paket', 'data': '9 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 9GB, Masa Aktif Mengikuti Kartu'},
    {'id': 46, 'name': "Tri Always On 12GB", 'price': 57000, 'category': 'Tri', 'type': 'Paket', 'data': '12 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 12GB, Masa Aktif Mengikuti Kartu'},
    {'id': 47, 'name': "Tri Always On 40gb", 'price': 109000, 'category': 'Tri', 'type': 'Paket', 'data': '40 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 40gb, Masa Aktif Mengikuti Kartu'},
    {'id': 48, 'name': "Tri Unlimited Aplikasi 6GB + 20GB Malam", 'price': 78000, 'category': 'Tri', 'type': 'Paket', 'data': '6 GB + 20 GB', 'validity': 'Unlimited', 'details': 'Kuota Utama 6GB, Kuota Malam 20GB, Unlimited Aplikasi'},
    {'id': 49, 'name': "Tri Pulsa 5.000", 'price': 6000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+5 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 50, 'name': "Tri Pulsa 10.000", 'price': 11000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+10 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 51, 'name': "Tri Pulsa 15.000", 'price': 15000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 15.000'},
    {'id': 52, 'name': "Tri Pulsa 20.000", 'price': 20000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 20.000', 'validity': '+20 Hari', 'details': 'Pulsa Reguler 20.000'},
    {'id': 53, 'name': "Tri Pulsa 25.000", 'price': 25000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+25 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 54, 'name': "Tri Pulsa 30.000", 'price': 30000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 30.000'},
    {'id': 55, 'name': "Tri Pulsa 40.000", 'price': 40000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': '+40 Hari', 'details': 'Pulsa Reguler 40.000'},
    {'id': 56, 'name': "Tri Pulsa 50.000", 'price': 50000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+50 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 57, 'name': "Tri Pulsa 60.000", 'price': 60000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 60.000'},
    {'id': 58, 'name': "Tri Pulsa 70.000", 'price': 70000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 70.000'},
    {'id': 59, 'name': "Tri Pulsa 75.000", 'price': 75000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 75.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 75.000'},
    {'id': 60, 'name': "Tri Pulsa 80.000", 'price': 79000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 80.000'},
    {'id': 61, 'name': "Tri Pulsa 90.000", 'price': 89000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': '+90 Hari', 'details': 'Pulsa Reguler 90.000'},
    {'id': 62, 'name': "Tri Pulsa 100.000", 'price': 99000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+100 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 63, 'name': "Tri Pulsa 125.000", 'price': 125000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 125.000', 'validity': '+125 Hari', 'details': 'Pulsa Reguler 125.000'},
    {'id': 64, 'name': "Tri Pulsa 150.000", 'price': 149000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': '+150 Hari', 'details': 'Pulsa Reguler 150.000'},
    {'id': 65, 'name': "Tri Pulsa 200.000", 'price': 198000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': '+200 Hari', 'details': 'Pulsa Reguler 200.000'},
    {'id': 66, 'name': "Tri Pulsa 250.000", 'price': 247000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 250.000', 'validity': '+250 Hari', 'details': 'Pulsa Reguler 250.000'},
    {'id': 67, 'name': "Tri Pulsa 300.000", 'price': 297000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 300.000', 'validity': '+300 Hari', 'details': 'Pulsa Reguler 300.000'},
    {'id': 68, 'name': "Tri Pulsa 500.000", 'price': 502000, 'category': 'Tri', 'type': 'Pulsa', 'data': 'Rp 500.000', 'validity': '+500 Hari', 'details': 'Pulsa Reguler 500.000'},
    # Axis
    {'id': 69, 'name': "Axis Paket 500mb 30hari", 'price': 4000, 'category': 'Axis', 'type': 'Paket', 'data': '500 MB', 'validity': '30 Hari', 'details': 'Kuota 500Mb, Berlaku Nasional'},
    {'id': 70, 'name': "Axis Paket 1gb 30hari", 'price': 8000, 'category': 'Axis', 'type': 'Paket', 'data': '1 GB', 'validity': '30 Hari', 'details': 'Kuota 1gb, Berlaku Nasional'},
    {'id': 71, 'name': "Axis Paket Bronet 2gb 30hari", 'price': 19000, 'category': 'Axis', 'type': 'Paket', 'data': '2 GB', 'validity': '30 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 72, 'name': "Axis Paket Bronet 3gb 30hari", 'price': 25000, 'category': 'Axis', 'type': 'Paket', 'data': '3 GB', 'validity': '30 Hari', 'details': 'Kuota 3gb, Berlaku Nasional'},
    {'id': 73, 'name': "Axis Paket Bronet 6gb 30hari", 'price': 34000, 'category': 'Axis', 'type': 'Paket', 'data': '6 GB', 'validity': '30 Hari', 'details': 'Kuota 6gb, Berlaku Nasional'},
    {'id': 74, 'name': "Axis Paket Bronet 8gb 30hari", 'price': 39000, 'category': 'Axis', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': 'Kuota 8gb, Berlaku Nasional'},
    {'id': 75, 'name': "Axis Paket Bronet 14gb 30hari", 'price': 58000, 'category': 'Axis', 'type': 'Paket', 'data': '14 GB', 'validity': '30 Hari', 'details': 'Kuota 14gb, Berlaku Nasional'},
    {'id': 76, 'name': "Axis Paket Bronet 20gb 30hari", 'price': 73000, 'category': 'Axis', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20gb, Berlaku Nasional'},
    {'id': 77, 'name': "Axis Paket Bronet 30gb 30hari", 'price': 89000, 'category': 'Axis', 'type': 'Paket', 'data': '30 GB', 'validity': '30 Hari', 'details': 'Kuota 30gb, Berlaku Nasional'},
    {'id': 78, 'name': "Axis Paket Bronet 35gb 60hari", 'price': 104000, 'category': 'Axis', 'type': 'Paket', 'data': '35 GB', 'validity': '60 Hari', 'details': 'Kuota 35gb, Berlaku Nasional'},
    {'id': 79, 'name': "Axis Paket Bronet 75gb 60hari", 'price': 164000, 'category': 'Axis', 'type': 'Paket', 'data': '75 GB', 'validity': '60 Hari', 'details': 'Kuota 75gb, Berlaku Nasional'},
    {'id': 80, 'name': "Axis Paket Bronet Mini 1.5gb 1hari", 'price': 6000, 'category': 'Axis', 'type': 'Paket', 'data': '1.5 GB', 'validity': '1 Hari', 'details': 'Kuota 1.5gb, Berlaku Nasional'},
    {'id': 81, 'name': "Axis Paket Bronet Mini 2.5gb 1hari", 'price': 8000, 'category': 'Axis', 'type': 'Paket', 'data': '2.5 GB', 'validity': '1 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional'},
    {'id': 82, 'name': "Axis Paket Bronet Mini 2gb 3hari", 'price': 9000, 'category': 'Axis', 'type': 'Paket', 'data': '2 GB', 'validity': '3 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 83, 'name': "Axis Paket Bronet Mini 2.5gb 2hari", 'price': 11000, 'category': 'Axis', 'type': 'Paket', 'data': '2.5 GB', 'validity': '2 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional'},
    {'id': 84, 'name': "Axis Paket Bronet Mini 2.5gb 3hari", 'price': 11000, 'category': 'Axis', 'type': 'Paket', 'data': '2.5 GB', 'validity': '3 Hari', 'details': 'Kuota 2.5gb, Berlaku Nasional'},
    {'id': 85, 'name': "Axis Paket Bronet Mini 3gb 3hari", 'price': 11000, 'category': 'Axis', 'type': 'Paket', 'data': '3 GB', 'validity': '3 Hari', 'details': 'Kuota 3gb, Berlaku Nasional'},
    {'id': 86, 'name': "Axis Paket Bronet Mini 2gb 5hari", 'price': 13000, 'category': 'Axis', 'type': 'Paket', 'data': '2 GB', 'validity': '5 Hari', 'details': 'Kuota 2gb, Berlaku Nasional'},
    {'id': 87, 'name': "Axis Paket Bronet Mini 2.5gb 5hari", 'price': 13000, 'category': 'Axis', 'type': 'Paket', 'data': '2.5 GB', 'validity': '5 Hari', 'details': 'Kuota 2.5gb, Jawa Bali'},
    {'id': 88, 'name': "Axis Paket Bronet Mini 4.5gb 3hari", 'price': 14000, 'category': 'Axis', 'type': 'Paket', 'data': '4.5 GB', 'validity': '3 Hari', 'details': 'Kuota 4.5gb, Berlaku Nasional'},
    {'id': 89, 'name': "Axis Paket Bronet Mini 8gb 3hari", 'price': 15000, 'category': 'Axis', 'type': 'Paket', 'data': '8 GB', 'validity': '3 Hari', 'details': 'Kuota 8gb, Berlaku Nasional'},
    {'id': 90, 'name': "Axis Paket Bronet Mini 4gb 5hari", 'price': 16000, 'category': 'Axis', 'type': 'Paket', 'data': '4 GB', 'validity': '5 Hari', 'details': 'Kuota 4gb, Berlaku Nasional'},
    {'id': 91, 'name': "Axis Paket Bronet Mini 7.5gb 5hari", 'price': 22000, 'category': 'Axis', 'type': 'Paket', 'data': '7.5 GB', 'validity': '5 Hari', 'details': 'Kuota 7.5gb, Berlaku Nasional'},
    {'id': 92, 'name': "Axis Paket Bronet Mini 7gb 5hari", 'price': 23000, 'category': 'Axis', 'type': 'Paket', 'data': '7 GB', 'validity': '5 Hari', 'details': 'Kuota 7gb, Berlaku Nasional'},
    {'id': 93, 'name': "Axis Paket Bronet Mini 3.5gb 7hari", 'price': 23000, 'category': 'Axis', 'type': 'Paket', 'data': '3.5 GB', 'validity': '7 Hari', 'details': 'Kuota 3.5gb, Berlaku Nasional'},
    {'id': 94, 'name': "Axis Paket Bronet Mini 7gb 7hari", 'price': 23000, 'category': 'Axis', 'type': 'Paket', 'data': '7 GB', 'validity': '7 Hari', 'details': 'Kuota 7gb, Berlaku Nasional'},
    {'id': 95, 'name': "Axis Paket Bronet Mini 8.5gb 7hari", 'price': 26000, 'category': 'Axis', 'type': 'Paket', 'data': '8.5 GB', 'validity': '7 Hari', 'details': 'Kuota 8.5gb, Berlaku Nasional'},
    {'id': 96, 'name': "Axis Paket Bronet Mini 12gb 5hari", 'price': 27000, 'category': 'Axis', 'type': 'Paket', 'data': '12 GB', 'validity': '5 Hari', 'details': 'Kuota 12gb, Berlaku Nasional'},
    {'id': 97, 'name': "Axis Paket Bronet Mini 4gb 15hari", 'price': 28000, 'category': 'Axis', 'type': 'Paket', 'data': '4 GB', 'validity': '15 Hari', 'details': 'Kuota 4gb, Berlaku Nasional'},
    {'id': 98, 'name': "Axis Paket Bronet Mini 5gb 15hari", 'price': 28000, 'category': 'Axis', 'type': 'Paket', 'data': '5 GB', 'validity': '15 Hari', 'details': 'Kuota 5gb, Berlaku Nasional'},
    {'id': 99, 'name': "Axis Paket Bronet Mini 11gb 7hari", 'price': 29000, 'category': 'Axis', 'type': 'Paket', 'data': '11 GB', 'validity': '7 Hari', 'details': 'Kuota 11gb, Berlaku Nasional'},
    {'id': 100, 'name': "Axis Paket Bronet Mini 24gb 7hari", 'price': 40000, 'category': 'Axis', 'type': 'Paket', 'data': '24 GB', 'validity': '7 Hari', 'details': 'Kuota 24gb, Berlaku Nasional'},
    {'id': 101, 'name': "Axis Paket Bronet Mini 8gb 15hari", 'price': 42000, 'category': 'Axis', 'type': 'Paket', 'data': '8 GB', 'validity': '15 Hari', 'details': 'Kuota 8gb, Berlaku Nasional'},
    {'id': 102, 'name': "Axis Paket Bronet Mini 11.5gb 15hari", 'price': 42000, 'category': 'Axis', 'type': 'Paket', 'data': '11.5 GB', 'validity': '15 Hari', 'details': 'Kuota 11.5gb, Berlaku Nasional'},
    {'id': 103, 'name': "Axis Paket Bronet Mini 30gb 15hari", 'price': 72000, 'category': 'Axis', 'type': 'Paket', 'data': '30 GB', 'validity': '15 Hari', 'details': 'Kuota 30gb, Berlaku Nasional'},
    {'id': 104, 'name': "Axis Pulsa 5.000", 'price': 6000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 105, 'name': "Axis Pulsa 10.000", 'price': 11000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 106, 'name': "Axis Pulsa 15.000", 'price': 16000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': '+20 Hari', 'details': 'Pulsa Reguler 15.000'},
    {'id': 107, 'name': "Axis Pulsa 25.000", 'price': 25000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 108, 'name': "Axis Pulsa 30.000", 'price': 30000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': '+35 Hari', 'details': 'Pulsa Reguler 30.000'},
    {'id': 109, 'name': "Axis Pulsa 40.000", 'price': 41000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': '+40 Hari', 'details': 'Pulsa Reguler 40.000'},
    {'id': 110, 'name': "Axis Pulsa 50.000", 'price': 50000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 111, 'name': "Axis Pulsa 60.000", 'price': 60000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 60.000'},
    {'id': 112, 'name': "Axis Pulsa 70.000", 'price': 70000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 70.000'},
    {'id': 113, 'name': "Axis Pulsa 80.000", 'price': 80000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 80.000'},
    {'id': 114, 'name': "Axis Pulsa 90.000", 'price': 90000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 90.000'},
    {'id': 115, 'name': "Axis Pulsa 100.000", 'price': 100000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 116, 'name': "Axis Pulsa 150.000", 'price': 150000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': '+90 Hari', 'details': 'Pulsa Reguler 150.000'},
    {'id': 117, 'name': "Axis Pulsa 200.000", 'price': 200000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': '+120 Hari', 'details': 'Pulsa Reguler 200.000'},
    {'id': 118, 'name': "Axis Pulsa 300.000", 'price': 300000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 300.000', 'validity': '+180 Hari', 'details': 'Pulsa Reguler 300.000'},
    {'id': 119, 'name': "Axis Pulsa 500.000", 'price': 508000, 'category': 'Axis', 'type': 'Pulsa', 'data': 'Rp 500.000', 'validity': '+240 Hari', 'details': 'Pulsa Reguler 500.000'},
    # By.U
    {'id': 120, 'name': "By.U Paket Data Harian 1GB 1Hari", 'price': 5000, 'category': 'By.U', 'type': 'Paket', 'data': '1 GB', 'validity': '1 Hari', 'details': 'Kuota 1GB, Nasional'},
    {'id': 121, 'name': "By.U Paket Data Harian 2GB 1Hari", 'price': 8000, 'category': 'By.U', 'type': 'Paket', 'data': '2 GB', 'validity': '1 Hari', 'details': 'Kuota 2GB, Nasional'},
    {'id': 122, 'name': "By.U Paket Data Harian 3GB 3Hari", 'price': 9000, 'category': 'By.U', 'type': 'Paket', 'data': '3 GB', 'validity': '3 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 123, 'name': "By.U Paket Data Mingguan 4GB 7Hari", 'price': 12000, 'category': 'By.U', 'type': 'Paket', 'data': '4 GB', 'validity': '7 Hari', 'details': 'Kuota 4GB, Nasional'},
    {'id': 124, 'name': "By.U Paket Data Harian 2.5GB 5Hari", 'price': 12000, 'category': 'By.U', 'type': 'Paket', 'data': '2.5 GB', 'validity': '5 Hari', 'details': 'Kuota 2.5GB, Nasional'},
    {'id': 125, 'name': "By.U Paket Data Harian 3GB 7Hari", 'price': 14000, 'category': 'By.U', 'type': 'Paket', 'data': '3 GB', 'validity': '7 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 126, 'name': "By.U Paket Data Mingguan 3GB 14Hari", 'price': 17000, 'category': 'By.U', 'type': 'Paket', 'data': '3 GB', 'validity': '14 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 127, 'name': "Promo By.U Paket Data Mingguan 7GB 20Hari", 'price': 17000, 'category': 'By.U', 'type': 'Paket', 'data': '7 GB', 'validity': '20 Hari', 'details': 'Kuota 7GB, Nasional'},
    {'id': 128, 'name': "By.U Paket Data Mingguan 5GB 7Hari", 'price': 19000, 'category': 'By.U', 'type': 'Paket', 'data': '5 GB', 'validity': '7 Hari', 'details': 'Kuota 5GB, Nasional'},
    {'id': 129, 'name': "Promo By.U Paket Data Bulanan 9GB 30Hari", 'price': 27000, 'category': 'By.U', 'type': 'Paket', 'data': '9 GB', 'validity': '30 Hari', 'details': 'Kuota 9GB, Nasional'},
    {'id': 130, 'name': "By.U Paket Data Bulanan 6GB 30Hari", 'price': 31000, 'category': 'By.U', 'type': 'Paket', 'data': '6 GB', 'validity': '30 Hari', 'details': 'Kuota 6GB, Nasional'},
    {'id': 131, 'name': "Promo By.U Paket Data Bulanan 14GB 30Hari", 'price': 37000, 'category': 'By.U', 'type': 'Paket', 'data': '14 GB', 'validity': '30 Hari', 'details': 'Kuota 14GB, Nasional'},
    {'id': 132, 'name': "Promo By.U Paket Data Bulanan 20GB 30Hari", 'price': 47000, 'category': 'By.U', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': 'Kuota 20GB, Nasional'},
    {'id': 133, 'name': "By.U Paket Data Bulanan 12GB 30Hari", 'price': 52000, 'category': 'By.U', 'type': 'Paket', 'data': '12 GB', 'validity': '30 Hari', 'details': 'Kuota 12GB, Nasional'},
    {'id': 134, 'name': "Promo By.U Paket Data Bulanan 42GB 30Hari", 'price': 76000, 'category': 'By.U', 'type': 'Paket', 'data': '42 GB', 'validity': '30 Hari', 'details': 'Kuota 42GB, Nasional'},
    {'id': 135, 'name': "Promo By.U Paket Data Bulanan 65GB 30Hari", 'price': 102000, 'category': 'By.U', 'type': 'Paket', 'data': '65 GB', 'validity': '30 Hari', 'details': 'Kuota 65GB, Nasional'},
    {'id': 136, 'name': "By.U Paket Data Bulanan 50GB 30Hari", 'price': 123000, 'category': 'By.U', 'type': 'Paket', 'data': '50 GB', 'validity': '30 Hari', 'details': 'Kuota 50GB, Nasional'},
    {'id': 137, 'name': "By.U Paket Data Bulanan 75GB 30Hari", 'price': 155000, 'category': 'By.U', 'type': 'Paket', 'data': '75 GB', 'validity': '30 Hari', 'details': 'Kuota 75GB, Nasional'},
    {'id': 138, 'name': "By.U Pulsa 2.000", 'price': 3000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 2.000', 'validity': 'N/A', 'details': 'Pulsa By.U 2.000'},
    {'id': 139, 'name': "By.U Pulsa 3.000", 'price': 4000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 3.000', 'validity': 'N/A', 'details': 'Pulsa By.U 3.000'},
    {'id': 140, 'name': "By.U Pulsa 4.000", 'price': 5000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 4.000', 'validity': 'N/A', 'details': 'Pulsa By.U 4.000'},
    {'id': 141, 'name': "By.U Pulsa 5.000", 'price': 6000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': 'N/A', 'details': 'Pulsa By.U 5.000'},
    {'id': 142, 'name': "By.U Pulsa 10.000", 'price': 11000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': 'N/A', 'details': 'Pulsa By.U 10.000'},
    {'id': 143, 'name': "By.U Pulsa 15.000", 'price': 16000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': 'N/A', 'details': 'Pulsa By.U 15.000'},
    {'id': 144, 'name': "By.U Pulsa 20.000", 'price': 21000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 20.000', 'validity': 'N/A', 'details': 'Pulsa By.U 20.000'},
    {'id': 145, 'name': "By.U Pulsa 25.000", 'price': 25000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': 'N/A', 'details': 'Pulsa By.U 25.000'},
    {'id': 146, 'name': "By.U Pulsa 30.000", 'price': 30000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': 'N/A', 'details': 'Pulsa By.U 30.000'},
    {'id': 147, 'name': "By.U Pulsa 40.000", 'price': 41000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': 'N/A', 'details': 'Pulsa By.U 40.000'},
    {'id': 148, 'name': "By.U Pulsa 50.000", 'price': 50000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': 'N/A', 'details': 'Pulsa By.U 50.000'},
    {'id': 149, 'name': "By.U Pulsa 55.000", 'price': 56000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 55.000', 'validity': 'N/A', 'details': 'Pulsa By.U 55.000'},
    {'id': 150, 'name': "By.U Pulsa 60.000", 'price': 61000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': 'N/A', 'details': 'Pulsa By.U 60.000'},
    {'id': 151, 'name': "By.U Pulsa 70.000", 'price': 71000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': 'N/A', 'details': 'Pulsa By.U 70.000'},
    {'id': 152, 'name': "By.U Pulsa 75.000", 'price': 76000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 75.000', 'validity': 'N/A', 'details': 'Pulsa By.U 75.000'},
    {'id': 153, 'name': "By.U Pulsa 80.000", 'price': 81000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': 'N/A', 'details': 'Pulsa By.U 80.000'},
    {'id': 154, 'name': "By.U Pulsa 85.000", 'price': 86000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 85.000', 'validity': 'N/A', 'details': 'Pulsa By.U 85.000'},
    {'id': 155, 'name': "By.U Pulsa 90.000", 'price': 91000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': 'N/A', 'details': 'Pulsa By.U 90.000'},
    {'id': 156, 'name': "By.U Pulsa 95.000", 'price': 96000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 95.000', 'validity': 'N/A', 'details': 'Pulsa By.U 95.000'},
    {'id': 157, 'name': "By.U Pulsa 100.000", 'price': 100000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': 'N/A', 'details': 'Pulsa By.U 100.000'},
    {'id': 158, 'name': "By.U Pulsa 150.000", 'price': 151000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': 'N/A', 'details': 'Pulsa By.U 150.000'},
    {'id': 159, 'name': "By.U Pulsa 200.000", 'price': 203000, 'category': 'By.U', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': 'N/A', 'details': 'Pulsa By.U 200.000'},
    # Indosat
    {'id': 160, 'name': "Freedom U 5.5GB 30Hari", 'price': 34000, 'category': 'Indosat', 'type': 'Paket', 'data': '5.5 GB', 'validity': '30 Hari', 'details': '1GB Kuota Utama, 2GB Kuota Apps'},
    {'id': 161, 'name': "Freedom U 10GB 30Hari", 'price': 56000, 'category': 'Indosat', 'type': 'Paket', 'data': '10 GB', 'validity': '30 Hari', 'details': '2GB Kuota Utama, 8GB Kuota Apps'},
    {'id': 162, 'name': "Freedom U 20GB 30Hari", 'price': 80000, 'category': 'Indosat', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': '3GB Kuota Utama, 17GB Kuota Apps'},
    {'id': 163, 'name': "Freedom U 35GB 30Hari", 'price': 103000, 'category': 'Indosat', 'type': 'Paket', 'data': '35 GB', 'validity': '30 Hari', 'details': '7GB Kuota Utama, 28GB Kuota Apps'},
    {'id': 164, 'name': "Freedom U 45GB 30Hari", 'price': 115000, 'category': 'Indosat', 'type': 'Paket', 'data': '45 GB', 'validity': '30 Hari', 'details': '10GB Kuota Utama, 35GB Kuota Apps'},
    {'id': 165, 'name': "Freedom U JUMBO 90GB 30Hari", 'price': 156000, 'category': 'Indosat', 'type': 'Paket', 'data': '90 GB', 'validity': '30 Hari', 'details': '90GB Kuota Utama, Bonus SMS/Telp'},
    {'id': 166, 'name': "Freedom Combo 6GB", 'price': 34000, 'category': 'Indosat', 'type': 'Paket', 'data': '6 GB', 'validity': '30 Hari', 'details': '4GB All Jaringan, 2GB Malam, Bonus Nelpon'},
    {'id': 167, 'name': "Freedom Combo 10GB", 'price': 46000, 'category': 'Indosat', 'type': 'Paket', 'data': '10 GB', 'validity': '30 Hari', 'details': '7GB All Jaringan, 3GB Malam, Bonus Nelpon'},
    {'id': 168, 'name': "Freedom Combo 20GB", 'price': 72000, 'category': 'Indosat', 'type': 'Paket', 'data': '20 GB', 'validity': '30 Hari', 'details': '15GB All Jaringan, 5GB Malam, Bonus Nelpon'},
    {'id': 169, 'name': "Freedom Combo 30GB", 'price': 94000, 'category': 'Indosat', 'type': 'Paket', 'data': '30 GB', 'validity': '30 Hari', 'details': '23GB All Jaringan, 7GB Malam, Bonus Nelpon'},
    {'id': 170, 'name': "Freedom Internet 1.5GB 1Hari", 'price': 5000, 'category': 'Indosat', 'type': 'Paket', 'data': '1.5 GB', 'validity': '1 Hari', 'details': 'Kuota 1.5GB, Nasional'},
    {'id': 171, 'name': "Freedom Internet 1GB 2Hari", 'price': 6000, 'category': 'Indosat', 'type': 'Paket', 'data': '1 GB', 'validity': '2 Hari', 'details': 'Kuota 1GB, Nasional'},
    {'id': 172, 'name': "Freedom Internet 3GB 1Hari", 'price': 7000, 'category': 'Indosat', 'type': 'Paket', 'data': '3 GB', 'validity': '1 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 173, 'name': "Freedom Internet 5GB 2Hari", 'price': 9000, 'category': 'Indosat', 'type': 'Paket', 'data': '5 GB', 'validity': '2 Hari', 'details': 'Kuota 5GB, Nasional'},
    {'id': 174, 'name': "Freedom Internet 3GB 3Hari", 'price': 12000, 'category': 'Indosat', 'type': 'Paket', 'data': '3 GB', 'validity': '3 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 175, 'name': "Freedom Internet 2.5GB 5Hari", 'price': 13000, 'category': 'Indosat', 'type': 'Paket', 'data': '2.5 GB', 'validity': '5 Hari', 'details': 'Kuota 2.5GB, Nasional'},
    {'id': 176, 'name': "Freedom Internet 3.5GB 5Hari", 'price': 14000, 'category': 'Indosat', 'type': 'Paket', 'data': '3.5 GB', 'validity': '5 Hari', 'details': 'Kuota 3.5GB, Nasional'},
    {'id': 177, 'name': "Freedom Internet 5GB 5Hari", 'price': 17000, 'category': 'Indosat', 'type': 'Paket', 'data': '5 GB', 'validity': '5 Hari', 'details': 'Kuota 5GB, Nasional'},
    {'id': 178, 'name': "Freedom Internet 5GB 3Hari", 'price': 20000, 'category': 'Indosat', 'type': 'Paket', 'data': '5 GB', 'validity': '3 Hari', 'details': 'Kuota 5GB, Nasional'},
    {'id': 179, 'name': "Freedom Internet 3GB 14Hari", 'price': 20000, 'category': 'Indosat', 'type': 'Paket', 'data': '3 GB', 'validity': '14 Hari', 'details': 'Kuota 3GB, Nasional'},
    {'id': 180, 'name': "Freedom Internet 7GB 7Hari", 'price': 24000, 'category': 'Indosat', 'type': 'Paket', 'data': '7 GB', 'validity': '7 Hari', 'details': 'Kuota 7GB, Nasional'},
    {'id': 181, 'name': "Freedom Internet 6GB 28Hari", 'price': 26000, 'category': 'Indosat', 'type': 'Paket', 'data': '6 GB', 'validity': '28 Hari', 'details': 'Kuota 6GB, Nasional'},
    {'id': 182, 'name': "Freedom Internet 15GB 7Hari", 'price': 30000, 'category': 'Indosat', 'type': 'Paket', 'data': '15 GB', 'validity': '7 Hari', 'details': 'Kuota 15GB, Nasional'},
    {'id': 183, 'name': "Freedom Internet 6.5GB 28Hari", 'price': 32000, 'category': 'Indosat', 'type': 'Paket', 'data': '6.5 GB', 'validity': '28 Hari', 'details': 'Kuota 6.5GB, Nasional'},
    {'id': 184, 'name': "Freedom Internet 7GB 28Hari", 'price': 34000, 'category': 'Indosat', 'type': 'Paket', 'data': '7 GB', 'validity': '28 Hari', 'details': 'Kuota 7GB, Nasional'},
    {'id': 185, 'name': "Freedom Internet 9GB 28Hari", 'price': 43000, 'category': 'Indosat', 'type': 'Paket', 'data': '9 GB', 'validity': '28 Hari', 'details': 'Kuota 9GB, Nasional'},
    {'id': 186, 'name': "Freedom Internet 13GB 28Hari", 'price': 52000, 'category': 'Indosat', 'type': 'Paket', 'data': '13 GB', 'validity': '28 Hari', 'details': 'Kuota 13GB, Nasional'},
    {'id': 187, 'name': "Freedom Internet 20GB 28Hari", 'price': 76000, 'category': 'Indosat', 'type': 'Paket', 'data': '20 GB', 'validity': '28 Hari', 'details': 'Kuota 20GB, Nasional'},
    {'id': 188, 'name': "Freedom Internet 30GB 28Hari", 'price': 90000, 'category': 'Indosat', 'type': 'Paket', 'data': '30 GB', 'validity': '28 Hari', 'details': 'Kuota 30GB, Nasional'},
    {'id': 189, 'name': "Freedom Internet 52GB 28Hari", 'price': 113000, 'category': 'Indosat', 'type': 'Paket', 'data': '52 GB', 'validity': '28 Hari', 'details': 'Kuota 52GB, Nasional'},
    {'id': 190, 'name': "Freedom Internet 70GB 28Hari", 'price': 121000, 'category': 'Indosat', 'type': 'Paket', 'data': '70 GB', 'validity': '28 Hari', 'details': 'Kuota 70GB, Nasional'},
    {'id': 191, 'name': "Freedom Internet 100GB 28Hari", 'price': 130000, 'category': 'Indosat', 'type': 'Paket', 'data': '100 GB', 'validity': '28 Hari', 'details': 'Kuota 100GB, Nasional'},
    {'id': 192, 'name': "Freedom Internet 150GB 28Hari", 'price': 140000, 'category': 'Indosat', 'type': 'Paket', 'data': '150 GB', 'validity': '28 Hari', 'details': 'Kuota 150GB, Nasional'},
    {'id': 193, 'name': "Freedom Internet 200GB 28Hari", 'price': 191000, 'category': 'Indosat', 'type': 'Paket', 'data': '200 GB', 'validity': '28 Hari', 'details': 'Kuota 200GB, Nasional'},
    {'id': 194, 'name': "Indosat Pulsa 5.000", 'price': 7000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 195, 'name': "Indosat Pulsa 10.000", 'price': 12000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 196, 'name': "Indosat Pulsa 12.000", 'price': 14000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 12.000', 'validity': '+18 Hari', 'details': 'Pulsa Reguler 12.000'},
    {'id': 197, 'name': "Indosat Pulsa 15.000", 'price': 16000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': '+20 Hari', 'details': 'Pulsa Reguler 15.000'},
    {'id': 198, 'name': "Indosat Pulsa 20.000", 'price': 21000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 20.000', 'validity': '+24 Hari', 'details': 'Pulsa Reguler 20.000'},
    {'id': 199, 'name': "Indosat Pulsa 25.000", 'price': 26000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 200, 'name': "Indosat Pulsa 30.000", 'price': 31000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': '+33 Hari', 'details': 'Pulsa Reguler 30.000'},
    {'id': 201, 'name': "Indosat Pulsa 40.000", 'price': 41000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': '+36 Hari', 'details': 'Pulsa Reguler 40.000'},
    {'id': 202, 'name': "Indosat Pulsa 50.000", 'price': 50000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 203, 'name': "Indosat Pulsa 60.000", 'price': 60000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': '+50 Hari', 'details': 'Pulsa Reguler 60.000'},
    {'id': 204, 'name': "Indosat Pulsa 70.000", 'price': 70000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': '+50 Hari', 'details': 'Pulsa Reguler 70.000'},
    {'id': 205, 'name': "Indosat Pulsa 80.000", 'price': 80000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': '+55 Hari', 'details': 'Pulsa Reguler 80.000'},
    {'id': 206, 'name': "Indosat Pulsa 90.000", 'price': 90000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 90.000'},
    {'id': 207, 'name': "Indosat Pulsa 100.000", 'price': 100000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 208, 'name': "Indosat Pulsa 115.000", 'price': 115000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 115.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 115.000'},
    {'id': 209, 'name': "Indosat Pulsa 125.000", 'price': 125000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 125.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 125.000'},
    {'id': 210, 'name': "Indosat Pulsa 150.000", 'price': 149000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 150.000'},
    {'id': 211, 'name': "Indosat Pulsa 175.000", 'price': 174000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 175.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 175.000'},
    {'id': 212, 'name': "Indosat Pulsa 200.000", 'price': 198000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 200.000'},
    {'id': 213, 'name': "Indosat Pulsa 250.000", 'price': 248000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 250.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 250.000'},
    {'id': 214, 'name': "Indosat Pulsa 300.000", 'price': 298000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 300.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 300.000'},
    {'id': 215, 'name': "Indosat Pulsa 400.000", 'price': 396000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 400.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 400.000'},
    {'id': 216, 'name': "Indosat Pulsa 500.000", 'price': 503000, 'category': 'Indosat', 'type': 'Pulsa', 'data': 'Rp 500.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 500.000'},
    # XL
    {'id': 217, 'name': "XL Flex S Kuota 3.5GB 21Hari", 'price': 20000, 'category': 'XL', 'type': 'Paket', 'data': '3.5 GB', 'validity': '21 Hari', 'details': '3.5GB Nasional, Hingga 1GB Lokal'},
    {'id': 218, 'name': "XL Flex S-Old Kuota 3.5GB 28Hari", 'price': 22000, 'category': 'XL', 'type': 'Paket', 'data': '3.5 GB', 'validity': '28 Hari', 'details': '3.5GB Nasional, Hingga 1GB Lokal'},
    {'id': 219, 'name': "XL Flex S Kuota 5GB 28Hari", 'price': 27000, 'category': 'XL', 'type': 'Paket', 'data': '5 GB', 'validity': '28 Hari', 'details': '5GB Nasional, Hingga 3GB Lokal, Nelpon 5 Menit'},
    {'id': 220, 'name': "XL Flex S Plus Kuota 7GB 28Hari", 'price': 33000, 'category': 'XL', 'type': 'Paket', 'data': '7 GB', 'validity': '28 Hari', 'details': '7GB Nasional, Hingga 3.5GB Lokal, Nelpon 5 Menit'},
    {'id': 221, 'name': "XL Flex M Kuota 10GB 28Hari", 'price': 45000, 'category': 'XL', 'type': 'Paket', 'data': '10 GB', 'validity': '28 Hari', 'details': '10GB Nasional, Hingga 5GB Lokal, Nelpon 5 Menit'},
    {'id': 222, 'name': "XL Flex M Plus Kuota 14GB 28Hari", 'price': 55000, 'category': 'XL', 'type': 'Paket', 'data': '14 GB', 'validity': '28 Hari', 'details': '14GB Nasional, Hingga 6GB Lokal, Nelpon 5 Menit'},
    {'id': 223, 'name': "XL Flex L Kuota 18GB 28Hari", 'price': 65000, 'category': 'XL', 'type': 'Paket', 'data': '18 GB', 'validity': '28 Hari', 'details': '18GB Nasional, Hingga 9GB Lokal, Nelpon 5 Menit'},
    {'id': 224, 'name': "XL Flex L Plus Kuota 26GB 28Hari", 'price': 75000, 'category': 'XL', 'type': 'Paket', 'data': '26 GB', 'validity': '28 Hari', 'details': '26GB Nasional, Hingga 11GB Lokal, Nelpon 5 Menit'},
    {'id': 225, 'name': "XL Flex XL Kuota 32GB 28Hari", 'price': 91000, 'category': 'XL', 'type': 'Paket', 'data': '32 GB', 'validity': '28 Hari', 'details': '32GB Nasional, Hingga 11GB Lokal, Nelpon 5 Menit'},
    {'id': 226, 'name': "XL Flex XXL Kuota 65GB 28Hari", 'price': 125000, 'category': 'XL', 'type': 'Paket', 'data': '65 GB', 'validity': '28 Hari', 'details': '65GB Nasional, Hingga 25GB Lokal, Nelpon 5 Menit'},
    {'id': 227, 'name': "XL Hotrod 1Gb 2Hari", 'price': 5000, 'category': 'XL', 'type': 'Paket', 'data': '1 GB', 'validity': '2 Hari', 'details': 'Kuota 1Gb'},
    {'id': 228, 'name': "XL Hotrod 500Mb 7Hari", 'price': 6000, 'category': 'XL', 'type': 'Paket', 'data': '500 MB', 'validity': '7 Hari', 'details': 'Kuota 500MB'},
    {'id': 229, 'name': "XL Hotrod 1Gb 7Hari", 'price': 10000, 'category': 'XL', 'type': 'Paket', 'data': '1 GB', 'validity': '7 Hari', 'details': 'Kuota 1Gb'},
    {'id': 230, 'name': "XL Hotrod 1.5Gb 3Hari", 'price': 11000, 'category': 'XL', 'type': 'Paket', 'data': '1.5 GB', 'validity': '3 Hari', 'details': 'Kuota 1.5Gb'},
    {'id': 231, 'name': "XL Hotrod 2Gb 7Hari", 'price': 18000, 'category': 'XL', 'type': 'Paket', 'data': '2 GB', 'validity': '7 Hari', 'details': 'Kuota 2Gb'},
    {'id': 232, 'name': "XL Hotrod 3Gb 7Hari", 'price': 23000, 'category': 'XL', 'type': 'Paket', 'data': '3 GB', 'validity': '7 Hari', 'details': 'Kuota 3Gb'},
    {'id': 233, 'name': "XL Kuota 500MB 28Hari", 'price': 4000, 'category': 'XL', 'type': 'Paket', 'data': '500 MB', 'validity': '28 Hari', 'details': 'Kuota 500Mb'},
    {'id': 234, 'name': "XL Kuota 1GB 28Hari", 'price': 8000, 'category': 'XL', 'type': 'Paket', 'data': '1 GB', 'validity': '28 Hari', 'details': 'Kuota 1GB'},
    {'id': 235, 'name': "XL Kuota 2GB 28Hari", 'price': 14000, 'category': 'XL', 'type': 'Paket', 'data': '2 GB', 'validity': '28 Hari', 'details': 'Kuota 2GB'},
    {'id': 236, 'name': "XL Kuota 3GB 28Hari", 'price': 22000, 'category': 'XL', 'type': 'Paket', 'data': '3 GB', 'validity': '28 Hari', 'details': 'Kuota 3GB, Extra Bonus'},
    {'id': 237, 'name': "XL Kuota 5GB 28Hari", 'price': 27000, 'category': 'XL', 'type': 'Paket', 'data': '5 GB', 'validity': '28 Hari', 'details': 'Kuota 5GB, Extra Bonus'},
    {'id': 238, 'name': "XL Kuota 7GB 28Hari", 'price': 33000, 'category': 'XL', 'type': 'Paket', 'data': '7 GB', 'validity': '28 Hari', 'details': 'Kuota 7GB, Extra Bonus'},
    {'id': 239, 'name': "XL Kuota 10GB 28Hari", 'price': 45000, 'category': 'XL', 'type': 'Paket', 'data': '10 GB', 'validity': '28 Hari', 'details': 'Kuota 10GB, Extra Bonus'},
    {'id': 240, 'name': "XL Kuota 14GB 28Hari", 'price': 55000, 'category': 'XL', 'type': 'Paket', 'data': '14 GB', 'validity': '28 Hari', 'details': 'Kuota 14GB, Extra Bonus'},
    {'id': 241, 'name': "XL Kuota 18GB 28Hari", 'price': 65000, 'category': 'XL', 'type': 'Paket', 'data': '18 GB', 'validity': '28 Hari', 'details': 'Kuota 18GB, Extra Bonus'},
    {'id': 242, 'name': "XL Kuota 26GB 28Hari", 'price': 75000, 'category': 'XL', 'type': 'Paket', 'data': '26 GB', 'validity': '28 Hari', 'details': 'Kuota 26GB, Extra Bonus'},
    {'id': 243, 'name': "XL Kuota 32GB 28Hari", 'price': 93000, 'category': 'XL', 'type': 'Paket', 'data': '32 GB', 'validity': '28 Hari', 'details': 'Kuota 32GB, Extra Bonus'},
    {'id': 244, 'name': "XL Xtra On 1GB", 'price': 15000, 'category': 'XL', 'type': 'Paket', 'data': '1 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 1Gb, Masa Aktif Unlimited'},
    {'id': 245, 'name': "XL Xtra On 2GB", 'price': 24000, 'category': 'XL', 'type': 'Paket', 'data': '2 GB', 'validity': 'Aktif Selalu', 'details': 'Kuota 2Gb, Masa Aktif Unlimited'},
    {'id': 246, 'name': "XL Pulsa 5.000", 'price': 6000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': '+7 Hari', 'details': 'Pulsa Reguler 5.000'},
    {'id': 247, 'name': "XL Pulsa 10.000", 'price': 11000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': '+15 Hari', 'details': 'Pulsa Reguler 10.000'},
    {'id': 248, 'name': "XL Pulsa 15.000", 'price': 16000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': '+20 Hari', 'details': 'Pulsa Reguler 15.000'},
    {'id': 249, 'name': "XL Pulsa 25.000", 'price': 25000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': '+30 Hari', 'details': 'Pulsa Reguler 25.000'},
    {'id': 250, 'name': "XL Pulsa 30.000", 'price': 30000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': '+35 Hari', 'details': 'Pulsa Reguler 30.000'},
    {'id': 251, 'name': "XL Pulsa 40.000", 'price': 41000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': '+40 Hari', 'details': 'Pulsa Reguler 40.000'},
    {'id': 252, 'name': "XL Pulsa 50.000", 'price': 50000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 50.000'},
    {'id': 253, 'name': "XL Pulsa 60.000", 'price': 60000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 60.000'},
    {'id': 254, 'name': "XL Pulsa 70.000", 'price': 70000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 70.000'},
    {'id': 255, 'name': "XL Pulsa 80.000", 'price': 80000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 80.000'},
    {'id': 256, 'name': "XL Pulsa 90.000", 'price': 90000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': '+45 Hari', 'details': 'Pulsa Reguler 90.000'},
    {'id': 257, 'name': "XL Pulsa 100.000", 'price': 100000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': '+60 Hari', 'details': 'Pulsa Reguler 100.000'},
    {'id': 258, 'name': "XL Pulsa 150.000", 'price': 150000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': '+90 Hari', 'details': 'Pulsa Reguler 150.000'},
    {'id': 259, 'name': "XL Pulsa 200.000", 'price': 200000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': '+120 Hari', 'details': 'Pulsa Reguler 200.000'},
    {'id': 260, 'name': "XL Pulsa 300.000", 'price': 300000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 300.000', 'validity': '+180 Hari', 'details': 'Pulsa Reguler 300.000'},
    {'id': 261, 'name': "XL Pulsa 500.000", 'price': 508000, 'category': 'XL', 'type': 'Pulsa', 'data': 'Rp 500.000', 'validity': '+240 Hari', 'details': 'Pulsa Reguler 500.000'},
    # Telkomsel
    {'id': 262, 'name': "Telkomsel 100mb 7 Hari", 'price': 6000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '100 MB', 'validity': '7 Hari', 'details': '100mb, Semua Zona & Jaringan'},
    {'id': 263, 'name': "Telkomsel 250mb 7 Hari", 'price': 7000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '250 MB', 'validity': '7 Hari', 'details': '250mb, Semua Zona & Jaringan'},
    {'id': 264, 'name': "Telkomsel 500mb 7 Hari", 'price': 9000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '500 MB', 'validity': '7 Hari', 'details': '500mb, Semua Zona & Jaringan'},
    {'id': 265, 'name': "Telkomsel 1.5gb + Bonus Extra 30 Hari", 'price': 25000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '1.5 GB', 'validity': '30 Hari', 'details': '1.5gb + Bonus Extra Kuota'},
    {'id': 266, 'name': "Promo Tsel 3gb + Bonus Extra 30 Hari", 'price': 26000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '3 GB', 'validity': '30 Hari', 'details': '3gb + Bonus Extra Kuota'},
    {'id': 267, 'name': "Promo Tsel 5gb + Bonus Extra 30 Hari", 'price': 46000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '5 GB', 'validity': '30 Hari', 'details': '5gb + Bonus Extra Kuota'},
    {'id': 268, 'name': "Tsel 5gb + Bonus Extra 30 Hari", 'price': 50000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '5 GB', 'validity': '30 Hari', 'details': '5gb + Bonus Extra Kuota'},
    {'id': 269, 'name': "Promo Tsel 6.5gb + Bonus Extra 30 Hari", 'price': 57000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '6.5 GB', 'validity': '30 Hari', 'details': '6.5gb + Bonus Extra Kuota'},
    {'id': 270, 'name': "Tsel 6.5gb + Bonus Extra 30 Hari", 'price': 60000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '6.5 GB', 'validity': '30 Hari', 'details': '6.5gb + Bonus Extra Kuota'},
    {'id': 271, 'name': "Tsel 8gb + Bonus Extra 30 Hari", 'price': 68000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '8 GB', 'validity': '30 Hari', 'details': '8gb + Bonus Extra Kuota'},
    {'id': 272, 'name': "Tsel 12gb + Bonus Extra 30 Hari", 'price': 120000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '12 GB', 'validity': '30 Hari', 'details': '12gb + Bonus Extra Kuota'},
    {'id': 273, 'name': "Tsel 35gb + Extra Bonus 30 Hari", 'price': 133000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '35 GB', 'validity': '30 Hari', 'details': '35gb + Bonus Extra Kuota'},
    {'id': 274, 'name': "Tsel 57gb + Extra Bonus 30 Hari", 'price': 218000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '57 GB', 'validity': '30 Hari', 'details': '57gb + Bonus Extra Kuota'},
    {'id': 275, 'name': "Tsel 100gb + Extra Bonus 30 Hari", 'price': 269000, 'category': 'Telkomsel', 'type': 'Paket', 'data': '100-110 GB', 'validity': '30 Hari', 'details': '100gb - 110gb + Bonus Extra Kuota'},
    {'id': 276, 'name': "Telkomsel Pulsa 2.000", 'price': 3000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 2.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 2.000'},
    {'id': 277, 'name': "Telkomsel Pulsa 3.000", 'price': 4000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 3.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 3.000'},
    {'id': 278, 'name': "Telkomsel Pulsa 4.000", 'price': 5000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 4.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 4.000'},
    {'id': 279, 'name': "Telkomsel Pulsa 5.000", 'price': 6000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 5.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 5.000'},
    {'id': 280, 'name': "Telkomsel Pulsa 10.000", 'price': 11000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 10.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 10.000'},
    {'id': 281, 'name': "Telkomsel Pulsa 15.000", 'price': 16000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 15.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 15.000'},
    {'id': 282, 'name': "Telkomsel Pulsa 20.000", 'price': 20000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 20.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 20.000'},
    {'id': 283, 'name': "Telkomsel Pulsa 25.000", 'price': 25000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 25.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 25.000'},
    {'id': 284, 'name': "Telkomsel Pulsa 30.000", 'price': 30000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 30.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 30.000'},
    {'id': 285, 'name': "Telkomsel Pulsa 35.000", 'price': 35000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 35.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 35.000'},
    {'id': 286, 'name': "Telkomsel Pulsa 40.000", 'price': 40000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 40.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 40.000'},
    {'id': 287, 'name': "Telkomsel Pulsa 45.000", 'price': 45000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 45.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 45.000'},
    {'id': 288, 'name': "Telkomsel Pulsa 50.000", 'price': 50000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 50.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 50.000'},
    {'id': 289, 'name': "Telkomsel Pulsa 55.000", 'price': 55000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 55.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 55.000'},
    {'id': 290, 'name': "Telkomsel Pulsa 60.000", 'price': 60000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 60.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 60.000'},
    {'id': 291, 'name': "Telkomsel Pulsa 65.000", 'price': 65000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 65.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 65.000'},
    {'id': 292, 'name': "Telkomsel Pulsa 70.000", 'price': 70000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 70.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 70.000'},
    {'id': 293, 'name': "Telkomsel Pulsa 75.000", 'price': 75000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 75.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 75.000'},
    {'id': 294, 'name': "Telkomsel Pulsa 80.000", 'price': 80000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 80.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 80.000'},
    {'id': 295, 'name': "Telkomsel Pulsa 85.000", 'price': 85000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 85.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 85.000'},
    {'id': 296, 'name': "Telkomsel Pulsa 90.000", 'price': 90000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 90.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 90.000'},
    {'id': 297, 'name': "Telkomsel Pulsa 95.000", 'price': 95000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 95.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 95.000'},
    {'id': 298, 'name': "Telkomsel Pulsa 100.000", 'price': 99000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 100.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 100.000'},
    {'id': 299, 'name': "Telkomsel Pulsa 150.000", 'price': 150000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 150.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 150.000'},
    {'id': 300, 'name': "Telkomsel Pulsa 200.000", 'price': 199000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 200.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 200.000'},
    {'id': 301, 'name': "Telkomsel Pulsa 300.000", 'price': 303000, 'category': 'Telkomsel', 'type': 'Pulsa', 'data': 'Rp 300.000', 'validity': 'N/A', 'details': 'Pulsa Reguler 300.000'},
    # XL Akrab, etc.
    {'id': 302, 'name': "XL Akrab Mini Lite", 'price': 46000, 'category': 'XL', 'type': 'Akrab', 'data': '13-32 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 303, 'name': "XL Akrab Mini Lite V2", 'price': 46000, 'category': 'XL', 'type': 'Akrab', 'data': '13-15 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 304, 'name': "XL Akrab Mini", 'price': 58000, 'category': 'XL', 'type': 'Akrab', 'data': '33-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 305, 'name': "XL Akrab Mini V2", 'price': 64000, 'category': 'XL', 'type': 'Akrab', 'data': '31-50 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 306, 'name': "XL Akrab Big", 'price': 66000, 'category': 'XL', 'type': 'Akrab', 'data': '38-40 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 307, 'name': "XL Akrab Big V2", 'price': 67000, 'category': 'XL', 'type': 'Akrab', 'data': '38-57 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 308, 'name': "XL Akrab Big Extra V2", 'price': 80000, 'category': 'XL', 'type': 'Akrab', 'data': '33-71 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 309, 'name': "XL Akrab Big Ultimate V2", 'price': 84000, 'category': 'XL', 'type': 'Akrab', 'data': '54-71 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 310, 'name': "XL Akrab Jumbo Lite", 'price': 73000, 'category': 'XL', 'type': 'Akrab', 'data': '47-64 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 311, 'name': "XL Akrab Jumbo Lite V2", 'price': 76000, 'category': 'XL', 'type': 'Akrab', 'data': '70 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 312, 'name': "XL Akrab Jumbo", 'price': 91000, 'category': 'XL', 'type': 'Akrab', 'data': '70 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 313, 'name': "XL Akrab Jumbo V2", 'price': 97000, 'category': 'XL', 'type': 'Akrab', 'data': '70 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 314, 'name': "XL Akrab Mega Big", 'price': 98000, 'category': 'XL', 'type': 'Akrab', 'data': '90-92 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 315, 'name': "XL Akrab Mega Big V2", 'price': 102000, 'category': 'XL', 'type': 'Akrab', 'data': '90 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 316, 'name': "XL Akrab Extra Mega Big V2", 'price': 132000, 'category': 'XL', 'type': 'Akrab', 'data': '110 GB', 'validity': '30 Hari', 'details': 'Paket Akrab untuk keluarga.'},
    {'id': 317, 'name': "XL Bebas Puas 75GB", 'price': 98000, 'category': 'XL', 'type': 'BebasPuas', 'data': '75GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 318, 'name': "XL Bebas Puas 234GB", 'price': 171000, 'category': 'XL', 'type': 'BebasPuas', 'data': '234GB', 'validity': '30 Hari', 'details': 'Kuota besar, bebas internetan.'},
    {'id': 319, 'name': "XL Circle 7–11GB", 'price': 31000, 'category': 'XL', 'type': 'Circle', 'data': '7-11GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 320, 'name': "XL Circle 12–16GB", 'price': 36000, 'category': 'XL', 'type': 'Circle', 'data': '12-16GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 321, 'name': "XL Circle 17–21GB", 'price': 42000, 'category': 'XL', 'type': 'Circle', 'data': '17-21GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 322, 'name': "XL Circle 22–26GB", 'price': 51000, 'category': 'XL', 'type': 'Circle', 'data': '22-26GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 323, 'name': "XL Circle 27–31GB", 'price': 58000, 'category': 'XL', 'type': 'Circle', 'data': '27-31GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 324, 'name': "XL Circle 32–36GB", 'price': 66000, 'category': 'XL', 'type': 'Circle', 'data': '32-36GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
    {'id': 325, 'name': "XL Circle 37–41GB", 'price': 76000, 'category': 'XL', 'type': 'Circle', 'data': '37-41GB', 'validity': '30 Hari', 'details': 'Paket internet XL Circle.'},
]

# --- Fungsi untuk membuat key unik ---
def create_package_key(pkg):
    name_slug = re.sub(r'[^a-z0-9_]', '', pkg['name'].lower().replace(' ', '_'))
    return f"pkg_{pkg['id']}_{name_slug}"

# --- Memproses data mentah menjadi struktur yang bisa digunakan bot ---
ALL_PACKAGES_DATA = {create_package_key(pkg): pkg for pkg in ALL_PACKAGES_RAW}
PRICES = {key: data['price'] for key, data in ALL_PACKAGES_DATA.items()}

# --- Mengelompokkan paket berdasarkan kategori dan tipe ---
def get_products(category=None, product_type=None, special_type=None):
    filtered_items = ALL_PACKAGES_DATA.items()

    if category:
        filtered_items = [item for item in filtered_items if item[1].get('category', '').lower() == category.lower()]

    if special_type:
        filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == special_type.lower()]
    elif product_type:
        if category and category.lower() == 'xl' and product_type.lower() == 'paket':
            special_types = ['akrab', 'bebaspuas', 'circle']
            filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == 'paket' and item[1].get('type', '').lower() not in special_types]
        else:
            filtered_items = [item for item in filtered_items if item[1].get('type', '').lower() == product_type.lower()]
            
    return {key: data['name'] for key, data in filtered_items}

# --- DETAIL KUOTA PAKET ---
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
AKRAB_QUOTA_DETAILS['pkg_304_xl_akrab_mini'] = AKRAB_QUOTA_DETAILS.get('pkg_305_xl_akrab_mini_v2')

# ==============================================================================
# ✍️ Fungsi Pembuat Deskripsi Paket
# ==============================================================================
def create_general_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key)
    if not info: return "Deskripsi tidak ditemukan."
    name = info.get('name', "N/A")
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    header = f"<b>{safe_html(name)}</b>\n<b>Harga: {price}</b>\n\n"
    if info.get('type') == 'Pulsa':
        description = (header + f"• 💰 <b>Nominal Pulsa:</b> {info.get('data', 'N/A')}\n" +
                       f"• ⏳ <b>Tambah Masa Aktif:</b> {info.get('validity', 'N/A')}\n" +
                       f"• 📝 <b>Detail:</b> {safe_html(info.get('details', 'N/A'))}\n" +
                       f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}")
    else:
        description = (header + f"• 💾 <b>Kuota:</b> {info.get('data', 'N/A')}\n" +
                       f"• 📅 <b>Masa Aktif:</b> {info.get('validity', 'N/A')}\n" +
                       f"• 📝 <b>Rincian:</b> {safe_html(info.get('details', 'N/A'))}\n" +
                       f"• 📱 <b>Provider:</b> {info.get('category', 'N/A')}")
    return description

def create_akrab_description(package_key):
    package_name = ALL_PACKAGES_DATA.get(package_key, {}).get('name', 'Paket Akrab')
    price = PRICES.get(package_key, 0)
    formatted_price = f"Rp{price:,}".replace(",", ".")
    quota_info = AKRAB_QUOTA_DETAILS.get(package_key)
    description = (f"<b>{safe_html(package_name)}</b>\n<b>Harga: {formatted_price}</b>\n\n" +
                   f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL).\n" +
                   f"• 🛡️ <b>Jaminan:</b> GARANSI FULL.\n" +
                   f"• 🌐 <b>Kompatibilitas:</b> Bisa untuk XL / AXIS / LIVEON.\n" +
                   f"• 📅 <b>Masa Aktif:</b> ±28 hari, sesuai ketentuan pihak XL.\n\n")
    if quota_info:
        description += (f"• 💾 <b>Kuota 24 Jam (berdasarkan zona):</b>\n" +
                        f"  - <b>AREA 1:</b> {quota_info.get('1', 'N/A')}\n" +
                        f"  - <b>AREA 2:</b> {quota_info.get('2', 'N/A')}\n" +
                        f"  - <b>AREA 3:</b> {quota_info.get('3', 'N/A')}\n" +
                        f"  - <b>AREA 4:</b> {quota_info.get('4', 'N/A')}\n\n")
    else:
        description += "• 💾 <b>Detail Kuota:</b>\n  - Informasi detail kuota berdasarkan zona untuk paket ini akan segera diperbarui. Hubungi admin untuk informasi lebih lanjut.\n\n"
    description += (f"• 📋 <b>Prosedur & Ketentuan:</b>\n" +
                    f"  - Pastikan kartu SIM terpasang pada perangkat (HP/Modem) untuk deteksi lokasi BTS dan mendapatkan bonus kuota lokal.\n" +
                    f"  - Apabila kuota MyRewards belum masuk full, tunggu 1x24 jam sebelum laporan ke Admin.\n\n" +
                    f"• ℹ️ <b>Informasi Tambahan:</b>\n" +
                    f"  - <a href='http://bit.ly/area_akrab'>Cek Area Anda di sini</a>\n" +
                    f"  - <a href='https://kmsp-store.com/cara-unreg-paket-akrab-yang-benar'>Panduan Unreg Paket Akrab</a>")
    return description

def create_circle_description(package_key):
    package_name = ALL_PACKAGES_DATA.get(package_key, {}).get('name', 'Paket XL Circle')
    price = PRICES.get(package_key, 0)
    formatted_price = f"Rp{price:,}".replace(",", ".")
    quota_range = ALL_PACKAGES_DATA.get(package_key, {}).get('data', 'N/A')
    description = (f"<b>{safe_html(package_name)}</b>\n<b>Harga: {formatted_price}</b>\n\n" +
                   f"• 💾 <b>Estimasi Kuota:</b> {quota_range} (bisa dapat lebih jika beruntung).\n" +
                   f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n" +
                   f"• ⏳ <b>Masa Aktif:</b> 28 hari atau hingga kuota habis. Jika kuota habis sebelum 28 hari, keanggotaan akan masuk kondisi <b>BEKU/FREEZE</b> dan order ulang baru bisa dilakukan bulan depan.\n" +
                   f"• ⚡ <b>Aktivasi:</b> Instan, tidak menggunakan OTP.\n\n" +
                   f"⚠️ <b>PERHATIAN (PENTING):</b>\n" +
                   f"<b>1. Cara Cek Kuota:</b>\n" +
                   f"   - Buka aplikasi <b>MyXL terbaru</b>.\n" +
                   f"   - Klik menu <b>XL CIRCLE</b> di bagian bawah layar. (Bukan dari 'Lihat Paket Saya').\n\n" +
                   f"<b>2. Syarat & Ketentuan:</b>\n" +
                   f"   - <b>Umur Kartu:</b> Minimal 60 hari. Cek di <a href='https://sidompul.kmsp-store.com/'>sini</a>.\n" +
                   f"   - <b>Keanggotaan:</b> Tidak sedang terdaftar/bergabung di Circle lain dalam bulan yang sama.\n" +
                   f"   - <b>Masa Tenggang:</b> Kartu tidak boleh dalam masa tenggang. Paket ini <b>tidak menambah</b> masa aktif kartu.\n" +
                   f"   - <b>Isi Ulang Masa Aktif:</b> Jika kartu akan tenggang, disarankan isi paket masa aktif terlebih dahulu.\n" +
                   f"   - <b>Prioritas Kuota:</b> Jika ada kuota utama lain, kuota tersebut akan dipakai lebih dulu sebelum kuota Circle.\n" +
                   f"   - <b>Dilarang Unreg:</b> Keluar dari keanggotaan Circle akan menghanguskan garansi tanpa refund dan tidak bisa di-invite ulang.\n")
    return description

def create_bebaspuas_description(package_key):
    info = ALL_PACKAGES_DATA.get(package_key, {})
    name = info.get('name', 'Bebas Puas')
    price = f"Rp{info.get('price', 0):,}".replace(",", ".")
    kuota = "75GB" if "75" in name else "234GB"
    return (f"<b>{safe_html(name)}</b>\n<b>Harga: {price}</b>\n\n" +
            f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) jalur Sidompul.\n" +
            f"• ⚡ <b>Aktivasi Instan:</b> Tidak memerlukan kode OTP.\n" +
            f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n" +
            f"• 🌍 <b>Area:</b> Berlaku di semua area.\n" +
            f"• 📅 <b>Masa Aktif & Garansi:</b> 30 Hari.\n" +
            f"• 💾 <b>Kuota Utama:</b> {kuota}, full reguler 24 jam.\n\n" +
            f"• ⭐ <b>Fitur Unggulan:</b>\n" +
            f"  - <b>Akulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli/menimpa dengan paket Bebas Puas lain.\n" +
            f"  - <b>Tanpa Syarat Pulsa:</b> Aktivasi paket tidak memerlukan pulsa minimum.\n\n" +
            f"• 🎁 <b>Klaim Bonus:</b>\n" +
            f"  - Tersedia bonus kuota (pilih salah satu: YouTube, TikTok, atau Kuota Utama) yang dapat diklaim di aplikasi myXL.\n" +
            f"  - Disarankan untuk mengklaim bonus sebelum melakukan pembelian ulang (menimpa paket) untuk memaksimalkan keuntungan.")

# --- Kumpulan Semua Deskripsi ---
PAKET_DESCRIPTIONS = {**{key: create_general_description(key) for key in ALL_PACKAGES_DATA}}
for key in get_products(category='XL', special_type='Akrab'): PAKET_DESCRIPTIONS[key] = create_akrab_description(key)
for key in get_products(category='XL', special_type='Circle'): PAKET_DESCRIPTIONS[key] = create_circle_description(key)
for key in get_products(category='XL', special_type='BebasPuas'): PAKET_DESCRIPTIONS[key] = create_bebaspuas_description(key)
PAKET_DESCRIPTIONS["bantuan"] = ("<b>❔ Bantuan Bot Pulsa Net</b>\n\n" +
                                 "Ketik /start untuk kembali ke menu utama.\n" +
                                 "Hubungi admin jika Anda ingin mendaftar reseller atau melaporkan kendala teknis.\n\n" +
                                 "📞 <b>Admin:</b> @hexynos\n" +
                                 "🌐 <b>Website:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>")

# =============================
# 🏠 MENU UTAMA & NAVIGASI
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📶 Paket Data", callback_data="main_paket"), 
                 InlineKeyboardButton("💰 Pulsa", callback_data="main_pulsa")],
                [InlineKeyboardButton("❔ Bantuan", callback_data="main_bantuan")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Selamat datang di <b>Pulsa Net</b> 🎉\n\nSilakan pilih jenis produk yang Anda inginkan:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

async def show_operator_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_type_key = query.data.split('_')[1]
    product_type_name = "Paket Data" if product_type_key == "paket" else "Pulsa"
    operators = {"XL": "💙", "Axis": "💜", "Tri": "🧡", "Telkomsel": "❤️", "Indosat": "💛", "By.U": "🖤"}
    keyboard = []
    # Membuat 2 tombol per baris
    op_items = list(operators.items())
    for i in range(0, len(op_items), 2):
        row = [InlineKeyboardButton(f"{icon} {op}", callback_data=f"list_{product_type_key}_{op.lower()}") for op, icon in op_items[i:i + 2]]
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Anda memilih <b>{product_type_name}</b>. Silakan pilih provider:"
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

async def show_xl_paket_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🤝 Akrab XL", callback_data="list_paket_xl_akrab")],
        [InlineKeyboardButton("🥳 XL Bebas Puas", callback_data="list_paket_xl_bebaspuas")],
        [InlineKeyboardButton("🌀 XL Circle", callback_data="list_paket_xl_circle")],
        [InlineKeyboardButton("🚀 Paket XL Lainnya", callback_data="list_paket_xl_paket")],
        [InlineKeyboardButton("⬅️ Kembali ke Pilihan Provider", callback_data="main_paket")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "<b>💙 Paket Data XL</b>\n\nSilakan pilih jenis paket XL yang Anda inginkan:"
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    product_type_key = parts[1]
    category_key = parts[2]
    special_type_key = parts[3] if len(parts) > 3 else None

    titles_map = {"tri": "🧡 Tri", "axis": "💜 Axis", "telkomsel": "❤️ Telkomsel", "indosat": "💛 Indosat", "by.u": "🖤 By.U", "xl": "💙 XL"}
    base_title = titles_map.get(category_key, "Produk")
    product_type_name = "Paket Data" if product_type_key == 'paket' else "Pulsa"
    title = f"{base_title} - {product_type_name}"

    products = {}

    # --- PERBAIKAN UTAMA: MEMPERBAIKI LOGIKA FILTER UNTUK MENGHINDARI KATEGORI KOSONG ---
    if special_type_key:
        if category_key == 'xl' and special_type_key == 'paket':
            # Ini adalah kasus "Paket XL Lainnya", harus menggunakan filter product_type
            # untuk memicu logika pengecualian di get_products.
            products = get_products(category=category_key, product_type='paket')
            title = "🚀 Paket XL Lainnya"
        else:
            # Ini adalah kasus sub-kategori XL seperti Akrab, Circle.
            products = get_products(category=category_key, special_type=special_type_key)
            if special_type_key == 'akrab': title = "🤝 Paket Akrab XL"
            elif special_type_key == 'bebaspuas': title = "🥳 XL Bebas Puas"
            elif special_type_key == 'circle': title = "🌀 XL Circle"
    else:
        # Kasus umum untuk operator lain atau Pulsa.
        products = get_products(category=category_key, product_type=product_type_key)
    # --- AKHIR PERBAIKAN ---

    if not products:
        back_button_data = "main_paket" if product_type_key == 'paket' else 'main_pulsa'
        if category_key == 'xl' and product_type_key == 'paket':
            back_button_data = 'list_paket_xl' # Kembali ke submenu XL

        await query.edit_message_text(f"Saat ini belum ada produk untuk kategori <b>{title}</b>.", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=back_button_data)]]), 
                                      parse_mode="HTML")
        return

    sorted_keys = sorted(products.keys(), key=lambda k: PRICES.get(k, float('inf')))
    keyboard = []
    for i in range(0, len(sorted_keys), 2):
        row = []
        key1 = sorted_keys[i]
        name1 = products[key1]
        price1 = PRICES.get(key1, 0)
        formatted_price1 = f"Rp{price1:,}".replace(",", ".")
        short_name1 = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', name1, flags=re.I).replace('Paket ', '')
        row.append(InlineKeyboardButton(f"{short_name1} - {formatted_price1}", callback_data=key1))

        if i + 1 < len(sorted_keys):
            key2 = sorted_keys[i+1]
            name2 = products[key2]
            price2 = PRICES.get(key2, 0)
            formatted_price2 = f"Rp{price2:,}".replace(",", ".")
            short_name2 = re.sub(r'^(Tri|Axis|XL|Telkomsel|Indosat|By\.U)\s*', '', name2, flags=re.I).replace('Paket ', '')
            row.append(InlineKeyboardButton(f"{short_name2} - {formatted_price2}", callback_data=key2))
        
        keyboard.append(row)

    back_button_data = "list_paket_xl" if category_key == 'xl' and product_type_key == 'paket' else f"main_{product_type_key}"
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data=back_button_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"<b>{title}</b>\n\nSilakan pilih produk:", reply_markup=reply_markup, parse_mode="HTML")

async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    package_key = query.data
    text = PAKET_DESCRIPTIONS.get(package_key, "Deskripsi tidak ditemukan.")
    
    info = ALL_PACKAGES_DATA.get(package_key, {})
    category = info.get('category', '').lower()
    type_from_data = info.get('type', '').lower()
    
    back_data = "back_to_start"
    
    if type_from_data == 'pulsa':
        back_data = f"list_pulsa_{category}"
    elif category == 'xl':
        if type_from_data in ['akrab', 'bebaspuas', 'circle']:
            back_data = f"list_paket_xl_{type_from_data}"
        else: # Untuk 'Paket' biasa
            back_data = "list_paket_xl_paket"
    else: # Untuk paket data operator lain
        product_type_key = 'paket'
        back_data = f"list_{product_type_key}_{category}"

    keyboard = [
        [InlineKeyboardButton("🛒 Beli Produk Ini", url="https://pulsanet.kesug.com/beli.html")],
        [InlineKeyboardButton("⬅️ Kembali ke Daftar Produk", callback_data=back_data)],
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

# =============================
# 🚀 Jalankan Bot
# =============================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^back_to_start$'))
    app.add_handler(CallbackQueryHandler(show_bantuan, pattern='^main_bantuan$'))
    app.add_handler(CallbackQueryHandler(show_operator_menu, pattern=r'^main_(paket|pulsa)$'))
    app.add_handler(CallbackQueryHandler(show_xl_paket_submenu, pattern=r'^list_paket_xl$'))
    app.add_handler(CallbackQueryHandler(show_product_list, pattern=r'^list_(paket|pulsa)_.+$'))

    all_package_keys_pattern = '|'.join(re.escape(k) for k in ALL_PACKAGES_DATA)
    app.add_handler(CallbackQueryHandler(show_package_details, pattern=f'^({all_package_keys_pattern})$'))
    
    print("🤖 Bot Pulsa Net (v5.4 - Stabil) sedang berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
