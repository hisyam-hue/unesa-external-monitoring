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

    # Hitung ringkasan
    total_publikasi = len(df)
    total_media = len(df[df['tier_media'].isin(['Tier 1 (Nasional)', 'Tier 2 (Regional)'])])
    
    positif_count = len(df[df['sentimen'] == 'Positif'])
    netral_count = len(df[df['sentimen'] == 'Netral'])
    negatif_count = len(df[df['sentimen'] == 'Negatif'])
    
    # Hitung Sub-Isu Krisis untuk berita negatif
    df_negatif = df[df['sentimen'] == 'Negatif']
    sub_isu_counts = df_negatif['sub_isu'].value_counts().to_dict() if 'sub_isu' in df_negatif.columns else {}

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
                <button onclick="switchTab('tone')" id="btn-tone" class="tab-btn px-4 py-2 rounded-lg transition">🚨 Analisis Tone Pemberitaan</button>
            </div>
        </div>

        <!-- Metric Cards -->
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
                <p class="text-xs font-semibold text-slate-500 uppercase">Tone Positif</p>
                <h3 class="text-3xl font-bold text-emerald-600 mt-2">{positif_count}</h3>
                <span class="text-xs text-emerald-600 font-medium">{round(positif_count/total_publikasi*100, 1) if total_publikasi else 0}% Sentimen Positif</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Tone Netral</p>
                <h3 class="text-3xl font-bold text-slate-600 mt-2">{netral_count}</h3>
                <span class="text-xs text-slate-500 font-medium">{round(netral_count/total_publikasi*100, 1) if total_publikasi else 0}% Sentimen Netral</span>
            </div>
            <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <p class="text-xs font-semibold text-slate-500 uppercase">Isu / Tone Negatif</p>
                <h3 class="text-3xl font-bold text-rose-600 mt-2">{negatif_count}</h3>
                <span class="text-xs text-rose-600 font-medium">{round(negatif_count/total_publikasi*100, 1) if total_publikasi else 0}% Perlu Atensi Humas</span>
            </div>
        </div>

        <!-- TAB TONE PEMBERITAAN -->
        <div id="tab-tone" class="space-y-6">
            <div class="grid grid-cols-2 gap-6">
                <!-- Donut Chart Tone -->
                <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h2 class="text-lg font-bold text-slate-800 mb-1">Proporsi Tone Pemberitaan</h2>
                    <p class="text-xs text-slate-500 mb-4">Grafik persentase persepsi publik pada berita eksternal</p>
                    <div class="h-64 flex justify-center">
                        <canvas id="toneChart"></canvas>
                    </div>
                </div>

                <!-- Bar Chart Sub-Isu Krisis (BARU) -->
                <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <div class="flex justify-between items-center mb-1">
                        <h2 class="text-lg font-bold text-slate-800">Rincian Sub-Isu Krisis (Tone Negatif)</h2>
                        <span class="bg-rose-100 text-rose-700 text-xs px-2.5 py-1 rounded-full font-bold">{negatif_count} Isu</span>
                    </div>
                    <p class="text-xs text-slate-500 mb-4">Distribusi klaster topik berita bernada negatif yang memerlukan mitigasi Humas</p>
                    <div class="h-64">
                        <canvas id="subIsuChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tabel Berita Negatif -->
            <div class="bg-white rounded-2xl border border-rose-200 shadow-sm overflow-hidden">
                <div class="bg-rose-50/50 p-6 border-b border-rose-100 flex justify-between items-center">
                    <div>
                        <h2 class="text-lg font-bold text-rose-900 flex items-center gap-2">🚨 Daftar Berita Tone Negatif & Isu Atensi Humas</h2>
                        <p class="text-xs text-rose-600">Pemberitaan eksternal yang memerlukan klarifikasi atau strategi penanganan krisis</p>
                    </div>
                </div>
                <div class="overflow-x-auto max-h-[500px]">
                    <table class="w-full text-left text-sm text-slate-600">
                        <thead class="bg-slate-50 text-xs uppercase text-slate-500 sticky top-0 border-b border-slate-200">
                            <tr>
                                <th class="p-4">Tanggal</th>
                                <th class="p-4">Judul Berita</th>
                                <th class="p-4">Sub-Isu Krisis</th>
                                <th class="p-4">Nama Media</th>
                                <th class="p-4">Aksi</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100" id="table-negatif-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        const rawData = {df.to_json(orient='records')};

        // Render Donut Chart
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

        // Render Sub-Isu Bar Chart (BARU)
        const subIsuData = {json.dumps(sub_isu_counts)};
        new Chart(document.getElementById('subIsuChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(subIsuData),
                datasets: [{{
                    label: 'Jumlah Berita',
                    data: Object.values(subIsuData),
                    backgroundColor: '#e11d48',
                    borderRadius: 6
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
            <tr class="hover:bg-slate-50 transition">
                <td class="p-4 whitespace-nowrap text-xs text-slate-500">${{item.tanggal || '-'}}</td>
                <td class="p-4 font-semibold text-slate-800">${{item.judul}}</td>
                <td class="p-4"><span class="bg-rose-100 text-rose-700 text-xs px-2.5 py-1 rounded-full font-medium">${{item.sub_isu || 'Isu Krisis'}}</span></td>
                <td class="p-4 text-xs text-slate-600">${{item.nama_media || item.sumber}}</td>
                <td class="p-4"><a href="${{item.link}}" target="_blank" class="text-blue-600 hover:underline text-xs font-semibold">Buka Isu ↗</a></td>
            </tr>
        `).join('');
    </script>
</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Dashboard HTML berhasil dibuat!")

if __name__ == "__main__":
    generate_dashboard()
