# -*- coding: utf-8 -*-
"""Textos de entrega para o WhatsApp (Miguel, 11/out/2026): vão junto do PDF, prontos para copiar.

  PLANEJAMENTO — datas do bloco, dias de treino, principais exercícios com 1RM, até 2 itens "Pensado para você",
                 semana do teste e próxima revisão.
  FICHA        — agenda do que o aluno faz no bloco, por semana e dia: o que gravar, o que anotar e o teste AMRAP,
                 pelas mesmas regras automáticas do motor (GRAVAR em %1RM ≥ 80% fora do aquecimento e em AMRAP;
                 ANOTAR em faixa de repetições e AMRAP).
  RESULTADOS   — 1RM estimado antes → depois (no máximo 4), peso levantado (o mesmo número do PDF pós), itens do
                 feedback com fato verificável e início do próximo bloco.

Nada é inventado: sem o dado, a linha some. Sem diagnóstico, sem promessa, sem linguagem de guru.
"""
import datetime as dt
import re

from . import armazenamento as A
from . import dados
from .relatorios import _contexto, _lista, itens_auto, mil, n0, var

MES_CURTO = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FAIXA_RE = re.compile(r"^\s*\d+\s*[-–—]\s*\d+\s*$")


def _d(x) -> str:
    """13/out"""
    if not x:
        return ""
    d = x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])
    return f"{d.day:02d}/{MES_CURTO[d.month - 1]}"


def _periodo(ini: str) -> str:
    """13 a 19/out · 27/out a 02/nov"""
    if not ini:
        return ""
    a = dt.date.fromisoformat(ini)
    b = a + dt.timedelta(days=6)
    return f"{a.day:02d} a {_d(b)}" if a.month == b.month else f"{_d(a)} a {_d(b)}"


def _data_do_dia(ini: str, dia: str):
    if not ini or dia not in dados.DIAS_ORDEM:
        return None
    d0 = dt.date.fromisoformat(ini)
    return d0 + dt.timedelta(days=(dados.DIAS_ORDEM.index(dia) - d0.weekday()) % 7)


def _partes(obs) -> list[str]:
    return [p.strip().lower() for p in str(obs or "").split(" - ") if p.strip()]


def _tarefa(r: dict) -> str:
    """O que o aluno faz nesta linha da ficha (vazio = nada a gravar ou anotar)."""
    reps, partes = str(r.get("reps") or ""), _partes(r.get("obs"))
    ex = r["ex"]
    if "amrap" in reps.lower() or "amrap" in partes:
        carga = f" com {r['kg']} kg" if r.get("kg") else ""
        return f"{ex}: AMRAP{carga}. Grave e anote as repetições"
    gravar = "gravar" in partes or (r.get("pct") and round(r["pct"] * 100) >= 80 and "aquecimento" not in partes)
    anotar = "anotar" in partes or bool(FAIXA_RE.match(reps))
    serie = f"{r['series']}×{re.sub(r'\s*[-–—]\s*', ' a ', reps)}" if r.get("series") and reps else ""
    if r.get("pct") and gravar:
        serie += f" a {round(r['pct'] * 100)}%"
    serie = f" {serie}" if serie else ""
    if gravar and anotar:
        return f"{ex}{serie}: grave e anote repetições e carga"
    if gravar:
        return f"{ex}{serie}: grave"
    if anotar:
        return f"{ex}{serie}: anote repetições e carga"
    return ""


def agenda(C: dict, bloco: int) -> list[dict]:
    """[{semana, periodo, teste, dias: [{dia, data, tarefas}]}] só com as semanas que têm algo a fazer."""
    out = []
    for s in C["P"]["semanas"]:
        if s["bloco"] != bloco:
            continue
        dias, teste = [], False
        for num, rows in s["treinos"].items():
            tarefas = []
            for r in rows:
                t = _tarefa(r)
                if t and t not in tarefas:
                    tarefas.append(t)
                teste = teste or "amrap" in (str(r.get("reps")) + str(r.get("obs"))).lower()
            if tarefas:
                dia = s["dias"].get(f"T{num}", "")
                dias.append({"dia": dados.DIA_CURTO.get(dia, f"Treino {num}"), "data": _d(_data_do_dia(s["data"], dia)),
                             "ordem": dados.DIAS_ORDEM.index(dia) if dia in dados.DIAS_ORDEM else 9, "tarefas": tarefas})
        if dias:
            dias.sort(key=lambda d: d["ordem"])
            out.append({"semana": s["semana"], "periodo": _periodo(s["data"]), "teste": teste, "dias": dias})
    return out


def _sem_bloco(C):
    return [s for s in C["R"]["semanas"] if s["bloco"] == C["bloco"]]


