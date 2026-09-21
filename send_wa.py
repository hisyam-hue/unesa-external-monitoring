import os
import pandas as pd
import requests
import json # Diperlukan untuk mengirim format button

CSV_FILE = "rekap_berita_eksternal.csv"
FONNTE_TOKEN = os.environ.get("FONNTE_TOKEN")
# Ganti dengan nomor tujuan atau ID Grup WhatsApp Anda
TARGET_PHONE = "120363430947326532@g.us"

def send_whatsapp_notification():
    if not FONNTE_TOKEN:
        print("Error: FONNTE_TOKEN tidak ditemukan di environment variables.")
        return

    try:
        df = pd.read_csv(CSV_FILE)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    total_berita = len(df)
    latest_news = df.head(3)
    
    # --- PESAN UTAMA (TEKS BIASA, TANPA LINK/PREVIEW) ---
    message_header = (
        "📢 *MONITORING PEMBERITAAN EKSTERNAL UNESA*\n"
        "----------------------------------------\n"
        f"📊 *Total Terdeteksi:* {total_berita} Berita Eksternal\n\n"
        "📰 *3 Pemberitaan Terbaru Hari Ini:*\n\n"
    )

    # Daftar item berita dalam bentuk teks biasa, TANPA URL mentah
    news_items_text = []
    for idx, row in latest_news.iterrows():
        judul = str(row.get('judul', 'Tanpa Judul')).strip()
        raw_media = str(row.get('nama_media', row.get('sumber', 'Media Eksternal'))).strip()
        # Bersihkan nama media (buang ekstensi .id, .com)
        clean_media = raw_media.split('.')[0].replace('https://', '').replace('http://', '').replace('www.', '').title()
        
        news_item = f"• *{clean_media}*\n  _{judul}_"
        news_items_text.append(news_item)

    # Gabungkan header dan item berita menjadi satu string pesan
    full_message = message_header + "\n\n".join(news_items_text)

    # --- MENYIAPKAN BUTTON (TOMBOL LINK UNTUK MASING-MASING BERITA) ---
    # Fonnte butuh data tombol yang diformat khusus sebagai JSON
    buttons_data = []
    for idx, row in latest_news.iterrows():
        link = str(row.get('link', '#')).strip()
        judul = str(row.get('judul', 'Tanpa Judul')).strip()
        # Batasi panjang judul untuk label tombol agar tidak terpotong (maks 20-25 karakter)
        button_label = (judul[:20] + '...') if len(judul) > 20 else judul
        
        buttons_data.append({
            "type": "url",
            "url": link,
            "text": f"Buka: {button_label}" # Label tombol
        })
        
    # --- MENGIRIM VIA FONNTE API DENGAN FORMAT BUTTON ---
    payload = {
        'target': TARGET_PHONE,
        'message': full_message,
        'countryCode': '62',
        'type': 'template', # Penting: set tipe ke 'template' untuk kirim button
        'buttons': json.dumps(buttons_data) # Masukkan data tombol dalam format JSON string
    }
    
    headers = {
        'Authorization': FONNTE_TOKEN,
        'Content-Type': 'application/x-www-form-urlencoded' # Wajib untuk Fonnte type template
    }

    try:
        response = requests.post('https://api.fonnte.com/send', data=payload, headers=headers)
        res_data = response.json()
        print("Fonnte Response:", res_data)
    except Exception as e:
        print(f"Gagal mengirim WhatsApp: {e}")

if __name__ == "__main__":
    send_whatsapp_notification()
