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

    total_publikasi = len(df)
    df_pers = df[df['tier_media'].isin(['Tier 1 (Nasional)', 'Tier 2 (Regional)'])]
    total_media = len(df_pers)
    
    positif_count = len(df[df['sentimen'] == 'Positif'])
    netral_count = len(df[df['sentimen'] == 'Netral'])
    negatif_count = len(df[df['sentimen'] == 'Negatif'])
    
    kat_counts = df['kategori'].value_counts().to_dict()
    tema_terpopuler = list(kat_counts.keys())[0] if kat_counts else "Akademik & Umum"
    tema_count = list(kat_counts.values())[0] if kat_counts else 0

    df_tier1 = df[df['tier_media'] == 'Tier 1 (Nasional)']['nama_media'].value_counts().head(3).to_dict()
    df_tier2 = df[df['tier_media'] == 'Tier 2 (Regional)']['nama_media'].value_counts().head(3).to_dict()
    tier_counts = df['tier_media'].value_counts().to_dict()

    df_negatif = df[df['sentimen'] == 'Negatif'].copy()
    if not df_negatif.empty and 'sub_isu' in df_negatif.columns:
        sub_isu_counts = df_negatif['sub_isu'].value_counts().to_dict()
    else:
        sub_isu_counts = {"Kekerasan Seksual & PPKS": negatif_count}

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
        .tab-panel {{ display: none; }}
        .tab-panel.active {{ display: block; }}
    </style>
