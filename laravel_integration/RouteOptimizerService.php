<?php
/**
 * Contoh Integrasi Laravel → FastAPI Optimizer
 * 
 * File ini menunjukkan cara memanggil FastAPI service dari Laravel.
 * Letakkan di: app/Services/RouteOptimizerService.php
 * 
 * Cara pakai di Controller:
 *   $service = new RouteOptimizerService();
 *   $result  = $service->optimize($masaTanam);
 */

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Exception;

class RouteOptimizerService
{
    /**
     * URL base FastAPI service.
     * Simpan di .env Laravel: OPTIMIZER_API_URL=http://localhost:8001
     */
    private string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = config('services.optimizer.url', 'http://localhost:8001');
    }

    // ─── Public Methods ────────────────────────────────────────────────────────

    /**
     * Jalankan optimasi rute untuk masa tanam tertentu.
     * 
     * @param string $masaTanam  'MT1' | 'MT2' | 'MT3'
     * @param int    $iterasi    Jumlah iterasi ALNS (default: 158)
     * @return array             Response dari FastAPI
     * @throws Exception         Jika request gagal
     */
    public function optimize(string $masaTanam = 'MT1', int $iterasi = 158): array
    {
        $payload = $this->buildPayload($masaTanam, $iterasi);

        Log::info('[Optimizer] Mengirim request optimasi', [
            'masa_tanam' => $masaTanam,
            'iterasi'    => $iterasi,
            'n_kios'     => count($payload['demand']) - 1,
        ]);

        $response = Http::timeout(120)             // timeout 2 menit (ALNS bisa butuh waktu)
            ->retry(2, 1000)                        // retry 2x jika gagal, jeda 1 detik
            ->post("{$this->baseUrl}/api/v1/optimize", $payload);

        if ($response->failed()) {
            $errorBody = $response->json();
            $errorMsg  = $errorBody['detail'] ?? 'Unknown error dari optimizer service';
            Log::error('[Optimizer] Request gagal', ['status' => $response->status(), 'body' => $errorBody]);
            throw new Exception("Optimizer service error: {$errorMsg}", $response->status());
        }

        $result = $response->json();
        Log::info('[Optimizer] Optimasi berhasil', [
            'total_jarak'      => $result['total_jarak_km'],
            'iterasi_terbaik'  => $result['iterasi_terbaik'],
            'jumlah_trip'      => $result['jumlah_trip'],
        ]);

        return $result;
    }

    /**
     * Optimasi dengan log iterasi lengkap (untuk debugging/visualisasi).
     */
    public function optimizeWithLog(string $masaTanam = 'MT1', int $iterasi = 158): array
    {
        $payload  = $this->buildPayload($masaTanam, $iterasi);
        $response = Http::timeout(120)
            ->post("{$this->baseUrl}/api/v1/optimize/with-log", $payload);

        if ($response->failed()) {
            throw new Exception('Optimizer with-log request gagal: ' . $response->body());
        }

        return $response->json();
    }

    /**
     * Cek apakah FastAPI service sedang running.
     */
    public function isHealthy(): bool
    {
        try {
            $response = Http::timeout(5)->get("{$this->baseUrl}/health");
            return $response->ok() && $response->json('status') === 'healthy';
        } catch (Exception) {
            return false;
        }
    }

    // ─── Private Helpers ───────────────────────────────────────────────────────

    /**
     * Build payload JSON untuk dikirim ke FastAPI.
     * 
     * Dalam implementasi nyata, matriks_jarak dan demand diambil dari database MySQL.
     * Demand bisa berubah tiap masa tanam.
     */
    private function buildPayload(string $masaTanam, int $iterasi): array
    {
        // TODO: Ganti dengan query dari database
        // Contoh: $nodes = Node::with('demands')->get();
        //         $demand = $nodes->pluck("demand_{$masaTanam}")->prepend(0)->toArray();

        // ── Matriks Jarak (dari tabel matriks di DB atau hardcode dari Excel) ──
        $matriksJarak = $this->getMatriksJarak();

        // ── Demand sesuai masa tanam ───────────────────────────────────────────
        $demand = $this->getDemand($masaTanam);

        // ── Node info (nama kios + koordinat untuk display di peta) ───────────
        $nodeInfo = $this->getNodeInfo();

        return [
            // Data utama
            'matriks_jarak'  => $matriksJarak,
            'demand'         => $demand,

            // Constraint (bisa disimpan di tabel config DB)
            'kapasitas_truk' => 250,
            'batas_waktu'    => 240.0,
            'waktu_jalan'    => 2.0,
            'waktu_bongkar'  => 0.5,

            // ALNS hyperparameter
            'iterasi_target' => $iterasi,
            'w_toleransi'    => 0.05,
            'alpha'          => 0.95,
            'rho'            => 0.1,
            'destroy_ratio'  => 0.30,
            'skor_pi'        => [33, 9, 13, 0],

            // Metadata
            'masa_tanam'     => $masaTanam,
            'node_info'      => $nodeInfo,
        ];
    }

    /**
     * Ambil matriks jarak.
     * Dalam produksi: query dari tabel `matriks_jarak` di MySQL.
     */
    private function getMatriksJarak(): array
    {
        // TODO: return DB::table('matriks_jarak')->...->toArray()
        return [
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
        ];
    }

    /**
     * Ambil demand sesuai masa tanam.
     * Dalam produksi: query dari tabel `demands` di MySQL berdasarkan masa_tanam.
     */
    private function getDemand(string $masaTanam): array
    {
        // TODO: return Demand::where('masa_tanam', $masaTanam)->orderBy('node_id')->pluck('jumlah')->prepend(0)->toArray()
        $demandData = [
            'MT1' => [0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59],  // UREA MT1
            'MT2' => [0, 171, 77, 98, 84, 123, 86, 101, 110, 69, 106, 88, 59],  // UREA MT2 (sama)
            'MT3' => [0, 155, 23, 198, 10, 292, 12, 341, 73, 43, 113, 36, 74],  // UREA MT3
        ];

        return $demandData[$masaTanam] ?? $demandData['MT1'];
    }

    /**
     * Ambil informasi node (nama + koordinat).
     * Dalam produksi: query dari tabel `nodes` di MySQL.
     */
    private function getNodeInfo(): array
    {
        // TODO: return Node::all()->map(fn($n) => ['node_id' => $n->id, 'nama' => $n->nama, ...])->toArray()
        return [
            ['node_id' => 0,  'nama' => 'Gudang',              'latitude' => -7.664482, 'longitude' => 111.201067],
            ['node_id' => 1,  'nama' => 'Brahman Maju',         'latitude' => -7.673204, 'longitude' => 111.201399],
            ['node_id' => 2,  'nama' => 'Sumber Makmur',        'latitude' => -7.684752, 'longitude' => 111.201509],
            ['node_id' => 3,  'nama' => 'Gading Makmur',        'latitude' => -7.659649, 'longitude' => 111.200538],
            ['node_id' => 4,  'nama' => 'Margo Rukun',          'latitude' => -7.678135, 'longitude' => 111.202285],
            ['node_id' => 5,  'nama' => 'Margo Rukun Abadi',    'latitude' => -7.675488, 'longitude' => 111.203398],
            ['node_id' => 6,  'nama' => 'Margo Rukun Barokah',  'latitude' => -7.681612, 'longitude' => 111.120244],
            ['node_id' => 7,  'nama' => 'Krida Tani 1',         'latitude' => -7.663758, 'longitude' => 111.119909],
            ['node_id' => 8,  'nama' => 'Krida Tani 2',         'latitude' => -7.663058, 'longitude' => 111.200173],
            ['node_id' => 9,  'nama' => 'Karya Makmur',         'latitude' => -7.662627, 'longitude' => 111.201903],
            ['node_id' => 10, 'nama' => 'Tani Makmur',          'latitude' => -7.649686, 'longitude' => 111.201824],
            ['node_id' => 11, 'nama' => 'Tani Makmur Abadi',    'latitude' => -7.658894, 'longitude' => 111.202158],
            ['node_id' => 12, 'nama' => 'Pinang Jaya',          'latitude' => -7.646107, 'longitude' => 111.200528],
        ];
    }
}
