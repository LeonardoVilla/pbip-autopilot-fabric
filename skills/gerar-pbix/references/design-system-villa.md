# Design System — Painéis VILLA (padrão Turnover/RH)

Padrões visuais extraídos de um painel de produção validado (`Painel-RM-Turnover`),
aprovado pelo usuário. Use como base ao gerar painéis VILLA para manter consistência.

## Paleta de cores

| Uso | Hex |
|-----|-----|
| Header (faixa superior) | `#15314F` (azul marinho) |
| Faixa de slicers | `#F4F6FA` (cinza muito claro) |
| Fundo da página | `#EEF1F6` (cinza-azulado) |
| Fundo de card/tabela/gráfico | `#FFFFFF` |
| Borda de card/tabela | `#E5E9F0` (cinza clara) |
| Cabeçalho de tabela | `#15314F` fundo, `#FFFFFF` texto |
| Número KPI / texto principal | `#15314F` |

### Cores de acento por KPI (barra lateral + label)

Cada card tem uma barra vertical de 5px de largura à esquerda, na cor do acento.
O label do card usa a mesma cor; o número usa sempre `#15314F`.

| KPI | Acento |
|-----|--------|
| Admitidos | `#0E7C86` (petróleo) |
| Demitidos | `#C0392B` (vermelho) |
| Transferidos | `#E67E22` (laranja) |
| Promoções | `#1E8449` (verde) |
| Colaboradores Ativos | `#2471A3` (azul) |
| Turnover % | `#7D3C98` (roxo) |

## Tipografia (valores exatos, validados em produção)

| Elemento | Fonte | Tamanho | Peso | Cor |
|----------|-------|---------|------|-----|
| Título do header (página) | Segoe UI | **18pt** | Bold | `#FFFFFF` |
| Número do KPI (card) | Segoe UI Semibold | **26D** (`fontSize`) | Semibold | `#15314F` |
| Label do KPI (textbox acima do card) | Segoe UI | **9pt** | Bold | cor do acento |
| Título de tabela/gráfico/donut (`vcObjects.title`) | Segoe UI | **12D** | — | `#15314F` |
| Cabeçalho de tabela (`columnHeaders`) | Segoe UI | **9D** | — | `#FFFFFF` sobre `#15314F` |
| Valores de tabela (`values`) | Segoe UI | **9D** | — | padrão |
| Header do slicer | Segoe UI | **8D** (`textSize`) | — | cor do tema |
| Itens do slicer | Segoe UI | **8D** (`textSize`) | — | cor do tema |

> Nota de unidade: propriedades de visual (`fontSize` em `objects`) usam o sufixo `D` (double),
> ex. `"26D"`. Texto de `textbox` usa string com unidade explícita, ex. `"18pt"`, `"9pt"`.

## Layout (canvas 1280×720) — dimensões exatas

| Elemento | X | Y | W | H |
|----------|---|---|---|---|
| Header | 0 | 0 | 1280 | 58 |
| Textbox do título (dentro do header) | 24 | 12 | **820** | **40** |
| Logo (no header, à direita) | ~1150–1166 | 12 | ~100–115 | ~40–42 |
| Faixa de slicers | 0 | 58 | 1280 | 52 |
| Slicer individual (faixa de 6, via `grid()`) | 14+ | 64 | ~202 (uniforme) | **42** |
| Barra de acento do card | x_card | 122 | 5 | 92 |
| Card KPI | x_card | 122 | ~200–240 | 92 |
| Textbox do label do KPI (acima do número) | x_card+12 | 130–132 | **184** (ou w-16) | **30** |
| Ícone do KPI | x_card+6 a +12 | ~152 | ~42–61 | ~40–53 |
| Tabela (2 lado a lado) | 14 / 646 | ~230 | ~410–620 | 258 |
| Gráfico/donut (rodapé) | 14 | 500 | 1252 | 206 |

- **Espaçamento entre KPIs**: ~210px de passo com 6 cards (gap 10px).
- **Cards**: fundo branco, borda `#E5E9F0`, cantos arredondados (radius 8D), sem título interno (`title.show: false`).
- **Barra de acento**: shape de 5px à esquerda, mesma altura do card, z acima do card (z+5).
- **Textbox do label do KPI**: altura mínima **30px** — 22px corta o texto em fontes 9pt bold.
- **Textbox do título da página**: ~820×40px, encostado à esquerda (x=24), fonte 18pt bold branco.

## Ícones dos KPIs

Estilo: ilustração colorida flat (Flaticon-like), círculo/cena preenchida.
Disponíveis em `assets/villa-turnover/`:

