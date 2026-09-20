import pandas as pd
import json

def generate_dashboard():
    csv_file = 'rekap_berita_eksternal.csv'
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Gagal membaca CSV: {e}")
        return

    df.fillna('', inplace=True)
    
    # Deteksi nama kolom secara dinamis
    col_tgl = 'tanggal' if 'tanggal' in df.columns else df.columns[0]
    col_media = 'media' if 'media' in df.columns else ('sumber' if 'sumber' in df.columns else df.columns[1])
    col_judul = 'judul' if 'judul' in df.columns else df.columns[2]
    col_kat = 'kategori' if 'kategori' in df.columns else 'Akademik & Umum'
    col_sent = 'sentimen' if 'sentimen' in df.columns else 'Netral'
    col_url = 'url' if 'url' in df.columns else ('link' if 'link' in df.columns else '#')

    # Sorting berdasarkan tanggal terbaru
    df['dt_temp'] = pd.to_datetime(df[col_tgl], errors='coerce')
    df = df.sort_values(by='dt_temp', ascending=False)

    # Hitung Statistik Utama
    total_berita = len(df)
    media_pers = len(df[df[col_media].astype(str).str.contains('Media|Pers|Portal|Kompas|Detik|Surabaya|Tribun|Jawa|Disway|iNews|Antara', case=False, na=False)]) if col_media in df.columns else total_berita
    persen_pers = round((media_pers / total_berita * 100), 1) if total_berita > 0 else 0
    
    positif = len(df[df[col_sent].astype(str).str.lower() == 'positif']) if col_sent in df.columns else 0
    negatif = len(df[df[col_sent].astype(str).str.lower() == 'negatif']) if col_sent in df.columns else 0
    netral = total_berita - (positif + negatif)
    
    persen_pos = round((positif / total_berita * 100), 1) if total_berita > 0 else 0
    persen_neg = round((negatif / total_berita * 100), 1) if total_berita > 0 else 0

    # Data Chart Tren Bulanan
    bulan_list = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    monthly_counts = [0] * 12
    
    for dt in df['dt_temp']:
        if pd.notnull(dt):
            m = dt.month - 1
            if 0 <= m < 12:
                monthly_counts[m] += 1

    # Breakdown Tier Media (Estimasi Berdasarkan Publisher)
    tier1_count = len(df[df[col_media].astype(str).str.contains('Kompas|Detik|Antara|CNN|iNews|Tempo|Liputan6|Republika|Sindonews|Merdeka', case=False, na=False)])
    tier2_count = media_pers - tier1_count if media_pers > tier1_count else 0
    tier_akademik = total_berita - media_pers

    # Breakdown Tema/Kategori
    kat_counts = df[col_kat].value_counts().to_dict() if col_kat in df.columns else {}
    top_kat_html = ""
    for k, v in list(kat_counts.items())[:5]:
        if not k: k = "Akademik & Umum"
        pct = round((v / total_berita * 100), 1) if total_berita > 0 else 0
        top_kat_html += f"""
        <div class="space-y-1">
            <div class="flex justify-between text-xs font-semibold">
                <span class="text-slate-700">{k}</span>
                <span class="text-slate-500">{v} Berita ({pct}%)</span>
            </div>
            <div class="w-full bg-slate-100 rounded-full h-2">
                <div class="bg-blue-600 h-2 rounded-full" style="width: {pct}%"></div>
            </div>
        </div>
        """

    # Ambil 100 berita TERBARU untuk tabel
    top_df = df.head(100)
    table_rows = ""
    for idx, row in top_df.iterrows():
        tgl = row.get(col_tgl, '-')
        med = row.get(col_media, '-') if row.get(col_media, '-') != '' else 'Media Pers'
        kat = row.get(col_kat, 'Akademik & Umum') if row.get(col_kat, '') != '' else 'Akademik & Umum'
        jdl = row.get(col_judul, '-')
        snt = row.get(col_sent, 'Netral') if row.get(col_sent, '') != '' else 'Netral'
        url = row.get(col_url, '#')
        
        badge_cls = 'bg-slate-100 text-slate-700'
        if str(snt).lower() == 'positif':
            badge_cls = 'bg-emerald-100 text-emerald-700 font-semibold'
        elif str(snt).lower() == 'negatif':
            badge_cls = 'bg-rose-100 text-rose-700 font-semibold'

        table_rows += f"""
        <tr class="hover:bg-slate-50 border-b border-slate-100 text-sm">
            <td class="py-3 px-4 whitespace-nowrap text-slate-500">{tgl}</td>
            <td class="py-3 px-4 font-semibold text-slate-800">{med}</td>
            <td class="py-3 px-4"><span class="px-2.5 py-1 bg-blue-50 text-blue-600 rounded-md text-xs font-medium">{kat}</span></td>
            <td class="py-3 px-4 text-slate-900 font-medium">{jdl}</td>
            <td class="py-3 px-4"><span class="px-2.5 py-1 rounded-full text-xs {badge_cls}">{snt}</span></td>
            <td class="py-3 px-4 text-right"><a href="{url}" target="_blank" class="text-blue-600 hover:text-blue-800 text-xs font-semibold">Buka ↗</a></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Pemberitaan Eksternal UNESA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style> body {{ font-family: 'Inter', sans-serif; }} </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen pb-12">

    <!-- Header / Navbar -->
    <header class="bg-slate-900 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <span class="bg-blue-600 text-xs font-bold px-2.5 py-1 rounded-md tracking-wide uppercase">EKSTERNAL</span>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">Monitoring Pemberitaan Eksternal UNESA</h1>
                    <p class="text-xs text-slate-400">Analisis Media Massa Digital, Sentiment Tracking & Detektor Isu (2026)</p>
                </div>
            </div>
            <div class="bg-slate-800 border border-slate-700 text-emerald-400 text-xs font-semibold px-3 py-1.5 rounded-full flex items-center space-x-2">
                <span class="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                <span>{total_berita} Data Relevan Loaded</span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 space-y-10">

        <!-- SECTION 1: IKHTISAR & KEY METRICS -->
        <section>
            <div class="flex items-center space-x-2 mb-4">
                <div class="w-1.5 h-5 bg-blue-600 rounded-full"></div>
                <h2 class="text-lg font-bold text-slate-900 uppercase tracking-wide">Ikhtisar & Key Metrics</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm border-l-4 border-l-blue-600">
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Publikasi</p>
                    <h3 class="text-2xl font-bold text-slate-900 mt-1">{total_berita}</h3>
                    <p class="text-xs text-slate-500 mt-1">Januari - September 2026</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm border-l-4 border-l-emerald-500">
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Publikasi Media Pers</p>
                    <h3 class="text-2xl font-bold text-slate-900 mt-1">{media_pers}</h3>
                    <p class="text-xs text-emerald-600 font-medium mt-1">{persen_pers}% dari Total Data</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm border-l-4 border-l-purple-500">
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tema Terpopuler</p>
                    <h3 class="text-lg font-bold text-slate-900 mt-1 truncate">Akademik & Inovasi</h3>
                    <p class="text-xs text-slate-500 mt-1">Dominasi Publikasi</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm border-l-4 border-l-teal-500">
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sentimen Positif</p>
                    <h3 class="text-2xl font-bold text-slate-900 mt-1">{positif}</h3>
                    <p class="text-xs text-teal-600 font-medium mt-1">{persen_pos}% Tone Positif</p>
                </div>
                <div class="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm border-l-4 border-l-rose-500">
                    <p class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Isu / Tone Negatif</p>
                    <h3 class="text-2xl font-bold text-slate-900 mt-1">{negatif}</h3>
                    <p class="text-xs text-rose-600 font-semibold mt-1">⚠️ Perlu Atensi Humas</p>
                </div>
            </div>
        </section>

        <!-- SECTION 2: ANALISIS DETAIL (TEMA, TIER MEDIA & SENTIMEN) -->
        <section>
            <div class="flex items-center space-x-2 mb-4">
                <div class="w-1.5 h-5 bg-purple-600 rounded-full"></div>
                <h2 class="text-lg font-bold text-slate-900 uppercase tracking-wide">Analisis Tema, Tier Media & Sentimen</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                <!-- Box 1: Analisis Tema & Kategori -->
                <div class="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
                    <div class="border-b border-slate-100 pb-3">
                        <h3 class="text-base font-bold text-slate-900">Distribusi Kategori Tema</h3>
                        <p class="text-xs text-slate-500">Topik berita paling banyak dipublikasikan</p>
                    </div>
                    <div class="space-y-3">
                        {top_kat_html}
                    </div>
                </div>

                <!-- Box 2: Analisis Tier Media -->
                <div class="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
                    <div class="border-b border-slate-100 pb-3">
                        <h3 class="text-base font-bold text-slate-900">Analisis Tier Media Massa</h3>
                        <p class="text-xs text-slate-500">Klasifikasi kredibilitas & jangkauan penerbit</p>
                    </div>
                    <div class="space-y-3">
                        <div class="p-3 bg-blue-50/60 rounded-lg border border-blue-100 flex justify-between items-center">
                            <div>
                                <p class="text-xs font-bold text-blue-900">Tier 1: Media Nasional Utama</p>
                                <p class="text-[11px] text-blue-600">Kompas, Detik, Antara, Tempo, dll</p>
                            </div>
                            <span class="text-base font-extrabold text-blue-700">{tier1_count}</span>
                        </div>
                        <div class="p-3 bg-emerald-50/60 rounded-lg border border-emerald-100 flex justify-between items-center">
                            <div>
                                <p class="text-xs font-bold text-emerald-900">Tier 2: Media Regional & Disway</p>
                                <p class="text-[11px] text-emerald-600">Surabaya Pagi, Disway, JatimNet, dll</p>
                            </div>
                            <span class="text-base font-extrabold text-emerald-700">{tier2_count}</span>
                        </div>
                        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 flex justify-between items-center">
                            <div>
                                <p class="text-xs font-bold text-slate-800">Portal Akademik & Lainnya</p>
                                <p class="text-[11px] text-slate-500">Blog kampus & rilis publik</p>
                            </div>
                            <span class="text-base font-extrabold text-slate-700">{tier_akademik}</span>
                        </div>
                    </div>
                </div>

                <!-- Box 3: Analisis Ringkasan Sentimen -->
                <div class="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
                    <div class="border-b border-slate-100 pb-3">
                        <h3 class="text-base font-bold text-slate-900">Analisis Sentimen Berita</h3>
                        <p class="text-xs text-slate-500">Kondisi persepsi publik terhadap UNESA</p>
                    </div>
                    <div class="space-y-3">
                        <div class="p-3 bg-emerald-50/80 rounded-lg border border-emerald-200 flex justify-between items-center">
                            <span class="text-xs font-bold text-emerald-800">Tone Positif (Apresiasi/Prestasi)</span>
                            <span class="text-sm font-extrabold text-emerald-700">{positif} ({persen_pos}%)</span>
                        </div>
                        <div class="p-3 bg-slate-100 rounded-lg border border-slate-200 flex justify-between items-center">
                            <span class="text-xs font-bold text-slate-700">Tone Netral (Informatif)</span>
                            <span class="text-sm font-extrabold text-slate-700">{netral}</span>
                        </div>
                        <div class="p-3 bg-rose-50/80 rounded-lg border border-rose-200 flex justify-between items-center">
                            <span class="text-xs font-bold text-rose-800">Tone Negatif / Potensi Isu</span>
                            <span class="text-sm font-extrabold text-rose-700">{negatif} ({persen_neg}%)</span>
                        </div>
                    </div>
                </div>

            </div>
        </section>

        <!-- SECTION 3: ANALISIS TREN BULANAN & DISTRIBUSI GRAPH -->
        <section>
            <div class="flex items-center space-x-2 mb-4">
                <div class="w-1.5 h-5 bg-indigo-600 rounded-full"></div>
                <h2 class="text-lg font-bold text-slate-900 uppercase tracking-wide">Grafik Volume & Proporsi Sentimen</h2>
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900 mb-1">Volume Pemberitaan per Bulan (2026)</h3>
                    <p class="text-xs text-slate-500 mb-4">Tren jumlah publikasi berita eksternal harian/bulanan</p>
                    <div class="h-64">
                        <canvas id="trendChart"></canvas>
                    </div>
                </div>
                <div class="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
                    <h3 class="text-base font-bold text-slate-900 mb-1">Distribusi Sentimen Berita</h3>
                    <p class="text-xs text-slate-500 mb-4">Proporsi Tone Positif, Netral & Negatif</p>
                    <div class="h-64 flex justify-center items-center">
                        <canvas id="sentimentChart"></canvas>
                    </div>
                </div>
            </div>
        </section>

        <!-- SECTION 4: REKAP DATA BERITA TERKINI -->
        <section>
            <div class="flex items-center space-x-2 mb-4">
                <div class="w-1.5 h-5 bg-emerald-600 rounded-full"></div>
                <h2 class="text-lg font-bold text-slate-900 uppercase tracking-wide">Rekap Pemberitaan Eksternal Terkini</h2>
            </div>
            <div class="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div class="p-5 border-b border-slate-100">
                    <p class="text-xs text-slate-500">Disaring berdasarkan kriteria relevansi pemberitaan akademik UNESA & diurutkan dari yang terbaru</p>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="bg-slate-50 border-b border-slate-200/80 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                <th class="py-3 px-4">Tanggal</th>
                                <th class="py-3 px-4">Media / Sumber</th>
                                <th class="py-3 px-4">Kategori Tema</th>
                                <th class="py-3 px-4">Judul Berita</th>
                                <th class="py-3 px-4">Sentimen</th>
                                <th class="py-3 px-4 text-right">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <script>
        // Tren Chart (Warna-warni)
        const ctxTrend = document.getElementById('trendChart').getContext('2d');
        new Chart(ctxTrend, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(bulan_list)},
                datasets: [{{
                    label: 'Jumlah Berita',
                    data: {json.dumps(monthly_counts)},
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', 
                        '#ec4899', '#06b6d4', '#84cc16', '#6366f1', 
                        '#14b8a6', '#f97316', '#a855f7', '#64748b'
                    ],
                    borderRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true }} }}
            }}
        }});

        // Sentimen Chart
        const ctxSent = document.getElementById('sentimentChart').getContext('2d');
        new Chart(ctxSent, {{
            type: 'doughnut',
            data: {{
                labels: ['Positif', 'Netral', 'Negatif'],
                datasets: [{{
                    data: [{positif}, {netral}, {negatif}],
                    backgroundColor: ['#10b981', '#cbd5e1', '#f43f5e']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom' }} }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open('dashboard_eksternal.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("Dashboard HTML berhasil diperbarui!")

if __name__ == '__main__':
    generate_dashboard()
