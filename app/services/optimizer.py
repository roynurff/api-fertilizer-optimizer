"""
ALNS Optimizer Core
Mengintegrasikan semua komponen:
  1. Cheapest Insertion Heuristic → Solusi Awal
  2. ALNS Loop (Destroy + Repair + SA Acceptance)
  3. Weight Update (Exponential Smoothing)
  4. Global Best Tracking
  5. Geometric Cooling Schedule
"""

import math
import random
import copy
import time
from typing import List, Tuple, Dict, Any

from app.services.constraints import (
    evaluasi_rute_tunggal,
    evaluasi_semua_rute,
    hitung_delta_sisip,
)
from app.services.operators import (
    pilih_operator,
    eksekusi_destroy,
    eksekusi_repair,
)


# ─── Solusi Awal: Cheapest Insertion Heuristic ────────────────────────────────

def buat_solusi_awal(
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
) -> List[List[int]]:
    """
    Membangun solusi awal menggunakan Cheapest Insertion Heuristic.

    Algoritma:
    - Mulai dengan satu rute kosong [0, 0]
    - Iterasi tiap kios yang belum dilayani
    - Cari pasangan (kios, rute, posisi_sisip) yang menghasilkan Δ terkecil
    - Sisipkan; jika tidak ada posisi feasible → buka trip baru

    Returns:
        List rute awal, contoh: [[0,9,10,12,0], [0,2,4,0], ...]
    """
    n_nodes = len(demand)
    kios_sisa = list(range(1, n_nodes))  # Semua kios kecuali depot (0)
    rute_aktif = [[0, 0]]

    while kios_sisa:
        delta_terbaik = float("inf")
        kios_terpilih = -1
        rute_idx_terpilih = -1
        posisi_terpilih = -1

        for kios in kios_sisa:
            for ri, rute in enumerate(rute_aktif):
                for posisi in range(1, len(rute)):
                    delta = hitung_delta_sisip(
                        rute, kios, posisi,
                        matriks_jarak, demand,
                        kapasitas_truk, batas_waktu,
                        waktu_jalan, waktu_bongkar,
                    )
                    if delta < delta_terbaik:
                        delta_terbaik = delta
                        kios_terpilih = kios
                        rute_idx_terpilih = ri
                        posisi_terpilih = posisi

        if delta_terbaik == float("inf"):
            # Tidak ada posisi feasible di rute manapun → buka trip baru
            rute_aktif.append([0, 0])
        else:
            rute_aktif[rute_idx_terpilih].insert(posisi_terpilih, kios_terpilih)
            kios_sisa.remove(kios_terpilih)

    return rute_aktif


# ─── Simulated Annealing Acceptance ───────────────────────────────────────────

def hitung_suhu_awal(w_toleransi: float, z_awal: float) -> float:
    """
    Hitung suhu awal SA berdasarkan toleransi dan nilai fungsi objektif awal.

    Rumus: T_awal = -(w × Z_awal) / ln(0.5)
    """
    return -(w_toleransi * z_awal) / math.log(0.5)


def kriteria_penerimaan_sa(
    z_baru: float,
    z_lama: float,
    suhu: float,
) -> Tuple[bool, float, float]:
    """
    Kriteria penerimaan Simulated Annealing.

    Kondisi 1: Jika ΔZ ≤ 0 → terima langsung
    Kondisi 2: Jika ΔZ > 0 → terima dengan probabilitas P = e^(-ΔZ/T)

    Returns:
        (diterima: bool, delta_z: float, probabilitas: float)
    """
    delta_z = z_baru - z_lama

    if delta_z <= 0:
        return True, delta_z, 1.0

    probabilitas = math.exp(-delta_z / suhu)
    diterima = random.random() <= probabilitas
    return diterima, delta_z, probabilitas


# ─── Scoring & Weight Update ──────────────────────────────────────────────────

def tentukan_skor(
    z_baru: float,
    z_lama: float,
    z_global_best: float,
    diterima: bool,
    skor_pi: List[int],
) -> int:
    """
    Tentukan reward score untuk operator yang baru bertugas.

    π1 = skor_pi[0] : Global Best baru
    π2 = skor_pi[1] : Lebih baik dari current, tapi bukan global best
    π3 = skor_pi[2] : Lebih buruk, tapi diterima SA (diversifikasi)
    π4 = skor_pi[3] : Ditolak
    """
    if z_baru < z_global_best:
        return skor_pi[0]
    if z_baru < z_lama:
        return skor_pi[1]
    if diterima:
        return skor_pi[2]
    return skor_pi[3]


def update_bobot(bobot_lama: float, skor: int, rho: float) -> float:
    """
    Perbarui bobot operator dengan exponential smoothing.

    Rumus: w_(i+1) = (1 - ρ) × w_i + ρ × π
    """
    return round((1 - rho) * bobot_lama + (rho * skor), 4)


# ─── Main ALNS Optimizer ──────────────────────────────────────────────────────