def texto_planejamento(aluno: dict, C: dict) -> str:
    primeiro, bloco = aluno["nome"].split()[0], C["bloco"]
    ss = _sem_bloco(C)
    ini = ss[0]["data"] if ss else ""
    fim = (dt.date.fromisoformat(ss[-1]["data"]) + dt.timedelta(days=6)) if ss and ss[-1]["data"] else None
    dias = [d.lower() for d in C["dias"]]
    abre = f"{primeiro}, segue o seu planejamento do Bloco {bloco:02d}"
    if ini and fim:
        abre += f": de {_d(ini)} a {_d(fim)}"
    if dias:
        abre += f", treinos {'no' if dias[0] in ('sábado', 'domingo') else 'na'} {_lista(dias)}"
    linhas = [abre + "."]

    ref = C["P"].get("rm_ref", {}).get(bloco, {})
    if ref:
        nomes = list(ref)
        partes = [f"{nomes[0]} (1RM estimado de {round(ref[nomes[0]]['est'])} kg)"] + \
                 [f"{n} ({round(ref[n]['est'])} kg)" for n in nomes[1:]]
        ver = "é" if len(nomes) == 1 else "são"
        linhas.append(f"{'O principal exercício' if len(nomes) == 1 else 'Os principais exercícios'} deste bloco {ver} "
                      f"{_lista(partes)}. As cargas da ficha partem desses números.")

    for i in itens_auto(aluno, "pre", C)[:2]:
        linhas.append(f"Você contou: {i['aluno'].rstrip('.')}. {i['treino']}")

    testes = [a for a in agenda(C, bloco) if a["teste"]]
    if testes:
        t = testes[0]
        linhas.append(f"Na semana {t['semana']}{' (' + t['periodo'] + ')' if t['periodo'] else ''} tem teste: "
                      f"as séries AMRAP atualizam o seu 1RM.")
    if aluno.get("proxima_atualizacao"):
        linhas.append(f"Próxima revisão: {_d(aluno['proxima_atualizacao'])}.")
    return "\n\n".join(linhas)


def texto_ficha(aluno: dict, C: dict) -> str:
    primeiro, bloco = aluno["nome"].split()[0], C["bloco"]
    ag = agenda(C, bloco)
    if not ag:
        return f"{primeiro}, sua ficha do Bloco {bloco:02d} está no PDF. Neste bloco não há séries para gravar ou anotar."
    blocos = [f"{primeiro}, sua ficha do Bloco {bloco:02d} está no PDF. O que preciso de você:"]
    grava = anota = False
    for a in ag:
        cab = f"*Semana {a['semana']}{' (' + a['periodo'] + ')' if a['periodo'] else ''}{', teste' if a['teste'] else ''}*"
        itens = []
        for d in a["dias"]:
            rot = f"{d['dia']}, {d['data']}" if d["data"] else d["dia"]
            for t in d["tarefas"]:
                itens.append(f"• {rot}: {t}.")
                grava = grava or "grave" in t.lower()
                anota = anota or "anote" in t.lower()
        blocos.append(cab + "\n" + "\n".join(itens))
    envio = "os vídeos e as anotações" if grava and anota else "os vídeos" if grava else "as anotações"
    blocos.append(f"Me mande {envio} aqui no dia do treino.")
    return "\n\n".join(blocos)


def texto_resultados(aluno: dict, C: dict) -> str:
    primeiro, R, atual = aluno["nome"].split()[0], C["R"], C["atual"]
    ss = [s for s in R["semanas"] if s["bloco"] == atual["bloco"]]
    fechou = bool(ss) and atual["global"] == ss[-1]["global"]
    linhas = [f"{primeiro}, fechamos o Bloco {atual['bloco']:02d}." if fechou
              else f"{primeiro}, seus resultados até a semana {atual['semana']} do Bloco {atual['bloco']:02d}."]
    evo = [x for x in R.get("rm_evolucao", []) if x.get("variacao") is not None][:4]
    if evo:
        linhas.append("Seus números (1RM estimado):\n" + "\n".join(
            f"• {x['exercicio']}: {n0(x['blocos'][0]['est'])} → {n0(x['blocos'][-1]['est'])} kg ({var(x['variacao'])})"
            for x in evo))
    feitas = [s for s in R["semanas"] if s["global"] <= atual["global"]]
    vol = sum(s["vtt"] for s in feitas)
    if vol:
        n = len(feitas)
        linhas.append(f"Em {n} {'semana' if n == 1 else 'semanas'} você levantou {mil(vol)} kg somando todas as séries.")
    for i in itens_auto(aluno, "pos", C)[:2]:
        if i.get("chave") == "motivacao" and evo:
            continue                          # os números já estão na lista acima
        linhas.append(f"{i['aluno'].rstrip('.')}. {i['resultado']}")
    prox = next((s for s in R["semanas"] if s["bloco"] == atual["bloco"] + 1 and s["data"]), None)
    if prox:
        linhas.append(f"O Bloco {prox['bloco']:02d} começa em {_d(prox['data'])}.")
    elif aluno.get("proxima_atualizacao"):
        linhas.append(f"Próxima revisão: {_d(aluno['proxima_atualizacao'])}.")
    linhas.append("O PDF com os detalhes vai junto.")
    return "\n\n".join(linhas)


def gerar(slug: str) -> dict:
    aluno = A.carregar(slug)
    if not aluno:
        raise ValueError("Aluno não encontrado.")
    C = _contexto(aluno)
    return {"planejamento": texto_planejamento(aluno, C), "ficha": texto_ficha(aluno, C),
            "resultados": texto_resultados(aluno, C)}
