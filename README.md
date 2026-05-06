# 🌾 Fertilizer Route Optimizer — FastAPI Service

Layanan optimasi rute distribusi pupuk menggunakan **CVRPTW + ALNS** (Adaptive Large Neighborhood Search).

---

## 📁 Struktur Project

```
fertilizer_optimizer/
├── app/
│   ├── main.py                      # Entry point FastAPI
│   ├── core/
│   │   └── config.py                # Konfigurasi & settings
│   ├── models/
│   │   └── schemas.py               # Pydantic request & response models
│   ├── routers/
│   │   └── optimize.py              # Endpoint POST /optimize
│   └── services/
│       ├── constraints.py           # Fungsi evaluasi CVRPTW
│       ├── operators.py             # Destroy & Repair operators ALNS
│       ├── optimizer.py             # Core ALNS loop + solusi awal
│       └── utils.py                 # Helper format response
├── tests/
│   └── test_optimize.py             # Test suite lengkap
├── laravel_integration/
│   ├── RouteOptimizerService.php    # Service Laravel
│   └── OptimizerController.php     # Controller Laravel
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Langkah Setup & Instalasi

### 1. Clone / Copy project ke server kamu

```bash
cd /var/www   # atau direktori pilihan kamu
# Copy folder fertilizer_optimizer ke sini
```

### 2. Buat Virtual Environment Python

```bash
cd fertilizer_optimizer
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# atau
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi environment

```bash
cp .env.example .env
# Edit .env — sesuaikan ALLOWED_ORIGINS dengan URL Laravel kamu
nano .env
```

---

## 🚀 Menjalankan Service

### Development (auto-reload aktif)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2
```

> **Catatan Port**: FastAPI berjalan di port **8001** (bukan 8000) agar tidak bentrok dengan Laravel yang default di port 8000.

Service berjalan → buka browser:
- **Swagger UI (Docs)**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

---

## 🧪 Testing

### Jalankan semua test

```bash
cd fertilizer_optimizer
pytest tests/ -v
```

### Jalankan test dengan output detail

```bash
pytest tests/ -v --tb=short
```

### Jalankan test class tertentu saja

```bash
pytest tests/test_optimize.py::TestOptimizeEndpoint -v
pytest tests/test_optimize.py::TestValidasiInput -v
```

### Test manual via curl

```bash
curl -X POST http://localhost:8001/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "matriks_jarak": [
      [0.00, 0.97, 2.26, 0.54, 1.53, 1.25, 9.20, 9.03, 0.19, 0.23, 1.65, 0.63, 2.05],
      [0.97, 0.00, 1.29, 1.51, 0.56, 0.34, 9.08, 9.13, 1.14, 1.18, 2.62, 1.60, 3.02],
      [2.26, 1.29, 0.00, 2.80, 0.74, 1.05, 9.05, 9.38, 2.42, 2.46, 3.90, 2.88, 4.30],
      [0.54, 1.51, 2.80, 0.00, 2.07, 1.79, 9.27, 8.99, 0.38, 0.36, 1.12, 0.20, 1.51],
      [1.53, 0.56, 0.74, 2.07, 0.00, 9.14, 9.28, 1.69, 1.43, 3.17, 2.88, 3.57, 3.29],
      [1.25, 0.34, 1.05, 1.79, 9.14, 0.00, 9.28, 9.39, 1.43, 1.44, 2.88, 1.85, 3.29],
      [9.20, 9.08, 9.05, 9.27, 9.28, 9.28, 0.00, 1.99, 9.13, 9.33, 9.75, 9.46, 9.77],
      [9.03, 9.13, 9.38, 8.99, 1.69, 9.39, 1.99, 0.00, 8.94, 9.13, 9.25, 9.17, 9.19],
      [0.19, 1.14, 2.42, 0.38, 1.43, 1.43, 9.13, 8.94, 0.00, 0.20, 1.50, 1.50, 1.89],
      [0.23, 1.18, 2.46, 0.36, 3.17, 1.44, 9.33, 9.13, 0.20, 0.00, 1.44, 0.42, 1.85],
      [1.65, 2.62, 3.90, 1.12, 2.88, 2.88, 9.75, 9.25, 1.50, 1.44, 0.00, 1.03, 0.42],
      [0.63, 1.60, 2.88, 0.20, 3.57, 1.85, 9.46, 9.17, 0.51, 0.42, 1.03, 0.00, 1.44],
      [2.05, 3.02, 4.30, 1.51, 3.29, 3.29, 9.77, 9.19, 1.89, 1.85, 0.42, 1.44, 0.00]
    ],
    "demand": [0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59],
    "kapasitas_truk": 250,
    "batas_waktu": 240.0,
    "waktu_jalan": 2.0,
    "waktu_bongkar": 0.5,
    "iterasi_target": 158,
    "masa_tanam": "MT1"
  }'
