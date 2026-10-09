---
name: "consultoria-planilha"
description: "Gera o PDF de entrega personalizado da consultoria de Miguel Valcanover (FORÇA & INTELIGÊNCIA) a partir da planilha de prescrição de um aluno (.xlsx com abas \"aluno NN\", \"bloco NN\", \"prs\", \"macro\"), usando o TEMPLATE MESTRE aprovado (identidade visual travada). Use SEMPRE que Miguel enviar a planilha de prescrição de um aluno, ou pedir \"entrega\", \"PDF do aluno\", \"ficha do aluno\", \"novo bloco\", \"gerar o PDF\", revisar uma prescrição antes de enviar, ou incluir PRs/feedback na revisão de um bloco, mesmo que ele não diga \"skill\". Extrai os dados, revisa a prescrição sem alterá-la, aplica o template e verifica o PDF contra a planilha. Nunca redesenha o layout. Não é para a anamnese de aluno novo (Google Forms): isso é a skill consultoria-anamnese."
---

# Consultoria — Prescrição e Entrega (template mestre v1.12)

Transforma a planilha de prescrição de **um aluno / um bloco** em um **PDF profissional para o aluno**, sempre no mesmo layout aprovado por Miguel, e entrega a Miguel um **relatório de revisão** separado (nunca vai ao aluno).

## Regras inegociáveis

1. **O design é fixo.** Capa, perfil, tabelas, legenda, fontes, cores, textos fixos e espaçamentos estão no template mestre (`scripts/template_mestre.py` + `.css`, protegidos por `TEMPLATE_LOCK.json`). Não redesenhar, não "melhorar", não mudar nem uma margem. Se algo precisar mudar, **proponha a Miguel** e espere autorização (ver "Alterando o template").
2. **A prescrição é de Miguel.** O PDF reproduz exatamente séries, reps, cargas, %1RM, exercícios, observações e AQC da planilha. Nunca alterar silenciosamente. Inconsistência → sinalizar a Miguel, não corrigir.
3. **Nunca inventar dados** (cargas, PRs, PSE, velocidade, VTT/VTR, histórico, anamnese, feedback). Lacuna → dizer o que falta. Informação mais recente prevalece quando houver versões diferentes.
4. **Claude revisa e sugere; Miguel decide.** Toda sugestão de prescrição = PROPOSTA → JUSTIFICATIVA → EVIDÊNCIA CIENTÍFICA → LIMITAÇÕES, apresentada a Miguel **antes** de gerar. Não inventar referências; se não puder verificar a literatura, dizer isso. O PDF final traz **apenas a versão aprovada por Miguel**.
5. **PR só com evidência.** A aba `prs` guarda séries de referência → mostradas como **"1RM estimado"** (Brzycki), nunca como PR. PR real só entra via `contexto.json` com `fonte`.
6. **Anamnese e feedback NÃO vão no PDF do aluno** (decisão de Miguel): não incluir, não pedir, não resumir no PDF. Servem só para a análise e para o relatório de revisão interno, se Miguel enviar.
7. **Posicionamento:** FORÇA & INTELIGÊNCIA. Sem promessas, sem linguagem de guru, sem enquadrar como estética/emagrecimento. O objetivo do aluno é usado EXATAMENTE como está na planilha (sem alerta, sem reescrever).
8. **Nunca usar nome nem planilha de aluno real** em template, exemplo ou teste (decisão de Miguel, 4/out/2026). Testes usam `exemplos/exemplo.xlsx` (aluno fictício).

## Fluxo (siga na ordem)

**0. (Opcional, 10 s) Sanidade do template:** `python scripts/verificar_template.py` → deve imprimir `PASSOU — design idêntico ao aprovado`. A comparação é pixel a pixel: se falhar com a trava OK, olhe as páginas lado a lado antes de concluir que o design mudou (diferença de renderização entre máquinas), e avise Miguel.

**1. Receber materiais.** Planilha do aluno (.xlsx). Feedback/PRs podem vir como arquivos, Drive ou texto colado — leia os reais. Se a planilha for só o layout vazio (sem prescrição), avise Miguel.

