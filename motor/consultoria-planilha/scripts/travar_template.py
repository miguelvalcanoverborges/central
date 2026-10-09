# -*- coding: utf-8 -*-
"""Trava (ou re-trava) o template mestre. Só usar quando Miguel AUTORIZAR uma mudança de layout.
Uso: python travar_template.py --versao 1.1 --autorizado-por "Miguel" --motivo "..."
"""
import argparse, datetime, hashlib, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ARQS = ['template_mestre.py', 'template_mestre.css']
ASSETS = ['../assets/KronaOne.ttf', '../assets/Exo2.ttf', '../assets/gorilla_white.png', '../assets/halftone.png']

def hashes():
    out = {}
    for a in ARQS + ASSETS:
        with open(os.path.join(HERE, a), 'rb') as f:
            out[os.path.basename(a)] = hashlib.sha256(f.read()).hexdigest()
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--versao', required=True); ap.add_argument('--autorizado-por', required=True)
    ap.add_argument('--motivo', default='')
    a = ap.parse_args()
    lock = {'versao': a.versao, 'autorizado_por': a.autorizado_por, 'motivo': a.motivo,
            'data': datetime.date.today().isoformat(), 'sha256': hashes()}
    with open(os.path.join(HERE, '..', 'TEMPLATE_LOCK.json'), 'w', encoding='utf-8') as f:
        json.dump(lock, f, indent=1, ensure_ascii=False)
    print('Template travado na versão', a.versao)
