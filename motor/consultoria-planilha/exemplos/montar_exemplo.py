# Planilha de EXEMPLO FICTÍCIO (não é aluno real) para o teste de regressão do template.
# Uso: python montar_exemplo.py [planilha-base Consultoria_3x.xlsx]  (padrão: arquivo do projeto)
import openpyxl, datetime, sys
BASE = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/knowledge/Consultoria_3x.xlsx'
wb = openpyxl.load_workbook(BASE)
al, bl, pr, mc = wb['aluno 01'], wb['bloco 01'], wb['prs'], wb['macro']
al['C2'] = 'Aluno Exemplo'
al['C3'] = 'Exemplo fictício para teste do template'
for col, t in zip('BDF', ['T01', 'T02', 'T03']):
    al[f'{col}6'] = t
al['A9'] = 'Exemplo fictício: dados criados só para testar o layout.'
for r, (ex, s, rp, kg, obs) in zip(range(13, 16), [
        ('Mobilidade de quadril', 2, '10', None, 'https://www.youtube.com/watch?v=exemplo'),
        ('Prancha', 3, '30s', None, None),
        ('Agachamento goblet', 2, '10', 12, None)]):
    al[f'A{r}'], al[f'B{r}'], al[f'C{r}'] = ex, s, rp
    if kg: al[f'D{r}'] = kg
    if obs: al[f'E{r}'] = obs
mc['B6'] = datetime.datetime(2026, 1, 5)
PRS = {'Agachamento': (5, 100), 'Supino': (5, 70), 'Terra': (3, 130), 'Arranco': (3, 50)}
for r in range(6, 13):
    nome = pr[f'A{r}'].value
    if nome in PRS:
        pr[f'B{r}'], pr[f'C{r}'] = PRS[nome]
RM = {k: reps_kg[1] / (1.0278 - 0.0278 * reps_kg[0]) for k, reps_kg in PRS.items()}
for r in range(6, 13):
    nome = pr[f'A{r}'].value
    for c, f in zip('DEFGH', (1, .95, .9, .85, .8)):
        pr[f'{c}{r}'] = round(RM[nome] * f, 4) if nome in RM else None
# valores fixos no lugar das fórmulas (sem recálculo disponível), mesmas contas da planilha
ini = datetime.datetime(2026, 1, 5)
for c, d in zip(['C', 'I', 'O', 'U'], range(0, 28, 7)):
    for r in (3, 18, 33):
        if bl[f'{c}{r}'].value is not None: bl[f'{c}{r}'] = ini + datetime.timedelta(days=d)
pr['B3'] = ini
LINHA_PR = {'Agachamento': 6, 'Supino': 7, 'Terra': 8, 'Arranco': 11}
TREINOS = {6: [('Agachamento', 3, 5, 60, 'aquecimento'), ('Agachamento', 4, 5, 85, 'principal'),
               ('Supino', 4, 6, 60, None), ('Remada curvada', 3, 10, 40, 'biset'),
               ('Prancha lateral', 3, '30s', None, 'biset')],
           21: [('Arranco', 5, 3, 35, 'gravar'), ('Levantamento terra', 4, 4, 100, None),
                ('Desenvolvimento com halteres', 3, '8 - 12', 14, None), ('Afundo', 3, 10, 20, None)],
           36: [('Agachamento frontal', 4, 5, 60, None), ('Supino inclinado', 3, 8, 50, None),
                ('Barra fixa', 3, 'AMRAP', None, 'amrap'), ('Elevação pélvica', 3, 12, 60, None)]}
for r0, exs in TREINOS.items():
    for i, (ex, s, rp, kg, obs) in enumerate(exs):
        r = r0 + i
        bl[f'B{r}'], bl[f'C{r}'], bl[f'D{r}'] = ex, s, rp
        if kg is not None: bl[f'E{r}'] = kg
        if obs: bl[f'G{r}'] = obs
        base = next((b for b in LINHA_PR if b.lower() in ex.lower()), None)
        bl[f'F{r}'] = round(kg / RM[base], 4) if base and kg else None
wb.save('exemplo.xlsx')
