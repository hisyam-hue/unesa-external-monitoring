import pandas as pd
import json

CSV_FILE = "rekap_berita_eksternal.csv"
OUTPUT_HTML = "index.html"

def generate_dashboard():
    try:
        df = pd.read_csv(CSV_FILE)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    # Hitung ringkasan utama
    total_publikasi = len(df)
    df_pers = df[df['tier_media'].isin(['Tier 1 (Nasional)', 'Tier 2 (Regional)'])]
    total_media = len(df_pers)
    
    positif_count = len(df[df['sentimen'] == 'Positif'])
    netral_count = len(df[df['sentimen'] == 'Netral'])
    negatif_count = len(df[df['sentimen'] == 'Negatif'])
    
    # Kategori Terpopuler
    kat_counts = df['kategori'].value_counts().to_dict()
    tema_terpopuler = list(kat_counts.keys())[0] if kat_counts else "Akademik & Umum"
    tema_count = list(kat_counts.values())[0] if kat_counts else 0

    # Hitung Tier Media
    tier_counts = df['tier_media'].value_counts().to_dict()

    # Hitung Sub-Isu Krisis untuk berita negatif
    df_negatif = df[df['sentimen'] == 'Negatif'].copy()
    if 'sub_isu' not in df_negatif.columns:
        df_negatif['sub_isu'] = 'Kekerasan Seksual & PPKS'
    else:
        df_negatif['sub_isu'] = df_negatif['sub_isu'].fillna('Tindak Kriminal & Hukum')
        
    sub_isu_counts = df_negatif['sub_isu'].value_counts().to_dict()

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoring Pemberitaan Eksternal UNESA</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }}
        .tab-btn.active {{ background-color: #2563eb; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto space-y-6">
        <!-- Header -->
        <div class="bg-slate-900 text-white p-6 rounded-2xl flex justify-between items-center shadow-lg">
            <div>
                <span class="bg-blue-600 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">EXTERNAL</span>
                <h1 class="text-2xl font-bold mt-2">Monitoring Pemberitaan Eksternal UNESA</h1>
                <p class="text-slate-400 text-sm">Analisis Media Massa Digital, Sentiment Tracking & Detector Isu (2026)</p>
            </div>
            <div class="flex gap-2 bg-slate-800 p-1.5 rounded-xl text-xs font-semibold text-slate-300">
                <button onclick="switchTab('ikhtisar')" id="btn-ikhtisar" class="tab-btn active px-4 py-2 rounded-lg transition">📊 Ikhtisar</button>
                <button onclick="switchTab('tema')" id="btn-tema" class="tab-btn px-4 py-2 rounded-lg transition">📊 Analisis Tren Tema</button>
                <button onclick="switchTab('tier')" id="btn-tier" class="tab-btn px-4 py-2 rounded-lg transition">📊 Analisis Tier Media</button>
                <button onclick="switchTab('tone')" id="btn-tone" class="tab-btn px-4 py-2 rounded-lg transition">🚨 Analisis Tone Pemberitaan</button>
            </div>
        </div>

        <!-- Metric Cards Top -->
        <div class="grid grid-cols-5 gap-4">
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Total Publikasi</p>
                <h3 class="text-3xl font-bold text-slate-900 mt-2">{total_publikasi}</h3>
                <span class="text-xs text-blue-600 font-medium">Januari - September 2026</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Publikasi Media Pers</p>
                <h3 class="text-3xl font-bold text-slate-900 mt-2">{total_media}</h3>
                <span class="text-xs text-emerald-600 font-medium">{round(total_media/total_publikasi*100, 1) if total_publikasi else 0}% dari Total</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Tema Terpopuler</p>
                <h3 class="text-xl font-bold text-blue-600 mt-2 truncate">{tema_terpopuler}</h3>
                <span class="text-xs text-slate-500 font-medium">{tema_count} Berita</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Sentimen Positif</p>
                <h3 class="text-3xl font-bold text-emerald-600 mt-2">{positif_count}</h3>
                <span class="text-xs text-emerald-600 font-medium">{round(positif_count/total_publikasi*100, 1) if total_publikasi else 0}% Tone Positif</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm border-l-4 border-l-rose-500">
                <p class="text-xs font-semibold text-slate-500 uppercase">Isu / Tone Negatif</p>
                <h3 class="text-3xl font-bold text-rose-600 mt-2">{negatif_count}</h3>
                <span class="text-xs text-rose-600 font-medium">{round(negatif_count/total_publikasi*100, 1) if total_publikasi else 0}% Perlu Atensi</span>
            </div>
        </div>

        <!-- TAB 1: IKHTISAR -->
        <div id="tab-ikhtisar" class="tab-content active space-y-6">
            <div class="grid grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-lg font-bold text-slate-800 mb-4">Sebaran Kategori Berita</h2>
                    <div class="h-64"><canvas id="kategoriChart"></canvas></div>
                </div>
                <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-lg font-bold text-slate-800 mb-4">Sebaran Tier Media</h2>
                    <div class="h-64"><canvas id="tierOverviewChart"></canvas></div>
                </div>
            </div>
        </div>

        <!-- TAB 2: ANALISIS TREN TEMA -->
        <div id="tab-tema" class="tab-content space-y-6">
            <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h2 class="text-lg font-bold text-slate-800 mb-4">Analisis Tren Tema Pemberitaan</h2>
                <div class="h-80"><canvas id="temaFullChart"></canvas></div>
            </div>
        </div>

        <!-- TAB 3: ANALISIS TIER MEDIA -->
        <div id="tab-tier" class="tab-content space-y-6">
            <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <h2 class="text-lg font-bold text-slate-800 mb-4">Distribusi Media Berdasarkan Tier</h2>
                <div class="h-80"><canvas id="tierFullChart"></canvas></div>
            </div>
        </div>

        <!-- TAB 4: ANALISIS TONE PEMBERITAAN -->
        <div id="tab-tone" class="tab-content space-y-6">
            <div class="grid grid-cols-12 gap-6">
                <!-- Donut Chart -->
                <div class="col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-lg font-bold text-slate-800 mb-1">Proporsi Tone Pemberitaan</h2>
                    <p class="text-xs text-slate-500 mb-4">Grafik donat persentase persepsi publik</p>
                    <div class="h-64 flex justify-center"><canvas id="toneChart"></canvas></div>
                </div>

                <!-- Horizontal Bar Chart Sub-Isu Krisis -->
                <div class="col-span-7 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <h2 class="text-lg font-bold text-slate-800">Distribusi Kategori Sub-Isu Krisis</h2>
                            <span class="bg-rose-100 text-rose-700 text-xs px-3 py-1 rounded-full font-bold">{negatif_count} Total Isu</span>
                        </div>
                        <p class="text-xs text-slate-500 mb-4">Pengelompokan berita bernada negatif berdasarkan topik spesifik</p>
                    </div>
                    <div class="h-56"><canvas id="subIsuChart"></canvas></div>
                </div>
            </div>

            <!-- Tabel Berita Negatif -->
            <div class="bg-white rounded-2xl border border-rose-200 shadow-sm overflow-hidden">
                <div class="bg-rose-50/50 p-5 border-b border-rose-100 flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-bold text-rose-900 flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse"></span>
                            Daftar Berita Tone Negatif & Isu Atensi Humas
                        </h2>
                        <p class="text-xs text-rose-600">Pemberitaan eksternal yang memerlukan mitigasi atau klarifikasi isu</p>
                    </div>
                    <span class="bg-rose-600 text-white text-xs px-3 py-1 rounded-full font-bold">{negatif_count} Isu</span>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-xs uppercase text-slate-500 sticky top-0 border-b border-slate-200">
                            <tr>
                                <th class="p-4 w-32">Tanggal</th>
                                <th class="p-4">Judul Berita</th>
                                <th class="p-4 w-52">Sub-Isu Krisis</th>
                                <th class="p-4 w-44">Nama Media</th>
                                <th class="p-4 w-24 text-center">Tone</th>
                                <th class="p-4 w-28 text-right">Link Berita</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100" id="table-negatif-body"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        const rawData = {df.to_json(orient='records')};

        function switchTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById('tab-' + tabName).classList.add('active');
            document.getElementById('btn-' + tabName).classList.add('active');
        }}

        // Donut Chart Tone
        new Chart(document.getElementById('toneChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Positif', 'Netral', 'Negatif'],
                datasets: [{{
                    data: [{positif_count}, {netral_count}, {negatif_count}],
                    backgroundColor: ['#10b981', '#cbd5e1', '#f43f5e']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        // Kategori Chart
        const katData = {json.dumps(kat_counts)};
        new Chart(document.getElementById('kategoriChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(katData),
                datasets: [{{ label: 'Jumlah Berita', data: Object.values(katData), backgroundColor: '#3b82f6', borderRadius: 6 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        // Tier Overview Chart
        const tierData = {json.dumps(tier_counts)};
        new Chart(document.getElementById('tierOverviewChart'), {{
            type: 'pie',
            data: {{
                labels: Object.keys(tierData),
                datasets: [{{ data: Object.values(tierData), backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#64748b'] }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        // Tema Full Chart
        new Chart(document.getElementById('temaFullChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(katData),
                datasets: [{{ label: 'Total Publikasi', data: Object.values(katData), backgroundColor: '#1d4ed8', borderRadius: 6 }}]
            }},
            options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false }}
        }});

        // Tier Full Chart
        new Chart(document.getElementById('tierFullChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(tierData),
                datasets: [{{ label: 'Jumlah Media', data: Object.values(tierData), backgroundColor: '#059669', borderRadius: 6 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        // Sub-Isu Bar Chart
        const subIsuData = {json.dumps(sub_isu_counts)};
        new Chart(document.getElementById('subIsuChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(subIsuData),
                datasets: [{{
                    label: 'Jumlah Berita',
                    data: Object.values(subIsuData),
                    backgroundColor: ['#e11d48', '#f43f5e', '#fb7185', '#fda4af'],
                    borderRadius: 8,
                    barThickness: 22
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        // Render Table Negatif
        const tbody = document.getElementById('table-negatif-body');
        const listNegatif = rawData.filter(d => d.sentimen === 'Negatif');
        
        tbody.innerHTML = listNegatif.map(item => `
            <tr class="hover:bg-rose-50/30 transition">
                <td class="p-4 text-xs font-medium text-slate-500 whitespace-nowrap">${{item.tanggal || '-'}}</td>
                <td class="p-4 font-semibold text-slate-800">${{item.judul}}</td>
                <td class="p-4">
                    <span class="bg-rose-100 text-rose-800 border border-rose-200 text-xs px-2.5 py-1 rounded-md font-medium inline-block">
                        ${{item.sub_isu || 'Tindak Kriminal & Hukum'}}
                    </span>
                </td>
                <td class="p-4 text-xs font-medium text-slate-600">${{item.nama_media || item.sumber}}</td>
                <td class="p-4 text-center">
                    <span class="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase">Negatif</span>
                </td>
                <td class="p-4 text-right">
                    <a href="${{item.link}}" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline text-xs font-semibold inline-flex items-center gap-1">
                        Buka Isu ↗
                    </a>
                </td>
            </tr>
        `).join('');
    </script>
</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Dashboard HTML berhasil dibuat lengkap dengan semua Tab!")

if __name__ == "__main__":
    generate_dashboard()
