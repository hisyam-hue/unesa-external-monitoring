import pandas as pd
import json
import shutil

CSV_FILE = "rekap_berita_eksternal.csv"
HTML_OUTPUT = "dashboard_eksternal.html"

def build_dashboard():
    print("=== MENGUPDATE DASHBOARD DENGAN TAB INTERAKTIF SESUAI PPT UNESA ===")
    
    try:
        df = pd.read_csv(CSV_FILE)
        df = df.fillna('')
        data_json = json.dumps(df.to_dict(orient='records'), ensure_ascii=False)
        print(f"[+] Berhasil memuat {len(df)} data dari '{CSV_FILE}'.")
    except Exception as e:
        print(f"[ERROR] Gagal membaca CSV: {e}")
        return

    html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Monitoring Berita Eksternal UNESA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; }}
        .tab-btn-active {{ background-color: #2563eb; color: #ffffff; font-weight: 700; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .tab-btn-inactive {{ color: #94a3b8; }}
        .tab-btn-inactive:hover {{ color: #ffffff; background-color: rgba(255, 255, 255, 0.1); }}
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header Navigasi Tab Utama (Sesuai PPT UNESA) -->
        <header class="bg-slate-900 text-white rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-4">
                <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-extrabold px-4 py-2 rounded-xl text-xl tracking-wider shadow-lg">
                    EXTERNAL
                </div>
                <div>
                    <h1 class="text-xl font-bold">Monitoring Pemberitaan Eksternal UNESA</h1>
                    <p class="text-xs text-slate-400">Analisis Media Massa Digital, Sentiment Tracking & Detector Isu (2026)</p>
                </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
                <div class="bg-slate-800 p-1.5 rounded-xl flex items-center gap-1 border border-slate-700">
                    <button id="tab-btn-ikhtisar" onclick="switchTab('ikhtisar')" class="tab-btn-active text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5">
                        ⚙ Ikhtisar
                    </button>
                    <button id="tab-btn-tema" onclick="switchTab('tema')" class="tab-btn-inactive text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5">
                        📊 Analisis Tren Tema
                    </button>
                    <button id="tab-btn-tier" onclick="switchTab('tier')" class="tab-btn-inactive text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5">
                        📰 Analisis Tier Media
                    </button>
                    <button id="tab-btn-tone" onclick="switchTab('tone')" class="tab-btn-inactive text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5">
                        🚨 Analisis Tone Pemberitaan
                    </button>
                </div>

                <span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-3.5 py-2 rounded-xl font-semibold flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span id="data-status">Berita Loaded</span>
                </span>
            </div>
        </header>

        <!-- KPI Cards Summary -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-blue-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">TOTAL PUBLIKASI</p>
                <h3 id="stat-total" class="text-3xl font-extrabold text-slate-800 mt-2">-</h3>
                <p class="text-xs text-blue-600 font-semibold mt-1">Januari - September 2026</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-emerald-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">PUBLIKASI MEDIA PERS</p>
                <h3 id="stat-pers" class="text-3xl font-extrabold text-slate-800 mt-2">-</h3>
                <p id="stat-pers-pct" class="text-xs text-emerald-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-indigo-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">TEMA TERPOPULER</p>
                <h3 id="stat-top-theme" class="text-lg font-extrabold text-indigo-700 mt-2 truncate">-</h3>
                <p id="stat-top-theme-cnt" class="text-xs text-indigo-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-purple-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">SENTIMEN POSITIF</p>
                <h3 id="stat-positive" class="text-3xl font-extrabold text-purple-600 mt-2">-</h3>
                <p id="stat-positive-pct" class="text-xs text-purple-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-rose-500 cursor-pointer hover:bg-rose-50/30 transition" onclick="switchTab('tone')">
                <div class="flex justify-between items-start">
                    <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">ISU / TONE NEGATIF</p>
                    <span class="text-[10px] bg-rose-100 text-rose-700 font-extrabold px-1.5 py-0.5 rounded">Atensi ↗</span>
                </div>
                <h3 id="stat-negative" class="text-3xl font-extrabold text-rose-600 mt-2">-</h3>
                <p id="stat-negative-pct" class="text-xs text-rose-600 font-semibold mt-1">-</p>
            </div>
        </div>

        <!-- TAB 1: IKHTISAR -->
        <div id="tab-content-ikhtisar" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <div class="flex justify-between items-center mb-4">
                        <div>
                            <h3 class="font-bold text-slate-800 text-base">Volume Pemberitaan per Bulan (2026)</h3>
                            <p class="text-xs text-slate-400">Tren jumlah publikasi berita eksternal dari Januari s.d September 2026</p>
                        </div>
                        <span class="text-[11px] bg-slate-100 text-slate-500 px-2.5 py-1 rounded-lg font-semibold">Tren Bulanan</span>
                    </div>
                    <div class="h-72 relative">
                        <canvas id="barChartIkhtisar"></canvas>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Proporsi Tema & Kategori</h3>
                        <p class="text-xs text-slate-400 mb-4">Distribusikan topik berita berdasarkan bidang</p>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="donutChartIkhtisar"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabel Sample Berita Terkini -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-slate-800 text-base">Rekap Pemberitaan Eksternal Terkini</h3>
                    <p class="text-xs text-slate-400">Diurutkan dari yang terbaru & disaring relevansinya</p>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-400 text-xs uppercase">
                            <tr>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Media / Sumber</th>
                                <th class="p-3">Kategori Tema</th>
                                <th class="p-3">Judul Berita</th>
                                <th class="p-3">Sentimen</th>
                                <th class="p-3 text-right">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="table-ikhtisar-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 2: ANALISIS TREN TEMA -->
        <div id="tab-content-tema" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <div class="mb-4">
                        <h3 class="font-bold text-slate-800 text-base">Analisis Tren Tema Pemberitaan Eksternal UNESA</h3>
                        <p class="text-xs text-slate-400">Peringkat sebaran tema dan isu populer yang banyak diulas media eksternal</p>
                    </div>
                    <div class="h-80 relative">
                        <canvas id="barChartTema"></canvas>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Proporsi Tema & Kategori</h3>
                        <p class="text-xs text-slate-400 mb-4">Persentase kontribusi masing-masing rumpun topik</p>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="donutChartTema"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabel Daftar Berita per Tema -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Daftar Berita Berdasarkan Tema Popular</h3>
                        <p class="text-xs text-slate-400">Rincian artikel pemberitaan yang dikelompokkan sesuai rumpun tema</p>
                    </div>
                    <select id="filter-tema-select" onchange="filterTableTema()" class="px-3 py-2 border border-slate-200 rounded-xl text-xs bg-indigo-50 text-indigo-700 font-bold focus:outline-none">
                        <option value="">Semua Tema & Kategori</option>
                    </select>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-400 text-xs uppercase sticky top-0">
                            <tr>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Judul Berita</th>
                                <th class="p-3">Kategori Tema</th>
                                <th class="p-3">Nama Media</th>
                                <th class="p-3 text-right">Link Berita</th>
                            </tr>
                        </thead>
                        <tbody id="table-tema-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: ANALISIS TIER MEDIA -->
        <div id="tab-content-tier" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm space-y-6">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Analisis Tier Media Eksternal UNESA</h3>
                        <p class="text-xs text-slate-400">Klasifikasi media nasional (Tier 1) dan media regional/daerah (Tier 2)</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="p-4 bg-blue-50/60 rounded-2xl border border-blue-100 space-y-3">
                            <div class="flex justify-between items-center border-b border-blue-200/60 pb-2">
                                <span class="text-xs font-extrabold text-blue-900 uppercase">Tier 1: Media Nasional</span>
                                <span id="cnt-tier1" class="bg-blue-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">0</span>
                            </div>
                            <ul id="list-tier1" class="text-xs space-y-2 text-slate-700 font-medium"></ul>
                        </div>

                        <div class="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-100 space-y-3">
                            <div class="flex justify-between items-center border-b border-emerald-200/60 pb-2">
                                <span class="text-xs font-extrabold text-emerald-900 uppercase">Tier 2: Media Regional</span>
                                <span id="cnt-tier2" class="bg-emerald-600 text-white text-xs font-bold px-2.5 py-0.5 rounded-full">0</span>
                            </div>
                            <ul id="list-tier2" class="text-xs space-y-2 text-slate-700 font-medium"></ul>
                        </div>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Proporsi Sebaran Media</h3>
                        <p class="text-xs text-slate-400 mb-4">Perbandingan liputan Tier 1 vs Tier 2 vs Kampus</p>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="donutChartTier"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabel Seluruh Media -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <h3 class="font-bold text-slate-800 text-base mb-4">Daftar Seluruh Media yang Memberitakan UNESA</h3>
                <div class="overflow-x-auto max-h-[400px]">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-400 text-xs uppercase sticky top-0">
                            <tr>
                                <th class="p-3">Nama Media</th>
                                <th class="p-3">Kategori Tier</th>
                                <th class="p-3">Jumlah Berita</th>
                                <th class="p-3">Topik Utama Diliput</th>
                            </tr>
                        </thead>
                        <tbody id="table-media-list-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: ANALISIS TONE PEMBERITAAN -->
        <div id="tab-content-tone" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base mb-1">Analisis Tone Pemberitaan UNESA</h3>
                        <p class="text-xs text-slate-400 mb-6">Distribusi tone sentimen opini publik dan framing media massa</p>
                        
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div class="p-4 bg-emerald-50 rounded-2xl border border-emerald-200">
                                <p class="text-xs font-bold text-emerald-800 uppercase">Tone Positif</p>
                                <h4 id="tone-pos-cnt" class="text-2xl font-extrabold text-emerald-700 mt-1">0</h4>
                                <p id="tone-pos-pct" class="text-xs text-emerald-600 font-semibold mt-1">0%</p>
                            </div>
                            <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200">
                                <p class="text-xs font-bold text-slate-700 uppercase">Tone Netral</p>
                                <h4 id="tone-net-cnt" class="text-2xl font-extrabold text-slate-700 mt-1">0</h4>
                                <p id="tone-net-pct" class="text-xs text-slate-500 font-semibold mt-1">0%</p>
                            </div>
                            <div class="p-4 bg-rose-50 rounded-2xl border border-rose-200">
                                <p class="text-xs font-bold text-rose-800 uppercase">Tone Negatif / Isu</p>
                                <h4 id="tone-neg-cnt" class="text-2xl font-extrabold text-rose-700 mt-1">0</h4>
                                <p id="tone-neg-pct" class="text-xs text-rose-600 font-semibold mt-1">0%</p>
                            </div>
                        </div>
                    </div>
                    <p class="text-xs text-slate-400 mt-4 leading-relaxed">
                        *Catatan Humas: Tone negatif mencakup pemberitaan aduan krisis, isu hukum, atau investigasi. Sistem dilengkapi deteksi otomatis penanganan krisis responsif.
                    </p>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Proporsi Tone Pemberitaan</h3>
                        <p class="text-xs text-slate-400 mb-4">Grafik donat persentase persepsi publik</p>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="donutChartTone"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabel Khusus Berita Tone Negatif / Isu -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm border-t-4 border-t-rose-500">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h3 class="font-bold text-rose-700 text-base flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                            Daftar Berita Tone Negatif & Isu Atensi Humas
                        </h3>
                        <p class="text-xs text-slate-400">Pemberitaan eksternal yang memerlukan mitigasi atau klarifikasi isu</p>
                    </div>
                    <span id="badge-neg-count" class="bg-rose-100 text-rose-700 font-extrabold text-xs px-3 py-1 rounded-full">0 Isu</span>
                </div>
                <div class="overflow-x-auto max-h-[450px]">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-rose-50 text-rose-800 text-xs uppercase sticky top-0">
                            <tr>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Judul Berita</th>
                                <th class="p-3">Nama Media</th>
                                <th class="p-3">Tone</th>
                                <th class="p-3 text-right">Link Berita</th>
                            </tr>
                        </thead>
                        <tbody id="table-tone-negative-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>

    <script>
        const rawData = {data_json};

        let barIkhtisarInst, donutIkhtisarInst, barTemaInst, donutTemaInst, donutTierInst, donutToneInst;

        function switchTab(tabName) {{
            ['ikhtisar', 'tema', 'tier', 'tone'].forEach(t => {{
                document.getElementById(`tab-content-${{t}}`).classList.add('hidden');
                document.getElementById(`tab-btn-${{t}}`).className = 'tab-btn-inactive text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5';
            }});

            document.getElementById(`tab-content-${{tabName}}`).classList.remove('hidden');
            document.getElementById(`tab-btn-${{tabName}}`).className = 'tab-btn-active text-xs px-3.5 py-2 rounded-lg transition flex items-center gap-1.5';
        }}

        function initDashboard() {{
            document.getElementById('data-status').innerText = rawData.length + ' Berita Loaded';
            document.getElementById('stat-total').innerText = rawData.length;

            let persCnt = 0, posCnt = 0, negCnt = 0, netCnt = 0;
            const monthlyCounts = {{ 'Jan':0, 'Feb':0, 'Mar':0, 'Apr':0, 'Mei':0, 'Jun':0, 'Jul':0, 'Agu':0, 'Sep':0 }};
            const categoryCounts = {{}};
            const mediaTierMap = {{ tier1: {{}}, tier2: {{}}, other: {{}} }};

            rawData.forEach(row => {{
                const snt = (row.sentimen || 'Netral').toLowerCase();
                if (snt === 'positif') posCnt++;
                else if (snt === 'negatif') negCnt++;
                else netCnt++;

                const kat = row.kategori || 'Akademik & Umum';
                categoryCounts[kat] = (categoryCounts[kat] || 0) + 1;

                const med = row.nama_media || 'Media Online';
                const tier = row.tier_media || 'Tier 3 (Lokal)';
                if (tier.includes('Tier 1')) {{
                    persCnt++;
                    mediaTierMap.tier1[med] = (mediaTierMap.tier1[med] || 0) + 1;
                }} else if (tier.includes('Tier 2')) {{
                    persCnt++;
                    mediaTierMap.tier2[med] = (mediaTierMap.tier2[med] || 0) + 1;
                }} else {{
                    mediaTierMap.other[med] = (mediaTierMap.other[med] || 0) + 1;
                }}

                const tgl = (row.tanggal || '').toString();
                if (tgl.includes('Jan')) monthlyCounts['Jan']++;
                else if (tgl.includes('Feb')) monthlyCounts['Feb']++;
                else if (tgl.includes('Mar')) monthlyCounts['Mar']++;
                else if (tgl.includes('Apr')) monthlyCounts['Apr']++;
                else if (tgl.includes('May') || tgl.includes('Mei')) monthlyCounts['Mei']++;
                else if (tgl.includes('Jun')) monthlyCounts['Jun']++;
                else if (tgl.includes('Jul')) monthlyCounts['Jul']++;
                else if (tgl.includes('Aug') || tgl.includes('Agu')) monthlyCounts['Agu']++;
                else if (tgl.includes('Sep')) monthlyCounts['Sep']++;
            }});

            const total = rawData.length || 1;
            document.getElementById('stat-pers').innerText = persCnt;
            document.getElementById('stat-pers-pct').innerText = ((persCnt/total)*100).toFixed(1) + '% dari Total';

            document.getElementById('stat-positive').innerText = posCnt;
            document.getElementById('stat-positive-pct').innerText = ((posCnt/total)*100).toFixed(1) + '% Tone Positif';

            document.getElementById('stat-negative').innerText = negCnt;
            document.getElementById('stat-negative-pct').innerText = ((negCnt/total)*100).toFixed(1) + '% Perlu Atensi';

            let topKat = '-', maxKat = 0;
            Object.entries(categoryCounts).forEach(([k,v]) => {{
                if (v > maxKat) {{ maxKat = v; topKat = k; }}
            }});
            document.getElementById('stat-top-theme').innerText = topKat;
            document.getElementById('stat-top-theme-cnt').innerText = maxKat + ' Berita';

            document.getElementById('tone-pos-cnt').innerText = posCnt;
            document.getElementById('tone-pos-pct').innerText = ((posCnt/total)*100).toFixed(1) + '%';
            document.getElementById('tone-net-cnt').innerText = netCnt;
            document.getElementById('tone-net-pct').innerText = ((netCnt/total)*100).toFixed(1) + '%';
            document.getElementById('tone-neg-cnt').innerText = negCnt;
            document.getElementById('tone-neg-pct').innerText = ((negCnt/total)*100).toFixed(1) + '%';
            document.getElementById('badge-neg-count').innerText = negCnt + ' Isu';

            renderCharts(monthlyCounts, categoryCounts, posCnt, netCnt, negCnt, mediaTierMap);
            renderTables(categoryCounts, mediaTierMap);
        }}

        function renderCharts(monthly, categories, pos, net, neg, mediaMap) {{
            const ctxBar1 = document.getElementById('barChartIkhtisar').getContext('2d');
            barIkhtisarInst = new Chart(ctxBar1, {{
                type: 'bar',
                data: {{
                    labels: Object.keys(monthly),
                    datasets: [{{
                        data: Object.values(monthly),
                        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#6366f1', '#14b8a6'],
                        borderRadius: 6
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
            }});

            const ctxDonut1 = document.getElementById('donutChartIkhtisar').getContext('2d');
            donutIkhtisarInst = new Chart(ctxDonut1, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(categories),
                    datasets: [{{
                        data: Object.values(categories),
                        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            const ctxBar2 = document.getElementById('barChartTema').getContext('2d');
            const sortedCat = Object.entries(categories).sort((a,b) => b[1] - a[1]);
            barTemaInst = new Chart(ctxBar2, {{
                type: 'bar',
                data: {{
                    labels: sortedCat.map(x => x[0]),
                    datasets: [{{
                        label: 'Jumlah Berita',
                        data: sortedCat.map(x => x[1]),
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }}]
                }},
                options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }} }}
            }});

            const ctxDonut2 = document.getElementById('donutChartTema').getContext('2d');
            donutTemaInst = new Chart(ctxDonut2, {{
                type: 'doughnut',
                data: {{
                    labels: sortedCat.map(x => x[0]),
                    datasets: [{{
                        data: sortedCat.map(x => x[1]),
                        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            const t1Sum = Object.values(mediaMap.tier1).reduce((a,b)=>a+b,0);
            const t2Sum = Object.values(mediaMap.tier2).reduce((a,b)=>a+b,0);
            const othSum = Object.values(mediaMap.other).reduce((a,b)=>a+b,0);

            const ctxDonut3 = document.getElementById('donutChartTier').getContext('2d');
            donutTierInst = new Chart(ctxDonut3, {{
                type: 'doughnut',
                data: {{
                    labels: ['Tier 1 Nasional', 'Tier 2 Regional', 'Portal Kampus/Lain'],
                    datasets: [{{
                        data: [t1Sum, t2Sum, othSum],
                        backgroundColor: ['#2563eb', '#10b981', '#cbd5e1']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            const ctxDonut4 = document.getElementById('donutChartTone').getContext('2d');
            donutToneInst = new Chart(ctxDonut4, {{
                type: 'doughnut',
                data: {{
                    labels: ['Positif', 'Netral', 'Negatif'],
                    datasets: [{{
                        data: [pos, net, neg],
                        backgroundColor: ['#10b981', '#cbd5e1', '#f43f5e']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});
        }}

        function renderTables(categories, mediaMap) {{
            const select = document.getElementById('filter-tema-select');
            select.innerHTML = '<option value="">Semua Tema & Kategori</option>';
            Object.keys(categories).sort().forEach(k => {{
                select.innerHTML += `<option value="${{k}}">${{k}} (${{categories[k]}})</option>`;
            }});

            const ikhtisarBody = document.getElementById('table-ikhtisar-body');
            ikhtisarBody.innerHTML = '';
            rawData.slice(0, 10).forEach(row => {{
                ikhtisarBody.innerHTML += `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="p-3 text-xs text-slate-400 font-medium">${{row.tanggal || '-'}}</td>
                        <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                        <td class="p-3"><span class="bg-blue-50 text-blue-700 px-2.5 py-1 rounded-md text-xs font-semibold">${{row.kategori || 'Akademik'}}</span></td>
                        <td class="p-3 font-medium text-slate-800">${{row.judul || '-'}}</td>
                        <td class="p-3">${{getBadgeTone(row.sentimen)}}</td>
                        <td class="p-3 text-right"><a href="${{row.link}}" target="_blank" class="text-blue-600 font-bold text-xs hover:underline">Buka ↗</a></td>
                    </tr>
                `;
            }});

            renderTableTema(rawData);

            const ul1 = document.getElementById('list-tier1');
            const ul2 = document.getElementById('list-tier2');
            ul1.innerHTML = ''; ul2.innerHTML = '';

            const t1Sorted = Object.entries(mediaMap.tier1).sort((a,b)=>b[1]-a[1]);
            const t2Sorted = Object.entries(mediaMap.tier2).sort((a,b)=>b[1]-a[1]);

            document.getElementById('cnt-tier1').innerText = t1Sorted.reduce((a,b)=>a+b[1],0) + ' Berita';
            document.getElementById('cnt-tier2').innerText = t2Sorted.reduce((a,b)=>a+b[1],0) + ' Berita';

            t1Sorted.slice(0, 6).forEach(([med, cnt]) => {{
                ul1.innerHTML += `<li class="flex justify-between"><span>▫️ ${med}</span><span class="font-bold text-blue-700">${cnt} berita</span></li>`;
            }});
            t2Sorted.slice(0, 6).forEach(([med, cnt]) => {{
                ul2.innerHTML += `<li class="flex justify-between"><span>▫️ ${med}</span><span class="font-bold text-emerald-700">${cnt} berita</span></li>`;
            }});

            const mediaBody = document.getElementById('table-media-list-body');
            mediaBody.innerHTML = '';
            const allMediaCombined = [];
            Object.entries(mediaMap.tier1).forEach(([m,c]) => allMediaCombined.push({{ media:m, count:c, tier:'Tier 1 (Nasional)' }}));
            Object.entries(mediaMap.tier2).forEach(([m,c]) => allMediaCombined.push({{ media:m, count:c, tier:'Tier 2 (Regional)' }}));
            Object.entries(mediaMap.other).forEach(([m,c]) => allMediaCombined.push({{ media:m, count:c, tier:'Portal Kampus/Lain' }}));

            allMediaCombined.sort((a,b)=>b.count - a.count).forEach(item => {{
                mediaBody.innerHTML += `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="p-3 font-bold text-slate-800 text-xs">${{item.media}}</td>
                        <td class="p-3 text-xs"><span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-semibold text-[11px]">${{item.tier}}</span></td>
                        <td class="p-3 font-semibold text-blue-600 text-xs">${{item.count}} Berita</td>
                        <td class="p-3 text-xs text-slate-500">Liputan Umum & Akademik UNESA</td>
                    </tr>
                `;
            }});

            const negBody = document.getElementById('table-tone-negative-body');
            negBody.innerHTML = '';
            const negData = rawData.filter(r => (r.sentimen || '').toLowerCase() === 'negatif');

            if (negData.length === 0) {{
                negBody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-400">Tidak ada pemberitaan ber-tone negatif/isu pada periode ini. 🎉</td></tr>';
            }} else {{
                negData.forEach(row => {{
                    negBody.innerHTML += `
                        <tr class="border-b border-slate-100 hover:bg-rose-50/50">
                            <td class="p-3 text-xs text-slate-500 font-medium">${{row.tanggal || '-'}}</td>
                            <td class="p-3 font-semibold text-slate-900">${{row.judul || '-'}}</td>
                            <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                            <td class="p-3"><span class="bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-[10px] font-bold">Negatif</span></td>
                            <td class="p-3 text-right"><a href="${{row.link}}" target="_blank" class="text-rose-600 font-bold text-xs hover:underline">Buka Isu ↗</a></td>
                        </tr>
                    `;
                }});
            }}
        }}

        function getBadgeTone(snt) {{
            const val = (snt || 'Netral').toLowerCase();
            if (val === 'positif') return '<span class="bg-emerald-100 text-emerald-700 px-2.5 py-0.5 rounded-full text-xs font-bold">Positif</span>';
            if (val === 'negatif') return '<span class="bg-rose-100 text-rose-700 px-2.5 py-0.5 rounded-full text-xs font-bold">Negatif</span>';
            return '<span class="bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded-full text-xs font-bold">Netral</span>';
        }}

        function renderTableTema(data) {{
            const temaBody = document.getElementById('table-tema-body');
            temaBody.innerHTML = '';
            data.forEach(row => {{
                temaBody.innerHTML += `
                    <tr class="border-b border-slate-100 hover:bg-slate-50">
                        <td class="p-3 text-xs text-slate-400 font-medium">${{row.tanggal || '-'}}</td>
                        <td class="p-3 font-medium text-slate-800">${{row.judul || '-'}}</td>
                        <td class="p-3"><span class="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md text-xs font-semibold">${{row.kategori || 'Akademik'}}</span></td>
                        <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                        <td class="p-3 text-right"><a href="${{row.link}}" target="_blank" class="text-blue-600 font-bold text-xs hover:underline">Buka ↗</a></td>
                    </tr>
                `;
            }});
        }}

        function filterTableTema() {{
            const selected = document.getElementById('filter-tema-select').value;
            if (!selected) {{
                renderTableTema(rawData);
            }} else {{
                const filtered = rawData.filter(r => (r.kategori || '') === selected);
                renderTableTema(filtered);
            }}
        }}

        window.onload = initDashboard;
    </script>
</body>
</html>
"""

    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    shutil.copy(HTML_OUTPUT, 'index.html')
    print(f"[SUKSES] File '{HTML_OUTPUT}' & 'index.html' diperbarui dengan 4 Tab Interaktif PPT!")

if __name__ == "__main__":
    build_dashboard()
