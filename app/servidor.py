# -*- coding: utf-8 -*-
"""Servidor local da Central (só responde no próprio computador: 127.0.0.1)."""
import datetime as dt
import os
import platform
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

from . import planos  # noqa: E402
from . import armazenamento as A
from . import backup, planilha
from .config import ASSETS, ICONE, MOTOR, WEB, caminho_poppler

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
ULTIMO_PING = {"t": time.time(), "algum": False}
_trava = threading.Lock()          # uma operação de planilha por vez (o motor usa arquivos)


def _ok(**kw):
    return jsonify({"ok": True, **kw})


def _falha(msg, status=400, **kw):
    return jsonify({"ok": False, "erro": msg, **kw}), status


def _arquivo_do_aluno(slug: str, rel: str) -> Path:
    base = A.pasta(slug).resolve()
    p = (base / rel).resolve()
    if base not in p.parents or not p.exists():
        abort(404)
    return p


def _abrir_no_sistema(p: Path, mostrar_pasta=False):
    sistema = platform.system()
    if sistema == "Windows":
        if mostrar_pasta:
            subprocess.Popen(["explorer", "/select,", str(p)])
        else:
            os.startfile(str(p))  # noqa: S606  (abre no programa padrão: leitor de PDF, Excel…)
    elif sistema == "Darwin":
        subprocess.Popen(["open", "-R", str(p)] if mostrar_pasta else ["open", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p.parent if mostrar_pasta else p)])


# ------------------------------------------------------------------ páginas e arquivos estáticos
@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/web/<path:arq>")
def web(arq):
    return send_from_directory(WEB, arq)


@app.get("/fonts/<nome>")
def fontes(nome):
    if nome not in ("KronaOne.ttf", "Exo2.ttf"):
        abort(404)
    return send_from_directory(ASSETS, nome)


@app.get("/marca/gorila.png")
def gorila():
    return send_from_directory(ASSETS, "gorilla_white.png")


@app.get("/marca/halftone.png")
def halftone():
    return send_from_directory(ASSETS, "halftone.png")


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(ICONE, "gorila.ico")


@app.get("/marca/icone.png")
def icone_png():
    return send_from_directory(ICONE, "gorila_256.png")


@app.get("/api/ping")
def ping():
    ULTIMO_PING["t"] = time.time()
    ULTIMO_PING["algum"] = True
    return jsonify({"app": "central-consultoria", "ok": True})


# ------------------------------------------------------------------ alunos
@app.get("/api/alunos")
def alunos_lista():
    return jsonify([planilha.resumo(a) for a in A.listar()])


@app.get("/api/alunos/<slug>")
def aluno_detalhe(slug):
    a = A.carregar(slug)
    if not a:
        return _falha("Aluno não encontrado.", 404)
    return jsonify({**planilha.resumo(a), "planilhas": a.get("planilhas", []), "entregas": a.get("entregas", []),
                    "historico": a.get("historico", [])[:60]})


EDITAVEIS = {"nome", "status", "objetivo", "notas", "proxima_atualizacao"}


