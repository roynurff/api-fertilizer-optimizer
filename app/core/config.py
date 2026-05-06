"""
Application configuration — edit .env or environment variables to override.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API
    APP_NAME: str = "Fertilizer Route Optimizer"
    DEBUG: bool = False

    # CORS — tambahkan URL Laravel production kamu di sini
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",   # Laravel dev default
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "*",                       # Ganti ke URL spesifik saat production!
    ]

    # ALNS default parameters (bisa di-override lewat request body)
    DEFAULT_ITERASI: int = 158
    DEFAULT_KAPASITAS_TRUK: int = 250        # sak
    DEFAULT_BATAS_WAKTU: float = 240.0       # menit
    DEFAULT_WAKTU_JALAN: float = 2.0         # menit per km
    DEFAULT_WAKTU_BONGKAR: float = 0.5       # menit per sak
    DEFAULT_W_TOLERANSI: float = 0.05
    DEFAULT_ALPHA: float = 0.95
    DEFAULT_RHO: float = 0.1
    DEFAULT_SKOR_PI: List[int] = [33, 9, 13, 0]
    DEFAULT_DESTROY_RATIO: float = 0.30      # 30% dari total node

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
