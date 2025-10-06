# ============================================
# 🤖 Bot Pulsa Net
# File: bot_pulsanet_secure.py
# Developer: Farid Fauzi
# Versi: 3.4 (Penyempurnaan Deskripsi & Keamanan Token)
# ============================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from zoneinfo import ZoneInfo
import warnings
import re
import html
import os # <-- Pustaka 'os' ditambahkan untuk mengakses environment variable

# Menghilangkan peringatan 'pkg_resources is deprecated'
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# --- AMANKAN TOKEN BOT ANDA ---
# Mengambil token dari Environment Variable untuk keamanan.
# Jangan tulis token Anda langsung di sini jika kode ini akan diunggah ke publik.
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    # Jika variabel TELEGRAM_BOT_TOKEN tidak ditemukan di server, hentikan bot dengan pesan error yang jelas.
    raise ValueError("Token bot tidak ditemukan! Silakan set TELEGRAM_BOT_TOKEN di environment variable.")


def safe_html(text):
    """Loloskan karakter khusus HTML: <, >, &"""
    return html.escape(str(text))

# --- DAFTAR NAMA PAKET & HARGA ---
AKRAB_PACKAGES = {
    "akrab_mini_lite": "XL Akrab Mini Lite", "akrab_mini_lite_v2": "XL Akrab Mini Lite V2",
    "akrab_mini": "XL Akrab Mini", "akrab_mini_v2": "Akrab Anggota MINI V2",
    "akrab_big": "Akrab Anggota BIG", "akrab_big_v2": "Akrab Anggota BIG V2",
    "akrab_big_extra_v2": "Akrab Anggota BIG EXTRA V2", "akrab_big_ultimate_v2": "Akrab Anggota BIG ULTIMATE V2",
    "akrab_jumbo_lite": "XL Akrab Jumbo Lite", "akrab_jumbo_lite_v2": "Akrab Anggota JUMBO LITE V2",
    "akrab_jumbo": "Akrab Anggota JUMBO", "akrab_jumbo_v2": "Akrab Anggota JUMBO V2",
    "akrab_mega_big": "Akrab Anggota MEGA BIG", "akrab_mega_big_v2": "Akrab Anggota MEGA BIG V2",
    "akrab_extra_mega_big_v2": "Akrab Anggota EXTRA MEGA BIG V2",
}

BEBAS_PUAS_PACKAGES = {
    "bebaspuas_75gb": "XL Bebas Puas 75GB", "bebaspuas_234gb": "XL Bebas Puas 234GB",
}

CIRCLE_PACKAGES = {
    "circle_7gb": "XL Circle 7–11GB", "circle_12gb": "XL Circle 12–16GB",
    "circle_17gb": "XL Circle 17–21GB", "circle_22gb": "XL Circle 22–26GB",
    "circle_27gb": "XL Circle 27–31GB", "circle_32gb": "XL Circle 32–36GB",
    "circle_37gb": "XL Circle 37–41GB",
}

PRICES = {
    # Harga Akrab
    "akrab_mini_lite": 46000, "akrab_mini_lite_v2": 46000, "akrab_mini": 58000,
    "akrab_mini_v2": 64000, "akrab_big": 66000, "akrab_big_v2": 67000,
    "akrab_big_extra_v2": 80000, "akrab_big_ultimate_v2": 84000, "akrab_jumbo_lite": 73000,
    "akrab_jumbo_lite_v2": 76000, "akrab_jumbo": 91000, "akrab_jumbo_v2": 97000,
    "akrab_mega_big": 98000, "akrab_mega_big_v2": 102000, "akrab_extra_mega_big_v2": 132000,
    # Harga Bebas Puas
    "bebaspuas_75gb": 98000, "bebaspuas_234gb": 171000,
    # Harga XL Circle
    "circle_7gb": 31000, "circle_12gb": 36000, "circle_17gb": 42000,
    "circle_22gb": 51000, "circle_27gb": 58000, "circle_32gb": 66000,
    "circle_37gb": 76000,
}

