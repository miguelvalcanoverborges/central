'use strict';
/* Aba DADOS — gráficos e análise semanal do planejado (VTT, VTR, intensidade).
   Usa os utilitários de app.js (api, esc, aviso, modal, confirmar, data, bloco2, icone). */

const NF0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const NF1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fmtVtt = (v) => (v == null ? '—' : `${NF0.format(v)} kg`);
const fmtVtr = (v) => (v == null ? '—' : NF0.format(v));
const fmtInt = (v) => (v == null ? '—' : `${NF1.format(v)}%`);
const sinal = (v) => (v > 0 ? '+' : v < 0 ? '−' : '±');
const fmtDelta = (v) => (v == null ? '' : `${sinal(v)}${NF1.format(Math.abs(v))}%`);
const fmtPP = (v) => (v == null ? '' : `${sinal(v)}${NF1.format(Math.abs(v))} p.p.`);
const METRICAS = {
  vtt: { nome: 'VTT', longo: 'VTT (tonelagem)', fmt: fmtVtt, eixo: (v) => NF0.format(v), delta: 'd_vtt' },
  vtr: { nome: 'VTR', longo: 'VTR (repetições)', fmt: fmtVtr, eixo: (v) => NF0.format(v), delta: 'd_vtr' },
  int: { nome: 'Intensidade', longo: 'Intensidade média (%1RM)', fmt: fmtInt, eixo: (v) => `${NF0.format(v)}%`, delta: 'd_int' },
};
const COR = { real: '#000000', plan: '#8c8981', grade: '#e7e5df', eixo: '#55554f', selecao: '#f1f0eb', alerta: '#b3261e' };
const SVGNS = 'http://www.w3.org/2000/svg';
const FAIXA_COR = ['#b4b1a8', '#86837b', '#55534d', '#111110'];   // rampa ordinal validada (claro → escuro)
const estadoDados = { slug: null, R: null, sel: null };

/* ---------------------------------------------------------------- tooltip */
let dica = null;
function mostrarDica(el, linhas) {
  if (!dica) { dica = document.createElement('div'); dica.className = 'dica'; document.body.append(dica); }
  dica.replaceChildren(...linhas.map(([forte, fraco, alerta]) => {
    const p = document.createElement('div');
    const b = document.createElement('b'); b.textContent = forte;
    if (alerta) b.className = 'alerta-txt';
    p.append(b);
    if (fraco) { const s = document.createElement('span'); s.textContent = ' ' + fraco; p.append(s); }
    return p;
  }));
  dica.hidden = false;
  const r = el.getBoundingClientRect();
  const w = dica.offsetWidth, h = dica.offsetHeight;
  let x = r.left + r.width / 2 - w / 2;
  x = Math.max(8, Math.min(window.innerWidth - w - 8, x));
  let y = r.top - h - 10;
  if (y < 70) y = r.bottom + 10;
  dica.style.left = `${x}px`;
  dica.style.top = `${y}px`;
}
function esconderDica() { if (dica) dica.hidden = true; }

/* ---------------------------------------------------------------- SVG */
function el(tag, attrs = {}, pai) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) e.setAttribute(k, v);
  if (pai) pai.append(e);
  return e;
}
function txt(pai, x, y, t, attrs = {}) {
  const e = el('text', { x, y, ...attrs }, pai);
  e.textContent = t;
  return e;
}
function escala(max, min = 0, nTicks = 4) {
  if (max <= min) max = min + 1;
  const bruto = (max - min) / nTicks;
  const mag = 10 ** Math.floor(Math.log10(bruto));
  const passo = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= bruto);
  const ini = Math.floor(min / passo) * passo;
  const fim = Math.ceil(max / passo) * passo;
  const ticks = [];
  for (let v = ini; v <= fim + 1e-9; v += passo) ticks.push(+v.toFixed(6));
  return { min: ini, max: fim, ticks };
}
function caminhoColuna(x, y, w, h) {
  if (h <= 0.5) return `M${x},${y + h}h${w}`;
  const r = Math.min(4, w / 2, h);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

/* Colunas por semana. pontos: [{g, rotulo, bloco, valor, plano, real(bool), alerta, delta, dica:[...] }] */
function graficoColunas(caixa, pontos, { formatoEixo, altura = 230, sel, aoSelecionar, compacto = false, rotuloAlerta = true }) {
  caixa.replaceChildren();
  const W = Math.max(caixa.clientWidth || 360, 240);
  const m = { t: compacto ? 14 : 24, r: 6, b: compacto ? 24 : 40, l: compacto ? 40 : 54 };
  const H = altura;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img' }, caixa);
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const valores = pontos.flatMap((p) => [p.valor || 0, p.plano || 0]);
  const esc2 = escala(Math.max(...valores, 0) * 1.08);
  const Y = (v) => m.t + ih - (v - esc2.min) / (esc2.max - esc2.min) * ih;
  for (const t of esc2.ticks) {
    el('line', { x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t), stroke: COR.grade, 'stroke-width': 1 }, svg);
    txt(svg, m.l - 8, Y(t) + 4, formatoEixo(t), { 'text-anchor': 'end', class: 'eixo' });
  }
  const banda = iw / pontos.length;
  const bw = Math.min(24, banda * 0.62);
  pontos.forEach((p, i) => {
    const cx = m.l + banda * i + banda / 2;
    if (p.g === sel) el('rect', { x: m.l + banda * i + 1, y: m.t - 6, width: banda - 2, height: ih + 6, fill: COR.selecao, rx: 4 }, svg);
    if (!p.vazio) {
      const v = p.valor || 0;
      el('path', { d: caminhoColuna(cx - bw / 2, Y(v), bw, Y(0) - Y(v)), fill: p.real ? COR.real : COR.plan }, svg);
      if (p.real && p.plano != null && Math.abs(p.plano - v) > 1e-6) {
        el('line', { x1: cx - bw / 2 - 4, x2: cx + bw / 2 + 4, y1: Y(p.plano), y2: Y(p.plano), stroke: COR.plan, 'stroke-width': 2, 'stroke-linecap': 'round' }, svg);
      }
      if (p.alerta && rotuloAlerta) {
        const y0 = Math.min(Y(v), p.plano != null ? Y(p.plano) : Y(v)) - 6;
        txt(svg, cx, y0, `▲${NF0.format(p.delta)}%`, { 'text-anchor': 'middle', class: 'rotulo-alerta' });
      }
    }
    txt(svg, cx, H - m.b + 15, p.rotulo, { 'text-anchor': 'middle', class: `eixo${p.g === sel ? ' eixo-sel' : ''}` });
    const alvo = el('rect', { x: m.l + banda * i, y: m.t - 6, width: banda, height: ih + 6 + 18, fill: 'transparent', tabindex: 0, class: 'alvo' }, svg);
    alvo.setAttribute('aria-label', (p.dica || []).map((l) => l.filter(Boolean).join(' ')).join('. '));
    const mostrar = () => mostrarDica(alvo, p.dica || []);
    alvo.addEventListener('pointerenter', mostrar);
    alvo.addEventListener('focus', mostrar);
    alvo.addEventListener('pointerleave', esconderDica);
    alvo.addEventListener('blur', esconderDica);
    if (aoSelecionar) {
      alvo.style.cursor = 'pointer';
      alvo.addEventListener('click', () => aoSelecionar(p.g));
      alvo.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); aoSelecionar(p.g); } });
    }
  });
  // blocos sob o eixo
  if (!compacto) {
    const blocos = [...new Set(pontos.map((p) => p.bloco))];
    for (const b of blocos) {
      const idx = pontos.map((p, i) => (p.bloco === b ? i : -1)).filter((i) => i >= 0);
      const x0 = m.l + banda * idx[0] + 4, x1 = m.l + banda * (idx[idx.length - 1] + 1) - 4;
      el('line', { x1: x0, x2: x1, y1: H - 14, y2: H - 14, stroke: COR.grade, 'stroke-width': 1 }, svg);
      txt(svg, (x0 + x1) / 2, H - 2, `Bloco ${bloco2(b)}`, { 'text-anchor': 'middle', class: 'eixo eixo-bloco' });
    }
  }
  el('line', { x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0), stroke: '#c9c6bd', 'stroke-width': 1 }, svg);
}

