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

# Daftar berita negatif palsu / noise dari data lama yang wajib dibuang
INVALID_TITLES = [
    "Kapolrestabes Surabaya Minta Maaf",
    "Polisi di Bulukumba Ditangkap",
    "Diduga Lecehkan 7 Anak Laki-laki",
    "Siap Huni 45jt/th Disewakan"
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
    if not title:
        return ""
    parts = title.split(' - ')
    if len(parts) > 1 and len(parts[-1]) < 30:
        title = ' - '.join(parts[:-1])
    return clean_text(title)

def fetch_article_body_text(url):
    """Mengambil teks paragraf utama artikel & membuang box sisipan Pilihan Redaksi/Baca Juga."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Hapus elemen tag umum
        for element in soup(["aside", "footer", "nav", "script", "style", "form"]):
            element.extract()
            
        # 2. Hapus spesifik box "Pilihan Redaksi", "Baca Juga", "Berita Terkait", Iklan
        for div in soup.find_all(["div", "section", "article", "blockquote"], class_=re.compile(r'(sidebar|related|baca-juga|ad-|recommendation|widget|pilihan-redaksi|detail-tag|insert|multi-link)', re.I)):
            div.extract()

        # 3. Hapus paragraf yang berawalan "Lihat Juga:", "Baca juga:", "Pilihan Redaksi:"
        for p in soup.find_all('p'):
            p_text = p.get_text().strip().lower()
            if p_text.startswith(('baca juga', 'lihat juga', 'pilihan redaksi', 'simak juga', 'baca selengkapnya')):
                p.extract()
            
        paragraphs = soup.find_all('p')
        body_text = ' '.join([clean_text(p.get_text()) for p in paragraphs])
        return body_text
    except Exception:
        return ""

def classify_news(title, body_text=""):
    """Menentukan kategori dan sentimen secara akurat."""
    text_to_check = (title + " " + body_text).lower()
    
    # Kategori Pakar
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

    # Sentimen
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
    """Membersihkan file CSV lama dari berita sampah/noise secara instan."""
    try:
        df = pd.read_csv(CSV_FILE)
        initial_len = len(df)
        
        # 1. Hapus domain & kata kunci terlarang
        pattern_domains = '|'.join([re.escape(d) for d in BLOCKLIST_DOMAINS])
        pattern_keywords = '|'.join([re.escape(k) for k in BLOCKLIST_KEYWORDS])
        
        df = df[~df['link'].astype(str).str.contains(pattern_domains, case=False, na=False)]
        df = df[~df['judul'].astype(str).str.contains(pattern_keywords, case=False, na=False)]
        
        # 2. Hapus judul sampah spesifik (Bulukumba, Rumah123, Pungli Sidoarjo, Bogor)
        pattern_invalid = '|'.join([re.escape(t) for t in INVALID_TITLES])
        df = df[~df['judul'].astype(str).str.contains(pattern_invalid, case=False, na=False)]
        
        # 3. Hapus judul terlalu pendek
        df = df[df['judul'].astype(str).str.len() > 15]
        
        # 4. Perbaiki berita Pakar (seperti Sita Aset Suara.com) agar tidak Negatif
        for idx, row in df.iterrows():
            title = str(row['judul'])
            kat, sen = classify_news(title, "")
            df.at[idx, 'kategori'] = kat
            if kat == "Pikiran Pakar" or "akademisi unesa" in title.lower() or "pakar" in title.lower():
                df.at[idx, 'kategori'] = "Pikiran Pakar"
                df.at[idx, 'sentimen'] = "Positif" if "dorong" in title.lower() else "Netral"

        print(f"[CLEANUP] Berhasil membersihkan CSV lama: dari {initial_len} menjadi {len(df)} berita.")
        return df
    except Exception as e:
        print(f"[WARN] Gagal membersihkan CSV lama: {e}")
        return pd.DataFrame()

def fetch_external_news():
    print("=== MENGAMBIL BERITA EKSTERNAL UNESA (ENHANCED NOISE FILTER) ===")
    
    # Clean CSV lama
    df_old_clean = filter_and_clean_existing_csv()

    # Fetch RSS Baru
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

            if any(dom in link.lower() for dom in BLOCKLIST_DOMAINS) or any(kw in title.lower() for kw in BLOCKLIST_KEYWORDS):
                continue

            body_text = fetch_article_body_text(link)
            contains_unesa_title = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', title, re.I))
            contains_unesa_body = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', body_text, re.I))

            if not (contains_unesa_title or contains_unesa_body):
                continue

            kategori, sentimen = classify_news(title, body_text)

            try:
                dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                formatted_date = dt.strftime("%Y-%m-%d")
            except Exception:
                formatted_date = datetime.now().strftime("%Y-%m-%d")

            news_list.append({
                'tanggal': formatted_date,
                'sumber': source_name,
                'nama_media': source_name,
                'kategori': kategori,
                'judul': title,
                'sentimen': sentimen,
                'tier_media': "Tier 1 (Nasional)" if any(m in source_name.lower() for m in ['kompas','detik','antara','cnn']) else "Tier 2 (Regional)",
                'link': link
            })

    df_new = pd.DataFrame(news_list)
    df_combined = pd.concat([df_new, df_old_clean]).drop_duplicates(subset=['judul'], keep='first')
    
    if not df_combined.empty:
        df_combined.to_csv(CSV_FILE, index=False)
        print(f"[SUKSES] Total {len(df_combined)} berita bersih berhasil disimpan di '{CSV_FILE}'.")

if __name__ == "__main__":
    fetch_external_news()
