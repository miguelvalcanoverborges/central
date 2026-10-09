# -*- coding: utf-8 -*-
"""
TEMPLATE MESTRE v1.12 — FORÇA & INTELIGÊNCIA · Miguel Valcanover
=================================================================
TRAVADO. Este arquivo + template_mestre.css definem a identidade visual aprovada
(capa, perfil, tabelas de treino). NÃO editar sem autorização de Miguel.
Alterações autorizadas devem ser re-travadas com `travar_template.py`.

Este módulo recebe dados já extraídos (dados.json) e devolve HTML. Nenhum dado de aluno
é escrito aqui: tudo vem de `D` (extraído da planilha) e `ctx` (contexto opcional aprovado).
"""
import base64
import datetime
import html
import os

VERSAO = '1.12'
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets')
IG = '@miguelvalcanover'
PHONE = '(55) 99105-8153'
e = html.escape

# Capacidade útil do corpo de uma página de treino (mm) e estimativa de altura dos blocos.
# Calibrado para reproduzir o layout aprovado: [AQC + Treino 01] / [Treino 02 + Treino 03].
CAPACIDADE_MM = 224.0


def _b64(name, mime):
    with open(os.path.join(ASSETS, name), 'rb') as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def css():
    with open(os.path.join(HERE, 'template_mestre.css'), encoding='utf-8') as f:
        txt = f.read()
    return (txt.replace('__KRONA__', _b64('KronaOne.ttf', 'font/ttf'))
               .replace('__EXO__', _b64('Exo2.ttf', 'font/ttf')))


def fmt(n):
    if n is None:
        return '—'
    if isinstance(n, str):          # v1.9: séries em faixa ("3 - 4", já normalizada pelo extrator) aparecem como estão
        return n
    return str(int(n)) if float(n).is_integer() else str(n).replace('.', ',')


def fmt_reps(v):
    """Repetições/tempo sem casa decimal: 10.0 -> 10; '10.0' -> 10; '8 - 12' e textos ficam como estão."""
    import re
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return re.sub(r'(?<![\d.,])(\d+)\.0+(?![\d])', r'\1', str(v))


# Etiquetas reconhecidas na coluna OBS (qualquer outro texto vira nota em itálico, literal).
TAGS = {'aquecimento': ('ghost', 'Aquecimento'), 'principal': ('line', 'Principal'),
        'gravar': ('solid rec', 'Gravar'), 'biset': ('line', 'Biset'), 'amrap': ('line', 'AMRAP'),
        'anotar': ('solid', 'Anotar')}   # v1.10: faixa de repetições → o aluno anota reps e carga de cada série


def pills(obs):
    if not obs:
        return ''
    parts = [p.strip() for p in obs.split(' - ')]
    if all(p.lower() in TAGS for p in parts):
        return ''.join(f'<span class="pill {TAGS[p.lower()][0]}">{TAGS[p.lower()][1]}</span>' for p in parts)
    # v1.10: nota de Miguel + etiqueta automática (Gravar/Anotar) → etiquetas como pílula e a nota literal, em itálico
    auto = [p for p in parts if p.lower() in ('gravar', 'anotar')]
    if auto:
        nota = ' - '.join(p for p in parts if p.lower() not in ('gravar', 'anotar'))
        return (''.join(f'<span class="pill {TAGS[p.lower()][0]}">{TAGS[p.lower()][1]}</span>' for p in auto)
                + f'<span class="note">{e(nota)}</span>')
    return f'<span class="note">{e(obs)}</span>'


def treino_table(num, rows, dia, semana):
    body = []
    for idx, r in enumerate(rows, 1):
        obs = (r['obs'] or '').lower()
        cls = []
        if 'aquecimento' in obs:
            cls.append('warm')
        if 'biset' in obs:
            cls.append('biset')
        pct = r['pct']
        pct_html = '<span class="dash">—</span>' if pct is None else (
            f'<b>{round(pct*100)}%</b><div class="bar"><i style="width:{min(100, pct*100):.0f}%"></i></div>')
        kg = f"{fmt(r['kg'])}<small> kg</small>" if r['kg'] else '<span class="dash">—</span>'
        body.append(f'''<tr class="{' '.join(cls)}">
          <td class="idx"><span>{idx}</span></td>
          <td class="ex">{e(r['ex'])}</td>
          <td class="n">{fmt(r['sets'])}</td><td class="n">{e(fmt_reps(r['reps']))}</td>
          <td class="n kg">{kg}</td><td class="n pc">{pct_html}</td>
          <td class="ob"><div class="obw">{pills(r['obs'])}{('<a class="vid" href="' + e(r['link']) + '">▶ Ver vídeo</a>') if r.get('link') else ''}</div></td></tr>''')
    return f'''<section class="treino">
      <div class="thead"><span class="tname">TREINO {num}</span><span class="tday">{e(dia)}</span><span class="tweek">SEMANA {semana:02d}</span></div>
      <table>
        <colgroup><col style="width:8mm"><col><col style="width:13mm"><col style="width:14mm"><col style="width:16mm"><col style="width:19mm"><col style="width:41mm"></colgroup>
        <thead><tr><th></th><th class="l">EXERCÍCIO</th><th>SÉRIES</th><th>REPS</th><th>CARGA</th><th>%1RM</th><th class="l">OBS</th></tr></thead>
        <tbody>{''.join(body)}</tbody>
      </table></section>'''