def jalankan_alns(
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
    iterasi_target: int,
    w_toleransi: float,
    alpha: float,
    rho: float,
    destroy_ratio: float,
    skor_pi: List[int],
) -> Dict[str, Any]:
    """
    Jalankan algoritma ALNS lengkap.

    Returns:
        Dict berisi semua hasil: rute_terbaik, total_jarak, iterasi_terbaik,
        log iterasi, suhu awal/akhir, alasan berhenti, dll.
    """
    waktu_mulai = time.time()

    # ── 1. Hitung degree of destruction ──────────────────────────────────────
    n_kios = len(demand) - 1  # Total kios (tidak termasuk depot)
    n_destroy = max(4, int(destroy_ratio * n_kios))

    # ── 2. Buat solusi awal ───────────────────────────────────────────────────
    solusi_awal = buat_solusi_awal(
        matriks_jarak, demand, kapasitas_truk,
        batas_waktu, waktu_jalan, waktu_bongkar,
    )
    z_awal, w_awal, q_awal = evaluasi_semua_rute(
        solusi_awal, matriks_jarak, demand, waktu_jalan, waktu_bongkar
    )

    # ── 3. Hitung suhu awal ───────────────────────────────────────────────────
    suhu_awal = hitung_suhu_awal(w_toleransi, z_awal)

    # ── 4. Inisialisasi state ─────────────────────────────────────────────────
    r_global_best = copy.deepcopy(solusi_awal)
    z_global_best = z_awal
    r_current = copy.deepcopy(solusi_awal)
    z_current = z_awal
    suhu_current = suhu_awal

    # Bobot operator: [destroy_0=Random, destroy_1=Worst], [repair_0=Greedy]
    bobot_destroy = [1.0, 1.0]
    bobot_repair = [1.0]

    iterasi_terbaik = 0  # 0 = global best adalah solusi awal
    log_iterasi = []
    alasan_berhenti = "iterasi_maksimal"
    iterasi_berjalan = 0

    # ── 5. ALNS Loop ──────────────────────────────────────────────────────────
    for i in range(1, iterasi_target + 1):
        iterasi_berjalan = i

        # Pilih operator
        id_destroy = pilih_operator(bobot_destroy)
        id_repair = pilih_operator(bobot_repair)  # Saat ini hanya 1 repair operator

        nama_destroy = "Random" if id_destroy == 0 else "Worst"

        # Fase Destroy
        r_bolong, node_tercabut = eksekusi_destroy(
            r_current, id_destroy, n_destroy, demand, waktu_bongkar
        )

        # Fase Repair
        r_baru = eksekusi_repair(
            r_bolong, node_tercabut,
            matriks_jarak, demand,
            kapasitas_truk, batas_waktu,
            waktu_jalan, waktu_bongkar,
        )

        z_baru, w_baru, _ = evaluasi_semua_rute(
            r_baru, matriks_jarak, demand, waktu_jalan, waktu_bongkar
        )

        # Kriteria penerimaan SA
        diterima, delta_z, prob = kriteria_penerimaan_sa(z_baru, z_current, suhu_current)

        # Tentukan skor & update bobot
        skor = tentukan_skor(z_baru, z_current, z_global_best, diterima, skor_pi)
        bobot_destroy[id_destroy] = update_bobot(bobot_destroy[id_destroy], skor, rho)
        bobot_repair[id_repair] = update_bobot(bobot_repair[id_repair], skor, rho)

        # Update solusi current & global best
        status = "DITOLAK"
        if diterima:
            r_current = copy.deepcopy(r_baru)
            z_current = z_baru
            status = "DITERIMA"

            if z_baru < z_global_best:
                r_global_best = copy.deepcopy(r_baru)
                z_global_best = z_baru
                iterasi_terbaik = i
                status = "GLOBAL BEST"

        # Catat log
        log_iterasi.append({
            "iterasi": i,
            "operator_destroy": nama_destroy,
            "node_dicabut": node_tercabut,
            "jarak_km": z_baru,
            "waktu_menit": w_baru,
            "status": status,
            "suhu": round(suhu_current, 5),
        })

        # Cooling schedule: T_(i+1) = α × T_i
        suhu_current *= alpha

        # Kriteria berhenti: suhu minimum
        # if suhu_current <= 0.001:
        #     alasan_berhenti = "suhu_minimum"
        #     break

    suhu_akhir = suhu_current
    waktu_selesai = time.time()
    durasi_komputasi = round(waktu_selesai - waktu_mulai, 3)

    # ── 6. Evaluasi hasil final ───────────────────────────────────────────────
    z_final, w_final, q_final = evaluasi_semua_rute(
        r_global_best, matriks_jarak, demand, waktu_jalan, waktu_bongkar
    )

    return {
        "rute_terbaik": r_global_best,
        "z_global_best": z_final,
        "w_global_best": w_final,
        "q_global_best": q_final,
        "iterasi_terbaik": iterasi_terbaik,
        "total_iterasi_dijalankan": iterasi_berjalan,
        "solusi_awal": solusi_awal,
        "z_awal": z_awal,
        "suhu_awal": round(suhu_awal, 5),
        "suhu_akhir": round(suhu_akhir, 5),
        "alasan_berhenti": alasan_berhenti,
        "log_iterasi": log_iterasi,
        "durasi_komputasi_detik": durasi_komputasi,
        "n_destroy": n_destroy,
    }