@app.patch("/api/alunos/<slug>")
def aluno_editar(slug):
    a = A.carregar(slug)
    if not a:
        return _falha("Aluno não encontrado.", 404)
    corpo = request.get_json() or {}
    dados = {k: v for k, v in corpo.items() if k in EDITAVEIS | {"plano_auto", "proxima_auto"}}
    mudou = []
    if "contrato" in corpo:
        try:
            planos.definir(a, (corpo["contrato"] or {}).get("plano", ""), (corpo["contrato"] or {}).get("inicio") or None)
        except ValueError as ex:
            return _falha(str(ex))
    if "nome" in dados and dados["nome"].strip() and dados["nome"].strip() != a["nome"]:
        a["nome"] = dados["nome"].strip()
        mudou.append("nome")
    if "status" in dados and dados["status"] in A.STATUS and dados["status"] != a.get("status"):
        A.registrar(a, f"Situação alterada para {dados['status']}")
        a["status"] = dados["status"]
    if "plano" in dados and dados["plano"] != a.get("plano"):
        a["plano"], a["plano_manual"] = dados["plano"], True
        mudou.append("plano")
    if dados.get("plano_auto"):
        a["plano_manual"] = False
    if "proxima_atualizacao" in dados and dados["proxima_atualizacao"] != a.get("proxima_atualizacao"):
        a["proxima_atualizacao"], a["proxima_manual"] = dados["proxima_atualizacao"], True
        mudou.append("próxima atualização")
    if dados.get("proxima_auto"):
        a["proxima_manual"] = False
    for k in ("objetivo", "notas"):
        if k in dados and dados[k] != a.get(k):
            a[k] = dados[k]
    if mudou:
        A.registrar(a, "Editado: " + ", ".join(mudou))
    A.salvar(a)
    if dados.get("plano_auto") or dados.get("proxima_auto"):
        ultimo = next((p for p in a.get("planilhas", []) if (A.pasta(slug) / "trabalho" / p["id"] / "dados.json").exists()), None)
        if ultimo:
            planilha._atualizar_aluno(slug, ultimo["id"], A.ler_json(A.pasta(slug) / "trabalho" / ultimo["id"] / "dados.json"))
    return _ok(aluno=planilha.resumo(A.carregar(slug)))


@app.post("/api/alunos/<slug>/renovar")
def aluno_renovar(slug):
    a = A.carregar(slug)
    if not a:
        return _falha("Aluno não encontrado.", 404)
    try:
        planos.renovar(a)
    except ValueError as ex:
        return _falha(str(ex))
    A.salvar(a)
    return _ok(aluno=planilha.resumo(a))


# ------------------------------------------------------------------ planos e resumo do mês
@app.get("/api/planos")
def planos_tabela():
    return jsonify(planos.tabela())


@app.put("/api/planos")
def planos_salvar():
    try:
        return _ok(planos=planos.salvar_tabela(request.get_json() or {}))
    except (TypeError, ValueError):
        return _falha("Valor inválido.")


@app.get("/api/resumo")
def resumo_mes():
    import datetime as _dt
    hoje = _dt.date.today()
    ano = int(request.args.get("ano") or hoje.year)
    mes = int(request.args.get("mes") or hoje.month)
    return jsonify(planos.resumo_mes(ano, mes))


@app.delete("/api/alunos/<slug>")
def aluno_excluir(slug):
    if not A.carregar(slug):
        return _falha("Aluno não encontrado.", 404)
    return _ok(lixeira=A.excluir(slug))


@app.get("/api/lixeira")
def lixeira():
    return jsonify(A.lixeira())


@app.post("/api/lixeira/<id_>/restaurar")
def lixeira_restaurar(id_):
    try:
        a = A.restaurar(id_)
    except (FileNotFoundError, FileExistsError) as ex:
        return _falha(str(ex))
    return _ok(slug=a["slug"])


# ------------------------------------------------------------------ planilha matriz
@app.post("/api/planilha")
def planilha_receber():
    f = request.files.get("arquivo")
    if not f or not f.filename.lower().endswith((".xlsx", ".xlsm")):
        return _falha("Envie a planilha matriz em formato .xlsx.")
    with _trava:
        r = planilha.receber(f.filename, f.read(), request.form.get("slug") or None)
    return jsonify(r) if r.get("ok") else (jsonify(r), 422)


@app.get("/api/revisao/<slug>/<envio>")
def revisao(slug, envio):
    if not A.carregar(slug):
        return _falha("Aluno não encontrado.", 404)
    return jsonify(planilha.revisao(slug, envio))


