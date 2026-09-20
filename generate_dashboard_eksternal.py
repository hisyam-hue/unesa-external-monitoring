import pandas as pd
import json

CSV_FILE = "rekap_berita_eksternal.csv"
HTML_OUTPUT = "index.html"

def build_dashboard():
    print("=== MENGUPDATE DASHBOARD DENGAN ANALISIS TEMA/KATEGORI BERITA ===")
    
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
        .tab-btn-active {{ background-color: #3b82f6; color: #ffffff; font-weight: 700; }}
        .tab-btn-inactive {{ color: #94a3b8; }}
        .tab-btn-inactive:hover {{ color: #ffffff; background-color: rgba(255, 255, 255, 0.1); }}
    </style>
</head>
<body class="p-4 md:p-8">
    <div class="max-w-7xl mx-auto space-y-6">
        
        <!-- Header Navigasi -->
        <header class="bg-slate-900 text-white rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-4">
                <div class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-extrabold px-4 py-2 rounded-xl text-xl tracking-wider shadow-lg">
                    EXTERNAL
                </div>
                <div>
                    <h1 class="text-xl font-bold">Monitoring Pemberitaan Eksternal UNESA</h1>
                    <p class="text-xs text-slate-400">Analisis Tema Berita, Media Massa Digital & Portal Kampus Mitra (2026)</p>
                </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
                <div class="bg-slate-800 p-1 rounded-xl flex items-center gap-1 border border-slate-700">
                    <button id="tab-btn-ikhtisar" onclick="switchTab('ikhtisar')" class="tab-btn-active text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5">
                        Ikhtisar
                    </button>
                    <button id="tab-btn-kategori" onclick="switchTab('kategori')" class="tab-btn-inactive text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5">
                        Analisis Tema & Kategori
                    </button>
                    <button id="tab-btn-rekap" onclick="switchTab('rekap')" class="tab-btn-inactive text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5">
                        Rekap Data
                    </button>
                    <button id="tab-btn-tier" onclick="switchTab('tier')" class="tab-btn-inactive text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5">
                        Tier & Sentimen
                    </button>
                </div>

                <span class="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-3 py-1.5 rounded-full font-semibold flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span id="data-status">Data Aktif</span>
                </span>
            </div>
        </header>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-blue-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Publikasi</p>
                <h3 id="stat-total" class="text-3xl font-extrabold text-slate-800 mt-2">-</h3>
                <p class="text-xs text-blue-600 font-semibold mt-1">Januari - September 2026</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-emerald-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Publikasi Media Pers</p>
                <h3 id="stat-pers" class="text-3xl font-extrabold text-slate-800 mt-2">-</h3>
                <p id="stat-pers-pct" class="text-xs text-emerald-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-indigo-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Tema Terpopuler</p>
                <h3 id="stat-top-theme" class="text-lg font-extrabold text-indigo-700 mt-2 truncate">-</h3>
                <p id="stat-top-theme-cnt" class="text-xs text-indigo-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-purple-500">
                <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Sentimen Positif</p>
                <h3 id="stat-positive" class="text-3xl font-extrabold text-purple-600 mt-2">-</h3>
                <p id="stat-positive-pct" class="text-xs text-purple-600 font-semibold mt-1">-</p>
            </div>
            <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm border-l-4 border-l-rose-500 cursor-pointer hover:bg-rose-50/30 transition" onclick="quickFilterSentimen('Negatif')">
                <div class="flex justify-between items-start">
                    <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Isu / Tone Negatif</p>
                    <span class="text-[10px] bg-rose-100 text-rose-700 font-extrabold px-1.5 py-0.5 rounded">Cek ↗</span>
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
                            <p class="text-xs text-slate-400">Jumlah publikasi berita eksternal dari Januari s.d September 2026</p>
                        </div>
                        <span class="text-[11px] bg-slate-100 text-slate-500 px-2.5 py-1 rounded-lg font-semibold">Bulanan</span>
                    </div>
                    <div class="h-72 relative">
                        <canvas id="barChart"></canvas>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Komposisi Sumber Data</h3>
                        <p class="text-xs text-slate-400 mb-4">Perbandingan Media Pers vs Kampus Lain</p>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="tierChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Preview Berita Terkini -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold text-slate-800 text-base">Sample Pemberitaan Eksternal Terkini</h3>
                    <button onclick="switchTab('rekap')" class="text-blue-600 hover:text-blue-800 text-xs font-bold">Lihat Semua Data ↗</button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-400 text-xs uppercase">
                            <tr>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Media / Website</th>
                                <th class="p-3">Kategori Tema</th>
                                <th class="p-3">Judul Berita</th>
                                <th class="p-3">Sentimen</th>
                                <th class="p-3">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="news-preview-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB BARU: ANALISIS TEMA & KATEGORI -->
        <div id="tab-content-kategori" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Chart Peringkat Tema Berita Laris -->
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <div class="flex justify-between items-center mb-4">
                        <div>
                            <h3 class="font-bold text-slate-800 text-base">Peringkat Tema Berita Paling Laris</h3>
                            <p class="text-xs text-slate-400">Kategori topik UNESA yang paling sering dipublikasikan media luar</p>
                        </div>
                        <span class="text-[10px] bg-indigo-50 text-indigo-700 px-2 py-1 rounded-md font-bold">Topik Favorit</span>
                    </div>
                    <div class="h-80 relative">
                        <canvas id="categoryChart"></canvas>
                    </div>
                </div>

                <!-- Matriks Top Media & Topik Utama -->
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <div class="mb-4">
                        <h3 class="font-bold text-slate-800 text-base">Media Paling Aktif & Topik Utama Liputannya</h3>
                        <p class="text-xs text-slate-400">Menganalisis minat dan fokus isu dari masing-masing media penerbit</p>
                    </div>
                    <div class="overflow-x-auto max-h-80 overflow-y-auto">
                        <table class="w-full text-left text-sm text-slate-600">
                            <thead class="bg-slate-50 text-slate-400 text-xs uppercase sticky top-0">
                                <tr>
                                    <th class="p-2.5">Nama Media</th>
                                    <th class="p-2.5">Jumlah Berita</th>
                                    <th class="p-2.5">Topik Paling Sering Diliput</th>
                                    <th class="p-2.5">Aksi Filter</th>
                                </tr>
                            </thead>
                            <tbody id="top-media-topics-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: REKAP DATA & FILTER -->
        <div id="tab-content-rekap" class="hidden space-y-4">
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                <div class="flex flex-col md:flex-row justify-between items-center gap-4 mb-4">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base">Seluruh Arsip Pemberitaan Eksternal</h3>
                        <p class="text-xs text-slate-400">Filter berdasarkan kategori tema, tipe sumber, atau kata kunci</p>
                    </div>
                    <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
                        <!-- Filter Kategori Tema Baru -->
                        <select id="filter-kategori" onchange="filterData()" class="px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none bg-indigo-50 text-indigo-700 font-bold">
                            <option value="">Semua Kategori Tema</option>
                        </select>
                        <select id="filter-tipe" onchange="filterData()" class="px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none bg-blue-50 text-blue-700 font-bold">
                            <option value="">Semua Tipe Sumber</option>
                            <option value="Media Massa / Pers">Media Massa / Pers</option>
                            <option value="Portal Kampus / Akademik">Portal Kampus Lain</option>
                        </select>
                        <select id="filter-sentimen" onchange="filterData()" class="px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none">
                            <option value="">Semua Sentimen</option>
                            <option value="Positif">Positif</option>
                            <option value="Netral">Netral</option>
                            <option value="Negatif">Negatif</option>
                        </select>
                        <input type="text" id="search-input" onkeyup="filterData()" placeholder="Cari judul atau media..." class="px-4 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 flex-1">
                    </div>
                </div>

                <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-slate-400 text-xs uppercase sticky top-0">
                            <tr>
                                <th class="p-3">No</th>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Nama Media</th>
                                <th class="p-3">Tipe Sumber</th>
                                <th class="p-3">Judul Artikel</th>
                                <th class="p-3">Kategori Tema</th>
                                <th class="p-3">Sentimen</th>
                                <th class="p-3">Tautan</th>
                            </tr>
                        </thead>
                        <tbody id="news-full-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 3: ANALYTICS TIER & ISU NEGATIF -->
        <div id="tab-content-tier" class="hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                    <h3 class="font-bold text-slate-800 text-base mb-4">Sebaran Tone Sentimen Pemberitaan</h3>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="sentimentChart"></canvas>
                    </div>
                </div>
                <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
                    <div>
                        <h3 class="font-bold text-slate-800 text-base mb-2">Ringkasan Analisis Media</h3>
                        <p class="text-xs text-slate-500 leading-relaxed">
                            Data telah dikelompokkan secara terpisah antara media massa publik (Pers) dan website resmi kampus/perguruan tinggi lain. Hal ini memberikan gambaran yang presisi antara jangkauan opini publik nasional dengan jejaring kolaborasi akademik antar-kampus.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Tabel Khusus Monitoring Isu & Berita Negatif -->
            <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm border-t-4 border-t-rose-500">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
                    <div>
                        <h3 class="font-bold text-rose-700 text-base flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
                            Daftar Pemberitaan & Isu Ber-Tone Negatif / Kritik
                        </h3>
                        <p class="text-xs text-slate-400">Rincian seluruh berita eksternal yang terdeteksi mengandung potensi isu atau kritik</p>
                    </div>
                    <span id="badge-count-negatif" class="bg-rose-100 text-rose-700 text-xs font-bold px-3 py-1 rounded-full">0 Isu Ditemukan</span>
                </div>
                <div class="overflow-x-auto max-h-[400px] overflow-y-auto">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-rose-50 text-rose-700 text-xs uppercase sticky top-0">
                            <tr>
                                <th class="p-3">Tanggal</th>
                                <th class="p-3">Nama Media</th>
                                <th class="p-3">Judul Berita / Isu</th>
                                <th class="p-3">Kategori</th>
                                <th class="p-3">Aksi</th>
                            </tr>
                        </thead>
                        <tbody id="negative-news-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>

    <script>
        const globalData = {data_json};

        let barChartInstance = null;
        let tierChartInstance = null;
        let sentimentChartInstance = null;
        let categoryChartInstance = null;

        const monthColors = [
            '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', 
            '#EC4899', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
        ];

        function switchTab(tabName) {{
            ['ikhtisar', 'kategori', 'rekap', 'tier'].forEach(t => {{
                const el = document.getElementById(`tab-content-${{t}}`);
                const btn = document.getElementById(`tab-btn-${{t}}`);
                if (el) el.classList.add('hidden');
                if (btn) btn.className = 'tab-btn-inactive text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5';
            }});

            const targetEl = document.getElementById(`tab-content-${{tabName}}`);
            const targetBtn = document.getElementById(`tab-btn-${{tabName}}`);
            if (targetEl) targetEl.classList.remove('hidden');
            if (targetBtn) targetBtn.className = 'tab-btn-active text-xs px-3 py-1.5 rounded-lg transition flex items-center gap-1.5';
        }}

        function initDashboard() {{
            document.getElementById('data-status').innerText = globalData.length + ' Data Eksternal';
            document.getElementById('stat-total').innerText = globalData.length;

            let persCount = 0;
            let kampusCount = 0;
            let posCount = 0;

            const monthlyCounts = {{ 'Jan':0, 'Feb':0, 'Mar':0, 'Apr':0, 'Mei':0, 'Jun':0, 'Jul':0, 'Agu':0, 'Sep':0 }};
            const tipeCounts = {{ 'Media Massa / Pers':0, 'Portal Kampus / Akademik':0 }};
            const sentimentCounts = {{ 'Positif':0, 'Netral':0, 'Negatif':0 }};
            const categoryCounts = {{}};
            const mediaCategoryMap = {{}};

            globalData.forEach(row => {{
                const tipe = row.tipe_sumber || 'Media Massa / Pers';
                tipeCounts[tipe] = (tipeCounts[tipe] || 0) + 1;

                if (tipe === 'Media Massa / Pers') persCount++;
                else kampusCount++;

                const sent = row.sentimen || 'Netral';
                sentimentCounts[sent] = (sentimentCounts[sent] || 0) + 1;

                // Hitung Frekuensi Kategori Tema
                const kat = row.kategori || 'Akademik & Umum';
                categoryCounts[kat] = (categoryCounts[kat] || 0) + 1;

                // Pemetaan Media -> Topik Utama
                const mediaName = row.nama_media || 'Media Online';
                if (!mediaCategoryMap[mediaName]) mediaCategoryMap[mediaName] = {{ total:0, categories:{{}} }};
                mediaCategoryMap[mediaName].total += 1;
                mediaCategoryMap[mediaName].categories[kat] = (mediaCategoryMap[mediaName].categories[kat] || 0) + 1;

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

            // Cari Tema Terpopuler
            let topTheme = '-';
            let maxThemeCnt = 0;
            Object.entries(categoryCounts).forEach(([k, v]) => {{
                if (v > maxThemeCnt) {{ maxThemeCnt = v; topTheme = k; }}
            }});

            document.getElementById('stat-top-theme').innerText = topTheme;
            document.getElementById('stat-top-theme-cnt').innerText = maxThemeCnt + ' Berita Diliput';

            posCount = sentimentCounts['Positif'] || 0;
            const total = globalData.length || 1;

            document.getElementById('stat-pers').innerText = persCount;
            document.getElementById('stat-pers-pct').innerText = ((persCount/total)*100).toFixed(1) + '% dari Total';

            document.getElementById('stat-positive').innerText = posCount;
            document.getElementById('stat-positive-pct').innerText = ((posCount/total)*100).toFixed(1) + '% Tone Positif';

            populateCategoryDropdown(categoryCounts);
            renderCharts(monthlyCounts, tipeCounts, sentimentCounts, categoryCounts);
            renderTopMediaTopics(mediaCategoryMap);
            renderPreviewTable(globalData.slice(0, 10));
            renderFullTable(globalData);
            renderNegativeNewsTable(globalData);
        }}

        function populateCategoryDropdown(categories) {{
            const select = document.getElementById('filter-kategori');
            if (!select) return;
            select.innerHTML = '<option value="">Semua Kategori Tema</option>';
            
            Object.keys(categories).sort().forEach(kat => {{
                const option = document.createElement('option');
                option.value = kat;
                option.innerText = `${{kat}} (${{categories[kat]}})`;
                select.appendChild(option);
            }});
        }}

        function renderTopMediaTopics(mediaMap) {{
            const tbody = document.getElementById('top-media-topics-body');
            if (!tbody) return;
            tbody.innerHTML = '';

            // Sort Media dengan Berita Terbanyak
            const sortedMedia = Object.entries(mediaMap)
                .sort((a, b) => b[1].total - a[1].total)
                .slice(0, 15); // Ambil 15 teratas

            sortedMedia.forEach(([mediaName, info]) => {{
                let topKat = '-';
                let maxKatCnt = 0;
                Object.entries(info.categories).forEach(([k, v]) => {{
                    if (v > maxKatCnt) {{ maxKatCnt = v; topKat = k; }}
                }});

                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-slate-50';
                tr.innerHTML = `
                    <td class="p-2.5 font-bold text-slate-800 text-xs">${{mediaName}}</td>
                    <td class="p-2.5 font-semibold text-blue-600 text-xs">${{info.total}} Berita</td>
                    <td class="p-2.5 text-xs text-slate-700">
                        <span class="bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded font-bold text-[11px]">${{topKat}}</span>
                        <span class="text-slate-400 text-[10px]">(${{maxKatCnt}}x)</span>
                    </td>
                    <td class="p-2.5">
                        <button onclick="filterByMedia('${{mediaName}}')" class="text-xs text-blue-600 hover:underline font-bold">Filter ↗</button>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function filterByMedia(mediaName) {{
            switchTab('rekap');
            document.getElementById('search-input').value = mediaName;
            filterData();
        }}

        function filterByCategory(katName) {{
            switchTab('rekap');
            const select = document.getElementById('filter-kategori');
            if (select) {{
                select.value = katName;
                filterData();
            }}
        }}

        function renderCharts(monthlyData, tipeData, sentData, categoryData) {{
            if (typeof Chart === 'undefined') return;

            // 1. Bar Chart Bulanan
            const ctx1 = document.getElementById('barChart').getContext('2d');
            if (barChartInstance) barChartInstance.destroy();
            barChartInstance = new Chart(ctx1, {{
                type: 'bar',
                data: {{
                    labels: Object.keys(monthlyData),
                    datasets: [{{
                        label: 'Jumlah Publikasi',
                        data: Object.values(monthlyData),
                        backgroundColor: monthColors,
                        borderRadius: 8
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false, 
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ y: {{ beginAtZero: true }} }}
                }}
            }});

            // 2. Doughnut Tipe Sumber
            const ctx2 = document.getElementById('tierChart').getContext('2d');
            if (tierChartInstance) tierChartInstance.destroy();
            tierChartInstance = new Chart(ctx2, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(tipeData),
                    datasets: [{{
                        data: Object.values(tipeData),
                        backgroundColor: ['#10B981', '#3B82F6']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});

            // 3. Horizontal Bar Chart Kategori Tema Terlaris
            const ctxCat = document.getElementById('categoryChart').getContext('2d');
            if (categoryChartInstance) categoryChartInstance.destroy();

            const sortedCategories = Object.entries(categoryData).sort((a,b) => b[1] - a[1]);
            categoryChartInstance = new Chart(ctxCat, {{
                type: 'bar',
                data: {{
                    labels: sortedCategories.map(x => x[0]),
                    datasets: [{{
                        label: 'Jumlah Berita',
                        data: sortedCategories.map(x => x[1]),
                        backgroundColor: '#6366F1',
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{ x: {{ beginAtZero: true }} }}
                }}
            }});

            // 4. Pie Chart Sentimen
            const ctx3 = document.getElementById('sentimentChart').getContext('2d');
            if (sentimentChartInstance) sentimentChartInstance.destroy();
            sentimentChartInstance = new Chart(ctx3, {{
                type: 'pie',
                data: {{
                    labels: Object.keys(sentData),
                    datasets: [{{
                        data: Object.values(sentData),
                        backgroundColor: ['#10B981', '#3B82F6', '#EF4444']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
            }});
        }}

        function quickFilterSentimen(sentVal) {{
            switchTab('rekap');
            const select = document.getElementById('filter-sentimen');
            if (select) {{
                select.value = sentVal;
                filterData();
            }}
        }}

        function renderNegativeNewsTable(data) {{
            const negData = data.filter(row => (row.sentimen || '') === 'Negatif');
            const badge = document.getElementById('badge-count-negatif');
            if (badge) badge.innerText = negData.length + ' Isu Ditemukan';

            const tbody = document.getElementById('negative-news-body');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (negData.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-400 font-medium">Tidak ada pemberitaan ber-tone negatif/kritik pada periode ini. 🎉</td></tr>';
                return;
            }}

            negData.forEach(row => {{
                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-rose-50/50 transition';
                tr.innerHTML = `
                    <td class="p-3 text-xs text-slate-500 font-medium">${{row.tanggal || '-'}}</td>
                    <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                    <td class="p-3 font-medium text-slate-900">${{row.judul || '-'}}</td>
                    <td class="p-3 text-xs text-slate-600"><span class="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-semibold">${{row.kategori || 'Akademik'}}</span></td>
                    <td class="p-3"><a href="${{row.link}}" target="_blank" class="text-rose-600 font-bold text-xs hover:underline flex items-center gap-1">Buka Isu ↗</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function getSentimentBadge(sent) {{
            if (sent === 'Positif') return '<span class="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-md text-[10px] font-bold">Positif</span>';
            if (sent === 'Negatif') return '<span class="bg-rose-100 text-rose-700 px-2 py-0.5 rounded-md text-[10px] font-bold">Negatif</span>';
            return '<span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md text-[10px] font-bold">Netral</span>';
        }}

        function getCategoryBadge(kat) {{
            return `<span class="bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded-md text-[10px] font-bold">${{kat || 'Akademik'}}</span>`;
        }}

        function renderPreviewTable(data) {{
            const tbody = document.getElementById('news-preview-body');
            tbody.innerHTML = '';
            data.forEach(row => {{
                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-slate-50';
                tr.innerHTML = `
                    <td class="p-3 text-xs text-slate-400 font-medium">${{row.tanggal || '-'}}</td>
                    <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                    <td class="p-3">${{getCategoryBadge(row.kategori)}}</td>
                    <td class="p-3 font-medium text-slate-800">${{row.judul || '-'}}</td>
                    <td class="p-3">${{getSentimentBadge(row.sentimen)}}</td>
                    <td class="p-3"><a href="${{row.link}}" target="_blank" class="text-blue-600 font-bold text-xs hover:underline">Buka ↗</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function renderFullTable(data) {{
            const tbody = document.getElementById('news-full-body');
            tbody.innerHTML = '';
            data.forEach((row, idx) => {{
                const tr = document.createElement('tr');
                tr.className = 'border-b border-slate-100 hover:bg-slate-50';
                tr.innerHTML = `
                    <td class="p-3 text-xs text-slate-400">${{idx + 1}}</td>
                    <td class="p-3 text-xs text-slate-400 font-medium">${{row.tanggal || '-'}}</td>
                    <td class="p-3 font-semibold text-slate-700 text-xs">${{row.nama_media || '-'}}</td>
                    <td class="p-3 text-xs text-slate-500">${{row.tipe_sumber || 'Media Pers'}}</td>
                    <td class="p-3 font-medium text-slate-800">${{row.judul || '-'}}</td>
                    <td class="p-3">${{getCategoryBadge(row.kategori)}}</td>
                    <td class="p-3">${{getSentimentBadge(row.sentimen)}}</td>
                    <td class="p-3"><a href="${{row.link}}" target="_blank" class="text-blue-600 font-bold text-xs hover:underline">Buka ↗</a></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function filterData() {{
            const query = document.getElementById('search-input').value.toLowerCase();
            const selectedKategori = document.getElementById('filter-kategori').value;
            const selectedTipe = document.getElementById('filter-tipe').value;
            const selectedSentimen = document.getElementById('filter-sentimen').value;

            const filtered = globalData.filter(row => {{
                const tipeVal = row.tipe_sumber || 'Media Massa / Pers';
                const matchQuery = (row.judul && row.judul.toLowerCase().includes(query)) ||
                                   (row.nama_media && row.nama_media.toLowerCase().includes(query));
                const matchKategori = !selectedKategori || (row.kategori === selectedKategori);
                const matchTipe = !selectedTipe || (tipeVal === selectedTipe);
                const matchSentimen = !selectedSentimen || (row.sentimen === selectedSentimen);

                return matchQuery && matchKategori && matchTipe && matchSentimen;
            }});

            renderFullTable(filtered);
        }}

        window.onload = initDashboard;
    </script>
</body>
</html>
"""

    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"[SUKSES] File '{HTML_OUTPUT}' selesai diperbarui dengan Fitur Analisis Tema & Topik Laris!")

if __name__ == "__main__":
    build_dashboard()
