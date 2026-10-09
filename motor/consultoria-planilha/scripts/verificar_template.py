# -*- coding: utf-8 -*-
"""Teste de regressão do template mestre.
1) Confere a trava (hash dos arquivos do template).
2) Roda o fluxo completo na planilha de exemplo (exemplos/exemplo.xlsx, aluno fictício) e compara, pixel a pixel,
   cada página com o PDF APROVADO (referencia/). Qualquer diferença = o design mudou.
Uso: python verificar_template.py"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import travar_template, json
from PIL import Image, ImageChops

lock = json.load(open(os.path.join(RAIZ, 'TEMPLATE_LOCK.json'), encoding='utf-8'))
dif = [k for k, v in lock['sha256'].items() if travar_template.hashes().get(k) != v]
print('Trava:', 'OK (v' + lock['versao'] + ')' if not dif else 'ALTERADO → ' + ', '.join(dif))
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(HERE, 'extrair_dados.py'), os.path.join(RAIZ, 'exemplos', 'exemplo.xlsx'), '--saida', tmp], check=True, capture_output=True)
novo = os.path.join(tmp, 'novo.pdf')
r = subprocess.run([sys.executable, os.path.join(HERE, 'gerar_pdf.py'), os.path.join(tmp, 'dados.json'), '--saida', novo, '--sem-verificar'], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip())
ref = os.path.join(RAIZ, 'referencia', f'REFERENCIA_v{lock["versao"]}_exemplo.pdf')   # sempre a da versão travada
for tag, f in (('ref', ref), ('new', novo)):
    subprocess.run(['pdftoppm', '-r', '80', '-png', f, os.path.join(tmp, tag)], check=True)
pr = sorted(x for x in os.listdir(tmp) if x.startswith('ref-')); pn = sorted(x for x in os.listdir(tmp) if x.startswith('new-'))
falhas = 0
if len(pr) != len(pn): print(f'✗ nº de páginas difere: {len(pr)} vs {len(pn)}'); falhas += 1
for a, b in zip(pr, pn):
    ia, ib = Image.open(os.path.join(tmp, a)).convert('RGB'), Image.open(os.path.join(tmp, b)).convert('RGB')
    bbox = ImageChops.difference(ia, ib).getbbox()
    print(f'  página {a[4:-4]}:', 'idêntica' if bbox is None else f'DIFERENTE em {bbox}')
    falhas += bbox is not None
print('RESULTADO:', 'PASSOU — design idêntico ao aprovado' if not falhas and not dif else 'FALHOU')
sys.exit(1 if falhas or dif else 0)
