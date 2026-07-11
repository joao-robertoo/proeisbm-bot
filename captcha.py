"""
captcha.py — Anti-Captcha API

Correcoes:
  • case=True  → captcha do PROEISBM E case-sensitive
  • numeric=0  → pode ter letras e numeros misturados
  • Timeout reduzido para 60s (captchas simples resolvem em 5-15s)
  • ANTICAPTCHA_KEY lida diretamente do .env — sem depender de config.py especifico
  • NOVO: alerta Telegram quando saldo estiver baixo (< U$0.50) ou zerado
  • NOVO: quando saldo zera, envia mensagem no Telegram e levanta excecao
    para o bot parar o loop em vez de travar silenciosamente
"""

import os
import sys
import time
import base64
import io
from pathlib import Path
import requests
from PIL import Image

API_URL_CREATE = "https://api.anti-captcha.com/createTask"
API_URL_RESULT = "https://api.anti-captcha.com/getTaskResult"
MAX_ESPERA_SEG = 60
INTERVALO_POLL = 2

# Limite de saldo para disparar aviso (em dolares)
SALDO_ALERTA_BAIXO = 0.50

# Controle interno para nao enviar o mesmo aviso repetidamente
_alerta_baixo_enviado   = False
_alerta_zerado_enviado  = False


