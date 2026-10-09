# -*- coding: utf-8 -*-
"""
Gera o PDF de entrega do aluno a partir de dados.json (+ contexto.json opcional).

Uso:
  python gerar_pdf.py pasta/dados.json [--contexto contexto.json] [--saida arquivo.pdf]

contexto.json (opcional; só conteúdo aprovado por Miguel — nunca inventado):
{
  "prs": [ {"exercicio": "Agachamento", "kg": 100, "data": "12/09/2026", "fonte": "teste de 1RM / vídeo / competição"} ],
  "usa_pse": true                                                   # só se o aluno usa PSE
}
Decisão de Miguel: anamnese e feedback NÃO entram no PDF do aluno. "perfil_extra" (até 4 campos) existe no
template, mas só é usado se Miguel pedir explicitamente.
Depois de gerar, roda a verificação do PDF contra a planilha (verificar_pdf.py).
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Renderização fixa: sem isto, a suavização de fonte muda conforme a máquina e os textos da legenda
# podem quebrar em 3 linhas com palavra solta (regra de Miguel: 2 linhas, nunca palavra sozinha).
CHROMIUM_ARGS = ['--font-render-hinting=none']

def checar_trava():
    lock_p = os.path.join(HERE, '..', 'TEMPLATE_LOCK.json')
    if not os.path.exists(lock_p):
        sys.exit('ERRO: TEMPLATE_LOCK.json ausente. Template sem trava.')
    import travar_template
    lock = json.load(open(lock_p, encoding='utf-8'))
    atual = travar_template.hashes()
    dif = [k for k, v in lock['sha256'].items() if atual.get(k) != v]
    if dif:
        sys.exit('ERRO: o TEMPLATE MESTRE foi alterado (' + ', '.join(dif) + ') sem re-travar. '
                 'Mudanças visuais exigem autorização de Miguel. Restaure os arquivos originais '
                 'ou, se autorizado, rode travar_template.py.')
    return lock

def validar_contexto(ctx):
    if len(ctx.get('perfil_extra', [])) > 4:
        sys.exit('ERRO: perfil_extra aceita no máximo 4 itens (o card de perfil tem 2 colunas e precisa caber na página).')
    for x in ctx.get('perfil_extra', []):
        if not x.get('rotulo') or not x.get('valor'):
            sys.exit('ERRO: perfil_extra exige "rotulo" e "valor".')
    for p in ctx.get('prs', []):
        if not all(p.get(k) for k in ('exercicio', 'kg', 'data', 'fonte')):
            sys.exit('ERRO: todo PR precisa de exercicio, kg, data e FONTE (evidência). Nunca declarar PR sem evidência.')

def validar_orcamento(D, ctx):
    """Regra fixa da página 'Seu perfil': SEUS NÚMEROS tem 1 linha de no máximo 4 cartões.
    O espaço restante (observação geral, PSE/AMRAP na legenda, perfil_extra) é MEDIDO no PDF renderizado
    (guarda de layout em main), não estimado: estimativas antigas recusavam páginas que cabiam."""
    k = lambda x: ''.join(c for c in x.lower() if c.isalnum())
    chaves = {k(n) for n in D['rm']} | {k(p['exercicio']) for p in ctx.get('prs', [])}
    if len(chaves) > 4:
        sys.exit(f'ERRO: SEUS NÚMEROS comporta no máximo 4 cartões (1 linha) e há {len(chaves)} '
                 f'({", ".join(sorted(chaves))}). Miguel decide quais exercícios mostrar. '
                 'Escolha com --numeros no extrair_dados.py. PR real substitui o cartão estimado do MESMO exercício.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dados'); ap.add_argument('--contexto'); ap.add_argument('--saida')
    ap.add_argument('--sem-verificar', action='store_true')
    a = ap.parse_args()
    lock = checar_trava()
    D = json.load(open(a.dados, encoding='utf-8'))
    ctx = json.load(open(a.contexto, encoding='utf-8')) if a.contexto else {}
    validar_contexto(ctx)
    validar_orcamento(D, ctx)
    import template_mestre
    doc = template_mestre.render(D, ctx)
    nome = D['aluno']['nome'].replace(' ', '_')
    saida = a.saida or os.path.join(os.path.dirname(os.path.abspath(a.dados)), f'Entrega_{nome}_Bloco{int(D["bloco"]["numero"]):02d}.pdf')
    open(os.path.splitext(saida)[0] + '.html', 'w', encoding='utf-8').write(doc)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=CHROMIUM_ARGS); pg = b.new_page()
        pg.set_content(doc, wait_until='load'); pg.evaluate('document.fonts.ready')
        over = pg.evaluate('''() => [...document.querySelectorAll('.page.light')].map((p, i) => {
            const f = p.querySelector('.ftr').getBoundingClientRect().top;
            const kids = [...p.querySelector('.body').children];
            const bottom = Math.max(...kids.map(c => c.getBoundingClientRect().bottom));
            return {pagina: [...document.querySelectorAll('.page')].indexOf(p) + 1, folga_mm: (f - bottom) / 3.7795};
        })''')
        pg.pdf(path=saida, width='210mm', height='297mm', print_background=True, prefer_css_page_size=True)
        b.close()
    ruins = [o for o in over if o['folga_mm'] < 4]
    os.remove(os.path.splitext(saida)[0] + '.html')
    if ruins:
        os.remove(saida)
        perfil = [o for o in ruins if o['pagina'] == 2]
        treino = [o for o in ruins if o['pagina'] > 2]
        msg = 'ERRO DE LAYOUT: PDF NÃO gerado.'
        if perfil:
            msg += (f' Página 2 (Seu perfil) sem espaço (folga {perfil[0]["folga_mm"]:.1f} mm; mínimo 4 mm): '
                    'a observação geral da aba aluno (A9) está longa demais, ou há perfil_extra/PSE somando espaço. '
                    'Não reescreva o texto de Miguel: peça a ele para encurtar a observação ou dizer o que tirar.')
        if treino:
            msg += (' Páginas de treino ' + str([(o['pagina'], round(o['folga_mm'], 1)) for o in treino]) +
                    ': a paginação automática subestimou a altura (normalmente nomes de exercício ou notas de OBS longos '
                    'quebrando linha). NÃO corte a prescrição: avise Miguel (encurtar o texto na planilha ou autorizar ajuste do template).')
        sys.exit(msg + ' Nunca ajuste o template por conta própria.')
    print(f'PDF ({"template v" + lock["versao"]}) -> {saida}')
    if not a.sem_verificar:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'verificar_pdf.py'), saida, a.dados] + (['--contexto', a.contexto] if a.contexto else []))
        sys.exit(r.returncode)

if __name__ == '__main__':
    main()
