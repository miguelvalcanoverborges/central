'use strict';
/* Central da Consultoria — interface. Tudo é salvo no computador pelo servidor local. */

const $ = (s, el = document) => el.querySelector(s);
const tela = $('#tela');
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function api(metodo, url, corpo) {
  const op = { method: metodo, headers: {} };
  if (corpo instanceof FormData) op.body = corpo;
  else if (corpo !== undefined) { op.body = JSON.stringify(corpo); op.headers['Content-Type'] = 'application/json'; }
  const r = await fetch(url, op);
  let j = null;
  try { j = await r.json(); } catch { /* sem corpo */ }
  if (!r.ok && !(j && 'ok' in j)) throw new Error((j && j.erro) || `Erro ${r.status}`);
  return j;
}

/* ---------------------------------------------------------------- formatação */
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
function data(iso) {
  if (!iso) return '—';
  const [a, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${a}`;
}
function dataCurta(iso) {
  if (!iso) return '—';
  const [a, m, d] = iso.slice(0, 10).split('-');
  return `${+d} ${MESES[+m - 1]} ${a}`;
}
const reais = (v) => `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 }).format(v || 0)}`;
function relativo(dias) {
  if (dias === null || dias === undefined) return '';
  if (dias === 0) return 'hoje';
  if (dias === 1) return 'amanhã';
  if (dias === -1) return 'ontem';
  return dias > 0 ? `em ${dias} dias` : `há ${-dias} dias`;
}
function dataHora(s) {
  if (!s) return '—';
  const [d, h] = s.split(' ');
  return `${data(d)} ${h || ''}`.trim();
}
const bloco2 = (n) => (n ? String(n).padStart(2, '0') : '—');
const icone = {
  pdf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/></svg>',
  enviar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 20h16"/></svg>',
  pasta: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
  lixo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  voltar: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M15 5l-7 7 7 7"/></svg>',
};

/* ---------------------------------------------------------------- avisos e modais */
function aviso(msg, erro = false) {
  const el = document.createElement('div');
  el.className = 'aviso' + (erro ? ' erro' : '');
  el.textContent = msg;
  $('#avisos').append(el);
  setTimeout(() => el.remove(), erro ? 6000 : 2200);
}

function modal(html, classe = '') {
  const m = $('#modal');
  m.innerHTML = `<div class="caixa-modal ${classe}" role="dialog" aria-modal="true">${html}</div>`;
  m.hidden = false;
  const fechar = () => { m.hidden = true; m.innerHTML = ''; };
  m.onclick = (e) => { if (e.target === m) fechar(); };
  return { el: m, fechar };
}

function confirmar(titulo, texto, rotuloOk, perigo = false) {
  return new Promise((res) => {
    const { el, fechar } = modal(`<h2>${esc(titulo)}</h2><p>${texto}</p>
      <div class="botoes"><button class="btn discreto" data-n>Cancelar</button>
      <button class="btn ${perigo ? 'perigo' : 'primario'}" data-s>${esc(rotuloOk)}</button></div>`);
    $('[data-n]', el).onclick = () => { fechar(); res(false); };
    $('[data-s]', el).onclick = () => { fechar(); res(true); };
    $('[data-s]', el).focus();
  });
}

/* ---------------------------------------------------------------- visualizador de PDF */
async function verPdf(slug, rel, titulo) {
  const { paginas } = await api('GET', `/api/arquivo/${slug}/paginas?rel=${encodeURIComponent(rel)}`);
  const v = document.createElement('div');
  v.className = 'visualizador';
  v.innerHTML = `<header><h2>${esc(titulo || rel.split('/').pop())}</h2>
      <button class="btn" data-abrir>${icone.pdf} Abrir no leitor de PDF</button>
      <button class="btn" data-pasta>${icone.pasta} Mostrar na pasta</button>
      <button class="btn" data-fechar>Fechar</button></header>
    <div class="paginas">${Array.from({ length: paginas }, (_, i) =>
      `<img loading="lazy" alt="Página ${i + 1}" src="/api/arquivo/${slug}/pagina?rel=${encodeURIComponent(rel)}&n=${i}&zoom=1.6">`).join('')}</div>`;
  document.body.append(v);
  const fechar = () => { v.remove(); document.removeEventListener('keydown', tecla); };
  const tecla = (e) => { if (e.key === 'Escape') fechar(); };
  document.addEventListener('keydown', tecla);
  $('[data-fechar]', v).onclick = fechar;
  $('[data-abrir]', v).onclick = () => abrirArquivo(slug, rel);
  $('[data-pasta]', v).onclick = () => abrirArquivo(slug, rel, true);
  $('[data-fechar]', v).focus();
}

function abrirArquivo(slug, rel, pasta = false) {
  api('POST', `/api/arquivo/${slug}/abrir`, { rel, pasta }).catch((e) => aviso(e.message, true));
}

/* ---------------------------------------------------------------- envio da planilha matriz */
let slugDestinoEnvio = null;

function escolherPlanilha(slug = null) {
  slugDestinoEnvio = slug;
  const inp = $('#arquivo');
  inp.value = '';
  inp.click();
}
$('#arquivo').addEventListener('change', (e) => { if (e.target.files[0]) enviarPlanilha(e.target.files[0], slugDestinoEnvio); });

async function enviarPlanilha(arquivo, slug = null) {
  if (!/\.xls[xm]$/i.test(arquivo.name)) { aviso('Envie a planilha matriz em .xlsx', true); return; }
  const prog = $('#progresso');
  const passos = [...$('#progresso-passos').children];
  $('#progresso-titulo').textContent = 'Lendo a planilha';
  $('#progresso-erro').hidden = true;
  $('#progresso-passos').hidden = false;
  passos.forEach((p) => (p.className = ''));
  prog.hidden = false;
  let i = 0;
  passos[0].className = 'atual';
  const avancar = setInterval(() => {
    if (i < passos.length - 1) { passos[i].className = 'feito'; i += 1; passos[i].className = 'atual'; }
  }, 1100);
  const fd = new FormData();
  fd.append('arquivo', arquivo);
  if (slug) fd.append('slug', slug);
  try {
    const r = await api('POST', '/api/planilha', fd);
    clearInterval(avancar);
    if (!r.ok) throw Object.assign(new Error(r.erro), { log: r.log });
    passos.forEach((p) => (p.className = 'feito'));
    await new Promise((ok) => setTimeout(ok, 350));
    prog.hidden = true;
    if (r.novo_aluno) aviso('Aluno novo adicionado ao painel');
    location.hash = `#/revisao/${r.slug}/${r.envio}`;
  } catch (e) {
    clearInterval(avancar);
    $('#progresso-titulo').textContent = 'Não consegui ler esta planilha';
    $('#progresso-passos').hidden = true;
    const box = $('#progresso-erro');
    box.hidden = false;
    box.innerHTML = `<div class="erro-caixa">${esc(e.message)}</div>
      ${e.log ? `<details class="detalhes"><summary>Detalhes técnicos</summary><pre class="log">${esc(e.log)}</pre></details>` : ''}
      <div class="botoes" style="display:flex;justify-content:flex-end;margin-top:20px"><button class="btn primario">Fechar</button></div>`;
    $('button', box).onclick = () => { prog.hidden = true; };
  }
}

