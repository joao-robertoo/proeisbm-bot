"""
BOT PROEISBM v7.1 Elite — Niteroi
Motor: Anti-Captcha API (~99% precisao)

CORRECOES v7.1:
  • Captcha vazio agora contabiliza em captchas_errados (fix do painel)
  • Credenciais hardcoded — sem .env, sem arquivo externo
  • Intervalo reduzido para 5s
  • Telegram notifica os 3 estagios inclusive quando vaga e negada
  • Sessao Chrome limpa a cada reinicio (sem cache de login antigo)
"""

import time
import logging
import os
import sys
import shutil
import base64
import io
import gc
from datetime import datetime, timedelta
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    InvalidSessionIdException,
    WebDriverException,
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

from config_niteroi import LOGIN, SENHA, INTERVALO_SEGUNDOS, CONVENIO_ALVO, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from notificacao import (
    notificar_vaga_encontrada,
    notificar_inscrevendo,
    notificar_inscricao_confirmada,
    notificar,
)
from captcha import resolver_via_anticaptcha, verificar_saldo, SaldoInsuficienteError

BOT_ID     = "niteroi"
PERFIL_DIR = f"chrome-profile-{BOT_ID}"

console = Console()

os.makedirs("logs", exist_ok=True)
os.makedirs("captchas", exist_ok=True)
log_arquivo = f"logs/bot_{BOT_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_arquivo, encoding="utf-8")]
)
log = logging.getLogger(__name__)

URL_BASE     = "http://www.proeisbm.cbmerj.rj.gov.br/"
URL_SERVICOS = "http://www.proeisbm.cbmerj.rj.gov.br/index.php?option=com_servicos_vagos&Itemid=155"

SELETORES_SOLICITAR = [
    "//input[@type='submit'][contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ','abcdefghijklmnopqrstuvwxyzaeiouaoaeiouaeiouaeiou'),'solicitar')]",
    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ','abcdefghijklmnopqrstuvwxyzaeiouaoaeiouaeiouaeiou'),'solicitar')]",
    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÇ','abcdefghijklmnopqrstuvwxyzaeiouaoaeiouaeiouaeiou'),'solicitar')]",
    "//input[@type='submit'][contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'assumir')]",
    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'assumir')]",
    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'assumir')]",
    "//input[@type='submit'][contains(translate(@value,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'inscrever')]",
    "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'inscrever')]",
    "//input[@value='SOLICITAR SERVICO']",
    "//input[@value='SOLICITAR SERVIÇO']",
    "//input[contains(@value,'SOLICITAR')]",
    "//input[contains(@value,'ASSUMIR')]",
]

PALAVRAS_SEM_VAGA = [
    "nenhuma desistencia",
    "nenhum servico",
    "nenhum serviço",
    "sem vagas",
    "nao ha vagas",
    "não há vagas",
    "nao existem servicos",
    "não existem serviços",
    "nao ha servicos disponiveis",
    "não há serviços disponíveis",
]

PALAVRAS_SUCESSO = [
    "sucesso", "registrado", "confirmad", "inscrito",
    "realizada", "efetuada", "solicitacao", "solicitação",
    "assumir", "servico disponivel", "serviço disponível",
    "incluido", "incluído", "seu pedido", "cadastrado",
]

PALAVRAS_NEGADO = [
    "nao foi possivel", "não foi possível",
    "nao e possivel", "não é possível",
    "coincide", "restrito", "nao autorizado",
    "não autorizado", "acesso negado",
]

stats = {
    "tentativas": 0,
    "captchas_errados": 0,
    "captchas_certos": 0,
    "captchas_vazios": 0,
    "sem_vaga": 0,
    "inicio": datetime.now(),
    "status": "Iniciando...",
    "ultimo_captcha": "-",
    "logins_ok": 0,
    "saldo_api": 0.0,
}


# ─────────────────────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────────────────────

