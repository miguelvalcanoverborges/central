# -*- coding: utf-8 -*-
"""Textos de entrega (app/textos.py) com aluna fictícia montada aqui mesmo. Rodar: python testes/testar_textos.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import textos  # noqa: E402

DIAS = {"T01": "SEGUNDA", "T02": "QUARTA", "T03": "SEXTA"}


def linha(ex, series, reps, kg="", pct=None, obs=""):
    return {"ex": ex, "base": ex, "series": series, "reps": reps, "kg": kg, "pct": pct, "obs": obs}


def semana(n, data, treinos):
    return {"bloco": 2, "semana": n, "global": 4 + n, "data": data, "dias": DIAS, "treinos": treinos}


P = {"semanas": [
    semana(1, "2026-10-12", {"01": [linha("Agachamento", "3", "5", "60", .7, "aquecimento"), linha("Agachamento", "4", "5", "62", .75)],
                             "02": [linha("Supino", "3", "8 - 10", "35")]}),
    semana(2, "2026-10-19", {"01": [linha("Agachamento", "4", "4", "66", .8)]}),
    semana(3, "2026-10-26", {"03": [linha("Terra", "3", "3", "85", .85, "gravar")]}),
    semana(4, "2026-11-02", {"01": [linha("Agachamento", "1", "AMRAP", "70", .82)], "02": [linha("Supino", "1", "5", "40", .82, "amrap")]}),
], "rm_ref": {2: {"Agachamento": {"est": 82.4}, "Supino": {"est": 48.6}, "Terra": {"est": 100.2}}}}
R = {"semanas": [{"bloco": 1, "semana": k, "global": k, "data": f"2026-09-{14 + 7 * (k - 1):02d}", "vtt": 5000, "int": 70} for k in range(1, 3)]
     + [{"bloco": 2, "semana": k, "global": 4 + k, "data": s["data"], "vtt": 6000, "int": 75} for k, s in enumerate(P["semanas"], 1)],
     "rm_evolucao": [{"exercicio": "Agachamento", "blocos": [{"est": 75}, {"est": 82.4}], "variacao": 9.9},
                     {"exercicio": "Supino", "blocos": [{"est": 45}, {"est": 48.6}], "variacao": 8.0},
                     {"exercicio": "Arranco", "blocos": [{"est": 40}], "variacao": None}]}
C = {"P": P, "R": R, "bloco": 2, "atual": R["semanas"][-1], "dias": ["Segunda", "Quarta", "Sexta"]}
aluno = {"slug": "teste", "nome": "Maria Silva", "proxima_atualizacao": "2026-11-09"}
textos.itens_auto = lambda aluno, tipo, C=None: []      # sem anamnese/feedback no teste

pl, fi, re_ = textos.texto_planejamento(aluno, C), textos.texto_ficha(aluno, C), textos.texto_resultados(aluno, C)
for t in (pl, fi, re_):
    print(t, "\n" + "-" * 60)

assert "de 12/out a 08/nov, treinos na segunda, quarta e sexta." in pl
assert "Agachamento (1RM estimado de 82 kg), Supino (49 kg) e Terra (100 kg)" in pl
assert "Na semana 4 (02 a 08/nov) tem teste" in pl
assert "Agachamento 3×5" not in fi, "aquecimento não entra"
assert "*Semana 1 (12 a 18/out)*\n• Quarta, 14/out: Supino 3×8 a 10: anote repetições e carga." in fi
assert "• Segunda, 19/out: Agachamento 4×4 a 80%: grave." in fi
assert "• Sexta, 30/out: Terra 3×3 a 85%: grave." in fi
assert "*Semana 4 (02 a 08/nov), teste*" in fi and "Agachamento: AMRAP com 70 kg. Grave e anote as repetições." in fi
assert "Supino: AMRAP com 40 kg" in fi
assert "Me mande os vídeos e as anotações aqui no dia do treino." in fi
assert "fechamos o Bloco 02." in re_ and "• Agachamento: 75 → 82 kg (+10%)" in re_ and "Arranco" not in re_
assert "Em 6 semanas você levantou 34 mil kg" in re_ and "Próxima revisão: 09/nov." in re_
print("OK: textos de entrega")
