# -*- coding: utf-8 -*-
"""Teste dos Modelos de bloco, só com alunos FICTÍCIOS, numa cópia temporária da Central (os dados reais não são tocados).
Uso: python testes/testar_modelos.py            (imprime o que conferiu; código de saída ≠ 0 se algo falhar)

As planilhas fictícias são feitas a partir das planilhas matriz em branco de Miguel (matrizes/, layout novo:
exercício de cada semana na própria coluna B/I/P/W, dados em C/J/Q/X), preenchidas sem openpyxl (gráficos e fórmulas
ficam), e a partir do exemplo do motor (layout antigo).

1. "Aluno Modelo" (fictício, layout novo) → salva o bloco 02 como modelo, sem criar aluno no painel;
2. aluno fictício (layout novo, só bloco 01) entra na Central, e o PDF do bloco 01 sai e é conferido;
3. "Novo bloco a partir de modelo" no bloco 02: cada kg (= %1RM × 1RM digitado, múltiplo de 1 kg), exercício de cada
   semana na sua coluna, kg em branco nos acessórios e sem 1RM, aba prs, resto da planilha idêntico (gráficos inclusive);
4. a planilha montada volta pela Central: leitura, aba Dados (VTT/VTR) e PDF conferido, sem divergência de %1RM;
5. ciclo novo com a matriz em branco de 3 treinos;
6. layout antigo (exemplo do motor) continua funcionando.
"""
import io
import math
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="central-modelos-"))
for parte in ("app", "motor", "icone", "matrizes"):
    shutil.copytree(RAIZ / parte, TMP / parte)
sys.path.insert(0, str(TMP))

from app import armazenamento as A  # noqa: E402
from app import dados as DADOS  # noqa: E402
from app import modelos as M  # noqa: E402
from app import xlsx_celulas as XL  # noqa: E402
from app.servidor import app  # noqa: E402

falhas = []


def confere(cond, msg):
    print(("  ok  " if cond else "  FALHOU  ") + msg)
    if not cond:
        falhas.append(msg)


L = XL.col_letras
BRZ = lambda reps, kg: kg / (1.0278 - 0.0278 * reps)  # noqa: E731
COLS_NOVO = [(2, 3), (9, 10), (16, 17), (23, 24)]    # (exercício, SETS) de cada semana
PRS_LINHA = {1: 6, 2: 18, 3: 30}
NOMES_PRS = ["Agachamento", "Supino", "Terra", "Desenvolvimento", "Remada", "Arranco", "Arremesso"]


def base(ex):
    n = M.X.sem_acento(ex)
    return next((lab for k, lab in M.X.BASES if k in n), None)


def preencher(matriz: Path, saida: Path, nome: str, blocos: dict, prs: dict):
    """Planilha FICTÍCIA no layout novo. blocos = {n: [treino: [(ex, [(sets, reps, kg, obs) ou None] × 4)]]};
    prs = {n: {'Agachamento': (reps, kg)}}. %1RM guardado = kg ÷ 1RM, como a planilha calcularia."""
    val, cache = {"aluno 01": {"C2": nome, "C3": "Ficar mais forte (fictício)", "B6": "T01", "D6": "T02", "F6": "T03"},
                  "prs": {}}, {"prs": {}}
    for n, d in prs.items():
        for ex, (reps, kg) in d.items():
            r = PRS_LINHA[n] + NOMES_PRS.index(ex)
            val["prs"][f"B{r}"], val["prs"][f"C{r}"] = reps, kg
            cache["prs"][f"D{r}"] = round(BRZ(reps, kg), 4)
    for n, treinos in blocos.items():
        aba = f"bloco {n:02d}"
        val[aba], cache[aba] = {}, {}
        rm = {k: BRZ(*v) for k, v in prs.get(n, {}).items()}
        for t, linhas in enumerate(treinos):
            for i, (ex, semanas) in enumerate(linhas):
                r = 6 + 15 * t + i
                for (ce, c0), s in zip(COLS_NOVO, semanas):
                    if not s:
                        continue
                    sets, reps, kg, obs = s
                    nome_sem = ex if isinstance(ex, str) else ex[COLS_NOVO.index((ce, c0))]
                    val[aba][f"{L(ce)}{r}"] = nome_sem
                    val[aba].update({f"{L(c0)}{r}": sets, f"{L(c0 + 1)}{r}": reps, f"{L(c0 + 2)}{r}": kg,
                                     f"{L(c0 + 4)}{r}": obs})
                    b = base(nome_sem)
                    cache[aba][f"{L(c0 + 3)}{r}"] = round(kg / rm[b], 4) if (kg and b in rm) else ""
    novo, _ = XL.escrever(matriz.read_bytes(), val, cache)
    saida.write_bytes(novo)