def banner():
    console.print()
    console.print(Panel.fit(
        Align.center(Text.from_markup(
            "[bold blue]BOT PROEISBM v7.1 ELITE[/]\n"
            "[dim]Automacao de Monitoramento de Vagas[/]\n"
            f"[cyan]Convenio: {CONVENIO_ALVO}[/]\n"
            "[dim]Anti-Captcha API · Inscricao Automatica · Popup OK[/]"
        )),
        border_style="blue", box=box.DOUBLE, padding=(1, 4),
    ))
    console.print()


def painel_status():
    decorrido = str(timedelta(seconds=int((datetime.now() - stats["inicio"]).total_seconds())))
    table = Table(box=box.ROUNDED, border_style="cyan", show_header=False, padding=(0, 2))
    table.add_column("", style="bold yellow", width=24)
    table.add_column("", style="white", width=36)
    table.add_row("Tempo rodando",     f"[bold green]{decorrido}[/]")
    table.add_row("Tentativas",        f"[bold white]{stats['tentativas']}[/]")
    table.add_row("Sem vaga",          f"[bold blue]{stats['sem_vaga']}[/]")
    table.add_row("Captchas corretos", f"[bold green]{stats['captchas_certos']}[/]")
    table.add_row("Captchas errados",  f"[bold red]{stats['captchas_errados']}[/]")
    table.add_row("Captchas vazios",   f"[bold magenta]{stats['captchas_vazios']}[/]")
    table.add_row("Logins OK",         f"[bold cyan]{stats['logins_ok']}[/]")
    table.add_row("Ultimo captcha",    f"[bold magenta]{stats['ultimo_captcha']}[/]")
    table.add_row("Motor",             f"[bold green]Anti-Captcha API[/]")
    table.add_row("Saldo API",         f"[bold green]U${stats['saldo_api']:.4f}[/]")
    table.add_row("Status",            f"[bold yellow]{stats['status']}[/]")
    return Panel(table, title=f"[bold blue]PROEISBM MONITOR — {CONVENIO_ALVO}[/]", border_style="blue", box=box.HEAVY)


def log_info(msg): log.info(msg);    console.print(f"  [cyan]>[/] [white]{msg}[/]")
def log_ok(msg):   log.info(msg);    console.print(f"  [bold green]OK[/] [green]{msg}[/]")
def log_warn(msg): log.warning(msg); console.print(f"  [bold yellow]![/] [yellow]{msg}[/]")
def log_erro(msg): log.error(msg);   console.print(f"  [bold red]X[/] [red]{msg}[/]")


# ─────────────────────────────────────────────────────────────
#  HELPER — aceita qualquer alert/confirm aberto
# ─────────────────────────────────────────────────────────────

def _aceitar_alert_se_presente(driver, timeout: int = 5) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        texto_alert = alert.text
        alert.accept()
        log_ok(f"Popup aceito: '{texto_alert}'")
        return True
    except NoAlertPresentException:
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
#  CHROME
# ─────────────────────────────────────────────────────────────

