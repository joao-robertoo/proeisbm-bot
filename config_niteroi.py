"""
config_niteroi.py — Bot Niteroi — PRONTO, NAO MEXA
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=ENV_PATH)
    except Exception:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if sep:
                os.environ.setdefault(key.strip(), value.strip())

LOGIN = os.getenv("NITEROI_LOGIN", "")
SENHA = os.getenv("NITEROI_SENHA", "")
CONVENIO_ALVO = "Prefeitura de Niteroi"

TELEGRAM_TOKEN = os.getenv("NITEROI_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("NITEROI_TELEGRAM_CHAT_ID", "")

ANTICAPTCHA_KEY = os.getenv("ANTICAPTCHA_KEY", "")

INTERVALO_SEGUNDOS = 5