# -*- coding: utf-8 -*-
"""Perguntas dos formulários de Miguel (ANAMNESE e FEEDBACK semanal) → onde cada resposta entra nos PDFs.

As perguntas são encontradas pelo TEXTO (sem depender do número, que muda quando o Forms é refeito).
Nada aqui inventa: "VOCÊ CONTOU / VOCÊ PEDIU" é a resposta do aluno, enxuta; "NO SEU TREINO / O QUE ACONTECEU" só vem
preenchido quando é um fato verificável (dias de treino da planilha, regra fixa da metodologia, resposta de um feedback
mais recente, número do 1RM). O resto fica em branco para Miguel completar.

PDF PRÉ — "Pensado para você" (prioridade, no máximo 4):
  1. motivação  2. dor/lesão  3. disponibilidade  4. preferências  5. outra atividade  6. sono (só se pouco/difícil)
  Fora do PDF por padrão: medicação, diagnósticos, peso, altura, nascimento, profissão, álcool, fumo, contatos.
PDF PÓS — "O que você pediu, o que mudou" (prioridade, no máximo 4):
  1. motivação da anamnese → evolução do 1RM dos exercícios citados
  2. dor (anamnese ou feedback) → último feedback sem dor
  3. sugestão do feedback → (Miguel escreve o que foi ajustado)
  4. dificuldade do feedback → último feedback sem dificuldade
"""
import re
import unicodedata


def sa(s) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").lower()


def _r(pares: list, *padroes: str) -> str:
    """Resposta da pergunta que casa com o primeiro padrão possível ('a&b' = contém a e b). A ordem dos padrões manda:
    o mais específico vem primeiro ("qual regiao" acha a 2.1 antes de "regiao do corpo" achar a 2)."""
    for p in padroes:
        for q, v in pares:
            if all(t in sa(q) for t in p.split("&")):
                return str(v).strip()
    return ""


def _min(v: str) -> str:
    v = str(v or "").strip().rstrip(".")
    return v[:1].lower() + v[1:] if v and not v[:2].isupper() else v


def _regiao(pares: list) -> str:
    r = _r(pares, "qual regiao", "regiao do corpo&qual", "onde e como")
    return "" if negativa(r) or positiva(r) and len(r) <= 4 else r.rstrip(".")


def _nomes(lista: list[str]) -> str:
    return lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " e " + lista[-1]


def citados(texto: str, exercicios: list[str]) -> list[str]:
    """Exercícios do bloco que o aluno citou no texto (pelo nome; 'levantamento terra' = Terra)."""
    t = sa(texto)
    return [x for x in exercicios if sa(x) in t or (sa(x) == "terra" and "terra" in t)]


NEGATIVAS = ("nao", "nenhum", "nenhuma", "nada", "n/a", "sem dor", "nunca", "nao sinto", "nao tenho", "nao pratico")


def negativa(v: str) -> bool:
    n = sa(v).strip(" .!")
    return not n or n in NEGATIVAS or n.startswith(("nao ", "nao,", "nenhum", "nenhuma", "nada"))


def positiva(v: str) -> bool:
    return sa(v).strip().startswith("sim")


def enxuto(v: str, limite: int = 110) -> str:
    v = re.sub(r"\s+", " ", str(v or "")).strip().rstrip(".")
    if v:
        v = v[0].upper() + v[1:]
    if len(v) > limite:
        corte = v[:limite].rsplit(" ", 1)[0].rstrip(",;:")
        v = corte + "…"
    return v


