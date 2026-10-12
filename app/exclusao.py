# -*- coding: utf-8 -*-
"""Excluir aluno de vez (pedido de Miguel, 12/out/2026): apaga tudo o que a Central tem sobre ele.

- a pasta dados/alunos/<slug>/ (cadastro, plano, planilhas, leituras, PDFs de ficha/planejamento/resultados,
  anamnese, feedbacks e anexos);
- cópias dele na lixeira (exclusões antigas, dados/lixeira/<slug>__*);
- sobras da área provisória de leitura (dados/_entrada/<envio> dos envios dele);
- a parte dele dentro de cada backup (backups/*.zip e os exportados em Documentos): o .zip é regravado sem ela;
- linhas do dados/central.log que citam a pasta dele.
Antes de apagar, a Central mostra exatamente isso (inventario) e exige o nome do aluno digitado.
"""
import os
import re
import shutil
import zipfile
from pathlib import Path

from . import armazenamento as A
from .config import BACKUPS, DADOS, ENTRADA, LIXEIRA

LOG = DADOS / "central.log"


def pasta_exportacao() -> Path:
    """Onde "Exportar backup" grava (Documentos/Central da Consultoria - Backups)."""
    docs = Path.home() / "Documents"
    return (docs if docs.exists() else Path.home()) / "Central da Consultoria - Backups"


def _na_lixeira(slug: str) -> list[Path]:
    return sorted(p for p in LIXEIRA.glob(f"{slug}__*") if p.is_dir() and p.name.split("__")[0] == slug) \
        if LIXEIRA.exists() else []


def _prefixos(slug: str) -> tuple[str, ...]:
    """Entradas do aluno dentro de um backup (dados/alunos/<slug>/ e dados/lixeira/<slug>__…/)."""
    return (f"dados/alunos/{slug}/", f"dados/lixeira/{slug}__")


def _e_do_aluno(nome_zip: str, slug: str) -> bool:
    n = nome_zip.replace("\\", "/")
    return n.startswith(_prefixos(slug)[0]) or (n.startswith(_prefixos(slug)[1]) and "/" in n[len("dados/lixeira/"):])


def _backups() -> list[Path]:
    out = sorted(BACKUPS.glob("*.zip")) if BACKUPS.exists() else []
    exp = pasta_exportacao()
    if exp.exists():
        out += sorted(exp.glob("central-consultoria_*.zip"))
    return out


def _backups_com(slug: str) -> list[tuple[Path, int]]:
    out = []
    for z in _backups():
        try:
            with zipfile.ZipFile(z) as zf:
                n = sum(1 for i in zf.namelist() if _e_do_aluno(i, slug))
        except (zipfile.BadZipFile, OSError):
            continue
        if n:
            out.append((z, n))
    return out


def _entradas(aluno: dict) -> list[Path]:
    ids = {p.get("id") for p in aluno.get("planilhas", []) if p.get("id")}
    return [ENTRADA / i for i in sorted(ids) if (ENTRADA / i).is_dir()]


def _padroes_log(slug: str) -> re.Pattern:
    return re.compile(rf"alunos[\\/]+{re.escape(slug)}(?:[\\/]|$)|lixeira[\\/]+{re.escape(slug)}__")


def _linhas_log(slug: str) -> int:
    try:
        texto = LOG.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return 0
    pad = _padroes_log(slug)
    return sum(1 for ln in texto.splitlines() if pad.search(ln))


def _cadastro(slug: str) -> dict | None:
    a = A.carregar(slug)
    if a:
        return a
    for p in reversed(_na_lixeira(slug)):
        a = A.ler_json(p / "aluno.json")
        if a:
            return a
    return None


def _contar(pastas: list[Path]) -> list[str]:
    """Resumo do que há nas pastas do aluno, em frases curtas para a confirmação."""
    planilhas = ficha = plan = result = leituras = anexos = feedbacks = 0
    anamnese = False
    for raiz in pastas:
        planilhas += sum(1 for p in (raiz / "planilhas").glob("*") if p.is_file() and p.suffix.lower() in (".xlsx", ".xlsm"))
        for p in (raiz / "pdfs").rglob("*.pdf"):
            if p.name.endswith("_Planejamento.pdf"):
                plan += 1
            elif p.name.endswith("_Resultados.pdf"):
                result += 1
            else:
                ficha += 1
        leituras += sum(1 for p in (raiz / "trabalho").glob("*") if p.is_dir())
        anexos += sum(1 for p in (raiz / "anexos").rglob("*") if p.is_file())
        anamnese |= (raiz / "anamnese.json").exists()
        feedbacks += len(A.ler_json(raiz / "feedbacks.json", []) or [])

    def n(q, um, varios):
        return f"{q} {um if q == 1 else varios}"
    itens = ["Cadastro, plano contratado e histórico"]
    if planilhas:
        itens.append(n(planilhas, "planilha recebida", "planilhas recebidas"))
    if leituras:
        itens.append(n(leituras, "leitura de planilha", "leituras de planilha") + " (revisão e aba Dados)")
    if ficha:
        itens.append(n(ficha, "PDF de ficha", "PDFs de ficha"))
    if plan:
        itens.append(n(plan, "PDF de planejamento", "PDFs de planejamento"))
    if result:
        itens.append(n(result, "PDF de resultados", "PDFs de resultados"))
    if anamnese:
        itens.append("Anamnese")
    if feedbacks:
        itens.append(n(feedbacks, "feedback semanal", "feedbacks semanais"))
    if anexos:
        itens.append(n(anexos, "anexo", "anexos") + " (anamnese, feedbacks)")
    return itens