// soltar a planilha em qualquer lugar da janela
let contaArrasto = 0;
const temArquivo = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
window.addEventListener('dragenter', (e) => { if (!temArquivo(e)) return; e.preventDefault(); contaArrasto += 1; $('#soltar').hidden = false; });
window.addEventListener('dragover', (e) => { if (temArquivo(e)) e.preventDefault(); });
window.addEventListener('dragleave', () => { contaArrasto = Math.max(0, contaArrasto - 1); if (!contaArrasto) $('#soltar').hidden = true; });
window.addEventListener('drop', (e) => {
  if (!temArquivo(e)) return;
  e.preventDefault();
  contaArrasto = 0;
  $('#soltar').hidden = true;
  const f = e.dataTransfer.files[0];
  const m = location.hash.match(/^#\/aluno\/([^/]+)/);
  if (f) enviarPlanilha(f, m ? m[1] : null);
});

/* ---------------------------------------------------------------- PAINEL */
const filtro = { status: 'Ativo', busca: '' };

async function telaPainel() {
  const [alunos, S] = await Promise.all([api('GET', '/api/alunos'), api('GET', '/api/semana')]);
  tela.innerHTML = `
    ${estaSemana(S)}
    <section class="receber" id="receber" tabindex="0" role="button" aria-label="Enviar planilha matriz">
      <h1>Arraste a planilha matriz aqui</h1>
      <span class="btn grande">${icone.enviar} Escolher planilha</span>
    </section>
    <div class="indicadores">
      <div class="filtros">
        <input class="busca" type="search" placeholder="Buscar aluno" value="${esc(filtro.busca)}" aria-label="Buscar aluno">
        <div class="chips" role="group" aria-label="Situação">
          ${['Ativo', 'Pausado', 'Encerrado', 'Todos'].map((s) =>
            `<button aria-pressed="${filtro.status === s}" data-s="${s}">${s === 'Ativo' ? 'Ativos' : s === 'Todos' ? 'Todos' : s + 's'}</button>`).join('')}
        </div>
      </div>
    </div>
    <div id="lista"></div>`;
  const receber = $('#receber');
  receber.onclick = () => escolherPlanilha();
  receber.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); escolherPlanilha(); } };
  ['dragenter', 'dragover'].forEach((ev) => receber.addEventListener(ev, () => receber.classList.add('arrastando')));
  ['dragleave', 'drop'].forEach((ev) => receber.addEventListener(ev, () => receber.classList.remove('arrastando')));
  $('.busca').oninput = (e) => { filtro.busca = e.target.value; desenharLista(alunos); };
  tela.querySelectorAll('.chips button').forEach((b) => (b.onclick = () => {
    filtro.status = b.dataset.s;
    tela.querySelectorAll('.chips button').forEach((x) => x.setAttribute('aria-pressed', x === b));
    desenharLista(alunos);
  }));
  desenharLista(alunos);
}

const TRIAGEM = { dor: 'Dor', adesao: 'Adesão', objetivo: 'Objetivo', sugestao: 'Sugestão', recuperacao: 'Recuperação' };

function estaSemana(S) {
  const item = (href, nome, txt, cls = '') => `<li><a href="${href}">${esc(nome)}</a><span class="${cls}">${txt}</span></li>`;
  const grupos = [
    ['Montar bloco', S.blocos.map((x) => item(`#/aluno/${x.slug}`, x.nome,
      `Bloco ${bloco2(x.bloco)} · ${x.situacao === 'atrasada' ? 'atrasado' : 'até ' + dataCurta(x.data)}`, x.situacao))],
    ['AMRAP', (S.amrap || []).map((x) => item(`#/aluno/${x.slug}`, x.nome,
      `Semana ${x.semana} · ${x.exercicios.join(', ')}`, 'proxima'))],
    ['Feedback', S.feedbacks.map((x) => item(`#/dados/${x.slug}/feedback`, x.nome,
      [...new Set(x.atencao.map((t) => TRIAGEM[t.tipo]))].join(' · ') + (x.n > 1 ? ` · ${x.n} feedbacks` : ''),
      x.atencao.some((t) => t.tipo === 'dor') ? 'atrasada' : 'proxima'))],
    ['Renovação', S.renovacoes.map((x) => item(`#/aluno/${x.slug}`, x.nome,
      `${x.situacao === 'vencido' ? 'Venceu' : 'Vence'} ${dataCurta(x.vence)}`, x.situacao === 'vencido' ? 'atrasada' : 'proxima'))],
  ].filter(([, l]) => l.length);
  return `<section class="semana"><h2>Esta semana</h2>
    ${grupos.length ? `<div class="semana-grupos">${grupos.map(([t, l]) => `<div><h3>${t}</h3><ul>${l.join('')}</ul></div>`).join('')}</div>`
      : '<p class="sub">Nada pendente.</p>'}</section>`;
}