**2. Extrair e revisar:**
```bash
python scripts/extrair_dados.py <planilha.xlsx> --saida <pasta> [--bloco N] [--numeros "Supino,Terra,..."]
```
Gera `dados.json` + `relatorio_revisao.md`. Leia o relatório inteiro.
- `--bloco`: padrão é o último bloco com prescrição.
- **PSE: nenhum aluno usa por enquanto (Miguel, 5/out/2026).** Não perguntar e não passar `--usa-pse`; a ficha sai sem PSE. O parâmetro continua existindo só para quando Miguel disser que um aluno passou a usar.
- `--numeros`: escolhe até 4 exercícios para "Seus números" (Miguel decide quais), quando a aba `prs` tem mais de 4.
- Se o extrator parar com **"séries escritas como texto"** (ex.: "3x"), não escolha um número: pergunte a Miguel o valor e peça para corrigir a planilha. Faixa ("3-4") não para: vira "3 - 4".

**3. Revisão técnica → Miguel.** Antes, leia `referencia/METODOLOGIA.md` (fases acumulação, transformação e realização; faixas de %1RM, aquecimento, GRAVAR/ANOTAR, progressão, PSE, VTT/VTR por fase) e confira o bloco contra ela: fase do bloco, faixa de %1RM e aquecimento. A periodização é de Miguel: aponte, não reescreva. Apresente separado: **O QUE MIGUEL PRESCREVEU / O QUE O CLAUDE OBSERVOU / O QUE SUGERE / POR QUÊ** (+ evidência/limitações). Raciocínio por aluno: o que foi planejado → o que aconteceu → como respondeu → manter/ajustar/reduzir/progredir. Estagnação: investigar contexto antes de trocar treino. Nenhuma métrica isolada é verdade. **Aguardar aprovação** antes de gerar o PDF final se houve sugestão.

**4. Contexto (opcional) → `contexto.json`.** Só para PR real (`prs`: `{exercicio, kg, data, fonte}`, todos obrigatórios; máx. 4 cartões no total). Formato em `referencia/contexto_exemplo.json`. O campo `perfil_extra` existe no template, mas só é usado se Miguel pedir.

**5. Gerar o PDF:**
```bash
python scripts/gerar_pdf.py <pasta>/dados.json [--contexto contexto.json] --saida <pasta de saída>/Entrega_<Nome>_Bloco<NN>.pdf
```
Faz sozinho: confere a trava do template → valida contexto e nº de cartões → renderiza com configuração fixa de fonte → **recusa** PDF que encoste no rodapé (folga < 4 mm, medida de verdade) → roda `verificar_pdf.py` (PDF × planilha: exercícios, séries, reps, cargas, %1RM, AQC, 1RM, nome, objetivo, datas, botões de vídeo, etiquetas Gravar e Anotar). Código de saída ≠ 0 = **não entregar**: ler a mensagem e corrigir a causa. Nunca editar o template para "fazer caber" e nunca cortar ou reescrever a prescrição/observação de Miguel; se faltar espaço, a mensagem diz o que perguntar a ele.

**6. Conferência visual.** Rasterize e olhe as páginas (`pdftoppm -r 60 -png`): hierarquia, nada cortado, nada sobreposto, textos corretos, legenda sem palavra solta.

**7. Entregar.** Envie o PDF a Miguel (ferramenta de envio de arquivos da sessão). Resposta curta: o que foi gerado + os **alertas do relatório que exigem decisão dele**, com `relatorio_revisao.md` como arquivo separado. Não despejar o relatório inteiro no chat.

## Estrutura do PDF

Capa · Seu perfil · semanas de treino. (A página final "Próximos passos" foi removida a pedido de Miguel na v1.1.) Detalhes visuais em `referencia/ESPECIFICACAO_TEMPLATE.md`.

- **Mais de uma semana prescrita:** cada semana começa em página nova; AQC só na primeira. Rodapé da página de perfil omite "Semana" quando há várias.
- **Treinos:** empacotamento automático (preenche a página em ordem; Treino 04 entra normalmente).
- **Seus números:** no máximo 4 cartões (1 linha). Mais que isso, o PDF aborta de propósito → `--numeros`.
- **Página de perfil:** sem subtítulo. A OBS geral da aba aluno (A9) aparece como caixa "Observação: ..." no início de "Como ler a sua ficha", exceto as linhas padrão "Faça os exercícios na ordem proposta" e "Considere kg = 20kg (barra) + peso em anilhas", que não são exibidas.
- Observação conhecida (não alterada): nos cartões de "Seus números" o texto sai "1 reps × 80 kg" quando a referência é 1 repetição.

## O que vem de onde (planilha → PDF)