def inventario(slug: str) -> dict | None:
    """O que será apagado. None se a Central não tem nada desse aluno."""
    a = _cadastro(slug)
    if not a:
        return None
    ativa = A.pasta(slug) if A.pasta(slug).is_dir() else None
    lix = _na_lixeira(slug)
    pastas = ([ativa] if ativa else []) + lix
    arquivos = sum(1 for raiz in pastas for p in raiz.rglob("*") if p.is_file())
    itens = _contar([ativa] if ativa else lix[-1:])   # a cópia da lixeira entra só como "cópia", sem contar de novo
    if lix:
        itens.append(f"{len(lix)} {'cópia' if len(lix) == 1 else 'cópias'} na lixeira")
    entradas = _entradas(a)
    if entradas:
        itens.append(f"{len(entradas)} {'leitura interrompida' if len(entradas) == 1 else 'leituras interrompidas'}")
    linhas = _linhas_log(slug)
    if linhas:
        itens.append(f"{linhas} {'linha' if linhas == 1 else 'linhas'} do registro de erros")
    return {"slug": slug, "nome": a.get("nome", slug), "ativo": bool(ativa), "itens": itens, "arquivos": arquivos,
            "backups": [{"nome": z.name, "pasta": "Documentos" if z.parent != BACKUPS else "backups", "arquivos": n}
                        for z, n in _backups_com(slug)]}


def _nome_confere(digitado: str, nome: str) -> bool:
    return bool(digitado.strip()) and A.slugify(digitado) == A.slugify(nome)


def _regravar_zip(z: Path, slug: str):
    """Regrava o backup sem as entradas do aluno (gravação atômica: temporário + substituição)."""
    tmp = z.with_name(f".tmp_{z.name}")
    with zipfile.ZipFile(z) as orig, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as novo:
        for info in orig.infolist():
            if not _e_do_aluno(info.filename, slug):
                novo.writestr(info, orig.read(info.filename))
        resta = len(novo.infolist())
    if resta:
        os.replace(tmp, z)
    else:          # o backup só tinha este aluno
        tmp.unlink()
        z.unlink()


def _limpar_log(slug: str):
    try:
        texto = LOG.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return
    pad = _padroes_log(slug)
    linhas = texto.splitlines(keepends=True)
    novas = [ln for ln in linhas if not pad.search(ln)]
    if len(novas) != len(linhas):
        A.gravar_seguro(LOG, "".join(novas))


def excluir(slug: str, nome_digitado: str) -> dict:
    """Apaga o aluno de vez. Exige o nome digitado igual ao do cadastro (sem diferença de acento ou maiúscula)."""
    inv = inventario(slug)
    if not inv:
        raise FileNotFoundError("Aluno não encontrado.")
    if not _nome_confere(nome_digitado, inv["nome"]):
        raise ValueError("O nome digitado não confere.")
    a = _cadastro(slug)

    # 1) tira a pasta do aluno do lugar primeiro: se algum arquivo dele estiver aberto (PDF, planilha), para aqui
    #    sem ter mexido em nada. ".tmp_" fica fora do backup e da lista de alunos.
    fila = DADOS / f".tmp_excluindo_{slug}"
    shutil.rmtree(fila, ignore_errors=True)
    if A.pasta(slug).is_dir():
        try:
            A.pasta(slug).rename(fila)
        except OSError as ex:
            raise PermissionError("Feche os PDFs e planilhas deste aluno e tente de novo.") from ex

    # 2) backups sem a parte dele
    falhas = []
    for z, _ in _backups_com(slug):
        try:
            _regravar_zip(z, slug)
        except (OSError, zipfile.BadZipFile):
            falhas.append(z.name)

    # 3) o resto
    for p in [fila, *_na_lixeira(slug), *_entradas(a)]:
        shutil.rmtree(p, ignore_errors=True)
    try:
        from . import dados
        raiz = str(A.pasta(slug))
        for k in [k for k in dados._cache if k.startswith(raiz)]:
            dados._cache.pop(k, None)
    except Exception:  # noqa: BLE001
        pass
    _limpar_log(slug)

    sobrou = [p.name for p in (fila, A.pasta(slug), *_na_lixeira(slug)) if p.exists()]
    return {"nome": inv["nome"], "falhas_backup": falhas, "sobrou": sobrou}
