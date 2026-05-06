<?php
/**
 * Contoh Controller Laravel untuk memanggil optimizer.
 * Letakkan di: app/Http/Controllers/OptimizerController.php
 */

namespace App\Http\Controllers;

use App\Services\RouteOptimizerService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Exception;

class OptimizerController extends Controller
{
    public function __construct(private RouteOptimizerService $optimizer) {}

    /**
     * POST /optimize
     * Terima input dari form Laravel, kirim ke FastAPI, simpan dan return hasil.
     */
    public function optimize(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'masa_tanam' => 'required|in:MT1,MT2,MT3',
            'iterasi'    => 'nullable|integer|min:10|max:10000',
        ]);

        // Cek dulu apakah service Python aktif
        if (!$this->optimizer->isHealthy()) {
            return response()->json([
                'success' => false,
                'message' => 'Optimizer service tidak tersedia. Pastikan FastAPI sudah berjalan.',
            ], 503);
        }

        try {
            $result = $this->optimizer->optimize(
                masaTanam: $validated['masa_tanam'],
                iterasi: $validated['iterasi'] ?? 158,
            );

            // TODO: Simpan hasil ke database jika perlu
            // OptimizationResult::create([...])

            return response()->json([
                'success' => true,
                'data'    => $result,
            ]);

        } catch (Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * GET /optimize/health
     * Cek status FastAPI service dari Laravel.
     */
    public function healthCheck(): JsonResponse
    {
        return response()->json([
            'optimizer_online' => $this->optimizer->isHealthy(),
        ]);
    }
}
