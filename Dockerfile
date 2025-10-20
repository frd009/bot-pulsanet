# Gunakan base image Python 3.11 yang ramping sebagai dasar.
FROM python:3.11-slim

# Atur direktori kerja di dalam kontainer.
WORKDIR /app

# Perbarui daftar paket dan instal ffmpeg.
# Bendera -y mengonfirmasi instalasi secara otomatis.
# rm -rf membersihkan cache untuk menjaga ukuran image tetap kecil.
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu untuk optimasi cache.
COPY requirements.txt .

# Instal semua dependensi Python.
RUN pip install --no-cache-dir -r requirements.txt

# Salin sisa kode aplikasi Anda ke direktori kerja.
COPY . .

# Perintah yang akan dijalankan saat kontainer dimulai.
CMD ["python", "bot_pulsanet.py"]
