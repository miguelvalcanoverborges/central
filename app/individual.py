# -*- coding: utf-8 -*-
"""Individualização: anamnese e feedbacks semanais (Forms) usados nos itens pessoais dos PDFs pré e pós.

dados/alunos/<slug>/
  anamnese.json        respostas do Forms (resposta base + histórico), sem contatos
  feedbacks.json       [{id, bloco, semana, global, texto, anexos[], registrado_em}]
  anexos/              arquivos anexados (planilha da anamnese, prints, PDFs de feedback…) — nunca apagados

Os itens dos PDFs são escolhidos em relatorios.itens_auto (regras de formularios.py).
"""
import datetime as dt
import json
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
def importar_feedbacks(slug: str, arquivo: str, chave: str, semanas: list[dict]) -> dict:
    """Um feedback por resposta do Forms, na semana do ciclo em que foi respondido. Importar de novo SUBSTITUI
    (Miguel, 16/out/2026): a resposta já guardada (mesma data/hora do Forms) é trocada pela da planilha nova — se o
    aluno editou a resposta no Forms, vale a versão nova e o "visto" volta a ficar pendente. Nada duplica."""
    import datetime as dt_
    caminho = (A.pasta(slug) / arquivo).resolve()
    if A.pasta(slug).resolve() not in caminho.parents:
        raise ValueError("Arquivo inválido.")
    pessoas = anamnese.ler(caminho.read_bytes(), caminho.name)
    if chave not in pessoas:
        raise ValueError("Pessoa não encontrada na planilha.")
    lst = A.ler_json(_p(slug, "feedbacks.json"), [])
    por_data = {f["forms_data"]: f for f in lst if f.get("forms_data")}
    anexo = {"nome": Path(arquivo).name.split("_", 1)[-1], "arquivo": arquivo}
    novos = atualizados = 0
    for r in pessoas[chave]["respostas"]:
        if not r["data"]:
            continue
        d = dt_.date.fromisoformat(r["data"][:10])
        sem = None
        for s_ in semanas:          # semana do ciclo em que o feedback foi respondido (ou a última que já tinha começado)
            if s_["data"] and dt_.date.fromisoformat(s_["data"]) <= d:
                sem = s_
        pares = json.loads(json.dumps(r["pares"], ensure_ascii=False))   # mesmo formato do que já está gravado
        reg = {"forms_data": r["data"], "data": r["data"], "data_txt": r["data_txt"],
               "bloco": sem["bloco"] if sem else None, "semana": sem["semana"] if sem else None,
               "global": sem["global"] if sem else None, "pares": pares,
               "texto": formularios.texto_feedback(pares)}
        antigo = por_data.get(r["data"])
        if antigo is None:
            lst.append({"id": _id(), "anexos": [anexo], "registrado_em": A.agora(), **reg})
            novos += 1
            continue
        mudou = antigo.get("pares") != pares
        if mudou or any(antigo.get(k) != v for k, v in reg.items()):
            antigo.update(reg)
            antigo["atualizado_em"] = A.agora()
            if mudou:
                antigo["visto"] = False
                atualizados += 1
        if anexo["arquivo"] not in {x.get("arquivo") for x in antigo.get("anexos", [])}:
            antigo.setdefault("anexos", []).append(anexo)
    _gravar_feedbacks(slug, lst)
    if novos or atualizados:
        a = A.carregar(slug)
        A.registrar(a, f"Feedback do Forms: {novos} novo(s), {atualizados} atualizado(s)")
        A.salvar(a)
    return {"novos": novos, "atualizados": atualizados}


def linha_do_tempo(slug: str, semanas: list[dict], ate_global: int | None = None) -> list[dict]:
    """Notas do feedback por semana do ciclo (a resposta mais recente da semana vale), para os gráficos da Central e
    do PDF de Resultados. [{global, bloco, rotulo, notas|None}] para cada semana da planilha."""
    por_sem = {}
    datas = [(s["data"], s["global"]) for s in semanas if s.get("data")]
    for f in sorted(carregar_feedbacks(slug), key=lambda f: f.get("data") or ""):
        if not f.get("pares"):
            continue
        # a semana sai da DATA da resposta, sempre de novo (Miguel, 21/out/2026): o feedback importado antes de a planilha
        # do bloco seguinte chegar não fica preso na última semana que existia naquele dia
        g = max((g for d, g in datas if f.get("data") and d <= f["data"][:10]), default=None) if datas else f.get("global")
        if g:
            por_sem[g] = formularios.notas(f["pares"])   # sempre recalculado das respostas
    return [{"global": s["global"], "bloco": s["bloco"], "rotulo": f"S{s['global']:02d}",
             "notas": por_sem.get(s["global"]) if ate_global is None or s["global"] <= ate_global else None,
             "futura": ate_global is not None and s["global"] > ate_global}
            for s in semanas]


# ------------------------------------------------------------------ sugestões automáticas dos itens dos PDFs
