import feedparser
import pandas as pd
import requests
import urllib.parse
import re
from datetime import datetime

CSV_FILE = "rekap_berita_eksternal.csv"

DATE_RANGES = [
    # Januari 2026
    ("2026-01-01", "2026-01-10", "Januari (Awal)"),
    ("2026-01-11", "2026-01-20", "Januari (Tengah)"),
    ("2026-01-21", "2026-01-31", "Januari (Akhir)"),
    # Februari 2026
    ("2026-02-01", "2026-02-10", "Februari (Awal)"),
    ("2026-02-11", "2026-02-20", "Februari (Tengah)"),
    ("2026-02-21", "2026-02-28", "Februari (Akhir)"),
    # Maret 2026
    ("2026-03-01", "2026-03-10", "Maret (Awal)"),
    ("2026-03-11", "2026-03-20", "Maret (Tengah)"),
    ("2026-03-21", "2026-03-31", "Maret (Akhir)"),
    # April 2026
    ("2026-04-01", "2026-04-10", "April (Awal)"),
    ("2026-04-11", "2026-04-20", "April (Tengah)"),
    ("2026-04-21", "2026-04-30", "April (Akhir)"),
    # Mei 2026
    ("2026-05-01", "2026-05-10", "Mei (Awal)"),
    ("2026-05-11", "2026-05-20", "Mei (Tengah)"),
    ("2026-05-21", "2026-05-31", "Mei (Akhir)"),
    # Juni 2026
    ("2026-06-01", "2026-06-10", "Juni (Awal)"),
    ("2026-06-11", "2026-06-20", "Juni (Tengah)"),
    ("2026-06-21", "2026-06-30", "Juni (Akhir)"),
    # Juli 2026
    ("2026-07-01", "2026-07-10", "Juli (Awal)"),
    ("2026-07-11", "2026-07-20", "Juli (Tengah)"),
    ("2026-07-21", "2026-07-31", "Juli (Akhir)"),
    # Agustus 2026
    ("2026-08-01", "2026-08-10", "Agustus (Awal)"),
    ("2026-08-11", "2026-08-20", "Agustus (Tengah)"),
    ("2026-08-21", "2026-08-31", "Agustus (Akhir)"),
    # September 2026
    ("2026-09-01", "2026-09-10", "September (Awal)"),
    ("2026-09-11", "2026-09-20", "September (Tengah)"),
    ("2026-09-21", "2026-09-30", "September (Akhir)")
]

EXCLUDE_QUERY = "-site:unesa.ac.id -site:scholar.google.com -site:instagram.com -site:youtube.com -site:facebook.com -site:tiktok.com -site:twitter.com -site:linkedin.com"
KEYWORDS = [f'"UNESA" {EXCLUDE_QUERY}', f'"Universitas Negeri Surabaya" {EXCLUDE_QUERY}']

BLOCKED_KEYWORDS = [
    'linkedin', 'x.com', 'twitter', 'facebook', 'instagram', 'youtube', 'tiktok',
    'scholar', 'researchgate', 'academia.edu', 'garuda.kemdikbud', 'neliti',
    'semanticscholar', 'youtu.be', 'pinterest', 'journal', 'jurnal', 'ejournal', 
    'ojs', 'article/view', 'view/file', 'download/pdf', 'repository'
]

CAMPUS_KEYWORDS = [
    'universitas', 'institut', 'politeknik', 'sekolah tinggi', 'akademi',
    'univ ', 'ac.id', '.edu', 'uin ', 'iain', 'isi ', 'isbi'
]

def clean_text(text):
    if not text:
        return ""
    return ' '.join(text.split())

def is_blocked_site(nama_media, link):
    combined = (nama_media + " " + link).lower()
    return any(b in combined for b in BLOCKED_KEYWORDS)

def classify_media_type_and_tier(nama_media, link):
    combined = (nama_media + " " + link).lower()

    if any(ck in combined for ck in CAMPUS_KEYWORDS) and 'unesa' not in combined:
        return "Portal Kampus / Akademik", "Tier Kampus Mitra"

    tier1_keywords = [
        'detik', 'kompas', 'antara', 'liputan6', 'cnnindonesia', 'jawapos', 
        'tempo', 'merdeka', 'republika', 'viva', 'cnbcindonesia', 'sindonews',
        'tribunnews', 'inews', 'okezone', 'kumparan', 'idntimes', 'bisnis.com'
    ]
    
    tier2_keywords = [
        'radar', 'beritajatim', 'lensaindonesia', 'surabayapagi', 'suarasurabaya', 
        'duta', 'jatim', 'surabaya', 'memorandum', 'kabarbisnis', 'timesindonesia',
        'antara jatim', 'rri'
    ]

    if any(k in combined for k in tier1_keywords):
        return "Media Massa / Pers", "Tier 1 (Nasional)"
    elif any(k in combined for k in tier2_keywords):
        return "Media Massa / Pers", "Tier 2 (Regional)"
    else:
        return "Media Massa / Pers", "Tier 3 (Lokal/Independen)"

