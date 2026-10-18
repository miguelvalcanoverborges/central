# Especificação do Template Mestre v1.13 — FORÇA & INTELIGÊNCIA

Aprovado por Miguel Valcanover a partir de uma entrega real de Bloco 01. Referência de teste atual: exemplo fictício (`referencia/REFERENCIA_v1.13_exemplo.pdf`). **Travado.** v1.1: página "Próximos passos" removida a pedido de Miguel (a v1.0 tinha 5 páginas).

## Identidade
- **Formato:** A4 retrato. Cor: preto #000 e branco; apoio em cinzas (#f4f4f1 cartões, #8a8a86 rótulos, #e6e6e2 linhas). Sem cor de destaque.
- **Tipografia:** títulos *Krona One* (largos, caixa alta, brilho nas páginas escuras); corpo *Exo 2* (300–800). Fontes embutidas no PDF.
- **Marca:** gorila branco (capa, cabeçalho preto, fechamento); halftone decorativo no canto; chevrons pontilhados (funil) no fechamento.

## Páginas
1. **Capa (escura):** gorila · FORÇA & INTELIGÊNCIA · PLANO DE TREINAMENTO · **BLOCO NN** (brilho) · nome · data de início (só a data) · rodapé: Miguel Valcanover · Treinador / @miguelvalcanover · (55) 99105-8153.
2. ~~Seu perfil~~: removida na v1.15 (Miguel, 18/out/2026). A legenda "Como ler a sua ficha" está na 2ª página do PDF "Seu planejamento" da Central.
2. **Semana NN (clara, a partir da página 02):** a 1ª abre com a caixa "Observação" quando houver (v1.15). Título "SEMANA NN", subtítulo "BLOCO NN · dd/mm" (data de início da semana, v1.11). AQC (cabeçalho cinza-escuro, só na 1ª semana) e treinos (cabeçalho preto: TREINO NN · DIA · SEMANA NN). Colunas: nº de ordem · Exercício · Séries · Reps · Carga · %1RM (com barra) · Obs (etiquetas). Aquecimento em sub-linha cinza sob a série principal (v1.13); Biset só com fundo cinza claro e etiqueta (sem barra lateral, v1.2); link na OBS = botão "Ver vídeo" (v1.3); página de perfil sem subtítulo e com caixa "Observação" quando houver (v1.3). Empacotamento: preenche a página em ordem; semana nova = página nova (referência: [AQC + T01] / [T02 + T03]).
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

## v1.13 (12/out/2026, autorizado por Miguel)
- Aquecimento como sub-linha da série principal: os degraus de aquecimento seguidos do mesmo exercício saem da tabela e aparecem em cinza, logo abaixo do nome da principal ("Aquecimento 55 kg × 3 · 59 kg × 2"; mais de uma série: "3×5 com 60 kg"). O %1RM dos degraus não aparece. Aquecimento sem a principal do mesmo exercício logo depois continua como linha própria, com a etiqueta. A sub-linha não aumenta a altura da linha: a semana volta a caber numa página (ficha de 4 semanas com o aquecimento da Central: 12 → 6 páginas). Legenda: "Séries leves de preparo: 55 kg × 3 = 1 série de 3 reps com 55 kg." O verificador confere cada degrau na sub-linha.

## v1.15 (18/out/2026, autorizado por Miguel)
- A página "Seu perfil / Seus números / Como ler a sua ficha" saiu da ficha: capa + semanas. A observação geral (A9) abre a 1ª página de treino; a paginação reserva o espaço dela. A legenda, com os mesmos textos, está na 2ª página do PDF "Seu planejamento" (Central).
