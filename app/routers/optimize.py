"""
Router: /api/v1/optimize
Endpoint utama yang menerima request dari Laravel dan menjalankan ALNS.
"""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.schemas import OptimizeRequest, OptimizeResponse, ErrorResponse
from app.services.optimizer import jalankan_alns
from app.services.utils import bangun_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Jalankan Optimasi Rute Distribusi Pupuk",
    description="""
Menjalankan algoritma **CVRPTW + ALNS** untuk menemukan rute distribusi pupuk yang optimal.

### Flow:
1. Validasi request (matriks, demand, parameter)
2. Bangun solusi awal dengan Cheapest Insertion Heuristic
3. Jalankan loop ALNS (Destroy + Repair + Simulated Annealing)
4. Kembalikan **global best solution** (tidak harus iterasi terakhir)

### Constraints:
- **Kapasitas**: Total muatan per trip ≤ `kapasitas_truk` sak
- **Waktu**: `(jarak × waktu_jalan) + (muatan × waktu_bongkar)` ≤ `batas_waktu` menit
    """,
    responses={
        200: {"description": "Optimasi berhasil", "model": OptimizeResponse},
        400: {"description": "Request tidak valid", "model": ErrorResponse},
        422: {"description": "Validasi Pydantic gagal"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
)
async def optimize_route(request: OptimizeRequest) -> OptimizeResponse:
    """
    Endpoint POST /api/v1/optimize

    Menerima parameter optimasi dari Laravel dan mengembalikan rute terbaik dalam JSON.
    """
    # ── Cross-field validation ─────────────────────────────────────────────────
    try:
        request.validate_consistency()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    logger.info(
        f"[OPTIMIZE] Request diterima — "
        f"n_nodes={len(request.demand)}, "
        f"iterasi={request.iterasi_target}, "
        f"masa_tanam={request.masa_tanam}"
    )

    # ── Jalankan ALNS ─────────────────────────────────────────────────────────
    try:
        hasil = jalankan_alns(
            matriks_jarak=request.matriks_jarak,
            demand=request.demand,
            kapasitas_truk=request.kapasitas_truk,
            batas_waktu=request.batas_waktu,
            waktu_jalan=request.waktu_jalan,
            waktu_bongkar=request.waktu_bongkar,
            iterasi_target=request.iterasi_target,
            w_toleransi=request.w_toleransi,
            alpha=request.alpha,
            rho=request.rho,
            destroy_ratio=request.destroy_ratio,
            skor_pi=request.skor_pi,
        )
    except Exception as e:
        logger.error(f"[OPTIMIZE] Error saat menjalankan ALNS: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat menjalankan optimasi: {str(e)}",
        )

    # ── Format response ───────────────────────────────────────────────────────
    response = bangun_response(hasil, request)

    logger.info(
        f"[OPTIMIZE] Selesai — "
        f"global_best={hasil['z_global_best']} km, "
        f"iterasi_terbaik={hasil['iterasi_terbaik']}, "
        f"durasi={hasil['durasi_komputasi_detik']}s"
    )

    return response


@router.post(
    "/optimize/with-log",
    summary="Optimasi + Log Iterasi Lengkap",
    description="Sama seperti /optimize, tetapi response juga menyertakan log tiap iterasi. "
                "Berguna untuk debugging dan visualisasi konvergensi.",
    status_code=status.HTTP_200_OK,
)
async def optimize_route_with_log(request: OptimizeRequest):
    """
    Endpoint dengan log iterasi lengkap.
    Gunakan hanya untuk keperluan analisis/debugging — response lebih besar.
    """
    try:
        request.validate_consistency()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        hasil = jalankan_alns(
            matriks_jarak=request.matriks_jarak,
            demand=request.demand,
            kapasitas_truk=request.kapasitas_truk,
            batas_waktu=request.batas_waktu,
            waktu_jalan=request.waktu_jalan,
            waktu_bongkar=request.waktu_bongkar,
            iterasi_target=request.iterasi_target,
            w_toleransi=request.w_toleransi,
            alpha=request.alpha,
            rho=request.rho,
            destroy_ratio=request.destroy_ratio,
            skor_pi=request.skor_pi,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    response = bangun_response(hasil, request)

    # Tambahkan log iterasi ke response
    return {
        **response.model_dump(),
        "log_iterasi": hasil["log_iterasi"],
        "durasi_komputasi_detik": hasil["durasi_komputasi_detik"],
        "n_destroy_per_iterasi": hasil["n_destroy"],
        "z_awal": hasil["z_awal"],
    }