/* Linha de intensidade por semana. */
function graficoLinha(caixa, pontos, { altura = 230, sel, aoSelecionar, mostrarPlano }) {
  caixa.replaceChildren();
  const W = Math.max(caixa.clientWidth || 360, 240);
  const m = { t: 24, r: 10, b: 40, l: 54 };
  const H = altura;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img' }, caixa);
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const vals = pontos.flatMap((p) => [p.valor, mostrarPlano ? p.plano : null]).filter((v) => v != null);
  if (!vals.length) { txt(svg, W / 2, H / 2, 'Sem %1RM nesta planilha', { 'text-anchor': 'middle', class: 'eixo' }); return; }
  const esc2 = escala(Math.max(...vals) + 2, Math.max(0, Math.min(...vals) - 4));
  const Y = (v) => m.t + ih - (v - esc2.min) / (esc2.max - esc2.min) * ih;
  for (const t of esc2.ticks) {
    el('line', { x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t), stroke: COR.grade, 'stroke-width': 1 }, svg);
    txt(svg, m.l - 8, Y(t) + 4, `${NF0.format(t)}%`, { 'text-anchor': 'end', class: 'eixo' });
  }
  const banda = iw / pontos.length;
  const X = (i) => m.l + banda * i + banda / 2;
  pontos.forEach((p, i) => {
    if (p.g === sel) el('rect', { x: m.l + banda * i + 1, y: m.t - 6, width: banda - 2, height: ih + 6, fill: COR.selecao, rx: 4 }, svg);
  });
  const linha = (chave, cor) => {
    let d = '';
    pontos.forEach((p, i) => { if (p[chave] != null) d += `${d && pontos[i - 1] && pontos[i - 1][chave] != null ? 'L' : 'M'}${X(i)},${Y(p[chave])}`; });
    if (d) el('path', { d, fill: 'none', stroke: cor, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
  };
  if (mostrarPlano) linha('plano', COR.plan);
  linha('valor', COR.real);
  pontos.forEach((p, i) => {
    if (p.valor != null) el('circle', { cx: X(i), cy: Y(p.valor), r: 4, fill: p.real ? COR.real : COR.plan, stroke: '#fff', 'stroke-width': 2 }, svg);
    txt(svg, X(i), H - m.b + 15, p.rotulo, { 'text-anchor': 'middle', class: `eixo${p.g === sel ? ' eixo-sel' : ''}` });
    const alvo = el('rect', { x: m.l + banda * i, y: m.t - 6, width: banda, height: ih + 24, fill: 'transparent', tabindex: 0, class: 'alvo' }, svg);
    const mostrar = () => mostrarDica(alvo, p.dica || []);
    alvo.addEventListener('pointerenter', mostrar);
    alvo.addEventListener('focus', mostrar);
    alvo.addEventListener('pointerleave', esconderDica);
    alvo.addEventListener('blur', esconderDica);
    if (aoSelecionar) {
      alvo.style.cursor = 'pointer';
      alvo.addEventListener('click', () => aoSelecionar(p.g));
    }
  });
  const blocos = [...new Set(pontos.map((p) => p.bloco))];
  for (const b of blocos) {
    const idx = pontos.map((p, i) => (p.bloco === b ? i : -1)).filter((i) => i >= 0);
    const x0 = m.l + banda * idx[0] + 4, x1 = m.l + banda * (idx[idx.length - 1] + 1) - 4;
    el('line', { x1: x0, x2: x1, y1: H - 14, y2: H - 14, stroke: COR.grade, 'stroke-width': 1 }, svg);
    txt(svg, (x0 + x1) / 2, H - 2, `Bloco ${bloco2(b)}`, { 'text-anchor': 'middle', class: 'eixo eixo-bloco' });
  }
}

/* Colunas empilhadas: séries por faixa de %1RM em cada semana. */
function graficoEmpilhado(caixa, pontos, { altura = 230, sel, aoSelecionar }) {
  caixa.replaceChildren();
  const W = Math.max(caixa.clientWidth || 360, 240);
  const m = { t: 14, r: 6, b: 40, l: 44 };
  const H = altura;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: 'img' }, caixa);
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const esc2 = escala(Math.max(...pontos.map((p) => p.partes.reduce((a, b) => a + b, 0)), 1) * 1.05);
  const Y = (v) => m.t + ih - (v - esc2.min) / (esc2.max - esc2.min) * ih;
  for (const t of esc2.ticks) {
    el('line', { x1: m.l, x2: W - m.r, y1: Y(t), y2: Y(t), stroke: COR.grade, 'stroke-width': 1 }, svg);
    txt(svg, m.l - 8, Y(t) + 4, NF0.format(t), { 'text-anchor': 'end', class: 'eixo' });
  }
  const banda = iw / pontos.length, bw = Math.min(24, banda * 0.62);
  pontos.forEach((p, i) => {
    const cx = m.l + banda * i + banda / 2;
    if (p.g === sel) el('rect', { x: m.l + banda * i + 1, y: m.t - 6, width: banda - 2, height: ih + 6, fill: COR.selecao, rx: 4 }, svg);
    let base = 0;
    const total = p.partes.reduce((a, b) => a + b, 0);
    p.partes.forEach((n, k) => {
      if (!n) return;
      const y0 = Y(base + n), y1 = Y(base);
      const topo = p.partes.slice(k + 1).every((x) => !x);
      const h = Math.max(0, y1 - y0 - 2);   // 2px de respiro entre segmentos
      el('path', { d: topo ? caminhoColuna(cx - bw / 2, y0, bw, h) : `M${cx - bw / 2},${y0}h${bw}v${h}h${-bw}Z`, fill: FAIXA_COR[k] }, svg);
      base += n;
    });
    if (!total) txt(svg, cx, Y(0) - 4, '—', { 'text-anchor': 'middle', class: 'eixo' });
    txt(svg, cx, H - m.b + 15, p.rotulo, { 'text-anchor': 'middle', class: `eixo${p.g === sel ? ' eixo-sel' : ''}` });
    const alvo = el('rect', { x: m.l + banda * i, y: m.t - 6, width: banda, height: ih + 24, fill: 'transparent', tabindex: 0, class: 'alvo' }, svg);
    const mostrar = () => mostrarDica(alvo, p.dica);
    alvo.addEventListener('pointerenter', mostrar);
    alvo.addEventListener('focus', mostrar);
    alvo.addEventListener('pointerleave', esconderDica);
    alvo.addEventListener('blur', esconderDica);
    if (aoSelecionar) { alvo.style.cursor = 'pointer'; alvo.addEventListener('click', () => aoSelecionar(p.g)); }
  });
  const blocos = [...new Set(pontos.map((p) => p.bloco))];
  for (const b of blocos) {
    const idx = pontos.map((p, i) => (p.bloco === b ? i : -1)).filter((i) => i >= 0);
    const x0 = m.l + banda * idx[0] + 4, x1 = m.l + banda * (idx[idx.length - 1] + 1) - 4;
    el('line', { x1: x0, x2: x1, y1: H - 14, y2: H - 14, stroke: COR.grade, 'stroke-width': 1 }, svg);
    txt(svg, (x0 + x1) / 2, H - 2, `Bloco ${bloco2(b)}`, { 'text-anchor': 'middle', class: 'eixo eixo-bloco' });
  }
  el('line', { x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0), stroke: '#c9c6bd', 'stroke-width': 1 }, svg);
}