# --- DETAIL KUOTA PAKET ---
AKRAB_QUOTA_DETAILS = {
    "akrab_mini_v2": {"1": "31GB - 33GB", "2": "33GB - 35GB", "3": "38GB - 40GB", "4": "48GB - 50GB"},
    "akrab_big": {"1": "38 GB - 40 GB", "2": "40 GB - 42 GB", "3": "45 GB - 47 GB", "4": "55 GB - 57 GB"},
    "akrab_big_v2": {"1": "38GB - 40GB", "2": "40GB - 42GB", "3": "45GB - 47GB", "4": "55GB - 57GB"},
    "akrab_big_extra_v2": {"1": "33GB", "2": "36GB", "3": "47GB", "4": "71GB"},
    "akrab_big_ultimate_v2": {"1": "54GB", "2": "56GB", "3": "61GB", "4": "71GB"},
    "akrab_jumbo_lite_v2": {"1": "47GB", "2": "49GB", "3": "54GB", "4": "64GB"},
    "akrab_jumbo": {"1": "65 GB", "2": "70 GB", "3": "83 GB", "4": "123 GB"},
    "akrab_jumbo_v2": {"1": "65GB", "2": "70GB", "3": "83GB", "4": "123GB"},
    "akrab_mega_big": {"1": "88 GB - 90 GB", "2": "90 GB - 92 GB", "3": "95 GB - 97 GB", "4": "105 GB - 107 GB"},
    "akrab_mega_big_v2": {"1": "88GB - 90GB", "2": "90GB - 92GB", "3": "95GB - 97GB", "4": "105GB - 107GB"},
    "akrab_extra_mega_big_v2": {"1": "105GB", "2": "110GB", "3": "123GB", "4": "163GB"}
}

# ==============================================================================
# 2️⃣ Fungsi Pembuat Deskripsi Paket
# ==============================================================================

def create_akrab_description(package_key):
    package_name = AKRAB_PACKAGES.get(package_key, "Paket Akrab")
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
    package_name = CIRCLE_PACKAGES.get(package_key, "Paket XL Circle")
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

# --- Kumpulan Semua Deskripsi ---
PAKET_DESCRIPTIONS = {
    **{key: create_akrab_description(key) for key in AKRAB_PACKAGES},
    **{key: create_circle_description(key) for key in CIRCLE_PACKAGES},
    "bebaspuas_75gb": (
        f"<b>{safe_html(BEBAS_PUAS_PACKAGES['bebaspuas_75gb'])}</b>\n<b>Harga: Rp{PRICES['bebaspuas_75gb']:,}</b>\n\n".replace(",", ".") +
        f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) jalur Sidompul.\n"
        f"• ⚡ <b>Aktivasi Instan:</b> Tidak memerlukan kode OTP.\n"
        f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n"
        f"• 🌍 <b>Area:</b> Berlaku di semua area.\n"
        f"• 📅 <b>Masa Aktif & Garansi:</b> 30 Hari.\n"
        f"• 💾 <b>Kuota Utama:</b> 75GB, full reguler 24 jam.\n\n"
        f"• ⭐ <b>Fitur Unggulan:</b>\n"
        f"  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli/menimpa dengan paket Bebas Puas lain.\n"
        f"  - <b>Tanpa Syarat Pulsa:</b> Aktivasi paket tidak memerlukan pulsa minimum.\n\n"
        f"• 🎁 <b>Klaim Bonus:</b>\n"
        f"  - Tersedia bonus kuota (pilih salah satu: YouTube, TikTok, atau Kuota Utama) yang dapat diklaim di aplikasi myXL.\n"
        f"  - Disarankan untuk mengklaim bonus sebelum melakukan pembelian ulang (menimpa paket) untuk memaksimalkan keuntungan."
    ),
    "bebaspuas_234gb": (
        f"<b>{safe_html(BEBAS_PUAS_PACKAGES['bebaspuas_234gb'])}</b>\n<b>Harga: Rp{PRICES['bebaspuas_234gb']:,}</b>\n\n".replace(",", ".") +
        f"• ✅ <b>Jenis Paket:</b> Resmi (OFFICIAL) jalur Sidompul.\n"
        f"• ⚡ <b>Aktivasi Instan:</b> Tidak memerlukan kode OTP.\n"
        f"• 📱 <b>Kompatibilitas:</b> Hanya untuk XL Prabayar (Prepaid).\n"
        f"• 🌍 <b>Area:</b> Berlaku di semua area.\n"
        f"• 📅 <b>Masa Aktif & Garansi:</b> 30 Hari.\n"
        f"• 💾 <b>Kuota Utama:</b> 234GB, full reguler 24 jam.\n\n"
        f"• ⭐ <b>Fitur Unggulan:</b>\n"
        f"  - <b>Akumulasi Kuota:</b> Sisa kuota dan masa aktif akan ditambahkan jika Anda membeli/menimpa dengan paket Bebas Puas lain.\n"
        f"  - <b>Tanpa Syarat Pulsa:</b> Aktivasi paket tidak memerlukan pulsa minimum.\n\n"
        f"• 🎁 <b>Klaim Bonus:</b>\n"
        f"  - Tersedia bonus kuota (pilih salah satu: YouTube, TikTok, atau Kuota Utama) yang dapat diklaim di aplikasi myXL.\n"
        f"  - Disarankan untuk mengklaim bonus sebelum melakukan pembelian ulang (menimpa paket) untuk memaksimalkan keuntungan."
    ),
    "bantuan": (
        "<b>🛒 Bantuan Bot Pulsa Net</b>\n\n"
        "Ketik /start untuk kembali ke menu utama.\n"
        "Hubungi admin jika Anda ingin mendaftar reseller atau melaporkan kendala teknis.\n\n"
        "📞 <b>Admin:</b> @hexynos\n"
        "🌐 <b>Website:</b> <a href='https://pulsanet.kesug.com/'>pulsanet.kesug.com</a>"
    ),
}

