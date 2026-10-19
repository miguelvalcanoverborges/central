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
  o mesmo bloco substitui o anterior (decisão de Miguel, 9/out/2026). Semanas avulsas (Miguel, 10/out/2026): na barra da
  revisão escolhe-se as semanas; o PDF parcial é a mesma ficha só com elas (`dados_semanas.json` filtrado, template intacto,
  conferido) em arquivo próprio (`_Semana03`, `_Semanas03a04`, `_Semanas01e03`) que não substitui o do bloco inteiro.
  Excluir aluno = apagar DE VEZ (Miguel, 12/out/2026, `app/exclusao.py`): pasta do aluno, cópias na lixeira, leituras
  interrompidas em `_entrada`, a parte dele em cada backup (backups/ e os exportados em Documentos) e as linhas do log;
  a confirmação lista tudo isso e exige o nome digitado. É a única exceção a "nunca apagar planilhas". A lixeira só
  guarda exclusões antigas (restaurar ou excluir). Teste: `python testes/testar_exclusao.py`.
  Dados novos ficam em `dados/` (entram no backup).
- **Não alterar nada em `motor/consultoria-planilha/`** (template travado por hash em `TEMPLATE_LOCK.json`).
  Mudança visual só com autorização explícita de Miguel, seguindo o SKILL.md do motor. O app chama os scripts por subprocess.
- A prescrição é de Miguel: o PDF reproduz a planilha (a cópia ajustada, ver abaixo). Inconsistência vira alerta, nunca correção.
- Nunca inventar dados. 1RM para o aluno: só o estimado da aba prs ("PR real" retirado a pedido de Miguel, 9/out/2026); desde a
  v1.15 a ficha não tem "Seus números" (o 1RM do bloco está no "Seu planejamento") e a revisão não pede mais essa escolha.
- Aba DADOS: lê a planilha ORIGINAL (`dados.planilha_atual`): o aquecimento da Central NÃO entra em VTT/VTR/%1RM
  (Miguel, 10/out/2026). O planejado tem de bater com a aba MACRO da planilha (VTT = SUMPRODUCT séries×reps×kg; VTR = séries×reps;
  %1RM = AVERAGEIF >0). Alerta = aumento de VTT, VTR ou intensidade média (relativo, não em pontos) > 25% sobre a semana
  anterior (regra de Miguel; era 10%, passou a 25% em 8/out/2026). A seção "Por dia de treino" foi retirada a pedido de Miguel.
  PSE: desligada na ficha para todos os alunos (decisão de Miguel, nenhum usa por enquanto; o app nunca passa --usa-pse
  e esconde o alerta de PSE da revisão). Na aba DADOS a PSE só aparece se o aluno anotar.
  Faixa de reps, AMRAP e tempo somam ZERO em VTT/VTR. Sem registro de treino realizado (removido a pedido de Miguel,
  5/out/2026; `realizado.json` antigos são ignorados, nunca apagados).