def sem(*v):   # 4 semanas iguais com progressão de séries
    return [v, v, v, v]


# ---------------------------------------------------------------- planilhas fictícias
matriz3 = TMP / "matrizes" / "Consultoria_3x.xlsx"
modelo_xlsx = TMP / "Consultoria_3x Aluno Modelo.xlsx"
B2 = [
    [("Agachamento", [(3, 5, 70, "aquecimento"), (3, 5, 72, "aquecimento"), (3, 5, 75, "aquecimento"), None]),
     ("Agachamento", [(4, 5, 95, "principal"), (5, 5, 95, "principal"), (5, 5, 100, "principal"), (3, 5, 90, "principal")]),
     ("Supino", sem(4, 6, 65, None)),
     ("Remada curvada", sem(3, 10, 40, "biset")),
     ("Prancha lateral", sem(3, "30s", None, "biset"))],
    [("Arranco", sem(5, 3, 40, "gravar")),
     (["Levantamento terra", "Levantamento terra", "Levantamento terra romeno", "Levantamento terra"], sem(4, 4, 110, None)),
     ("Desenvolvimento com halteres", sem(3, "8 - 12", 14, None))],
    [("Agachamento frontal", sem(4, 5, 70, None)),
     ("Supino inclinado", sem(3, 8, 50, None)),
     ("Barra fixa", sem(3, "AMRAP", None, None))],
]
B1 = [[("Agachamento", sem(3, 8, 60, None)), ("Supino", sem(3, 8, 50, None))],
      [("Levantamento terra", sem(3, 6, 90, None))],
      [("Remada curvada", sem(3, 10, 35, None))]]
preencher(matriz3, modelo_xlsx, "Aluno Modelo", {1: B1, 2: B2},
          {1: {"Agachamento": (5, 100), "Supino": (5, 70), "Terra": (3, 130), "Arranco": (3, 50)},
           2: {"Agachamento": (5, 110), "Supino": (5, 75), "Terra": (3, 140), "Arranco": (3, 55)}})
aluno_xlsx = TMP / "Consultoria_3x Aluno Teste Modelos.xlsx"
preencher(matriz3, aluno_xlsx, "Aluno Teste Modelos", {1: B1},
          {1: {"Agachamento": (5, 90), "Supino": (5, 60), "Terra": (3, 120)}})

cli = app.test_client()
print("Central temporária em", TMP)

print("1. Salvar como modelo (Aluno Modelo, layout novo, sem criar aluno)")
r = cli.post("/api/modelos/ler", data={"arquivo": (open(modelo_xlsx, "rb"), modelo_xlsx.name)},
             content_type="multipart/form-data").get_json()
confere(r["ok"] and r["blocos"] == [1, 2], f"blocos prescritos lidos: {r.get('blocos')}")
r2 = cli.post("/api/modelos", json={"token": r["token"], "arquivo": r["arquivo"], "aluno": r["aluno"],
                                     "blocos": [{"bloco": 1, "nome": "Adaptação 3x"}, {"bloco": 2, "nome": "Acumulação 3x"}]}).get_json()
