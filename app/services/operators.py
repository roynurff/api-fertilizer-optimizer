"""
ALNS Operator Module
Berisi operator Destroy dan Repair sesuai literatur Ropke & Pisinger (2006).

Destroy Operators:
  - Random Removal : Cabut node secara acak penuh
  - Worst Removal  : Cabut node berdasarkan biaya/muatan terburuk + noise

Repair Operator:
  - Greedy Insertion (Cheapest Insertion): Sisipkan ke posisi yang menambah jarak terkecil
"""

import random
import copy
from typing import List, Tuple

from app.services.constraints import hitung_delta_sisip


# ─── Operator Selector ────────────────────────────────────────────────────────

def pilih_operator(bobot: List[float]) -> int:
    """
    Pilih operator menggunakan roulette wheel selection berdasarkan bobot.
    Menghitung probabilitas tiap operator: p_o = w_o / sum(w_d)

    Returns:
        Index operator yang terpilih.
    """
    total = sum(bobot)
    prob = [w / total for w in bobot]
    r = random.random()
    akumulasi = 0.0
    for i, p in enumerate(prob):
        akumulasi += p
        if r <= akumulasi:
            return i
    return len(bobot) - 1


# ─── Destroy Operators ────────────────────────────────────────────────────────

def random_removal(
    rute_kerja: List[List[int]],
    n_destroy: int,
) -> Tuple[List[List[int]], List[int]]:
    """
    Operator 0: Random Removal
    Mencabut n_destroy node secara acak murni dari rute.

    Returns:
        (rute_bolong, list_node_tercabut)
    """
    kios_aktif = [n for r in rute_kerja for n in r if n != 0]
    tercabut = random.sample(kios_aktif, min(n_destroy, len(kios_aktif)))

    for rute in rute_kerja:
        for node in tercabut:
            if node in rute:
                rute.remove(node)

    # Hapus rute yang sekarang hanya berisi [0, 0] (kosong)
    rute_bersih = [r for r in rute_kerja if len(r) > 2]
    return rute_bersih, tercabut


def worst_removal(
    rute_kerja: List[List[int]],
    n_destroy: int,
    demand: List[int],
    waktu_bongkar: float,
) -> Tuple[List[List[int]], List[int]]:
    """
    Operator 1: Worst Removal dengan Noise (70%–130%)
    Mencabut node berdasarkan kontribusi waktu bongkar terbesar,
    ditambah noise acak agar tidak terjebak mencabut node yang sama terus.

    Noise ini merupakan best-practice dari Ropke & Pisinger (2006)
    untuk diversifikasi pencarian.

    Returns:
        (rute_bolong, list_node_tercabut)
    """
    kios_aktif = [n for r in rute_kerja for n in r if n != 0]

    # Sort berdasarkan kontribusi waktu bongkar × noise acak
    diurutkan = sorted(
        kios_aktif,
        key=lambda x: (demand[x] * waktu_bongkar) * random.uniform(0.7, 1.3),
        reverse=True,
    )
    tercabut = diurutkan[:n_destroy]

    for rute in rute_kerja:
        for node in tercabut:
            if node in rute:
                rute.remove(node)

    rute_bersih = [r for r in rute_kerja if len(r) > 2]
    return rute_bersih, tercabut


def eksekusi_destroy(
    rute_input: List[List[int]],
    id_operator: int,
    n_destroy: int,
    demand: List[int],
    waktu_bongkar: float,
) -> Tuple[List[List[int]], List[int]]:
    """
    Dispatcher untuk operator destroy.

    Args:
        id_operator : 0 = Random Removal, 1 = Worst Removal

    Returns:
        (rute_bolong, list_node_tercabut)
    """
    rute_kerja = copy.deepcopy(rute_input)

    if id_operator == 0:
        return random_removal(rute_kerja, n_destroy)
    else:
        return worst_removal(rute_kerja, n_destroy, demand, waktu_bongkar)


# ─── Repair Operator ──────────────────────────────────────────────────────────

def greedy_insertion(
    rute_bolong: List[List[int]],
    node_tercabut: List[int],
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
) -> List[List[int]]:
    """
    Greedy Insertion (Cheapest Insertion Heuristic)
    Menyisipkan setiap node yang tercabut ke posisi yang menghasilkan
    penambahan jarak terkecil (Δ minimum) sambil tetap feasible.

    Jika tidak ada posisi feasible di rute yang ada → buat trip baru.

    Returns:
        rute_baru yang sudah lengkap (semua node tersisipkan kembali)
    """
    rute_kerja = copy.deepcopy(rute_bolong)

    # Pastikan ada minimal satu rute aktif
    if not rute_kerja:
        rute_kerja.append([0, 0])

    for node in node_tercabut:
        delta_terbaik = float("inf")
        rute_idx_terbaik = -1
        posisi_terbaik = -1

        for ri, rute in enumerate(rute_kerja):
            for posisi in range(1, len(rute)):
                delta = hitung_delta_sisip(
                    rute, node, posisi,
                    matriks_jarak, demand,
                    kapasitas_truk, batas_waktu,
                    waktu_jalan, waktu_bongkar,
                )
                if delta < delta_terbaik:
                    delta_terbaik = delta
                    rute_idx_terbaik = ri
                    posisi_terbaik = posisi

        if delta_terbaik == float("inf"):
            # Tidak ada posisi feasible → buat trip baru khusus node ini
            rute_kerja.append([0, node, 0])
        else:
            rute_kerja[rute_idx_terbaik].insert(posisi_terbaik, node)

    return rute_kerja


def eksekusi_repair(
    rute_bolong: List[List[int]],
    node_tercabut: List[int],
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
) -> List[List[int]]:
    """
    Dispatcher untuk operator repair (saat ini hanya Greedy Insertion).
    Mudah diperluas ke Regret Insertion di masa depan.
    """
    return greedy_insertion(
        rute_bolong, node_tercabut,
        matriks_jarak, demand,
        kapasitas_truk, batas_waktu,
        waktu_jalan, waktu_bongkar,
    )
