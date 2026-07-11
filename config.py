"""
config.py — Bot Marica — PRONTO, NAO MEXA
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

LOGIN = os.getenv("MARICA_LOGIN", "")
SENHA = os.getenv("MARICA_SENHA", "")
CONVENIO_ALVO = "Prefeitura de Marica"

TELEGRAM_TOKEN = os.getenv("MARICA_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("MARICA_TELEGRAM_CHAT_ID", "")

ANTICAPTCHA_KEY = os.getenv("ANTICAPTCHA_KEY", "")

INTERVALO_SEGUNDOS = 5