def aqc_block(aqc):
    # Regra de Miguel (3/out/2026): mostrar SEMPRE a carga do AQC quando houver; a coluna CARGA só existe se algum item tem carga.
    tem_kg = any(a.get('kg') not in (None, '') for a in aqc)
    rows = []
    for i, a in enumerate(aqc, 1):
        link = ''
        if a.get('link'):
            link = f'<a class="vid" href="{e(a["link"])}">▶ Ver vídeo</a>'
        elif a.get('nota'):
            link = f'<span class="note">{e(a["nota"])}</span>'
        kg = a.get('kg')
        if isinstance(kg, (int, float)):
            kg_cell = f'{fmt(kg)} <small>kg</small>'
        else:
            kg_cell = e(str(kg)) if kg not in (None, '') else '—'
        kg_td = f'<td class="n kg">{kg_cell}</td>' if tem_kg else ''
        rows.append(f'''<tr><td class="idx"><span>{i}</span></td><td class="ex">{e(a['ex'])}</td>
        <td class="n">{fmt(a['sets'])}</td><td class="n">{e(fmt_reps(a['reps']))}</td>{kg_td}<td class="ob">{link}</td></tr>''')
    cols = '<col style="width:8mm"><col><col style="width:14mm"><col style="width:26mm">' + ('<col style="width:20mm">' if tem_kg else '') + '<col style="width:39mm">'
    th_kg = '<th>CARGA</th>' if tem_kg else ''
    return f'''<section class="treino aqc">
      <div class="thead alt"><span class="tname">AQC</span><span class="tday">AQUECIMENTO GERAL</span></div>
      <table>
        <colgroup>{cols}</colgroup>
        <thead><tr><th></th><th class="l">EXERCÍCIO</th><th>SÉRIES</th><th>REPS / TEMPO</th>{th_kg}<th class="l"></th></tr></thead>
        <tbody>{''.join(rows)}</tbody></table></section>'''


def header(title, sub, gor):
    sub_html = f'<p>{sub}</p>' if sub else ''
    return f'''<div class="hdr"><img class="hg" src="{gor}"><div class="hb">FORÇA &amp; INTELIGÊNCIA</div></div>
    <div class="ttl"><h2>{title}</h2>{sub_html}</div>'''


def footer(n, nome, bloco, semana_label):
    sem = f' · {semana_label}' if semana_label else ''
    return f'''<div class="ftr"><span>{e(nome)} · Bloco {bloco:02d}{sem}</span>
    <span>Miguel Valcanover · Treinador · {IG}</span><span class="pg">{n:02d}</span></div>'''


def _altura(rows, extra=0):
    return 25.0 + 10.8 * rows + extra


def paginar(D):
    """Distribui AQC + treinos em páginas (A4). Regra: preenche a página em ordem; quebra quando
    o próximo bloco não cabe. Uma nova semana sempre começa em página nova.
    Retorna lista de páginas: {'semana': n, 'blocos': [('aqc',None)|('treino',num)]}"""
    paginas = []
    for si, sem in enumerate(D['semanas']):
        itens = []
        if si == 0 and D.get('aqc'):
            itens.append(('aqc', None, _altura(len(D['aqc']))))
        for num in sorted(sem['treinos']):
            itens.append(('treino', num, _altura(len(sem['treinos'][num]))))
        atual, usado = [], 0.0
        for tipo, num, h in itens:
            if atual and usado + h > CAPACIDADE_MM:
                paginas.append({'semana': sem['numero'], 'blocos': atual})
                atual, usado = [], 0.0
            atual.append((tipo, num))
            usado += h
        if atual:
            paginas.append({'semana': sem['numero'], 'blocos': atual})
    return paginas