# =============================
# 1️⃣ Fungsi utama menu
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 Paket Akrab XL", callback_data="menu_akrab_category")],
        [InlineKeyboardButton("🔥 XL Bebas Puas", callback_data="menu_bebaspuas_category")],
        [InlineKeyboardButton("🔵 XL Circle", callback_data="menu_circle_category")],
        [InlineKeyboardButton("🛒 Bantuan", callback_data="menu_bantuan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "Selamat datang di <b>Pulsa Net</b> 🎉\n\n"
        "Kami menyediakan berbagai pilihan paket data XL/AXIS dengan harga kompetitif dan aktivasi cepat.\n\n"
        "Silakan pilih kategori paket di bawah ini 👇"
    )
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            await update.callback_query.message.reply_text(text="<b>Pulsa Net</b> - Menu Utama", reply_markup=reply_markup, parse_mode="HTML")
        await update.callback_query.answer()
    elif update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="HTML")

# =============================
# 3️⃣ Callback Handlers
# =============================

async def category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("_category", "")
    packages = None
    if data == "menu_akrab":
        title = "📦 Paket Akrab XL"
        packages = AKRAB_PACKAGES
    elif data == "menu_bebaspuas":
        title = "🔥 XL Bebas Puas"
        packages = BEBAS_PUAS_PACKAGES
    elif data == "menu_circle":
        title = "🔵 XL Circle"
        packages = CIRCLE_PACKAGES
    
    if not packages:
        await query.edit_message_text("Kategori tidak ditemukan.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="back_to_start")]]), parse_mode="HTML")
        return

    keyboard = []
    keys = list(packages.keys())
    for i in range(0, len(keys), 2):
        row = []
        key1 = keys[i]
        name1 = packages[key1]
        price1 = PRICES.get(key1, 0)
        formatted_price1 = f"Rp{price1:,}".replace(",", ".")
        button_text1 = f"{name1.replace('Akrab Anggota ', '').replace('XL ', '')} - {formatted_price1}"
        row.append(InlineKeyboardButton(button_text1, callback_data=key1))

        if i + 1 < len(keys):
            key2 = keys[i+1]
            name2 = packages[key2]
            price2 = PRICES.get(key2, 0)
            formatted_price2 = f"Rp{price2:,}".replace(",", ".")
            button_text2 = f"{name2.replace('Akrab Anggota ', '').replace('XL ', '')} - {formatted_price2}"
            row.append(InlineKeyboardButton(button_text2, callback_data=key2))
        
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"<b>{title}</b>\n\nSilakan pilih paket yang detailnya ingin Anda lihat:"
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")


async def show_package_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    package_key = query.data
    text = PAKET_DESCRIPTIONS.get(package_key, "Deskripsi tidak ditemukan.")
    purchase_url = "https://pulsanet.kesug.com/"
    back_to_category_data = "menu_akrab_category"
    if "bebaspuas" in package_key:
        back_to_category_data = "menu_bebaspuas_category"
    elif "circle" in package_key:
        back_to_category_data = "menu_circle_category"

    keyboard = [
        [InlineKeyboardButton("🛒 Beli Paket Ini", url=purchase_url)],
        [InlineKeyboardButton("⬅️ Kembali ke Daftar Paket", callback_data=back_to_category_data)],
        [InlineKeyboardButton("🏠 Kembali ke Menu Utama", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True
    )


async def show_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = PAKET_DESCRIPTIONS.get("bantuan", "Bantuan tidak ditemukan.")
    keyboard = [[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


# =============================
# 4️⃣ Jalankan Bot
# =============================
def main():
    jakarta_tz = ZoneInfo("Asia/Jakarta")
    app = Application.builder().token(TOKEN).build()
    app.job_queue.scheduler.configure(timezone=jakarta_tz)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_menu, pattern=r'^(menu_akrab_category|menu_bebaspuas_category|menu_circle_category)$'))
    app.add_handler(CallbackQueryHandler(show_bantuan, pattern='^menu_bantuan$'))

    all_package_keys_dict = {**AKRAB_PACKAGES, **BEBAS_PUAS_PACKAGES, **CIRCLE_PACKAGES}
    all_package_keys_pattern = '|'.join(re.escape(k) for k in all_package_keys_dict)
    app.add_handler(CallbackQueryHandler(show_package_details, pattern=f'^({all_package_keys_pattern})$'))
    
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_start$'))

    print("🤖 Bot Pulsa Net sedang berjalan...")
    app.run_polling()


# =============================
# 5️⃣ Jalankan Program
# =============================
if __name__ == "__main__":
    main()
