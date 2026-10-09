# -*- coding: utf-8 -*-
"""Individualização: anamnese e feedbacks semanais (Forms) usados nos itens pessoais dos PDFs pré e pós.

dados/alunos/<slug>/
  anamnese.json        respostas do Forms (resposta base + histórico), sem contatos
  feedbacks.json       [{id, bloco, semana, global, texto, anexos[], registrado_em}]
  anexos/              arquivos anexados (planilha da anamnese, prints, PDFs de feedback…) — nunca apagados

Os itens dos PDFs são escolhidos em relatorios.itens_auto (regras de formularios.py).
"""
import datetime as dt
import difflib
import re
import uuid
from pathlib import Path

from . import anamnese, formularios
from . import armazenamento as A

MAX_ITENS = 4


def _p(slug: str, nome: str) -> Path:
    return A.pasta(slug) / nome


def _id() -> str:
    return uuid.uuid4().hex[:10]


def _nome_seguro(nome: str) -> str:
    base = re.sub(r"[^\w.\- ]+", "_", Path(nome).name).strip() or "arquivo"
    return f"{dt.datetime.now():%Y%m%d-%H%M%S}_{base}"


def salvar_anexo(slug: str, nome: str, conteudo: bytes) -> str:
    destino = _p(slug, "anexos") / _nome_seguro(nome)
    A.gravar_seguro(destino, conteudo)
    return destino.relative_to(A.pasta(slug)).as_posix()


# ------------------------------------------------------------------ anamnese
def carregar_anamnese(slug: str) -> dict | None:
    return A.ler_json(_p(slug, "anamnese.json"))


def ler_planilha_anamnese(slug: str, nome_arq: str, conteudo: bytes) -> dict:
    """Guarda o arquivo e devolve as pessoas encontradas + a sugerida (nome mais parecido com o do aluno)."""
    pessoas = anamnese.ler(conteudo, nome_arq)
    if not pessoas:
        raise ValueError("A planilha não tem respostas.")
    rel = salvar_anexo(slug, nome_arq, conteudo)
    aluno = A.carregar(slug)
    nomes = [aluno["nome"]] + aluno.get("nomes_planilha", [])
    resumo = anamnese.resumo_pessoas(pessoas)

    def nota(r):
        return max(difflib.SequenceMatcher(None, anamnese._norm_nome(r["nome"]), anamnese._norm_nome(n)).ratio() for n in nomes)
    sugerida = max(resumo, key=nota)
    return {"arquivo": rel, "pessoas": [{k: v for k, v in r.items() if k != "_ord"} for r in resumo],
            "sugerida": sugerida["chave"] if nota(sugerida) >= 0.6 else None}


def escolher_anamnese(slug: str, arquivo: str, chave: str) -> dict:
    caminho = (A.pasta(slug) / arquivo).resolve()
    if A.pasta(slug).resolve() not in caminho.parents:
        raise ValueError("Arquivo inválido.")
    pessoas = anamnese.ler(caminho.read_bytes(), caminho.name)
    if chave not in pessoas:
        raise ValueError("Pessoa não encontrada na planilha.")
    p = pessoas[chave]
    anterior = carregar_anamnese(slug)
    if anterior:   # guarda a versão anterior
        A.gravar_json(_p(slug, "anexos") / f"anamnese_ate_{dt.datetime.now():%Y%m%d-%H%M%S}.json", anterior)
    reg = {"importado_em": A.agora(), "arquivo": arquivo, "nome": p["nome"], "respostas": p["respostas"],
           "mudancas": anamnese.mudancas(p)}
    A.gravar_json(_p(slug, "anamnese.json"), reg)
    a = A.carregar(slug)
    A.registrar(a, f"Anamnese anexada (resposta base {p['respostas'][0]['data_txt']})")
    A.salvar(a)
    return reg


def remover_anamnese(slug: str):
    p = _p(slug, "anamnese.json")
    if p.exists():
        A.gravar_json(_p(slug, "anexos") / f"anamnese_removida_{dt.datetime.now():%Y%m%d-%H%M%S}.json", A.ler_json(p))
        p.unlink()


# ------------------------------------------------------------------ feedbacks semanais
def carregar_feedbacks(slug: str) -> list[dict]:
    """Feedbacks com a triagem (pontos que pedem atenção), do mais recente para o mais antigo."""
    lst = A.ler_json(_p(slug, "feedbacks.json"), [])
    for f in lst:
        f["atencao"] = formularios.triagem(f.get("pares") or [])
    return sorted(lst, key=lambda f: f.get("data") or f.get("registrado_em", ""), reverse=True)


def marcar_visto(slug: str, fid: str, visto: bool = True):
    lst = A.ler_json(_p(slug, "feedbacks.json"), [])
    for f in lst:
        if f["id"] == fid:
            f["visto"] = bool(visto)
    _gravar_feedbacks(slug, lst)


def _gravar_feedbacks(slug, lst):
    lst.sort(key=lambda f: (f.get("global") or 0, f.get("registrado_em", "")), reverse=True)
    A.gravar_json(_p(slug, "feedbacks.json"), lst)


def remover_feedback(slug: str, fid: str):
    lst = [f for f in A.ler_json(_p(slug, "feedbacks.json"), []) if f["id"] != fid]
    _gravar_feedbacks(slug, lst)


# ------------------------------------------------------------------ itens dos PDFs
def ler_planilha_feedback(slug: str, nome_arq: str, conteudo: bytes) -> dict:
    """Mesmo processo da anamnese: guarda o arquivo e sugere a pessoa pelo nome."""
    return ler_planilha_anamnese(slug, nome_arq, conteudo)


def importar_feedbacks(slug: str, arquivo: str, chave: str, semanas: list[dict]) -> int:
    """Cria um feedback por resposta do Forms (sem duplicar), na semana do ciclo em que foi respondido."""
    import datetime as dt_
    caminho = (A.pasta(slug) / arquivo).resolve()
    if A.pasta(slug).resolve() not in caminho.parents:
        raise ValueError("Arquivo inválido.")
    pessoas = anamnese.ler(caminho.read_bytes(), caminho.name)
    if chave not in pessoas:
        raise ValueError("Pessoa não encontrada na planilha.")
    lst = A.ler_json(_p(slug, "feedbacks.json"), [])
    existentes = {f.get("forms_data") for f in lst if f.get("forms_data")}
    novos = 0
    for r in pessoas[chave]["respostas"]:
        if not r["data"] or r["data"] in existentes:
            continue
        d = dt_.date.fromisoformat(r["data"][:10])
        sem = None
        for s_ in semanas:          # semana do ciclo em que o feedback foi respondido (ou a última que já tinha começado)
            if s_["data"] and dt_.date.fromisoformat(s_["data"]) <= d:
                sem = s_
        lst.append({"id": _id(), "anexos": [{"nome": Path(arquivo).name.split("_", 1)[-1], "arquivo": arquivo}],
                    "registrado_em": A.agora(), "forms_data": r["data"], "data": r["data"], "data_txt": r["data_txt"],
                    "bloco": sem["bloco"] if sem else None, "semana": sem["semana"] if sem else None,
                    "global": sem["global"] if sem else None, "pares": r["pares"],
                    "texto": formularios.texto_feedback(r["pares"])})
        novos += 1
    _gravar_feedbacks(slug, lst)
    if novos:
        a = A.carregar(slug)
        A.registrar(a, f"{novos} feedback(s) semanal(is) importado(s) da planilha do Forms")
        A.salvar(a)
    return novos


# ------------------------------------------------------------------ sugestões automáticas dos itens dos PDFs