function sparkColunas(caixa, valores, sel) {
  const W = 132, H = 30;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' }, caixa);
  const max = Math.max(...valores.map((v) => v.valor || 0), 1);
  const banda = W / valores.length, bw = Math.min(7, banda - 2);
  valores.forEach((v, i) => {
    const h = Math.max(v.vazio ? 0 : 1.5, (v.valor || 0) / max * (H - 2));
    if (v.vazio) return;
    el('path', { d: caminhoColuna(banda * i + (banda - bw) / 2, H - h, bw, h), fill: v.g === sel ? COR.real : v.alerta ? COR.alerta : '#cfccc3' }, svg);
  });
}

/* ---------------------------------------------------------------- dados → pontos */
function deltaTexto(p, chave) {
  const d = p[METRICAS[chave].delta];
  if (d == null) return '';
  const pp = chave === 'int' && p.d_int_pp != null ? ` (${fmtPP(p.d_int_pp)})` : '';
  return `${fmtDelta(d)} vs semana anterior${pp}`;
}

function pontosSemana(R, chave) {
  return R.semanas.map((s) => {
    const alerta = s.alerta && s[METRICAS[chave].delta] > R.limite;
    const linhas = [[METRICAS[chave].fmt(s[chave]), `${METRICAS[chave].nome} · ${s.rotulo} · ${data(s.data)}`]];
    const dt = deltaTexto(s, chave);
    if (dt) linhas.push([dt, '', alerta]);
    return { g: s.global, rotulo: s.rotulo, bloco: s.bloco, valor: s[chave], plano: null, real: true,
             alerta, delta: s[METRICAS[chave].delta], dica: linhas };
  });
}

/* ---------------------------------------------------------------- PAINEL DE DADOS */
const filtroDados = { busca: '' };