def _get_base_dir() -> Path:
    """Mesma logica dos configs — funciona tanto em .py quanto em .exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _ler_anticaptcha_key() -> str:
    """Le a ANTICAPTCHA_KEY diretamente do .env, sem importar config.py."""
    env_path = _get_base_dir() / ".env"
    if not env_path.exists():
        return os.environ.get("ANTICAPTCHA_KEY", "")
    try:
        with open(env_path, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha.startswith("ANTICAPTCHA_KEY="):
                    return linha.partition("=")[2].strip()
    except Exception:
        pass
    return os.environ.get("ANTICAPTCHA_KEY", "")


def _ler_tokens_telegram() -> list:
    """
    Le todos os pares TELEGRAM_TOKEN / TELEGRAM_CHAT_ID do .env.
    Retorna lista de tuplas [(token, chat_id), ...] para notificar
    tanto o bot Marica quanto o Niteroi.
    """
    env_path = _get_base_dir() / ".env"
    tokens = {}
    chats  = {}
    if env_path.exists():
        try:
            with open(env_path, encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha or linha.startswith("#"):
                        continue
                    if "TELEGRAM_TOKEN=" in linha:
                        chave, _, valor = linha.partition("=")
                        tokens[chave.strip()] = valor.strip()
                    if "TELEGRAM_CHAT_ID=" in linha:
                        chave, _, valor = linha.partition("=")
                        chats[chave.strip()] = valor.strip()
        except Exception:
            pass

    pares = []
    # Marica
    t = tokens.get("MARICA_TELEGRAM_TOKEN", "")
    c = chats.get("MARICA_TELEGRAM_CHAT_ID", "")
    if t and c:
        pares.append((t, c))
    # Niteroi
    t = tokens.get("NITEROI_TELEGRAM_TOKEN", "")
    c = chats.get("NITEROI_TELEGRAM_CHAT_ID", "")
    if t and c:
        pares.append((t, c))
    return pares


def _enviar_telegram(mensagem: str):
    """Envia mensagem para todos os chats configurados no .env."""
    for token, chat_id in _ler_tokens_telegram():
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(
                url,
                data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"},
                timeout=10
            )
        except Exception:
            pass


try:
    from config import ANTICAPTCHA_KEY as _KEY_CONFIG
except Exception:
    _KEY_CONFIG = ""
ANTICAPTCHA_KEY = _ler_anticaptcha_key() or _KEY_CONFIG


def _imagem_para_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    w, h = img.size
    img_grande = img.resize((w * 2, h * 2), Image.LANCZOS)
    img_grande.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def resolver_via_anticaptcha(img: Image.Image) -> str:
    """
    Envia a imagem para Anti-Captcha API.
    Retorna o texto resolvido ou '' em caso de falha.
    Levanta SaldoInsuficienteError se o saldo estiver zerado.
    """
    global _alerta_baixo_enviado, _alerta_zerado_enviado

    key = ANTICAPTCHA_KEY or _ler_anticaptcha_key()
    if not key:
        return ""

    img_b64 = _imagem_para_base64(img)

    payload_criar = {
        "clientKey": key,
        "task": {
            "type": "ImageToTextTask",
            "body": img_b64,
            "phrase": False,
            "case": True,
            "numeric": 0,
            "math": False,
            "minLength": 4,
            "maxLength": 6,
            "comment": "Captcha alfanumerico do sistema PROEISBM, case-sensitive"
        },
        "softId": 0
    }

    try:
        resp  = requests.post(API_URL_CREATE, json=payload_criar, timeout=15)
        dados = resp.json()
    except Exception:
        return ""

    # Erro de saldo insuficiente — codigo 10 da Anti-Captcha API
    erro_id  = dados.get("errorId", 0)
    erro_cod = dados.get("errorCode", "")

    if erro_id != 0:
        if erro_cod in ("ERROR_ZERO_BALANCE", "ERROR_NO_SLOT_AVAILABLE") or erro_id == 10:
            if not _alerta_zerado_enviado:
                _alerta_zerado_enviado = True
                _enviar_telegram(
                    "🚨 *ANTI-CAPTCHA SEM SALDO!*\n"
                    "O robô PAROU de funcionar.\n"
                    "Recarregue os créditos em anti-captcha.com e reinicie o bot."
                )
            raise SaldoInsuficienteError("Saldo Anti-Captcha zerado — bot pausado.")
        return ""

    if "taskId" not in dados:
        return ""

    task_id = dados["taskId"]
    payload_resultado = {"clientKey": key, "taskId": task_id}

    inicio = time.time()
    while time.time() - inicio < MAX_ESPERA_SEG:
        time.sleep(INTERVALO_POLL)
        try:
            resp      = requests.post(API_URL_RESULT, json=payload_resultado, timeout=15)
            resultado = resp.json()
        except Exception:
            continue

        if resultado.get("errorId", 1) != 0:
            return ""

        if resultado.get("status") == "ready":
            texto = resultado.get("solution", {}).get("text", "").strip()
            return ''.join(c for c in texto if c.isalnum())

    return ""


def verificar_saldo() -> float:
    """
    Retorna o saldo de creditos da Anti-Captcha.
    Envia alerta no Telegram se saldo estiver baixo ou zerado.
    """
    global _alerta_baixo_enviado, _alerta_zerado_enviado

    key = ANTICAPTCHA_KEY or _ler_anticaptcha_key()
    if not key:
        return 0.0
    try:
        resp  = requests.post(
            "https://api.anti-captcha.com/getBalance",
            json={"clientKey": key},
            timeout=10
        )
        dados = resp.json()
        if dados.get("errorId", 1) == 0:
            saldo = float(dados.get("balance", 0))

            if saldo <= 0.0 and not _alerta_zerado_enviado:
                _alerta_zerado_enviado = True
                _enviar_telegram(
                    "🚨 *ANTI-CAPTCHA SEM SALDO!*\n"
                    "O robô PAROU de funcionar.\n"
                    "Recarregue os créditos em anti-captcha.com e reinicie o bot."
                )
            elif 0.0 < saldo < SALDO_ALERTA_BAIXO and not _alerta_baixo_enviado:
                _alerta_baixo_enviado = True
                _enviar_telegram(
                    f"⚠️ *SALDO ANTI-CAPTCHA BAIXO!*\n"
                    f"Saldo atual: U${saldo:.4f}\n"
                    f"Recarregue em breve para o robô não parar."
                )
            elif saldo >= SALDO_ALERTA_BAIXO:
                # Reseta os alertas se o saldo for recarregado
                _alerta_baixo_enviado  = False
                _alerta_zerado_enviado = False

            return saldo
    except Exception:
        pass
    return 0.0


# ─────────────────────────────────────────────────────────────
#  Excecao customizada — capturada no loop principal do bot
# ─────────────────────────────────────────────────────────────

class SaldoInsuficienteError(Exception):
    """Levantada quando a Anti-Captcha retorna erro de saldo zerado."""
    pass