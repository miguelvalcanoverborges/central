# -*- coding: utf-8 -*-
"""Mensagens prontas para o WhatsApp (Miguel, 11/out/2026). As regras e os textos ficam no motor
(`motor/consultoria-planilha/scripts/mensagem.py`, o mesmo da skill consultoria-planilha); aqui só se juntam os dados
do aluno na Central:

- ENTREGA: dados.json da ficha (a cópia ajustada; só as semanas escolhidas), próxima revisão do aluno e se o
  planejamento do bloco já foi gerado.
- RESULTADOS: 1RM entre blocos (aba Dados, da planilha original), os itens do PDF pós e o início do próximo bloco.
"""
import json
import re
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
    nome_pl = re.sub(r'[\\/:*?"<>|\s]+', "", aluno["nome"]) + f"_Bloco{n:02d}_Planejamento.pdf"
    com_plan = any(str(r.get("pdf", "")).endswith(nome_pl) for r in aluno.get("relatorios", []))
    return texto_entrega(D, semanas, aluno.get("proxima_atualizacao"), com_plan)


def resultados(slug: str) -> str:
    from . import dados, relatorios
    aluno = A.carregar(slug)
    C = relatorios._contexto(aluno)
    itens = relatorios.itens_auto(aluno, "pos", C)
    sem = C["R"]["semanas"]
    # o bloco que fecha é o da semana atual, o mesmo do PDF de resultados (com o bloco seguinte já na planilha,
    # a mensagem dizia "fechamos" o bloco novo; revisão de 11/out/2026)
    bloco = C["atual"]["bloco"]
    prox = next((s["data"] for s in sem if s["bloco"] == bloco + 1 and s.get("data")), None)
    if not prox and bloco == C["bloco"]:
        prox = aluno.get("proxima_atualizacao")
    return texto_resultados(aluno["nome"], bloco, C["R"].get("rm_evolucao", []), itens, prox)


# ------------------------------------------------------------------ a partir de um PDF aberto no visualizador
def do_pdf(slug: str, rel: str) -> str:
    """A mensagem que acompanha o PDF aberto (Miguel, 12/out/2026: o botão fica junto de qualquer PDF).
    Ficha = entrega daquelas semanas; Planejamento = entrega do bloco (que já cita os 2 PDFs); Resultados = resultados."""
    aluno = A.carregar(slug)
    entregas = aluno.get("entregas", [])
    e = next((x for x in entregas if x.get("pdf") == rel), None)
    if e and e.get("envio"):
        return entrega(slug, e["envio"], e.get("semanas"))
    m = re.search(r"_Bloco(\d+)_Planejamento\.pdf$", rel)
    if m:
        n = int(m.group(1))
        do_bloco = [x for x in entregas if x.get("bloco") == n and x.get("envio")]
        e = next((x for x in do_bloco if not x.get("semanas")), do_bloco[0] if do_bloco else None)
        if not e:
            raise ValueError("Gere a ficha deste bloco primeiro: a mensagem vai junto dos dois PDFs.")
        return entrega(slug, e["envio"], e.get("semanas"))
    if any(r.get("pdf") == rel and r.get("tipo") == "pos" for r in aluno.get("relatorios", [])):
        return resultados(slug)
    raise ValueError("Este PDF não tem mensagem.")