</head>
<body class="p-3 md:p-6">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- HEADER UTAMA RESPONSIF (TIDAK TABRAKAN DI HP) -->
        <div class="bg-slate-900 text-white p-5 md:p-6 rounded-2xl shadow-lg space-y-4">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <span class="bg-blue-600 text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider">EXTERNAL</span>
                    <h1 class="text-xl md:text-2xl font-bold mt-2">Monitoring Pemberitaan Eksternal UNESA</h1>
                    <p class="text-slate-400 text-xs mt-0.5">Analisis Media Massa Digital, Sentiment Tracking & Detector Isu (2026)</p>
                </div>
                <span class="bg-emerald-950/80 text-emerald-400 border border-emerald-800/50 text-[11px] px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    {total_publikasi} Berita Loaded
                </span>
            </div>
            
            <!-- Tombol Navigasi Tab (Rapi Berjajar di HP) -->
            <div class="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 bg-slate-800 p-2 rounded-xl text-xs font-semibold text-slate-300">
                <button onclick="openTab('ikhtisar')" id="btn-ikhtisar" class="tab-btn active px-3.5 py-2.5 rounded-lg transition text-center">📊 Ikhtisar</button>
                <button onclick="openTab('tema')" id="btn-tema" class="tab-btn px-3.5 py-2.5 rounded-lg transition text-center">📊 Tren Tema</button>
                <button onclick="openTab('tier')" id="btn-tier" class="tab-btn px-3.5 py-2.5 rounded-lg transition text-center">📊 Tier Media</button>
                <button onclick="openTab('tone')" id="btn-tone" class="tab-btn px-3.5 py-2.5 rounded-lg transition text-center">🚨 Tone & Isu</button>
            </div>
        </div>

        <!-- METRIC CARDS (RESPONSIF 2 KOLOM DI HP, 5 DI DESKTOP) -->
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 md:gap-4">
            <div class="bg-white p-4 md:p-5 rounded-xl border border-slate-200 border-l-4 border-l-blue-500 shadow-sm">
                <p class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-wider">TOTAL PUBLIKASI</p>
                <h3 class="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">{total_publikasi}</h3>
                <span class="text-[11px] md:text-xs text-blue-600 font-medium mt-1 block">Jan - Sep 2026</span>
            </div>
            <div class="bg-white p-4 md:p-5 rounded-xl border border-slate-200 border-l-4 border-l-emerald-500 shadow-sm">
                <p class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-wider">MEDIA PERS</p>
                <h3 class="text-2xl md:text-3xl font-extrabold text-slate-900 mt-1">{total_media}</h3>
                <span class="text-[11px] md:text-xs text-emerald-600 font-medium mt-1 block">{round(total_media/total_publikasi*100, 1) if total_publikasi else 0}% Total</span>
            </div>
            <div class="bg-white p-4 md:p-5 rounded-xl border border-slate-200 border-l-4 border-l-indigo-500 shadow-sm">
                <p class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-wider">TEMA TERPOPULER</p>
                <h3 class="text-sm md:text-lg font-bold text-indigo-600 mt-1 truncate">{tema_terpopuler}</h3>
                <span class="text-[11px] md:text-xs text-slate-500 font-medium mt-1 block">{tema_count} Berita</span>
            </div>
            <div class="bg-white p-4 md:p-5 rounded-xl border border-slate-200 border-l-4 border-l-purple-500 shadow-sm">
                <p class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-wider">SENTIMEN POSITIF</p>
                <h3 class="text-2xl md:text-3xl font-extrabold text-purple-600 mt-1">{positif_count}</h3>
                <span class="text-[11px] md:text-xs text-purple-600 font-medium mt-1 block">{round(positif_count/total_publikasi*100, 1) if total_publikasi else 0}% Positif</span>
            </div>
            <div class="bg-white p-4 md:p-5 rounded-xl border border-slate-200 border-l-4 border-l-rose-500 shadow-sm relative col-span-2 lg:col-span-1">
                <p class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-wider">ISU / TONE NEGATIF</p>
                <h3 class="text-2xl md:text-3xl font-extrabold text-rose-600 mt-1">{negatif_count}</h3>
                <span class="text-[11px] md:text-xs text-rose-600 font-medium mt-1 block">{round(negatif_count/total_publikasi*100, 1) if total_publikasi else 0}% Atensi</span>
                <span class="absolute top-4 right-4 bg-rose-100 text-rose-700 text-[10px] font-bold px-2 py-0.5 rounded">Atensi ↗</span>
            </div>
        </div>

        <!-- TAB 1: IKHTISAR -->
        <div id="tab-ikhtisar" class="tab-panel active space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div class="lg:col-span-7 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <div class="flex justify-between items-center mb-1">
                        <div>
                            <h2 class="text-base font-bold text-slate-800">Volume Pemberitaan per Bulan (2026)</h2>
                            <p class="text-xs text-slate-400">Tren jumlah publikasi berita eksternal</p>
                        </div>
                    </div>
                    <div class="h-60 md:h-64 mt-4"><canvas id="volumeMonthlyChart"></canvas></div>
                </div>

                <div class="lg:col-span-5 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-base font-bold text-slate-800 mb-0.5">Proporsi Tema & Kategori</h2>
                    <p class="text-xs text-slate-400 mb-4">Distribusi topik berdasarkan bidang</p>
                    <div class="h-60 md:h-64 flex justify-center"><canvas id="proporsiTemaChart"></canvas></div>
                </div>
            </div>

            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="p-5 border-b border-slate-100">
                    <h2 class="text-base font-bold text-slate-800">Rekap Pemberitaan Eksternal Terkini</h2>
                    <p class="text-xs text-slate-400">Diurutkan dari yang terbaru & disaring relevansinya</p>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-xs text-slate-600 min-w-[650px]">
                        <thead class="bg-slate-50 text-[11px] uppercase text-slate-400 sticky top-0 border-b border-slate-200">
                            <tr>
                                <th class="p-4 w-28">TANGGAL</th>
                                <th class="p-4 w-40">MEDIA / SUMBER</th>
                                <th class="p-4 w-48">KATEGORI TEMA</th>
                                <th class="p-4">JUDUL BERITA</th>
                                <th class="p-4 w-24 text-center">SENTIMEN</th>
                                <th class="p-4 w-20 text-right">AKSI</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100" id="table-ikhtisar-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: ANALISIS TREN TEMA -->
        <div id="tab-tema" class="tab-panel space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div class="lg:col-span-6 bg-white p-5 md:p-6 rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/50 to-white shadow-sm flex flex-col justify-between">
                    <div>
                        <h2 class="text-base md:text-lg font-bold text-blue-900 mb-1">Peta Tema & Isu Populer Eksternal</h2>
                        <p class="text-xs text-slate-500 mb-4">Urutan tema berita paling banyak diulas</p>
                        <div class="space-y-3">
                            """ + "".join([f"""
                            <div class="flex items-center justify-between p-3 bg-white rounded-xl border border-slate-100 shadow-2xs">
                                <span class="text-xs font-semibold text-slate-700">{i+1}. {k}</span>
                                <span class="bg-blue-100 text-blue-700 text-xs px-2.5 py-0.5 rounded-full font-bold">{v} Berita</span>
                            </div>""" for i, (k, v) in enumerate(list(kat_counts.items())[:6])]) + f"""
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-6 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <h2 class="text-base md:text-lg font-bold text-slate-800 mb-1">Proporsi Tema dan Kategori Publikasi</h2>
                        <p class="text-xs text-slate-400 mb-4">Persentase sebaran topik dari seluruh total berita</p>
                    </div>
                    <div class="h-60 md:h-64 flex justify-center"><canvas id="temaDonutFullChart"></canvas></div>
                </div>
            </div>

            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="p-5 border-b border-slate-100">
                    <h2 class="text-base font-bold text-slate-800">Daftar Berita Berdasarkan Tema</h2>
                    <p class="text-xs text-slate-400">Seluruh publikasi media luar berdasarkan topik berita</p>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-xs text-slate-600 min-w-[650px]">
                        <thead class="bg-slate-50 text-[11px] uppercase text-slate-400 sticky top-0 border-b border-slate-200">
                            <tr>
                                <th class="p-4 w-28">TANGGAL</th>
                                <th class="p-4 w-48">TEMA</th>
                                <th class="p-4 w-44">NAMA MEDIA</th>
                                <th class="p-4">JUDUL BERITA</th>
                                <th class="p-4 w-20 text-right">LINK BERITA</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100" id="table-tema-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: ANALISIS TIER MEDIA -->
        <div id="tab-tier" class="tab-panel space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div class="lg:col-span-6 bg-white p-5 md:p-6 rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white shadow-sm">
                    <h2 class="text-base md:text-lg font-bold text-indigo-900 mb-1">Rincian Top Media Pemberita UNESA</h2>
                    <p class="text-xs text-slate-500 mb-4">Media pers teratas yang aktif mempublikasikan berita</p>
                    
                    <div class="space-y-4">
                        <div class="bg-white p-4 rounded-xl border border-indigo-100 shadow-2xs">
                            <h3 class="text-xs font-bold text-indigo-700 uppercase mb-2">Tier 1 (Nasional)</h3>
                            <div class="space-y-1.5">
                                """ + "".join([f"<div class='flex justify-between text-xs text-slate-600'><span>• {m}</span><span class='font-bold text-slate-800'>{c} berita</span></div>" for m, c in df_tier1.items()]) + f"""
                            </div>
                        </div>
                        <div class="bg-white p-4 rounded-xl border border-emerald-100 shadow-2xs">
                            <h3 class="text-xs font-bold text-emerald-700 uppercase mb-2">Tier 2 (Regional)</h3>
                            <div class="space-y-1.5">
                                """ + "".join([f"<div class='flex justify-between text-xs text-slate-600'><span>• {m}</span><span class='font-bold text-slate-800'>{c} berita</span></div>" for m, c in df_tier2.items()]) + f"""
                            </div>
                        </div>
                    </div>
                </div>

                <div class="lg:col-span-6 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <h2 class="text-base md:text-lg font-bold text-slate-800 mb-1">Proporsi Sebaran Berita Tier Media</h2>
                        <p class="text-xs text-slate-400 mb-4">Persentase level media massa</p>
                    </div>
                    <div class="h-60 md:h-64 flex justify-center"><canvas id="tierDonutFullChart"></canvas></div>
                </div>
            </div>

            <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="p-5 border-b border-slate-100">
                    <h2 class="text-base font-bold text-slate-800">Daftar Seluruh Media yang Memberitakan UNESA</h2>
                    <p class="text-xs text-slate-400">Rekapitulasi lengkap media massa pers</p>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-xs text-slate-600 min-w-[500px]">
                        <thead class="bg-slate-50 text-[11px] uppercase text-slate-400 sticky top-0 border-b border-slate-200">
                            <tr>
                                <th class="p-4 w-16 text-center">NO</th>
                                <th class="p-4">NAMA MEDIA</th>
                                <th class="p-4 w-48">TIER MEDIA</th>
                                <th class="p-4 w-36 text-center">TOTAL PUBLIKASI</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100" id="table-tier-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: ANALISIS TONE PEMBERITAAN -->
        <div id="tab-tone" class="tab-panel space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <div class="lg:col-span-5 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-base md:text-lg font-bold text-slate-800 mb-1">Proporsi Tone Pemberitaan</h2>
                    <p class="text-xs text-slate-500 mb-4">Grafik donat persentase persepsi publik</p>
                    <div class="h-60 md:h-64 flex justify-center"><canvas id="toneChart"></canvas></div>
                </div>

                <div class="lg:col-span-7 bg-white p-5 md:p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <div class="flex justify-between items-center mb-1">
                            <h2 class="text-base md:text-lg font-bold text-slate-800">Distribusi Kategori Sub-Isu Krisis</h2>
                            <span class="bg-rose-100 text-rose-700 text-xs px-3 py-1 rounded-full font-bold">{negatif_count} Total Isu</span>
                        </div>
                        <p class="text-xs text-slate-500 mb-4">Pengelompokan berita negatif berdasarkan topik</p>
                    </div>
                    <div class="h-56"><canvas id="subIsuChart"></canvas></div>
                </div>
            </div>

            <div class="bg-white rounded-2xl border border-rose-200 shadow-sm overflow-hidden">
                <div class="bg-rose-50/50 p-4 md:p-5 border-b border-rose-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                    <div>
                        <h2 class="text-base md:text-lg font-bold text-rose-900 flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse"></span>
                            Daftar Berita Tone Negatif & Isu Atensi Humas
                        </h2>
                        <p class="text-xs text-rose-600">Pemberitaan eksternal yang memerlukan mitigasi</p>
                    </div>
                    <span class="bg-rose-600 text-white text-xs px-3 py-1 rounded-full font-bold">{negatif_count} Isu</span>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-sm text-slate-600 min-w-[650px]">
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

        function openTab(tabId) {{
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById('tab-' + tabId).classList.add('active');
            document.getElementById('btn-' + tabId).classList.add('active');
        }}

        const monthMap = {{
            'jan': 0, 'january': 0, 'januari': 0,
            'feb': 1, 'february': 1, 'februari': 1,
            'mar': 2, 'march': 2, 'maret': 2,
            'apr': 3, 'april': 3,
            'may': 4, 'mei': 4,
            'jun': 5, 'june': 5, 'juni': 5,
            'jul': 6, 'july': 6, 'juli': 6,
            'aug': 7, 'august': 7, 'agustus': 7, 'agu': 7,
            'sep': 8, 'september': 8
        }};

        const monthlyCounts = [0, 0, 0, 0, 0, 0, 0, 0, 0];

        rawData.forEach(item => {{
            if (item.tanggal) {{
                const strTgl = String(item.tanggal).toLowerCase();
                let foundIndex = -1;

                for (const [key, idx] of Object.entries(monthMap)) {{
                    if (strTgl.includes(key)) {{
                        foundIndex = idx;
                        break;
                    }}
                }}

                if (foundIndex === -1 && strTgl.includes('-')) {{
                    const parts = strTgl.split('-');
                    if (parts.length >= 2) {{
                        const mVal = parseInt(parts[1], 10);
                        if (mVal >= 1 && mVal <= 9) foundIndex = mVal - 1;
                    }}
                }}

                if (foundIndex >= 0 && foundIndex <= 8) {{
                    monthlyCounts[foundIndex] += 1;
                }}
            }}
        }});

        new Chart(document.getElementById('volumeMonthlyChart'), {{
            type: 'bar',
            data: {{
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep'],
                datasets: [{{
                    label: 'Jumlah Berita',
                    data: monthlyCounts,
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#a855f7', '#14b8a6'],
                    borderRadius: 6
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
        }});

        const katData = {json.dumps(kat_counts)};
        new Chart(document.getElementById('proporsiTemaChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(katData),
                datasets: [{{
                    data: Object.values(katData),
                    backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b', '#f43f5e']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 9 }} }} }} }} }}
        }});

        new Chart(document.getElementById('temaDonutFullChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(katData),
                datasets: [{{ data: Object.values(katData), backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#64748b', '#f43f5e'] }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 9 }} }} }} }} }}
        }});

        const tierData = {json.dumps(tier_counts)};
        new Chart(document.getElementById('tierDonutFullChart'), {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(tierData),
                datasets: [{{ data: Object.values(tierData), backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#64748b'] }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 9 }} }} }} }} }}
        }});

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

        document.getElementById('table-ikhtisar-body').innerHTML = rawData.slice(0, 15).map(item => `
            <tr class="hover:bg-slate-50 transition">
                <td class="p-4 text-slate-400 font-medium whitespace-nowrap">${{item.tanggal || '-'}}</td>
                <td class="p-4 font-medium text-slate-700">${{item.nama_media || item.sumber}}</td>
                <td class="p-4">
                    <span class="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded font-medium text-[11px] whitespace-nowrap">
                        ${{item.kategori || 'Akademik & Umum'}}
                    </span>
                </td>
                <td class="p-4 font-semibold text-slate-800 min-w-[250px]">${{item.judul}}</td>
                <td class="p-4 text-center">
                    <span class="${{item.sentimen === 'Positif' ? 'bg-emerald-100 text-emerald-700' : (item.sentimen === 'Negatif' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-600')}} text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap">
                        ${{item.sentimen}}
                    </span>
                </td>
                <td class="p-4 text-right"><a href="${{item.link}}" target="_blank" class="text-blue-600 hover:underline font-semibold whitespace-nowrap">Buka ↗</a></td>
            </tr>
        `).join('');

        document.getElementById('table-tema-body').innerHTML = rawData.slice(0, 25).map(item => `
            <tr class="hover:bg-slate-50 transition">
                <td class="p-4 text-slate-400 font-medium whitespace-nowrap">${{item.tanggal || '-'}}</td>
                <td class="p-4"><span class="bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded font-medium text-[11px] whitespace-nowrap">${{item.kategori || 'Akademik & Umum'}}</span></td>
                <td class="p-4 font-medium text-slate-700">${{item.nama_media || item.sumber}}</td>
                <td class="p-4 font-semibold text-slate-800 min-w-[250px]">${{item.judul}}</td>
                <td class="p-4 text-right"><a href="${{item.link}}" target="_blank" class="text-blue-600 hover:underline font-semibold whitespace-nowrap">Buka ↗</a></td>
            </tr>
        `).join('');

        const mediaGrouped = {{}};
        rawData.forEach(d => {{
            const m = d.nama_media || d.sumber;
            if (m) {{
                if (!mediaGrouped[m]) mediaGrouped[m] = {{ name: m, tier: d.tier_media || 'Tier 2 (Regional)', count: 0 }};
                mediaGrouped[m].count += 1;
            }}
        }});
        const sortedMedia = Object.values(mediaGrouped).sort((a,b) => b.count - a.count);

        document.getElementById('table-tier-body').innerHTML = sortedMedia.map((item, idx) => `
            <tr class="hover:bg-slate-50 transition">
                <td class="p-4 text-center font-bold text-slate-400">${{idx + 1}}</td>
                <td class="p-4 font-bold text-slate-800">${{item.name}}</td>
                <td class="p-4"><span class="bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded font-medium text-[11px] whitespace-nowrap">${{item.tier}}</span></td>
                <td class="p-4 text-center font-extrabold text-blue-600">${{item.count}} Berita</td>
            </tr>
        `).join('');

        const listNegatif = rawData.filter(d => d.sentimen === 'Negatif');
        document.getElementById('table-negatif-body').innerHTML = listNegatif.map(item => `
            <tr class="hover:bg-rose-50/30 transition">
                <td class="p-4 text-xs font-medium text-slate-500 whitespace-nowrap">${{item.tanggal || '-'}}</td>
                <td class="p-4 font-semibold text-slate-800 min-w-[250px]">${{item.judul}}</td>
                <td class="p-4">
                    <span class="bg-rose-100 text-rose-800 border border-rose-200 text-xs px-2.5 py-1 rounded-md font-medium inline-block whitespace-nowrap">
                        ${{item.sub_isu || 'Kekerasan Seksual & PPKS'}}
                    </span>
                </td>
                <td class="p-4 text-xs font-medium text-slate-600">${{item.nama_media || item.sumber}}</td>
                <td class="p-4 text-center"><span class="bg-rose-500 text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase whitespace-nowrap">Negatif</span></td>
                <td class="p-4 text-right"><a href="${{item.link}}" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline text-xs font-semibold inline-flex items-center gap-1 whitespace-nowrap">Buka Isu ↗</a></td>
            </tr>
        `).join('');
    </script>
</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Dashboard HTML responsif HP berhasil diperbarui!")

if __name__ == "__main__":
    generate_dashboard()
