# -*- coding: utf-8 -*-
"""Central da Consultoria — abre o programa numa janela própria, sem terminal.

O atalho da área de trabalho (ícone de gorila) roda este arquivo com pythonw.exe, que não abre janela de console.
Ele liga o servidor local (só neste computador) e abre a janela do app no Microsoft Edge em modo aplicativo
(sem barra de endereço). Ao fechar a janela, o programa se encerra sozinho.
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
LOG = RAIZ / "dados" / "central.log"

# pythonw não tem console: manda qualquer saída para o arquivo de log
if sys.stdout is None or sys.stderr is None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    _saida = open(LOG, "a", encoding="utf-8", buffering=1)  # noqa: SIM115
    sys.stdout = sys.stdout or _saida
    sys.stderr = sys.stderr or _saida


def log(msg: str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")


def aviso_erro(msg: str):
    """Sem console, erros aparecem numa caixa de mensagem."""
    log(msg)
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg[:1500], "Central da Consultoria", 0x10)
    else:
        print(msg, file=sys.stderr)


def ja_rodando(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/api/ping", timeout=1.5) as r:
            return json.loads(r.read()).get("app") == "central-consultoria"
    except Exception:  # noqa: BLE001
        return False


def achar_edge() -> str | None:
    cands = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    for nome in ("msedge", "microsoft-edge", "google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(nome)
        if p:
            return p
    return None


def abrir_janela(url: str):
    nav = achar_edge()
    if nav:
        perfil = RAIZ / "dados" / ".janela"     # perfil próprio: janela separada, com o ícone do app
        subprocess.Popen([nav, f"--app={url}", f"--user-data-dir={perfil}", "--window-size=1400,920",
                          "--no-first-run", "--no-default-browser-check", "--disable-features=Translate"],
                         creationflags=0x08000000 if os.name == "nt" else 0)
    else:
        webbrowser.open(url)


def vigiar(servidor):
    """Encerra quando a janela fecha (a página para de mandar sinal de vida)."""
    from app.servidor import ULTIMO_PING
    inicio = time.time()
    while True:
        time.sleep(5)
        parado = time.time() - ULTIMO_PING["t"]
        if (ULTIMO_PING["algum"] and parado > 40) or (not ULTIMO_PING["algum"] and time.time() - inicio > 180):
            log("Janela fechada: encerrando.")
            servidor.shutdown()
            os._exit(0)


def main():
    from app.config import PORTA
    url = f"http://127.0.0.1:{PORTA}"
    if ja_rodando(url):
        abrir_janela(url)
        return
    from werkzeug.serving import make_server

    from app import backup
    from app.servidor import app
    try:
        backup.diario()
    except Exception:  # noqa: BLE001
        log("Backup automático falhou:\n" + traceback.format_exc())
    try:
        servidor = make_server("127.0.0.1", PORTA, app, threaded=True)
    except OSError:
        aviso_erro(f"A porta {PORTA} está ocupada por outro programa. Feche-o e abra a Central de novo.")
        return
    threading.Thread(target=vigiar, args=(servidor,), daemon=True).start()
    log("Central iniciada.")
    abrir_janela(url)
    servidor.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        aviso_erro("A Central não conseguiu abrir.\n\n" + traceback.format_exc())
