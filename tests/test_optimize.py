"""
Test Suite — CVRPTW ALNS FastAPI Service
Jalankan dengan: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ─── Data Test (sama persis dengan notebook kamu) ─────────────────────────────

MATRIKS_JARAK = [
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
    [2.05, 3.02, 4.30, 1.51, 3.29, 3.29, 9.77, 9.19, 1.89, 1.85, 0.42, 1.44, 0.00],
]

DEMAND_MT1 = [0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59]  # UREA MT1

NODE_INFO = [
    {"node_id": 0, "nama": "Gudang", "latitude": -7.664482, "longitude": 111.201067},
    {"node_id": 1, "nama": "Brahman Maju", "latitude": -7.673204, "longitude": 111.201399},
    {"node_id": 2, "nama": "Sumber Makmur", "latitude": -7.684752, "longitude": 111.201509},
    {"node_id": 3, "nama": "Gading Makmur", "latitude": -7.659649, "longitude": 111.200538},
    {"node_id": 4, "nama": "Margo Rukun", "latitude": -7.678135, "longitude": 111.202285},
    {"node_id": 5, "nama": "Margo Rukun Abadi", "latitude": -7.675488, "longitude": 111.203398},
    {"node_id": 6, "nama": "Margo Rukun Barokah", "latitude": -7.681612, "longitude": 111.120244},
    {"node_id": 7, "nama": "Krida Tani 1", "latitude": -7.663758, "longitude": 111.119909},
    {"node_id": 8, "nama": "Krida Tani 2", "latitude": -7.663058, "longitude": 111.200173},
    {"node_id": 9, "nama": "Karya Makmur", "latitude": -7.662627, "longitude": 111.201903},
    {"node_id": 10, "nama": "Tani Makmur", "latitude": -7.649686, "longitude": 111.201824},
    {"node_id": 11, "nama": "Tani Makmur Abadi", "latitude": -7.658894, "longitude": 111.202158},
    {"node_id": 12, "nama": "Pinang Jaya", "latitude": -7.646107, "longitude": 111.200528},
]

PAYLOAD_VALID = {
    "matriks_jarak": MATRIKS_JARAK,
    "demand": DEMAND_MT1,
    "kapasitas_truk": 250,
    "batas_waktu": 240.0,
    "waktu_jalan": 2.0,
    "waktu_bongkar": 0.5,
    "iterasi_target": 50,   # Sengaja kecil agar test cepat
    "w_toleransi": 0.05,
    "alpha": 0.95,
    "rho": 0.1,
    "destroy_ratio": 0.30,
    "skor_pi": [33, 9, 13, 0],
    "masa_tanam": "MT1",
    "node_info": NODE_INFO,
}


# ─── Health Check Tests ───────────────────────────────────────────────────────

class TestHealthEndpoints:
    def test_root_ok(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


# ─── Optimize Endpoint Tests ──────────────────────────────────────────────────

class TestOptimizeEndpoint:

    def test_optimize_success_status_200(self):
        """Endpoint harus return 200 dengan payload valid."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        assert r.status_code == 200

    def test_optimize_response_structure(self):
        """Response harus memiliki semua field yang dibutuhkan."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        required_fields = [
            "status", "pesan", "total_node_kios", "total_demand_sak",
            "iterasi_terbaik", "total_iterasi_dijalankan",
            "total_jarak_km", "total_waktu_menit", "total_muatan_sak",
            "jumlah_trip", "rute_terbaik", "suhu_awal", "suhu_akhir",
            "alasan_berhenti",
        ]
        for field in required_fields:
            assert field in data, f"Field '{field}' tidak ada di response"

    def test_optimize_status_success(self):
        """Field status harus 'success'."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        assert r.json()["status"] == "success"

    def test_optimize_semua_kios_terlayani(self):
        """Semua 12 kios harus terlayani dalam rute terbaik."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        node_terlayani = set()
        for trip in data["rute_terbaik"]:
            for node in trip["rute_node"]:
                if node != 0:
                    node_terlayani.add(node)

        assert node_terlayani == set(range(1, 13)), \
            f"Node yang terlayani: {sorted(node_terlayani)}, seharusnya: {list(range(1, 13))}"

    def test_optimize_constraint_kapasitas(self):
        """Setiap trip tidak boleh melebihi kapasitas truk."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        for trip in data["rute_terbaik"]:
            assert trip["muatan_sak"] <= PAYLOAD_VALID["kapasitas_truk"], \
                f"Trip {trip['trip_ke']} melebihi kapasitas: {trip['muatan_sak']} sak"

    def test_optimize_constraint_waktu(self):
        """Setiap trip tidak boleh melebihi batas waktu operasional."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        for trip in data["rute_terbaik"]:
            assert trip["waktu_menit"] <= PAYLOAD_VALID["batas_waktu"], \
                f"Trip {trip['trip_ke']} melebihi batas waktu: {trip['waktu_menit']} menit"

    def test_optimize_rute_dimulai_dan_diakhiri_depot(self):
        """Setiap rute harus dimulai dan diakhiri di node 0 (depot/gudang)."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        for trip in data["rute_terbaik"]:
            assert trip["rute_node"][0] == 0, f"Trip {trip['trip_ke']} tidak dimulai dari depot"
            assert trip["rute_node"][-1] == 0, f"Trip {trip['trip_ke']} tidak kembali ke depot"

    def test_optimize_global_best_bukan_harus_iterasi_terakhir(self):
        """iterasi_terbaik harus <= total_iterasi_dijalankan."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()
        assert data["iterasi_terbaik"] <= data["total_iterasi_dijalankan"]

    def test_optimize_total_muatan_sesuai_demand(self):
        """Total muatan global best harus sama dengan total demand semua kios."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        total_demand = sum(DEMAND_MT1)
        assert data["total_muatan_sak"] == total_demand, \
            f"Total muatan {data['total_muatan_sak']} ≠ total demand {total_demand}"

    def test_optimize_nama_node_ada_di_response(self):
        """Jika node_info dikirim, nama_node harus tampil di tiap trip."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        data = r.json()

        for trip in data["rute_terbaik"]:
            assert trip["nama_node"] is not None
            assert len(trip["nama_node"]) == len(trip["rute_node"])

    def test_optimize_masa_tanam_di_response(self):
        """masa_tanam harus diteruskan ke response."""
        r = client.post("/api/v1/optimize", json=PAYLOAD_VALID)
        assert r.json()["masa_tanam"] == "MT1"

    def test_optimize_dengan_iterasi_berbeda(self):
        """Endpoint harus berjalan dengan jumlah iterasi berbeda."""
        payload_kecil = {**PAYLOAD_VALID, "iterasi_target": 10}
        r = client.post("/api/v1/optimize", json=payload_kecil)
        assert r.status_code == 200
        assert r.json()["total_iterasi_dijalankan"] <= 10


# ─── Validation Error Tests ───────────────────────────────────────────────────

class TestValidasiInput:

    def test_demand_depot_bukan_nol(self):
        """Demand index 0 yang bukan 0 harus ditolak."""
        payload = {**PAYLOAD_VALID, "demand": [5] + DEMAND_MT1[1:]}
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code in [400, 422]

    def test_matriks_tidak_persegi(self):
        """Matriks yang tidak persegi harus ditolak."""
        matriks_rusak = [row[:10] for row in MATRIKS_JARAK]  # Potong jadi n x 10
        payload = {**PAYLOAD_VALID, "matriks_jarak": matriks_rusak}
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code in [400, 422]

    def test_panjang_demand_tidak_konsisten(self):
        """Panjang demand berbeda dari ukuran matriks harus ditolak."""
        payload = {**PAYLOAD_VALID, "demand": DEMAND_MT1[:-1]}  # Kurangi 1 elemen
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code in [400, 422]

    def test_iterasi_kurang_dari_minimum(self):
        """iterasi_target < 10 harus ditolak Pydantic."""
        payload = {**PAYLOAD_VALID, "iterasi_target": 5}
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code == 422

    def test_kapasitas_negatif(self):
        """kapasitas_truk <= 0 harus ditolak."""
        payload = {**PAYLOAD_VALID, "kapasitas_truk": 0}
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code == 422

    def test_skor_pi_kurang_dari_4(self):
        """skor_pi dengan kurang dari 4 elemen harus ditolak."""
        payload = {**PAYLOAD_VALID, "skor_pi": [33, 9, 13]}
        r = client.post("/api/v1/optimize", json=payload)
        assert r.status_code == 422


# ─── With-Log Endpoint Tests ──────────────────────────────────────────────────

class TestOptimizeWithLog:

    def test_with_log_ada_field_log_iterasi(self):
        """Endpoint /optimize/with-log harus menyertakan log_iterasi."""
        r = client.post("/api/v1/optimize/with-log", json=PAYLOAD_VALID)
        assert r.status_code == 200
        data = r.json()
        assert "log_iterasi" in data
        assert isinstance(data["log_iterasi"], list)
        assert len(data["log_iterasi"]) > 0

    def test_with_log_struktur_log(self):
        """Setiap entry log harus memiliki field yang benar."""
        r = client.post("/api/v1/optimize/with-log", json=PAYLOAD_VALID)
        log = r.json()["log_iterasi"]
        entry = log[0]

        required = ["iterasi", "operator_destroy", "node_dicabut", "jarak_km", "waktu_menit", "status"]
        for field in required:
            assert field in entry, f"Field '{field}' tidak ada di log entry"

    def test_with_log_ada_durasi_komputasi(self):
        """Response harus menyertakan durasi komputasi."""
        r = client.post("/api/v1/optimize/with-log", json=PAYLOAD_VALID)
        assert "durasi_komputasi_detik" in r.json()
