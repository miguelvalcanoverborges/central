# -*- coding: utf-8 -*-
"""PDFs para o aluno, a partir da aba DADOS.

  PRÉ  — "Seu planejamento": sem capa (Miguel, 9/out/2026), 2 páginas (Miguel, 18/out/2026: a 2ª é "Como ler a sua
         ficha", que saiu da ficha na v1.15), individualizada: o ciclo segue o plano
         contratado (mensal = só o bloco; trimestral = 3 blocos), "Como vamos acompanhar" só mostra Anotar, Gravar e
         Teste (AMRAP) se o bloco tiver. Arquivo "MariaSilva_Bloco02_Planejamento.pdf", substituído ao gerar de novo.
  PÓS  — "Sua evolução": capa no desenho da capa da ficha (template mestre, sem alterá-lo) + 1 página com
         resultados e evoluções até a semana atual

Regras (skill consultoria-planilha / metodologia de Miguel): sem promessas, sem linguagem de guru, sem enquadrar como
estética; números só da planilha (o planejado); da anamnese e do feedback o programa escolhe sozinho os itens
pessoais (no máximo 4, só com fato verificável na 2ª parte, cada texto em até 2 linhas, sem palavra solta).
"""
import datetime as dt
import html
import re
import sys

from . import armazenamento as A
from . import dados, individual, planos
from .config import SCRIPTS

sys.path.insert(0, str(SCRIPTS))
import template_mestre as T  # noqa: E402

e = html.escape
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
         "novembro", "dezembro"]
CHROMIUM_ARGS = ["--font-render-hinting=none"]   # mesma renderização fixa do gerador da ficha
CINZA_PLAN, CINZA_FUT, PRETO, GRADE = "#9a9892", "#e3e1db", "#000000", "#e6e6e2"


# ------------------------------------------------------------------ formatação pt-BR
def n0(v) -> str:
    return f"{v:,.0f}".replace(",", ".") if v is not None else "—"


def n1(v) -> str:
    return f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") if v is not None else "—"


def pct(v) -> str:
    return f"{n0(v)}%" if v is not None else "—"


def var(v) -> str:
    if v is None:
        return ""
    return ("+" if v > 0 else "−" if v < 0 else "±") + f"{n0(abs(v))}%"


def kg_txt(v) -> str:
    if v is None:
        return "—"
    return (str(int(v)) if float(v).is_integer() else str(v).replace(".", ",")) + " kg"


def data_br(iso: str, ano=True) -> str:
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso[:10])
    return d.strftime("%d/%m/%Y" if ano else "%d/%m")


def mes_ano(d: dt.date) -> str:
    return f"{MESES[d.month - 1]} de {d.year}"


# ------------------------------------------------------------------ gráficos SVG (tons de cinza, Exo)
def _escala(maximo, minimo=0.0, n=4):
    if maximo <= minimo:
        maximo = minimo + 1
    bruto = (maximo - minimo) / n
    import math
    mag = 10 ** math.floor(math.log10(bruto))
    passo = next(p * mag for p in (1, 2, 2.5, 5, 10) if p * mag >= bruto)
    ini = math.floor(minimo / passo) * passo
    fim = math.ceil(maximo / passo) * passo
    ticks, v = [], ini
    while v <= fim + 1e-9:
        ticks.append(round(v, 6))
        v += passo
    return ini, fim, ticks


def _col(x, y, w, h):
    if h <= 0.5:
        return f"M{x},{y + h}h{w}"
    r = min(3, w / 2, h)
    return f"M{x},{y + h}V{y + r}Q{x},{y} {x + r},{y}H{x + w - r}Q{x + w},{y} {x + w},{y + r}V{y + h}Z"


