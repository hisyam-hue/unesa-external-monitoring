import feedparser
import pandas as pd
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime

# File output CSV
CSV_FILE = "rekap_berita_eksternal.csv"

# 1. DOMAIN BLOCKLIST (Abaikan situs properti, iklan, dan marketplace)
BLOCKED_DOMAINS = [
    'rumah123.com', 'olx.co.id', 'lamudi.co.id', 'rumah.com', 'carousell.com',
    'shopee.co.id', 'tokopedia.com', 'facebook.com', 'instagram.com', 'tiktok.com'
]

# 2. ADVERTISEMENT & REAL ESTATE KEYWORDS
AD_KEYWORDS = [
    'disewakan', 'dijual', 'siap huni', 'sewa rumah', 'kost', 'kontrakan',
    'dkt unesa', 'dekat unesa', 'jual rumah', 'over kredit', 'kavling'
]

# 3. EXPERT / ACADEMIC KEYWORDS
EXPERT_KEYWORDS = [
    'pakar', 'akademisi', 'dosen', 'pengamat', 'peneliti', 'pakar unesa',
    'akademisi unesa', 'tanggapan pakar', 'kata pakar', 'pandangan pakar'
]

# 4. TRUE NEGATIVE CRISIS KEYWORDS (Hanya jika krisis MENGINFEKSI / DILAKUKAN / TERJADI DI UNESA)
TRUE_NEGATIVE_KEYWORDS = [
    'kasus unesa', 'dugaan pelecehan unesa', 'sanksi unesa', 'demo unesa',
    'korupsi unesa', 'kriminal unesa', 'tersangka unesa', 'kekerasan seksual unesa',
    'sanksi mahasiswa unesa', 'oknum unesa'
]

def clean_title(title):
    """Membersihkan judul dari suffix nama media (- Suara.com, - Detik.com)"""
    title = re.sub(r'\s*-\s*[A-Za-z0-9\.\s]+$', '', title)
    return title.strip()

def extract_media_name(source_title, link):
    """Mengekstrak nama media secara rapi"""
    if source_title and len(source_title) > 2:
        return source_title
    try:
        domain = urllib.parse.urlparse(link).netloc
        domain = domain.replace('www.', '')
        return domain.capitalize()
    except:
        return "Media Online"

def fetch_article_body_text(url):
    """
    Mengunduh HTML artikel dan mengekstrak HANYA Teks Utama / Paragraf Isi Artikel.
    Menghapus elemen sidebar, rekomendasi 'baca juga', iklan, dan footer.
    """
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')

        # Hapus elemen pengganggu (Sidebar, Iklan, Rekomendasi, Footer, Navigation)
        for element in soup(['script', 'style', 'aside', 'footer', 'header', 'nav', 'form']):
            element.decompose()

        # Hapus div/section yang memiliki class atau id terkait 'sidebar', 'related', 'baca-juga', 'recommendation', 'ads'
        for div in soup.find_all(['div', 'section', 'ul'], class_=re.compile(r'sidebar|related|baca-juga|recommend|banner|ad-|promo|terkait', re.I)):
            div.decompose()
        for div in soup.find_all(['div', 'section', 'ul'], id=re.compile(r'sidebar|related|baca-juga|recommend|banner|ad-|promo|terkait', re.I)):
            div.decompose()

        # Ekstrak paragraf (<p>) dalam elemen utama (<article> atau main content)
        article_body = soup.find('article') or soup.find('main') or soup
        paragraphs = article_body.find_all('p')
        body_text = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        return body_text
    except Exception:
        return ""

def classify_category_and_sentiment(title, body_text):
    """
    Logika Klasifikasi Tema dan Sentimen Berbasis Judul & Isi Artikel
    """
    combined_text = (title + " " + body_text).lower()

    # Rule A: Pakar / Akademisi UNESA memberi tanggapan/opini
    if any(k in combined_text for k in EXPERT_KEYWORDS):
        return "Pikiran Pakar", "Positif"

    # Rule B: True Negative (Hanya jika krisis terjadi LANGSUNG di UNESA/melibatkan oknum internal)
    if any(k in combined_text for k in TRUE_NEGATIVE_KEYWORDS):
        return "Isu Hukum & PPKS", "Negatif"

    # Rule C: Prestasi & Penghargaan
    if any(k in combined_text for k in ['juara', 'medali', 'penghargaan', 'prestasi', 'raih', 'sabet', 'menang', 'bonus']):
        return "Prestasi & Penghargaan", "Positif"

    # Rule D: Riset & Inovasi
    if any(k in combined_text for k in ['inovasi', 'riset', 'penelitian', 'karya', 'ciptakan', 'teknologi', 'paten']):
        return "Riset & Inovasi", "Positif"

    # Rule E: Kemahasiswaan & Olahraga
    if any(k in combined_text for k in ['mahasiswa', 'kkn', 'magang', 'atlet', 'olahraga', 'piala', 'lomba', 'pembekalan']):
        return "Kemahasiswaan", "Positif"

    # Rule F: Kerjasama & Internasional
    if any(k in combined_text for k in ['kerjasama', 'mou', 'internasional', 'pertukaran', 'mitra', 'gandeng']):
        return "Kerjasama & Internasional", "Positif"

    # Default Fallback
    return "Akademik & Umum", "Netral"

