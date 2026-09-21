import os
import pandas as pd
import requests

CSV_FILE = "rekap_berita_eksternal.csv"
FONNTE_TOKEN = os.environ.get("FONNTE_TOKEN")
TARGET_PHONE = "120363430947326532@g.us" # Ganti dengan nomor atau ID Grup WhatsApp Anda

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
    
    message_lines = [
        "📢 *MONITORING PEMBERITAAN EKSTERNAL UNESA*",
        "----------------------------------------",
        f"📊 *Total Terdeteksi:* {total_berita} Berita Eksternal",
        "",
        "📰 *3 Pemberitaan Terbaru Hari Ini:*",
        ""
    ]

    for idx, row in latest_news.iterrows():
        judul = str(row.get('judul', 'Tanpa Judul')).strip()
        raw_media = str(row.get('nama_media', row.get('sumber', 'Media Eksternal'))).strip()
        link = str(row.get('link', '#')).strip()
        
        # Membersihkan nama media dari ekstensi domain agar tidak salah klik ke homepage
        clean_media = raw_media.split('.')[0].replace('https://', '').replace('http://', '').replace('www.', '').title()
        
        # Format berita dengan nama media bersih, judul, dan link langsung ke artikel
        news_item = f"• *{clean_media}*\n  {judul}\n  🔗 {link}"
        message_lines.append(news_item)

    message_lines.extend([
        "",
        "----------------------------------------",
        "🌐 *Akses Dashboard Lengkap (4 Tab):*",
        "https://hisyam-hue.github.io/unesa-external-monitoring/"
    ])

    full_message = "\n".join(message_lines)

    payload = {
        'target': TARGET_PHONE,
        'message': full_message,
        'countryCode': '62',
    }
    
    headers = {
        'Authorization': FONNTE_TOKEN
    }

    try:
        response = requests.post('https://api.fonnte.com/send', data=payload, headers=headers)
        res_data = response.json()
        print("Fonnte Response:", res_data)
    except Exception as e:
        print(f"Gagal mengirim WhatsApp: {e}")

if __name__ == "__main__":
    send_whatsapp_notification()