confere(r2["ok"] and len(r2["modelos"]) == 2, "dois modelos salvos da mesma planilha")
mid = next(m["id"] for m in r2["modelos"] if m["nome"] == "Acumulação 3x")
modelo = M.carregar(mid)
t2 = modelo["treinos"][1]["linhas"][1]
confere([s["ex"] for s in t2["semanas"]][2] == "Levantamento terra romeno", "exercício de cada semana lido na sua coluna")
confere(abs(modelo["treinos"][0]["linhas"][1]["semanas"][0]["pct"] - 95 / BRZ(5, 110)) < 1e-3, "%1RM do modelo lido")
confere(modelo["treinos"][0]["linhas"][0]["semanas"][3] is None, "semana sem a linha fica vazia no modelo")
confere(cli.get("/api/alunos").get_json() == [], "nenhum aluno novo no painel")
confere(sorted(x["treinos"] for x in cli.get("/api/modelos").get_json()["matriz"]) == [2, 3, 4],
        "planilhas em branco 2x, 3x e 4x disponíveis")

print("2. Aluno fictício (layout novo) entra na Central")
r = cli.post("/api/planilha", data={"arquivo": (open(aluno_xlsx, "rb"), aluno_xlsx.name)},
             content_type="multipart/form-data").get_json()
confere(r["ok"], "planilha recebida")
slug, envio = r["slug"], r["envio"]
rv = cli.get(f"/api/revisao/{slug}/{envio}").get_json()
confere(rv.get("bloco") == 1 and any("Layout novo" in i for i in rv.get("infos", [])), "motor leu o bloco 01 no layout novo")
ex_s1 = [l["exercicio"] for l in rv["tabela"] if l["semana"] == 1]
confere(ex_s1 == ["Agachamento", "Supino", "Levantamento terra", "Remada curvada"], f"exercícios da semana 1: {ex_s1}")
g = cli.post(f"/api/revisao/{slug}/{envio}/gerar", json={"prs": []}).get_json()
confere(g["ok"], "PDF do bloco 01 gerado e conferido" + ("" if g["ok"] else ": " + str(g.get("erro"))))

print("3. Novo bloco a partir de modelo (bloco 02)")
op = cli.get(f"/api/alunos/{slug}/novo-bloco").get_json()
confere(op["padrao"] == "2", f"destino sugerido = bloco 02 (veio {op['padrao']})")
RMS = {"Agachamento": {"reps": 5, "kg": 100}, "Supino": {"reps": 6, "kg": 65}}      # Terra e Arranco sem 1RM
res = cli.post(f"/api/alunos/{slug}/novo-bloco", json={"modelo": mid, "destino": "2", "rm": RMS}).get_json()
confere(res["ok"], "planilha montada")
saida = A.pasta(slug) / res["arquivo"]
print("   para ajustar:", *res["pendencias"], sep="\n     - ")
wv = openpyxl.load_workbook(saida, data_only=True)
wf = openpyxl.load_workbook(saida)
ws = wv["bloco 02"]
rm = {k: BRZ(v["reps"], v["kg"]) for k, v in RMS.items()}
erros, n_kg, n_vazio = [], 0, 0
for ti, t in enumerate(modelo["treinos"]):
    for i, lin in enumerate(t["linhas"]):
        r = 6 + 15 * ti + i
        for w, (ce, c0) in enumerate(COLS_NOVO):
            s = lin["semanas"][w]
            if not s:
                if ws.cell(r, ce).value or ws.cell(r, c0).value:
                    erros.append(f"{L(ce)}{r}: deveria estar vazia")
                continue
            if ws.cell(r, ce).value != s["ex"]:
                erros.append(f"{L(ce)}{r}: {ws.cell(r, ce).value!r} ≠ {s['ex']!r}")
            if ws.cell(r, c0).value != s["sets"] or ws.cell(r, c0 + 1).value != s["reps"]:
                erros.append(f"{L(c0)}{r}: séries/reps")
            kg = ws.cell(r, c0 + 2).value
            if s["pct"] and s["base"] in rm:
                esp = math.floor(s["pct"] * rm[s["base"]] + 0.5)
                n_kg += kg == esp
                if kg != esp:
                    erros.append(f"{L(c0 + 2)}{r}: kg {kg} ≠ {esp}")
            elif kg is not None:
                erros.append(f"{L(c0 + 2)}{r}: deveria estar em branco ({kg})")
            else:
                n_vazio += 1