- PDFs para o aluno (`app/relatorios.py`): pós = capa no desenho da capa do template (usa CSS/fontes/imagens do motor sem
  alterá-los) + até 2 páginas (Miguel, 16/out/2026: 2ª página só com "Como você se sentiu" quando há feedback); pré "Seu planejamento" = sem capa e sem gráficos (Miguel, 9/out/2026), DUAS páginas (Miguel, 18/out/2026), modelo "Capítulos"
  (Miguel, 19/out/2026: seções numeradas 01, 02…; a sobra de cada página é dividida entre as seções, sem vazio no fim;
  "Como vamos acompanhar" vai para a página que deixa as duas mais equilibradas). Acompanha as semanas entregues (última
  entrega do bloco: bloco inteiro ou semanas avulsas; próxima revisão = dia seguinte à última semana). 1ª = perfil
  ("Esta entrega"), "Pensado para você" (um ponto da anamnese por linha, até 6: motivação, dor e lesões, rotina,
  preferências, outra atividade, sono; o ponto aparece mesmo sem 2ª parte, que só vem com fato verificável, Miguel
  19/out/2026), ciclo (só com mais de um bloco) e 1RM; 2ª = "Como ler a sua ficha" (`relatorios.html_como_ler`: uma linha real da ficha
  lida em palavras + a legenda do template só com o que a ficha do bloco mostra, lida do dados.json do envio), "Se faltar
  um treino" (regra de Miguel, 18/out/2026: faz o treino que faltou, nunca pula; texto fixo, `relatorios.html_faltou`) e "Como
  vamos acompanhar". Individualizada:
  ciclo pelo plano contratado (mensal = só o bloco; trimestral = 3 blocos; sem plano = só os blocos da planilha), "Como vamos
  acompanhar" só com Anote/Grave/Teste se o bloco tiver ANOTAR/GRAVAR/AMRAP (o teste é na semana do AMRAP, nunca "semana 3");
  arquivo `pdfs/MariaSilva_Bloco02_Planejamento.pdf`, substituído ao gerar de novo (também sai pelo botão "Planejamento" do
  "PDF pronto" da revisão, para a entrega ficar numa tela só); pós = `pdfs/MariaSilva_Bloco01_Resultados.pdf` (bloco da
  semana atual), substituído ao gerar de novo; em "O seu ciclo" os blocos anteriores ao do PDF são "concluído"; sem promessas, sem linguagem de guru, sem enquadrar como estética.
  Anamnese e feedback NÃO entram na ficha de entrega do bloco (regra da skill). Nos PDFs pré/pós os itens pessoais são escolhidos
  automaticamente (`relatorios.itens_auto`, decisão de Miguel 5/out/2026: sem editor na interface), sem diagnóstico. As regras
  (`app/formularios.py`) acham as perguntas pelo TEXTO, nunca usam medicação/diagnóstico/peso/altura/nascimento/profissão/
  fumo/álcool/contatos, e só preenchem a 2ª parte com fato verificável (planilha, metodologia fixa, feedback mais recente).
  Pós: máximo 4 itens, só com as duas partes. Cada texto em até 2 linhas no PDF (medido no Chromium: encurta o texto do aluno ou tira o item) e sem palavra solta (nbsp). O pré sempre mostra a
  tabela "Principais exercícios" só com nome + 1RM estimado do bloco; os itens pessoais e essa tabela nunca são cortados.
- Mensagens para o WhatsApp junto do PDF (Miguel, 11/out/2026, outra conversa): texto e regras em
  `motor/consultoria-planilha/scripts/mensagem.py` (o mesmo da skill consultoria-planilha; `app/mensagens.py` só junta os
  dados do aluno). Num lugar só (Miguel, 12/out/2026): seção "Para enviar" no topo da ficha do aluno, com a última
  entrega (ficha + Seu planejamento do bloco, uma mensagem para os dois; "+ Planejamento" se faltar) e o último PDF de
  Resultados, cada um com o texto visível e "Copiar mensagem". "PDF pronto" e a aba PDFs só levam até lá ("Enviar").
  Próxima revisão na mensagem de entrega (Miguel, 18/out/2026) = dia seguinte à última semana enviada: bloco inteiro =
  fim do bloco (nem sempre 4 semanas), semana avulsa = semana seguinte.
  O PDF é o principal (Miguel, 11/out/2026): a mensagem de resultados só aponta para o PDF e diz o início do próximo
  bloco, sem repetir 1RM ou itens; a mensagem de entrega (ficha + planejamento) fica como está.
  A aba Textos (`app/textos.py`), feita em paralelo no mesmo dia, foi retirada por decisão de Miguel (11/out/2026).
- Parte administrativa (`app/planos.py`): plano contratado no aluno.json ("contrato"), tabela de valores em
  dados/planos.json (padrão = PDF de planos de Miguel). Mensal = 4 semanas, trimestral = 12 (também no personal). Valor gravado no
  contrato ao contratar/renovar. Aba Resumo: previsto no mês, média por mês, vencimentos, alunos por plano.
