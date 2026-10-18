# -*- coding: utf-8 -*-
"""Confere o PDF final contra dados.json (que veio da planilha): exercícios, séries, reps, cargas,
%1RM, AQC, 1RM estimados, nome, objetivo, datas. Sai com código 1 se houver divergência."""
import argparse, json, re, subprocess, sys

def norm(t): return re.sub(r'\s+', ' ', t).strip()
def fmt(n):
    """Mesmo formato do template: None -> '—'; 10.0 -> '10'; 2.5 -> '2,5'; texto fica como está."""
    if n is None: return '—'
    if isinstance(n, str): return n
    return str(int(n)) if float(n).is_integer() else str(n).replace('.', ',')

def contem_em_ordem(palavras, texto):
    """Todas as palavras aparecem no texto, na ordem (outras palavras podem ficar no meio)."""
    it = iter(texto.split())
    return all(any(w == t for t in it) for w in palavras)

def acha_linha(seg, nome, want, pct=None):
    """Procura a linha do exercício: a linha com séries/reps/carga (want) e, perto dela, o nome e o %1RM.
    Nome curto: tudo na mesma linha. Nome longo que quebrou em 2 linhas no PDF: o nome aparece, em ordem,
    entre até 3 linhas acima e 1 abaixo, e o %1RM (centralizado na célula) pode ficar numa dessas linhas."""
    hifen = lambda x: re.sub(r'\s*-\s*', '-', x)   # o pdftotext às vezes come o espaço de "3 - 4" em coluna estreita
    # valor inteiro, não pedaço de outro: "3" não casa com "3-4", "4" não casa com "40 kg"
    tem = lambda w, l: re.search(r'(?<![\w,\-])' + re.escape(hifen(w)) + r'(?![\w,\-])', hifen(l)) is not None
    for i, l in enumerate(seg):
        if not all(tem(w, l) for w in want):
            continue
        janela = seg[max(0, i - 3):i + 2]
        nome_ok = nome in l or contem_em_ordem(nome.split(), ' '.join(janela))
        pct_ok = pct is None or any(tem(pct, x) for x in janela)
        if nome_ok and pct_ok:
            return True
    return False


def aquecimento_compacto(rows):
    """v1.13: quais séries de aquecimento viram sub-linha da principal (mesma regra do template, refeita aqui para
    a conferência não depender dele): degraus seguidos do mesmo exercício logo antes da série não-aquecimento dele.
    Devolve {índice da principal: [degraus]} e o conjunto dos índices dos degraus incorporados."""
    sub, usados, pend = {}, set(), []
    eh_aq = lambda r: 'aquecimento' in (r.get('obs') or '').lower()
    for i, r in enumerate(rows):
        if eh_aq(r):
            if pend and rows[pend[-1]]['ex'] != r['ex']:
                pend = []
            pend.append(i); continue
        if pend and rows[pend[0]]['ex'] == r['ex']:
            sub[i] = [rows[j] for j in pend]; usados |= set(pend)
        pend = []
    return sub, usados