| PDF | Origem |
|---|---|
| Nome, objetivo | aba `aluno NN` C2, C3 (segue referência a `aluno 01` se vazio) |
| Dias/Treinos por semana | `aluno NN` B5:F6 — só marcadores `T01`, `T02`... contam como dia de treino |
| AQC (aquecimento geral, 1ª semana) | `aluno NN` A13:E15 (link ou hiperlink em E vira "▶ Ver vídeo"; texto vira nota; D = carga) |
| Capa: Bloco e data | nº do bloco; `macro` linha 6 (B/F/J = bloco 01/02/03) |
| Semanas, treinos, exercícios, séries, reps, carga, %1RM, OBS | aba `bloco NN`: colunas lidas do cabeçalho (`colunas_semanas`). Planilhas-base atuais (out/2026): cada semana tem a própria coluna de exercício — exercício/SETS em B/C, I/J, P/Q, W/X (o exercício pode mudar de uma semana para outra). Layout anterior: exercício só em B, semanas em C, I, O, U. Treinos achados pelos títulos "TREINO NN" (coluna A); o extrator lê todas as linhas até o próximo título (linhas vazias ignoradas; não depende da fórmula de %1RM). Layout antigo: 7 exercícios por treino a cada 12 linhas. Layout novo (out/2026): 10 exercícios a cada 15 linhas. O relatório lista as linhas detectadas |
| "Seus números" | aba `prs` (bloco 01/02/03: linhas 6, 18, 30, 7 exercícios: Agachamento, Supino, Terra, Desenvolvimento, Remada, Arranco, Arremesso) → 1RM estimado = kg ÷ (1,0278 − 0,0278·reps) |

- Semana/treino sem séries+reps **não entra** no PDF (vira informação no relatório).
- %1RM exibido = valor calculado pela própria planilha (recalculado só para conferir; divergência vira alerta). Variações usam o 1RM do exercício-base por palavra-chave (ex.: "Supino inclinado" → Supino); o relatório lista essas correspondências.
- Planilhas-base: `Consultoria_2x`, `3x`, `4x` (2, 3 ou 4 treinos), mesmas abas e colunas. A fórmula de VTT/VTR da macro soma as linhas 6:15.
- Leitura dos dois layouts (exercício por semana e o anterior) autorizada por Miguel em 7/out/2026; o template não mudou.

## Regras de exibição definidas por Miguel

**Números**
- Repetições e séries sempre inteiras, sem ponto (10.0 → 10).
- Cargas fracionárias (ex.: 62,5 kg) aparecem como estão, nunca arredondadas e sem alerta (decisão de Miguel, 4/out/2026).
- **Faixas sempre com espaço dos dois lados do hífen** (regra de Miguel, 4/out/2026): séries "3-4" → "3 - 4"; reps "8-12" → "8 - 12". Vale para treinos e AQC. Série em faixa vira informação no relatório.
- Séries em outro texto (ex.: "3x") → o extrator para e pede a decisão de Miguel.
- Faixas nunca quebram em 2 linhas na tabela.

**Etiquetas da coluna OBS** — reconhecidas: `aquecimento`, `principal`, `gravar`, `biset`, `anotar` (combináveis com " - "). Qualquer outro texto aparece literal em itálico; nota de Miguel + Gravar/Anotar automático na mesma OBS → etiquetas em pílula e a nota em itálico ao lado (v1.10). Muitas etiquetas quebram em 2 linhas dentro da OBS, sem alargar a coluna (v1.10). Biset = fundo cinza claro + etiqueta, sem barra lateral (v1.2, permanente).

**Aquecimento / Principal (automático, por treino, exercícios com o MESMO nome)**
- Exercício que NÃO se repete → sem etiqueta Aquecimento/Principal.
- Se se repete: 1ª ocorrência = Aquecimento; última = Principal; intermediária com carga maior que a anterior = Aquecimento. Intermediária sem aumento de carga → Aquecimento + alerta. Linha com a **mesma carga da última** (ex.: 2×3 + 1×AMRAP em duas linhas) também é **Principal** (Miguel, 7/out/2026).
- Etiquetas Aquecimento/Principal da planilha são substituídas por essa regra; Gravar, Biset, Anotar, notas e links são preservados.
- Variação "- sem step" conta como o mesmo exercício (ex.: "Levantamento terra romeno" e "Levantamento terra romeno - sem step"). Outros nomes diferentes NÃO contam → sinalizar a Miguel quando parecer ser o mesmo.