# ------------------------------------------------------------------ ANAMNESE → PDF PRÉ
def itens_pre(anamnese: dict | None, dias_treino: list[str], n_treinos: int, rm_bloco: dict | None = None) -> list[dict]:
    if not anamnese:
        return []
    pares = anamnese["respostas"][0]["pares"]
    data = anamnese["respostas"][0]["data_txt"]
    out = []

    mot = _r(pares, "motivacao", "objetivo")
    if mot and not negativa(mot):
        rm_bloco = {k: v for k, v in (rm_bloco or {}).items() if v}
        cit = citados(mot, list(rm_bloco))[:3]
        treino = ""
        if cit:
            kg = [f"{rm_bloco[x]:.0f}" for x in cit]
            treino = (f"{_nomes([cit[0]] + [c.lower() for c in cit[1:]])} estão neste bloco, com 1RM estimado de {_nomes(kg)} kg."
                      if len(cit) > 1 else f"{cit[0]} está neste bloco, com 1RM estimado de {kg[0]} kg.")
        out.append({"origem": f"anamnese · motivação ({data})", "chave": "motivacao", "aluno": enxuto(mot), "treino": treino})

    dor_sim = _r(pares, "sente dor", "dor ou desconforto")
    regiao = _regiao(pares)
    lesoes = _r(pares, "lesoes", "lesao")
    partes = []
    if positiva(dor_sim) or (regiao and not negativa(regiao)):
        partes.append(f"Dor ou desconforto: {_min(regiao)}" if regiao else "Sente dor ou desconforto")
    if lesoes and not negativa(lesoes):
        partes.append(f"histórico de {_min(lesoes)}" if partes else f"Histórico de {_min(lesoes)}")
    if partes:
        out.append({"origem": f"anamnese · dor e lesões ({data})", "chave": "dor", "aluno": enxuto("; ".join(partes)),
                    "treino": "Os exercícios que envolvem essa região começam com carga conservadora e técnica conferida por vídeo."})

    dias = _r(pares, "dias por semana")
    tempo = _r(pares, "tempo por dia", "tempo disponivel")
    hora = _r(pares, "horarios")
    local = _r(pares, "onde pretende", "onde voce pretende", "local")
    if tempo and "dia" not in sa(tempo) and re.match(r"^\s*[\d,.]+\s*(h|hora|min)", sa(tempo)):
        tempo = f"{tempo.strip()} por dia"
    disp = [x for x in (f"{dias.strip()} dias por semana" if dias and dias.strip().isdigit() else dias, tempo, hora, local)
            if x and not negativa(x)]
    disp = [disp[0]] + [_min(x) for x in disp[1:]] if disp else []
    if disp:
        treino = (f"{n_treinos} treinos por semana ({_nomes([d.lower() for d in dias_treino])}), dentro da sua disponibilidade."
                  if n_treinos and dias_treino else "")
        out.append({"origem": f"anamnese · disponibilidade ({data})", "chave": "rotina", "aluno": enxuto(", ".join(disp)), "treino": treino})

    gosta = _r(pares, "mais gosta")
    evita = _r(pares, "nao gosta", "evita")
    pref = []
    if gosta and not negativa(gosta):
        pref.append(f"Gosta de {_min(gosta)}")
    if evita and not negativa(evita):
        pref.append(f"evita {_min(evita)}" if pref else f"Evita {_min(evita)}")
    if pref:
        out.append({"origem": f"anamnese · preferências ({data})", "chave": "preferencias", "aluno": enxuto("; ".join(pref)), "treino": ""})

    ativ = _r(pares, "tipo de atividade")
    if ativ and not negativa(ativ):
        out.append({"origem": f"anamnese · outras atividades ({data})", "chave": "atividade", "aluno": enxuto(ativ), "treino": ""})

    horas = _r(pares, "horas voce dorme", "horas dorme", "dorme por noite")
    dif = _r(pares, "dificuldade para dormir", "manter o sono")
    m = re.search(r"\d+(?:[.,]\d+)?", horas or "")
    pouco = bool(m and float(m.group(0).replace(",", ".")) < 7)
    if pouco or (dif and not negativa(dif)):
        txt = f"Dorme {horas}" if horas else "Sono"
        if dif and not negativa(dif):
            txt += f"; dificuldade para dormir: {_min(dif)}"
        out.append({"origem": f"anamnese · sono ({data})", "chave": "sono", "aluno": enxuto(txt), "treino": ""})
    return out


# ------------------------------------------------------------------ FEEDBACK (Forms) → texto da semana
def texto_feedback(pares: list) -> str:
    rot = [("adesao", "Adesão"), ("mais gostou", "Gostou"), ("nao gostou&dificuldade", "Dificuldade"),
           ("desconforto ou dor", "Dor ou desconforto"), ("onde e como", "Onde"), ("recuperacao", "Recuperação"),
           ("alinhado", "Alinhado ao objetivo"), ("sugestao", "Sugestão")]
    linhas = []
    for chave, nome in rot:
        v = _r(pares, chave)
        if v:
            linhas.append(f"{nome}: {v}")
    usados = {sa(q) for q, _ in pares if any(all(t in sa(q) for t in c.split("&")) for c, _ in rot)}
    linhas += [f"{q.rstrip(' ?')}: {v}" for q, v in pares if sa(q) not in usados]
    return "\n".join(linhas)


