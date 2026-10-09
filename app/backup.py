# -*- coding: utf-8 -*-
"""Backup da pasta dados/ (alunos, anamneses, briefings, entregas, metodologia).

- Automático: ao abrir o programa, uma cópia por dia em backups/backup_AAAA-MM-DD.zip (guarda os últimos 30).
- Manual: exportar agora (download) e restaurar a partir de um .zip.
- Restaurar sempre faz antes uma cópia de segurança do estado atual, então nada se perde.
"""
import datetime as dt
import io
import shutil
import zipfile
from pathlib import Path

from .config import BACKUPS, DADOS

MANTER = 30
IGNORAR = ("_entrada",)


def _arquivos():
    for p in sorted(DADOS.rglob("*")):
        rel = p.relative_to(DADOS)
        if p.is_file() and not any(part in IGNORAR or part.startswith(".tmp_") for part in rel.parts):
            yield p, rel


def _zipar(destino) -> int:
    n = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in _arquivos():
            z.write(p, Path("dados") / rel)
            n += 1
    return n


def criar(sufixo: str = "") -> Path:
    BACKUPS.mkdir(parents=True, exist_ok=True)
    hoje = dt.datetime.now()
    nome = f"backup_{hoje:%Y-%m-%d}{sufixo}.zip" if not sufixo else f"backup_{hoje:%Y-%m-%d_%H%M%S}{sufixo}.zip"
    destino = BACKUPS / nome
    tmp = destino.with_suffix(".tmp")
    _zipar(tmp)
    tmp.replace(destino)
    return destino


def diario() -> Path | None:
    """Cria o backup do dia se ainda não existe. Chamado ao abrir o programa."""
    hoje = BACKUPS / f"backup_{dt.date.today():%Y-%m-%d}.zip"
    if hoje.exists() or not any(True for _ in _arquivos()):
        return None
    p = criar()
    _limpar()
    return p


def _limpar():
    diarios = sorted(BACKUPS.glob("backup_????-??-??.zip"))
    for p in diarios[:-MANTER]:
        p.unlink(missing_ok=True)


def listar() -> list[Path]:
    return sorted(BACKUPS.glob("backup_*.zip"), reverse=True)


def exportar_bytes() -> bytes:
    buf = io.BytesIO()
    _zipar(buf)
    return buf.getvalue()


def restaurar(zip_bytes: bytes) -> tuple[bool, str]:
    """Substitui dados/ pelo conteúdo do .zip (exportado por este programa)."""
    try:
        z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return False, "O arquivo não é um .zip válido."
    nomes = [n for n in z.namelist() if not n.endswith("/")]
    if not nomes or not all(n.startswith("dados/") for n in nomes):
        return False, "Este .zip não é um backup da Central (esperava a pasta dados/ dentro dele)."
    if any(".." in Path(n).parts for n in nomes):
        return False, "Arquivo de backup inválido."
    seguranca = criar(sufixo="_antes-de-restaurar")
    tmp = DADOS.parent / "_restaurando"
    shutil.rmtree(tmp, ignore_errors=True)
    z.extractall(tmp)
    antigo = DADOS.parent / "_dados_antigo"
    shutil.rmtree(antigo, ignore_errors=True)
    DADOS.rename(antigo)
    (tmp / "dados").rename(DADOS)
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(antigo, ignore_errors=True)
    return True, f"Restaurado. O estado anterior foi guardado em {seguranca.name}."