def render(D, ctx=None):
    """D: dados extraídos da planilha. ctx: contexto opcional aprovado por Miguel
    (perfil_extra, prs com fonte, usa_pse)."""
    ctx = ctx or {}
    GOR = _b64('gorilla_white.png', 'image/png')
    HALF = _b64('halftone.png', 'image/png')

    nome = D['aluno']['nome']
    obj = D['aluno']['objetivo'] or '—'
    bloco = int(D['bloco']['numero'])
    inicio = D['bloco'].get('inicio')
    dias = D['dias']                       # {'SEGUNDA': 'T01', ...}
    dia_de = {v: k for k, v in dias.items()}   # {'T01': 'SEGUNDA'}
    usa_pse = bool(ctx.get('usa_pse', D.get('usa_pse', False)))
    semanas = D['semanas']
    pag = paginar(D)
    # v1.11: datas do bloco (início da aba macro; bloco = 4 semanas) e data de início de cada semana
    ini = datetime.datetime.strptime(inicio, '%d/%m/%Y').date() if inicio else None
    fim = ini + datetime.timedelta(days=27) if ini else None

    def data_semana(n):
        return f' · {ini + datetime.timedelta(days=7 * (n - 1)):%d/%m}' if ini else ''

    # ---------- CAPA
    cmeta = f'<div class="cmeta"><b>{inicio}</b></div>' if inicio else ''
    cover = f'''<div class="page dark cover">
  <img class="half" src="{HALF}">
  <img class="cg" src="{GOR}">
  <div class="tag">FORÇA &amp; INTELIGÊNCIA</div>
  <div class="ct">
    <div class="kick">PLANO DE TREINAMENTO</div>
    <h1 class="glow">BLOCO {bloco:02d}</h1>
    <div class="name">{e(nome)}</div>
  </div>
  {cmeta}
  <div class="cfoot"><b>Miguel Valcanover</b> <em>· Treinador</em><br><span>{IG} · {PHONE}</span></div>
</div>'''

    # ---------- PERFIL + NÚMEROS + COMO LER
    def _k(x):
        return ''.join(c for c in x.lower() if c.isalnum())
    prs_ctx = {_k(x['exercicio']): x for x in ctx.get('prs', [])}   # PRs reais (exigem 'fonte')
    usados, cards, tem_est = set(), [], False

    def pr_card(pr):
        return f'''<div class="rm"><small>{e(pr['exercicio'].upper())}</small><b>{round(pr['kg'])}<i> kg</i></b>
   <span>PR</span><em>{e(pr['data'])}</em></div>'''
    for k, v in D['rm'].items():
        if _k(k) in prs_ctx:                      # PR real tem prioridade sobre a estimativa
            cards.append(pr_card(prs_ctx[_k(k)])); usados.add(_k(k))
        else:
            tem_est = True
            cards.append(f'''<div class="rm"><small>{e(k.upper())}</small><b>{round(v['est'])}<i> kg</i></b>
   <span>1RM estimado</span><em>{int(v['reps'])} reps × {fmt(v['kg'])} kg</em></div>''')
    for kk, pr in prs_ctx.items():
        if kk not in usados:
            cards.append(pr_card(pr))
    nota_est = ('<p class="foot">Estimativas calculadas pela fórmula de Brzycki, atualizadas na revisão do bloco.</p>'
                if tem_est else '')
    numeros = (f'<h3>SEUS NÚMEROS</h3>\n  <div class="rms">{"".join(cards)}</div>\n  {nota_est}' if cards else '')

    dias_txt = ' · '.join(d.capitalize() for d in dias.keys())
    extra_cells = ''.join(f'<div><small>{e(x["rotulo"].upper())}</small><b>{e(x["valor"])}</b></div>'
                          for x in ctx.get('perfil_extra', []))
    pse_item = ('<div><b>PSE</b><span>Nota que você dá ao esforço sentido na série, para eu acompanhar sua resposta ao treino.</span></div>'
                if usa_pse else '')
    tem_amrap = any('amrap' in (str(r['reps']) + ' ' + str(r['obs'] or '')).lower()
                    for s in semanas for rows in s['treinos'].values() for r in rows)
    # v1.10 (Miguel, 5/out/2026): ANOTAR entra na legenda, no lugar da PSE, sempre que houver faixa de repetições
    tem_anotar = any('anotar' in str(r['obs'] or '').lower()
                     for s in semanas for rows in s['treinos'].values() for r in rows)
    anotar_item = ('<div><span class="pill solid">Anotar</span><span>Anote as repetições e a carga que você usou em cada série, para eu ajustar a sua progressão.</span></div>'
                   if tem_anotar else '')
    # v1.12 (Miguel, 9/out/2026): a legenda só explica o que aparece na ficha deste bloco (etiqueta, coluna com valor)
    linhas_f = [r for s in semanas for rows in s['treinos'].values() for r in rows]
    etiq = set()
    for r in linhas_f:
        etiq |= {k for k in TAGS if f'pill {TAGS[k][0]}">{TAGS[k][1]}<' in pills(r['obs'])}
    tem_carga = any(r['kg'] for r in linhas_f) or any(a.get('kg') not in (None, '') for a in D.get('aqc', []))
    tem_pct = any(r['pct'] is not None for r in linhas_f)

    def item(cond, html):
        return html if cond else ''
    carga_item = item(tem_carga, '<div><b>CARGA</b><span>Peso total do exercício, em quilos. Na barra livre, some o peso da barra com o das anilhas.</span></div>')
    pct_item = item(tem_pct, '<div><b>%1RM</b><span>Intensidade da carga em relação ao seu 1RM, ou seja, sua carga máxima em uma repetição.</span></div>')
    aquec_item = item('aquecimento' in etiq, '<div><span class="pill ghost">Aquecimento</span><span>Série mais leve, feita antes das séries de trabalho para preparar o movimento.</span></div>')
    princ_item = item('principal' in etiq, '<div><span class="pill line">Principal</span><span>Série de trabalho do exercício, feita com a carga prescrita e com atenção total à técnica.</span></div>')
    gravar_item = item('gravar' in etiq, '<div><span class="pill solid rec">Gravar</span><span>Grave essa série em vídeo e envie para eu analisar sua técnica e ajustar as suas cargas.</span></div>')
    biset_item = item('biset' in etiq, '<div><span class="pill line">Biset</span><span>Dois exercícios feitos em sequência, um logo após o outro, na ordem em que aparecem na ficha.</span></div>')
    amrap_item = ('<div><b>AMRAP</b><span>O máximo de repetições possível na série, sempre mantendo a boa técnica de execução.</span></div>'
                  if tem_amrap else '')
    obs_geral_html = ''.join(f'<div class="rule"><b>Observação:</b> {e(t)}</div>' for t in D.get('observacoes', []))
    rot_semana = f'Semana {semanas[0]["numero"]:02d}' if len(semanas) == 1 else ''
    perfil = f'''<div class="page light">{header('SEU PERFIL', '', GOR)}
  <div class="body">
  <div class="card prof">
    <div><small>NOME</small><b>{e(nome)}</b></div>
    <div><small>OBJETIVO</small><b>{e(obj)}</b></div>
    <div><small>TREINOS</small><b>{len(dias)}× por semana<br><span>{dias_txt}</span></b></div>
    <div><small>BLOCO</small><b>{bloco:02d} · 4 semanas<br><span>{f'{ini:%d/%m/%Y} a {fim:%d/%m/%Y}' if ini else ''}</span></b></div>
    {extra_cells}
  </div>

  {numeros}

  <h3>COMO LER A SUA FICHA</h3>
  {obs_geral_html}
  <div class="legend">
    <div><b>SÉRIES</b><span>Quantas vezes você repete o conjunto de repetições, fazendo uma série depois da outra.</span></div>
    <div><b>REPS</b><span>Quantas repetições fazer em cada série. Se houver faixa, faça dentro do intervalo indicado.</span></div>
    {carga_item}{pct_item}
    {anotar_item}{pse_item}
    {aquec_item}{princ_item}{gravar_item}
    {biset_item}{amrap_item}
  </div>
  </div>{footer(2, nome, bloco, rot_semana)}</div>'''

    # ---------- PÁGINAS DE TREINO
    por_semana = {s['numero']: s for s in semanas}
    paginas_treino = []
    n = 3
    for p in pag:
        sem = por_semana[p['semana']]
        corpo = ''
        for tipo, num in p['blocos']:
            if tipo == 'aqc':
                corpo += aqc_block(D['aqc'])
            else:
                corpo += treino_table(num, sem['treinos'][num], dia_de.get('T' + num, ''), p['semana'])
        paginas_treino.append(f'''<div class="page light">{header(f"SEMANA {p['semana']:02d}", f"Bloco {bloco:02d}{data_semana(p['semana'])}", GOR)}
  <div class="body">{corpo}</div>{footer(n, nome, bloco, f"Semana {p['semana']:02d}")}</div>''')
        n += 1

    titulo = f'Plano de Treinamento — {nome} — Bloco {bloco:02d}'
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>{e(titulo)}</title>'
            f'<style>{css()}</style></head><body>{cover}{perfil}{"".join(paginas_treino)}</body></html>')
