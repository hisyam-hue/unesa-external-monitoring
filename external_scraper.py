import pandas as pd
import feedparser
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

RSS_URLS = [
    "https://news.google.com/rss/search?q=UNESA&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=Universitas+Negeri+Surabaya&hl=id&gl=ID&ceid=ID:id",
    "https://www.antaranews.com/rss/terkini.xml"
]

CSV_FILE = "rekap_berita_eksternal.csv"

BLOCKLIST_KEYWORDS = [
    "disewakan", "dijual", "siap huni", "kost", "kontrakan", 
    "tanah dijual", "rumah dijual", "over kredit", "shm",
    "login", "reset password", "email reset", "portal mahasiswa",
    "pencurian dan perusakan fasilitas umum", "wali kota ajak warga",
    "kebun binatang surabaya", "pemkot surabaya gandeng kejati"
]

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
    if not title:
        return ""
    parts = title.split(' - ')
    if len(parts) > 1 and len(parts[-1]) < 30:
        title = ' - '.join(parts[:-1])
    return clean_text(title)

def fetch_article_body_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5, verify=False)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(["aside", "footer", "nav", "script", "style", "form"]):
            element.extract()
            
        for div in soup.find_all(["div", "section", "article", "blockquote"], class_=re.compile(r'(sidebar|related|baca-juga|ad-|recommendation|widget|pilihan-redaksi|detail-tag|insert|multi-link)', re.I)):
            div.extract()

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
    text_to_check = (title + " " + body_text).lower()
    
    # Kategori
    if any(k in text_to_check for k in ['pakar', 'akademisi', 'dosen', 'pengamat', 'peneliti', 'tanggapan', 'dorong', 'soroti', 'pakar unesa']):
        kategori = "Pikiran Pakar"
    elif any(k in text_to_check for k in ['prestasi', 'juara', 'medali', 'penghargaan', 'beasiswa']):
        kategori = "Prestasi & Penghargaan"
    elif any(k in text_to_check for k in ['riset', 'inovasi', 'paten', 'penelitian', 'karya']):
        kategori = "Riset & Inovasi"
    elif any(k in text_to_check for k in ['mahasiswa', 'ukm', 'pemira', 'bem', 'kkn', 'magang']):
        kategori = "Kemahasiswaan"
    elif any(k in text_to_check for k in ['pengabdian', 'masyarakat', 'binaan', 'desa', 'layani pemeriksaan', 'kesehatan gratis', 'turun ke wilayah bencana', 'tim dokter']):
        kategori = "Pengabdian Masyarakat"
    elif any(k in text_to_check for k in ['kerjasama', 'mou', 'kunjungan', 'mitra']):
        kategori = "Kerjasama & Internasional"
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa', 'pelecehan seksual', 'kejahatan seksual']):
        kategori = "Isu Hukum & PPKS"
    else:
        kategori = "Akademik & Umum"

    # Sentimen (Baksos Tim Dokter UNESA WAJIB POSITIF)
    if any(k in text_to_check for k in ['kesehatan gratis', 'bantuan bencana', 'tim dokter unesa', 'pemeriksaan gratis', 'layani pemeriksaan']):
        sentimen = "Positif"
    elif kategori == "Pikiran Pakar":
        sentimen = "Positif" if any(k in text_to_check for k in ['solusi', 'dorong', 'inovasi', 'bantu', 'mekanisme']) else "Netral"
    elif any(k in text_to_check for k in ['dugaan persekusi', 'kasus kekerasan', 'korupsi unesa', 'pungli unesa', 'pelecehan seksual', 'kejahatan seksual', 'kekerasan seksual']):
        sentimen = "Negatif"
    elif any(k in text_to_check for k in ['juara', 'unggul', 'sukses', 'bangga', 'resmi', 'apresiasi']):
        sentimen = "Positif"
    else:
        sentimen = "Netral"

    # Sub-Isu Krisis
    sub_isu = "-"
    if sentimen == "Negatif":
        if any(k in text_to_check for k in ['pelecehan', 'kekerasan seksual', 'kejahatan seksual', 'diskors', 'persekusi', 'ppks', 'wa diskors']):
            sub_isu = "Kekerasan Seksual & PPKS"
        elif any(k in text_to_check for k in ['pencurian', 'mencuri', 'korupsi', 'pungli', 'narkoba', 'polisi', 'ditangkap', 'sengketa', 'hukum']):
            sub_isu = "Tindak Kriminal & Hukum"
        elif any(k in text_to_check for k in ['bunuh diri', 'tewas', 'gantung diri', 'tenggelam', 'kecelakaan', 'korban']):
            sub_isu = "Insiden & Kesehatan Mental"
        else:
            sub_isu = "Isu Akademik & Kemahasiswaan"

    return kategori, sentimen, sub_isu

def filter_and_clean_existing_csv():
    try:
        df = pd.read_csv(CSV_FILE)
        initial_len = len(df)
        
        pattern_domains = '|'.join([re.escape(d) for d in BLOCKLIST_DOMAINS])
        pattern_keywords = '|'.join([re.escape(k) for k in BLOCKLIST_KEYWORDS])
        
        df = df[~df['link'].astype(str).str.contains(pattern_domains, case=False, na=False)]
        df = df[~df['judul'].astype(str).str.contains(pattern_keywords, case=False, na=False)]
        
        # Hapus berita Pemkot/KBS jika tidak menyebutkan UNESA
        noise_keywords = ['bulukumba', 'bogor', 'sidoarjo', 'kapolrestabes surabaya', 'wali kota ajak warga', 'pencurian dan perusakan', 'kebun binatang surabaya', 'pemkot surabaya gandeng kejati']
        pattern_noise = '|'.join(noise_keywords)
        
        rows_to_keep = []
        for idx, row in df.iterrows():
            title = str(row['judul']).lower()
            
            if re.search(pattern_noise, title) and not re.search(r'\b(unesa|universitas negeri surabaya)\b', title):
                continue
                
            kat, sen, sub = classify_news(row['judul'], "")
            row_dict = row.to_dict()
            row_dict['kategori'] = kat
            row_dict['sentimen'] = sen
            row_dict['sub_isu'] = sub
            
            rows_to_keep.append(row_dict)
            
        df_clean = pd.DataFrame(rows_to_keep)
        print(f"[CLEANUP] Berhasil membersihkan CSV lama: dari {initial_len} menjadi {len(df_clean)} berita.")
        return df_clean
    except Exception as e:
        print(f"[WARN] Gagal membersihkan CSV lama: {e}")
        return pd.DataFrame()

def fetch_external_news():
    print("=== SCRAPING & CLEANING FINAL ===")
    
    df_old_clean = filter_and_clean_existing_csv()

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

            kategori, sentimen, sub_isu = classify_news(title, body_text)

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
                'sub_isu': sub_isu,
                'tier_media': "Tier 1 (Nasional)" if any(m in source_name.lower() for m in ['kompas','detik','antara','cnn']) else "Tier 2 (Regional)",
                'link': link
            })

    df_new = pd.DataFrame(news_list)
    df_combined = pd.concat([df_new, df_old_clean]).drop_duplicates(subset=['judul'], keep='first')
    
    if not df_combined.empty:
        df_combined.to_csv(CSV_FILE, index=False)
        print(f"[SUKSES] Saved {len(df_combined)} items to '{CSV_FILE}'.")

if __name__ == "__main__":
    fetch_external_news()
