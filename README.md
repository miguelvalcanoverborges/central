# Central da Consultoria — FORÇA & INTELIGÊNCIA

Programa de Miguel Valcanover para a **prescrição e entrega do PDF de treinamento** a partir da planilha matriz,
usando o motor da skill `consultoria-planilha` (template mestre v1.11, travado).

- Abre pelo **ícone de gorila na área de trabalho**, numa janela própria. Nada de terminal ou CMD.
- **Sem IA e sem internet** no uso do dia a dia. Tudo fica no seu computador.
- **Tudo é salvo automaticamente**, com backup diário.

---

## Instalar (uma vez só)

1. Descompacte a pasta `central-consultoria` num lugar fixo, por exemplo `Documentos\central-consultoria`.
   (Não apague nem mova a pasta depois: é nela que ficam o programa e os dados.)
2. Dê dois cliques em **`INSTALAR.bat`**.
   Ele instala o Python (se faltar), as bibliotecas, o gerador de PDF e a conferência do PDF (Poppler), testa a
   geração com o aluno de exemplo e cria o **ícone de gorila** na área de trabalho e no menu Iniciar.
   Leva alguns minutos e é o único momento que precisa de internet. Se o Windows perguntar, permita.
3. No fim, a Central abre sozinha. Daí em diante, é só usar o ícone.

Requisitos: Windows 10 ou 11 (a janela usa o Microsoft Edge, que já vem no Windows).

---

## Como usar

**Enviar a planilha matriz.** No painel, arraste a planilha para a área preta (ou para qualquer lugar da janela),
ou clique em "Escolher planilha". O programa, sozinho:

1. identifica o aluno pelo nome da planilha (aba aluno, C2) — se for novo, ele entra no painel;
2. lê o **bloco atual** e a data de início;
3. calcula a **próxima atualização**: o início do próximo bloco na aba macro, ou 4 semanas após o início;
4. aplica o que você já decidiu para esse aluno (exercícios de "Seus números");
5. abre a **revisão**: o que precisa da sua decisão (só aparece se houver), a prescrição lida e os ajustes da Central.
   A ficha sai sem PSE (nenhum aluno usa PSE por enquanto).

Clique em **Gerar PDF**. O PDF é gerado no template mestre e conferido contra a planilha
(exercícios, séries, reps, cargas, %1RM, vídeos, datas). Só é liberado sem divergências.

**Esta semana.** No topo do painel, só o que pede ação nos próximos 7 dias (ou "Nada pendente"):
**Montar bloco** (próxima atualização em até 7 dias ou atrasada), **AMRAP** (alunos com AMRAP prescrito na semana atual, com os exercícios),
**Feedback** (feedbacks com ponto de atenção ainda não vistos) e **Renovação** (plano vence em 7 dias ou venceu).
Clique no nome para ir ao aluno (no feedback, direto para a aba Anamnese e feedback).

**Painel.** Alunos ordenados pela próxima atualização, com bloco, semana do bloco, plano contratado, última e próxima
atualização (âmbar = nos próximos 7 dias; vermelho = atrasada). "Ver PDF" abre o plano do aluno dentro do app.
A interface é enxuta de propósito: textos de ajuda saíram; o que é secundário (atividade, respostas da
anamnese, cada feedback) fica recolhido e abre com um clique.

**Ficha do aluno.** Clique no nome:
- editar nome, situação (ativo, pausado, encerrado), plano contratado, objetivo, próxima atualização e anotações
  — salva sozinho;
- **Atualizar plano**: envie a nova versão da planilha (ou arraste o arquivo na ficha);
- **Histórico de planilhas**: todas as planilhas recebidas, com data, bloco, situação, PDF e a planilha original;
- **Excluir**: o aluno vai para a lixeira (Configurações → Lixeira → Restaurar).

Se o programa ligar a planilha ao aluno errado (nome escrito diferente), use "Não é este aluno?" na revisão:
a planilha passa para o aluno certo e o nome fica lembrado para as próximas.

**Ajustes da Central.** A prescrição e a periodização são suas: envie a planilha totalmente planejada. Ao recebê-la,
a Central grava uma **cópia ajustada** (a original fica guardada, intacta) e o PDF sai dela. A aba Dados usa a original: o aquecimento da Central não
entra no VTT, VTR e %1RM (Miguel, 10/out/2026).
- **Aquecimento** antes da série principal dos exercícios da aba prs com 1RM: 65%×3, 70%×2 e 80%×1 do 1RM, só os degraus
  abaixo da carga (acima de 90%, mais 90%×1), kg no múltiplo de 1 kg. A Central abre espaço descendo os exercícios
  de baixo. Se você já escreveu mais de uma série do exercício naquele treino e semana, nada é inserido ali.
- **AMRAP** fica exatamente como você escreveu na planilha: é você quem indica quais séries são AMRAP.
- **GRAVAR** (AMRAP e 80% ou mais, nunca no aquecimento) e **ANOTAR** (faixa de repetições e AMRAP) continuam automáticos.
- Na revisão, "Ajustes da Central" lista o que mudou; no histórico, "Planilha ajustada" e "Original".