def texto_degrau(a):
    reps = fmt(a['reps']); kg = f"{fmt(a['kg'])} kg" if a.get('kg') else ''
    if (a.get('sets') or 1) == 1:
        return f'{kg} × {reps}' if kg else f'1×{reps}'
    return f"{fmt(a['sets'])}×{reps}" + (f' com {kg}' if kg else '')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('pdf'); ap.add_argument('dados'); ap.add_argument('--contexto')
    a = ap.parse_args()
    D = json.load(open(a.dados, encoding='utf-8')); ctx = json.load(open(a.contexto, encoding='utf-8')) if a.contexto else {}
    txt = subprocess.run(['pdftotext', '-layout', a.pdf, '-'], capture_output=True, text=True).stdout
    paginas = [norm(p) for p in txt.split('\f')]
    tudo = ' '.join(paginas)
    erros, ok = [], 0
    def chk(cond, msg):
        nonlocal ok
        if cond: ok += 1
        else: erros.append(msg)
    cp = lambda t: re.sub(r'\s+', '', t).upper()
    raw = subprocess.run(['pdftotext', '-raw', a.pdf, '-'], capture_output=True, text=True).stdout.split('\f')
    pg = [cp(x) for x in raw]          # compacto, ordem de leitura (imune a letter-spacing e colunas)
    chk(cp(D['aluno']['nome']) in pg[0], 'nome do aluno ausente na capa')
    if D['bloco'].get('inicio'): chk(cp(D['bloco']['inicio']) in pg[0], 'data de início ausente na capa')
    chk(cp(f'BLOCO {int(D["bloco"]["numero"]):02d}') in pg[0], 'título do bloco ausente na capa')
    if D['bloco'].get('inicio'):   # data de início de cada semana no subtítulo
        import datetime as _dt
        ini = _dt.datetime.strptime(D['bloco']['inicio'], '%d/%m/%Y').date()
        for s_ in D['semanas']:
            d_ = ini + _dt.timedelta(days=7 * (s_['numero'] - 1))
            chk(cp(f'BLOCO {int(D["bloco"]["numero"]):02d} · {d_:%d/%m}') in ''.join(pg[1:]), f'data da semana {s_["numero"]:02d} ausente')
    # v1.15: sem a página de perfil; a observação geral abre a 1ª página de treino
    for t in D.get('observacoes', []):
        chk(cp('Observação:' + t) in pg[1], f'observação ausente na 1ª página de treino: {t}')
    chk('COMOLERASUAFICHA' not in ''.join(pg), 'legenda "Como ler a sua ficha" ainda na ficha')
    n_links = len([1 for q in D.get('aqc', []) if q.get('link')]) + sum(1 for s in D['semanas'] for rows in s['treinos'].values() for r in rows if r.get('link'))
    chk(' '.join(raw).count('▶') == n_links, f'ícones de vídeo ▶: esperado {n_links}')   # v1.14: só o ícone, sem título
    n_grav = sum(1 for s in D['semanas'] for rows in s['treinos'].values() for r in rows if r.get('obs') and 'gravar' in r['obs'].lower())
    chk(sum(x.count('GRAVAR') for x in pg[1:]) == n_grav, f'etiquetas GRAVAR: esperado {n_grav}')
    for s in D['semanas']:
        for rows in s['treinos'].values():
            for r in rows:
                if r['pct'] is not None and round(r['pct'] * 100) >= 80 and 'aquecimento' not in (r.get('obs') or '').lower():
                    chk(bool(r.get('obs')) and 'gravar' in r['obs'].lower(), f'S{s["numero"]:02d} {r["ex"]} com 80% ou mais sem GRAVAR')
    # v1.10: faixa de repetições → ANOTAR na linha
    n_anot = sum(1 for s in D['semanas'] for rows in s['treinos'].values() for r in rows if r.get('obs') and 'anotar' in r['obs'].lower())
    chk(sum(x.count('ANOTAR') for x in pg[1:]) == n_anot, f'etiquetas ANOTAR: esperado {n_anot}')
    for s in D['semanas']:
        for rows in s['treinos'].values():
            for r in rows:
                if re.fullmatch(r'\d+ - \d+', str(r['reps'])) or 'amrap' in str(r['reps']).lower():
                    chk(bool(r.get('obs')) and 'anotar' in r['obs'].lower(), f'S{s["numero"]:02d} {r["ex"]} com faixa de repetições ou AMRAP sem ANOTAR')
    # sequência de linhas por semana/treino
    linhas = [norm(l) for l in txt.splitlines()]
    sem = tre = None; blocos = {}
    for l in linhas:
        m = re.match(r'^SEMANA (\d+)$', l)
        if m: sem = int(m.group(1)); tre = None; continue
        m = re.match(r'^TREINO (\d+)\b', l)
        if m: tre = m.group(1); blocos.setdefault((sem, tre), []); continue
        if l.startswith('AQC '): tre = 'AQC'; blocos.setdefault((sem, 'AQC'), []); continue
        if tre: blocos[(sem, tre)].append(l)
    for s in D['semanas']:
        for num, rows in s['treinos'].items():
            seg = blocos.get((s['numero'], num), [])
            chk(bool(seg), f'Semana {s["numero"]} Treino {num} não encontrado no PDF')
            sub, usados = aquecimento_compacto(rows)
            seg_c = cp(' '.join(seg))
            for i, ps in sub.items():   # v1.13: "Aquecimento 55 kg × 3 · 59 kg × 2" logo abaixo do nome da principal
                esperado = 'Aquecimento ' + ' · '.join(texto_degrau(a) for a in ps)
                chk(re.search(re.escape(cp(rows[i]['ex'])) + r'.{0,40}?' + re.escape(cp(esperado)), seg_c) is not None,
                    f'S{s["numero"]:02d} T{num}: aquecimento divergente → {rows[i]["ex"]} | esperado {esperado}')
            for k, r in enumerate(rows):
                if k in usados:
                    continue
                want = [str(fmt(r['sets'])), str(r['reps'])] + ([fmt(r['kg']) + ' kg'] if r['kg'] else [])
                pct = f"{round(r['pct']*100)}%" if r['pct'] is not None else None
                hit = acha_linha(seg, r['ex'], want, pct)
                chk(hit, f'S{s["numero"]:02d} T{num}: linha divergente → {r["ex"]} | esperado {" ".join(want + ([pct] if pct else []))}')
    if D.get('aqc'):
        seg = blocos.get((D['semanas'][0]['numero'], 'AQC'), [])
        for q in D['aqc']:
            kgw = [fmt(q['kg']) + ' kg'] if isinstance(q.get('kg'), (int, float)) else []
            chk(acha_linha(seg, q['ex'], [fmt(q['sets']), str(q['reps'])] + kgw), f'AQC divergente → {q["ex"]} {" ".join(kgw)}')
    print(f'VERIFICAÇÃO: {ok} itens conferidos · {len(erros)} divergência(s)')
    for e in erros: print('  ✗', e)
    sys.exit(1 if erros else 0)

if __name__ == '__main__':
    main()