async function telaDadosLista() {
  tela.innerHTML = '<div class="vazio"><p class="sub">Carregando os dados dos alunos…</p></div>';
  const lista = await api('GET', '/api/dados');
  const ativos = lista.filter((a) => a.status !== 'Encerrado').sort((a, b) => a.nome.localeCompare(b.nome));
  tela.innerHTML = `
    <div class="topo"><div style="flex:1 1 320px"><h1>Dados</h1></div>
      <input class="busca" type="search" placeholder="Buscar aluno" aria-label="Buscar aluno" value="${esc(filtroDados.busca)}"></div>
    <div class="cards-dados" id="cards"></div>`;
  const desenhar = () => {
    const q = filtroDados.busca.trim().toLowerCase();
    const lst = ativos.filter((a) => a.nome.toLowerCase().includes(q));
    const box = $('#cards');
    if (!ativos.length) { box.innerHTML = `<div class="vazio"><h2>Nenhum aluno ainda</h2><p>Envie a planilha matriz de um aluno na aba Alunos. Os dados aparecem aqui automaticamente.</p></div>`; return; }
    box.innerHTML = lst.map((a) => {
      if (!a.tem_planilha || a.erro) {
        return `<div class="card-dados inativo"><div class="cd-nome">${esc(a.nome)}</div><p class="sub peq">${esc(a.erro || 'Sem planilha matriz lida.')}</p></div>`;
      }
      const at = a.atual || {};
      return `<a class="card-dados" href="#/dados/${a.slug}">
        <div class="cd-nome">${esc(a.nome)}</div>
        <div class="cd-sub">${[a.contrato, at.rotulo ? `bloco ${bloco2(at.bloco)}, semana ${at.semana}` : ''].filter(Boolean).map(esc).join(' · ')}</div>
        ${a.alertas ? `<span class="pilula vermelha cd-alerta" title="Semanas com aumento de VTT, VTR ou intensidade acima de ${a.limite}%">▲ ${a.alertas} ${a.alertas === 1 ? 'semana' : 'semanas'} com aumento acima de ${a.limite}%</span>` : ''}
        <div class="cd-nums">
          <div><b>${fmtVtt(at.vtt)}</b><span class="${at.d_vtt > a.limite ? 'alerta-txt' : ''}">VTT ${at.d_vtt != null ? fmtDelta(at.d_vtt) : ''}</span></div>
          <div><b>${fmtVtr(at.vtr)}</b><span class="${at.d_vtr > a.limite ? 'alerta-txt' : ''}">VTR ${at.d_vtr != null ? fmtDelta(at.d_vtr) : ''}</span></div>
          <div><b>${fmtInt(at.int)}</b><span class="${at.d_int > a.limite ? 'alerta-txt' : ''}">%1RM ${at.d_int != null ? fmtDelta(at.d_int) : ''}</span></div>
        </div>
        <div class="cd-spark" data-spark="${a.slug}"></div>
      </a>`;
    }).join('') || '<div class="vazio">Nenhum aluno com esse nome.</div>';
    lst.forEach((a) => {
      const c = box.querySelector(`[data-spark="${a.slug}"]`);
      if (c && a.semanas) {
        const atual = a.semanas.findIndex((s) => s.atual);
        graficoMini(c, a.semanas.map((s, i) => ({ valor: s.vtt, alerta: s.alerta, atual: i === atual, rotulo: s.rotulo })));
      }
    });
  };
  $('.busca').oninput = (e) => { filtroDados.busca = e.target.value; desenhar(); };
  desenhar();
}

