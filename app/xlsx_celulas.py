# -*- coding: utf-8 -*-
"""Escreve valores em células de um .xlsx mexendo só nessas células, direto no XML.

Por que não openpyxl para gravar: ao salvar, o openpyxl descarta gráficos, imagens e partes que não entende, e
apaga o resultado de todas as fórmulas. Aqui o resto da planilha matriz fica byte a byte igual: fórmulas
(inclusive as do Google Sheets), formatação, mesclagens, aba macro, validações.

Regras:
  - célula com fórmula NUNCA é sobrescrita (a fórmula é de Miguel); ela volta na lista "mantidas";
  - em célula com fórmula dá para atualizar só o resultado guardado (cache), sem tocar na fórmula;
  - texto entra como inlineStr (não mexe na tabela de textos compartilhados);
  - o estilo da célula (s="…") é mantido;
  - o hiperlink antigo de uma célula reescrita sai (senão o link errado ficaria preso nela);
  - a pasta de trabalho é marcada para recalcular ao abrir (fullCalcOnLoad).
"""
import io
import posixpath
import re
import zipfile
from xml.sax.saxutils import escape

NS_REL_DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


# ------------------------------------------------------------------ endereços
def col_num(letras: str) -> int:
    n = 0
    for ch in letras:
        n = n * 26 + (ord(ch) - 64)
    return n


def col_letras(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def separar(coord: str) -> tuple[str, int]:
    m = re.fullmatch(r"([A-Z]+)(\d+)", coord)
    if not m:
        raise ValueError(f"Endereço inválido: {coord}")
    return m.group(1), int(m.group(2))


def _desescapar(s: str) -> str:
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
             .replace("&amp;", "&"))


# ------------------------------------------------------------------ mapa aba → arquivo XML
def mapa_abas(z: zipfile.ZipFile) -> dict[str, str]:
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    alvo = {}
    for m in re.finditer(r"<Relationship\b[^>]*>", rels):
        tag = m.group(0)
        i = re.search(r'\bId="([^"]+)"', tag)
        t = re.search(r'\bTarget="([^"]+)"', tag)
        if i and t:
            alvo[i.group(1)] = t.group(1)
    out = {}
    for m in re.finditer(r"<(?:\w+:)?sheet\b[^>]*/?>", wb):
        tag = m.group(0)
        nome = re.search(r'\bname="([^"]*)"', tag)
        rid = re.search(r'\b(?:\w+:)?id="([^"]+)"', tag)
        if not (nome and rid and rid.group(1) in alvo):
            continue
        t = alvo[rid.group(1)]
        caminho = t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join("xl", t))
        out[_desescapar(nome.group(1))] = caminho
    return out


# ------------------------------------------------------------------ edição de uma aba
_ROW_RE = re.compile(r"<row\b([^>]*?)(/>|>(.*?)</row>)", re.S)
_CELL_RE = re.compile(r"<c\b([^>]*?)(/>|>(.*?)</c>)", re.S)


def _attr(attrs: str, nome: str) -> str | None:
    m = re.search(rf'\b{nome}="([^"]*)"', attrs)
    return m.group(1) if m else None


def _num_txt(v) -> str:
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return repr(v) if isinstance(v, float) else str(v)


def _celula_valor(ref: str, estilo: str | None, v) -> str:
    s = f' s="{estilo}"' if estilo else ""
    if v is None or (isinstance(v, str) and v == ""):
        return f'<c r="{ref}"{s}/>'
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f'<c r="{ref}"{s}><v>{_num_txt(v)}</v></c>'
    return f'<c r="{ref}"{s} t="inlineStr"><is><t xml:space="preserve">{escape(str(v))}</t></is></c>'


def _celula_cache(attrs: str, interno: str, v) -> str:
    """Mesma célula com a fórmula intacta e só o resultado guardado trocado."""
    attrs = re.sub(r'\s+t="[^"]*"', "", attrs)
    sem_v = re.sub(r"<v\s*/>|<v\b[^>]*>.*?</v>", "", interno, flags=re.S)
    if v is None or v == "":
        return f'<c{attrs} t="str">{sem_v}<v></v></c>'
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"<c{attrs}>{sem_v}<v>{_num_txt(v)}</v></c>"
    return f'<c{attrs} t="str">{sem_v}<v>{escape(str(v))}</v></c>'


def _estilos_colunas(xml: str) -> dict[int, str]:
    out = {}
    for m in re.finditer(r"<col\b([^>]*)/?>", xml):
        a = m.group(1)
        lo, hi, st = _attr(a, "min"), _attr(a, "max"), _attr(a, "style")
        if lo and hi and st:
            for c in range(int(lo), min(int(hi), 200) + 1):
                out[c] = st
    return out