def classify_category_and_sentiment(judul):
    j = judul.lower()
    
    # Kata Kunci Krisis Murni Menggunakan Boundary \b (Mencegah Salah Cocok Substring 'ks' di 'fleksibel' atau 'prediksi')
    crisis_pattern = r'\b(kekerasan|pelecehan|seksual|ppks|skandal|korupsi|sengketa|protes|demo|polisi|polda|kejati|pembunuhan|kriminal|pidana|pemeriksaan|tersangka|pelanggaran)\b'
    mitigation_pattern = r'\b(gerak cepat|tindak tegas|usut|usut tuntas|sanksi tegas|bentuk satgas|tangani|penanganan|dampingi|komitmen|sikat|tindak lanjut|solusi|respons|langkah tegas|diapresiasi|transparan|tuntaskan|pemberhentian)\b'

    has_crisis = bool(re.search(crisis_pattern, j))
    has_mitigation = bool(re.search(mitigation_pattern, j))

    if has_crisis and has_mitigation:
        kategori = "Penanganan Krisis & PPKS"
        sentimen = "Positif"
    elif has_crisis:
        kategori = "Isu Hukum & PPKS"
        sentimen = "Negatif"
    elif re.search(r'\b(juara|raih|medali|penghargaan|prestasi|unggul|rekor|borong|sabet)\b', j):
        kategori = "Prestasi & Penghargaan"
        sentimen = "Positif"
    elif re.search(r'\b(penelitian|inovasi|riset|ciptakan|karya|teknologi|robot|paten|buku|kajian)\b', j):
        kategori = "Riset & Inovasi"
        sentimen = "Positif"
    elif re.search(r'\b(maba|ukm|ormawa|mahasiswa|kkn|duta|batu|pkkmb|magang|pelepasan)\b', j):
        kategori = "Kemahasiswaan"
        sentimen = "Netral"
    elif re.search(r'\b(pengabdian|masyarakat|bina|pendampingan|pelatihan)\b', j):
        kategori = "Pengabdian Masyarakat"
        sentimen = "Positif"
    elif re.search(r'\b(mou|kerja sama|kerjasama|mitra|gaet|gandeng|internasional|visiting)\b', j):
        kategori = "Kerjasama & Internasional"
        sentimen = "Positif"
    elif re.search(r'\b(pakar|pengamat|kata dosen|menurut pakar|tanggapan akademisi|opini|edukasi|penyakit|infeksi|bahaya)\b', j):
        kategori = "Pikiran Pakar"
        sentimen = "Netral"
    elif re.search(r'\b(utbk|snbp|snbt|prediksi|lolos|pendaftaran|persyaratan|fasilitas|hybrid|fleksibel)\b', j):
        kategori = "Akademik & Admisi"
        sentimen = "Netral"
    else:
        kategori = "Akademik & Umum"
        sentimen = "Netral"

    # Penyesuaian Sentimen Akhir
    if sentimen == "Netral" and not has_crisis:
        if re.search(r'\b(juara|sukses|banggakan|prestasi|apresiasi|inovasi|lulus|resmikan|hebat|terbaik|dukung|positif|lolos|fleksibel)\b', j):
            sentimen = "Positif"
        elif re.search(r'\b(dugaan penyelewengan|skandal|pencurian|penganiayaan|penipuan|pungli)\b', j):
            sentimen = "Negatif"

    return kategori, sentimen

def fetch_google_news_rss(keyword, start_date, end_date):
    query = f'{keyword} after:{start_date} before:{end_date}'
    encoded_kw = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=id&gl=ID&ceid=ID:id"
    
    feed = feedparser.parse(rss_url)
    articles = []
    
    for entry in feed.entries:
        link = entry.link
        judul = clean_text(entry.title)

        nama_media = "Media Online"
        if " - " in judul:
            parts = judul.rsplit(" - ", 1)
            judul_bersih = parts[0]
            nama_media = parts[1]
        else:
            judul_bersih = judul

        if 'unesa.ac.id' in link.lower() or 'unesa' in nama_media.lower():
            continue

        if is_blocked_site(nama_media, link):
            continue

        tgl_raw = entry.get('published', '')
        try:
            dt = datetime.strptime(tgl_raw, '%a, %d %b %Y %H:%M:%S %Z')
            if dt.year != 2026:
                continue
            tgl_formatted = dt.strftime('%d %B %Y')
        except:
            tgl_formatted = tgl_raw

        tipe_sumber, tier_media = classify_media_type_and_tier(nama_media, link)
        kategori, sentimen = classify_category_and_sentiment(judul_bersih)

        articles.append({
            'tanggal': tgl_formatted,
            'nama_media': nama_media,
            'tipe_sumber': tipe_sumber,
            'tier_media': tier_media,
            'judul': judul_bersih,
            'kategori': kategori,
            'sentimen': sentimen,
            'link': link,
            'sumber_engine': 'Google News RSS (10-Daily)'
        })
        
    return articles

def run_external_monitoring():
    print("=== MEMULAI PENJARINGAN DATA DENGAN REGEX STRICT BOUNDARY (2026) ===")
    all_articles = []

    for start_date, end_date, label_periode in DATE_RANGES:
        print(f"\n[+] Memproses Periode: {label_periode} ({start_date} s.d {end_date})")
        
        for kw in KEYWORDS:
            g_news = fetch_google_news_rss(kw, start_date, end_date)
            print(f"    - Query Ditemukan {len(g_news)} data eksternal valid")
            all_articles.extend(g_news)

    if not all_articles:
        print("\nTidak ada artikel yang ditemukan.")
        return

    df = pd.DataFrame(all_articles)
    df_clean = df.drop_duplicates(subset=['link']).copy()
    df_clean = df_clean.drop_duplicates(subset=['judul']).copy()

    df_clean.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    print(f"\n[SUKSES REVISI] Total {len(df_clean)} berita eksternal murni berhasil direkap ke '{CSV_FILE}'.")

if __name__ == "__main__":
    run_external_monitoring()