@app.post("/api/revisao/<slug>/<envio>/opcoes")
def revisao_opcoes(slug, envio):
    d = request.get_json() or {}
    with _trava:
        r = planilha.reextrair(slug, envio, usa_pse=d.get("usa_pse"),
                               numeros=d["numeros"] if "numeros" in d else "__manter__",
                               bloco=d["bloco"] if "bloco" in d else "__manter__")
    return jsonify(r)


@app.post("/api/revisao/<slug>/<envio>/prs")
def revisao_prs(slug, envio):
    estado_p = A.pasta(slug) / "trabalho" / envio / "estado.json"
    estado = A.ler_json(estado_p)
    estado["prs"] = (request.get_json() or {}).get("prs", [])
    A.gravar_json(estado_p, estado)
    return _ok()


@app.post("/api/revisao/<slug>/<envio>/gerar")
def revisao_gerar(slug, envio):
    with _trava:
        r = planilha.gerar(slug, envio, (request.get_json() or {}).get("prs", []))
    return jsonify(r)


@app.post("/api/revisao/<slug>/<envio>/vincular")
def revisao_vincular(slug, envio):
    destino = (request.get_json() or {}).get("slug")
    if not A.carregar(destino or ""):
        return _falha("Aluno de destino não encontrado.")
    with _trava:
        return jsonify(planilha.vincular(slug, envio, destino))


# ------------------------------------------------------------------ PDFs e arquivos
@app.get("/api/arquivo/<slug>/paginas")
def pdf_paginas(slug):
    p = _arquivo_do_aluno(slug, request.args["rel"])
    import pymupdf as fitz
    with fitz.open(p) as doc:
        return jsonify({"paginas": doc.page_count})


@app.get("/api/arquivo/<slug>/pagina")
def pdf_pagina(slug):
    p = _arquivo_do_aluno(slug, request.args["rel"])
    n = int(request.args.get("n", 0))
    zoom = min(float(request.args.get("zoom", 1.4)), 3.0)
    import io

    import pymupdf as fitz
    with fitz.open(p) as doc:
        png = doc[n].get_pixmap(matrix=fitz.Matrix(zoom, zoom)).tobytes("png")
    return send_file(io.BytesIO(png), mimetype="image/png", max_age=3600)


@app.post("/api/arquivo/<slug>/abrir")
def arquivo_abrir(slug):
    d = request.get_json() or {}
    p = _arquivo_do_aluno(slug, d.get("rel", ""))
    _abrir_no_sistema(p, mostrar_pasta=bool(d.get("pasta")))
    return _ok()


# ------------------------------------------------------------------ configurações
@app.get("/api/sistema")
def sistema():
    lock = A.ler_json(MOTOR / "TEMPLATE_LOCK.json", {})
    return jsonify({"template": lock.get("versao"), "template_data": lock.get("data"),
                    "poppler": bool(caminho_poppler()), "dados": str(A.pasta("x").parent.parent),
                    "backups": [{"nome": p.name, "kb": round(p.stat().st_size / 1024)} for p in backup.listar()[:30]]})


def _pasta_exportacao() -> Path:
    docs = Path.home() / "Documents"
    base = docs if docs.exists() else Path.home()
    p = base / "Central da Consultoria - Backups"
    p.mkdir(parents=True, exist_ok=True)
    return p


@app.post("/api/backup/exportar")
def backup_exportar():
    destino = _pasta_exportacao() / f"central-consultoria_{dt.datetime.now():%Y-%m-%d_%H%M}.zip"
    A.gravar_seguro(destino, backup.exportar_bytes())
    _abrir_no_sistema(destino, mostrar_pasta=True)
    return _ok(arquivo=str(destino))


@app.post("/api/backup/restaurar")
def backup_restaurar():
    f = request.files.get("arquivo")
    if not f:
        return _falha("Escolha o arquivo .zip do backup.")
    with _trava:
        ok, msg = backup.restaurar(f.read())
    return jsonify({"ok": ok, "mensagem": msg})


