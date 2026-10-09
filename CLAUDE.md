# Central da Consultoria — instruções para o Claude Code

App de área de trabalho de Miguel Valcanover (FORÇA & INTELIGÊNCIA) para a **prescrição e entrega do PDF de treinamento**
a partir da planilha matriz, e aba DADOS (VTT, VTR, %1RM do planejado por semana/exercício,
anamnese e feedback semanal anexados, PDFs pré e pós para o aluno). Veja o README.md.

## Regras inegociáveis
- **Sem IA e sem internet** no uso. Não adicionar APIs, nuvem, contas ou chaves. Internet só no INSTALAR.
- **Sem terminal para o usuário.** Abre pelo atalho (pythonw + Central.pyw). Todo subprocess no Windows usa
  `creationflags=CREATE_NO_WINDOW` (ver `app/planilha.py`). Erros vão para `dados/central.log` ou caixa de mensagem.
- **Tudo salvo automaticamente**, sempre por `armazenamento.gravar_seguro`/`gravar_json` (gravação atômica).
  Nunca apagar planilhas recebidas (`planilhas/`). PDF de entrega: `pdfs/MariaSilva_Bloco02.pdf`, um por bloco; gerar de novo
  o mesmo bloco substitui o anterior (decisão de Miguel, 9/out/2026). Excluir aluno = mover para `dados/lixeira/`.
  Dados novos ficam em `dados/` (entram no backup).
- **Não alterar nada em `motor/consultoria-planilha/`** (template travado por hash em `TEMPLATE_LOCK.json`).
  Mudança visual só com autorização explícita de Miguel, seguindo o SKILL.md do motor. O app chama os scripts por subprocess.
- A prescrição é de Miguel: o PDF reproduz a planilha (a cópia ajustada, ver abaixo). Inconsistência vira alerta, nunca correção.
- Nunca inventar dados. PR real só com exercício, kg, data e fonte. "Seus números": no máximo 4.
- Aba DADOS: o planejado tem de bater com a aba MACRO da planilha (VTT = SUMPRODUCT séries×reps×kg; VTR = séries×reps;
  %1RM = AVERAGEIF >0). Alerta = aumento de VTT, VTR ou intensidade média (relativo, não em pontos) > 25% sobre a semana
  anterior (regra de Miguel; era 10%, passou a 25% em 8/out/2026). A seção "Por dia de treino" foi retirada a pedido de Miguel.
  PSE: desligada na ficha para todos os alunos (decisão de Miguel, nenhum usa por enquanto; o app nunca passa --usa-pse
  e esconde o alerta de PSE da revisão). Na aba DADOS a PSE só aparece se o aluno anotar.
  Faixa de reps, AMRAP e tempo somam ZERO em VTT/VTR. Sem registro de treino realizado (removido a pedido de Miguel,
  5/out/2026; `realizado.json` antigos são ignorados, nunca apagados).
- PDFs para o aluno (`app/relatorios.py`): capa no desenho da capa do template (usa CSS/fontes/imagens do motor sem
  alterá-los) + 1 página; sem promessas, sem linguagem de guru, sem enquadrar como estética.
  Anamnese e feedback NÃO entram na ficha de entrega do bloco (regra da skill). Nos PDFs pré/pós os itens pessoais são escolhidos
  automaticamente (`relatorios.itens_auto`, decisão de Miguel 5/out/2026: sem editor na interface), sem diagnóstico. As regras
  (`app/formularios.py`) acham as perguntas pelo TEXTO, nunca usam medicação/diagnóstico/peso/altura/nascimento/profissão/
  fumo/álcool/contatos, e só preenchem a 2ª parte com fato verificável (planilha, metodologia fixa, feedback mais recente).
  Máximo 4 itens, só com as duas partes; cada texto em até 2 linhas no PDF (medido no Chromium: encurta o texto do aluno ou tira o item) e sem palavra solta (nbsp). O pré sempre mostra a
  tabela "Principais exercícios" só com nome + 1RM estimado do bloco; os itens pessoais e essa tabela nunca são cortados.
- Parte administrativa (`app/planos.py`): plano contratado no aluno.json ("contrato"), tabela de valores em
  dados/planos.json (padrão = PDF de planos de Miguel). Mensal = 4 semanas, trimestral = 12 (também no personal). Valor gravado no
  contrato ao contratar/renovar. Aba Resumo: previsto no mês, média por mês, vencimentos, alunos por plano.
- "Esta semana" (`/api/semana`, topo do painel): blocos para montar em 7 dias, alunos na semana 3 (teste com vídeo),
  feedbacks com atenção não vistos, renovações. Triagem do feedback em `formularios.triagem` (dor, adesão, objetivo,
  sugestão, recuperação): só marca, nunca interpreta nem diagnostica; "visto" fica em feedbacks.json.
- Prescrição e periodização são de Miguel (9/out/2026: modelos de bloco e modelos-base de periodização EXCLUÍDOS da
  Central e das skills). Ele envia a planilha totalmente planejada; ao receber, `app/ajuste.py` grava uma CÓPIA AJUSTADA
  (`planilhas/<envio>_ajustada_<arquivo>`; a original fica intacta ao lado) e o PDF e a aba Dados saem dela:
  aquecimento 1×3 a 65/70/80% (+90% acima de 90%) antes da principal dos exercícios da aba prs com 1RM, só os degraus
  abaixo da carga, kg no múltiplo de 1 kg, abrindo espaço e descendo os de baixo (não insere se Miguel já escreveu mais
  de uma série não-AMRAP do exercício no treino/semana). O AMRAP NÃO é ajustado: Miguel indica na planilha quais séries
  são AMRAP (9/out/2026; a regra "AMRAP 1x por semana" foi retirada). GRAVAR/ANOTAR/Aquecimento-Principal seguem no motor.
  "Ajustes da Central" aparecem na revisão. Gravação só por `app/xlsx_celulas.py` (XML direto; fórmulas, macro e
  gráficos intactos). Teste: `python testes/testar_ajuste.py`.
- Planilhas matriz: layout novo (exercício de cada semana na própria coluna, B/C, I/J, P/Q, W/X) e antigo; motor
  (`extrair_dados.colunas_semanas`), aba Dados e ajuste leem os dois (autorizado por Miguel em 7/out/2026).
- Testes só com aluno fictício (`motor/consultoria-planilha/exemplos/exemplo.xlsx`), nunca planilha real.
- Interface na identidade do PDF: preto/branco, Krona One (títulos e números) + Exo 2, gorila, retícula.
  Português do Brasil, frases curtas, sem jargão técnico para o usuário. Minimalista (pedido de Miguel): sem textos de
  ajuda, sem botões redundantes; o secundário fica recolhido em <details>.

## Rodar
`.venv\Scripts\python Central.pyw` — ou só o servidor: `python -c "from app.servidor import app; app.run(port=8765)"`.
Teste do motor: `python motor/consultoria-planilha/scripts/verificar_template.py`.

## GitHub
Cópia do código em `github.com/miguelvalcanoverborges/central` (privado, branch `main`). Decisão de Miguel (9/out/2026):
**toda mudança no código vai para o GitHub** logo depois de feita (commit + push em `main`). A Central em si continua
sem internet no uso; quem envia é quem altera o código. Nunca enviar `dados/`, `backups/`, `ferramentas/`, `.venv/`
(já no `.gitignore`) nem planilhas reais de aluno. Sem git neste computador: pedir no projeto CONSULTORIA do Claude
"atualize a Central no GitHub".
