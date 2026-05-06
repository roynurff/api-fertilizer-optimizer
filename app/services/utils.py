"""
Utility Functions
Helper untuk memformat hasil optimasi menjadi response schema yang clean.
"""

from typing import List, Optional, Dict, Any

from app.models.schemas import TripDetail, OptimizeResponse
from app.services.constraints import evaluasi_rute_tunggal


def bangun_nama_node_map(
    node_info: Optional[List] = None,
    n_nodes: int = 0,
) -> Dict[int, str]:
    """
    Buat mapping node_id → nama dari node_info opsional.
    Default: "Node {id}" jika tidak ada nama.
    """
    nama_map = {0: "Gudang"}
    for i in range(1, n_nodes):
        nama_map[i] = f"Node {i}"

    if node_info:
        for info in node_info:
            nama_map[info.node_id] = info.nama or f"Node {info.node_id}"

    return nama_map


def format_trip_detail(
    trip_idx: int,
    rute: List[int],
    matriks_jarak: List[List[float]],
    demand: List[int],
    kapasitas_truk: int,
    batas_waktu: float,
    waktu_jalan: float,
    waktu_bongkar: float,
    nama_map: Dict[int, str],
) -> TripDetail:
    """
    Format satu rute menjadi TripDetail untuk response JSON.
    """
    jarak, waktu, muatan = evaluasi_rute_tunggal(
        rute, matriks_jarak, demand, waktu_jalan, waktu_bongkar
    )

    nama_node = [nama_map.get(n, f"Node {n}") for n in rute]
    feasible = muatan <= kapasitas_truk and waktu <= batas_waktu

    return TripDetail(
        trip_ke=trip_idx,
        rute_node=rute,
        nama_node=nama_node,
        jarak_km=round(jarak, 2),
        muatan_sak=muatan,
        kapasitas_sak=kapasitas_truk,
        waktu_menit=round(waktu, 2),
        feasible=feasible,
    )


def bangun_response(
    hasil_alns: Dict[str, Any],
    request_data,
) -> OptimizeResponse:
    """
    Konversi output raw dari jalankan_alns() ke OptimizeResponse Pydantic model.

    Args:
        hasil_alns   : Dict output dari optimizer.jalankan_alns()
        request_data : OptimizeRequest object dari endpoint
    """
    demand = request_data.demand
    matriks = request_data.matriks_jarak
    n_nodes = len(demand)

    nama_map = bangun_nama_node_map(request_data.node_info, n_nodes)

    # Format tiap trip
    trip_details = []
    for idx, rute in enumerate(hasil_alns["rute_terbaik"], start=1):
        trip = format_trip_detail(
            trip_idx=idx,
            rute=rute,
            matriks_jarak=matriks,
            demand=demand,
            kapasitas_truk=request_data.kapasitas_truk,
            batas_waktu=request_data.batas_waktu,
            waktu_jalan=request_data.waktu_jalan,
            waktu_bongkar=request_data.waktu_bongkar,
            nama_map=nama_map,
        )
        trip_details.append(trip)

    iterasi_terbaik = hasil_alns["iterasi_terbaik"]
    pesan = (
        f"Optimasi berhasil. Global best ditemukan pada iterasi ke-{iterasi_terbaik}."
        if iterasi_terbaik > 0
        else "Optimasi berhasil. Solusi awal (Cheapest Insertion) sudah optimal."
    )

    return OptimizeResponse(
        status="success",
        pesan=pesan,
        masa_tanam=request_data.masa_tanam,
        total_node_kios=n_nodes - 1,
        total_demand_sak=sum(demand),
        iterasi_terbaik=iterasi_terbaik,
        total_iterasi_dijalankan=hasil_alns["total_iterasi_dijalankan"],
        total_jarak_km=hasil_alns["z_global_best"],
        total_waktu_menit=hasil_alns["w_global_best"],
        total_muatan_sak=hasil_alns["q_global_best"],
        jumlah_trip=len(trip_details),
        rute_terbaik=trip_details,
        suhu_awal=hasil_alns["suhu_awal"],
        suhu_akhir=hasil_alns["suhu_akhir"],
        alasan_berhenti=hasil_alns["alasan_berhenti"],
    )