@app.post("/api/diagnostico")
def diagnostico():
    itens = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        itens.append({"nome": "Gerador de PDF (Chromium)", "ok": True})
    except Exception:  # noqa: BLE001
        itens.append({"nome": "Gerador de PDF (Chromium)", "ok": False, "dica": "Rode o INSTALAR de novo."})
    itens.append({"nome": "Conferência PDF × planilha (Poppler)", "ok": bool(caminho_poppler()),
                  "dica": "" if caminho_poppler() else "Rode o INSTALAR de novo (ele baixa o Poppler)."})
    itens.append({"nome": "Template mestre travado", "ok": (MOTOR / "TEMPLATE_LOCK.json").exists()})
    return jsonify(itens)


# ------------------------------------------------------------------ aba DADOS
from . import dados  # noqa: E402


def _planilha_ou_erro(slug):
    a = A.carregar(slug)
    if not a:
        return None, None, _falha("Aluno não encontrado.", 404)
    p = dados.planilha_atual(a)
    if not p:
        return a, None, _falha("Este aluno ainda não tem planilha matriz lida.", 404)
    return a, p, None


@app.get("/api/dados")
def dados_lista():
    out = []
    for a in A.listar():
        p = dados.planilha_atual(a)
        ct = planos.situacao(a)
        item = {"slug": a["slug"], "nome": a["nome"], "status": a.get("status"), "contrato": ct and ct["nome"],
                "bloco_atual": a.get("bloco_atual"), "tem_planilha": bool(p),
                "limite": dados.LIMITE_AUMENTO}
        if p:
            try:
                R = dados.analisar(p)
            except Exception as ex:  # noqa: BLE001
                item["erro"] = f"Não consegui ler a planilha: {ex}"
                out.append(item)
                continue
            sem = R["semanas"]
            atual = next((s for s in sem if s["atual"]), None) or (sem[-1] if sem else None)
            item.update({
                "semanas": [{"rotulo": s["rotulo"], "vtt": s["vtt"], "atual": s["atual"], "alerta": s["alerta"]} for s in sem],
                "atual": atual and {"rotulo": atual["rotulo"], "bloco": atual["bloco"], "semana": atual["semana"],
                                    **{k: atual[k] for k in ("vtt", "vtr", "int", "d_vtt", "d_vtr", "d_int", "alerta")}},
                "alertas": sum(1 for s in sem if s["alerta"]),
            })
        out.append(item)
    return jsonify(out)


@app.get("/api/dados/<slug>")
def dados_aluno(slug):
    a, p, erro = _planilha_ou_erro(slug)
    if erro:
        return erro
    R = dados.analisar(p)
    ct = planos.situacao(a)
    return jsonify({**R, "aluno": {"slug": slug, "nome": a["nome"], "contrato": ct and ct["nome"], "status": a.get("status")},
                    "relatorios": a.get("relatorios", [])[:20]})


@app.post("/api/dados/<slug>/pdf/<tipo>")
def dados_pdf(slug, tipo):
    from . import relatorios
    if tipo not in ("pre", "pos"):
        return _falha("Tipo de PDF inválido.")
    a, p, erro = _planilha_ou_erro(slug)
    if erro:
        return erro
    try:
        with _trava:
            return jsonify(relatorios.gerar(slug, tipo))
    except ValueError as ex:
        return _falha(str(ex))


# ------------------------------------------------------------------ anamnese e feedbacks
from . import individual  # noqa: E402


@app.get("/api/individual/<slug>")
def ind_tudo(slug):
    a = A.carregar(slug)
    if not a:
        return _falha("Aluno não encontrado.", 404)
    return jsonify({"anamnese": individual.carregar_anamnese(slug), "feedbacks": individual.carregar_feedbacks(slug)})