**Plano e renovação.** O único "plano" da Central é o contratado (a frequência muda de semana para semana e não é
guardada). Na ficha do aluno, escolha o **plano** (Online, Híbrida ou Personal, com a
modalidade) e o **início do plano**. A Central mostra o vencimento e o valor; o botão **Renovar** abre o próximo período
a partir do vencimento, com o valor da tabela do dia. Mensal = 4 semanas; trimestral = 12 semanas (também no personal).
No painel, a coluna Plano mostra o plano e o vencimento (âmbar = vence em 7 dias; vermelho = vencido), e o "Esta semana"
avisa planos vencidos e renovações próximas.

**Resumo.** A aba ao lado de Dados: alunos ativos com plano, **previsto no mês** (vencimentos do mês, com o que já foi
renovado), **média por mês** (trimestral conta ÷ 3), vencimentos do mês e alunos por plano. As setas trocam o mês.
Os valores da tabela de planos ficam em **Configurações → Planos e valores** (mudar um valor não altera contratos já feitos).

**Dados.** A aba ao lado de Alunos. Um cartão por aluno (semana atual, VTT, VTR, %1RM e quantas semanas passaram de
25% de aumento). Clique no aluno para ver, **só com o planejado da planilha** (o treino realizado não é registrado no app):

- **VTT, VTR e intensidade média (%1RM) de cada semana** (S01 a S12), em gráficos e na tabela semanal — a aba MACRO
  da planilha, com a variação em % de uma semana para a outra. ▲ vermelho = VTT, VTR ou intensidade média subiu **mais
  de 25%** (na intensidade, aumento relativo: 60% → 75,6% = +26%). O limite era 10% e passou para 25% a pedido de Miguel (8/out/2026).
- **Séries por faixa de intensidade** (abaixo de 70%, 70–80%, 80–90%, 90% ou mais).
- **Por exercício**: VTT, VTR e intensidade da semana escolhida, com a variação e o alerta de 25%.
- **1RM estimado por bloco** (aba prs).

A tela de dados do aluno tem três abas: **Números**, **Anamnese e feedback** e **PDFs**.

**Anamnese e feedback.** Anexe a planilha de respostas da anamnese do Forms (o programa lê todas as abas
"Respostas ao formulário", acha o aluno pelo nome e não guarda contatos). Anamnese e feedback têm o mesmo botão **Importar planilha**. No feedback, cada resposta do Forms vira o feedback da semana em que foi enviada (importar de novo não duplica). Ao importar, a Central marca só o que pede ação: **dor ou desconforto**, **adesão** baixa, **objetivo** (“não está
alinhado”), **sugestão** e **recuperação** ruim. O feedback marcado abre sozinho com esses pontos em destaque; o botão
**Visto** tira o aviso do painel (as respostas completas ficam em “Respostas”).

**O que entra nos PDFs é decidido pelo programa** (você não precisa escrever nada), no máximo 4 itens por PDF:
- **Pré · Pensado para você** (anamnese), nesta ordem: motivação (com o 1RM do bloco dos exercícios que o aluno citou),
  dor e lesões (começo com carga conservadora e técnica conferida por vídeo) e disponibilidade (dias de treino do bloco).
- **Pós · O que você pediu, o que mudou**: motivação (com a evolução do 1RM dos exercícios citados), dor e dificuldade
  (quando o feedback mais recente diz que passaram).
Um item só entra quando a segunda parte é um fato da planilha, da metodologia ou do feedback mais recente; o resto fica
de fora. Medicação, diagnósticos, peso, altura, nascimento, profissão, fumo, álcool e contatos nunca entram. Cada texto
fica em no máximo 2 linhas (se passar, o texto do aluno é encurtado ou o item sai) e a última linha nunca fica com uma
palavra só. Os itens usados ficam registrados no histórico do aluno.

**PDF para o aluno** (faixa cinza no topo da tela de dados do aluno):
- **Planejamento (pré)**: uma página só, sem capa, "Seu planejamento": perfil, "pensado para você", o ciclo, principais
  exercícios do bloco (nome e 1RM estimado) e como vamos acompanhar. Individualizado: o ciclo segue o plano contratado
  (mensal = só o bloco; trimestral = os 3 blocos; sem plano = só os blocos da planilha) e "Como vamos acompanhar" só
  mostra Anote, Grave e Teste (semana do AMRAP) se o bloco tiver. Arquivo `MariaSilva_Bloco02_Planejamento.pdf`;
  gerar de novo o mesmo bloco substitui o anterior.
- **Resultados (pós)**, capa igual à da ficha + 1 página, em linguagem do aluno ("semana 7", não "S07"): peso levantado, semana do ciclo, intensidade, mais força, "o que você pediu, o que mudou",
  gráficos semana a semana e evolução do 1RM por bloco, em linguagem simples.