def _limpar_perfil_chrome():
    """
    Remove o perfil Chrome salvo em disco.
    Garante que nenhuma sessao antiga persiste apos reinicio.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    perfil = os.path.join(base, f"chrome-profile-{BOT_ID}")
    if os.path.exists(perfil):
        try:
            shutil.rmtree(perfil)
            log_info("Perfil Chrome anterior removido — sessao limpa")
        except Exception as e:
            log_warn(f"Nao foi possivel remover perfil Chrome: {e}")

def _detectar_versao_chrome() -> int:
    """Le a versao major do Chrome instalado na maquina. Retorna int (ex: 147)."""
    import winreg, subprocess, re

    # Tentativa 1 — registro do Windows (mais confiavel)
    caminhos_reg = [
        r"SOFTWARE\Google\Chrome\BLBeacon",
        r"SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
    ]
    for caminho in caminhos_reg:
        try:
            chave = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, caminho)
            versao, _ = winreg.QueryValueEx(chave, "version")
            major = int(versao.split(".")[0])
            if major > 80:
                log_info(f"Chrome detectado via registro: versao {major}")
                return major
        except Exception:
            pass
        try:
            chave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, caminho)
            versao, _ = winreg.QueryValueEx(chave, "version")
            major = int(versao.split(".")[0])
            if major > 80:
                log_info(f"Chrome detectado via registro (user): versao {major}")
                return major
        except Exception:
            pass

    # Tentativa 2 — executar chrome --version
    caminhos_exe = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
    ]
    for exe in caminhos_exe:
        if os.path.exists(exe):
            try:
                saida = subprocess.check_output([exe, "--version"], timeout=5,
                                                 creationflags=0x08000000).decode()
                match = re.search(r"(\d+)\.", saida)
                if match:
                    major = int(match.group(1))
                    log_info(f"Chrome detectado via exe: versao {major}")
                    return major
            except Exception:
                pass

    # Fallback — deixa UC tentar sozinho
    log_warn("Nao foi possivel detectar versao do Chrome — UC vai tentar automaticamente")
    return None


def criar_driver():
    stats["status"] = "Iniciando Chrome..."
    import undetected_chromedriver as uc

    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    # ── Detecta versao real do Chrome ──
    versao_chrome = _detectar_versao_chrome()

    opcoes = uc.ChromeOptions()
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--disable-blink-features=AutomationControlled")
    opcoes.add_argument("--window-size=1920,1080")
    opcoes.add_argument(f"--user-data-dir={os.path.join(base, f'chrome-profile-{BOT_ID}')}")

    # ── Limpa cache UC corrompido (WinError 183) ──
    uc_cache = os.path.join(os.environ.get("APPDATA", ""), "undetected_chromedriver")
    if os.path.exists(uc_cache):
        try:
            shutil.rmtree(uc_cache)
            log_info("Cache UC removido — baixando versao correta...")
        except Exception:
            pass

    driver = uc.Chrome(
        options=opcoes,
        version_main=versao_chrome,   # None = UC tenta sozinho como fallback
        use_subprocess=True,
    )

    driver.implicitly_wait(2)
    return driver

def criar_driver_com_retry(tentativas: int = 5) -> object:
    for i in range(1, tentativas + 1):
        try:
            return criar_driver()
        except Exception as e:
            log_warn(f"Chrome nao iniciou (tentativa {i}/{tentativas}): {e}")
            if i < tentativas:
                espera = 10 * i
                log_info(f"Aguardando {espera}s antes de tentar novamente...")
                time.sleep(espera)
    log_warn("Matando processos Chrome presos...")
    try:
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
        os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
    except Exception:
        pass
    time.sleep(5)
    return criar_driver()


def driver_ativo(driver) -> bool:
    try:
        _ = driver.title
        return True
    except Exception:
        return False


def encerrar_driver(driver):
    try:
        driver.service.stop()
    except Exception:
        pass
    try:
        driver.quit()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
#  CAPTCHA
# ─────────────────────────────────────────────────────────────

def _capturar_imagem_captcha(driver) -> Image.Image:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//img[contains(@src,'captcha')]"))
    )
    time.sleep(0.3)

    try:
        img_b64 = driver.execute_script("""
            var img = document.querySelector('img[src*="captcha"]');
            if (!img || !img.complete || img.naturalWidth === 0) return null;
            var c = document.createElement('canvas');
            c.width  = img.naturalWidth  || img.width  || 150;
            c.height = img.naturalHeight || img.height || 50;
            c.getContext('2d').drawImage(img, 0, 0);
            return c.toDataURL('image/png').split(',')[1];
        """)
        if img_b64 and len(img_b64) > 300:
            log_info("Captcha capturado via canvas JS")
            return Image.open(io.BytesIO(base64.b64decode(img_b64)))
    except Exception as e:
        log_warn(f"Canvas falhou: {e}")

    try:
        img_el = driver.find_element(By.XPATH, "//img[contains(@src,'captcha')]")
        loc  = img_el.location_once_scrolled_into_view
        size = img_el.size
        png  = driver.get_screenshot_as_png()
        pg   = Image.open(io.BytesIO(png))
        ex   = pg.width  / driver.execute_script("return window.innerWidth")
        ey   = pg.height / driver.execute_script("return window.innerHeight")
        x1   = max(0, int(loc['x'] * ex) - 4)
        y1   = max(0, int(loc['y'] * ey) - 4)
        x2   = x1 + int(size['width']  * ex) + 8
        y2   = y1 + int(size['height'] * ey) + 8
        log_info("Captcha capturado via recorte")
        return pg.crop((x1, y1, x2, y2))
    except Exception as e:
        log_warn(f"Recorte falhou: {e}")

    raise Exception("Todos os metodos de captura falharam")


def resolver_captcha(driver) -> str:
    try:
        img_orig = _capturar_imagem_captcha(driver)
        ts = datetime.now().strftime("%H%M%S_%f")
        img_orig.save(f"captchas/cap_{BOT_ID}_{ts}.png")
    except Exception as e:
        log_erro(f"Captura do captcha falhou: {e}")
        return ""

    log_info("Enviando para Anti-Captcha API...")
    try:
        texto = resolver_via_anticaptcha(img_orig)
        if texto and 3 <= len(texto) <= 8:
            stats["ultimo_captcha"] = texto
            log_ok(f"Anti-Captcha resolveu: [bold green]{texto}[/]")
            return texto
        log_warn(f"Anti-Captcha retornou invalido: '{texto}'")
    except Exception as e:
        log_erro(f"Anti-Captcha falhou: {e}")

    return ""


def _preencher_captcha(driver, texto: str):
    try:
        driver.execute_script(f"document.getElementsByName('cd')[0].value = '{texto}';")
        return
    except Exception:
        pass
    try:
        campo = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='cd']"))
        )
        campo.clear()
        campo.send_keys(texto)
    except Exception as e:
        log_warn(f"Nao conseguiu preencher campo captcha: {e}")


# ─────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────

def fazer_login(driver) -> bool:
    stats["status"] = "Fazendo login..."
    log_info("Acessando PROEISBM...")
    driver.get(URL_BASE)

    wait = WebDriverWait(driver, 15)
    try:
        campo_rg = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']")))
        campo_rg.clear()
        campo_rg.send_keys(LOGIN)
        driver.find_element(By.XPATH, "//input[@name='passwd']").send_keys(SENHA)
        log_info("RG e senha preenchidos")
    except WebDriverException:
        raise
    except Exception as e:
        log_erro(f"Campos de login nao encontrados: {e}")
        return False

    texto = resolver_captcha(driver)
    if not texto:
        # ── FIX: captcha vazio contabiliza como erro ──
        stats["captchas_errados"] += 1
        stats["captchas_vazios"]  += 1
        log_warn("Captcha vazio no login — contabilizado")
        return False

    _preencher_captcha(driver, texto)

    try:
        botao = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='Submit']")))
        driver.execute_script("arguments[0].click();", botao)
    except WebDriverException:
        raise
    except Exception as e:
        log_erro(f"Botao de login nao encontrado: {e}")
        return False

    try:
        WebDriverWait(driver, 10).until(EC.staleness_of(botao))
    except Exception:
        time.sleep(1)

    conteudo = driver.page_source
    if "incorreto" in conteudo.lower() or 'name="cd"' in conteudo:
        stats["captchas_errados"] += 1
        log_warn(f"Login rejeitado — captcha '{texto}' errado")
        return False

    stats["captchas_certos"] += 1
    stats["logins_ok"] += 1
    log_ok("Login realizado com sucesso!")
    return True


# ─────────────────────────────────────────────────────────────
#  VERIFICACAO DE VAGAS
# ─────────────────────────────────────────────────────────────

def navegar_servicos_disponiveis(driver):
    stats["status"] = "Verificando vagas..."
    driver.get(URL_SERVICOS)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//select[@name='convenio'] | //img[contains(@src,'captcha')]"))
    )


def _encontrar_botao_solicitar(driver):
    for xpath in SELETORES_SOLICITAR:
        try:
            for el in driver.find_elements(By.XPATH, xpath):
                if el.is_displayed():
                    return el
        except Exception:
            pass
    return None


def _pagina_tem_vaga(driver, pagina_lower: str) -> bool:
    indicadores_vaga = [
        "solicitar servico",
        "solicitar serviço",
        "assumir servico",
        "assumir serviço",
        "inscrever",
        "servico disponivel",
        "serviço disponível",
        "vaga disponivel",
        "vaga disponível",
        "desistencia disponivel",
        "desistência disponível",
    ]
    return any(ind in pagina_lower for ind in indicadores_vaga)


def _normalizar(texto: str) -> str:
    import unicodedata
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )


def selecionar_convenio_e_verificar(driver) -> bool:
    wait = WebDriverWait(driver, 12)

    try:
        dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[@name='convenio']")))
        sel = Select(dropdown)
        alvo_norm = _normalizar(CONVENIO_ALVO)
        opcao_encontrada = None
        for op in sel.options:
            if alvo_norm in _normalizar(op.text):
                opcao_encontrada = op.text
                break
        if opcao_encontrada:
            sel.select_by_visible_text(opcao_encontrada)
            log_info(f"Convenio selecionado: {opcao_encontrada}")
        else:
            log_warn(f"Convenio '{CONVENIO_ALVO}' nao encontrado no dropdown — opcoes disponiveis: {[o.text for o in sel.options]}")
    except Exception as e:
        log_warn(f"Dropdown nao encontrado: {e}")

    texto = resolver_captcha(driver)
    if not texto:
        # ── FIX: captcha vazio contabiliza como erro ──
        stats["captchas_errados"] += 1
        stats["captchas_vazios"]  += 1
        log_warn("Captcha vazio na pagina de servicos — contabilizado")
        return False

    _preencher_captcha(driver, texto)

    try:
        botao_vis = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']")))
        driver.execute_script("arguments[0].click();", botao_vis)
        log_info("Clicou em Visualizar")
    except Exception as e:
        log_erro(f"Botao Visualizar nao encontrado: {e}")
        return False

    try:
        WebDriverWait(driver, 8).until(EC.staleness_of(botao_vis))
    except Exception:
        time.sleep(1)

    pagina_raw  = driver.page_source
    pagina      = pagina_raw.lower()

    if "incorreto" in pagina or 'name="cd"' in pagina_raw:
        stats["captchas_errados"] += 1
        log_warn(f"Captcha invalido (tentativa #{stats['tentativas']})")
        return False

    stats["captchas_certos"] += 1

    if any(k in pagina for k in PALAVRAS_SEM_VAGA):
        stats["sem_vaga"] += 1
        log_info(f"Sem vaga para {CONVENIO_ALVO} — tentativa #{stats['tentativas']} | Total sem vaga: {stats['sem_vaga']}")
        return False

    # Se a pagina ainda exibe o dropdown, a busca nao retornou resultado de vaga
    try:
        driver.find_element(By.XPATH, "//select[@name='convenio']")
        stats["sem_vaga"] += 1
        log_info(f"Sem vaga para {CONVENIO_ALVO} — tentativa #{stats['tentativas']} | Total sem vaga: {stats['sem_vaga']}")
        return False
    except Exception:
        pass

    botao_solicitar = _encontrar_botao_solicitar(driver)

    if not botao_solicitar and _pagina_tem_vaga(driver, pagina):
        log_warn("Botao nao encontrado pelo seletor mas pagina indica vaga — tentando fallback...")
        for termo in ["solicitar", "assumir", "inscrever"]:
            try:
                els = driver.find_elements(By.XPATH, f"//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{termo}')]")
                for el in els:
                    if el.is_displayed() and el.tag_name in ("input", "button", "a"):
                        botao_solicitar = el
                        val = el.text or el.get_attribute("value") or ""
                        log_ok(f"Botao encontrado via fallback: '{val}'")
                        break
            except Exception:
                pass
            if botao_solicitar:
                break

    if botao_solicitar:
        # ── ESTAGIO 1: VAGA ENCONTRADA ──
        console.print()
        console.print(Panel(
            Align.center(Text.from_markup(
                "[bold green blink]VAGA ENCONTRADA![/]\n"
                f"[white]Convenio: {CONVENIO_ALVO}[/]\n"
                f"[dim]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/]"
            )),
            border_style="green", box=box.DOUBLE,
        ))
        log.info("VAGA ENCONTRADA!")
        notificar_vaga_encontrada(CONVENIO_ALVO, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

        try:
            driver.execute_script("arguments[0].click();", botao_solicitar)
            log_ok("Clicou em SOLICITAR SERVICO")
        except UnexpectedAlertPresentException:
            pass

        aceitou = _aceitar_alert_se_presente(driver, timeout=5)
        if aceitou:
            log_ok("Popup de confirmacao aceito — OK clicado!")
        else:
            log_warn("Popup nao apareceu — continuando mesmo assim")

        time.sleep(0.5)
        return True

    stats["sem_vaga"] += 1
    log_warn(f"Pagina desconhecida apos captcha correto (tentativa #{stats['tentativas']}) | Total sem vaga: {stats['sem_vaga']}")
    log.warning(f"PAGINA DESCONHECIDA — HTML snippet: {pagina_raw[:500]}")
    return False


# ─────────────────────────────────────────────────────────────
#  INSCRICAO — verifica resultado apos aceitar o popup
# ─────────────────────────────────────────────────────────────

def confirmar_inscricao(driver) -> bool:
    stats["status"] = "Confirmando inscricao..."

    # ── ESTAGIO 2: SE INSCREVENDO ──
    notificar_inscrevendo(CONVENIO_ALVO, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    console.print()
    console.print(Panel(
        Align.center(Text.from_markup(
            "[bold yellow]SE INSCREVENDO...[/]\n"
            f"[white]Convenio: {CONVENIO_ALVO}[/]\n"
            "[dim]Aguarde a confirmacao[/]"
        )),
        border_style="yellow", box=box.ROUNDED,
    ))

    _aceitar_alert_se_presente(driver, timeout=3)
    time.sleep(1)

    try:
        pagina = driver.page_source.lower()
    except UnexpectedAlertPresentException:
        _aceitar_alert_se_presente(driver, timeout=3)
        time.sleep(0.5)
        pagina = driver.page_source.lower()

    if any(p in pagina for p in PALAVRAS_NEGADO):
        log_warn("Inscricao negada pelo sistema — vaga nao compativel com este militar")
        # ── FIX: Telegram notifica mesmo quando negado ──
        console.print()
        console.print(Panel(
            Align.center(Text.from_markup(
                "[bold red]VAGA NEGADA PELO SISTEMA[/]\n"
                f"[white]Convenio: {CONVENIO_ALVO}[/]\n"
                "[dim]Vaga nao compativel com a patente deste militar[/]"
            )),
            border_style="red", box=box.ROUNDED,
        ))
        notificar(
            f"⚠️ Vaga encontrada em {CONVENIO_ALVO} mas NEGADA pelo sistema.\n"
            "Motivo: vaga nao compativel com a patente deste militar.",
            TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
        )
        return False

    if any(p in pagina for p in PALAVRAS_SUCESSO):
        # ── ESTAGIO 3: INSCRICAO CONFIRMADA ──
        console.print()
        console.print(Panel(
            Align.center(Text.from_markup(
                "[bold green]INSCRICAO CONFIRMADA![/]\n"
                f"[white]Convenio: {CONVENIO_ALVO}[/]\n"
                f"[bold cyan]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/]"
            )),
            border_style="green", box=box.DOUBLE,
        ))
        log.info("INSCRICAO CONFIRMADA COM SUCESSO!")
        notificar_inscricao_confirmada(CONVENIO_ALVO, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        return True

    # Pagina ambigua — notifica para verificar manualmente
    log_warn("Status da inscricao incerto — verifique o sistema PROEISBM")
    notificar(
        f"⚠️ Vaga solicitada em {CONVENIO_ALVO} — resultado incerto.\nVerifique o sistema PROEISBM agora!",
        TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    )
    return True


# ─────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────

def executar_bot():
    banner()

    # ── FIX: Limpa perfil Chrome para garantir sessao fresca ──
    _limpar_perfil_chrome()

    try:
        saldo = verificar_saldo()
        stats["saldo_api"] = saldo
        if saldo > 0:
            log_ok(f"Anti-Captcha API ativa — Saldo: U${saldo:.4f}")
        else:
            log_warn("Anti-Captcha sem saldo — recarregue os creditos!")
    except Exception:
        log_warn("Nao foi possivel verificar saldo da API")

    console.print(painel_status())
    console.print()

    log_info("Iniciando Chrome...")
    driver = criar_driver_com_retry()
    log_ok("Chrome iniciado!")

    MAX_SEM_LOGIN = 20

    try:
        while True:
            console.print()
            console.print(painel_status())
            console.print()

            if not driver_ativo(driver):
                log_warn("Chrome encerrado — reiniciando...")
                encerrar_driver(driver)
                time.sleep(3)
                driver = criar_driver_com_retry()
                log_ok("Chrome reiniciado!")
                continue

            try:
                login_ok = fazer_login(driver)
            except (InvalidSessionIdException, WebDriverException):
                log_warn("Sessao invalida durante login — reiniciando Chrome...")
                encerrar_driver(driver)
                time.sleep(3)
                driver = criar_driver_com_retry()
                continue
            except Exception as e:
                log_erro(f"Erro no login: {e}")
                time.sleep(15)
                continue

            if not login_ok:
                log_warn("Login falhou — aguardando 15s...")
                time.sleep(15)
                continue

            tentativas_desde_login = 0

            while tentativas_desde_login < MAX_SEM_LOGIN:
                stats["tentativas"] += 1
                tentativas_desde_login += 1

                if stats["tentativas"] % 10 == 0:
                    try:
                        stats["saldo_api"] = verificar_saldo()
                    except Exception:
                        pass

                console.print()
                console.print(painel_status())

                try:
                    navegar_servicos_disponiveis(driver)
                    vaga = selecionar_convenio_e_verificar(driver)

                    if vaga:
                        ok = confirmar_inscricao(driver)
                        if ok:
                            console.print()
                            console.print(Panel(
                                Align.center(Text.from_markup(
                                    "[bold green]MISSAO CUMPRIDA![/]\n"
                                    "[white]Vaga capturada e inscricao confirmada![/]\n"
                                    f"[bold cyan]{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/]"
                                )),
                                border_style="green", box=box.DOUBLE,
                            ))
                            log.info("MISSAO CUMPRIDA!")
                            encerrar_driver(driver)
                            return

                    log_info(f"Aguardando {INTERVALO_SEGUNDOS}s...")
                    time.sleep(INTERVALO_SEGUNDOS)

                except SaldoInsuficienteError as e:
                    log_erro(str(e))
                    log_erro("Bot pausado — recarregue os creditos Anti-Captcha e reinicie.")
                    encerrar_driver(driver)
                    return

                except UnexpectedAlertPresentException:
                    log_warn("Alert inesperado detectado — aceitando...")
                    _aceitar_alert_se_presente(driver, timeout=3)
                    time.sleep(0.5)

                except (InvalidSessionIdException, WebDriverException):
                    log_warn("Sessao perdida — reiniciando Chrome...")
                    encerrar_driver(driver)
                    time.sleep(3)
                    driver = criar_driver_com_retry()
                    log_ok("Chrome reiniciado!")
                    break

                except Exception as e:
                    log_erro(f"Erro na tentativa #{stats['tentativas']}: {e}")
                    log_info("Refazendo login em 10s...")
                    time.sleep(10)
                    break

            else:
                log_info("Re-autenticando preventivamente...")

    except KeyboardInterrupt:
        console.print()
        console.print(Panel("[yellow]Bot encerrado pelo usuario.[/]", border_style="yellow"))
        log.info("Bot interrompido pelo usuario.")
    finally:
        encerrar_driver(driver)
        gc.collect()
        log_info("Navegador fechado.")


if __name__ == "__main__":
    executar_bot()