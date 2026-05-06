"""
Pydantic models — request & response schemas untuk endpoint /optimize
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# ─── Sub-models ───────────────────────────────────────────────────────────────

class NodeInfo(BaseModel):
    """Informasi opsional tiap node (nama kios, koordinat) — untuk display di Laravel."""
    node_id: int
    nama: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TripDetail(BaseModel):
    """Detail satu trip/perjalanan dalam rute terbaik."""
    trip_ke: int
    rute_node: List[int]                     # contoh: [0, 9, 10, 12, 0]
    nama_node: Optional[List[str]] = None    # contoh: ["Gudang", "Karya Makmur", ...]
    jarak_km: float
    muatan_sak: int
    kapasitas_sak: int
    waktu_menit: float
    feasible: bool


# ─── Request Model ─────────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    """
    Request body dari Laravel ke FastAPI.
    Semua parameter dinamis — tidak ada hardcode di sini.
    """

    # --- Data Utama (WAJIB) ---
    matriks_jarak: List[List[float]] = Field(
        ...,
        description="Matriks jarak Euclidean antar node (n x n). Index 0 = Gudang/Depot.",
        example=[
            [0.00, 0.97, 2.26],
            [0.97, 0.00, 1.29],
            [2.26, 1.29, 0.00],
        ]
    )
    demand: List[int] = Field(
        ...,
        description="Demand tiap node dalam sak. Index 0 = Gudang (harus 0).",
        example=[0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59]
    )

    # --- Constraint Parameter ---
    kapasitas_truk: int = Field(
        default=250,
        ge=1,
        description="Kapasitas maksimum truk dalam sak."
    )
    batas_waktu: float = Field(
        default=240.0,
        gt=0,
        description="Batas waktu operasional maksimum per trip dalam menit."
    )
    waktu_jalan: float = Field(
        default=2.0,
        gt=0,
        description="Waktu tempuh per km dalam menit (default: 2 menit/km = 30 km/jam)."
    )
    waktu_bongkar: float = Field(
        default=0.5,
        gt=0,
        description="Waktu bongkar per sak pupuk dalam menit."
    )

    # --- ALNS Hyperparameter ---
    iterasi_target: int = Field(
        default=158,
        ge=10,
        le=10000,
        description="Jumlah iterasi maksimum ALNS."
    )
    w_toleransi: float = Field(
        default=0.05,
        gt=0,
        lt=1,
        description="Toleransi probabilitas SA saat hitung suhu awal (default: 0.05 = 5%)."
    )
    alpha: float = Field(
        default=0.95,
        gt=0,
        lt=1,
        description="Cooling rate Simulated Annealing (default: 0.95)."
    )
    rho: float = Field(
        default=0.1,
        gt=0,
        lt=1,
        description="Reaction factor pembaruan bobot operator (default: 0.1)."
    )
    destroy_ratio: float = Field(
        default=0.30,
        gt=0,
        lt=1,
        description="Proporsi node yang dicabut saat fase destroy (default: 30%)."
    )
    skor_pi: List[int] = Field(
        default=[33, 9, 13, 0],
        min_length=4,
        max_length=4,
        description="Skor reward operator: [global_best, lebih_baik, diterima_sa, ditolak]."
    )

    # --- Informasi Tambahan (opsional, untuk display nama node di response) ---
    node_info: Optional[List[NodeInfo]] = Field(
        default=None,
        description="Informasi opsional nama dan koordinat tiap node."
    )

    # --- Masa Tanam (opsional, hanya untuk metadata response) ---
    masa_tanam: Optional[str] = Field(
        default=None,
        description="Label masa tanam (misal: 'MT1', 'MT2', 'MT3') — hanya untuk metadata."
    )

    # ─── Validators ───────────────────────────────────────────────────────────

    @field_validator("matriks_jarak")
    @classmethod
    def validate_matriks(cls, v: List[List[float]]) -> List[List[float]]:
        n = len(v)
        if n < 2:
            raise ValueError("Matriks jarak minimal berukuran 2x2 (1 depot + 1 kios).")
        for i, row in enumerate(v):
            if len(row) != n:
                raise ValueError(f"Matriks jarak harus berbentuk persegi (n x n). Baris {i} memiliki {len(row)} kolom, seharusnya {n}.")
        return v

    @field_validator("demand")
    @classmethod
    def validate_demand(cls, v: List[int]) -> List[int]:
        if v[0] != 0:
            raise ValueError("Demand index 0 (Gudang/Depot) harus bernilai 0.")
        if any(d < 0 for d in v):
            raise ValueError("Semua nilai demand harus >= 0.")
        return v

    @field_validator("skor_pi")
    @classmethod
    def validate_skor(cls, v: List[int]) -> List[int]:
        if len(v) != 4:
            raise ValueError("skor_pi harus memiliki tepat 4 nilai: [pi1, pi2, pi3, pi4].")
        return v

    def validate_consistency(self):
        """Cross-field validation: panjang matriks harus sama dengan panjang demand."""
        n_matrix = len(self.matriks_jarak)
        n_demand = len(self.demand)
        if n_matrix != n_demand:
            raise ValueError(
                f"Ukuran matriks_jarak ({n_matrix}x{n_matrix}) "
                f"tidak konsisten dengan panjang demand ({n_demand}). "
                f"Keduanya harus sama."
            )


# ─── Response Models ──────────────────────────────────────────────────────────

class OptimizeResponse(BaseModel):
    """Response dari FastAPI ke Laravel."""

    # Status
    status: str = Field(..., description="'success' atau 'error'")
    pesan: str = Field(..., description="Pesan deskriptif hasil optimasi.")

    # Metadata request
    masa_tanam: Optional[str] = None
    total_node_kios: int = Field(..., description="Jumlah kios yang dilayani (tidak termasuk depot).")
    total_demand_sak: int = Field(..., description="Total seluruh demand dalam sak.")

    # Hasil optimasi
    iterasi_terbaik: int = Field(..., description="Nomor iterasi saat global best ditemukan (0 = solusi awal).")
    total_iterasi_dijalankan: int = Field(..., description="Total iterasi yang benar-benar berjalan.")
    total_jarak_km: float = Field(..., description="Total jarak tempuh global best dalam km.")
    total_waktu_menit: float = Field(..., description="Total waktu operasional global best dalam menit.")
    total_muatan_sak: int = Field(..., description="Total muatan yang berhasil dikirim dalam sak.")
    jumlah_trip: int = Field(..., description="Jumlah trip/perjalanan dalam solusi terbaik.")

    # Rute terbaik
    rute_terbaik: List[TripDetail] = Field(..., description="Detail setiap trip dalam rute terbaik.")

    # Info algoritma
    suhu_awal: float
    suhu_akhir: float
    alasan_berhenti: str = Field(..., description="'iterasi_maksimal' atau 'suhu_minimum'.")

    class Config:
        json_schema_extra = {
            "example": {
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
                        "feasible": True,
                    }
                ],
                "suhu_awal": 2.53,
                "suhu_akhir": 0.00098,
                "alasan_berhenti": "suhu_minimum",
            }
        }


class ErrorResponse(BaseModel):
    status: str = "error"
    pesan: str
    detail: Optional[str] = None
