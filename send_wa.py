import os
import requests
import pandas as pd

def send_wa_notification():
    # Ambil token dari GitHub Secrets
    token = os.environ.get('FONNTE_TOKEN')
    
    # Target dikirim langsung ke Grup WA "Monitoring Publikasi Unesa"
    target_number = '120363430947326532@g.us' 
    
    if not token:
        print("FONNTE_TOKEN tidak ditemukan di environment!")
        return

    csv_file = 'rekap_berita_eksternal.csv'
    if not os.path.exists(csv_file):
        print(f"File {csv_file} tidak ditemukan!")
        return

    df = pd.read_csv(csv_file)
    df.fillna('', inplace=True)
    
    col_judul = 'judul' if 'judul' in df.columns else df.columns[2]
    col_media = 'media' if 'media' in df.columns else ('sumber' if 'sumber' in df.columns else df.columns[1])
    col_url = 'url' if 'url' in df.columns else ('link' if 'link' in df.columns else '#')

    # Ambil 3 berita paling baru untuk ringkasan
    top_news = df.head(3)
    
    pesan = "📢 *MONITORING PEMBERITAAN EKSTERNAL UNESA*\n"
    pesan += "----------------------------------------\n\n"
    pesan += f"📊 *Total Terdeteksi:* {len(df)} Berita Eksternal\n\n"
    pesan += "📰 *3 Pemberitaan Terbaru Hari Ini:*\n"
    
    for idx, row in top_news.iterrows():
        jdl = row.get(col_judul, '-')
        med = row.get(col_media, 'Media Pers')
        link = row.get(col_url, '#')
        pesan += f"\n▫️ *[{med}]* {jdl}\n🔗 {link}\n"
        
    pesan += "\n🌐 *Lihat Dashboard Selengkapnya:*\n"
    pesan += "https://hisyam-hue.github.io/unesa-external-monitoring/"

    # Kirim via API Fonnte
    url = 'https://api.fonnte.com/send'
    headers = {
        'Authorization': token
    }
    data = {
        'target': target_number,
        'message': pesan,
    }

    response = requests.post(url, headers=headers, data=data)
    print("Respon Fonnte:", response.text)

if __name__ == '__main__':
    send_wa_notification()