# ------------------------------------------------------------------ FEEDBACK + ANAMNESE → PDF PÓS
def itens_pos(anamnese: dict | None, feedbacks: list[dict], rm_evolucao: list[dict]) -> list[dict]:
    from .relatorios import n0, var
    out = []
    fbs = sorted([f for f in feedbacks if f.get("pares")], key=lambda f: f.get("data") or f.get("registrado_em", ""))
    ultimo = fbs[-1] if fbs else None
    ult_data = (ultimo or {}).get("data_txt", "")

    if anamnese:
        pares = anamnese["respostas"][0]["pares"]
        mot = _r(pares, "motivacao", "objetivo")
        if mot and not negativa(mot):
            evo = {x["exercicio"]: x for x in rm_evolucao if x.get("variacao") is not None}
            cit = [evo[n] for n in citados(mot, list(evo))[:2]]
            res = "; ".join(f"{x['exercicio']}: 1RM estimado de {n0(x['blocos'][0]['est'])} para {n0(x['blocos'][-1]['est'])} kg ({var(x['variacao'])})"
                            for x in cit)
            out.append({"origem": "anamnese · motivação", "chave": "motivacao", "aluno": enxuto(f"Na anamnese: {_min(mot)}"),
                        "resultado": res + "." if res else ""})
        regiao = _regiao(pares)
        if (positiva(_r(pares, "sente dor", "dor ou desconforto")) or (regiao and not negativa(regiao))) and ultimo:
            dor_ult = _r(ultimo["pares"], "desconforto ou dor")
            out.append({"origem": "anamnese · dor", "chave": "dor", "aluno": enxuto(f"Na anamnese, dor ou desconforto: {_min(regiao)}" if regiao else "Na anamnese: sentia dor ou desconforto"),
                        "resultado": f"No feedback de {ult_data}: sem dor ou desconforto." if dor_ult and negativa(dor_ult) else ""})

    for f in reversed(fbs[:-1] if len(fbs) > 1 else fbs):
        sug = _r(f["pares"], "sugestao")
        if sug and not negativa(sug) and not any(i["chave"] == "sugestao" for i in out):
            out.append({"origem": f"feedback · sugestão ({f.get('data_txt', '')})", "chave": "sugestao", "aluno": enxuto(sug), "resultado": ""})
        dif = _r(f["pares"], "nao gostou&dificuldade")
        if dif and not negativa(dif) and not any(i["chave"] == "dificuldade" for i in out):
            dif_ult = _r(ultimo["pares"], "nao gostou&dificuldade") if ultimo is not f else ""
            out.append({"origem": f"feedback · dificuldade ({f.get('data_txt', '')})", "chave": "dificuldade",
                        "aluno": enxuto(f"Dificuldade: {_min(dif)}"),
                        "resultado": f"No feedback de {ult_data}: nenhuma dificuldade relatada." if dif_ult and negativa(dif_ult) else ""})
        dor = _r(f["pares"], "desconforto ou dor")
        onde = _r(f["pares"], "onde e como")
        if positiva(dor) and not any(i["chave"] == "dor" for i in out):
            dor_ult = _r(ultimo["pares"], "desconforto ou dor") if ultimo is not f else ""
            out.append({"origem": f"feedback · dor ({f.get('data_txt', '')})", "chave": "dor",
                        "aluno": enxuto(f"Desconforto: {_min(onde)}" if onde else "Sentiu desconforto no treino"),
                        "resultado": f"No feedback de {ult_data}: sem dor ou desconforto." if dor_ult and negativa(dor_ult) else ""})
    ordem = {"motivacao": 0, "dor": 1, "sugestao": 2, "dificuldade": 3}
    out.sort(key=lambda i: ordem.get(i["chave"], 9))
    return out


# ------------------------------------------------------------------ triagem do feedback: só o que pede ação
RUINS = ("ruim", "pessim", "baixa", "fraca", "regular", "nao treinei", "nao fiz", "cansad", "pouco")


def _ruim(v: str) -> bool:
    n = sa(v)
    return bool(n) and any(t in n for t in RUINS)


def triagem(pares: list) -> list[dict]:
    """Pontos do feedback que pedem atenção de Miguel: dor, adesão baixa, desalinhado ao objetivo, sugestão,
    recuperação ruim. Feedback "tudo certo" devolve lista vazia."""
    out = []
    dor, onde = _r(pares, "desconforto ou dor"), _r(pares, "onde e como")
    if positiva(dor) or (onde and not negativa(onde)):
        out.append({"tipo": "dor", "texto": f"Dor: {_min(onde)}" if onde and not negativa(onde) else "Dor ou desconforto"})
    ades = _r(pares, "adesao")
    if _ruim(ades):
        out.append({"tipo": "adesao", "texto": f"Adesão: {_min(ades)}"})
    alin = _r(pares, "alinhado")
    if alin and negativa(alin):
        out.append({"tipo": "objetivo", "texto": "Não está alinhado com o objetivo"})
    sug = _r(pares, "sugestao")
    if sug and not negativa(sug) and not sa(sug).startswith(("nenhuma", "nada", "esta otimo", "ta otimo", "tudo certo")):
        out.append({"tipo": "sugestao", "texto": f"Sugestão: {_min(sug)}"})
    rec = _r(pares, "recuperacao")
    if _ruim(rec):
        out.append({"tipo": "recuperacao", "texto": f"Recuperação: {_min(rec)}"})
    return out
