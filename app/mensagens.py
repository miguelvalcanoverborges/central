# -*- coding: utf-8 -*-
"""Mensagens prontas para o WhatsApp (Miguel, 11/out/2026). As regras e os textos ficam no motor
(`motor/consultoria-planilha/scripts/mensagem.py`, o mesmo da skill consultoria-planilha); aqui só se juntam os dados
do aluno na Central:

- ENTREGA: dados.json da ficha (a cópia ajustada; só as semanas escolhidas), próxima revisão do aluno e se o
  planejamento do bloco já foi gerado.
- RESULTADOS: 1RM entre blocos (aba Dados, da planilha original), os itens do PDF pós e o início do próximo bloco.
"""
import json
import sys

from . import armazenamento as A
from .config import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
from mensagem import texto_entrega, texto_resultados  # noqa: E402,F401

# ------------------------------------------------------------------ a partir do aluno na Central
def entrega(slug: str, envio: str, semanas: list | None = None) -> str:
    aluno = A.carregar(slug)
    D = json.loads((A.pasta(slug) / "trabalho" / envio / "dados.json").read_text(encoding="utf-8"))
    n = int(D["bloco"]["numero"])
    from . import dados
    nome_pl = dados.nome_arquivo(aluno["nome"], n, dados.historico(aluno)["ciclo_envio"].get(envio, 1)) + "_Planejamento.pdf"
    com_plan = any(str(r.get("pdf", "")).endswith(nome_pl) for r in aluno.get("relatorios", []))
    return texto_entrega(D, semanas, aluno.get("proxima_atualizacao"), com_plan)


def resultados(slug: str) -> str:
    from . import relatorios
    aluno = A.carregar(slug)
    C = relatorios._contexto(aluno)
    itens = relatorios.itens_auto(aluno, "pos", C)
    sem = C["R"]["semanas"]
    # o bloco que fecha é o da semana atual, o mesmo do PDF de resultados (com o bloco seguinte já na planilha,
    # a mensagem dizia "fechamos" o bloco novo; revisão de 11/out/2026)
    bloco = C["atual"]["bloco"]
    ciclo = C["atual"]["ciclo"]
    prox = next((s["data"] for s in sem if s["ciclo"] == ciclo and s["bloco"] == bloco + 1 and s.get("data")), None)
    if not prox and bloco == C["bloco"] and ciclo == C["ciclo"]:
        prox = aluno.get("proxima_atualizacao")
    return texto_resultados(aluno["nome"], bloco, C["R"].get("rm_evolucao", []), itens, prox)


# ------------------------------------------------------------------ "Para enviar" (ficha do aluno): tudo num lugar só
def para_enviar(slug: str) -> list[dict]:
    """O que mandar ao aluno, com a mensagem pronta (Miguel, 12/out/2026: mensagens e PDFs juntos, num lugar só).
    1) a última entrega: ficha (bloco ou semanas) + o "Seu planejamento" do bloco, se existir; uma mensagem para os dois.
    2) o último PDF de resultados, com a mensagem dele."""
    aluno = A.carregar(slug)
    out = []
    e = next((x for x in aluno.get("entregas", []) if x.get("envio") and x.get("pdf")), None)
    if e:
        n = int(e["bloco"])
        from . import dados
        nome_pl = dados.nome_arquivo(aluno["nome"], n, e.get("ciclo") or 1) + "_Planejamento.pdf"
        pl = next((r for r in aluno.get("relatorios", []) if str(r.get("pdf", "")).endswith(nome_pl)), None)
        if pl and pl.get("data", "") < e.get("data", ""):
            pl = None      # gerado antes desta entrega: mostra outras semanas e outra próxima revisão (revisão de 21/out/2026)
        sem = e.get("semanas")
        rot = (f"Semana {sem[0]:02d}" if len(sem) == 1 else "Semanas " + ", ".join(f"{s:02d}" for s in sem)) if sem else "Ficha"
        # o planejamento acompanha as semanas entregues, então vai também com as semanas avulsas
        pdfs = ([{"rotulo": "Planejamento", "pdf": pl["pdf"]}] if pl else []) + [{"rotulo": rot, "pdf": e["pdf"]}]
        item = {"tipo": "entrega", "titulo": f"Bloco {n:02d}", "data": e.get("data", ""), "pdfs": pdfs,
                "falta_planejamento": not pl}
        try:
            item["texto"] = entrega(slug, e["envio"], sem)
        except Exception as ex:  # noqa: BLE001
            item["erro"] = f"Não consegui montar a mensagem: {ex}"
        out.append(item)
    r = next((x for x in aluno.get("relatorios", []) if x.get("tipo") == "pos"), None)
    if r:
        item = {"tipo": "resultados", "titulo": "Resultados", "data": r.get("data", ""),
                "pdfs": [{"rotulo": "Resultados", "pdf": r["pdf"]}]}
        try:   # o texto gravado junto com o PDF (uma planilha que chegou depois não muda a mensagem do PDF já gerado)
            item["texto"] = r.get("texto") or resultados(slug)
        except Exception as ex:  # noqa: BLE001
            item["erro"] = f"Não consegui montar a mensagem: {ex}"
        out.append(item)
    return out