function graficoMini(caixa, vals) {
  const W = Math.max(caixa.clientWidth || 300, 200), H = 46;
  const svg = el('svg', { width: W, height: H, viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' }, caixa);
  const max = Math.max(...vals.map((v) => v.valor || 0), 1);
  const banda = W / vals.length, bw = Math.min(14, banda * 0.6);
  vals.forEach((v, i) => {
    const h = Math.max(1.5, (v.valor || 0) / max * (H - 12));
    el('path', { d: caminhoColuna(banda * i + (banda - bw) / 2, H - 10 - h, bw, h), fill: v.atual ? COR.real : v.alerta ? COR.alerta : '#cfccc3' }, svg);
  });
  el('line', { x1: 0, x2: W, y1: H - 10, y2: H - 10, stroke: '#c9c6bd', 'stroke-width': 1 }, svg);
  const ia = vals.findIndex((v) => v.atual);
  if (ia >= 0) txt(svg, banda * ia + banda / 2, H, vals[ia].rotulo, { 'text-anchor': 'middle', class: 'eixo', 'font-size': 9 });
}

/* ---------------------------------------------------------------- DADOS DO ALUNO */
async function telaDadosAluno(slug, manterSel = false, abaInicial = null) {
  const R = await api('GET', `/api/dados/${slug}`);
  if (R.ok === false) {
    tela.innerHTML = `<a class="voltar" href="#/dados">${icone.voltar} Dados</a><div class="vazio"><h2>Sem dados</h2><p>${esc(R.erro)}</p></div>`;
    return;
  }
  if (estadoDados.slug !== slug) { estadoDados.slug = slug; estadoDados.sel = null; estadoDados.aba = 'numeros'; }
  if (abaInicial) estadoDados.aba = abaInicial;
  estadoDados.R = R;
  if (!manterSel || !R.semanas.some((s) => s.global === estadoDados.sel)) {
    const atual = R.semanas.find((s) => s.atual);
    estadoDados.sel = (atual || R.semanas[R.semanas.length - 1] || {}).global;
  }
  const aba = estadoDados.aba || 'numeros';
  const numeros = `
    <div class="filtros-dados">
      <div class="semanas-sel" role="group" aria-label="Semana">
        ${[...new Set(R.semanas.map((s) => s.bloco))].map((b) => `<div class="grupo-bloco"><span>Bloco ${bloco2(b)}</span>
          ${R.semanas.filter((s) => s.bloco === b).map((s) => `<button data-sel="${s.global}" aria-pressed="${s.global === estadoDados.sel}" title="${data(s.data)}">${s.rotulo}${s.atual ? '<i class="ponto-atual" aria-label="semana atual"></i>' : ''}</button>`).join('')}</div>`).join('')}
      </div>
    </div>
    <section id="resumo-semana"></section>
    <section class="secao">
      <div class="cab-secao"><h2>Por semana</h2></div>
      <div class="graficos-3">
        <figure><figcaption>VTT (kg)</figcaption><div class="grafico" id="g-vtt"></div></figure>
        <figure><figcaption>VTR (repetições)</figcaption><div class="grafico" id="g-vtr"></div></figure>
        <figure><figcaption>Intensidade média (%1RM)</figcaption><div class="grafico" id="g-int"></div></figure>
      </div>
      <p class="sub peq">▲ aumento acima de ${NF0.format(R.limite)}% sobre a semana anterior</p>
    </section>
    <section class="secao" id="tabela-semanal"></section>
    <section class="secao" id="faixas"></section>
    <section class="secao" id="por-exercicio"></section>
    <section class="secao" id="rm-blocos"></section>`;
  tela.innerHTML = `
    <a class="voltar" href="#/dados">${icone.voltar} Dados</a>
    <div class="topo">
      <div style="flex:1 1 320px"><h1>${esc(R.aluno.nome)}</h1>
        ${R.aluno.contrato ? `<p class="sub">${esc(R.aluno.contrato)}</p>` : ''}</div>
      <div class="topo-acoes">
        <a class="btn discreto" href="#/aluno/${slug}">Ficha do aluno</a>
      </div>
    </div>
    <div class="pdfs-aluno">
      <span class="pdfs-rotulo">PDF para o aluno</span>
      <button class="btn" data-pdf-tipo="pre">${icone.pdf} Planejamento</button>
      <button class="btn" data-pdf-tipo="pos">${icone.pdf} Resultados</button>
    </div>
    <div class="abas" role="tablist">
      ${[['numeros', 'Números'], ['individual', 'Anamnese e feedback'], ['pdfs', 'PDFs']].map(([k, t]) =>
        `<button role="tab" aria-selected="${aba === k}" data-aba="${k}">${t}</button>`).join('')}
    </div>
    ${aba === 'numeros' ? numeros : aba === 'individual' ? '<section id="individual"></section>' : '<section class="secao-1" id="pdfs"></section>'}`;

  tela.querySelectorAll('[data-sel]').forEach((b) => (b.onclick = () => selecionarSemana(+b.dataset.sel)));
  tela.querySelectorAll('[data-aba]').forEach((b) => (b.onclick = () => { estadoDados.aba = b.dataset.aba; telaDadosAluno(slug, true); }));
  tela.querySelectorAll('[data-pdf-tipo]').forEach((b) => (b.onclick = () => gerarPdfAluno(slug, b.dataset.pdfTipo, b)));
  if (aba === 'numeros') desenharDados();
  else if (aba === 'individual') desenharIndividual(slug);
  else desenharPdfs();
}

function selecionarSemana(g) {
  estadoDados.sel = g;
  tela.querySelectorAll('[data-sel]').forEach((b) => b.setAttribute('aria-pressed', +b.dataset.sel === g));
  desenharDados();
}

function desenharDados() {
  const R = estadoDados.R, sel = estadoDados.sel;
  graficoColunas($('#g-vtt'), pontosSemana(R, 'vtt'), { formatoEixo: (v) => (v >= 1000 ? `${NF0.format(v / 1000)} mil` : NF0.format(v)), sel, aoSelecionar: selecionarSemana });
  graficoColunas($('#g-vtr'), pontosSemana(R, 'vtr'), { formatoEixo: (v) => NF0.format(v), sel, aoSelecionar: selecionarSemana });
  graficoLinha($('#g-int'), pontosSemana(R, 'int'), { sel, aoSelecionar: selecionarSemana, mostrarPlano: false });
  desenharResumo();
  desenharTabelaSemanal();
  desenharFaixas();
  desenharPorExercicio();
  desenharRm();
}

function celDelta(v, alertaSe = null, pp = null) {
  if (v == null) return '<td class="n sub">—</td>';
  const alerta = alertaSe != null && v > alertaSe;
  const cls = alerta ? 'alerta-txt' : v < 0 ? 'sub' : '';
  return `<td class="n ${cls}">${alerta ? '▲ ' : ''}${fmtDelta(v)}${pp != null ? `<small> ${fmtPP(pp)}</small>` : ''}</td>`;
}

function desenharResumo() {
  const R = estadoDados.R;
  const s = R.semanas.find((x) => x.global === estadoDados.sel);
  if (!s) return;
  const v = s;
  const idx = R.semanas.indexOf(s);
  const ant = R.semanas[idx - 1];
  const tile = (chave, extra) => {
    const d = v[METRICAS[chave].delta];
    const alerta = d != null && d > R.limite;
    return `<div class="tile ${alerta ? 'tile-alerta' : ''}">
      <span class="tile-rotulo">${METRICAS[chave].longo}</span>
      <b class="tile-valor">${METRICAS[chave].fmt(v[chave])}</b>
      <span class="tile-delta ${alerta ? 'alerta-txt' : ''}">${d == null ? (ant ? 'sem comparação' : 'primeira semana') : `${alerta ? '▲ ' : ''}${fmtDelta(d)} vs ${ant.rotulo}`}${extra || ''}</span>
    </div>`;
  };
  $('#resumo-semana').innerHTML = `
    <div class="cab-secao"><h2>${s.rotulo} · bloco ${bloco2(s.bloco)}, semana ${s.semana}</h2>
      <span class="sub">${data(s.data)}${s.atual ? ' · semana atual' : ''}</span></div>
    ${v.alerta ? `<div class="aviso-alerta">▲ Aumento acima de ${NF0.format(R.limite)}% em relação à ${ant ? ant.rotulo : 'semana anterior'}: ${[v.d_vtt > R.limite ? `VTT ${fmtDelta(v.d_vtt)}` : '', v.d_vtr > R.limite ? `VTR ${fmtDelta(v.d_vtr)}` : '', v.d_int > R.limite ? `intensidade ${fmtDelta(v.d_int)}` : ''].filter(Boolean).join(', ').replace(/, ([^,]*)$/, ' e $1')}.</div>` : ''}
    <div class="tiles">${tile('vtt')}${tile('vtr')}${tile('int', v.d_int_pp != null ? ` (${fmtPP(v.d_int_pp)})` : '')}</div>
`;
}

function desenharTabelaSemanal() {
  const R = estadoDados.R;
  $('#tabela-semanal').innerHTML = `<div class="cab-secao"><h2>Tabela semanal</h2></div>
    <div class="rolagem"><table class="tabela tabela-macro"><thead><tr>
      <th>Semana</th><th>Data</th><th class="n">VTT</th><th class="n">Δ VTT</th><th class="n">VTR</th><th class="n">Δ VTR</th>
      <th class="n">Intensidade</th><th class="n">Δ intensidade</th></tr></thead><tbody>
    ${R.semanas.map((s, i) => {
      const v = s;
      const novoBloco = i > 0 && R.semanas[i - 1].bloco !== s.bloco;
      return `<tr class="${s.global === estadoDados.sel ? 'destaque' : ''} ${novoBloco ? 'novo-bloco' : ''}" data-linha-sel="${s.global}">
        <td><b class="num">${s.rotulo}</b> <span class="sub peq">B${bloco2(s.bloco)}·S${s.semana}</span>${s.atual ? ' <span class="pilula escura">atual</span>' : ''}</td>
        <td class="n">${data(s.data)}</td>
        <td class="n">${fmtVtt(v.vtt)}</td>${celDelta(v.d_vtt, R.limite)}
        <td class="n">${fmtVtr(v.vtr)}</td>${celDelta(v.d_vtr, R.limite)}
        <td class="n">${fmtInt(v.int)}</td>${celDelta(v.d_int, R.limite, v.d_int_pp)}
      </tr>`;
    }).join('')}</tbody></table></div>`;
  tela.querySelectorAll('[data-linha-sel]').forEach((tr) => (tr.onclick = () => selecionarSemana(+tr.dataset.linhaSel)));
}

function desenharFaixas() {
  const R = estadoDados.R, sel = estadoDados.sel;
  const s = R.semanas.find((x) => x.global === sel);
  const z = s.zonas || [0, 0, 0, 0];
  const total = z.reduce((a, b) => a + b, 0);
  $('#faixas').innerHTML = `<div class="cab-secao"><h2>Séries por faixa de intensidade</h2>
      <div class="legenda">${R.faixas.map((f, k) => `<span><i class="lg-col" style="background:${FAIXA_COR[k]}"></i>${f}</span>`).join('')}</div></div>
    <div class="faixas-grade">
      <figure><figcaption>Séries com %1RM em cada semana</figcaption><div class="grafico" id="g-faixas"></div></figure>
      <div class="faixas-semana"><h3>${s.rotulo}</h3>
        ${total ? R.faixas.map((f, k) => `<div class="faixa-linha"><span>${f}</span><span class="faixa-barra"><i style="width:${(z[k] / total * 100).toFixed(1)}%;background:${FAIXA_COR[k]}"></i></span><b>${NF0.format(z[k])}</b></div>`).join('')
          : '<p class="sub">Nenhuma série com %1RM nesta semana.</p>'}
      </div></div>`;
  graficoEmpilhado($('#g-faixas'), R.semanas.map((x) => {
    const zz = x.zonas || [0, 0, 0, 0];
    return { g: x.global, rotulo: x.rotulo, bloco: x.bloco, partes: zz,
             dica: [[`${NF0.format(zz.reduce((a, b) => a + b, 0))} séries com %1RM`, `${x.rotulo}`], ...R.faixas.map((f, k) => [NF0.format(zz[k]), f])] };
  }), { sel, aoSelecionar: selecionarSemana });
}

function desenharRm() {
  const R = estadoDados.R;
  const ev = R.rm_evolucao || [];
  if (!ev.length) { $('#rm-blocos').innerHTML = ''; return; }
  const blocos = [...new Set(ev.flatMap((e) => e.blocos.map((b) => b.bloco)))].sort();
  $('#rm-blocos').innerHTML = `<div class="cab-secao"><h2>1RM estimado por bloco</h2></div>
    <div class="rolagem"><table class="tabela tabela-rm"><thead><tr><th>Exercício</th>${blocos.map((b) => `<th>Bloco ${bloco2(b)}</th>`).join('')}<th class="n">Evolução</th></tr></thead><tbody>
    ${ev.map((e) => {
      const max = Math.max(...e.blocos.map((b) => b.est));
      return `<tr><td><b>${esc(e.exercicio)}</b></td>${blocos.map((bl) => {
        const b = e.blocos.find((x) => x.bloco === bl);
        return b ? `<td><div class="rm-celula"><b>${NF0.format(b.est)} kg</b><span class="sub peq">${NF0.format(b.reps)} × ${String(b.kg).replace('.', ',')} kg</span></div>
          <span class="rm-barra"><i style="width:${(b.est / max * 100).toFixed(1)}%"></i></span></td>` : '<td class="sub">—</td>';
      }).join('')}<td class="n">${e.variacao != null ? `<b>${fmtDelta(e.variacao)}</b>` : '<span class="sub">—</span>'}</td></tr>`;
    }).join('')}</tbody></table></div>`;
}

function desenharPorExercicio() {
  const R = estadoDados.R, sel = estadoDados.sel;
  const s = R.semanas.find((x) => x.global === sel);
  const idx = R.semanas.findIndex((x) => x.global === sel);
  const ant = R.semanas[idx - 1];
  const linhas = R.exercicios.map((e) => ({ e, p: e.semanas[idx] })).filter((x) => x.p && !x.p.vazio);
  $('#por-exercicio').innerHTML = `<div class="cab-secao"><h2>Por exercício · ${s.rotulo}</h2>
      <span class="sub">Variação sobre ${ant ? ant.rotulo : 'a semana anterior'}</span></div>
    <div class="rolagem"><table class="tabela"><thead><tr><th>Exercício</th><th class="n">VTT</th><th class="n">Δ VTT</th><th class="n">VTR</th><th class="n">Δ VTR</th>
      <th class="n">Intensidade</th><th class="n">Δ intensidade</th><th>VTT nas 12 semanas</th></tr></thead><tbody>
      ${linhas.map(({ e, p }) => `<tr class="${p.alerta ? 'linha-alerta' : ''}">
        <td><b>${esc(e.nome)}</b></td>
        <td class="n">${fmtVtt(p.vtt)}</td>${celDelta(p.d_vtt, R.limite)}
        <td class="n">${fmtVtr(p.vtr)}</td>${celDelta(p.d_vtr, R.limite)}
        <td class="n">${fmtInt(p.int)}</td>${celDelta(p.d_int, R.limite, p.d_int_pp)}
        <td data-spark-ex="${esc(e.chave)}"></td></tr>`).join('')}
    </tbody></table></div>`;
  linhas.forEach(({ e }) => {
    const c = $(`[data-spark-ex="${CSS.escape(e.chave)}"]`);
    sparkColunas(c, e.semanas.map((p) => ({ g: p.g, valor: p.vtt, vazio: p.vazio, alerta: p.alerta })), sel);
  });
}

async function gerarPdfAluno(slug, tipo, botao) {
  const nome = tipo === 'pre' ? 'Planejamento' : 'Resultados';
  const html0 = botao.innerHTML;
  botao.disabled = true;
  botao.textContent = 'Gerando…';
  try {
    const r = await api('POST', `/api/dados/${slug}/pdf/${tipo}`);
    if (!r.ok) { aviso(r.erro, true); return; }
    aviso(`PDF de ${nome.toLowerCase()} gerado`);
    if (r.omitidas && r.omitidas.length) aviso('Uma seção ficou de fora para caber em 2 páginas');
    await verPdf(slug, r.pdf, `${nome} — ${estadoDados.R.aluno.nome}`);
    const R = await api('GET', `/api/dados/${slug}`);
    estadoDados.R.relatorios = R.relatorios;
    if ($('#pdfs')) desenharPdfs();
  } catch (e) { aviso(e.message, true); } finally { botao.disabled = false; botao.innerHTML = html0; }
}

function desenharPdfs() {
  const R = estadoDados.R;
  const rel = R.relatorios || [];
  $('#pdfs').innerHTML = rel.length ? `<table class="tabela"><tbody>${rel.map((x) => `<tr><td><b>${x.tipo === 'pre' ? 'Planejamento' : 'Resultados'}</b></td>
      <td class="n sub">${dataHora(x.data)}</td>
      <td><div class="acoes"><button class="btn discreto" data-ver-rel="${esc(x.pdf)}" data-tipo="${x.tipo}">${icone.pdf} Ver</button>
        <button class="btn discreto" data-pasta-rel="${esc(x.pdf)}">${icone.pasta} Mostrar na pasta</button></div></td></tr>`).join('')}</tbody></table>`
    : '<p class="sub">Nenhum PDF gerado ainda.</p>';
  tela.querySelectorAll('[data-ver-rel]').forEach((b) => (b.onclick = () => verPdf(estadoDados.slug, b.dataset.verRel,
    `${b.dataset.tipo === 'pre' ? 'Planejamento' : 'Resultados'} — ${R.aluno.nome}`)));
  tela.querySelectorAll('[data-pasta-rel]').forEach((b) => (b.onclick = () => abrirArquivo(estadoDados.slug, b.dataset.pastaRel, true)));
}

/* ---------------------------------------------------------------- ANAMNESE E FEEDBACK (individualização dos PDFs) */
async function desenharIndividual(slug) {
  const box = $('#individual');
  box.innerHTML = '<p class="sub">Carregando…</p>';
  const I = await api('GET', `/api/individual/${slug}`);
  estadoDados.ind = I;
  const R = estadoDados.R;
  const an = I.anamnese;
  const base = an && an.respostas[0];

  box.innerHTML = `
    <div class="ind-grade">
      <div class="cartao">
        <div class="cab-secao"><h2>Anamnese</h2>
          <button class="btn" id="an-importar">Importar planilha</button></div>
        ${an ? `<p class="sub peq">Respondida em ${esc(base.data_txt)}</p>
            ${an.mudancas && an.mudancas.length ? `<details class="detalhes"><summary>${an.mudancas.length} resposta(s) mudaram desde a anterior</summary><ul>${an.mudancas.map((m) => `<li>${esc(m)}</li>`).join('')}</ul></details>` : ''}
            <details class="detalhes"><summary>Ver respostas</summary><div class="qa">${base.pares.map(([q, r]) => `<div class="qa-item"><small>${esc(q)}</small><p>${esc(r)}</p></div>`).join('')}</div></details>`
          : ''}
        ${an ? `<button class="btn discreto peq" id="an-remover" style="margin-top:6px">${icone.lixo} Remover</button>` : ''}
        <input type="file" id="an-arquivo" accept=".xlsx,.csv" hidden>
      </div>

      <div class="cartao">
        <div class="cab-secao"><h2>Feedback semanal</h2>
          <button class="btn" id="fb-forms">Importar planilha</button></div>
        <input type="file" id="fb-arquivo" accept=".xlsx,.csv" hidden>
        <div class="fb-lista">${I.feedbacks.length ? I.feedbacks.map((f) => {
            const at = f.atencao || [], novo = at.length && !f.visto;
            return `<details class="fb-item${f.visto ? ' visto' : ''}" ${novo ? 'open' : ''}>
            <summary class="fb-cab"><b class="num">${f.global ? `S${String(f.global).padStart(2, '0')}` : '—'}</b><span class="sub peq">${esc(f.data_txt || dataHora(f.registrado_em))}</span>
              <span>${[...new Set(at.map((t) => t.tipo))].map((t) => `<span class="tri ${t}">${TRIAGEM[t]}</span>`).join('')}</span></summary>
            ${at.length ? `<ul class="fb-atencao">${at.map((t) => `<li>${esc(t.texto)}</li>`).join('')}</ul>` : ''}
            ${f.texto ? (at.length ? `<details class="detalhes"><summary>Respostas</summary><p>${esc(f.texto)}</p></details>` : `<p>${esc(f.texto)}</p>`) : ''}
            <div style="display:flex;gap:8px;margin-top:6px">
              ${at.length ? `<button class="btn${novo ? '' : ' discreto'}" data-fb-visto="${f.id}" data-v="${novo ? 1 : 0}">${novo ? 'Visto' : 'Desmarcar visto'}</button>` : ''}
              <button class="btn discreto" data-fb-remover="${f.id}">${icone.lixo} Remover</button></div></details>`; }).join('')
          : '<p class="sub" style="margin-top:14px">Nenhum ainda.</p>'}</div>
      </div>
    </div>`;

  // ---- anamnese
  const inp = $('#an-arquivo');
  const anexar = () => { inp.value = ''; inp.click(); };
  $('#an-importar').onclick = anexar;
  if ($('#an-remover')) $('#an-remover').onclick = async () => {
    if (!(await confirmar('Remover a anamnese?', 'As respostas saem desta tela. Uma cópia fica guardada na pasta do aluno.', 'Remover', true))) return;
    await api('DELETE', `/api/individual/${slug}/anamnese`);
    aviso('Anamnese removida'); desenharIndividual(slug);
  };
  inp.onchange = async () => {
    const f = inp.files[0];
    if (!f) return;
    const fd = new FormData(); fd.append('arquivo', f);
    const r = await api('POST', `/api/individual/${slug}/anamnese`, fd);
    if (!r.ok) { aviso(r.erro, true); return; }
    const { el, fechar } = modal(`<h2>De quem são as respostas?</h2>
      <p>${r.pessoas.length} ${r.pessoas.length === 1 ? 'pessoa' : 'pessoas'} na planilha.${r.sugerida ? ' Selecionei a que tem o nome mais parecido com o do aluno.' : ''}</p>
      <select id="an-pessoa">${r.pessoas.map((p) => `<option value="${esc(p.chave)}" ${p.chave === r.sugerida ? 'selected' : ''}>${esc(p.nome)} · ${p.respostas} resposta(s), a mais recente em ${esc(p.mais_recente)}</option>`).join('')}</select>
      <div class="botoes"><button class="btn discreto" data-n>Cancelar</button><button class="btn primario" data-s>Usar estas respostas</button></div>`);
    $('[data-n]', el).onclick = fechar;
    $('[data-s]', el).onclick = async () => {
      const chave = $('#an-pessoa', el).value;
      fechar();
      const x = await api('POST', `/api/individual/${slug}/anamnese/escolher`, { arquivo: r.arquivo, chave });
      if (!x.ok) { aviso(x.erro, true); return; }
      aviso('Anamnese anexada'); desenharIndividual(slug);
    };
  };

  // ---- feedback
  box.querySelectorAll('[data-fb-visto]').forEach((b) => (b.onclick = async () => {
    await api('POST', `/api/individual/${slug}/feedback/${b.dataset.fbVisto}/visto`, { visto: b.dataset.v === '1' });
    desenharIndividual(slug);
  }));
  box.querySelectorAll('[data-fb-remover]').forEach((b) => (b.onclick = async () => {
    if (!(await confirmar('Remover este feedback?', 'O texto sai da lista. Anexos continuam guardados na pasta do aluno.', 'Remover', true))) return;
    await api('DELETE', `/api/individual/${slug}/feedback/${b.dataset.fbRemover}`);
    aviso('Feedback removido'); desenharIndividual(slug);
  }));

  // feedback do Forms
  const fbArq = $('#fb-arquivo');
  $('#fb-forms').onclick = () => { fbArq.value = ''; fbArq.click(); };
  fbArq.onchange = async () => {
    const f = fbArq.files[0];
    if (!f) return;
    const fd = new FormData(); fd.append('arquivo', f);
    const r = await api('POST', `/api/individual/${slug}/feedback-forms`, fd);
    if (!r.ok) { aviso(r.erro, true); return; }
    const { el, fechar } = modal(`<h2>De quem são os feedbacks?</h2>
      <p>${r.pessoas.length} ${r.pessoas.length === 1 ? 'pessoa' : 'pessoas'} na planilha.${r.sugerida ? ' Selecionei a que tem o nome mais parecido com o do aluno.' : ''}</p>
      <select id="fb-pessoa">${r.pessoas.map((p) => `<option value="${esc(p.chave)}" ${p.chave === r.sugerida ? 'selected' : ''}>${esc(p.nome)} · ${p.respostas} resposta(s), a mais recente em ${esc(p.mais_recente)}</option>`).join('')}</select>
      <div class="botoes"><button class="btn discreto" data-n>Cancelar</button><button class="btn primario" data-s>Importar feedbacks</button></div>`);
    $('[data-n]', el).onclick = fechar;
    $('[data-s]', el).onclick = async () => {
      const chave = $('#fb-pessoa', el).value;
      fechar();
      const x = await api('POST', `/api/individual/${slug}/feedback-forms/escolher`, { arquivo: r.arquivo, chave });
      if (!x.ok) { aviso(x.erro, true); return; }
      aviso(x.novos ? `${x.novos} ${x.novos === 1 ? 'feedback importado' : 'feedbacks importados'}` : 'Nenhum feedback novo nesta planilha');
      desenharIndividual(slug);
    };
  };
}
