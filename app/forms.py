# -*- coding: utf-8 -*-
"""Planilhas de respostas do Google Forms (ANAMNESE e FEEDBACK semanal) para TODOS os alunos de uma vez
(Miguel, 16/out/2026). Substitui a importação aluno por aluno.

1. ler()       guarda a planilha em dados/_forms/, descobre se é anamnese ou feedback e sugere o aluno de cada nome.
               Nada é gravado nos alunos aqui.
2. confirmar() só depois da conferência de Miguel: anexa a cada aluno escolhido (feedback: um por semana,
               reimportar substitui; anamnese: a resposta mais recente vira a base, a anterior fica guardada).
               O nome do Forms vira apelido do aluno ("nomes_forms"): na próxima vez ele já vem certo.
               "Ignorar" também é lembrado (leads, testes, ex-alunos).
               Anamnese de quem ainda não está cadastrado fica PENDENTE e é oferecida na ficha do aluno quando ele
               for cadastrado (pela planilha matriz).

Associação por nome: só é automática quando o nome é bem parecido com UM aluno; na dúvida, Miguel escolhe.
"""
import datetime as dt
import difflib

from . import anamnese, dados, individual
from . import armazenamento as A
from .config import DADOS

PASTA = DADOS / "_forms"
PENDENTES = PASTA / "pendentes.json"     # {chave: {"nome", "arquivo", "data_txt"}} anamneses sem aluno ainda
IGNORADOS = PASTA / "ignorados.json"     # ["nome normalizado", ...]
CERTO = 0.86                              # semelhança para associar sem perguntar


def _n(s: str) -> str:
    return anamnese._norm_nome(s)


def tipo(pessoas: dict) -> str:
    """'feedback' se as perguntas são as da semana (adesão, nesta semana); senão 'anamnese'."""
    perguntas = " ".join(_n(q) for p in pessoas.values() for r in p["respostas"][:1] for q, _ in r["pares"])
    return "feedback" if ("adesao" in perguntas or "nesta semana" in perguntas) else "anamnese"


def _nota(nome_forms: str, aluno: dict) -> float:
    """0 a 1. Apelido já confirmado = 1. Nome do Forms contido no nome do aluno ("João Vitor" em "João Vitor
    Rodrigues de Avila") conta como bem parecido."""
    f = _n(nome_forms)
    if f in {_n(x) for x in aluno.get("nomes_forms", [])}:
        return 1.0
    melhor = 0.0
    for nome in [aluno["nome"]] + aluno.get("nomes_planilha", []):
        a = _n(nome)
        r = difflib.SequenceMatcher(None, f, a).ratio()
        tf, ta = f.split(), a.split()
        if len(tf) >= 2 and all(t in ta for t in tf) and tf[0] == ta[0]:
            r = max(r, 0.9)
        melhor = max(melhor, r)
    return melhor


def _limpar(manter: str = ""):
    """A planilha bruta do Forms (com respostas de todos) não fica guardada: depois de confirmar, cada aluno tem a sua
    cópia em anexos/ (e sai junto se o aluno for excluído). Ficam só as que alguma anamnese pendente usa e as de hoje
    (conferência ainda aberta)."""
    usadas = {v["arquivo"] for v in A.ler_json(PENDENTES, {}).values()} | {manter}
    limite = dt.datetime.now().timestamp() - 86400
    for f in PASTA.glob("*"):
        if f.is_file() and f.suffix != ".json" and f.name not in usadas and f.stat().st_mtime < limite:
            f.unlink()


def ler(nome_arq: str, conteudo: bytes) -> dict:
    _limpar()
    pessoas = anamnese.ler(conteudo, nome_arq)
    if not pessoas:
        raise ValueError("A planilha não tem respostas.")
    t = tipo(pessoas)
    destino = PASTA / individual._nome_seguro(nome_arq)
    A.gravar_seguro(destino, conteudo)
    alunos = A.listar()
    ignorados = set(A.ler_json(IGNORADOS, []))
    linhas = []
    for r in anamnese.resumo_pessoas(pessoas):
        notas = sorted(((_nota(r["nome"], a), a) for a in alunos), key=lambda x: x[0], reverse=True)
        n1, a1 = notas[0] if notas else (0, None)
        n2 = notas[1][0] if len(notas) > 1 else 0
        if a1 and n1 >= CERTO and n1 - n2 >= 0.08:
            escolha, certo = a1["slug"], True
        elif _n(r["nome"]) in ignorados:
            escolha, certo = "ignorar", True
        else:
            escolha = a1["slug"] if a1 and n1 >= 0.6 else ("novo" if t == "anamnese" else "ignorar")
            certo = False
        linhas.append({"chave": r["chave"], "nome": r["nome"], "respostas": r["respostas"],
                       "mais_recente": r["mais_recente"], "escolha": escolha, "certo": certo, "_nota": n1})
    # dois nomes do Forms apontando para o mesmo aluno: só o mais parecido segue certo, o outro vai para conferência
    por_aluno = {}
    for l in linhas:
        if l["escolha"] not in ("novo", "ignorar"):
            por_aluno.setdefault(l["escolha"], []).append(l)
    for grupo in por_aluno.values():
        if len(grupo) > 1:
            grupo.sort(key=lambda l: l["_nota"], reverse=True)
            for l in grupo[1:]:
                if l["_nota"] < 1.0:          # apelido já confirmado por Miguel continua certo
                    l["certo"] = False
    for l in linhas:
        l.pop("_nota")
    linhas.sort(key=lambda x: x["certo"])             # as dúvidas primeiro
    return {"tipo": t, "arquivo": destino.name, "linhas": linhas,
            "alunos": [{"slug": a["slug"], "nome": a["nome"]} for a in sorted(alunos, key=lambda a: a["nome"])]}