function desenharLista(alunos) {
  const q = filtro.busca.trim().toLowerCase();
  const lst = alunos
    .filter((a) => (filtro.status === 'Todos' || a.status === filtro.status) && a.nome.toLowerCase().includes(q))
    .sort((a, b) => (a.proxima_atualizacao || '9999').localeCompare(b.proxima_atualizacao || '9999'));
  const el = $('#lista');
  if (!alunos.length) {
    el.innerHTML = '<div class="vazio"><h2>Nenhum aluno ainda</h2><p>Envie a planilha matriz de um aluno.</p></div>';
    return;
  }
  if (!lst.length) { el.innerHTML = '<div class="vazio">Nenhum aluno com esse filtro.</div>'; return; }
  el.innerHTML = `<div class="lista">
    <div class="lista-cab"><span style="text-align:center">Bloco</span><span>Aluno</span><span>Plano</span>
      <span>Última atualização</span><span>Próxima atualização</span><span></span></div>
    ${lst.map((a) => `
      <a class="aluno-linha" href="#/aluno/${a.slug}">
        <div class="bloco-num">${bloco2(a.bloco_atual)}${a.semana_do_bloco >= 1 && a.semana_do_bloco <= 4 ? `<small>semana ${a.semana_do_bloco}</small>` : ''}</div>
        <div class="aluno-nome">${esc(a.nome)}</div>
        <div class="col-plano">${a.contrato ? `<span class="pilula">${esc(a.contrato.nome)}</span>
          <span class="vence ${a.contrato.situacao}">vence ${dataCurta(a.contrato.vence)}</span>`
          : '<span class="sub">—</span>'}</div>
        <div class="data col-ultima"><b>${dataCurta(a.ultima_atualizacao)}</b></div>
        <div class="data ${a.situacao}"><b>${dataCurta(a.proxima_atualizacao)}</b><span>${a.status !== 'Ativo' ? esc(a.status) : relativo(a.dias_para_proxima)}</span></div>
        <div class="acoes">
          ${a.revisao_pendente ? `<button class="btn" data-rev="${a.slug}/${a.revisao_pendente}">Revisar</button>` : ''}
          ${a.ultimo_pdf ? `<button class="btn discreto" data-pdf="${a.slug}" data-rel="${esc(a.ultimo_pdf)}" data-nome="${esc(a.nome)}">${icone.pdf} Ver PDF</button>` : ''}
        </div>
      </a>`).join('')}
  </div>`;
  el.querySelectorAll('[data-pdf]').forEach((b) => (b.onclick = (e) => {
    e.preventDefault(); e.stopPropagation();
    verPdf(b.dataset.pdf, b.dataset.rel, `Plano de treinamento — ${b.dataset.nome}`);
  }));
  el.querySelectorAll('[data-rev]').forEach((b) => (b.onclick = (e) => {
    e.preventDefault(); e.stopPropagation();
    location.hash = `#/revisao/${b.dataset.rev}`;
  }));
}