@app.post("/api/individual/<slug>/anamnese")
def ind_anamnese_ler(slug):
    f = request.files.get("arquivo")
    if not f or not f.filename.lower().endswith((".xlsx", ".csv")):
        return _falha("Envie a planilha de respostas do Forms (.xlsx ou .csv).")
    try:
        return _ok(**individual.ler_planilha_anamnese(slug, f.filename, f.read()))
    except Exception as ex:  # noqa: BLE001
        return _falha(f"Não consegui ler a planilha: {ex}")


@app.post("/api/individual/<slug>/anamnese/escolher")
def ind_anamnese_escolher(slug):
    d = request.get_json() or {}
    try:
        return _ok(anamnese=individual.escolher_anamnese(slug, d.get("arquivo", ""), d.get("chave", "")))
    except ValueError as ex:
        return _falha(str(ex))


@app.delete("/api/individual/<slug>/anamnese")
def ind_anamnese_remover(slug):
    individual.remover_anamnese(slug)
    return _ok()


@app.delete("/api/individual/<slug>/feedback/<fid>")
def ind_feedback_remover(slug, fid):
    individual.remover_feedback(slug, fid)
    return _ok()


@app.post("/api/individual/<slug>/feedback/<fid>/visto")
def ind_feedback_visto(slug, fid):
    individual.marcar_visto(slug, fid, (request.get_json() or {}).get("visto", True))
    return _ok()


@app.get("/api/semana")
def semana():
    """O que fazer nos próximos 7 dias: blocos para montar, teste da semana 3, feedbacks com atenção, renovações."""
    g = {"blocos": [], "teste": [], "feedbacks": [], "renovacoes": []}
    for a in A.listar():
        if a.get("status") != "Ativo":
            continue
        r = planilha.resumo(a)
        base = {"slug": r["slug"], "nome": r["nome"]}
        if r["situacao"] in ("atrasada", "proxima"):
            g["blocos"].append({**base, "bloco": (r["bloco_atual"] or 0) + 1, "data": r["proxima_atualizacao"],
                                "dias": r["dias_para_proxima"], "situacao": r["situacao"]})
        if r["semana_do_bloco"] == 3:
            g["teste"].append({**base, "bloco": r["bloco_atual"]})
        pend = [f for f in individual.carregar_feedbacks(a["slug"]) if f["atencao"] and not f.get("visto")]
        if pend:
            g["feedbacks"].append({**base, "n": len(pend), "atencao": pend[0]["atencao"], "data": pend[0].get("data", "")})
        c = r["contrato"]
        if c and c["situacao"] in ("renova", "vencido"):
            g["renovacoes"].append({**base, "plano": c["nome"], "vence": c["vence"], "dias": c["dias"],
                                    "situacao": c["situacao"]})
    g["blocos"].sort(key=lambda x: x["data"] or "")
    g["renovacoes"].sort(key=lambda x: x["vence"])
    g["feedbacks"].sort(key=lambda x: x["data"], reverse=True)
    return jsonify(g)


@app.post("/api/individual/<slug>/feedback-forms")
def ind_feedback_forms(slug):
    f = request.files.get("arquivo")
    if not f or not f.filename.lower().endswith((".xlsx", ".csv")):
        return _falha("Envie a planilha de respostas do feedback (.xlsx ou .csv).")
    try:
        return _ok(**individual.ler_planilha_feedback(slug, f.filename, f.read()))
    except Exception as ex:  # noqa: BLE001
        return _falha(f"Não consegui ler a planilha: {ex}")


@app.post("/api/individual/<slug>/feedback-forms/escolher")
def ind_feedback_forms_escolher(slug):
    a, p, erro = _planilha_ou_erro(slug)
    semanas = dados.analisar(p)["semanas"] if not erro else []
    d = request.get_json() or {}
    try:
        return _ok(novos=individual.importar_feedbacks(slug, d.get("arquivo", ""), d.get("chave", ""), semanas))
    except ValueError as ex:
        return _falha(str(ex))
