# -*- coding: utf-8 -*-
"""Cadastro de alunos — uma pasta por aluno em dados/alunos/<slug>/.

dados/alunos/<slug>/
  aluno.json               cadastro, plano, bloco, datas, histórico de planilhas e eventos
  planilhas/               TODAS as planilhas matriz recebidas, com data (nunca apagadas)
  trabalho/<envio>/        leitura de cada envio: dados.json, relatorio_revisao.md, estado.json, PDF
  pdfs/                    PDFs entregues: um por bloco (MariaSilva_Bloco02.pdf); refazer o bloco substitui o anterior

Gravação segura: escreve num temporário e só então substitui o original.
"""
import datetime as dt
import json
import os
import re
import shutil
import tempfile
import unicodedata
from pathlib import Path

from .config import ALUNOS, LIXEIRA

STATUS = ["Ativo", "Pausado", "Encerrado"]


def slugify(nome: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", nome) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "aluno"


def agora() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def gravar_seguro(p: Path, conteudo: str | bytes):
    p.parent.mkdir(parents=True, exist_ok=True)
    binario = isinstance(conteudo, bytes)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp_")
    try:
        with os.fdopen(fd, "wb" if binario else "w", **({} if binario else {"encoding": "utf-8"})) as f:
            f.write(conteudo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def ler_json(p: Path, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def gravar_json(p: Path, obj):
    gravar_seguro(p, json.dumps(obj, ensure_ascii=False, indent=1))


def pasta(slug: str) -> Path:
    return ALUNOS / slug


def carregar(slug: str) -> dict | None:
    return ler_json(pasta(slug) / "aluno.json")


def salvar(aluno: dict) -> dict:
    aluno["atualizado_em"] = agora()
    gravar_json(pasta(aluno["slug"]) / "aluno.json", aluno)
    return aluno


def listar() -> list[dict]:
    out = []
    for p in ALUNOS.glob("*/aluno.json"):
        a = ler_json(p)
        if a:
            out.append(a)
    return out


def registrar(aluno: dict, evento: str):
    aluno.setdefault("historico", []).insert(0, {"data": agora(), "evento": evento})


def encontrar_por_nome(nome: str) -> dict | None:
    """Acha o aluno pelo nome da planilha (ou por um nome já vinculado a ele)."""
    s = slugify(nome)
    a = carregar(s)
    if a:
        return a
    for a in listar():
        if s in {slugify(n) for n in a.get("nomes_planilha", [])}:
            return a
    return None


def criar(nome: str) -> dict:
    slug = base = slugify(nome)
    i = 2
    while pasta(slug).exists():
        slug = f"{base}-{i}"
        i += 1
    aluno = {
        "slug": slug, "nome": nome.strip(), "nomes_planilha": [nome.strip()],
        "status": "Ativo", "plano": "", "plano_manual": False, "objetivo": "",
        "usa_pse": False, "notas": "", "numeros": None,
        "bloco_atual": None, "inicio_bloco": "", "ultima_atualizacao": "",
        "proxima_atualizacao": "", "proxima_manual": False,
        "criado_em": agora(), "planilhas": [], "entregas": [], "historico": [],
    }
    for sub in ("planilhas", "trabalho", "pdfs"):
        (pasta(slug) / sub).mkdir(parents=True, exist_ok=True)
    registrar(aluno, "Aluno criado automaticamente a partir da planilha matriz")
    return salvar(aluno)


def excluir(slug: str) -> str:
    """Move o aluno para a lixeira (dá para restaurar em Configurações)."""
    destino = LIXEIRA / f"{slug}__{dt.datetime.now():%Y%m%d-%H%M%S}"
    shutil.move(str(pasta(slug)), str(destino))
    return destino.name


def lixeira() -> list[dict]:
    out = []
    for p in sorted(LIXEIRA.iterdir(), reverse=True) if LIXEIRA.exists() else []:
        a = ler_json(p / "aluno.json")
        if a:
            data = p.name.split("__")[-1]
            out.append({"id": p.name, "nome": a.get("nome", p.name),
                        "excluido_em": f"{data[6:8]}/{data[4:6]}/{data[:4]} {data[9:11]}:{data[11:13]}"})
    return out


def restaurar(id_lixeira: str) -> dict:
    origem = LIXEIRA / id_lixeira
    if not origem.exists() or "/" in id_lixeira or "\\" in id_lixeira:
        raise FileNotFoundError("Item não encontrado na lixeira.")
    a = ler_json(origem / "aluno.json")
    slug = a["slug"]
    if pasta(slug).exists():
        raise FileExistsError(f"Já existe um aluno ativo com o mesmo identificador ({slug}).")
    shutil.move(str(origem), str(pasta(slug)))
    a = carregar(slug)
    registrar(a, "Aluno restaurado da lixeira")
    return salvar(a)