/* ---------------------------------------------------------------- FICHA DO ALUNO */
let planosTabela = [];
async function telaAluno(slug) {
  const [a, tab] = await Promise.all([api('GET', `/api/alunos/${slug}`), api('GET', '/api/planos')]);
  planosTabela = tab;
  if (a.ok === false) { tela.innerHTML = `<div class="vazio"><h2>Aluno não encontrado</h2><a class="link" href="#/">Voltar ao painel</a></div>`; return; }
  const sit = a.situacao;
  tela.innerHTML = `
    <a class="voltar" href="#/">${icone.voltar} Alunos</a>
    <div class="topo">
      <div style="flex:1 1 320px"><h1>${esc(a.nome)}</h1>
        ${a.status !== 'Ativo' ? `<p class="sub"><span class="pilula escura">${esc(a.status)}</span></p>` : ''}</div>
      <div class="topo-acoes">
        <button class="btn primario" id="atualizar">${icone.enviar} Atualizar plano</button>
        ${a.total_planilhas ? `<a class="btn" href="#/dados/${a.slug}">Dados</a>` : ''}
        <button class="btn discreto" id="excluir">${icone.lixo} Excluir</button>
      </div>
    </div>
    ${a.revisao_pendente ? `<div class="decisao" style="margin-bottom:24px;display:flex;align-items:center;gap:16px">
      <span style="flex:1">Planilha aguardando revisão.</span>
      <a class="btn" href="#/revisao/${a.slug}/${a.revisao_pendente}">Revisar</a></div>` : ''}
    <div class="grade">
      <div>
        <div class="cartao">
          <div class="duas">
            <label class="campo"><span>Nome</span><input data-campo="nome" value="${esc(a.nome)}"></label>
            <label class="campo"><span>Situação</span><select data-campo="status">
              ${['Ativo', 'Pausado', 'Encerrado'].map((s) => `<option ${s === a.status ? 'selected' : ''}>${s}</option>`).join('')}</select></label>
          </div>
          <div class="duas">
            <label class="campo"><span>Plano</span><select id="ct-plano"><option value="">—</option>
              ${planosTabela.map((p) => `<option value="${p.id}" ${a.contrato && a.contrato.plano === p.id ? 'selected' : ''}>${esc(p.nome)} · ${reais(p.valor)}</option>`).join('')}</select></label>
            <label class="campo"><span>Início do plano</span><input type="date" id="ct-inicio" value="${esc(a.contrato ? a.contrato.inicio : '')}" ${a.contrato ? '' : 'disabled'}></label>
          </div>
          ${a.contrato ? `<div class="contrato ${a.contrato.situacao}"><span>Vence em <b>${data(a.contrato.vence)}</b> · ${relativo(a.contrato.dias)} · ${reais(a.contrato.valor)}</span>
            <button class="btn" id="ct-renovar">Renovar</button></div>` : ''}
          <div class="duas">
            <label class="campo"><span>Objetivo</span><input data-campo="objetivo" value="${esc(a.objetivo || '')}"></label>
            <label class="campo"><span>Próxima atualização</span><input type="date" data-campo="proxima_atualizacao" value="${esc(a.proxima_atualizacao || '')}">
              ${a.proxima_manual ? '<span class="ajuda"><button class="link" data-auto="proxima_auto">Calcular pela planilha</button></span>' : ''}</label>
          </div>
          <label class="campo"><span>Anotações</span><textarea data-campo="notas" placeholder="Só para você">${esc(a.notas || '')}</textarea></label>
        </div>
      </div>
      <aside class="plano-atual">
        <div class="rotulo">Bloco atual</div>
        <div class="grande-bloco">${bloco2(a.bloco_atual)}</div>
        <dl>
          <div><dt class="rotulo">Início do bloco</dt><dd>${data(a.inicio_bloco)}</dd></div>
          <div><dt class="rotulo">Última atualização</dt><dd>${data(a.ultima_atualizacao)}</dd></div>
          <div><dt class="rotulo">Próxima atualização</dt><dd class="${sit}">${data(a.proxima_atualizacao)}<br><span class="peq">${relativo(a.dias_para_proxima)}</span></dd></div>
          ${a.semana_do_bloco >= 1 && a.semana_do_bloco <= 4 ? `<div><dt class="rotulo">Semana do bloco</dt><dd>${a.semana_do_bloco} de 4</dd></div>` : ''}
        </dl>
        ${a.ultimo_pdf ? `<div id="mini" class="miniaturas" style="margin-top:24px"></div>` : ''}
      </aside>
    </div>

    <section class="secao">
      <h2>Histórico de planilhas</h2>
      ${a.planilhas.length ? `<table class="tabela"><thead><tr><th>Recebida em</th><th>Arquivo</th><th>Bloco</th><th>Início do bloco</th><th>Situação</th><th></th></tr></thead><tbody>
        ${a.planilhas.map((p, i) => `<tr class="${i === 0 ? 'destaque' : ''}">
          <td class="n">${dataHora(p.enviado_em)}</td><td>${esc(p.nome_original)}</td>
          <td class="n num">${bloco2(p.bloco)}</td><td class="n">${data(p.inicio_bloco)}</td>
          <td><span class="pilula ${p.status === 'PDF gerado' ? 'escura' : p.status === 'Erro na leitura' ? 'vermelha' : 'ambar'}">${esc(p.status)}</span></td>
          <td><div class="acoes">
            ${p.status !== 'PDF gerado' ? `<a class="btn" href="#/revisao/${a.slug}/${p.id}">Revisar</a>` : `<a class="btn discreto" href="#/revisao/${a.slug}/${p.id}">Ver revisão</a>`}
            ${p.pdf ? `<button class="btn discreto" data-pdf="${esc(p.pdf)}">${icone.pdf} PDF</button>` : ''}
            <button class="btn discreto" data-planilha="${esc(p.arquivo)}">${p.original && p.original !== p.arquivo ? 'Planilha ajustada' : 'Abrir planilha'}</button>
            ${p.original && p.original !== p.arquivo ? `<button class="btn discreto" data-planilha="${esc(p.original)}">Original</button>` : ''}
          </div></td></tr>`).join('')}
      </tbody></table>` : '<p class="sub">Nenhuma planilha ainda.</p>'}
    </section>

    <details class="secao atividade"><summary>Atividade</summary>
      <ul class="eventos">${a.historico.map((h) => `<li><time>${dataHora(h.data)}</time><span>${esc(h.evento)}</span></li>`).join('')}</ul>
    </details>`;

  // salvamento automático dos campos
  let timer = null;
  const salvar = async (campo, valor) => {
    try {
      const r = await api('PATCH', `/api/alunos/${slug}`, { [campo]: valor });
      if (r.ok) aviso('Salvo');
      if (['proxima_atualizacao', 'status', 'nome'].includes(campo)) telaAluno(slug);
    } catch (e) { aviso(e.message, true); }
  };
  tela.querySelectorAll('[data-campo]').forEach((el) => {
    const campo = el.dataset.campo;
    if (el.type === 'checkbox') el.onchange = () => salvar(campo, el.checked);
    else if (el.tagName === 'SELECT' || el.type === 'date') el.onchange = () => salvar(campo, el.value);
    else {
      el.oninput = () => { clearTimeout(timer); timer = setTimeout(() => salvar(campo, el.value), 900); };
      el.onblur = () => { if (timer) { clearTimeout(timer); timer = null; salvar(campo, el.value); } };
    }
  });
  tela.querySelectorAll('[data-auto]').forEach((b) => (b.onclick = async (e) => {
    e.preventDefault();
    await api('PATCH', `/api/alunos/${slug}`, { [b.dataset.auto]: true });
    aviso('Salvo'); telaAluno(slug);
  }));
  const salvarContrato = async () => {
    const r = await api('PATCH', `/api/alunos/${slug}`, { contrato: { plano: $('#ct-plano').value, inicio: $('#ct-inicio').value } });
    if (!r.ok) { aviso(r.erro, true); return; }
    aviso('Salvo'); telaAluno(slug);
  };
  $('#ct-plano').onchange = salvarContrato;
  $('#ct-inicio').onchange = salvarContrato;
  if ($('#ct-renovar')) $('#ct-renovar').onclick = async () => {
    const r = await api('POST', `/api/alunos/${slug}/renovar`);
    if (!r.ok) { aviso(r.erro, true); return; }
    aviso('Plano renovado'); telaAluno(slug);
  };
  $('#atualizar').onclick = () => escolherPlanilha(slug);
  tela.querySelectorAll('[data-pdf]').forEach((b) => (b.onclick = () => verPdf(slug, b.dataset.pdf, `Plano de treinamento — ${a.nome}`)));
  tela.querySelectorAll('[data-planilha]').forEach((b) => (b.onclick = () => abrirArquivo(slug, b.dataset.planilha)));
  $('#excluir').onclick = async () => {
    const ok = await confirmar(`Excluir ${a.nome}?`,
      'O aluno sai do painel e vai para a lixeira, com todas as planilhas e PDFs. Dá para restaurar em Configurações.', 'Excluir aluno', true);
    if (!ok) return;
    await api('DELETE', `/api/alunos/${slug}`);
    aviso('Aluno movido para a lixeira');
    location.hash = '#/';
  };
  if (a.ultimo_pdf) miniaturas($('#mini'), slug, a.ultimo_pdf, a.nome, 2);
}