def editar_aba(xml: str, valores: dict[str, object], caches: dict[str, object] | None = None) -> tuple[str, list[str]]:
    """valores = {"E6": 80, "G6": "principal", "B9": None (limpar)} → só células SEM fórmula.
    caches = {"F6": 0.7111} → só células COM fórmula (troca o resultado guardado).
    Devolve (xml novo, endereços com fórmula que foram mantidos)."""
    caches = caches or {}
    pedidos: dict[int, dict[int, tuple[str, object]]] = {}
    for ref, v in valores.items():
        c, r = separar(ref)
        pedidos.setdefault(r, {})[col_num(c)] = ("valor", v)
    for ref, v in caches.items():
        c, r = separar(ref)
        pedidos.setdefault(r, {}).setdefault(col_num(c), ("cache", v))
    if not pedidos:
        return xml, []

    m_sd = re.search(r"<sheetData\s*/>|<sheetData\b[^>]*>(.*?)</sheetData>", xml, re.S)
    if not m_sd:
        raise ValueError("Aba sem sheetData.")
    corpo = m_sd.group(1) or ""
    estilos_col = _estilos_colunas(xml)
    mantidas, reescritas = [], []

    linhas = []   # [(num, attrs, [(col, xml)])]
    for m in _ROW_RE.finditer(corpo):
        attrs, interno = m.group(1), m.group(3) or ""
        num = int(_attr(attrs, "r"))
        cels = []
        for mc in _CELL_RE.finditer(interno):
            ref = _attr(mc.group(1), "r")
            cels.append((col_num(separar(ref)[0]), mc.group(0)))
        linhas.append([num, attrs, cels])
    por_num = {l[0]: l for l in linhas}

    for r, cols in pedidos.items():
        if r not in por_num:
            novo = [r, f' r="{r}"', []]
            linhas.append(novo)
            por_num[r] = novo
        linha = por_num[r]
        cels = dict(linha[2])
        for c, (tipo, v) in cols.items():
            ref = f"{col_letras(c)}{r}"
            atual = cels.get(c)
            tem_formula = bool(atual and re.search(r"<f\b", atual))
            if tipo == "valor":
                if tem_formula:
                    mantidas.append(ref)
                    continue
                estilo = _attr(_CELL_RE.match(atual).group(1), "s") if atual else estilos_col.get(c)
                cels[c] = _celula_valor(ref, estilo, v)
                reescritas.append(ref)
            elif tem_formula:
                mc = _CELL_RE.match(atual)
                cels[c] = _celula_cache(mc.group(1), mc.group(3) or "", v)
        linha[2] = sorted(cels.items())
        linha[1] = re.sub(r'\s+spans="[^"]*"', "", linha[1])   # a faixa de colunas pode ter mudado

    linhas.sort(key=lambda l: l[0])
    novo_corpo = "".join(
        f"<row{attrs}>{''.join(x for _, x in cels)}</row>" if cels else f"<row{attrs}/>"
        for _, attrs, cels in linhas)
    xml = xml[:m_sd.start()] + f"<sheetData>{novo_corpo}</sheetData>" + xml[m_sd.end():]

    # hiperlinks presos em células reescritas saem
    if reescritas and "<hyperlink" in xml:
        alvo = set(reescritas)
        xml = re.sub(r"<hyperlink\b[^>]*/>|<hyperlink\b[^>]*>.*?</hyperlink>",
                     lambda m: "" if _attr(m.group(0), "ref") in alvo else m.group(0), xml, flags=re.S)
        xml = re.sub(r"<hyperlinks>\s*</hyperlinks>|<hyperlinks/>", "", xml)
    return xml, mantidas


def _recalcular_ao_abrir(wb: str) -> str:
    if re.search(r"<calcPr\b", wb):
        def troca(m):
            tag = re.sub(r'\s+fullCalcOnLoad="[^"]*"', "", m.group(0))
            return tag.replace("<calcPr", '<calcPr fullCalcOnLoad="1"', 1)
        return re.sub(r"<calcPr\b[^>]*/?>", troca, wb, count=1)
    for marca in ("<oleSize", "<customWorkbookViews", "<pivotCaches", "<smartTagPr", "<smartTagTypes",
                  "<webPublishing", "<fileRecoveryPr", "<webPublishObjects", "<extLst", "</workbook>"):
        i = wb.find(marca)
        if i >= 0:
            return wb[:i] + '<calcPr fullCalcOnLoad="1"/>' + wb[i:]
    return wb


# ------------------------------------------------------------------ pasta de trabalho inteira
def escrever(origem: bytes, por_aba: dict[str, dict], caches: dict[str, dict] | None = None) -> tuple[bytes, list[str]]:
    """origem = bytes do .xlsx; por_aba = {"bloco 02": {"E6": 80, ...}}; caches idem (só resultado de fórmulas).
    Devolve (bytes do .xlsx novo, ["bloco 02!F6", ...] células com fórmula que foram mantidas)."""
    caches = caches or {}
    zin = zipfile.ZipFile(io.BytesIO(origem))
    abas = mapa_abas(zin)
    faltam = [n for n in set(por_aba) | set(caches) if n not in abas]
    if faltam:
        raise ValueError("A planilha não tem a(s) aba(s): " + ", ".join(sorted(faltam)))
    novos, mantidas = {}, []
    for nome in set(por_aba) | set(caches):
        parte = abas[nome]
        xml = zin.read(parte).decode("utf-8")
        xml, mant = editar_aba(xml, por_aba.get(nome, {}), caches.get(nome, {}))
        novos[parte] = xml.encode("utf-8")
        mantidas += [f"{nome}!{r}" for r in mant]
    novos["xl/workbook.xml"] = _recalcular_ao_abrir(zin.read("xl/workbook.xml").decode("utf-8")).encode("utf-8")

    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            dados = novos.get(info.filename)
            zout.writestr(info, dados if dados is not None else zin.read(info.filename))
    return saida.getvalue(), mantidas
