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
    "sibiti.co.id", "unesa.ac.id" # Memblokir domain sistem/lomba/internal non-pers
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
    """Membersihkan judul dari nama penulis atau akhiran portal yang janggal."""
    if not title:
        return ""
    
    # Potong jika ada pemisah nama media/penulis di akhir judul
    parts = title.split(' - ')
    if len(parts) > 1:
        # Jika bagian terakhir terlihat seperti nama media atau penulis pendek
        if len(parts[-1]) < 30:
            title = ' - '.join(parts[:-1])
            
    return clean_text(title)

def fetch_article_body_text(url):
    """Mengambil teks paragraf utama artikel & membersihkan elemen sidebar/baca juga."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=6, verify=False)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hapus elemen pengganggu (sidebar, footer, ad, widget)
        for element in soup(["aside", "footer", "nav", "script", "style", "form"]):
            element.extract()
            
        for div in soup.find_all(["div", "section"], class_=re.compile(r'(sidebar|related|baca-juga|ad-|recommendation|widget)', re.I)):
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
    if any(k in text_to_check for k in ['pakar', 'akademisi', 'dosen', 'pengamat', 'peneliti', 'tanggapan', 'dorong', 'soroti']):
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
        # Opini/analisis akademisi UNESA selalu dianggap Positif/Netral
        sentimen = "Positif" if any(k in text_to_check for k in ['solusi', 'dorong', 'inovasi', 'bantu', 'mekanisme']) else "Netral"
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa']):
        sentimen = "Negatif"
    elif any(k in text_to_check for k in ['juara', 'unggul', 'sukses', 'bangga', 'resmi', 'apresiasi']):
        sentimen = "Positif"
    else:
        sentimen = "Netral"

    return kategori, sentimen

def filter_row_validity(row):
    """Menyaring baris data apakah valid sebagai berita UNESA."""
    title = str(row.get('judul', '')).lower()
    link = str(row.get('link', '')).lower()
    
    # Cek Blocklist Domain & Kata Kunci
    if any(dom in link for dom in BLOCKLIST_DOMAINS):
        return False
    if any(kw in title for kw in BLOCKLIST_KEYWORDS):
        return False
    if len(title) < 15: # Filter judul terlalu pendek / nama penulis
        return False
        
    return True

def clean_and_reclassify_dataframe(df):
    """Membersihkan dan mengklasifikasi ulang seluruh isi dataframe."""
    cleaned_rows = []
    
    for _, row in df.iterrows():
        if not filter_row_validity(row):
            continue
            
        title = clean_title(str(row.get('judul', '')))
        link = str(row.get('link', ''))
        body_text = fetch_article_body_text(link)
        
        # Verifikasi ulang keberadaan kata UNESA
        contains_unesa_title = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', title, re.I))
        contains_unesa_body = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', body_text, re.I))

        if not (contains_unesa_title or contains_unesa_body):
            continue

        kategori, sentimen = classify_news(title, body_text)
        
        row_dict = row.to_dict()
        row_dict['judul'] = title
        row_dict['kategori'] = kategori
        row_dict['sentimen'] = sentimen
        cleaned_rows.append(row_dict)

    return pd.DataFrame(cleaned_rows)

def fetch_external_news():
    print("=== MENGAMBIL BERITA EKSTERNAL & MEMBERSIHKAN DATABASE CSV ===")
    
    # 1. Bersihkan Data Lama di CSV Terlebih Dahulu
    try:
        df_old = pd.read_csv(CSV_FILE)
        print(f"[INFO] Memuat {len(df_old)} data lama dari CSV untuk dibersihkan...")
        df_old_clean = clean_and_reclassify_dataframe(df_old)
    except Exception:
        df_old_clean = pd.DataFrame()

    # 2. Ambil Berita Baru dari Feed
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

            row_tmp = {'judul': title, 'link': link}
            if not filter_row_validity(row_tmp):
                continue

            body_text = fetch_article_body_text(link)
            contains_unesa_title = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', title, re.I))
            contains_unesa_body = bool(re.search(r'\b(unesa|universitas negeri surabaya)\b', body_text, re.I))

            if not (contains_unesa_title or contains_unesa_body):
                continue

            kategori, sentimen = classify_news(title, body_text)

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