async function miniaturas(el, slug, rel, nome, max = 99) {
  const { paginas } = await api('GET', `/api/arquivo/${slug}/paginas?rel=${encodeURIComponent(rel)}`);
  el.innerHTML = Array.from({ length: Math.min(paginas, max) }, (_, i) =>
    `<button aria-label="Ver página ${i + 1}"><img alt="" src="/api/arquivo/${slug}/pagina?rel=${encodeURIComponent(rel)}&n=${i}&zoom=0.5"></button>`).join('');
  el.querySelectorAll('button').forEach((b) => (b.onclick = () => verPdf(slug, rel, `Plano de treinamento — ${nome}`)));
}

/* ---------------------------------------------------------------- REVISÃO */
async function telaRevisao(slug, envio) {
  const r = await api('GET', `/api/revisao/${slug}/${envio}`);
  const a = r.aluno;
  const cab = `<a class="voltar" href="#/aluno/${slug}">${icone.voltar} ${esc(a.nome)}</a>`;
  if (!r.tabela) {
    tela.innerHTML = `${cab}<div class="topo"><h1>Esta planilha não pôde ser lida</h1></div>
      <div class="erro-caixa">${esc(r.erro || 'Erro desconhecido.')}</div>
      <p class="sub" style="margin-top:16px">Corrija a planilha e envie de novo pelo botão “Atualizar plano” na ficha do aluno.</p>
      ${r.log ? `<details class="detalhes"><summary>Detalhes técnicos</summary><pre class="log">${esc(r.log)}</pre></details>` : ''}`;
    return;
  }
  const est = r.estado;
  const res = est.resultado;
  const nomes = Object.keys(r.rm);
  const precisaEscolher = nomes.length > 4;
  const semanas = r.semanas;
  let semanaVista = semanas[0];
  const gerado = res && res.codigo === 0;

  tela.innerHTML = `${cab}
    <div class="topo">
      <div style="flex:1 1 320px"><h1>Revisão do bloco ${bloco2(r.bloco)}</h1></div>
      ${(est.blocos_disponiveis || []).length > 1 ? `<label class="campo" style="margin:0;min-width:200px"><span>Bloco para gerar</span>
        <select id="bloco">${[...est.blocos_disponiveis].map((b) => `<option value="${b}" ${b === r.bloco ? 'selected' : ''}>Bloco ${bloco2(b)}</option>`).join('')}</select></label>` : ''}
    </div>

    <div class="resumo">
      <div><div class="rotulo">Aluno</div><div class="valor">${esc(r.nome_planilha)}</div>
        <button class="link peq" id="vincular" style="margin-top:6px">Não é este aluno?</button></div>
      <div><div class="rotulo">Início do bloco</div><div class="valor">${data(r.inicio)}</div></div>
      <div><div class="rotulo">Próxima atualização</div><div class="valor">${data(a.proxima_atualizacao || r.proxima)}</div></div>
    </div>

    <section>
      ${r.alertas.length ? `<h2 style="margin-bottom:12px">Precisa da sua decisão</h2>
      <div class="decisoes">${r.alertas.map((t) => `<div class="decisao">${esc(t)}</div>`).join('')}</div>` : ''}
      ${r.erro ? `<div class="erro-caixa" style="margin-top:12px">${esc(r.erro)}</div>` : ''}
      ${r.ajustes && r.ajustes.length ? `<details class="detalhes"><summary>Ajustes da Central (${r.ajustes.length})</summary><ul>${r.ajustes.map((t) => `<li>${esc(t)}</li>`).join('')}</ul></details>` : ''}
      ${r.infos.length ? `<details class="detalhes"><summary>Detalhes da leitura</summary><ul>${r.infos.map((t) => `<li>${esc(t)}</li>`).join('')}</ul></details>` : ''}
    </section>

    ${precisaEscolher ? `<section class="secao"><div class="cartao">
        <h2>Seus números</h2>
        <p class="sub peq">O PDF mostra até 4. Escolha quais:</p>
        <div class="numeros" id="numeros">${nomes.map((n) => `<button aria-pressed="false" data-n="${esc(n)}">${esc(n)}</button>`).join('')}</div>
        <button class="btn" id="aplicar-numeros" style="margin-top:12px" disabled>Usar estes exercícios</button></div></section>` : ''}
    ${est.numeros ? '<div class="secao"><button class="btn discreto" id="trocar-numeros">Trocar exercícios de "Seus números"</button></div>' : ''}

    <section class="secao">
      <h2>Prescrição</h2>
      ${semanas.length > 1 ? `<div class="semanas-abas">${semanas.map((s) => `<button aria-pressed="${s === semanaVista}" data-sem="${s}">Semana ${bloco2(s)}</button>`).join('')}</div>` : ''}
      <div id="prescricao"></div>
    </section>

    <section class="secao" id="resultado"></section>
    <div class="barra-final" id="barra"><div>
      <p>${gerado ? `PDF gerado em ${dataHora(res.em)}` : ''}</p>
      <button class="btn primario grande" id="gerar">${gerado ? 'Gerar de novo' : 'Gerar PDF'}</button>
    </div></div>`;

  // prescrição por semana, no formato das tabelas do PDF
  const desenharPrescricao = () => {
    const linhas = r.tabela.filter((l) => l.semana === semanaVista);
    const treinos = [...new Set(linhas.map((l) => l.treino))];
    const dia = (t) => Object.entries(r.dias).filter(([, v]) => v === `T${t}`).map(([d]) => d.toLowerCase()).join(', ');
    $('#prescricao').innerHTML = treinos.map((t) => `
      <div class="treino"><div class="treino-cab"><span>TREINO ${t}</span><span>${esc(dia(t))}</span></div>
      <table class="tabela"><thead><tr><th>Exercício</th><th>Séries</th><th>Reps</th><th>Kg</th><th>%1RM</th><th>Obs</th></tr></thead><tbody>
      ${linhas.filter((l) => l.treino === t).map((l) => `<tr><td>${esc(l.exercicio)}</td><td class="n">${esc(l.series ?? '')}</td>
        <td class="n">${esc(l.reps ?? '')}</td><td class="n">${esc(l.kg ?? '')}</td><td class="n">${esc(l.pct)}</td>
        <td>${String(l.obs || '').split(' - ').filter(Boolean).map((o) => `<span class="etq ${/gravar|anotar/i.test(o) ? 'gravar' : ''}">${esc(o.charAt(0).toUpperCase() + o.slice(1))}</span>`).join('')}${l.video ? '<span class="etq">Vídeo</span>' : ''}</td></tr>`).join('')}
      </tbody></table></div>`).join('');
  };
  desenharPrescricao();
  tela.querySelectorAll('[data-sem]').forEach((b) => (b.onclick = () => {
    semanaVista = +b.dataset.sem;
    tela.querySelectorAll('[data-sem]').forEach((x) => x.setAttribute('aria-pressed', x === b));
    desenharPrescricao();
  }));

  // opções que pedem nova leitura da planilha
  const aplicar = async (corpo, msg) => {
    const btn = $('#gerar'); btn.disabled = true;
    const r2 = await api('POST', `/api/revisao/${slug}/${envio}/opcoes`, corpo);
    if (!r2.ok) aviso(r2.erro, true); else aviso(msg);
    telaRevisao(slug, envio);
  };
  if ($('#bloco')) $('#bloco').onchange = (e) => aplicar({ bloco: +e.target.value }, 'Bloco alterado');
  if ($('#trocar-numeros')) $('#trocar-numeros').onclick = () => aplicar({ numeros: null }, 'Escolha os exercícios');
  if (precisaEscolher) {
    const sel = new Set();
    tela.querySelectorAll('#numeros button').forEach((b) => (b.onclick = () => {
      const n = b.dataset.n;
      if (sel.has(n)) sel.delete(n); else if (sel.size < 4) sel.add(n); else { aviso('No máximo 4 exercícios', true); return; }
      b.setAttribute('aria-pressed', sel.has(n));
      $('#aplicar-numeros').disabled = !sel.size;
    }));
    $('#aplicar-numeros').onclick = () => aplicar({ numeros: [...sel] }, 'Exercícios salvos para este aluno');
  }

  // vincular a outro aluno
  $('#vincular').onclick = async () => {
    const todos = (await api('GET', '/api/alunos')).filter((x) => x.slug !== slug).sort((x, y) => x.nome.localeCompare(y.nome));
    if (!todos.length) { aviso('Não há outro aluno cadastrado'); return; }
    const { el, fechar } = modal(`<h2>Vincular a outro aluno</h2>
      <p>A planilha passa para o aluno escolhido, e o nome “${esc(r.nome_planilha)}” fica lembrado para as próximas planilhas.</p>
      <select id="destino">${todos.map((x) => `<option value="${x.slug}">${esc(x.nome)}</option>`).join('')}</select>
      <div class="botoes"><button class="btn discreto" data-n>Cancelar</button><button class="btn primario" data-s>Vincular</button></div>`);
    $('[data-n]', el).onclick = fechar;
    $('[data-s]', el).onclick = async () => {
      const destino = $('#destino', el).value;
      fechar();
      const v = await api('POST', `/api/revisao/${slug}/${envio}/vincular`, { slug: destino });
      if (v.ok) { aviso('Planilha vinculada'); location.hash = `#/revisao/${destino}/${envio}`; } else aviso(v.erro, true);
    };
  };

  // gerar
  const mostrarResultado = (ok, info) => {
    const box = $('#resultado');
    if (ok) {
      box.innerHTML = `<h2 style="margin-bottom:14px">PDF pronto</h2>
        <div class="resultado"><div class="miniaturas" id="mini-res"></div>
        <div><div class="tudo-certo">Conferido contra a planilha, sem divergências.</div>
          <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:18px">
            <button class="btn primario" data-ver>${icone.pdf} Ver PDF</button>
            <button class="btn" data-pasta>${icone.pasta} Mostrar na pasta</button></div></div></div>`;
      miniaturas($('#mini-res'), slug, info.pdf, a.nome, 4);
      $('[data-ver]', box).onclick = () => verPdf(slug, info.pdf, `Plano de treinamento — ${a.nome}`);
      $('[data-pasta]', box).onclick = () => abrirArquivo(slug, info.pdf, true);
    } else {
      box.innerHTML = `<h2 style="margin-bottom:14px">O PDF não foi liberado</h2><div class="erro-caixa">${esc(info.erro)}</div>
        ${info.log ? `<details class="detalhes"><summary>Detalhes técnicos</summary><pre class="log">${esc(info.log)}</pre></details>` : ''}`;
    }
    box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  $('#gerar').onclick = async () => {
    const btn = $('#gerar');
    btn.disabled = true; btn.textContent = 'Gerando…';
    try {
      const g = await api('POST', `/api/revisao/${slug}/${envio}/gerar`, {});
      mostrarResultado(g.ok, g);
      if (g.ok) aviso('PDF gerado');
      btn.textContent = g.ok ? 'Gerar de novo' : 'Tentar de novo';
    } catch (e) { aviso(e.message, true); btn.textContent = 'Tentar de novo'; }
    btn.disabled = false;
  };
  if (gerado) {
    const ultimo = r.entrada.pdf;
    if (ultimo) mostrarResultado(true, { pdf: ultimo });
  } else if (res && res.codigo !== 0) {
    mostrarResultado(false, { erro: res.mensagem || 'O PDF não foi gerado.', log: res.log });
  }
}

/* ---------------------------------------------------------------- RESUMO DO MÊS */
const MESES_LONGOS = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
const mesResumo = { ano: null, mes: null };
async function telaResumo() {
  const hoje = new Date();
  if (!mesResumo.ano) { mesResumo.ano = hoje.getFullYear(); mesResumo.mes = hoje.getMonth() + 1; }
  const r = await api('GET', `/api/resumo?ano=${mesResumo.ano}&mes=${mesResumo.mes}`);
  tela.innerHTML = `<div class="topo"><h1>Resumo</h1>
      <div class="mes-sel"><button class="btn discreto" data-mes="-1" aria-label="Mês anterior">‹</button>
        <b>${MESES_LONGOS[r.mes - 1]} de ${r.ano}</b><button class="btn discreto" data-mes="1" aria-label="Próximo mês">›</button></div></div>
    <div class="indicadores">
      <div class="indicador"><b>${r.alunos}</b><span>alunos ativos com plano</span></div>
      <div class="indicador"><b>${reais(r.previsto)}</b><span>previsto no mês${r.renovado ? ` · ${reais(r.renovado)} já renovado` : ''}</span></div>
      <div class="indicador"><b>${reais(r.mensal)}</b><span>média por mês</span></div>
    </div>
    <div class="grade">
      <section class="secao" style="margin-top:0"><h2>Vencimentos</h2>
        ${r.vencimentos.length ? `<table class="tabela"><tbody>${r.vencimentos.map((v) => `<tr>
          <td class="n">${data(v.data)}</td><td><a class="link" href="#/aluno/${v.slug}">${esc(v.nome)}</a></td>
          <td class="sub">${esc(v.plano)}</td><td class="n">${reais(v.valor)}</td>
          <td>${v.situacao === 'vencido' ? '<span class="pilula vermelha">vencido</span>' : v.situacao === 'renovado' ? '<span class="pilula escura">renovado</span>' : ''}</td></tr>`).join('')}</tbody></table>`
          : '<p class="sub">Nenhum vencimento neste mês.</p>'}</section>
      <aside class="secao" style="margin-top:0"><h2>Por plano</h2>
        ${r.planos.length ? `<table class="tabela"><tbody>${r.planos.map((p) => `<tr><td>${esc(p.nome)}</td>
          <td class="n">${p.alunos} ${p.alunos === 1 ? 'aluno' : 'alunos'}</td><td class="n">${reais(p.mensal)}<span class="sub peq">/mês</span></td></tr>`).join('')}</tbody></table>`
          : '<p class="sub">Nenhum aluno com plano.</p>'}
        ${r.sem_plano.length ? `<details class="detalhes"><summary>Sem plano (${r.sem_plano.length})</summary><ul>${r.sem_plano.map((x) => `<li><a class="link" href="#/aluno/${x.slug}">${esc(x.nome)}</a></li>`).join('')}</ul></details>` : ''}
      </aside>
    </div>`;
  tela.querySelectorAll('[data-mes]').forEach((b) => (b.onclick = () => {
    const m = mesResumo.mes + +b.dataset.mes;
    mesResumo.ano += m > 12 ? 1 : m < 1 ? -1 : 0;
    mesResumo.mes = ((m + 11) % 12) + 1;
    telaResumo();
  }));
}

/* ---------------------------------------------------------------- CONFIGURAÇÕES */
async function telaConfig() {
  const [s, lix, planosTab] = await Promise.all([api('GET', '/api/sistema'), api('GET', '/api/lixeira'), api('GET', '/api/planos')]);
  tela.innerHTML = `<div class="topo"><h1>Configurações</h1></div>
    <div class="grade">
      <div>
        <div class="cartao">
          <h2>Backup</h2>
          <p class="sub">Cópia automática todo dia. Exporte de vez em quando para fora do computador.</p>
          <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:18px">
            <button class="btn primario" id="exportar">Exportar backup</button>
            <button class="btn" id="restaurar">Restaurar</button>
          </div>
          ${s.backups.length ? `<details class="detalhes"><summary>Cópias automáticas (${s.backups.length})</summary><ul>${s.backups.map((b) => `<li>${esc(b.nome)} · ${b.kb} KB</li>`).join('')}</ul></details>` : ''}
          <input type="file" id="arq-backup" accept=".zip" hidden>
        </div>
        <div class="cartao">
          <h2>Lixeira</h2>
          ${lix.length ? `<table class="tabela"><tbody>${lix.map((x) => `<tr><td>${esc(x.nome)}</td><td class="n sub">excluído em ${esc(x.excluido_em)}</td>
            <td><div class="acoes"><button class="btn" data-rest="${esc(x.id)}">Restaurar</button></div></td></tr>`).join('')}</tbody></table>`
            : '<p class="sub">Vazia.</p>'}
        </div>
      </div>
      <aside>
      <div class="cartao">
        <h2>Planos e valores</h2>
        <div class="tabela-planos">${planosTab.map((p) => `<label><span>${esc(p.nome)}</span><span class="rs">R$</span>
          <input type="number" min="0" step="1" data-plano="${p.id}" value="${p.valor}"></label>`).join('')}</div>
      </div>
      <div class="cartao">
        <h2>Sistema</h2>
        <p>Template <b>v${esc(s.template)}</b></p>
        <button class="btn" id="diag" style="margin-top:18px">Conferir instalação</button>
        <div id="diag-res" style="margin-top:14px"></div>
      </div>
      </aside>
    </div>`;
  tela.querySelectorAll('[data-plano]').forEach((inp) => (inp.onchange = async () => {
    const r = await api('PUT', '/api/planos', { [inp.dataset.plano]: inp.value });
    aviso(r.ok ? 'Salvo' : r.erro, !r.ok);
  }));
  $('#exportar').onclick = async () => {
    const r = await api('POST', '/api/backup/exportar');
    aviso(r.ok ? 'Backup salvo em Documentos' : r.erro, !r.ok);
  };
  $('#restaurar').onclick = () => $('#arq-backup').click();
  $('#arq-backup').onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const ok = await confirmar('Restaurar este backup?', 'Todos os dados atuais serão substituídos pelos do backup. Antes, o programa guarda uma cópia do estado atual.', 'Restaurar', true);
    if (!ok) return;
    const fd = new FormData(); fd.append('arquivo', f);
    const r = await api('POST', '/api/backup/restaurar', fd);
    aviso(r.mensagem, !r.ok);
    if (r.ok) location.hash = '#/';
  };
  tela.querySelectorAll('[data-rest]').forEach((b) => (b.onclick = async () => {
    const r = await api('POST', `/api/lixeira/${encodeURIComponent(b.dataset.rest)}/restaurar`);
    if (r.ok) { aviso('Aluno restaurado'); location.hash = `#/aluno/${r.slug}`; } else aviso(r.erro, true);
  }));
  $('#diag').onclick = async () => {
    $('#diag-res').innerHTML = '<p class="sub">Conferindo…</p>';
    const itens = await api('POST', '/api/diagnostico');
    $('#diag-res').innerHTML = itens.map((i) => `<div class="${i.ok ? 'tudo-certo' : 'erro-caixa'}" style="margin-bottom:8px;font-weight:600">${i.ok ? '✓' : '✗'} ${esc(i.nome)}${i.dica ? `<br><span class="peq">${esc(i.dica)}</span>` : ''}</div>`).join('');
  };
}