def svg_colunas(pontos, w=330, h=112, fmt_eixo=n0, destaque=None):
    """pontos: [{rotulo, bloco, valor, cor}] — cor: 'real' | 'plan' | 'fut'."""
    m = {"t": 10, "r": 4, "b": 30, "l": 40}
    iw, ih = w - m["l"] - m["r"], h - m["t"] - m["b"]
    ini, fim, ticks = _escala(max([p["valor"] or 0 for p in pontos] + [1]) * 1.06)
    Y = lambda v: m["t"] + ih - (v - ini) / (fim - ini) * ih  # noqa: E731
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for t in ticks:
        out.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}" stroke-width="1"/>')
        out.append(f'<text x="{m["l"] - 5}" y="{Y(t) + 3:.1f}" text-anchor="end" class="ax">{fmt_eixo(t)}</text>')
    banda = iw / max(len(pontos), 1)
    bw = min(16, banda * 0.6)
    for i, p in enumerate(pontos):
        cx = m["l"] + banda * i + banda / 2
        if destaque is not None and p.get("g") == destaque:
            out.append(f'<rect x="{m["l"] + banda * i + 1:.1f}" y="{m["t"] - 4}" width="{banda - 2:.1f}" height="{ih + 4}" rx="3" fill="#f1f0eb"/>')
        v = p["valor"] or 0
        if p["cor"] == "fut":
            out.append(f'<path d="{_col(cx - bw / 2, Y(v), bw, Y(0) - Y(v))}" fill="#fff" stroke="#c9c6bd" stroke-width="1"/>')
        else:
            out.append(f'<path d="{_col(cx - bw / 2, Y(v), bw, Y(0) - Y(v))}" fill="{PRETO if p["cor"] == "real" else CINZA_PLAN}"/>')
        out.append(f'<text x="{cx:.1f}" y="{h - m["b"] + 11}" text-anchor="middle" class="ax{" axs" if p.get("g") == destaque else ""}">{e(p["rotulo"])}</text>')
    blocos = []
    for i, p in enumerate(pontos):
        if not blocos or blocos[-1][0] != p["bloco"]:
            blocos.append([p["bloco"], i, i])
        blocos[-1][2] = i
    for b, i0, i1 in blocos:
        x0, x1 = m["l"] + banda * i0 + 3, m["l"] + banda * (i1 + 1) - 3
        out.append(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{h - 11}" y2="{h - 11}" stroke="{GRADE}" stroke-width="1"/>')
        out.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{h - 2}" text-anchor="middle" class="ax axb">Bloco {b:02d}</text>')
    out.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(0):.1f}" y2="{Y(0):.1f}" stroke="#c9c6bd" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def svg_linha(pontos, w=330, h=112, destaque=None):
    """pontos: [{rotulo, bloco, valor(% ou None), cor}] — linha preta, pontos futuros em contorno."""
    m = {"t": 10, "r": 6, "b": 30, "l": 40}
    iw, ih = w - m["l"] - m["r"], h - m["t"] - m["b"]
    vals = [p["valor"] for p in pontos if p["valor"] is not None]
    if not vals:
        return ""
    ini, fim, ticks = _escala(max(vals) + 2, max(0, min(vals) - 4))
    Y = lambda v: m["t"] + ih - (v - ini) / (fim - ini) * ih  # noqa: E731
    banda = iw / max(len(pontos), 1)
    X = lambda i: m["l"] + banda * i + banda / 2  # noqa: E731
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for t in ticks:
        out.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" stroke="{GRADE}" stroke-width="1"/>')
        out.append(f'<text x="{m["l"] - 5}" y="{Y(t) + 3:.1f}" text-anchor="end" class="ax">{n0(t)}%</text>')
    for i, p in enumerate(pontos):
        if destaque is not None and p.get("g") == destaque:
            out.append(f'<rect x="{m["l"] + banda * i + 1:.1f}" y="{m["t"] - 4}" width="{banda - 2:.1f}" height="{ih + 4}" rx="3" fill="#f1f0eb"/>')
    # linha: trecho até a semana atual em preto; daí para a frente (planejado futuro) em cinza claro
    validos = [i for i, p in enumerate(pontos) if p["valor"] is not None]
    for a_, b_ in zip(validos, validos[1:]):
        cor = "#c9c6bd" if pontos[b_]["cor"] == "fut" else PRETO
        out.append(f'<line x1="{X(a_):.1f}" y1="{Y(pontos[a_]["valor"]):.1f}" x2="{X(b_):.1f}" y2="{Y(pontos[b_]["valor"]):.1f}" '
                   f'stroke="{cor}" stroke-width="2" stroke-linecap="round"/>')
    for i, p in enumerate(pontos):
        if p["valor"] is not None:
            if p["cor"] == "fut":
                out.append(f'<circle cx="{X(i):.1f}" cy="{Y(p["valor"]):.1f}" r="3" fill="#fff" stroke="#c9c6bd" stroke-width="1.5"/>')
            else:
                out.append(f'<circle cx="{X(i):.1f}" cy="{Y(p["valor"]):.1f}" r="3.5" fill="{PRETO if p["cor"] == "real" else CINZA_PLAN}" stroke="#fff" stroke-width="1.5"/>')
        out.append(f'<text x="{X(i):.1f}" y="{h - m["b"] + 11}" text-anchor="middle" class="ax{" axs" if p.get("g") == destaque else ""}">{e(p["rotulo"])}</text>')
    blocos = []
    for i, p in enumerate(pontos):
        if not blocos or blocos[-1][0] != p["bloco"]:
            blocos.append([p["bloco"], i, i])
        blocos[-1][2] = i
    for b, i0, i1 in blocos:
        x0, x1 = m["l"] + banda * i0 + 3, m["l"] + banda * (i1 + 1) - 3
        out.append(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{h - 11}" y2="{h - 11}" stroke="{GRADE}" stroke-width="1"/>')
        out.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{h - 2}" text-anchor="middle" class="ax axb">Bloco {b:02d}</text>')
    out.append("</svg>")
    return "".join(out)


def svg_feedback(linha: list[dict], w=680, destaque=None) -> str:
    """Linha do tempo do feedback semanal (Miguel, 16/out/2026): uma faixa por pergunta, semana a semana, no mesmo eixo
    S01…S12 e com a mesma marcação de blocos dos gráficos de cima. Cada ponto sobe de 1 (atenção) a 3 (bom); em "Sem dor"
    mais alto = menos dor. Semana sem resposta não tem ponto (nada é suposto). Vazio se não houver nenhuma nota."""
    from .formularios import INDICADORES
    if not linha or not any(p["notas"] and any(v for v in p["notas"].values()) for p in linha):
        return ""
    rh, gap = 16, 3                                   # altura de cada faixa (compacta: cabe com "Sua força estimada")
    m = {"t": 4, "r": 4, "b": 30, "l": 104}
    h = m["t"] + len(INDICADORES) * (rh + gap) - gap + m["b"]
    iw = w - m["l"] - m["r"]
    banda = iw / len(linha)
    X = lambda i: m["l"] + banda * i + banda / 2      # noqa: E731
    estilo = "font-family:inherit"
    out = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="{estilo}">']
    for k in range(len(INDICADORES)):              # fundo das faixas; a semana atual fica marcada por cima dele
        out.append(f'<rect x="{m["l"]}" y="{m["t"] + k * (rh + gap)}" width="{iw}" height="{rh}" rx="3" fill="#f7f6f2"/>')
    for i, p in enumerate(linha):
        if destaque is not None and p["global"] == destaque:
            out.append(f'<rect x="{m["l"] + banda * i + 1:.1f}" y="0" width="{banda - 2:.1f}" height="{h - m["b"] + 2}" rx="3" fill="#e9e7e0"/>')
    for k, (chave, nome) in enumerate(INDICADORES):
        y0 = m["t"] + k * (rh + gap)
        Y = lambda n: y0 + rh - 4 - (n - 1) * (rh - 8) / 2      # noqa: E731  nota 1 embaixo, 3 em cima
        out.append(f'<line x1="{m["l"] + 3}" x2="{w - m["r"] - 3}" y1="{Y(3):.1f}" y2="{Y(3):.1f}" stroke="{GRADE}" stroke-width="1" stroke-dasharray="2 3"/>')
        out.append(f'<text x="{m["l"] - 8}" y="{y0 + rh / 2 + 3:.1f}" text-anchor="end" class="ax fbn" '
                   f'style="font-size:8.5px;font-weight:700;fill:#000">{e(nome)}</text>')
        pts = [(i, p["notas"].get(chave)) for i, p in enumerate(linha) if p["notas"] and p["notas"].get(chave)]
        for (a_, va), (b_, vb) in zip(pts, pts[1:]):
            tracejado = ' stroke-dasharray="3 3"' if b_ - a_ > 1 else ""   # semana sem resposta no meio
            out.append(f'<line x1="{X(a_):.1f}" y1="{Y(va):.1f}" x2="{X(b_):.1f}" y2="{Y(vb):.1f}" stroke="#000" '
                       f'stroke-width="1.6" stroke-linecap="round"{tracejado}/>')
        for i, v in pts:
            if v == 1:     # atenção: anel, para ser visto sem depender de cor
                out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.2" fill="#fff" stroke="#000" stroke-width="1.6"/>')
            else:
                out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.1" fill="{PRETO if v == 3 else CINZA_PLAN}" stroke="#fff" stroke-width="1.2"/>')
    yb = h - m["b"]
    for i, p in enumerate(linha):
        out.append(f'<text x="{X(i):.1f}" y="{yb + 11}" text-anchor="middle" class="ax{" axs" if p["global"] == destaque else ""}" '
                   f'style="font-size:7.5px;fill:{"#000" if p["global"] == destaque else "#6f6f6a"}">{e(p["rotulo"])}</text>')
    blocos = []
    for i, p in enumerate(linha):
        if not blocos or blocos[-1][0] != p["bloco"]:
            blocos.append([p["bloco"], i, i])
        blocos[-1][2] = i
    for b, i0, i1 in blocos:
        x0, x1 = m["l"] + banda * i0 + 3, m["l"] + banda * (i1 + 1) - 3
        out.append(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{h - 11}" y2="{h - 11}" stroke="{GRADE}" stroke-width="1"/>')
        out.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{h - 2}" text-anchor="middle" class="ax axb" style="font-size:7px;fill:#9a9a94">Bloco {b:02d}</text>')
    out.append("</svg>")
    return "".join(out)


# Tabela "Como você se sentiu" do PDF de Resultados (Miguel, 16/out/2026: escolhida a tabela com palavras, mais
# objetiva que gráfico; "Treino × objetivo" fica só na Central). Uma linha por semana feita (no máximo as 12 últimas).
PDF_FEEDBACK = [("adesao", "Treinos", ("Tudo feito", "Parcial", "Não treinou")),
                ("sono", "Sono", ("Bom", "Regular", "Ruim")),
                ("dor", "Dor", ("Sem dor", "Leve", "Intensa")),
                ("recuperacao", "Recuperação", ("Boa", "Regular", "Ruim"))]
MAX_SEMANAS_FB = 12


def tabela_feedback(linha: list[dict], atual_g: int) -> str:
    feitas = [p for p in linha if not p.get("futura")]
    if not any(p["notas"] and any(p["notas"].get(k) for k, _, _ in PDF_FEEDBACK) for p in feitas):
        return ""                                     # sem nenhuma resposta: a seção não entra
    cortadas = len(feitas) > MAX_SEMANAS_FB
    feitas = feitas[-MAX_SEMANAS_FB:]
    head = "<tr><th>Semana</th>" + "".join(f"<th>{e(t)}</th>" for _, t, _ in PDF_FEEDBACK) + "</tr>"
    linhas = []
    for p in feitas:
        cel = []
        for k, _, rot in PDF_FEEDBACK:
            v = (p["notas"] or {}).get(k)
            cel.append(f'<td><span class="chip c{v}">{e(rot[3 - v])}</span></td>' if v else '<td><span class="sem-resp">—</span></td>')
        linhas.append(f'<tr class="{"atual" if p["global"] == atual_g else ""}"><td>S{p["global"]:02d}<small>bloco {p["bloco"]:02d}</small></td>{"".join(cel)}</tr>')
    sub_ = f"as últimas {MAX_SEMANAS_FB} semanas" if cortadas else "semana a semana"   # sem legenda (Miguel, 16/out/2026)
    return (f'<h3>COMO VOCÊ SE SENTIU</h3><p class="intro">Suas respostas no feedback semanal, {sub_}.</p>'
            f'<table class="tsem">{head}{"".join(linhas)}</table>')



def mil(v):
    return f"{n0(v / 1000)} mil" if v >= 1000 else n0(v)


# ------------------------------------------------------------------ peças comuns
CSS_EXTRA = """
.pv{ display:grid; border-top:.3mm solid #000; }
.pv .par{ display:grid; grid-template-columns:34mm 1fr; gap:4mm; background:none; border:0; border-bottom:.25mm solid #e2e2de; border-radius:0; padding:2.6mm 0; }
.pv .par small{ font-size:6.2pt; margin:.6mm 0 0; } .pv .par p{ font-size:8.8pt; margin:0; color:#333; }
.pv .par p.forte{ margin-top:.8mm; color:#000; } .pv .par p.forte::before{ content:"→ "; }
.faltou{ display:flex; justify-content:space-between; align-items:center; gap:6mm; background:#000; color:#fff; border-radius:3mm; padding:4mm 5mm; }
.faltou b{ display:block; font:400 11pt 'Krona'; } .faltou p{ font:500 8.6pt/1.4 'Exo'; color:#cfcfcf; margin-top:1.2mm; }
.faltou .seq{ display:flex; align-items:center; gap:1.6mm; white-space:nowrap; font:700 7.4pt 'Exo'; }
.faltou .seq span{ border:.35mm solid #fff; border-radius:5mm; padding:1mm 2.4mm; } .faltou .seq i{ font-style:normal; color:#8a8a8a; }
.exlinha .treino{ margin-bottom:2.5mm; }
.lido{ font:400 9pt/1.5 'Exo'; color:#333; border-left:1mm solid #000; padding:.4mm 0 .4mm 3mm; margin-bottom:2mm; }
.lido b{ font-weight:800; color:#000; }
.legend .play{ font:400 9pt 'Exo'; }
.ttl p{ text-transform:none; letter-spacing:.02em; }
.intro{ font:400 9.4pt/1.5 'Exo'; color:#333; margin-bottom:4mm; }
.prof4{ display:grid; grid-template-columns:repeat(4,1fr); gap:4mm 6mm; padding:4.2mm 6mm; }
.prof4 b{ font:700 9.6pt/1.3 'Exo'; } .prof4 b span{ display:block; font:500 8pt 'Exo'; color:#6b6b6b; margin-top:.6mm; }
h3{ margin:5mm 0 2.5mm; }
.dois{ display:grid; grid-template-columns:1fr 1fr; gap:6mm; }
.graf{ border:.3mm solid #e2e2de; border-radius:3mm; padding:3.5mm 3mm 2mm; }
.graf h4{ font:800 7.6pt 'Exo'; letter-spacing:.12em; text-transform:uppercase; margin:0 0 1.5mm 1mm; }
.h4s{ font:500 7.2pt 'Exo'; letter-spacing:0; text-transform:none; color:#8a8a86; }
.graf p{ font:400 8.2pt/1.4 'Exo'; color:#444; margin:1.5mm 1mm 0; }
.graf svg{ display:block; width:100%; height:auto; }
.ax{ font:500 7.5px 'Exo'; fill:#6f6f6a; } .axs{ fill:#000; font-weight:800; } .axb{ fill:#9a9a94; font-size:7px; }
.leg{ display:flex; gap:4mm; font:500 7.2pt 'Exo'; color:#555; margin:1mm 1mm 0; }
.leg i{ display:inline-block; width:2.4mm; height:2.8mm; border-radius:.6mm .6mm 0 0; margin-right:1.2mm; vertical-align:-.3mm; }
.linha-tempo{ display:grid; gap:2.5mm; }
.blocos{ display:grid; gap:3mm; }
.bloco{ border-radius:3mm; padding:2.8mm 4mm; background:#f4f4f1; }
.bloco.atual{ background:#000; color:#fff; }
.bloco.futuro{ background:#fff; border:.3mm dashed #c9c6bd; }
.bloco small{ margin-bottom:.8mm; } .bloco.atual small{ color:#9a9a9a; }
.bloco b{ display:block; font:400 10pt 'Krona'; }
.bloco span{ display:block; font:500 7.6pt/1.35 'Exo'; margin-top:.8mm; color:#555; } .bloco.atual span{ color:#cfcfcf; }
.semanas{ display:grid; gap:1.2mm; margin-top:2mm; }
.semanas i{ display:block; height:2.2mm; border-radius:1mm; background:#d9d7d0; }
.semanas i.feita{ background:#6f6d66; } .bloco.atual .semanas i{ background:#555; } .bloco.atual .semanas i.feita{ background:#fff; }
.semanas i.agora{ background:#fff; outline:.5mm solid #fff; box-shadow:0 0 0 .8mm #000 inset; }
.tab{ width:100%; border-collapse:collapse; }
.tab th{ font:700 6.2pt 'Exo'; letter-spacing:.18em; color:#8a8a86; padding:2mm 1.5mm; text-align:left; background:#f4f4f1; }
.tab th.n, .tab td.n{ text-align:right; }
.tab td{ height:auto; padding:1.25mm 1.5mm; border-bottom:.25mm solid #e6e6e2; font:500 9pt 'Exo'; text-align:left; }
.tab td b{ font-weight:800; }
.tab td.n{ font-variant-numeric:tabular-nums; white-space:nowrap; }
.passos{ display:grid; grid-template-columns:1fr 1fr; gap:2.5mm 6mm; }
.passos div{ border-left:1mm solid #000; padding:.4mm 0 .4mm 3mm; font:400 8.6pt/1.4 'Exo'; color:#333; }
.passos.p4{ grid-template-columns:repeat(4,1fr); gap:3mm 4mm; }
.passos.p4 div{ font-size:8.2pt; }
.passos div b{ display:block; font:800 7.8pt 'Exo'; letter-spacing:.06em; text-transform:uppercase; color:#000; margin-bottom:.6mm; }
.dest{ display:grid; grid-template-columns:repeat(4,1fr); gap:3.5mm; }
.dest .rm b{ font-size:20pt; margin:2.5mm 0 2mm; white-space:nowrap; }
.dest .rm b i{ font-size:8pt; }
.dest .rm span{ font-size:7.2pt; } .dest .rm em{ font-size:8pt; line-height:1.35; }
.forca{ display:grid; gap:2.6mm; }
.cinza{ color:#8a8a86; font-weight:500; font-size:8pt; }
.forca .f{ display:grid; grid-template-columns:32mm 1fr 16mm; gap:3mm; align-items:center; }
.forca .f > b{ font:800 9pt 'Exo'; }
.forca .barras{ display:grid; gap:.4mm; }
.forca .barras div{ display:grid; grid-template-columns:12mm 1fr 15mm; gap:2mm; align-items:center; font:500 7pt/1.2 'Exo'; color:#666; }
.forca .barras s{ display:block; height:1.8mm; background:#c9c6bd; border-radius:0 1mm 1mm 0; text-decoration:none; }
.forca .barras div:last-child s{ background:#000; }
.forca .barras em{ font:700 7.6pt 'Exo'; font-style:normal; color:#000; text-align:right; }
.forca .ev{ font:400 12pt 'Krona'; text-align:right; }
.nota{ font:400 7.8pt/1.45 'Exo'; color:#777; margin-top:2.5mm; }
.rm1s{ display:grid; grid-template-columns:repeat(4,1fr); gap:2.5mm; }
.rm1{ display:flex; justify-content:space-between; align-items:baseline; gap:2mm; background:#f4f4f1; border-radius:2.5mm; padding:3mm 3.5mm; }
.rm1 span{ font:700 8.8pt/1.25 'Exo'; } .rm1 b{ font:400 12pt 'Krona'; white-space:nowrap; }
.fcs{ display:grid; gap:3mm; }
.fc{ background:#f4f4f1; border-radius:2.5mm; padding:3mm 3.5mm; display:grid; gap:.6mm; }
.fc span{ font:800 8.6pt 'Exo'; } .fc b{ font:400 15pt/1.1 'Krona'; }
.fc em{ font:700 8.4pt 'Exo'; font-style:normal; } .fc i{ font:500 6.8pt 'Exo'; font-style:normal; color:#8a8a86; }
.pares{ display:grid; grid-template-columns:1fr 1fr; gap:2.5mm; }
.par{ border-left:1mm solid #000; background:#f4f4f1; border-radius:0 2.5mm 2.5mm 0; padding:2.4mm 3.5mm; }
.par small{ font-size:5.8pt; margin-bottom:.8mm; }
.par p{ font:400 8.2pt/1.35 'Exo'; color:#444; margin-bottom:1.4mm; } .par p.forte{ font-weight:700; color:#000; margin-bottom:0; }
.chip{ display:inline-block; min-width:16mm; text-align:center; font:700 7.6pt 'Exo'; padding:1.1mm 2mm; border-radius:5mm; }
.chip.c3{ background:#000; color:#fff; } .chip.c2{ background:#d9d7d0; color:#000; } .chip.c1{ background:#fff; color:#000; box-shadow:inset 0 0 0 .35mm #000; }
.sem-resp{ color:#b5b3ab; font:500 8pt 'Exo'; }
.tsem{ width:100%; border-collapse:separate; border-spacing:0 1.4mm; }
.tsem th{ font:700 6.4pt 'Exo'; letter-spacing:.14em; color:#8a8a86; text-transform:uppercase; text-align:center; padding:0 1mm 1mm; background:none; }
.tsem th:first-child, .tsem td:first-child{ text-align:left; }
.tsem td{ text-align:center; padding:1.3mm 1mm; background:#f4f4f1; height:auto; border:0; }
.tsem td:first-child{ border-radius:2mm 0 0 2mm; font:400 9pt 'Krona'; padding-left:3mm; }
.tsem td:last-child{ border-radius:0 2mm 2mm 0; }
.tsem td small{ display:block; font:500 6.4pt 'Exo'; color:#8a8a86; margin-top:.4mm; }
.tsem tr.atual td{ background:#ebe9e2; }

.fecho{ margin-top:5mm; font:500 italic 9pt/1.5 'Exo'; color:#555; }
"""


def sem_viuva(txt: str) -> str:
    """Escapa o texto e une as duas últimas palavras com espaço inseparável: a última linha nunca fica com uma palavra só."""
    t = e(re.sub(r"\s+", " ", txt or "").strip())
    i = t.rfind(" ")
    return t[:i] + "&nbsp;" + t[i + 1:] if i > 0 else t


def _capa(kick: str, titulo: str, nome: str, data: str) -> str:
    GOR, HALF = T._b64("gorilla_white.png", "image/png"), T._b64("halftone.png", "image/png")
    cmeta = f'<div class="cmeta"><b>{e(data)}</b></div>' if data else ""
    return f'''<div class="page dark cover">
  <img class="half" src="{HALF}">
  <img class="cg" src="{GOR}">
  <div class="tag">FORÇA &amp; INTELIGÊNCIA</div>
  <div class="ct">
    <div class="kick">{e(kick)}</div>
    <h1 class="glow">{e(titulo)}</h1>
    <div class="name">{e(nome)}</div>
  </div>
  {cmeta}
  <div class="cfoot"><b>Miguel Valcanover</b> <em>· Treinador</em><br><span>{T.IG} · {T.PHONE}</span></div>
</div>'''


def _pagina(titulo: str, sub: str, corpo: str, nome: str, rodape: str, num: str = "02") -> str:
    GOR = T._b64("gorilla_white.png", "image/png")
    return f'''<div class="page light">{T.header(titulo, e(sub), GOR)}
  <div class="body">{corpo}</div>
  <div class="ftr"><span>{e(nome)} · {e(rodape)}</span><span>Miguel Valcanover · Treinador · {T.IG}</span><span class="pg">{num}</span></div></div>'''


def _doc(titulo: str, paginas: str) -> str:
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{e(titulo)}</title>'
            f'<style>{T.css()}{CSS_EXTRA}</style></head><body>{paginas}</body></html>')


def _contexto(aluno: dict) -> dict:
    planilha = dados.planilha_atual(aluno)
    if not planilha:
        raise ValueError("Este aluno ainda não tem planilha matriz lida.")
    P = dados.ler_planilha(planilha)
    R = dados.analisar(planilha)
    if not R["semanas"]:
        raise ValueError("A planilha não tem semanas prescritas.")
    hoje = dt.date.today()
    sem = R["semanas"]
    atual = next((s for s in sem if s["atual"]), None)
    if not atual:
        iniciadas = [s for s in sem if s["data"] and dt.date.fromisoformat(s["data"]) <= hoje]
        atual = iniciadas[-1] if iniciadas else sem[0]
    bloco = aluno.get("bloco_atual") or max(s["bloco"] for s in sem)
    dias_bloco = next((s["dias"] for s in reversed(P["semanas"]) if s["bloco"] == bloco), {}) or P["semanas"][-1]["dias"]
    ordem = dados.DIAS_ORDEM
    dias = sorted(dias_bloco.values(), key=lambda d: ordem.index(d) if d in ordem else 99)
    return {"P": P, "R": R, "hoje": hoje, "atual": atual, "bloco": bloco, "dias": [dados.DIA_CURTO.get(d, d.title()) for d in dias]}


def _cor_semana(s, atual_g, hoje):
    """real = semana já feita ou em andamento (preto); fut = ainda vai acontecer (contorno)."""
    return "real" if s["global"] <= atual_g else "fut"


# ------------------------------------------------------------------ "Como ler a sua ficha" (2ª página do planejamento)
def _ficha_do_bloco(aluno: dict, bloco: int) -> dict | None:
    """Dados da ficha entregue deste bloco (dados.json do envio mais recente do bloco, já com o aquecimento da Central):
    a legenda explica o que a FICHA mostra, não a planilha original."""
    import json
    for p in aluno.get("planilhas", []):
        if p.get("bloco") == bloco:
            arq = A.pasta(aluno["slug"]) / "trabalho" / p["id"] / "dados.json"
            if arq.exists():
                return json.loads(arq.read_text(encoding="utf-8"))
    return None


def _ler_linha(r: dict) -> str:
    """A linha de exemplo lida em palavras, só com o que está na ficha."""
    reps = T.fmt_reps(r["reps"])
    txt = f'{T.fmt(r["sets"])} séries de {e(reps)} repetições' + (f' com {T.fmt(r["kg"])}&nbsp;kg' if r.get("kg") else "")
    if r.get("pct") is not None:
        txt += f', {round(r["pct"] * 100)}% do seu 1RM'
    if r.get("_aq"):
        txt += ". Antes delas, o aquecimento: " + ", depois ".join(
            (f'{T.fmt(a["sets"])} séries de {e(T.fmt_reps(a["reps"]))}' if (a.get("sets") or 1) > 1 else f'1 série de {e(T.fmt_reps(a["reps"]))}')
            + (f' com {T.fmt(a["kg"])}&nbsp;kg' if a.get("kg") else "") for a in r["_aq"])
    return txt + "."


def html_como_ler(D: dict | None) -> str:
    """Mesma legenda que a ficha tinha na 2ª página (textos do template até a v1.14), só com o que aparece na ficha deste
    bloco, mais uma linha real da ficha lida em palavras. Sem planilha lida, não há página."""
    if not D or not D.get("semanas"):
        return ""
    semanas = D["semanas"]
    linhas = [r for s in semanas for rows in s["treinos"].values() for r in rows]
    obs = lambda r: str(r.get("obs") or "").lower()
    etiq = {k for r in linhas for k in T.TAGS if f'pill {T.TAGS[k][0]}">{T.TAGS[k][1]}<' in T.pills(r["obs"])}
    tem_carga = any(r["kg"] for r in linhas)
    tem_pct = any(r["pct"] is not None for r in linhas)
    tem_amrap = any("amrap" in (str(r["reps"]).lower() + " " + obs(r)) for r in linhas)
    itens = [
        (True, "<b>SÉRIES</b>", "Quantas vezes você repete o conjunto de repetições, fazendo uma série depois da outra."),
        (True, "<b>REPS</b>", "Quantas repetições fazer em cada série. Se houver faixa, faça dentro do intervalo indicado."),
        (tem_carga, "<b>CARGA</b>", "Peso total do exercício, em quilos. Na barra livre, some o peso da barra com o das anilhas."),
        (tem_pct, "<b>%1RM</b>", "Intensidade da carga em relação ao seu 1RM, ou seja, sua carga máxima em uma repetição."),
        ("anotar" in etiq, '<span class="pill solid">Anotar</span>', "Anote as repetições e a carga que você usou em cada série, para eu ajustar a sua progressão."),
        ("aquecimento" in etiq, '<span class="pill ghost">Aquecimento</span>', "Séries leves de preparo, na linha cinza abaixo do exercício: 55&nbsp;kg&nbsp;×&nbsp;3 = 1 série de 3 reps com 55&nbsp;kg."),
        ("principal" in etiq, '<span class="pill line">Principal</span>', "Série de trabalho do exercício, feita com a carga prescrita e com atenção total à técnica."),
        ("gravar" in etiq, '<span class="pill solid rec">Gravar</span>', "Grave essa série em vídeo e envie para eu analisar sua técnica e ajustar as suas cargas."),
        ("biset" in etiq, '<span class="pill line">Biset</span>', "Dois exercícios feitos em sequência, um logo após o outro, na ordem em que aparecem na ficha."),
        (tem_amrap, "<b>AMRAP</b>", "O máximo de repetições possível na série, sempre mantendo a boa técnica de execução."),
        (any(r.get("link") for r in linhas), '<b class="play">▶</b>', "Toque no ícone para ver o vídeo do exercício."),
    ]
    legenda = "".join(f"<div>{rot}<span>{txt}</span></div>" for ok, rot, txt in itens if ok)

    # uma linha real da ficha: o 1º exercício da 1ª semana com aquecimento (ou com carga), como aparece na ficha
    s1 = semanas[0]
    dia_de = {v: k for k, v in D.get("dias", {}).items()}
    exemplo = ""
    for prefer_aq in (True, False):
        for num, rows in s1["treinos"].items():
            comp = T.compactar(rows)
            alvo = next((r for r in comp if (r.get("_aq") if prefer_aq else r.get("kg")) and "aquecimento" not in obs(r)), None)
            if alvo:
                trecho = [r for r in rows if r.get("linha") == alvo.get("linha") or r in (alvo.get("_aq") or [])]
                tabela = T.treino_table(num, trecho, dia_de.get(f"T{num}", "").capitalize(), int(s1["numero"]))
                exemplo = (f'<div class="exlinha">{tabela}</div>'
                           f'<p class="lido"><b>{e(alvo["ex"])}:</b> {_ler_linha(alvo)}</p>')
                break
        if exemplo:
            break
    return (f'{QUEBRA}<h3>COMO LER A SUA FICHA</h3>'
            + (f'<p class="intro">Uma linha da sua ficha, lida em palavras:</p>{exemplo}' if exemplo else "")
            + f'<div class="legend">{legenda}</div>')


def html_faltou(n_treinos: int) -> str:
    """Regra de Miguel (18/out/2026): treino que faltou é feito, nunca pulado. Mesmo texto para todos os alunos."""
    seq = ' <i>→</i> '.join(f'<span>Treino {i:02d}</span>' for i in range(1, min(n_treinos, 4) + 1)) if n_treinos > 1 else ""
    return ('<h3>SE FALTAR UM TREINO</h3><div class="faltou"><div><b>Faça o treino que faltou.</b>'
            '<p>Não pule para o próximo: a sequência continua de onde parou.</p></div>'
            + (f'<div class="seq">{seq}</div>' if seq else "") + '</div>')


# ------------------------------------------------------------------ PDF PRÉ — planejamento
def itens_auto(aluno: dict, tipo: str, C: dict | None = None) -> list[dict]:
    """Itens pessoais escolhidos pelo programa (decisão de Miguel, 5/out/2026: ele não edita mais).
    Só entram itens com as DUAS partes: a 2ª parte só existe quando é fato verificável (planilha, regra fixa da
    metodologia, feedback mais recente, 1RM). Ordem de prioridade de app/formularios.py; no máximo 4."""
    from . import formularios
    C = C or _contexto(aluno)
    slug = aluno["slug"]
    anamnese = individual.carregar_anamnese(slug)
    if tipo == "pre":
        rm_bloco = C["P"]["rm"].get(C["bloco"]) or {}
        itens = formularios.itens_pre(anamnese, C["dias"], len(C["dias"]), rm_bloco)
        chave = "treino"
    else:
        itens = formularios.itens_pos(anamnese, individual.carregar_feedbacks(slug), C["R"].get("rm_evolucao", []))
        chave = "resultado"
    if tipo == "pre":   # Miguel, 19/out/2026: os pontos da anamnese aparecem; a 2ª parte só quando é fato verificável
        return [i for i in itens if i.get("aluno")][:6]
    return [i for i in itens if i.get("aluno") and i.get(chave)][:individual.MAX_ITENS]


def _marcas_bloco(C: dict, bloco: int, sel: list[int] | None = None) -> dict:
    """O que a ficha deste bloco mostra (mesmas regras automáticas do motor): ANOTAR em faixa de repetições e AMRAP;
    GRAVAR em AMRAP e em %1RM de 80% ou mais; e as semanas e exercícios com AMRAP (teste do 1RM)."""
    anotar = gravar = False
    amrap_sem, amrap_ex = [], []
    for s in C["P"]["semanas"]:
        if s["bloco"] != bloco or (sel and s["semana"] not in sel):
            continue
        for rows in s["treinos"].values():
            for r in rows:
                reps, obs = str(r.get("reps") or "").lower(), str(r.get("obs") or "").lower()
                tem_amrap = "amrap" in reps or "amrap" in obs
                if tem_amrap or re.fullmatch(r"\d+\s*-\s*\d+", reps) or "anotar" in obs:
                    anotar = True
                if tem_amrap or (r.get("pct") and round(r["pct"] * 100) >= 80) or "gravar" in obs:
                    gravar = True
                if tem_amrap:
                    if s["semana"] not in amrap_sem:
                        amrap_sem.append(s["semana"])
                    nome = r.get("base") or r["ex"]
                    if nome not in amrap_ex:
                        amrap_ex.append(nome)
    return {"anotar": anotar, "gravar": gravar, "amrap_sem": sorted(amrap_sem), "amrap_ex": amrap_ex}


def _lista(itens: list) -> str:
    itens = [str(i) for i in itens]
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _blocos_do_ciclo(aluno: dict, C: dict) -> list[int]:
    """Blocos que aparecem em "O seu ciclo", conforme o plano contratado do aluno (decisão de Miguel, 9/out/2026):
    mensal = só o bloco atual; trimestral = os 3 blocos do período (os que ainda não têm prescrição ficam "A definir").
    Sem plano contratado: só os blocos que já estão na planilha, até o atual (nada é suposto)."""
    bloco = C["bloco"]
    situ = planos.situacao(aluno)
    if situ and situ.get("semanas"):
        n = max(1, round(situ["semanas"] / 4))
        k = 0
        ini_bloco = next((s["data"] for s in C["R"]["semanas"] if s["bloco"] == bloco and s["data"]), "")
        if n > 1 and ini_bloco and situ.get("inicio"):
            dias = (dt.date.fromisoformat(ini_bloco) - dt.date.fromisoformat(situ["inicio"])).days
            k = min(n - 1, max(0, round(dias / 28)))
        return [b for b in range(bloco - k, bloco - k + n) if b >= 1]
    return sorted({s["bloco"] for s in C["R"]["semanas"] if s["bloco"] <= bloco})


ROTULO_ITEM = {"motivacao": "MOTIVAÇÃO", "dor": "DOR E LESÕES", "rotina": "ROTINA", "preferencias": "PREFERÊNCIAS",
               "atividade": "OUTRA ATIVIDADE", "sono": "SONO"}


def semanas_entregues(aluno: dict, bloco: int) -> list[int] | None:
    """Semanas da última entrega deste bloco (ficha parcial); None = bloco inteiro. O planejamento acompanha o que foi
    entregue: 1, 2, 3 semanas ou o bloco todo (Miguel, 18-19/out/2026)."""
    ult = next((x for x in aluno.get("entregas", []) if x.get("bloco") == bloco), None)
    return sorted(ult["semanas"]) if ult and ult.get("semanas") else None


def _txt_semanas(sel: list[int]) -> str:
    return f"Semana {sel[0]:02d}" if len(sel) == 1 else "Semanas " + _lista([f"{x:02d}" for x in sel])


def html_pre(aluno: dict, itens: list | None = None) -> tuple[str, str]:
    """PDF "Seu planejamento": sem capa (Miguel, 9/out/2026), 2 páginas (Miguel, 18/out/2026), reorganizado em
    19/out/2026 (Miguel achou confuso). Página 1 = o aluno e o plano: perfil, "Pensado para você" (cada ponto da
    anamnese numa linha, com o que há no treino quando é fato verificável), ciclo (só com mais de um bloco) e 1RM.
    Página 2 = como usar a ficha: "Como ler", "Se faltar um treino" e "Como vamos acompanhar".
    Tudo segue as semanas entregues (bloco inteiro ou semanas avulsas)."""
    C = _contexto(aluno)
    R, bloco = C["R"], C["bloco"]
    sem_bloco = [s for s in R["semanas"] if s["bloco"] == bloco]
    sel = semanas_entregues(aluno, bloco)
    sem_ent = [s for s in sem_bloco if not sel or s["semana"] in sel]
    ini = sem_ent[0]["data"] if sem_ent else ""
    fim = (dt.date.fromisoformat(sem_ent[-1]["data"]) + dt.timedelta(days=6)).isoformat() if sem_ent and sem_ent[-1]["data"] else ""
    M = _marcas_bloco(C, bloco, sel)

    # ---- ciclo: só quando há mais de um bloco para mostrar (um bloco só já está no perfil)
    blocos = _blocos_do_ciclo(aluno, C)
    ciclo = ""
    if len(blocos) > 1:
        blocos_html = []
        for b in blocos:
            ss = [s for s in R["semanas"] if s["bloco"] == b]
            if ss:
                d1 = (dt.date.fromisoformat(ss[-1]["data"]) + dt.timedelta(days=6)).isoformat() if ss[-1]["data"] else ""
                status = "este bloco" if b == bloco else ("concluído" if b < bloco else "próximo")
                barras = "".join(f'<i class="{"feita" if b < bloco else "agora" if b == bloco and (not sel or s["semana"] in sel) else ""}"></i>' for s in ss)
                blocos_html.append(f'''<div class="bloco {"atual" if b == bloco else ""}"><small>BLOCO {b:02d} · {status.upper()}</small>
                  <b>{data_br(ss[0]["data"], False)} a {data_br(d1, False)}</b><span>{len(ss)} {"semana" if len(ss) == 1 else "semanas"}</span>
                  <div class="semanas" style="grid-template-columns:repeat({len(ss)},1fr)">{barras}</div></div>''')
            else:
                blocos_html.append(f'<div class="bloco futuro"><small>BLOCO {b:02d}</small><b>A definir</b><span>a partir dos seus resultados</span></div>')
        ciclo = (f'<h3>O SEU CICLO</h3><div class="blocos" style="grid-template-columns:repeat({len(blocos_html)},1fr)">'
                 f'{"".join(blocos_html)}</div>')

    # ---- principais exercícios: nome e 1RM estimado do bloco (aba prs)
    ref = C["P"].get("rm_ref", {}).get(bloco, {})
    cel = "".join(f'<div class="rm1"><span>{e(n)}</span><b>{round(v["est"])} kg</b></div>' for n, v in ref.items())
    tabela = (f'''<h3>SEU 1RM NESTE BLOCO</h3><div class="rm1s">{cel}</div>
      <p class="nota">Carga máxima estimada para uma repetição. É a base das cargas da sua ficha.</p>''' if cel else "")

    # ---- pensado para você: um ponto da anamnese por linha (palavras do aluno) + o que está no treino, se verificável
    itens = itens_auto(aluno, "pre", C) if itens is None else itens
    pensado = ("<h3>PENSADO PARA VOCÊ</h3><div class=\"pv\">" + "".join(
        f'<div class="par"><small>{ROTULO_ITEM.get(i.get("chave"), "VOCÊ CONTOU")}</small><div><p>{sem_viuva(i["aluno"])}</p>'
        + (f'<p class="forte">{sem_viuva(i["treino"])}</p>' if i.get("treino") else "") + "</div></div>"
        for i in itens) + "</div>") if itens else ""

    # ---- como vamos acompanhar: só o que existe nas semanas entregues
    base_rev = ("as suas anotações e vídeos" if M["anotar"] and M["gravar"] else "as suas anotações" if M["anotar"]
                else "os seus vídeos" if M["gravar"] else "o seu feedback")
    passos = []
    if M["anotar"]:
        passos.append('<div><b>Anote</b>Repetições e cargas das séries com <span class="pill solid">Anotar</span></div>')
    if M["gravar"]:
        passos.append('<div><b>Grave</b>As séries com <span class="pill solid rec">Gravar</span> para eu ver a técnica.</div>')
    if M["amrap_sem"]:
        sem_txt = f'Na semana {M["amrap_sem"][0]}' if len(M["amrap_sem"]) == 1 else f'Nas semanas {_lista(M["amrap_sem"])}'
        passos.append(f'<div><b>Teste</b>{sem_txt}, as séries AMRAP atualizam o seu 1RM.</div>')
    passos.append(f'<div><b>Ajuste</b>A próxima entrega parte d{base_rev}.</div>')      # das/dos/do
    acompanhar = f'<div class="passos p4" style="grid-template-columns:repeat({len(passos)},1fr)">{"".join(passos)}</div>'

    n_sem = len(sem_ent)
    # mesma regra da mensagem de entrega (Miguel, 18/out/2026): dia seguinte à última semana entregue
    prox = (dt.date.fromisoformat(fim) + dt.timedelta(days=1)).isoformat() if fim else (aluno.get("proxima_atualizacao") or "")
    entrega = (_txt_semanas(sel) if sel else f'Bloco {bloco:02d} · {n_sem} {"semana" if n_sem == 1 else "semanas"}')
    perfil = f'''<div class="card prof4">
      <div><small>OBJETIVO</small><b>{e(aluno.get("objetivo") or "—")}</b></div>
      <div><small>TREINOS</small><b>{len(C["dias"])}× por semana<span>{" · ".join(C["dias"])}</span></b></div>
      <div><small>ESTA ENTREGA</small><b>{entrega}<span>{data_br(ini)} a {data_br(fim)}</span></b></div>
      <div><small>PRÓXIMA REVISÃO</small><b>{data_br(prox) or "—"}<span>com {base_rev}</span></b></div></div>'''

    D = _ficha_do_bloco(aluno, bloco)
    if D and sel:
        D = {**D, "semanas": [x for x in D["semanas"] if int(x["numero"]) in sel] or D["semanas"]}
    secoes = [
        ("perfil", perfil),
        ("pensado", pensado),
        ("ciclo", ciclo),
        ("tabela", tabela),
        ("comoler", html_como_ler(D)),
        ("faltou", html_faltou(len(C["dias"]))),
        ("acompanhar", f"<h3>COMO VAMOS ACOMPANHAR</h3>{acompanhar}"),
    ]
    sub = f'Bloco {bloco:02d}{" · " + _txt_semanas(sel) if sel else ""} · {data_br(ini)} a {data_br(fim)}'
    return "", secoes, f"Planejamento · Bloco {bloco:02d}", "SEU PLANEJAMENTO", sub


# ------------------------------------------------------------------ PDF PÓS — resultados e evolução
def html_pos(aluno: dict, itens: list | None = None):
    C = _contexto(aluno)
    R, atual, hoje = C["R"], C["atual"], C["hoje"]
    nome = aluno["nome"]
    primeiro = nome.split()[0]
    feitas = [s for s in R["semanas"] if s["global"] <= atual["global"]]
    vol_total = sum(s["vtt"] for s in feitas)
    ints = [(s, s["int"]) for s in feitas if s["int"] is not None]
    evol_rm = [x for x in R.get("rm_evolucao", []) if x["variacao"] is not None]
    melhor = max(evol_rm, key=lambda x: x["variacao"]) if evol_rm else None

    sem = lambda x: f"semana {x['global']}"  # noqa: E731  (linguagem do aluno: "semana 7", não "S07")
    total = len(R["semanas"])
    cards = [f'''<div class="rm"><small>PESO LEVANTADO</small><b>{mil(vol_total)}<i> kg</i></b><span>em {len(feitas)} {"semana" if len(feitas) == 1 else "semanas"}</span>
      <em>somando todas as séries</em></div>''']
    cards.append(f'''<div class="rm"><small>SEU CICLO</small><b>{atual["global"]}<i> de {total}</i></b><span>semanas</span>
      <em>bloco {atual["bloco"]:02d}, semana {atual["semana"]}</em></div>''')
    if len(ints) >= 2:
        cards.append(f'''<div class="rm"><small>INTENSIDADE</small><b>{pct(ints[-1][1])}</b><span>do seu máximo</span>
          <em>era {pct(ints[0][1])} na 1ª semana</em></div>''')
    elif ints:
        cards.append(f'''<div class="rm"><small>INTENSIDADE</small><b>{pct(ints[-1][1])}</b><span>do seu máximo</span><em>nesta semana</em></div>''')
    if melhor and melhor["variacao"] > 0:
        b0, b1 = melhor["blocos"][0], melhor["blocos"][-1]
        cards.append(f'''<div class="rm"><small>MAIS FORÇA</small><b>{var(melhor["variacao"])}</b><span>{e(melhor["exercicio"])}</span>
          <em>{n0(b0["est"])} → {n0(b1["est"])} kg no 1RM</em></div>''')
    destaques = f'<div class="dest" style="grid-template-columns:repeat({len(cards)},1fr)">{"".join(cards)}</div>'

    # gráficos: semanas feitas em preto e próximas em contorno (valores da planilha)
    pts_v = [{"g": s["global"], "rotulo": f"S{s['global']:02d}", "bloco": s["bloco"],
              "valor": s["vtt"],
              "cor": _cor_semana(s, atual["global"], hoje)} for s in R["semanas"]]
    pts_i = [{"g": s["global"], "rotulo": f"S{s['global']:02d}", "bloco": s["bloco"],
              "valor": s["int"],
              "cor": _cor_semana(s, atual["global"], hoje)} for s in R["semanas"]]
    vols = [(s, s["vtt"]) for s in feitas]
    pico_s, pico_v = max(vols, key=lambda x: x[1])
    if len(vols) >= 2 and vols[0][1]:
        frase_vol = (f"Sua semana mais puxada foi a {sem(pico_s)}: {n0(pico_v)} kg, {var((pico_v - vols[0][1]) / vols[0][1] * 100)} "
                     f"sobre a 1ª. As mais leves são planejadas, para recuperar.") if pico_s is not vols[0][0] else \
                    f"Na 1ª semana você levantou {n0(vols[0][1])} kg. As semanas mais leves são planejadas, para recuperar."
    else:
        frase_vol = f"Na 1ª semana você levantou {n0(vols[0][1])} kg."
    if len(ints) >= 2:
        frase_int = f"Você está treinando mais perto do seu máximo: de {pct(ints[0][1])} na 1ª semana para {pct(ints[-1][1])} agora." \
            if ints[-1][1] > ints[0][1] else f"Agora você treina, em média, a {pct(ints[-1][1])} do seu máximo."
    else:
        frase_int = "A intensidade é o peso usado em relação ao seu máximo (1RM)."
    leg = ('<div class="leg"><span><i style="background:#000"></i>semanas feitas</span>'
           '<span><i style="background:#fff;border:.25mm solid #c9c6bd"></i>próximas semanas</span></div>')
    graficos = f'''<div class="dois">
      <div class="graf"><h4>Peso levantado por semana (kg)</h4>{svg_colunas(pts_v, fmt_eixo=mil, destaque=atual["global"])}<p>{e(frase_vol)}</p></div>
      <div class="graf"><h4>Intensidade média (% do seu máximo)</h4>{svg_linha(pts_i, destaque=atual["global"])}<p>{e(frase_int)}</p></div></div>{leg}'''

    # força estimada por bloco
    forca = ""
    ev = [x for x in R.get("rm_evolucao", []) if len(x["blocos"]) >= 2][:4]
    if ev:
        cards_f = "".join(
            f'''<div class="fc"><span>{e(x["exercicio"])}</span><b>{var(x["variacao"])}</b>
              <em>{" → ".join(n0(b["est"]) for b in x["blocos"])} kg</em><i>{" · ".join(f"bloco {b['bloco']:02d}" for b in x["blocos"])}</i></div>'''
            for x in ev)
        forca = (f'<h3>SUA FORÇA ESTIMADA</h3><div class="fcs" style="grid-template-columns:repeat({len(ev)},1fr)">{cards_f}</div>'
                 '<p class="nota">1RM estimado: a carga máxima para uma repetição, calculada a partir das suas séries de teste de cada bloco.</p>')

    # linha do tempo do feedback semanal (Miguel, 16/out/2026): mesmo eixo de semanas dos gráficos acima
    from . import individual as I_
    linha_fb = I_.linha_do_tempo(aluno["slug"], R["semanas"], ate_global=atual["global"])
    sentiu = tabela_feedback(linha_fb, atual["global"])

    itens = itens_auto(aluno, "pos", C) if itens is None else itens
    mudou = ("<h3>O QUE VOCÊ PEDIU, O QUE MUDOU</h3><div class=\"pares\">" + "".join(
        f'<div class="par"><small>VOCÊ PEDIU</small><p>{sem_viuva(i["aluno"])}</p><small>O QUE ACONTECEU</small><p class="forte">{sem_viuva(i["resultado"])}</p></div>'
        for i in itens) + "</div>") if itens else ""
    secoes = [
        ("intro", f'<p class="intro">{e(primeiro)}, aqui está o que você construiu até a semana {atual["global"]} do seu ciclo '
                  f'(bloco {atual["bloco"]:02d}, semana {atual["semana"]}).</p>'),
        ("destaques", destaques),
        ("mudou", mudou),
        ("graficos", f"<h3>SEMANA A SEMANA</h3>{graficos}" if len(feitas) >= 2 else
                     '<h3>SEMANA A SEMANA</h3><p class="nota">Os gráficos de volume e intensidade aparecem aqui a partir da segunda semana de treino.</p>'),
        ("forca", forca),
        ("quebra", QUEBRA if sentiu else ""),
        ("sentiu", sentiu),
        ("fecho", '<p class="fecho">Seguimos ajustando cada bloco com base no que você anota e no que os vídeos mostram.</p>'),
    ]
    capa = _capa("RESULTADOS E EVOLUÇÃO", f"BLOCO {atual['bloco']:02d}", nome, data_br(hoje.isoformat()))
    return capa, secoes, f"Resultados · semana {atual['global']}", "SUA EVOLUÇÃO", f"Semana {atual['global']} de {total} · {mes_ano(hoje)}"


# ------------------------------------------------------------------ geração
# Seções que podem sair para caber em 2 páginas, da menos para a mais importante.
# Nunca saem: perfil, itens pessoais (pensado/mudou), tabela de 1RM do pré, destaques do pós.
OPCIONAIS = {"pre": ["acompanhar", "ciclo"], "pos": ["fecho", "intro", "forca", "graficos"]}


QUEBRA = "<!--quebra-->"


def _montar(capa, secoes, rodape, titulo, sub, nome, omitir=()):
    """Seções em ordem; a seção "quebra" abre uma nova página (Resultados: capa + até 2 páginas, Miguel 16/out/2026).
    Página que ficaria só com seções vazias não é gerada."""
    corpo = "".join(html_ for chave, html_ in secoes if html_ and chave not in omitir)
    partes = [c for c in corpo.split(QUEBRA) if c.strip()]
    n0_ = 2 if capa else 1
    return _doc(f"{titulo} — {nome}", capa + "".join(
        _pagina(titulo, sub, c, nome, rodape, f"{n0_ + i:02d}") for i, c in enumerate(partes)))


def gerar(slug: str, tipo: str) -> dict:
    """Gera o PDF pré ('pre') ou pós ('pos') e guarda em pdfs/. Se não couber em 2 páginas, tira seções opcionais.
    Itens pessoais com mais de 2 linhas: o texto do aluno é encurtado; se a 2ª parte passar, o item sai."""
    from playwright.sync_api import sync_playwright
    from .formularios import enxuto
    aluno = A.carregar(slug)
    montar_html = html_pre if tipo == "pre" else html_pos
    campo2 = "treino" if tipo == "pre" else "resultado"
    itens = itens_auto(aluno, tipo)
    if tipo == "pre":   # "MariaSilva_Bloco02_Planejamento.pdf": um por bloco, gerar de novo substitui (Miguel, 9/out/2026)
        nome_arq = re.sub(r'[\\/:*?"<>|\s]+', "", aluno["nome"]) + f"_Bloco{int(_contexto(aluno)['bloco']):02d}_Planejamento.pdf"
    else:
        # "MariaSilva_Bloco02_Resultados.pdf" (bloco da semana atual), no mesmo padrão do planejamento: gerar de novo
        # substitui em vez de acumular arquivos com data e hora (revisão de 11/out/2026)
        nome_arq = re.sub(r'[\\/:*?"<>|\s]+', "", aluno["nome"]) + f"_Bloco{int(_contexto(aluno)['atual']['bloco']):02d}_Resultados.pdf"
    destino = A.pasta(slug) / "pdfs" / nome_arq
    destino.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=CHROMIUM_ARGS)
        pg = b.new_page()
        for _ in range(12):
            capa, secoes, rodape, titulo, sub = montar_html(aluno, itens)

            def medir(omit):
                pg.set_content(_montar(capa, secoes, rodape, titulo, sub, aluno["nome"], omit), wait_until="load")
                pg.evaluate("document.fonts.ready")
                return pg.evaluate('''() => Math.min(...[...document.querySelectorAll('.page')].filter(p => p.querySelector('.ftr')).map(p => {
                    const f=p.querySelector('.ftr').getBoundingClientRect().top;
                    const k=[...p.querySelector('.body').children].map(c=>c.getBoundingClientRect().bottom);
                    return (f-Math.max(...k))/3.7795; })) ''')   # cada página tem de caber
            existe = {k for k, h in secoes if h}
            omitidas = []
            folga = medir(omitidas)
            while folga < 4:
                resta = [c for c in OPCIONAIS[tipo] if c not in omitidas and c in existe]
                if not resta:
                    break
                omitidas.append(resta[0])
                folga = medir(omitidas)
            for c in reversed(list(omitidas)):          # devolve o que ainda couber, do mais importante para o menos
                teste = [x for x in omitidas if x != c]
                f2 = medir(teste)
                if f2 >= 4:
                    omitidas, folga = teste, f2
            medir(omitidas)
            # regra de Miguel: cada texto dos itens pessoais em no máximo 2 linhas (a palavra solta já é evitada)
            linhas = pg.evaluate('''() => [...document.querySelectorAll('.par')].map(par => [...par.querySelectorAll('p')].map(p => {
                const r = document.createRange(); r.selectNodeContents(p);
                return new Set([...r.getClientRects()].map(x => Math.round(x.top))).size; }))''')
            ajustar = False
            sair = set()
            for i, ls in enumerate(linhas):
                n_aluno, n_2 = (ls + [0, 0])[:2]
                if n_2 > 2:
                    sair.add(i)
                elif n_aluno > 2:
                    novo = enxuto(itens[i]["aluno"].rstrip("…"), max(40, len(itens[i]["aluno"]) - 15))
                    if novo == itens[i]["aluno"]:
                        sair.add(i)
                    else:
                        itens[i] = {**itens[i], "aluno": novo}
                    ajustar = True
            if sair:
                itens = [x for k, x in enumerate(itens) if k not in sair]
                ajustar = True
            if not ajustar and folga >= 4:
                break
            if not ajustar and folga < 4:
                if itens:                             # ainda não coube: o item menos importante sai
                    itens = itens[:-1]
                    continue
                b.close()
                raise ValueError("O conteúdo não coube na página.")
        pg.pdf(path=str(destino), width="210mm", height="297mm", print_background=True, prefer_css_page_size=True)
        b.close()
    rel = destino.relative_to(A.pasta(slug)).as_posix()
    aluno = A.carregar(slug)
    aluno["relatorios"] = [x for x in aluno.get("relatorios", []) if x.get("pdf") != rel]   # o substituído sai da lista
    aluno["relatorios"].insert(0, {"tipo": tipo, "data": A.agora(), "pdf": rel, "omitidas": omitidas,
                                                  "itens": [{"aluno": i["aluno"], campo2: i[campo2]} for i in itens]})
    A.registrar(aluno, f"PDF de {'planejamento' if tipo == 'pre' else 'resultados'} gerado para o aluno")
    A.salvar(aluno)
    return {"ok": True, "pdf": rel, "folga": round(folga, 1), "omitidas": omitidas}
