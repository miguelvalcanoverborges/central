# Especificação do Template Mestre v1.12 — FORÇA & INTELIGÊNCIA

Aprovado por Miguel Valcanover a partir de uma entrega real de Bloco 01. Referência de teste atual: exemplo fictício (`referencia/REFERENCIA_v1.12_exemplo.pdf`). **Travado.** v1.1: página "Próximos passos" removida a pedido de Miguel (a v1.0 tinha 5 páginas).

## Identidade
- **Formato:** A4 retrato. Cor: preto #000 e branco; apoio em cinzas (#f4f4f1 cartões, #8a8a86 rótulos, #e6e6e2 linhas). Sem cor de destaque.
- **Tipografia:** títulos *Krona One* (largos, caixa alta, brilho nas páginas escuras); corpo *Exo 2* (300–800). Fontes embutidas no PDF.
- **Marca:** gorila branco (capa, cabeçalho preto, fechamento); halftone decorativo no canto; chevrons pontilhados (funil) no fechamento.

## Páginas
1. **Capa (escura):** gorila · FORÇA & INTELIGÊNCIA · PLANO DE TREINAMENTO · **BLOCO NN** (brilho) · nome · data de início (só a data) · rodapé: Miguel Valcanover · Treinador / @miguelvalcanover · (55) 99105-8153.
2. **Seu perfil (clara):** card (Nome, Objetivo, Treinos "N× por semana" + dias, Bloco "NN · 4 semanas / dd/mm/aaaa a dd/mm/aaaa") [+ `perfil_extra`] · **Seus números** (até 4 cartões pretos: "1RM estimado" com "N reps × X kg", ou "PR" com data) + nota Brzycki (só se houver estimativa) · **Como ler a sua ficha**: [caixa "Observação" se houver] + legenda (a frase "Faça os exercícios na ordem proposta" foi removida na v1.4) (Séries, Reps, [Carga], [%1RM], [Anotar], [PSE], [Aquecimento], [Principal], [Gravar], [Biset], [AMRAP]; entre colchetes = só se aparece na ficha do bloco).
3. **Semana NN (clara):** título "SEMANA NN", subtítulo "BLOCO NN · dd/mm" (data de início da semana, v1.11). AQC (cabeçalho cinza-escuro, só na 1ª semana) e treinos (cabeçalho preto: TREINO NN · DIA · SEMANA NN). Colunas: nº de ordem · Exercício · Séries · Reps · Carga · %1RM (com barra) · Obs (etiquetas). Aquecimento em cinza; Biset só com fundo cinza claro e etiqueta (sem barra lateral, v1.2); link na OBS = botão "Ver vídeo" (v1.3); página de perfil sem subtítulo e com caixa "Observação" quando houver (v1.3). Empacotamento: preenche a página em ordem; semana nova = página nova (referência: [AQC + T01] / [T02 + T03]).
- Rodapé das páginas claras: "Nome · Bloco NN · Semana NN" | "Miguel Valcanover · Treinador · @miguelvalcanover" | nº da página.

## Textos fixos (aprovados)
Legenda, nota Brzycki estão no código (`template_mestre.py`) exatamente como aprovados.

## O que NÃO existe no layout (exige autorização para incluir)
Seção de feedback/anamnese longa, gráficos de evolução, VTT/VTR, múltiplos PRs por exercício, fotos.

## v1.8 (3/out/2026, autorizado por Miguel)
- AQC: coluna CARGA (condicional) entre "REPS / TEMPO" e a coluna de vídeo/nota, mostrada apenas se algum item do AQC tiver carga; valor com unidade "kg" pequena, "—" nos itens sem carga.
- Células numéricas das tabelas (`td.n`): `white-space:nowrap` (faixas como "15 - 20" não quebram).

## Renderização (4/out/2026)
- O PDF é gerado com a suavização de fonte fixa (`--font-render-hinting=none`, em `scripts/gerar_pdf.py`). Sem isso, conforme a máquina, os textos da legenda quebravam em 3 linhas com palavra solta. O design (template travado) não mudou.

## v1.9 (4/out/2026, autorizado por Miguel)
- Coluna SÉRIES aceita faixa, exibida como "3 - 4" (espaço dos dois lados do hífen). Sem outra mudança visual.
- Rótulo interno de versão corrigido; PDF de referência regenerado (legenda em 2 linhas, sem palavra solta).

## v1.10 (5/out/2026, autorizado por Miguel)
- Etiqueta **Anotar** (pílula preta, sem o ponto de gravação) em toda linha com faixa de repetições ou AMRAP, com ou sem carga (AMRAP fica com Gravar + Anotar).
- Legenda: item ANOTAR ("Anote as repetições e a carga que você usou em cada série, para eu ajustar a sua progressão."), no lugar da PSE, só quando há faixa de reps ou AMRAP. PSE desligada por padrão.
- OBS: etiquetas dentro de um contêiner que quebra em 2 linhas quando não cabem (a coluna não alarga); nota + etiqueta automática = pílulas + nota em itálico. Linhas de uma linha ficam idênticas à v1.9.

## v1.11 (5/out/2026, autorizado por Miguel)
- SEU PERFIL: cartão BLOCO mostra início e fim do bloco ("28/09/2026 a 25/10/2026"; fim = início + 27 dias).
- Páginas das semanas: subtítulo "BLOCO NN · dd/mm" com a data de início da semana (início do bloco + 7 dias por semana).

## v1.12 (9/out/2026, autorizado por Miguel)
- Legenda "Como ler a sua ficha": só explica o que aparece na ficha do bloco. SÉRIES e REPS sempre; CARGA e %1RM só se alguma linha tem valor; Aquecimento, Principal, Gravar, Biset e Anotar só se a etiqueta aparece em alguma OBS; AMRAP só se há AMRAP. Sem outra mudança visual.