/* ---------------------------------------------------------------- rotas */
async function rotear() {
  const h = location.hash || '#/';
  const rota = h.startsWith('#/config') ? 'config' : h.startsWith('#/dados') ? 'dados' : h.startsWith('#/resumo') ? 'resumo' : 'painel';
  document.querySelectorAll('.faixa-nav a').forEach((a) => a.classList.toggle('ativo', a.dataset.rota === rota));
  if (typeof esconderDica === 'function') esconderDica();
  if (!$('#modal').hidden) { $('#modal').hidden = true; $('#modal').innerHTML = ''; }
  try {
    let m;
    if ((m = h.match(/^#\/dados\/([^/]+)(\/feedback)?/))) await telaDadosAluno(m[1], false, m[2] ? 'individual' : null);
    else if (h.startsWith('#/dados')) await telaDadosLista();
    else if ((m = h.match(/^#\/aluno\/([^/]+)/))) await telaAluno(m[1]);
    else if ((m = h.match(/^#\/revisao\/([^/]+)\/([^/]+)/))) await telaRevisao(m[1], m[2]);
    else if (h.startsWith('#/config')) await telaConfig();
    else if (h.startsWith('#/resumo')) await telaResumo();
    else await telaPainel();
  } catch (e) {
    tela.innerHTML = `<div class="vazio"><h2>Algo não carregou</h2><p>${esc(e.message)}</p><p><a class="link" href="#/">Voltar ao painel</a></p></div>`;
  }
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', rotear);
window.addEventListener('DOMContentLoaded', rotear);   // depois de carregar dados.js

// sinal de vida: quando a janela fecha, o programa encerra sozinho
const ping = () => fetch('/api/ping').catch(() => {});
ping();
setInterval(ping, 5000);