```

---

## 📡 API Reference

### POST `/api/v1/optimize`

Optimasi rute, return global best solution saja.

### POST `/api/v1/optimize/with-log`

Optimasi rute + log tiap iterasi. Gunakan untuk debugging atau visualisasi grafik konvergensi.

### GET `/health`

Cek status service. Response: `{"status": "healthy"}`

---

## 📊 Contoh Request & Response

### Request JSON

```json
{
  "matriks_jarak": [[0.00, 0.97, ...], ...],
  "demand": [0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59],
  "kapasitas_truk": 250,
  "batas_waktu": 240.0,
  "waktu_jalan": 2.0,
  "waktu_bongkar": 0.5,
  "iterasi_target": 158,
  "w_toleransi": 0.05,
  "alpha": 0.95,
  "rho": 0.1,
  "destroy_ratio": 0.30,
  "skor_pi": [33, 9, 13, 0],
  "masa_tanam": "MT1",
  "node_info": [
    {"node_id": 0, "nama": "Gudang", "latitude": -7.664482, "longitude": 111.201067},
    {"node_id": 1, "nama": "Brahman Maju", "latitude": -7.673204, "longitude": 111.201399}
  ]
}
```

### Response JSON

```json
{
  "status": "success",
  "pesan": "Optimasi berhasil. Global best ditemukan pada iterasi ke-28.",
  "masa_tanam": "MT1",
  "total_node_kios": 12,
  "total_demand_sak": 1172,
  "iterasi_terbaik": 28,
  "total_iterasi_dijalankan": 158,
  "total_jarak_km": 35.07,
  "total_waktu_menit": 656.14,
  "total_muatan_sak": 1172,
  "jumlah_trip": 6,
  "rute_terbaik": [
    {
      "trip_ke": 1,
      "rute_node": [0, 9, 10, 12, 0],
      "nama_node": ["Gudang", "Karya Makmur", "Tani Makmur", "Pinang Jaya", "Gudang"],
      "jarak_km": 4.14,
      "muatan_sak": 234,
      "kapasitas_sak": 250,
      "waktu_menit": 125.28,
      "feasible": true
    }
  ],
  "suhu_awal": 2.53,
  "suhu_akhir": 0.00098,
  "alasan_berhenti": "suhu_minimum"
}
```

---

## 🔗 Integrasi Laravel

### 1. Tambahkan ke `config/services.php`

```php
'optimizer' => [
    'url' => env('OPTIMIZER_API_URL', 'http://localhost:8001'),
],
```

### 2. Tambahkan ke `.env` Laravel

```
OPTIMIZER_API_URL=http://localhost:8001
```

### 3. Copy file integrasi

```bash
cp laravel_integration/RouteOptimizerService.php /path/to/laravel/app/Services/
cp laravel_integration/OptimizerController.php /path/to/laravel/app/Http/Controllers/
```

### 4. Register route di `routes/api.php` Laravel

```php
use App\Http\Controllers\OptimizerController;

Route::post('/optimize', [OptimizerController::class, 'optimize']);
Route::get('/optimize/health', [OptimizerController::class, 'healthCheck']);
```

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---|---|
| `Connection refused` di Laravel | Pastikan FastAPI berjalan di port 8001 |
| `CORS error` | Tambahkan URL Laravel ke `ALLOWED_ORIGINS` di `.env` |
| Timeout | Naikkan `Http::timeout(...)` di service Laravel, atau kurangi `iterasi_target` |
| `422 Unprocessable Entity` | Cek format request: matriks harus persegi, demand[0] harus 0 |
| Import error Python | Pastikan virtual environment aktif dan semua package terinstall |

---

## 📌 Catatan Teknis

- **Global Best** adalah solusi terbaik yang pernah ditemukan sepanjang iterasi, **bukan** solusi dari iterasi terakhir
- **Degree of Destruction**: `max(4, int(destroy_ratio × n_kios))` → default 4 node dari 12 kios (33%)
- **Suhu Awal**: `T = -(w_toleransi × Z_awal) / ln(0.5)` — otomatis dihitung dari solusi awal
- **Worst Removal** menggunakan noise 70%–130% untuk diversifikasi dan menghindari local optimum