| Arquivo | Uso |
|---------|-----|
| `new-employee.png` | Admitidos |
| `resignation.png` | Demitidos |
| `turnover.png` | Transferidos / Turnover |
| `teamwork.png` | Colaboradores Ativos |
| `business.png` | Promoções / genérico |
| `logo-white-villa.png` | Logo VILLA (header, versão branca) |

Ícone posicionado dentro do card, abaixo do label, ~61×53px.

### De onde tirar novos ícones

**Recomendado: Iconify** (`api.iconify.design`) — use `iconify_buscar()` + `iconify_png()`.
- API pública com busca, 200k+ ícones, licença livre (MIT/Apache na maioria — sem atribuição).
- Coleções coloridas no estilo dos cards: `flat-color-icons:`, `twemoji:`, `fxemoji:`.
- Entrega SVG; converte para PNG com `resvg-py` (`pip install resvg-py`).
- `icones.js.org` é a interface de busca do próprio Iconify (mesma fonte).

**Alternativa: Flaticon** — use `baixar_flaticon()` com a URL/ID que o usuário fornecer.
- A página bloqueia scraping; o CDN de PNG (`cdn-icons-png.flaticon.com`) responde.
- Não dá para buscar (o usuário precisa navegar e colar a URL).
- Exige atribuição ao autor (licença grátis) — responsabilidade do usuário.

Fluxo típico: buscar/baixar o ícone → `register_image()` → `image_vc()` ou `kpi_card_villa(icon_logical=...)` → `pack_pbix_with_images()`.

## Tabelas (tableEx) — `table_vc()`

- Cabeçalho: fundo `#15314F`, texto `#FFFFFF`, `fontSize: 9D`.
- Valores: `fontSize: 9D`.
- `grid.gridVertical: false`, `grid.rowPadding: 2D`.
- Borda `#E5E9F0`, `radius: 8D` (sem `width` explícito). Fundo branco.
- Título (`vcObjects.title`) `fontSize: 12D` cor `#15314F`.
- 1ª coluna = dimensão (ex: SiglaUnidade, SECAO), demais = medidas.
- Linha de Total no rodapé (padrão do tableEx quando há medidas).

## Gráfico (clusteredColumnChart) — `grouped_bar_vc()`

- Colunas agrupadas (`clusteredColumnChart`), legenda `position: 'Top'`, `showTitle` não setado (padrão).
- `categoryAxis.showAxisTitle: false`. `valueAxis.show: false` **e** `showAxisTitle: false` (eixo Y totalmente oculto — os rótulos de dados substituem a escala).
- `labels.show: true` (rótulos de dados visíveis sobre as colunas).
- Séries de movimentação (exemplo): Admitidos/Demitidos/Transferidos, uma medida por série.
- Fundo branco, borda `#E5E9F0` radius 8D, título (`vcObjects.title`) `fontSize: 12D` cor `#15314F`.

## Gráfico (barChart) — `bar_vc()`

- Mesmo padrão de eixo oculto: `valueAxis.show: false` + `showAxisTitle: false`, `categoryAxis.showAxisTitle: false`.
- Fundo branco, borda `#E5E9F0` radius 8D, título `fontSize: 12D` cor `#15314F`.

## Donut (donutChart) — `donut_vc()`

- Legenda embaixo e centralizada: `legend.position: 'BottomCenter'`, `legend.showTitle: false`.
- Rótulos de dados: `labels.labelStyle: 'Data value, percent of total'` (mostra valor absoluto + %, não só %).
- Fundo branco, borda `#E5E9F0` radius 8D, título `fontSize: 12D` cor `#15314F`.

## Slicers

- Modo Dropdown.
- Header com `textSize: 8D`, cor do tema (`ThemeDataColor` ColorId 0), texto = rótulo curto
  (use o parâmetro `label` — ex: "Tipo de Contrato" para a coluna `CLASSIFICACAO_CONTRATO`,
  senão o nome longo trunca).
- Itens `textSize: 8D`, cor do tema. Fundo transparente (herda a faixa `#F4F6FA`),
  padding 0, borda 1D, `titleWrap: true`.
- Altura ~42px (menor corta o dropdown).
- **Faixa distribuída e alinhada**: gere as posições com `grid(N, 1, area_x=14, area_y=64,
  area_w=1252, area_h=42, gap=8)` — todos os slicers ficam com largura uniforme, sem colar nas
  bordas, e alinhados (x inicial 14, final 1266) com os gráficos/tabelas abaixo.
- 6 slicers típicos: Ano, Mês, Unidade, Seção, Tipo de Contrato, Vínculo.