def _copiar_para(slug: str, arquivo: str) -> str:
    """Cópia da planilha na pasta do aluno (anexos/), como na importação antiga."""
    origem = PASTA / arquivo
    return individual.salvar_anexo(slug, arquivo.split("_", 1)[-1], origem.read_bytes())


def _apelido(slug: str, nome: str):
    a = A.carregar(slug)
    if a and _n(nome) not in {_n(x) for x in a.get("nomes_forms", [])}:
        a.setdefault("nomes_forms", []).append(nome)
        A.salvar(a)


def confirmar(arquivo: str, tipo_: str, escolhas: dict) -> dict:
    """escolhas = {chave: slug | 'ignorar' | 'novo'}."""
    caminho = (PASTA / arquivo).resolve()
    if PASTA.resolve() not in caminho.parents or not caminho.exists():
        raise ValueError("Arquivo não encontrado. Envie a planilha de novo.")
    pessoas = anamnese.ler(caminho.read_bytes(), caminho.name)
    ignorados = set(A.ler_json(IGNORADOS, []))
    pend = A.ler_json(PENDENTES, {})
    res = {"alunos": 0, "novos": 0, "atualizados": 0, "pendentes": 0, "ignorados": 0}
    for chave, escolha in escolhas.items():
        p = pessoas.get(chave)
        if not p:
            continue
        if escolha == "ignorar":
            ignorados.add(_n(p["nome"]))
            res["ignorados"] += 1
            continue
        ignorados.discard(_n(p["nome"]))
        if escolha == "novo":
            if tipo_ == "anamnese":
                pend[chave] = {"nome": p["nome"], "arquivo": arquivo, "data_txt": p["respostas"][0]["data_txt"]}
                res["pendentes"] += 1
            continue
        if not A.carregar(escolha):
            continue
        rel = _copiar_para(escolha, arquivo)
        if tipo_ == "anamnese":
            individual.escolher_anamnese(escolha, rel, chave)
            pend.pop(chave, None)
        else:
            a = A.carregar(escolha)
            semanas = dados.analisar_aluno(a)["semanas"] if dados.planilha_atual(a) else []
            r = individual.importar_feedbacks(escolha, rel, chave, semanas)
            res["novos"] += r["novos"]
            res["atualizados"] += r["atualizados"]
        _apelido(escolha, p["nome"])
        res["alunos"] += 1
    A.gravar_json(IGNORADOS, sorted(ignorados))
    A.gravar_json(PENDENTES, pend)
    if arquivo not in {v["arquivo"] for v in pend.values()}:
        caminho.unlink(missing_ok=True)
    return res


# ------------------------------------------------------------------ anamnese pendente (aluno cadastrado depois)
def pendente_para(aluno: dict) -> dict | None:
    """Anamnese guardada como "aluno novo" cujo nome bate com este aluno (só se ele ainda não tem anamnese)."""
    if individual.carregar_anamnese(aluno["slug"]):
        return None
    pend = A.ler_json(PENDENTES, {})
    notas = sorted(((_nota(v["nome"], aluno), k) for k, v in pend.items()), reverse=True)
    if notas and notas[0][0] >= CERTO:
        k = notas[0][1]
        return {"chave": k, **pend[k]}
    return None


def anexar_pendente(slug: str, chave: str):
    pend = A.ler_json(PENDENTES, {})
    item = pend.get(chave)
    if not item:
        raise ValueError("Esta anamnese não está mais pendente.")
    rel = _copiar_para(slug, item["arquivo"])
    individual.escolher_anamnese(slug, rel, chave)
    _apelido(slug, item["nome"])
    pend.pop(chave)
    A.gravar_json(PENDENTES, pend)
    if item["arquivo"] not in {v["arquivo"] for v in pend.values()}:
        (PASTA / item["arquivo"]).unlink(missing_ok=True)