def is_valid_unesa_news(title, link, snippet=""):
    """
    Saringan Relevansi Berita UNESA
    """
    title_lower = title.lower()
    link_lower = link.lower()

    # 1. Filter Domain Iklan/Marketplace
    if any(domain in link_lower for domain in BLOCKED_DOMAINS):
        return False, ""

    # 2. Filter Kata Kunci Iklan Properti
    if any(ad_kw in title_lower for ad_kw in AD_KEYWORDS):
        return False, ""

    # 3. Ekstrak Isi Teks Utama Artikel (Bodi Berita)
    body_text = fetch_article_body_text(link)
    
    # Kombinasi teks yang dibersihkan (Bodi utama + Snippet RSS)
    clean_article_context = (body_text if body_text else snippet).lower()

    # 4. MEMERIKSA KEBERADAAN KATAKUNCI 'UNESA' DI BODI UTAMA TEKS
    # Mencegah artikel rekomendasi/sidebar dengan memastikan Unesa muncul di badan artikel
    has_unesa_in_title = ('unesa' in title_lower or 'universitas negeri surabaya' in title_lower)
    has_unesa_in_body = ('unesa' in clean_article_context or 'universitas negeri surabaya' in clean_article_context)

    if not (has_unesa_in_title or has_unesa_in_body):
        return False, ""

    return True, body_text

def fetch_external_news():
    print("=== STARTING FILTERED EXTERNAL NEWS SCRAPER (PARAGRAPH BODY VERIFICATION) ===")
    
    rss_urls = [
        "https://news.google.com/rss/search?q=UNESA&hl=id&gl=ID&ceid=ID:id",
        "https://news.google.com/rss/search?q=Universitas+Negeri+Surabaya&hl=id&gl=ID&ceid=ID:id"
    ]

    scraped_data = []
    seen_titles = set()

    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            raw_title = entry.get('title', '')
            clean_t = clean_title(raw_title)
            link = entry.get('link', '#')
            snippet = entry.get('summary', '')
            
            source_info = entry.get('source', {}).get('title', '')
            media_name = extract_media_name(source_info, link)

            pub_date = entry.get('published', '')
            try:
                dt_obj = datetime.strptime(pub_date[:16], '%a, %d %b %Y')
                formatted_date = dt_obj.strftime('%d %B %Y')
            except:
                formatted_date = datetime.now().strftime('%d %B %Y')

            # Terapkan Saringan Relevansi Berita Berbasis Bodi Utama Paragraf
            is_valid, body_text = is_valid_unesa_news(clean_t, link, snippet)
            if is_valid:
                title_key = clean_t.lower()[:30]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    
                    category, sentiment = classify_category_and_sentiment(clean_t, body_text)
                    
                    # Deteksi Tier Media
                    media_lower = media_name.lower()
                    if any(m in media_lower for m in ['kompas', 'detik', 'antara', 'tempo', 'cnn', 'tribun', 'inews', 'republika', 'liputan6', 'sindonews']):
                        tier = 'Tier 1 (Nasional)'
                    elif any(m in media_lower for m in ['surabaya', 'disway', 'jawapos', 'jatim', 'radar']):
                        tier = 'Tier 2 (Regional)'
                    else:
                        tier = 'Portal Kampus/Lain'

                    scraped_data.append({
                        'tanggal': formatted_date,
                        'nama_media': media_name,
                        'kategori': category,
                        'judul': clean_t,
                        'sentimen': sentiment,
                        'link': link,
                        'tier_media': tier
                    })

    df = pd.DataFrame(scraped_data)
    print(f"[+] Berhasil menyaring & mengumpulkan {len(df)} berita eksternal UNESA yang valid dan relevan.")
    
    if not df.empty:
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        print(f"[SUCCESS] Saved to '{CSV_FILE}'")
    else:
        print("[WARNING] Tidak ada berita baru yang memenuhi kriteria penyaringan.")

if __name__ == "__main__":
    fetch_external_news()
