# -*- coding: utf-8 -*-
"""Preenche cópias das planilhas de respostas (ANAMNESE e FEEDBACK) com respostas FICTÍCIAS para teste.
Uso: python testes/montar_formularios_teste.py ANAMNESE_respostas.xlsx FEEDBACK_respostas.xlsx pasta_saida"""
import datetime as dt
import sys
from pathlib import Path

import openpyxl

an, fb, saida = sys.argv[1], sys.argv[2], Path(sys.argv[3])
saida.mkdir(parents=True, exist_ok=True)

wb = openpyxl.load_workbook(an)
ws = wb["Respostas ao formulário 1"]
ws.append([dt.datetime(2026, 7, 28, 19, 10), "Aluno Doze Semanas", "10/03/1990", "Analista de sistemas", "1,78", "82",
           "aluno@exemplo.com", "Não", None, "Nenhuma", "Sim", "Ombro direito, no supino e em desenvolvimentos",
           "Tendinite no ombro (2023)", "Sim", "Musculação 3x por semana e corrida leve aos domingos",
           "6 horas", "Às vezes, quando trabalho até tarde", "Não", "Socialmente, fins de semana",
           "Razoável, como bem durante a semana", "Trabalho sentado das 8h às 18h, home office",
           "Agachamento e levantamento terra", "Supino com barra, porque o ombro incomoda", "3", "1 hora",
           "Depois das 19h", "Academia perto de casa",
           "Quero ficar mais forte no agachamento e no terra e treinar sem dor no ombro"])
ws.append([dt.datetime(2026, 7, 20, 9, 0), "Outra Pessoa Ficticia", "01/01/1985", "Professora", "1,65", "60", "",
           "Não", None, "Nenhuma", "Não", None, "Nenhuma", "Não", None, "8 horas", "Não", "Não", "Não", "Boa",
           "Rotina tranquila", "Nenhum", "Nenhum", "4", "45 minutos", "Manhã", "Em casa", "Saúde"])
wb.save(saida / "ANAMNESE_teste.xlsx")

wb = openpyxl.load_workbook(fb)
ws = wb["Respostas ao formulário 1"]
ws.append([dt.datetime(2026, 9, 26, 20, 0), "Aluno Doze Semanas", "Boa (faltei 1 treino)",
           "Agachamento, senti que a técnica melhorou", "Supino com barra, o ombro incomodou na última série",
           "Sim", "Ombro direito, leve, no supino", "Boa", "Sim",
           "Trocar o supino com barra por halteres e ter mais trabalho de técnica no arranco"])
ws.append([dt.datetime(2026, 10, 3, 19, 30), "Aluno Doze Semanas", "Ótima (fiz todos os treinos)",
           "Supino com halteres, sem dor", "Não", "Não", None, "Muito boa", "Sim", "Nenhuma, está ótimo"])
wb.save(saida / "FEEDBACK_teste.xlsx")
print("ok")