**GRAVAR automático**
- Toda série com %1RM exibido de 80% OU MAIS (o número arredondado que o aluno vê) leva Gravar, exceto linha de aquecimento (Miguel, 7/out/2026: aquecimento não ganha Gravar automático; se ele escrever Gravar na OBS, fica). Série sem %1RM calculado não recebe a etiqueta automática.
- Toda série AMRAP leva Gravar e também Anotar.
- A lista do que foi adicionado vai no relatório de revisão.

**ANOTAR automático (regra de Miguel, 5/out/2026)**
- Toda linha com **faixa de repetições** ("3 - 5", "8 - 12", qualquer faixa) **ou AMRAP** leva a etiqueta **Anotar** na OBS (pílula preta, como Gravar, sem o ponto de gravação), **com ou sem carga** prescrita. AMRAP fica com Gravar + Anotar (o aluno anota quantas repetições fez).
- Faixa de **séries** ("3 - 4") sozinha não leva Anotar.
- Sempre que houver Anotar (faixa de reps ou AMRAP), a legenda ganha o item ANOTAR, no lugar onde ficava a PSE: "Anote as repetições e a carga que você usou em cada série, para eu ajustar a sua progressão."
- A lista do que foi adicionado vai no relatório de revisão; o verificador confere se toda faixa de reps e todo AMRAP têm Anotar e se a legenda tem o item.

**AMRAP (regra de 4/out/2026)**
- AMRAP aparece só na coluna REPS; não existe etiqueta AMRAP na OBS (se a planilha tiver "amrap" na OBS, sai da OBS).
- REPS vazia + AMRAP na OBS → REPS mostra "AMRAP" (alerta no relatório).
- REPS numérica + AMRAP na OBS → REPS mostra "N + AMRAP" (alerta para Miguel confirmar).
- A legenda ganha o item AMRAP (explica a coluna REPS). VTT/VTR da macro não calculam AMRAP nem faixas de reps (o relatório avisa).

**Links de vídeo (SEMPRE)**
- Todo link vira o botão "▶ Ver vídeo", venha como: (a) URL escrita na OBS; (b) hiperlink de célula na OBS da aba `bloco` (texto visível = título do vídeo); (c) hiperlink de célula na aba `aluno NN`, que espelha o bloco (o extrator liga a linha ao exercício pela fórmula `='bloco NN'!$B$linha` e à semana pelo rótulo "SEMANA NN"); (d) hiperlink na OBS do AQC.
- O título do vídeo NUNCA aparece como texto no PDF. Conferir: nº de botões no PDF = nº de links na planilha (ler `cell.hyperlink`, não só o valor). O verificador faz isso.

**AQC**
- Mostra a carga sempre que houver: a coluna CARGA entra só se algum item tiver kg; item sem carga mostra "—". Não gerar alerta sobre isso.
- Item sem séries mostra "—" (vira informação no relatório).

**Aba aluno — dias**
- Só `T01`, `T02`... são dias de treino. "JJ" = jiu-jitsu (não é treino; não conta nos "treinos por semana"). Outros marcadores viram alerta.

**Datas e objetivo**
- Data de início: sempre a original da planilha (não alertar se cair fora dos dias de treino).
- Objetivo: texto exatamente como na planilha.

**Legenda "Como ler a sua ficha" (v1.7)**
- Só explica, SEM números nos textos (nada de "8 - 12", "20 kg").
- Cada item fecha em duas linhas, com a 2ª bem preenchida e nunca uma palavra solta. Não reescrever sem autorização; se mudar um texto, medir de novo e re-travar.
- A legenda só explica o que aparece na ficha do bloco (v1.12, Miguel 9/out/2026): SÉRIES e REPS sempre; CARGA e %1RM só se alguma linha tem valor; Aquecimento, Principal, Gravar, Biset e Anotar só se a etiqueta aparece em alguma OBS; AMRAP só se há AMRAP.
- ANOTAR entra na legenda só se alguma linha tem faixa de repetições ou AMRAP (v1.10, no lugar da PSE). PSE fica fora: nenhum aluno usa por enquanto.
- A quebra de linha depende da renderização de fonte: o gerador fixa essa configuração (`CHROMIUM_ARGS` em `gerar_pdf.py`). Não remover.

## Alterando o template (SÓ com autorização explícita de Miguel)