Os PDFs ficam em `dados\alunos\<aluno>\pdfs\` e na aba "PDFs". Se algo não couber, a seção menos
importante sai e o programa avisa.

A Central lê os dois layouts da planilha matriz: o atual (cada semana com a própria coluna de exercício) e o anterior
(exercício só na coluna B).

Os números do planejado são calculados exatamente como na aba MACRO: VTT = séries × reps × kg; VTR = séries × reps;
intensidade = média do %1RM das linhas com %1RM. Linhas com faixa ("8 - 12"), AMRAP ou tempo **somam zero** em VTT e
VTR (como na planilha). A planilha nunca é alterada.

---

## Onde ficam as coisas

Tudo dentro da pasta do programa, em `dados\`:

| O quê | Onde |
|---|---|
| Cadastro, plano, datas, histórico | `dados\alunos\<aluno>\aluno.json` |
| Todas as planilhas recebidas (originais, com data) e as cópias ajustadas | `dados\alunos\<aluno>\planilhas\` |
| PDFs de entrega, um por bloco (MariaSilva_Bloco02.pdf; refazer o bloco substitui o anterior) | `dados\alunos\<aluno>\pdfs\` |
| Leitura de cada planilha (relatório de revisão, ajustes) | `dados\alunos\<aluno>\trabalho\` |
| Tabela de planos e valores | `dados\planos.json` |
| Anamnese e feedbacks | `dados\alunos\<aluno>\anamnese.json`, `feedbacks.json` |
| Arquivos anexados (planilha da anamnese, prints…) | `dados\alunos\<aluno>\anexos\` |
| Alunos excluídos | `dados\lixeira\` |

**Backup:** uma cópia de `dados\` por dia, ao abrir o programa, em `backups\` (guarda as 30 últimas).
Em Configurações, "Exportar backup" salva um .zip em `Documentos\Central da Consultoria - Backups`.
Guarde cópias fora do computador (pendrive, Google Drive).

---

## Se algo der errado

- **O ícone não abre nada:** veja `dados\central.log`. Rodar o `INSTALAR.bat` de novo não apaga dados.
- **"A conferência não roda" / PDF não liberado:** Configurações → Conferir instalação.
- **A janela fechou e o programa continua?** Ele se encerra sozinho uns 40 segundos depois de fechar a janela.

---

## Para desenvolver (VS Code / Claude Code)

```
Central.pyw            inicializador sem console (servidor local + janela do Edge em modo app)
INSTALAR.bat           instalação de um clique (chama instalar.ps1)
app/
├─ servidor.py         rotas da interface (Flask, só em 127.0.0.1:8765), inclusive /api/semana ("Esta semana")
├─ planilha.py         recebimento automático, identificação do aluno, datas, revisão, geração do PDF
├─ dados.py            aba DADOS: todas as semanas (só o planejado), VTT/VTR/%1RM como a MACRO, variações, alertas
├─ relatorios.py       PDFs para o aluno: planejamento (pré) e resultados (pós)
├─ individual.py       anamnese, feedbacks semanais e itens pessoais dos PDFs
├─ anamnese.py         leitura da planilha de respostas do Forms (todas as abas "Respostas")
├─ planos.py          plano contratado, vencimento, renovação e resumo do mês
├─ ajuste.py          cópia ajustada da planilha recebida: aquecimento (AMRAP intocado)
├─ xlsx_celulas.py    grava células direto no XML do .xlsx (fórmulas, macro e formatação intactas)
├─ formularios.py      perguntas da anamnese e do feedback → itens dos PDFs pré e pós e triagem do feedback
├─ armazenamento.py    alunos, gravação segura, lixeira
├─ backup.py           backup diário, exportar, restaurar
├─ config.py           caminhos, Poppler, ambiente do motor
└─ web/                interface (index.html, app.css, app.js, dados.js — sem etapa de build)
testes/montar_planilha_12s.py   planilha FICTÍCIA de 12 semanas para testar a aba Dados
testes/popular_teste.py         envia esse aluno fictício para a Central (servidor rodando)
testes/montar_formularios_teste.py  anamnese e feedback FICTÍCIOS no formato do Forms, para testar a importação
testes/testar_ajuste.py         teste do ajuste automático (aluno fictício, na matriz em branco testes/matriz_3x.xlsx)
motor/consultoria-planilha/   cópia INTACTA da skill (template travado v1.11)
icone/                 ícone de gorila (.ico e .png)
```

Rodar sem o atalho: `.venv\Scripts\python Central.pyw` (ou só o servidor:
`.venv\Scripts\python -c "from app.servidor import app; app.run(port=8765)"` e abrir http://127.0.0.1:8765).

**Atualizar o motor quando a skill mudar:** substitua a pasta `motor\consultoria-planilha` pela versão nova da
skill e rode `.venv\Scripts\python motor\consultoria-planilha\scripts\verificar_template.py`.
