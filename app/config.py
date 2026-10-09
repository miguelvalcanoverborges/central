# -*- coding: utf-8 -*-
"""Caminhos da Central da Consultoria. Tudo local: sem IA, sem internet, sem contas externas."""
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
ALUNOS = DADOS / "alunos"
ENTRADA = DADOS / "_entrada"          # área provisória enquanto a planilha é lida
LIXEIRA = DADOS / "lixeira"           # alunos excluídos (dá para restaurar)
BACKUPS = RAIZ / "backups"
WEB = Path(__file__).resolve().parent / "web"
ICONE = RAIZ / "icone"

MOTOR = RAIZ / "motor" / "consultoria-planilha"
SCRIPTS = MOTOR / "scripts"
ASSETS = MOTOR / "assets"
FERRAMENTAS = RAIZ / "ferramentas"    # Poppler baixado pelo instalador (Windows)

PORTA = 8765

for p in (ALUNOS, ENTRADA, LIXEIRA, BACKUPS):
    p.mkdir(parents=True, exist_ok=True)


def caminho_poppler() -> str | None:
    """Pasta com pdftotext: a baixada pelo instalador (ferramentas/) ou a do sistema."""
    for exe in FERRAMENTAS.rglob("pdftotext.exe" if os.name == "nt" else "pdftotext"):
        return str(exe.parent)
    achado = shutil.which("pdftotext")
    return str(Path(achado).parent) if achado else None


def env_motor() -> dict:
    """Ambiente para rodar os scripts do motor: UTF-8 sempre e Poppler no PATH."""
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    pop = caminho_poppler()
    if pop:
        env["PATH"] = pop + os.pathsep + env.get("PATH", "")
    return env


def python_motor() -> str:
    """Executável Python para os scripts do motor (no Windows, pythonw não tem saída de texto)."""
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        cand = exe.with_name("python.exe")
        if cand.exists():
            return str(cand)
    return str(exe)