confere(not erros, f"{n_kg} cargas calculadas e {n_vazio} em branco conferidas" + ("" if not erros else " — " + "; ".join(erros[:6])))
confere(res["resumo"]["cargas"] == n_kg, "resumo bate")
confere(any("Sem 1RM de Terra" in p and "Levantamento terra romeno (semana 3)" in p for p in res["pendencias"]),
        "Terra sem 1RM listado por semana")
confere(any("Carga para preencher" in p and "Remada curvada" in p for p in res["pendencias"]), "acessórios listados")
pr = wv["prs"]
confere((pr["B18"].value, pr["C18"].value) == (5, 100) and (pr["B19"].value, pr["C19"].value) == (6, 65),
        "série de referência na aba prs (bloco 02)")
confere(str(wf["bloco 02"]["M6"].value).startswith("=IFERROR") and str(wf["prs"]["D18"].value).startswith("="),
        "fórmulas de %1RM e de 1RM mantidas")
za = zipfile.ZipFile(A.pasta(slug) / A.carregar(slug)["planilhas"][0]["arquivo"])
zb = zipfile.ZipFile(saida)
mapa = XL.mapa_abas(za)
mexidas = {mapa["bloco 02"], mapa["prs"], "xl/workbook.xml"}
iguais = all(za.read(i.filename) == zb.read(i.filename) for i in za.infolist() if i.filename not in mexidas)
confere(iguais and any("chart" in i.filename for i in zb.infolist()), "resto da planilha idêntico (gráficos inclusive)")

print("4. A planilha montada volta pela Central")
r = cli.post("/api/planilha", data={"arquivo": (open(saida, "rb"), aluno_xlsx.name), "slug": slug},
             content_type="multipart/form-data").get_json()
envio2 = r["envio"]
rv = cli.get(f"/api/revisao/{slug}/{envio2}").get_json()
confere(rv.get("bloco") == 2, "bloco 02 lido")
confere(not any("difere" in a or "não calculou" in a for a in rv.get("alertas", [])), "sem divergência de %1RM")
s3 = [l["exercicio"] for l in rv["tabela"] if l["semana"] == 3 and l["treino"] == "02"]
confere("Levantamento terra romeno" in s3, "PDF usa o exercício da semana 3")
g = cli.post(f"/api/revisao/{slug}/{envio2}/gerar", json={"prs": []}).get_json()
confere(g["ok"], "PDF do bloco 02 gerado e conferido" + ("" if g["ok"] else ": " + str(g.get("erro"))))
D = DADOS.analisar(DADOS.planilha_atual(A.carregar(slug)))
s5 = next(s for s in D["semanas"] if s["global"] == 5)
vtt = sum(s["sets"] * s["reps"] * (math.floor(s["pct"] * rm[s["base"]] + 0.5) if s["pct"] and s["base"] in rm else 0)
          for t in modelo["treinos"] for l in t["linhas"] for s in [l["semanas"][0]]
          if s and isinstance(s["reps"], int) and isinstance(s["sets"], int))
confere(abs(s5["vtt"] - vtt) < 0.5, f"aba Dados: VTT da semana 5 = {s5['vtt']} (esperado {vtt})")

