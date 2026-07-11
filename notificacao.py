"""
notificacao.py — Sistema de notificações em 3 estágios
  Estágio 1: VAGA ENCONTRADA
  Estágio 2: SE INSCREVENDO
  Estágio 3: INSCRIÇÃO CONFIRMADA

  Suporta múltiplos bots com tokens Telegram diferentes.
  Passa token e chat_id como parâmetros para cada chamada.
"""

import sys
import requests


# ─────────────────────────────────────────────────────────────
#  HELPERS INTERNOS
# ─────────────────────────────────────────────────────────────

def _beep(vezes: int = 3, freq: int = 1000, dur: int = 400):
    if sys.platform == "win32":
        try:
            import winsound
            for _ in range(vezes):
                winsound.Beep(freq, dur)
        except Exception:
            pass


def _notificacao_windows(titulo: str, mensagem: str, timeout: int = 30):
    try:
        from plyer import notification
        notification.notify(
            title=titulo,
            message=mensagem,
            app_name="PROEISBM Bot",
            timeout=timeout
        )
    except Exception as e:
        print(f"[NOTIFICAÇÃO WINDOWS] Erro: {e}")


def _notificacao_telegram(mensagem: str, token: str = "", chat_id: str = ""):
    """Envia mensagem para o Telegram usando o token e chat_id informados."""
    # Se não foram passados, tenta ler do config padrão
    if not token or not chat_id:
        try:
            from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
            token   = token   or TELEGRAM_TOKEN
            chat_id = chat_id or TELEGRAM_CHAT_ID
        except Exception:
            pass

    if not token or not chat_id:
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(
            url,
            data={"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"[TELEGRAM] Erro: {e}")


# ─────────────────────────────────────────────────────────────
#  ESTÁGIO 1 — VAGA ENCONTRADA
# ─────────────────────────────────────────────────────────────

def notificar_vaga_encontrada(convenio: str, token: str = "", chat_id: str = ""):
    titulo   = "🚨 VAGA ENCONTRADA!"
    mensagem = f"Vaga disponível para {convenio}!\nRobô iniciando inscrição agora..."
    telegram = f"🚨 *VAGA ENCONTRADA!*\nConvênio: {convenio}\nRobô iniciando inscrição agora..."

    print(f"\n{'='*55}")
    print(f"  🚨  VAGA ENCONTRADA — {convenio}")
    print(f"{'='*55}\n")

    _beep(vezes=5, freq=1200, dur=300)
    _notificacao_windows(titulo, mensagem, timeout=60)
    _notificacao_telegram(telegram, token, chat_id)


# ─────────────────────────────────────────────────────────────
#  ESTÁGIO 2 — SE INSCREVENDO
# ─────────────────────────────────────────────────────────────

def notificar_inscrevendo(convenio: str, token: str = "", chat_id: str = ""):
    titulo   = "⏳ Se inscrevendo..."
    mensagem = f"Robô realizando inscrição em {convenio}.\nAguarde a confirmação!"
    telegram = f"⏳ *Se inscrevendo...*\nConvênio: {convenio}\nAguarde a confirmação!"

    print(f"\n{'='*55}")
    print(f"  ⏳  SE INSCREVENDO — {convenio}")
    print(f"{'='*55}\n")

    _beep(vezes=2, freq=800, dur=200)
    _notificacao_windows(titulo, mensagem, timeout=30)
    _notificacao_telegram(telegram, token, chat_id)


# ─────────────────────────────────────────────────────────────
#  ESTÁGIO 3 — INSCRIÇÃO CONFIRMADA
# ─────────────────────────────────────────────────────────────

def notificar_inscricao_confirmada(convenio: str, token: str = "", chat_id: str = ""):
    titulo   = "✅ INSCRIÇÃO CONFIRMADA!"
    mensagem = f"Inscrição em {convenio} realizada com sucesso!\nVerifique o sistema PROEISBM."
    telegram = f"✅ *INSCRIÇÃO CONFIRMADA!*\nConvênio: {convenio}\nInscrição realizada com sucesso!\nVerifique o sistema PROEISBM."

    print(f"\n{'='*55}")
    print(f"  ✅  INSCRIÇÃO CONFIRMADA — {convenio}")
    print(f"{'='*55}\n")

    _beep(vezes=3, freq=1500, dur=500)
    _notificacao_windows(titulo, mensagem, timeout=120)
    _notificacao_telegram(telegram, token, chat_id)


# ─────────────────────────────────────────────────────────────
#  NOTIFICAÇÃO GENÉRICA (compatibilidade)
# ─────────────────────────────────────────────────────────────

def notificar(mensagem: str, token: str = "", chat_id: str = ""):
    print(f"\n{'='*55}")
    print(f"  📢  {mensagem}")
    print(f"{'='*55}\n")
    _beep(vezes=3)
    _notificacao_windows("🤖 BOT PROEISBM", mensagem)
    _notificacao_telegram(f"🤖 BOT PROEISBM\n{mensagem}", token, chat_id)
