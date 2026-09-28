---
name: gerar-visuais-pbir
description: Gera o relatório de um projeto Power BI (PBIP) escrevendo os JSONs do formato PBIR - páginas, visuais (card, tabela, matriz, gauge, linha, área, combo, donut, barras, slicer), filtros e layout. Use quando o usuário pedir para criar/gerar os visuais de um painel programaticamente. Não requer Desktop aberto; opera sobre a pasta *.Report do .pbip.
argument-hint: <pasta-do-projeto.pbip> [nome-do-painel]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.5.0
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
>
> **⚠️ set/2026:** confirmado em campo que gerar visuais "à mão" (sem antes
> checar uma referência real do Desktop instalado) tem alto risco de
> produzir um relatório que carrega o modelo mas falha ao renderizar com um
> erro genérico (`Cannot read properties of undefined (reading
> 'visualContainers')`) que NÃO indica qual visual ou campo é o culpado. As
> causas raiz confirmadas até agora — schema/tema de `report.json`
> desatualizado (regra 0), ausência de `filterConfig` em cada visual (regra
> 0a), e `version.json` com o schema/valor errado (regra 0b) — foram
> encontradas por eliminação, comparando contra uma referência real gerada
> no próprio Desktop do usuário. Depois desse ponto, erros de `visualType`
> inválido (regra 0c) e de filtro de página por medida (regra 0d) aparecem
> de forma isolada e mais fácil de diagnosticar. **Antes de gerar visuais em
> massa para um projeto novo, sempre pedir ao usuário (ou gerar você mesmo,
> se tiver Desktop disponível) uma página de referência com 2-3 tipos de
> visual diferentes (card, gráfico com eixo, slicer) já salvos pelo
> Desktop**, e copiar a estrutura exata de lá — não confiar nos exemplos
> desta skill sem essa checagem, pois a versão do Desktop do usuário pode já
> ter divergido deles.

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

   **⚠️ Correção validada em campo (VILLA MT, projeto de monitoria de
   atividade, set/2026, Desktop release ago/2026 build 2.157.1354.0):** o exemplo acima
   (`CY23SU04`/`version: "5.43"`/`type: 2`) é de uma versão antiga do Desktop
   e **não existe mais como arquivo de tema real** nessa build. Gerar
   `report.json` com esses valores inventados de memória faz o modelo carregar
   mas o relatório falha ao renderizar com o MESMO erro genérico descrito na
   regra 0a abaixo. O `report.json` real gerado por essa build usa:
   ```json
   {
     "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
     "themeCollection": {
       "baseTheme": {
         "name": "Fluent2-CY26SU08",
         "reportVersionAtImport": { "visual": "2.12.0", "report": "3.4.0", "page": "2.3.1" },
         "type": "SharedResources"
       }
     },
     "resourcePackages": [ { "name": "SharedResources", "type": "SharedResources",
       "items": [ { "name": "Fluent2-CY26SU08", "path": "BaseThemes/Fluent2-CY26SU08.json", "type": "BaseTheme" } ] } ],
     "settings": { "useStylableVisualContainerHeader": true, "exportDataMode": "AllowSummarized",
       "defaultDrillFilterOtherVisuals": true, "allowChangeFilterTypes": true,
       "useEnhancedTooltips": true, "useDefaultAggregateDisplayName": true }
   }
   ```
   Note `type: "SharedResources"` (string), não `type: 2` (número) — outra
   diferença de versão. **Regra reforçada: nunca reutilizar valores de
   `report.json`/`page.json`/`visual.json` citados nesta skill ou em qualquer
   doc/exemplo antigo sem primeiro gerar (ou pedir ao usuário para gerar) uma
   página em branco no Desktop instalado E COPIAR o `$schema`, o nome do tema
   e o arquivo `StaticResources/SharedResources/BaseThemes/<nome>.json` de lá.**
   Cada build do Desktop pode usar um tema padrão diferente; o nome do tema
   também muda o arquivo StaticResources necessário — sem ele, mesmo com o
   `report.json` correto, o Desktop não encontra o asset referenciado.

