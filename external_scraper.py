import pandas as pd
import feedparser
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URL RSS Feed Berita Eksternal UNESA (Google News RSS & Media Utama)
RSS_URLS = [
    "https://news.google.com/rss/search?q=UNESA&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Universitas+Negeri+Surabaya&hl=id&gl=ID&ceid=ID:id",
    "https://www.antaranews.com/rss/terkini.xml"
]

CSV_FILE = "rekap_berita_eksternal.csv"

# Kata kunci iklan / marketplace properti yang wajib diblokir
BLOCKLIST_KEYWORDS = [
    "disewakan", "dijual", "siap huni", "kost", "kontrakan", 
    "tanah dijual", "rumah dijual", "over kredit", "shm"
]

BLOCKLIST_DOMAINS = [
    "rumah123.com", "olx.co.id", "lamudi.co.id", "propertyguru", "mitula"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, label: Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_article_body_text(url):
    """Mengambil teks paragraf utama artikel & membersihkan elemen sidebar/baca juga."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=7, verify=False)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hapus elemen pengganggu (sidebar, footer, ad, widget)
        for element in soup(["aside", "footer", "nav", "script", "style"]):
            element.extract()
            
        for div in soup.find_all("div", class_=re.compile(r'(sidebar|related|baca-juga|ad-|recommendation)', re.I)):
            div.extract()
            
        paragraphs = soup.find_all('p')
        body_text = ' '.join([clean_text(p.get_text()) for p in paragraphs])
        return body_text
    except Exception:
        return ""

def classify_news(title, body_text):
    """Menentukan kategori dan sentimen secara akurat."""
    text_to_check = (title + " " + body_text).lower()
    
    # 1. Klasifikasi Kategori Tema
    if any(k in text_to_check for k in ['pakar', 'akademisi', 'dosen', 'pengamat', 'peneliti', 'tanggapan']):
        kategori = "Pikiran Pakar"
    elif any(k in text_to_check for k in ['prestasi', 'juara', 'medali', 'penghargaan', 'beasiswa']):
        kategori = "Prestasi & Penghargaan"
    elif any(k in text_to_check for k in ['riset', 'inovasi', 'paten', 'penelitian', 'karya']):
        kategori = "Riset & Inovasi"
    elif any(k in text_to_check for k in ['mahasiswa', 'ukm', 'pemira', 'bem', 'kkn', 'magang']):
        kategori = "Kemahasiswaan"
    elif any(k in text_to_check for k in ['pengabdian', 'masyarakat', 'binaan', 'desa']):
        kategori = "Pengabdian Masyarakat"
    elif any(k in text_to_check for k in ['kerjasama', 'mou', 'kunjungan', 'mitra']):
        kategori = "Kerjasama & Internasional"
    elif any(k in text_to_check for k in ['kasus', 'hukum', 'dugaan', 'polisi', 'sengketa', 'sidang']):
        kategori = "Isu Hukum & PPKS"
    else:
        kategori = "Akademik & Umum"

    # 2. Klasifikasi Sentimen
    if kategori == "Pikiran Pakar":
        sentimen = "Positif" if any(k in text_to_check for k in ['solusi', 'dorong', 'inovasi', 'bantu']) else "Netral"
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa']):
        sentimen = "Negatif"
    elif any(k in text_to_check for k in ['juara', 'unggul', 'sukses', 'bangga', 'resmi', 'apresiasi']):
        sentimen = "Positif"
    else:
        sentimen = "Netral"

    return kategori, sentimen

def determine_media_tier(source_name):
    source_lower = source_name.lower()
    tier1_list = ['detik', 'kompas', 'antara', 'cnn indonesia', 'tempo', 'republika', 'liputan6', 'jawapos', 'merdeka', 'sindonews', 'tribunnews']
    tier2_list = ['suara surabaya', 'beritajatim', 'radar surabaya', 'suryamalang', 'tribunjatim', 'duta.co']

    if any(m in source_lower for m in tier1_list):
        return "Tier 1 (Nasional)"
    elif any(m in source_lower for m in tier2_list):
        return "Tier 2 (Regional)"
    else:
        return "Portal Kampus/Lain"

def fetch_external_news():
    print("=== MENGAMBIL BERITA EKSTERNAL UNESA & MEMFILTER BODI TEKS ===")
    news_list = []

    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = clean_text(entry.get('title', ''))
            link = entry.get('link', '')
            pub_date = entry.get('published', '')

            # Ambil nama media
            source_name = "Media Online"
            if 'source' in entry and 'title' in entry.source:
                source_name = entry.source.title
            elif '-' in title:
                source_name = title.split('-')[-1].strip()

            # Filter 1: Blokir domain & kata kunci iklan
            if any(dom in link.lower() for dom in BLOCKLIST_DOMAINS):
                continue
            if any(kw in title.lower() for kw in BLOCKLIST_KEYWORDS):
                continue

            # Ambil bodi teks artikel
            body_text = fetch_article_body_text(link)

            # Filter 2: Verifikasi keberadaan kata UNESA pada judul/bodi teks utama
            contains_unesa_title = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', title, re.I))
            contains_unesa_body = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', body_text, re.I))

            if not (contains_unesa_title or contains_unesa_body):
                continue

            # Klasifikasi kategori, sentimen, dan tier
            kategori, sentimen = classify_news(title, body_text)
            tier_media = determine_media_tier(source_name)

            # Format tanggal
            try:
                dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                formatted_date = dt.strftime("%d %B %Y")
            except Exception:
                formatted_date = datetime.now().strftime("%d %B %Y")

            news_list.append({
                'tanggal': formatted_date,
                'sumber': source_name,
                'nama_media': source_name,
                'kategori': kategori,
                'judul': title,
                'sentimen': sentimen,
                'tier_media': tier_media,
                'link': link
            })

    if news_list:
        df_new = pd.DataFrame(news_list)
        try:
            df_old = pd.read_csv(CSV_FILE)
            df_combined = pd.concat([df_new, df_old]).drop_duplicates(subset=['judul'], keep='first')
        except Exception:
            df_combined = df_new

        df_combined.to_csv(CSV_FILE, index=False)
        print(f"[SUKSES] Total {len(df_combined)} berita tersimpan di '{CSV_FILE}'.")
    else:
        print("[INFO] Tidak ada berita baru yang lolos filter.")

if __name__ == "__main__":
    fetch_external_news()