1. Registrar o pedido e o motivo.
2. Editar `scripts/template_mestre.py/.css`.
3. Mostrar o resultado a Miguel e obter o OK.
4. Re-travar: `python scripts/travar_template.py --versao 1.10 --autorizado-por "Miguel Valcanover" --motivo "..."` (próxima versão depois da atual).
5. Gerar o novo PDF de referência `referencia/REFERENCIA_v<versão>_exemplo.pdf` (sempre a partir de `exemplos/exemplo.xlsx`; `verificar_template.py` usa automaticamente o da versão travada), remover o da versão anterior e atualizar `referencia/ESPECIFICACAO_TEMPLATE.md`. `verificar_template.py` deve voltar a PASSAR.

Sem re-travar, `gerar_pdf.py` aborta de propósito.

## Pendências conhecidas (decisões abertas com Miguel)

- Sem a página final, as orientações de uso (registrar treino, enviar vídeos, feedback semanal, atualização do bloco) não estão no PDF; se Miguel quiser que cheguem ao aluno, será por mensagem ou por nova versão do layout.
- Aba `prs` dos blocos 02 e 03: linhas 18 e 30 confirmadas no layout novo; a conferência automática de %1RM acusa se a planilha usar outra referência. Validar com a primeira planilha real de bloco 02+.
- Planilhas salvas sem valores calculados (ex.: gravadas por script) geram muitos alertas "planilha não calculou %1RM": pedir reexportação do Google Sheets/Excel.

## Arquivos

```
consultoria-planilha/
├─ SKILL.md                      este processo
├─ TEMPLATE_LOCK.json            versão + hash do template (trava)
├─ requirements.txt              openpyxl, playwright (chromium), pillow · sistema: poppler-utils
├─ scripts/
│  ├─ extrair_dados.py           planilha → dados.json + relatorio_revisao.md
│  ├─ gerar_pdf.py               dados.json (+contexto) → PDF (valida, renderiza, verifica)
│  ├─ verificar_pdf.py           PDF × dados da planilha
│  ├─ verificar_template.py      regressão visual contra o PDF aprovado
│  ├─ travar_template.py         (re)trava o template — só com autorização
│  └─ template_mestre.py/.css    O TEMPLATE (travado)
├─ assets/                       fontes (Krona One, Exo 2 — OFL), gorila, halftone
├─ referencia/                   PDF APROVADO, ESPECIFICACAO_TEMPLATE.md, contexto_exemplo.json, METODOLOGIA.md
└─ exemplos/                     exemplo.xlsx (aluno FICTÍCIO) + montar_exemplo.py
```

## Histórico de versões do template

- v1.1: removida a página "Próximos passos".
- v1.2: removida a barra vertical preta das linhas Biset.
- v1.3: link na OBS vira botão "Ver vídeo"; perfil sem subtítulo; caixa "Observação".
- v1.4: removida a frase "Faça os exercícios na ordem proposta".
- v1.7: legenda reescrita (sem números, 2 linhas por item).
- v1.8 (3/out/2026): coluna CARGA condicional no AQC; faixa de reps sem quebra de linha.
- v1.11 (5/out/2026, autorizado por Miguel): SEU PERFIL, cartão BLOCO com início e fim do bloco ("28/09/2026 a 25/10/2026", fim = início + 27 dias); páginas das semanas com a data de início da semana no subtítulo ("BLOCO 03 · 28/09"). O verificador confere as duas.
- v1.10 (5/out/2026, autorizado por Miguel): etiqueta ANOTAR automática em toda faixa de repetições (com ou sem carga) e em todo AMRAP e item ANOTAR na legenda no lugar da PSE; PSE desligada por padrão, sem perguntar; nota + etiqueta automática na mesma OBS (pílula + nota em itálico); etiquetas quebram em 2 linhas na OBS sem alargar a coluna (linhas de 1 linha idênticas à v1.9). Referência regenerada (o exemplo tem uma faixa de reps, então mostra ANOTAR).
- v1.12 (9/out/2026, autorizado por Miguel): a legenda "Como ler a sua ficha" só explica o que aparece na ficha do bloco (CARGA e %1RM só com valor; Aquecimento, Principal, Gravar, Biset, Anotar e AMRAP só se aparecem). O verificador confere cada item. Referência regenerada (o exemplo tem todos, então continua igual).
- v1.9 (4/out/2026, autorizado por Miguel): séries em faixa exibidas ("3 - 4"); rótulo interno de versão corrigido; referência regenerada com renderização de fonte fixa (legenda em 2 linhas, sem palavra solta). Nos scripts: verificação aceita nome de exercício longo em 2 linhas e AQC sem séries e confere valores inteiros ("3" não casa com "3 - 4"); checagem de espaço da página de perfil passou a ser só medida; séries em texto param com aviso claro.