0a. **TODO `visual.json` PRECISA de um `filterConfig` no nível raiz — sem ele,
    o relatório falha ao renderizar com erro genérico e difícil de
    diagnosticar.** Validado em campo (mesma sessão acima): gerar visuais só
    com `visual: {...}` e nenhum `filterConfig` faz o Desktop CARREGAR o
    modelo (as queries M aparecem normalmente no relatório de erro) mas falhar
    ao pintar o relatório com:
    ```
    Erro ao renderizar o relatório.
    JS Error Message: Cannot read properties of undefined (reading 'visualContainers')
    ```
    Esse erro **não aponta para o visual nem a página culpada** — é um erro
    de nível de exploração inteira, então schema/versão errados e
    `filterConfig` ausente produzem exatamente o mesmo sintoma, o que torna
    fácil gastar várias rodadas corrigindo a causa errada (aconteceu nesta
    sessão: corrigimos `compatibilityLevel`, depois `$schema` de
    report/page/visual, depois `drillFilterOtherVisuals`, e só depois de
    comparar com um visual REAL gerado pelo Desktop é que o `filterConfig`
    ausente apareceu como diferença).

    **Padrão confirmado** (todo visual real gerado pelo Desktop tem isso, sem
    exceção, mesmo sem nenhum filtro configurado pelo usuário): para cada
    campo usado em qualquer role de `query.queryState` (Values, Category, Y,
    Series, etc.), adicionar um filtro correspondente:
    ```json
    "filterConfig": {
      "filters": [
        {
          "name": "<20-caracteres-hex-aleatorios>",
          "field": { /* MESMO objeto field usado na projection */ },
          "type": "Advanced"      // quando o field usa Measure/Aggregation
        },
        {
          "name": "<outro-id>",
          "field": { /* ... */ },
          "type": "Categorical"   // quando o field usa Column/HierarchyLevel puro
        }
      ]
    }
    ```
    Regra de ouro (a mesma do `$schema`): **gerar 1-2 visuais reais no Desktop
    primeiro** (um cartão com medida, um gráfico com categoria+valor, um
    slicer) e copiar a forma exata do `filterConfig` resultante antes de gerar
    em massa — o padrão acima foi inferido de exemplos reais mas o Desktop
    pode ter regras adicionais (ex.: `ordinal`, `howCreated`) não cobertas
    aqui ainda.

0b. **`version.json` (em `*.Report/definition/version.json`) tem seu PRÓPRIO
    schema — não confundir com a versão `"4.0"` do `definition.pbir`/
    `definition.pbism`.** Validado em campo (mesma sessão): um `version.json`
    com `{"version": "4.0"}` (copiado por engano do valor usado em
    `definition.pbir`) é aceito silenciosamente na abertura mas contribui para
    o mesmo erro genérico `Cannot read properties of undefined (reading
    'visualContainers')` ao renderizar — foi a correção que, combinada com a
    regra 0a, resolveu o problema nesta sessão. O valor real gerado pelo
    Desktop é:
    ```json
    {
      "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
      "version": "2.0.0"
    }
    ```
    Sempre copiar este arquivo literalmente de uma referência real — não
    inferir o valor a partir de outros arquivos `.pbir`/`.pbism` do mesmo
    projeto, que usam um schema (`definitionProperties`) e um número de
    versão (`"4.0"`) completamente diferentes.

0c. **Nomes de `visualType` inválidos falham de forma isolada e clara** (ao
    contrário das regras 0/0a/0b, que travam o relatório inteiro) — o visual
    específico mostra "Não é possível exibir este visual" /
    `CustomVisualNotFound`, pedindo para "adicionar este visual personalizado
    ao relatório". Isso geralmente não significa que falta um visual de
    terceiros: é sinal de que o `visualType` usado não é um nome válido de
    visual NATIVO. Confirmado em campo: `"stackedColumnChart"` não existe — o
    nome nativo correto para colunas empilhadas é `"columnChart"` (o
    empilhamento é о padrão quando há múltiplos campos em Values sem
    agrupamento lado a lado); `"clusteredColumnChart"` é o nome para colunas
    agrupadas lado a lado. **Nunca inventar `visualType` por analogia com o
    nome que aparece na UI do Desktop** ("Gráfico de colunas empilhadas") —
    conferir o nome real gerado ao inserir esse visual pela interface antes de
    usá-lo em massa.

0d. **Filtro de PÁGINA baseado em MEDIDA (measure) é frágil e pode quebrar a
    renderização de todos os visuais da página com um erro genérico de
    "capacidade ou licença".** Confirmado em campo: um `page.json` com
    `filterConfig.filters[].field.Measure` (filtrando a página inteira por
    ex. `Flag Compliance = 1`, uma medida `IF(...)`) fez TODOS os visuais da
    página (cards e tabela) falharem com o diálogo genérico "Isso pode ser
    causado por um problema de capacidade ou licença" — mensagem que não tem
    relação óbvia com a causa real. A hipótese mais provável é que o motor
    não consegue aplicar um filtro de página em nível de medida quando os
    visuais da página não compartilham o mesmo contexto de granularidade (ex.:
    cards agregados sem a mesma dimensão usada na medida). **Preferir filtrar
    por COLUNA em nível de VISUAL** (`filterConfig` do `visual.json`, não do
    `page.json`) sempre que possível — filtro por coluna simples
    (`flag_uso_indevido = true`) funciona nativamente; filtro por medida com
    lógica OR/IF entre colunas é mais seguro implementar como medida auxiliar
    consumida por um slicer, não como filtro de página direto.

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
