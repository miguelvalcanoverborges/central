# -*- coding: utf-8 -*-
"""Parte administrativa: planos contratados, vencimento, renovação e resumo do mês.

Tabela de planos (valores do PDF de planos de Miguel) em dados/planos.json, editável em Configurações.
Contrato do aluno em aluno.json → "contrato": {"plano": id, "inicio": "AAAA-MM-DD", "valor": R$, "renovacoes": [...]}.
Período: mensal = 4 semanas (o bloco de treino); trimestral = 12 semanas (também no personal).
O valor fica gravado no contrato quando ele é criado ou renovado: mudar a tabela não altera contratos já feitos.
"""
import datetime as dt

from . import armazenamento as A
from .config import DADOS

ARQ = DADOS / "planos.json"
AVISO_DIAS = 7

PADRAO = [   # tabela de 6/out/2026 (PDF de planos de Miguel)
    {"id": "online-mensal", "nome": "Online · mensal", "grupo": "Online", "valor": 140, "semanas": 4},
    {"id": "online-trimestral", "nome": "Online · trimestral", "grupo": "Online", "valor": 380, "semanas": 12},
    {"id": "hibrida-mensal", "nome": "Híbrida · mensal", "grupo": "Híbrida", "valor": 240, "semanas": 4},
    {"id": "hibrida-trimestral", "nome": "Híbrida · trimestral", "grupo": "Híbrida", "valor": 650, "semanas": 12},
    {"id": "personal-1x", "nome": "Personal 1x/sem · mensal", "grupo": "Personal", "valor": 380, "semanas": 4},
    {"id": "personal-1x-trimestral", "nome": "Personal 1x/sem · trimestral", "grupo": "Personal", "valor": 1060, "semanas": 12},
    {"id": "personal-2x", "nome": "Personal 2x/sem · mensal", "grupo": "Personal", "valor": 720, "semanas": 4},
    {"id": "personal-2x-trimestral", "nome": "Personal 2x/sem · trimestral", "grupo": "Personal", "valor": 2000, "semanas": 12},
    {"id": "personal-3x", "nome": "Personal 3x/sem · mensal", "grupo": "Personal", "valor": 1020, "semanas": 4},
    {"id": "personal-3x-trimestral", "nome": "Personal 3x/sem · trimestral", "grupo": "Personal", "valor": 2850, "semanas": 12},
]
VERSAO_TABELA = 2   # muda quando a tabela padrão muda: valores salvos de uma tabela antiga são ignorados


def tabela() -> list[dict]:
    salvo = A.ler_json(ARQ, None)
    if not isinstance(salvo, dict) or salvo.get("versao") != VERSAO_TABELA:
        return [dict(p) for p in PADRAO]
    valores = salvo.get("valores", {})
    return [{**p, "valor": valores.get(p["id"], p["valor"])} for p in PADRAO]


def salvar_tabela(valores: dict) -> list[dict]:
    atual = tabela()
    for p in atual:
        v = valores.get(p["id"])
        if v not in (None, ""):
            p["valor"] = round(float(v), 2)
    A.gravar_json(ARQ, {"versao": VERSAO_TABELA, "valores": {p["id"]: p["valor"] for p in atual}})
    return atual


def _plano(pid: str) -> dict | None:
    return next((p for p in tabela() if p["id"] == pid), None)


def vencimento(contrato: dict) -> dt.date | None:
    p = _plano(contrato.get("plano", ""))
    if not p or not contrato.get("inicio"):
        return None
    return dt.date.fromisoformat(contrato["inicio"]) + dt.timedelta(weeks=p["semanas"])


def situacao(aluno: dict, hoje: dt.date | None = None) -> dict | None:
    """Resumo do contrato para a interface; None se o aluno não tem plano contratado."""
    c = aluno.get("contrato") or {}
    p = _plano(c.get("plano", ""))
    if not p:
        return None
    hoje = hoje or dt.date.today()
    v = vencimento(c)
    dias = (v - hoje).days if v else None
    sit = ""
    if aluno.get("status") == "Ativo" and dias is not None:
        sit = "vencido" if dias < 0 else "renova" if dias <= AVISO_DIAS else "em-dia"
    return {"plano": p["id"], "nome": p["nome"], "grupo": p["grupo"], "valor": c.get("valor", p["valor"]),
            "valor_tabela": p["valor"], "semanas": p["semanas"], "inicio": c.get("inicio", ""),
            "vence": v.isoformat() if v else "", "dias": dias, "situacao": sit,
            "renovacoes": len(c.get("renovacoes", []))}