print("5. Ciclo novo (matriz em branco de 3 treinos)")
res = cli.post(f"/api/alunos/{slug}/novo-bloco", json={"modelo": mid, "destino": "novo",
                                                        "rm": {"Agachamento": {"reps": 3, "kg": 120}}}).get_json()
confere(res["ok"] and res["bloco"] == 1, "ciclo novo montado no bloco 01")
wv = openpyxl.load_workbook(A.pasta(slug) / res["arquivo"], data_only=True)
confere(wv["aluno 01"]["C2"].value == "Aluno Teste Modelos", "nome do aluno")
confere([wv["aluno 01"][f"{c}6"].value for c in "BCDEF"] == ["T01", None, "T02", None, "T03"], "dias de treino do aluno")
confere(wv["bloco 01"]["P8"].value == "Supino" and wv["bloco 01"]["P22"].value == "Levantamento terra romeno", "modelo no bloco 01")
confere((wv["prs"]["B6"].value, wv["prs"]["C6"].value) == (3, 120), "1RM na aba prs (bloco 01)")
zc = zipfile.ZipFile(A.pasta(slug) / res["arquivo"])
confere(any("chart" in i.filename for i in zc.infolist()), "gráficos da matriz preservados")
r = cli.post("/api/modelos/matriz", data={"arquivo": (open(aluno_xlsx, "rb"), "cheia.xlsx")},
             content_type="multipart/form-data").get_json()
confere(not r["ok"], "planilha com prescrição recusada como matriz em branco")
r = cli.post("/api/modelos/matriz", data={"arquivo": (open(TMP / "matrizes" / "Consultoria_2x.xlsx", "rb"), "minha_2x.xlsx")},
             content_type="multipart/form-data").get_json()
confere(r["ok"] and r["matriz"]["treinos"] == 2, "trocar a matriz de 2 treinos")

print("6. Layout antigo (exemplo do motor)")
antigo = TMP / "Consultoria antiga.xlsx"
wb = openpyxl.load_workbook(TMP / "motor" / "consultoria-planilha" / "exemplos" / "exemplo.xlsx")
wb["aluno 01"]["C2"] = "Aluno Antigo"
wb.save(antigo)
r = cli.post("/api/planilha", data={"arquivo": (open(antigo, "rb"), antigo.name)}, content_type="multipart/form-data").get_json()
slug2 = r["slug"]
res = cli.post(f"/api/alunos/{slug2}/novo-bloco", json={"modelo": mid, "destino": "2", "rm": RMS}).get_json()
confere(res["ok"], "modelo do layout novo montado numa planilha do layout antigo")
w2 = openpyxl.load_workbook(A.pasta(slug2) / res["arquivo"], data_only=True)["bloco 02"]
confere(w2["B6"].value == "Agachamento" and w2["E7"].value == math.floor(modelo["treinos"][0]["linhas"][1]["semanas"][0]["pct"] * rm["Agachamento"] + 0.5),
        "nome em B e carga calculada no layout antigo")
confere(any("um nome por linha" in p for p in res["pendencias"]), "aviso da troca de exercício entre semanas")
r = cli.post("/api/planilha", data={"arquivo": (open(A.pasta(slug2) / res["arquivo"], "rb"), antigo.name), "slug": slug2},
             content_type="multipart/form-data").get_json()
g = cli.post(f"/api/revisao/{slug2}/{r['envio']}/gerar", json={"prs": []}).get_json()
confere(g["ok"], "PDF do layout antigo continua saindo" + ("" if g["ok"] else ": " + str(g.get("erro"))))

r = cli.delete(f"/api/modelos/{mid}").get_json()
confere(r["ok"] and not any(m["id"] == mid for m in cli.get("/api/modelos").get_json()["modelos"]), "modelo excluído")

if not falhas and not __import__("os").environ.get("MANTER"):
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRESULTADO:", "PASSOU" if not falhas else f"{len(falhas)} FALHA(S)")
sys.exit(1 if falhas else 0)
