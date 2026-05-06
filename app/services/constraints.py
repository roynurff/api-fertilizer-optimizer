"""
CVRPTW Constraint Functions
Berisi evaluasi rute berdasarkan formulasi model dari PDF.

Formulasi:
  - Kapasitas: sum(demand_i) <= kapasitas_truk
  - Waktu    : sum(jarak_ij * waktu_jalan) + sum(demand_i * waktu_bongkar) <= batas_waktu
"""

from typing import List, Tuple


def evaluasi_rute_tunggal(
    rute: List[int],
    matriks_jarak: List[List[float]],
    demand: List[int],
    waktu_jalan: float,
    waktu_bongkar: float,
) -> Tuple[float, float, int]:
    """
    Evaluasi satu trip/perjalanan.

    Args:
        rute          : List node yang dikunjungi, contoh [0, 3, 11, 0]
        matriks_jarak : Matriks jarak Euclidean n x n
        demand        : List demand tiap node
        waktu_jalan   : Menit per km
        waktu_bongkar : Menit per sak

    Returns:
        (total_jarak, total_waktu, total_muatan)
    """
    total_jarak = 0.0
    total_waktu = 0.0
    total_muatan = 0

    for i in range(len(rute) - 1):
        asal = rute[i]
        tujuan = rute[i + 1]
        jarak = matriks_jarak[asal][tujuan]
        muatan = demand[tujuan]

        total_jarak += jarak
        total_muatan += muatan
        # Rumus waktu: (jarak × waktu_jalan) + (demand × waktu_bongkar)
        total_waktu += (jarak * waktu_jalan) + (muatan * waktu_bongkar)

    return total_jarak, total_waktu, total_muatan


def evaluasi_semua_rute(
    semua_rute: List[List[int]],
    matriks_jarak: List[List[float]],
    demand: List[int],
    waktu_jalan: float,
    waktu_bongkar: float,
) -> Tuple[float, float, int]:
    """
    Evaluasi seluruh rute (semua trip).

    Returns:
        (total_jarak, total_waktu, total_muatan) — sudah dibulatkan 2 desimal
    """
    z_total = 0.0
    w_total = 0.0
    q_total = 0

    for rute in semua_rute:
        j, w, q = evaluasi_rute_tunggal(rute, matriks_jarak, demand, waktu_jalan, waktu_bongkar)
        z_total += j
        w_total += w
        q_total += q

    return round(z_total, 2), round(w_total, 2), q_total


def cek_feasibility(
    rute: List[int],
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
) -> bool:
    """
    Cek apakah satu rute memenuhi kedua constraint CVRPTW.

    Returns:
        True jika feasible (memenuhi kapasitas DAN waktu), False jika tidak.
    """
    _, waktu, muatan = evaluasi_rute_tunggal(
        rute, matriks_jarak, demand, waktu_jalan, waktu_bongkar
    )
    return muatan <= kapasitas_truk and waktu <= batas_waktu


def hitung_delta_sisip(
    rute: List[int],
    node_j: int,
    posisi_sisip: int,
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
) -> float:
    """
    Hitung biaya penambahan delta (Δ) saat menyisipkan node_j di posisi_sisip.

    Rumus: Δ = c(i,j) + c(j,k) − c(i,k)
    Jika simulasi pelanggaran constraint → return inf (penalti M).

    Args:
        rute         : Rute yang sedang dimodifikasi
        node_j       : Node kios yang ingin disisipkan
        posisi_sisip : Indeks posisi penyisipan dalam rute

    Returns:
        Nilai delta, atau float('inf') jika melanggar constraint.
    """
    node_i = rute[posisi_sisip - 1]
    node_k = rute[posisi_sisip]

    delta = (
        matriks_jarak[node_i][node_j]
        + matriks_jarak[node_j][node_k]
        - matriks_jarak[node_i][node_k]
    )

    # Simulasi penyisipan untuk cek constraint
    simulasi = rute.copy()
    simulasi.insert(posisi_sisip, node_j)

    if not cek_feasibility(
        simulasi, matriks_jarak, demand,
        kapasitas_truk, batas_waktu, waktu_jalan, waktu_bongkar
    ):
        return float("inf")  # Penalti M — tidak feasible

    return delta
