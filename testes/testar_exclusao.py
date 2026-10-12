# -*- coding: utf-8 -*-
"""Teste de "Excluir aluno de vez", só com alunos FICTÍCIOS, numa cópia temporária da Central (os dados e backups
reais não são tocados; a pasta Documentos também é falsa). Uso: python testes/testar_exclusao.py

Confere:
- a confirmação lista planilhas, PDFs (ficha, planejamento, resultados), anamnese, feedbacks, lixeira e backups;
- nome errado não apaga nada;
- com o nome certo some tudo do aluno: pasta, cópias na lixeira, leitura interrompida, parte dele em cada backup
  (inclusive o exportado em Documentos), linhas do registro de erros;
- o outro aluno (com identificador parecido: maria-teste x maria-teste-2) fica byte a byte igual, também nos backups.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="central-exclusao-"))
for parte in ("app", "motor", "icone"):
    shutil.copytree(RAIZ / parte, TMP / parte)
CASA = TMP / "casa"
(CASA / "Documents").mkdir(parents=True)
os.environ["HOME"] = os.environ["USERPROFILE"] = str(CASA)
sys.path.insert(0, str(TMP))

from app import armazenamento as A  # noqa: E402
from app import backup, exclusao  # noqa: E402
from app.config import DADOS, ENTRADA, LIXEIRA  # noqa: E402
from app.servidor import app  # noqa: E402

EXEMPLO = RAIZ / "motor" / "consultoria-planilha" / "exemplos" / "exemplo.xlsx"
falhas = []


def confere(cond, msg):
    print(("ok   " if cond else "FALHA ") + msg)
    if not cond:
        falhas.append(msg)


def popular(nome: str) -> dict:
    a = A.criar(nome)
    p = A.pasta(a["slug"])
    curto = nome.replace(" ", "")
    shutil.copy(EXEMPLO, p / "planilhas" / "20261001-100000_exemplo.xlsx")
    shutil.copy(EXEMPLO, p / "planilhas" / "20261001-100000_ajustada_exemplo.xlsx")
    (p / "trabalho" / "20261001-100000").mkdir(parents=True)
    (p / "trabalho" / "20261001-100000" / "dados.json").write_text("{}", encoding="utf-8")
    for arq in (f"{curto}_Bloco01.pdf", f"{curto}_Bloco01_Semana03.pdf", f"{curto}_Bloco01_Planejamento.pdf",
                f"{curto}_Bloco01_Resultados.pdf"):
        (p / "pdfs" / arq).write_bytes(b"%PDF-1.4 ficticio")
    A.gravar_json(p / "anamnese.json", {"respostas": {"Objetivo": "teste"}})
    A.gravar_json(p / "feedbacks.json", [{"id": "f1", "texto": "ok"}, {"id": "f2", "texto": "ok"}])
    (p / "anexos").mkdir()
    (p / "anexos" / "print.png").write_bytes(b"png")
    a["planilhas"] = [{"id": "20261001-100000"}, {"id": "20261002-090000"}]
    return A.salvar(a)


def assinatura(pasta: Path) -> dict:
    return {str(f.relative_to(pasta)): hashlib.sha1(f.read_bytes()).hexdigest() for f in sorted(pasta.rglob("*")) if f.is_file()}


try:
    alvo = popular("Maria Teste")
    outro = popular("Maria Teste")          # mesmo nome: slug maria-teste-2
    confere((alvo["slug"], outro["slug"]) == ("maria-teste", "maria-teste-2"), "dois alunos fictícios criados")
    # exclusão antiga do mesmo aluno na lixeira, leitura interrompida e registro de erros
    shutil.copytree(A.pasta(alvo["slug"]), LIXEIRA / "maria-teste__20261001-120000")
    (ENTRADA / "20261002-090000").mkdir(parents=True)
    (ENTRADA / "20261002-090000" / "exemplo.xlsx").write_bytes(EXEMPLO.read_bytes())
    log = DADOS / "central.log"
    log.write_text("início\n" + f"erro em {A.pasta('maria-teste')}\\pdfs\\x.pdf\n"
                   + f"erro em {A.pasta('maria-teste-2')}/pdfs/y.pdf\n" + "fim\n", encoding="utf-8")
    bk = backup.criar()
    exp = exclusao.pasta_exportacao()
    exp.mkdir(parents=True)
    exportado = exp / "central-consultoria_2026-10-01_1000.zip"
    exportado.write_bytes(backup.exportar_bytes())
    so_dele = backup.BACKUPS / "backup_2026-09-30.zip"
    with zipfile.ZipFile(so_dele, "w") as z:
        z.writestr("dados/alunos/maria-teste/aluno.json", "{}")

    antes_outro = assinatura(A.pasta(outro["slug"]))

    c = app.test_client()
    inv = c.get("/api/alunos/maria-teste/exclusao").get_json()
    texto = " | ".join(inv["itens"])
    print("     confirmação:", texto)
    print("     backups:", [b["nome"] for b in inv["backups"]])
    for trecho in ("2 planilhas recebidas", "2 PDFs de ficha", "1 PDF de planejamento", "1 PDF de resultados",
                   "Anamnese", "2 feedbacks semanais", "1 cópia na lixeira", "1 leitura interrompida",
                   "1 linha do registro"):
        confere(trecho in texto, f"confirmação mostra '{trecho}'")
    confere({b["nome"] for b in inv["backups"]} == {bk.name, exportado.name, so_dele.name},
            "confirmação lista os 3 backups com dados dele (inclusive o de Documentos)")

    r = c.delete("/api/alunos/maria-teste", json={"nome": "Maria Outra"})
    confere(r.status_code == 400 and A.pasta("maria-teste").exists(), "nome errado não apaga nada")

    r = c.delete("/api/alunos/maria-teste", json={"nome": "maria  teste"}).get_json()
    confere(r["ok"] and not r["falhas_backup"] and not r["sobrou"], "nome certo (sem diferença de maiúscula) exclui")
    confere(not A.pasta("maria-teste").exists(), "pasta do aluno apagada")
    confere(not list(LIXEIRA.glob("maria-teste__*")), "cópia na lixeira apagada")
    confere(not (ENTRADA / "20261002-090000").exists(), "leitura interrompida apagada")
    confere(not list(DADOS.glob(".tmp_*")), "nenhum temporário sobrou")
    linhas = log.read_text(encoding="utf-8")
    confere("maria-teste\\pdfs" not in linhas and "maria-teste-2/pdfs/y.pdf" in linhas and "início" in linhas,
            "registro de erros: só as linhas dele saíram")
    for z in (bk, exportado):
        nomes = zipfile.ZipFile(z).namelist()
        confere(not any(n.startswith(("dados/alunos/maria-teste/", "dados/lixeira/maria-teste__")) for n in nomes)
                and any(n.startswith("dados/alunos/maria-teste-2/") for n in nomes),
                f"{z.name}: sem ele, com o outro aluno")
    confere(not so_dele.exists(), "backup que só tinha ele foi apagado")
    confere(assinatura(A.pasta(outro["slug"])) == antes_outro, "outro aluno intacto (byte a byte)")
    confere(c.get("/api/alunos/maria-teste/exclusao").status_code == 404, "nada mais a excluir")
    confere(json.loads(c.get("/api/lixeira").data) == [], "lixeira vazia")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("\n" + ("TUDO CERTO" if not falhas else f"{len(falhas)} FALHA(S)"))
sys.exit(1 if falhas else 0)