def definir(aluno: dict, plano_id: str, inicio: str | None) -> dict:
    """Escolhe ou troca o plano (ou tira, com plano_id vazio)."""
    if not plano_id:
        if aluno.get("contrato"):
            A.registrar(aluno, "Plano contratado removido")
        aluno.pop("contrato", None)
        return aluno
    p = _plano(plano_id)
    if not p:
        raise ValueError("Plano desconhecido.")
    c = aluno.get("contrato") or {}
    novo = c.get("plano") != plano_id
    c["plano"] = plano_id
    c["inicio"] = inicio or c.get("inicio") or aluno.get("inicio_bloco") or dt.date.today().isoformat()
    if novo:
        c["valor"] = p["valor"]
        A.registrar(aluno, f"Plano contratado: {p['nome']} (R$ {fmt_valor(p['valor'])})")
    c.setdefault("renovacoes", [])
    aluno["contrato"] = c
    return aluno


def renovar(aluno: dict) -> dict:
    """Novo período a partir do vencimento atual, com o valor da tabela de hoje."""
    c = aluno.get("contrato") or {}
    p = _plano(c.get("plano", ""))
    v = vencimento(c)
    if not p or not v:
        raise ValueError("Este aluno não tem plano contratado.")
    c.setdefault("renovacoes", []).append({"em": A.agora(), "inicio": v.isoformat(), "valor": p["valor"]})
    c["inicio"], c["valor"] = v.isoformat(), p["valor"]
    aluno["contrato"] = c
    A.registrar(aluno, f"Plano renovado: {p['nome']} até {(v + dt.timedelta(weeks=p['semanas'])):%d/%m/%Y} (R$ {fmt_valor(p['valor'])})")
    return aluno


def fmt_valor(v) -> str:
    v = float(v or 0)
    return f"{v:,.0f}".replace(",", ".") if v.is_integer() else f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def resumo_mes(ano: int, mes: int) -> dict:
    """Alunos ativos por plano, valor mensal médio e os vencimentos (renovações) do mês."""
    hoje = dt.date.today()
    planos = {p["id"]: {**p, "alunos": 0, "mensal": 0.0} for p in tabela()}
    sem_plano, vencimentos = [], []
    ini_mes = dt.date(ano, mes, 1)
    fim_mes = dt.date(ano + (mes == 12), mes % 12 + 1, 1)
    for a in A.listar():
        if a.get("status") != "Ativo":
            continue
        s = situacao(a, hoje)
        if not s:
            sem_plano.append({"slug": a["slug"], "nome": a["nome"]})
            continue
        for r in (a.get("contrato") or {}).get("renovacoes", []):   # renovações já feitas cujo vencimento cai no mês
            d = dt.date.fromisoformat(r["inicio"])
            if ini_mes <= d < fim_mes:
                vencimentos.append({"slug": a["slug"], "nome": a["nome"], "plano": s["nome"], "data": d.isoformat(),
                                    "valor": r["valor"], "situacao": "renovado"})
        q = planos[s["plano"]]
        q["alunos"] += 1
        q["mensal"] += float(s["valor"]) * 4 / s["semanas"]          # valor por 4 semanas (trimestral ÷ 3)
        # vencimentos do mês: vencido e não renovado entra uma vez (no mês atual); senão projeta os próximos períodos
        v = dt.date.fromisoformat(s["vence"]) if s["vence"] else None
        if v and v < hoje:
            if ini_mes <= hoje < fim_mes:
                vencimentos.append({"slug": a["slug"], "nome": a["nome"], "plano": s["nome"], "data": v.isoformat(),
                                    "valor": s["valor_tabela"], "situacao": "vencido"})
            continue
        while v and v < fim_mes:
            if v >= ini_mes:
                vencimentos.append({"slug": a["slug"], "nome": a["nome"], "plano": s["nome"], "data": v.isoformat(),
                                    "valor": s["valor_tabela"], "situacao": ""})
            v += dt.timedelta(weeks=s["semanas"])
    vencimentos.sort(key=lambda x: x["data"])
    linhas = [p for p in planos.values() if p["alunos"]]
    return {"ano": ano, "mes": mes, "planos": linhas, "sem_plano": sem_plano, "vencimentos": vencimentos,
            "alunos": sum(p["alunos"] for p in linhas), "mensal": round(sum(p["mensal"] for p in linhas), 2),
            "previsto": round(sum(v["valor"] for v in vencimentos), 2),
            "renovado": round(sum(v["valor"] for v in vencimentos if v["situacao"] == "renovado"), 2)}
