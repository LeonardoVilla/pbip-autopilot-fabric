---
name: gerar-visuais-pbir
description: Gera o relatório de um projeto Power BI (PBIP) escrevendo os JSONs do formato PBIR - páginas, visuais (card, tabela, matriz, gauge, linha, área, combo, donut, barras, slicer), filtros e layout. Use quando o usuário pedir para criar/gerar os visuais de um painel programaticamente. Não requer Desktop aberto; opera sobre a pasta *.Report do .pbip.
argument-hint: <pasta-do-projeto.pbip> [nome-do-painel]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.6.0
---

# /gerar-visuais-pbir — Relatório como código (PBIR)

Escreve páginas e visuais como JSONs individuais no formato PBIR (Power BI
Enhanced Report Format) — formato oficial, documentado e com schema público,
projetado pela Microsoft para edição programática. Sucessora da skill
`gerar-pbix` do [PowerBI-Autopilot](https://github.com/LeonardoVilla/PowerBI-Autopilot):
**elimina** a cirurgia de ZIP (UTF-16LE, SecurityBindings, compress_type).

> **STATUS: esqueleto em validação.** O catálogo de visuais do projeto
> anterior (validado em produção no VILLA MT) ainda precisa ser portado —
> ver mapa em [docs/roadmap.md](../../docs/roadmap.md).

## Estrutura alvo

```
<Projeto>.Report/
  definition.pbir           # aponta o modelo: byPath (local) ou byConnection
  definition/
    version.json            # OBRIGATÓRIO — define quais arquivos o Desktop espera carregar
    report.json             # OBRIGATÓRIO — config global (themeCollection, filtros de relatório)
    reportExtensions.json   # opcional — medidas em nível de relatório
    bookmarks/              # opcional — 1 arquivo por bookmark + bookmarks.json (ordem/grupos)
      bookmarks.json
      <id-do-bookmark>.bookmark.json
    pages/
      pages.json            # ordem e página ativa
      <id-da-pagina>/
        page.json           # nome, dimensões, displayName, pageBinding (drillthrough/tooltip)
        visuals/
          <id-do-visual>/
            visual.json     # tipo, posição, campos, formatação
            mobile.json     # opcional — layout mobile do visual
  StaticResources/          # imagens/ícones/tema (substitui RegisteredResources)
```

`version.json` e `report.json` são **obrigatórios** (Microsoft Learn, "PBIR folder
and files") — sem eles o Desktop não reconhece a pasta `definition/` como PBIR
válido. `bookmarks/` só existe quando há pelo menos um bookmark (ex: os filtros
por clique no card, ver `docs/filtro-bookmarks-cards.md` do Painel-RM) — cada
bookmark é `<id>.bookmark.json`, nunca gerado à mão porque captura o estado
real de filtros/seleções da página (arriscado reconstruir por fora; sempre
criar pela interface do Desktop e só versionar o resultado).

**Limites do PBIR** (aplicados pelo serviço, vale ter em mente ao gerar em
massa): 1.000 páginas/relatório, 1.000 visuais/página, 1.000 arquivos de
recurso, 300MB para recursos e 300MB para os arquivos do relatório. Nenhum
painel VILLA atual chega perto, mas evitar gerar visuais duplicados por bug.

Cada `*.json` declara `$schema` (developer.microsoft.com/json-schemas/fabric/…) —
**sempre copiar o `$schema` de um arquivo gerado pelo próprio Desktop** na
mesma versão, nunca inventar a URL/versão.

## Fluxo de execução

1. **Coletar**: projeto `.pbip` alvo, páginas, visuais por página, medidas
   DAX existentes (nomes exatos).
2. **Inspecionar o modelo**: ler os TMDL de `*.SemanticModel/definition/tables/`
   para obter nomes EXATOS de tabelas/colunas/medidas (substitui a inspeção
   de XML do Excel do projeto anterior — agora a fonte da verdade é texto).
3. **Gerar referência**: criar uma página simples no Desktop, salvar, e usar
   o JSON resultante como gabarito estrutural antes de gerar em massa
   (mesma filosofia do template do projeto anterior).
4. **Escrever os JSONs** (UTF-8 normal — sem UTF-16LE!).
5. **Validar**: abrir o `.pbip` no Desktop; visual malformado aparece como
   erro no próprio visual, não corrompe o arquivo (ao contrário do `.pbix`).

## Padrão visual (design system)

Antes de escolher cor, fonte, borda, título ou eixo, ler
[references/design-system.md](references/design-system.md) — paleta,
tipografia, layout de página e o JSON pronto de cada tipo de visual (card,
gráfico, slicer, tabela), extraídos de um painel real em produção
(44 visuais, ago/2026). Seguir esse padrão salvo pedido em contrário.

> **Nunca sobrescrever formatação já aplicada pelo usuário.** Ao editar um
> visual existente, alterar apenas `query`/`position`; preservar os blocos
> `objects` e `visualContainerObjects` como estão.

## Regras críticas

0. **O `report.json` precisa de `themeCollection.baseTheme` no `config`.** Um
   report mínimo/vazio (ex.: só uma página em branco, útil quando o PBIP é "só
   modelo" e o usuário monta os visuais depois) que traga apenas
   `config: "{\"version\":\"...\"}"` sem `themeCollection` faz o Desktop falhar na
   RENDERIZAÇÃO (abre o modelo, mas: `Erro ao renderizar o relatório —
   TypeError: Cannot read properties of undefined (reading 'customTheme')`).
   Incluir sempre, no mínimo:
   ```json
   "themeCollection": { "baseTheme": { "name": "CY23SU04", "version": "5.43", "type": 2 } }
   ```
   (Copiar `name`/`version` de um report gerado pelo próprio Desktop.) O
   `customTheme` referencia um arquivo em `StaticResources/` — só incluir se o
   arquivo de tema existir; para report vazio, o `baseTheme` sozinho basta.
1. **NUNCA editar com o projeto aberto no Desktop** (Desktop sobrescreve ao salvar).
2. **IDs de página/visual**: seguir o padrão dos gerados pelo Desktop —
   identificador único de 20 caracteres (ex: `90c2e07d8e84e7d5c026`), pasta = id.
   Copiar o formato, não inventar. O nome/pasta só pode conter letras, dígitos,
   `_` ou `-` (regex de "word chars" + hífen); renomear é suportado mas quebra
   qualquer referência externa que apontava para o id antigo — exige reabrir o
   Desktop depois (ele preserva o nome novo na próxima gravação).
3. **`pageBinding.name` deve ser único no relatório inteiro** (drillthrough e
   tooltip de página compartilham esse mecanismo — ver seção própria abaixo).
   Copiar página com `pageBinding` de outro relatório sem trocar o `name` gera
   o erro "Values for the 'pageBinding.name' property must be unique." Usar
   sempre um GUID novo (padrão do Desktop desde jun/2024), nunca reaproveitar.
4. **`definition.pbir` byPath** (modelo local na mesma pasta) é o cenário
   deste projeto; `byConnection` só para deploy via Fabric API (fase 2).
5. **Medidas DAX**: referenciar por `Entity` + `Property` com o nome exato do
   TMDL (equivalente ao `measure_ref` do projeto anterior).
6. **Commitar antes de gerar** — undo via `git restore`.
7. **Bookmarks capturam dados reais do modelo** (ex: valor de um filtro fica
   gravado no `.bookmark.json`) — nunca gerar bookmark à mão fora do Desktop;
   só versionar o resultado depois de criado pela interface.

## Catálogo de visuais (a portar do projeto anterior)

Herança da `gerar-pbix`, validada em produção, a mapear para PBIR:
cards, donut, barras, linha, área, combo, tabela, matriz, gauge, slicers,
shape, textbox, botão de navegação, imagem (ícones/logo via StaticResources),
`grid()` de layout, filtros de página/visual, preset `kpi_card_villa` e o
design system VILLA.

## Drillthrough e Tooltip de página (validado em campo — VILLA MT, jul/2026)

Ambos são **`pageBinding` na página de destino** + configuração no visual de
origem. Foram a parte mais difícil de acertar às cegas; as regras abaixo saíram
de depuração real e evitam repetir o mesmo ciclo de tentativa-e-erro.

### Drillthrough (botão direito → Detalhar)

Na `page.json` da página de destino (a que abre filtrada):

```json
{
  "type": "Drillthrough",
  "filterConfig": {
    "filters": [
      {
        "name": "<id-do-filtro>",
        "ordinal": 0,
        "field": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_unidade" } }, "Property": "SiglaUnidade" } },
        "type": "Categorical",
        "howCreated": "Drillthrough",
        "objects": { "general": [ { "properties": { "requireSingleSelect": { "expr": { "Literal": { "Value": "true" } } } } } ] }
      }
    ],
    "filterSortOrder": "Custom"
  },
  "pageBinding": {
    "name": "drillthrough-<slug>",
    "type": "Drillthrough",
    "parameters": [
      {
        "name": "SiglaUnidade",
        "boundFilter": "<id-do-filtro>",
        "fieldExpr": { "Column": { "Expression": { "SourceRef": { "Entity": "dim_unidade" } }, "Property": "SiglaUnidade" } }
      }
    ]
  }
}
```

- **`pageBinding.parameters` NÃO pode ficar vazio (`[]`).** Com `[]`, o Desktop
  abre o arquivo sem erro mas **não reconhece a página como drillthrough** (a
  seção "Detalhamento" some do painel de formato). Cada parameter liga o filtro
  (`boundFilter` = o `name` do filtro em `filterConfig`) ao campo (`fieldExpr`,
  a mesma expressão de coluna do filtro).
- **O campo do filtro tem de ser a MESMA coluna que os visuais de origem usam.**
  Se o gráfico/tabela de origem agrupa por `dim_unidade.SiglaUnidade`, o
  drillthrough tem de filtrar por `SiglaUnidade` — não por `UNIDADE_CURTA` nem
  outra coluna da mesma tabela. Com coluna divergente, o "Detalhar" não aparece
  no menu de botão-direito. Não precisa configurar nada nos visuais de origem: o
  Desktop habilita "Detalhar" automaticamente em qualquer visual que use a coluna.
- Colunas calculadas (ex.: `SiglaUnidade` via `SWITCH`) funcionam como campo de
  drillthrough normalmente.

### Tooltip de página (popup ao passar o mouse)

Na `page.json` da página-tooltip: `"type": "Tooltip"`. Na interface é o dropdown
**Informações da página → Tipo de página → "Dica de Ferramenta"** (o mesmo lugar
onde "Detalhamento" = Drillthrough). No visual de origem, em
`visualContainerObjects`:

```json
"visualTooltip": [
  { "properties": {
      "show":    { "expr": { "Literal": { "Value": "true" } } },
      "type":    { "expr": { "Literal": { "Value": "'Canvas'" } } },
      "section": { "expr": { "Literal": { "Value": "'<id-da-pagina-tooltip>'" } } }
  } }
]
```

`section` é o **`name` (GUID) da página-tooltip**, não o `displayName`.

**`type` correto é `'Canvas'`, não `'ReportPage'`.** Confirmado em campo
(VILLA MT, Painel-RM-Turnover-GERT, jul/2026): gerar o JSON com
`type: 'ReportPage'` (valor citado em exemplos antigos/genéricos) faz o
tooltip nativo da série prevalecer mesmo com `section` correto — o Desktop
simplesmente não reconhece esse valor de enum como "página de relatório" na
versão atual. O valor real que o Desktop grava ao configurar pela UI ("Dicas
de ferramenta" → Tipo → "Página de relatório") é `'Canvas'`. **Sempre copiar
o `type` de um `visualTooltip` gerado pelo próprio Desktop na versão em uso**
(mesma regra geral do `$schema`) em vez de reaproveitar o valor de uma versão
anterior da doc/skill.

**NÃO adicionar `sentenceTemplate`/`showChartSpecificTooltips`/
`showSentenceFormat`/`showTooltipFieldsOnly` manualmente.** Essas 4
propriedades pareciam necessárias numa hipótese inicial, mas **não são** — o
tooltip funciona corretamente só com `show`/`type`/`section`. Pior: se o
`$schema` do arquivo (`visualContainer/2.10.0` no caso testado) não reconhece
essas propriedades na validação de leitura, o Desktop bloqueia a abertura do
relatório inteiro com **"Seu relatório tem problemas que não puderam ser
resolvidos"**, listando cada propriedade como "adicional" não reconhecida —
mesmo tendo sido o próprio Desktop quem as gravou anteriormente (grava mais
permissivamente do que valida na leitura). Se esse erro aparecer, a correção
é remover essas 4 propriedades do `visual.json` afetado (Desktop fechado) e
manter só `show`/`type`/`section`.

Armadilhas confirmadas:

- **NÃO reaproveitar uma página de drillthrough como tooltip.** Se um visual
  aponta `visualTooltip.section` para uma página cujo `type` é `Drillthrough`, o
  Desktop **converte essa página para `type: "Tooltip"` ao salvar** — e nesse
  processo **apaga o `filterConfig`/`pageBinding` de drillthrough dela**,
  quebrando o drillthrough silenciosamente. Drillthrough e tooltip pedem páginas
  **separadas**. Depois de configurar tooltip pela interface, reabra e confira
  que as páginas de drillthrough continuam `type: "Drillthrough"`.
- **Tabelas/matrizes (`tableEx`) não expõem o poço "Dicas de ferramentas"** no
  painel Compilar e têm suporte pobre a tooltip de página — mostram o tooltip
  padrão (valor da célula + rodapé de ações/Drill-through). Prefira gráficos
  (colunas, linha, barras) como origem do tooltip de página.
- **"Modern Visual Tooltips" é GA e padrão** (não é mais preview removível). O
  popup padrão traz um "Actions footer" com Drill-through embutido; é esse popup
  pequeno que aparece, não o tooltip de página, quando algo está desalinhado.
- **Gráfico com múltiplas séries mostrando o tooltip nativo (valores da série)
  em vez da página customizada, mesmo com `section` aparentemente correto**:
  quase sempre é o `type: 'ReportPage'` errado (ver correção acima — o valor
  certo é `'Canvas'`). **Não é** falta de `showChartSpecificTooltips`/
  `showSentenceFormat`/`showTooltipFieldsOnly` — gerar só com
  `show`/`type`/`section` (ver "Regra de ouro reforçada" abaixo) já é
  suficiente; essas 3 propriedades extras não resolvem o problema e ainda
  arriscam o erro bloqueante de schema descrito abaixo. Tabelas (`tableEx`)
  não sofrem do problema de tooltip nativo de série por não terem essa
  competição.
  **Se mesmo com o `type: 'Canvas'` o tooltip não disparar após reabrir**: no
  Desktop, painel Formatar visual → Dicas de ferramenta, mude Tipo para
  "Padrão" e volte para "Página de relatório", e mude Página para "Auto" e
  volte para a página correta — essa interação força o Desktop a reconciliar
  o estado (visto em campo: editar só o JSON não bastou numa ocasião, mesmo
  com os valores corretos já presentes em disco).
- **`displayOption`/tamanho**: gere a página-tooltip como o Desktop gera — a
  referência que funcionou usava `displayOption: "FitToPage"`. O Desktop mantém
  `visibility: "HiddenInViewMode"` em página-tooltip (readiciona ao salvar se
  você remover), então **não é** isso que impede o hover; é o padrão esperado.
  A causa real de "não dispara" costuma ser apontar para a página errada
  (`section` de uma página `Drillthrough`) ou usar tabela como origem.
- Tooltip de página **funciona no Desktop e no Service** (não é exclusivo da web).

## Contraste de texto sobre fundo customizado — nunca usar `ThemeDataColor` de cabeça

`ThemeDataColor` (`{"ColorId": 0, "Percent": 0}`) resolve para uma cor
diferente dependendo do `baseTheme` do relatório — em tema testado em
produção (ago/2026) `ColorId: 0` resolveu para uma cor **clara**, pensada
pra texto sobre fundo escuro do tema padrão. Ao aplicar essa mesma
propriedade em slicers/tabelas que ficam sobre um fundo de página **claro**
(cinza `#F4F6FA`/branco) customizado pelo próprio painel, o texto renderiza
praticamente invisível — sem erro nenhum na abertura, só ilegível na tela,
o tipo de bug que só aparece quando alguém manda print reclamando.

**Regra**: para qualquer `fontColor`/`fontColorPrimary`/`fontColorSecondary`
de texto que fica sobre um fundo controlado pelo próprio painel (não sobre
o tema padrão do Power BI sem alteração), usar sempre um `Literal` de cor
explícita compatível com esse fundo — nunca `ThemeDataColor`:

```json
"fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } }
```

`ThemeDataColor` só é seguro em elementos que herdam o tema padrão sem
nenhuma customização de fundo por cima.

## Imagem de fundo de página — sempre redimensionar + recomprimir antes de embutir

Reaproveitar uma imagem de fundo de um painel anterior (ou qualquer imagem
fornecida pelo usuário) sem processar primeiro é um erro de performance
comum: a imagem original costuma ter resolução e peso muito acima do que a
página realmente precisa (ex.: 1672×941px / 1,4 MB pra uma página de
1280×720). Isso soma rápido — duas páginas com a mesma imagem já são quase
3 MB só de fundo, sem contribuir em nada pro conteúdo.

**Regra**: antes de registrar qualquer imagem de fundo em
`StaticResources/RegisteredResources/`, redimensionar pro tamanho exato da
página (`page.json` → `width`/`height`) e recodificar como JPEG qualidade
~80 (fundos raramente precisam de transparência/PNG). Sem ImageMagick
disponível no Windows, usar .NET via PowerShell:

```powershell
Add-Type -AssemblyName System.Drawing
$original = [System.Drawing.Image]::FromFile($src)
$resized = New-Object System.Drawing.Bitmap($targetW, $targetH)
$graphics = [System.Drawing.Graphics]::FromImage($resized)
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$graphics.DrawImage($original, 0, 0, $targetW, $targetH)
$jpegCodec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$encParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
$encParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [int64]80)
$resized.Save($dst, $jpegCodec, $encParams)
```

Resultado validado em produção: 1,4 MB → 32 KB (~98% menor) sem perda
perceptível, reaproveitando a mesma imagem processada em duas páginas.

## Ícones outline via Iconify — SVG direto, sem depender de conversão pra PNG

O fluxo documentado em `gerar-pbix/references/design-system-villa.md`
(`iconify_png` via `resvg-py`) exige Python + uma dependência que nem
sempre está instalada no ambiente. Quando o que se precisa é um ícone
outline monocromático (não o estilo "flat-color-icons" ilustrado do preset
`kpi_card_villa`), a própria API do Iconify entrega o SVG já colorido via
query string — **não precisa converter pra PNG**, o Power BI aceita SVG
diretamente como `image` (mesmo mecanismo de `RegisteredResources`):

```bash
curl -s "https://api.iconify.design/tabler/alert-triangle.svg?color=%23B5342A" -o icon_atrasadas.svg
```

Duas correções necessárias antes de registrar o arquivo:
- Trocar `width="1em" height="1em"` (que a API retorna por padrão) por
  dimensões fixas em pixels (`width="48" height="48"`) — `1em` não renderiza
  de forma confiável como imagem estática fora de um contexto CSS.
- A cor vai na própria URL (`?color=%23RRGGBB`, hex com `#` urlencodado como
  `%23`) — escolher a cor de acento do KPI/elemento ali, sem precisar editar
  o SVG depois num editor.

Família `tabler:` tem bom catálogo outline consistente pra ícones de KPI
corporativo (`clipboard-list`, `circle-check`, `clock`, `chart-line`,
`alert-triangle`, etc.) — mesmo estilo visual entre ícones diferentes, sem
precisar garimpar coleção por coleção.

## Não inventar sintaxe de filtro/seletor sem gabarito real

Propriedades como `filterConfig` com tipo `Advanced` (filtro DAX-like
`Not`/`Comparison`/`null`) e seletores de série por `dataPoint` usando
`scopeId`/`equals` têm sintaxes internas do Power BI que não estão
documentadas publicamente e variam entre versões/schema. Escrever essas
estruturas "de memória" ou por analogia com outra propriedade é a fonte
mais provável de gerar um PBIR que abre sem erro de schema mas falha
silenciosamente ou quebra na próxima resalva do Desktop — a mesma classe de
risco já descrita na "Regra de ouro reforçada" abaixo, só que auto-infligida
em vez de causada pelo Desktop.

**Regra**: se não há um `visual.json` real (do próprio projeto ou de outro
já validado no repositório/`examples/`) pra copiar a estrutura exata,
preferir a alternativa mais simples que não depende de sintaxe não
verificada — por exemplo, resolver a exclusão de uma categoria vazia via
medida DAX (`BLANK()` no lugar de `0`) em vez de um filtro Advanced no
visual, ou deixar as cores de série padrão do tema em vez de um seletor
`dataPoint` por categoria sem gabarito. Ajustar manualmente pela interface
do Desktop depois é mais barato do que depurar um PBIR que quebra a
abertura ou corrompe silenciosamente.

### Regra de ouro reforçada

O Desktop **reescreve os arquivos ao salvar** e, ao fazê-lo, (a) injeta
propriedades que você omitiu — em `visualTooltip` ele adiciona
`showChartSpecificTooltips`, `showSentenceFormat`, `showTooltipFieldsOnly`; se
essas não existirem na versão de `$schema` que o arquivo declara, a próxima
abertura mostra **"Seu relatório tem problemas que não puderam ser resolvidos"**.
Mantenha só `show`/`type`/`section` e deixe o Desktop completar; (b) pode
converter/normalizar tipos de página (ver armadilha drillthrough↔tooltip acima).
**Corolário:** editar arquivo com o Desktop ABERTO gera conflito de sincronização
que pode disparar essa mesma tela de erro. Sempre feche o Desktop antes de editar
e, se ele já resalvou algo, releia o disco antes de continuar (`git diff`).
