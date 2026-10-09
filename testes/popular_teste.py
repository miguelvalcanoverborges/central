# -*- coding: utf-8 -*-
"""Popula a Central (servidor rodando em 127.0.0.1:8765) com um aluno FICTÍCIO de 12 semanas.
Uso: python testes/popular_teste.py caminho/planilha_ficticia.xlsx"""
import sys

import requests

B = "http://127.0.0.1:8765"
r = requests.post(B + "/api/planilha", files={"arquivo": ("Consultoria_3x Aluno Doze.xlsx", open(sys.argv[1], "rb"))}).json()
print("aluno:", r["slug"])
