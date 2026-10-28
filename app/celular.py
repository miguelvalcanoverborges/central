# -*- coding: utf-8 -*-
"""Central no celular (Miguel, 28/out/2026): a Central continua só no notebook; o celular abre ela pela internet
num túnel privado do Tailscale (só os aparelhos da conta de Miguel enxergam), com senha.

`tailscale serve` publica https://<computador>.<rede>.ts.net → http://127.0.0.1:8765. Os pedidos do celular chegam
pelo Tailscale com os cabeçalhos dele; os do notebook não. Os dados dos alunos nunca saem do notebook.
"""
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import armazenamento as A
from .config import DADOS, PORTA, RAIZ

ARQ = DADOS / "celular.json"
_SEM_JANELA = 0x08000000 if os.name == "nt" else 0       # CREATE_NO_WINDOW
_ERROS = {"n": 0, "ate": 0.0}                              # senha errada: 5 tentativas, depois 10 min de espera


def ler() -> dict:
    d = A.ler_json(ARQ, {})
    if not d.get("segredo"):                               # chave do cookie de quem já entrou com a senha
        d["segredo"] = secrets.token_hex(32)
        A.gravar_json(ARQ, d)
    return d


def ativo() -> bool:
    return bool(A.ler_json(ARQ, {}).get("ativo"))


def _hash(pin: str, sal: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(sal), 200_000).hex()


# ------------------------------------------------------------------ quem está pedindo
def remoto(req) -> bool:
    """Pedido que veio do celular (pelo Tailscale), não da janela do notebook."""
    if req.remote_addr not in ("127.0.0.1", "::1"):
        return True
    if req.headers.get("Tailscale-User-Login") or req.headers.get("X-Forwarded-For"):
        return True
    host = (req.host or "").split(":")[0]
    return host not in ("127.0.0.1", "localhost")


def marca_sessao(d: dict) -> str:
    """Muda quando a senha muda: quem entrou com a senha antiga precisa entrar de novo."""
    return (d.get("pin") or "")[:16]


def conferir_pin(pin: str) -> tuple[bool, str]:
    agora = time.time()
    if _ERROS["ate"] > agora:
        return False, f"Muitas tentativas. Tente de novo em {int((_ERROS['ate'] - agora) // 60) + 1} min."
    d = ler()
    if d.get("ativo") and d.get("pin") and secrets.compare_digest(_hash(pin or "", d["sal"]), d["pin"]):
        _ERROS["n"] = 0
        return True, ""
    _ERROS["n"] += 1
    if _ERROS["n"] >= 5:
        _ERROS.update(n=0, ate=agora + 600)
    return False, "Senha errada."


# ------------------------------------------------------------------ Tailscale
def _exe() -> str | None:
    for c in (os.path.expandvars(r"%ProgramFiles%\Tailscale\tailscale.exe"),
              os.path.expandvars(r"%ProgramFiles(x86)%\Tailscale\tailscale.exe"),
              "/Applications/Tailscale.app/Contents/MacOS/Tailscale"):
        if c and os.path.exists(c):
            return c
    return shutil.which("tailscale")


def _ts(*args, espera=15) -> tuple[int, str]:
    exe = _exe()
    if not exe:
        return 127, ""
    try:
        r = subprocess.run([exe, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=espera, creationflags=_SEM_JANELA)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:              # `serve` fica esperando quando o HTTPS ainda não foi liberado
        saida = e.stdout or b""
        saida = saida.decode("utf-8", "replace") if isinstance(saida, bytes) else saida
        return -1, saida
    except OSError as e:
        return 1, str(e)


def estado() -> dict:
    """O que a tela de Configurações mostra."""
    d = ler()
    out = {"ativo": bool(d.get("ativo")), "tem_senha": bool(d.get("pin")), "instalado": bool(_exe()),
           "conectado": False, "endereco": d.get("endereco", "")}
    if not out["instalado"]:
        return out
    cod, txt = _ts("status", "--json", espera=8)
    try:
        st = json.loads(txt) if cod == 0 else {}
    except ValueError:
        st = {}
    out["conectado"] = st.get("BackendState") == "Running"
    nome = ((st.get("Self") or {}).get("DNSName") or "").rstrip(".")
    if nome:
        out["endereco"] = f"https://{nome}"
    return out


def ligar(pin: str | None) -> dict:
    d = ler()
    if pin is not None:
        if not re.fullmatch(r"\d{4,8}", pin or ""):
            return {"ok": False, "erro": "A senha tem de ter de 4 a 8 números."}
        d["sal"] = secrets.token_hex(16)
        d["pin"] = _hash(pin, d["sal"])
    if not d.get("pin"):
        return {"ok": False, "erro": "Escolha uma senha."}
    A.gravar_json(ARQ, d)                                  # a senha fica guardada para a próxima tentativa
    st = estado()
    if not st["instalado"]:
        return {"ok": False, "erro": "Instale o Tailscale neste computador."}
    if not st["conectado"]:
        return {"ok": False, "erro": "Abra o Tailscale neste computador e entre na sua conta."}
    cod, txt = _ts("serve", "--bg", str(PORTA), espera=20)
    link = re.search(r"https://login\.tailscale\.com/\S+", txt)
    if cod != 0:
        if link:
            return {"ok": False, "liberar": link.group(0),
                    "erro": "Falta liberar o acesso no site do Tailscale. Abra o link, confirme e clique em Ligar de novo."}
        return {"ok": False, "erro": "O Tailscale não aceitou: " + (txt.strip()[:300] or "sem resposta")}
    d.update(ativo=True, endereco=st["endereco"])
    A.gravar_json(ARQ, d)
    _inicializacao(True)
    return {"ok": True, **estado()}


def desligar() -> dict:
    _ts("serve", "reset", espera=10)
    d = ler()
    d["ativo"] = False
    A.gravar_json(ARQ, d)
    _inicializacao(False)
    return {"ok": True, **estado()}


# ------------------------------------------------------------------ abrir sozinha ao ligar o computador
def _atalho_inicializacao() -> Path | None:
    if os.name != "nt":
        return None
    pasta = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
    return pasta / "Central da Consultoria (celular).vbs" if pasta.exists() else None


def _inicializacao(ligar_: bool):
    """Com o celular ligado, a Central abre escondida quando o Windows inicia (sem janela, sem terminal)."""
    alvo = _atalho_inicializacao()
    if not alvo:
        return
    if not ligar_:
        alvo.unlink(missing_ok=True)
        return
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe") if exe.with_name("pythonw.exe").exists() else exe
    A.gravar_seguro(alvo, f'CreateObject("WScript.Shell").Run """{pyw}"" ""{RAIZ / "Central.pyw"}"" --fundo", 0, False\n')