- "Esta semana" (`/api/semana`, topo do painel): blocos para montar em 7 dias, alunos com AMRAP na semana atual (teste com vídeo),
  feedbacks com atenção não vistos, renovações. Triagem do feedback em `formularios.triagem` (dor, adesão, objetivo,
  sugestão, recuperação): só marca, nunca interpreta nem diagnostica; "visto" fica em feedbacks.json.
- Respostas do Forms em lote (Miguel, 16/out/2026, `app/forms.py`): a planilha de anamnese ou feedback é solta no mesmo lugar
  da planilha matriz (`/api/planilha` reconhece pelas abas); conferência obrigatória antes de gravar; associação automática só
  com nome bem parecido com UM aluno (apelidos confirmados em `nomes_forms`; ignorados em dados/_forms/ignorados.json);
  anamnese de quem não tem cadastro fica pendente (dados/_forms/pendentes.json) e é oferecida na ficha quando o aluno existir.
  A planilha bruta não fica guardada (só a cópia de cada aluno em anexos/). A importação aluno por aluno foi retirada.
  Código morto removido no mesmo dia: `app/modelos.py` e seus testes (modelos de bloco excluídos em 9/out/2026).
- Feedback semanal (Miguel, 16/out/2026): importar a planilha do Forms de novo SUBSTITUI a resposta já guardada (mesma
  data/hora do Forms; se mudou, o "visto" volta a pendente) e nunca duplica. Notas em `formularios.notas` (3 bom,
  2 mais ou menos, 1 ruim; "Sem dor" invertida; resposta não reconhecida fica sem nota, nunca adivinhada). Na Central: linha
  do tempo (`relatorios.svg_feedback`) na aba "Anamnese e feedback", com as 5 perguntas. No PDF de Resultados: página
  própria "COMO VOCÊ SE SENTIU" (`relatorios.tabela_feedback`, escolhida por Miguel em 16/out/2026): tabela por semana com
  palavras (Treinos, Sono, Dor, Recuperação; "Treino × objetivo" NÃO entra no PDF), "—" sem resposta, sem legenda embaixo (Miguel, 16/out/2026), no máximo as 12
  últimas semanas; sem nenhum feedback a página não é gerada. Cada página tem de caber (medido no Chromium).
- Prescrição e periodização são de Miguel (9/out/2026: modelos de bloco e modelos-base de periodização EXCLUÍDOS da
  Central e das skills). Ele envia a planilha totalmente planejada; ao receber, `app/ajuste.py` grava uma CÓPIA AJUSTADA
  (`planilhas/<envio>_ajustada_<arquivo>`; a original fica intacta ao lado) e o PDF sai dela (a aba Dados usa a original):
  aquecimento 65%×3, 70%×2, 80%×1 (+90%×1 acima de 90%; reps caindo, Miguel 10/out/2026) antes da principal dos exercícios da aba prs com 1RM, só os degraus
  abaixo da carga, kg no múltiplo de 1 kg, abrindo espaço e descendo os de baixo (não insere se Miguel já escreveu mais
  de uma série não-AMRAP do exercício no treino/semana). O AMRAP NÃO é ajustado: Miguel indica na planilha quais séries
  são AMRAP (9/out/2026; a regra "AMRAP 1x por semana" foi retirada). GRAVAR/ANOTAR/Aquecimento-Principal seguem no motor.
  Template v1.13 (Miguel, 12/out/2026): no PDF o aquecimento é sub-linha cinza da série principal (uma semana por página).
  Template v1.14 (Miguel, 17/out/2026): vídeo = só o ícone ▶ (ficha, AQC e revisão), sem "Ver vídeo" e sem o título
  do vídeo como nota; numa linha com vídeo a OBS guarda só as etiquetas.
  Template v1.15 (Miguel, 18/out/2026): a ficha é capa + semanas; a página "Seu perfil / Seus números / Como ler a sua ficha"
  saiu (a legenda foi para a 2ª página do "Seu planejamento") e a observação geral abre a 1ª página de treino.
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
"atualize a Central no GitHub". Ao reescrever este arquivo, manter esta seção.
