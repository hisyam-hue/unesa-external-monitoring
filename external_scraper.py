import pandas as pd
import feedparser
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URL RSS Feed Berita Eksternal UNESA
RSS_URLS = [
    "https://news.google.com/rss/search?q=UNESA&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Universitas+Negeri+Surabaya&hl=id&gl=ID&ceid=ID:id",
    "https://www.antaranews.com/rss/terkini.xml"
]

CSV_FILE = "rekap_berita_eksternal.csv"

# Kata kunci iklan / marketplace / sistem internal yang wajib diblokir
BLOCKLIST_KEYWORDS = [
    "disewakan", "dijual", "siap huni", "kost", "kontrakan", 
    "tanah dijual", "rumah dijual", "over kredit", "shm",
    "login", "reset password", "email reset", "portal mahasiswa"
]

# Domain non-media & iklan properti yang diblokir
BLOCKLIST_DOMAINS = [
    "rumah123.com", "olx.co.id", "lamudi.co.id", "propertyguru", "mitula",
    "sibiti.co.id", "unesa.ac.id"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_title(title):
    """Membersihkan judul dari nama penulis atau pemisah media di akhir."""
    if not title:
        return ""
    parts = title.split(' - ')
    if len(parts) > 1 and len(parts[-1]) < 30:
        title = ' - '.join(parts[:-1])
    return clean_text(title)

def fetch_article_body_text(url):
    """Mengambil teks paragraf utama artikel & membersihkan elemen sidebar/baca juga."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=4, verify=False)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hapus elemen pengganggu
        for element in soup(["aside", "footer", "nav", "script", "style", "form"]):
            element.extract()
            
        for div in soup.find_all(["div", "section"], class_=re.compile(r'(sidebar|related|baca-juga|ad-|recommendation|widget)', re.I)):
            div.extract()
            
        paragraphs = soup.find_all('p')
        body_text = ' '.join([clean_text(p.get_text()) for p in paragraphs])
        return body_text
    except Exception:
        return ""

def classify_news(title, body_text=""):
    """Menentukan kategori dan sentimen secara akurat."""
    text_to_check = (title + " " + body_text).lower()
    
    # 1. Klasifikasi Kategori Tema
    if any(k in text_to_check for k in ['pakar', 'akademisi', 'dosen', 'pengamat', 'peneliti', 'tanggapan', 'dorong', 'soroti', 'pakar unesa']):
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
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa']):
        kategori = "Isu Hukum & PPKS"
    else:
        kategori = "Akademik & Umum"

    # 2. Klasifikasi Sentimen
    if kategori == "Pikiran Pakar":
        sentimen = "Positif" if any(k in text_to_check for k in ['solusi', 'dorong', 'inovasi', 'bantu', 'mekanisme']) else "Netral"
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa']):
        sentimen = "Negatif"
    elif any(k in text_to_check for k in ['juara', 'unggul', 'sukses', 'bangga', 'resmi', 'apresiasi']):
        sentimen = "Positif"
    else:
        sentimen = "Netral"

    return kategori, sentimen

def filter_and_clean_existing_csv():
    """Membersihkan file CSV lama secara kilat tanpa melakukan HTTP request ulang."""
    try:
        df = pd.read_csv(CSV_FILE)
        initial_len = len(df)
        
        # 1. Hapus domain & kata kunci terlarang
        pattern_domains = '|'.join([re.escape(d) for d in BLOCKLIST_DOMAINS])
        pattern_keywords = '|'.join([re.escape(k) for k in BLOCKLIST_KEYWORDS])
        
        df = df[~df['link'].astype(str).str.contains(pattern_domains, case=False, na=False)]
        df = df[~df['judul'].astype(str).str.contains(pattern_keywords, case=False, na=False)]
        
        # 2. Hapus judul terlalu pendek (nama penulis)
        df = df[df['judul'].astype(str).str.len() > 15]
        
        # 3. Perbaiki kategori & sentimen untuk pakar
        for idx, row in df.iterrows():
            title = str(row['judul'])
            kat, sen = classify_news(title, "")
            df.at[idx, 'kategori'] = kat
            if kat == "Pikiran Pakar" and row['sentimen'] == "Negatif":
                df.at[idx, 'sentimen'] = "Netral"

        print(f"[CLEANUP] Berhasil membersihkan CSV lama: dari {initial_len} menjadi {len(df)} berita.")
        return df
    except Exception as e:
        print(f"[WARN] Gagal membersihkan CSV lama: {e}")
        return pd.DataFrame()

def fetch_external_news():
    print("=== MENGAMBIL BERITA EKSTERNAL UNESA (FAST SCRAPER) ===")
    
    # 1. Clean CSV lama
    df_old_clean = filter_and_clean_existing_csv()

    # 2. Fetch RSS Baru
    news_list = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = clean_title(entry.get('title', ''))
            link = entry.get('link', '')
            pub_date = entry.get('published', '')

            source_name = "Media Online"
            if 'source' in entry and 'title' in entry.source:
                source_name = entry.source.title
            elif '-' in entry.get('title', ''):
                source_name = entry.get('title', '').split('-')[-1].strip()

            # Filter cepat
            if any(dom in link.lower() for dom in BLOCKLIST_DOMAINS) or any(kw in title.lower() for kw in BLOCKLIST_KEYWORDS):
                continue

            # Fetch bodi artikel baru saja
            body_text = fetch_article_body_text(link)
            contains_unesa_title = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', title, re.I))
            contains_unesa_body = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', body_text, re.I))

            if not (contains_unesa_title or contains_unesa_body):
                continue

            kategori, sentimen = classify_news(title, body_text)

            try:
                dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                formatted_date = dt.strftime("%Y-%m-%d") # Format baku ISO
            except Exception:
                formatted_date = datetime.now().strftime("%Y-%m-%d")

            news_list.append({
                'tanggal': formatted_date,
                'sumber': source_name,
                'nama_media': source_name,
                'kategori': kategori,
                'judul': title,
                'sentimen': sentimen,
                'tier_media': "Tier 1 (Nasional)" if any(m in source_name.lower() for m in ['kompas','detik','antara']) else "Tier 2 (Regional)",
                'link': link
            })

    df_new = pd.DataFrame(news_list)
    df_combined = pd.concat([df_new, df_old_clean]).drop_duplicates(subset=['judul'], keep='first')
    
    if not df_combined.empty:
        df_combined.to_csv(CSV_FILE, index=False)
        print(f"[SUKSES] Total {len(df_combined)} berita bersih berhasil disimpan di '{CSV_FILE}'.")

if __name__ == "__main__":
    fetch_external_news()
