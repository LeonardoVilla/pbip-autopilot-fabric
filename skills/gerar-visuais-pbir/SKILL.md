---
name: gerar-visuais-pbir
description: Gera o relatório de um projeto Power BI (PBIP) escrevendo os JSONs do formato PBIR - páginas, visuais (card, tabela, matriz, gauge, linha, área, combo, donut, barras, slicer), filtros e layout. Use quando o usuário pedir para criar/gerar os visuais de um painel programaticamente. Não requer Desktop aberto; opera sobre a pasta *.Report do .pbip.
argument-hint: <pasta-do-projeto.pbip> [nome-do-painel]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.2.0
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
    report.json             # config global do relatório
    version.json
    pages/
      pages.json            # ordem e página ativa
      <id-da-pagina>/
        page.json           # nome, dimensões, displayName
        visuals/
          <id-do-visual>/
            visual.json     # tipo, posição, campos, formatação
  StaticResources/          # imagens/ícones/tema (substitui RegisteredResources)
```

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
1. **NUNCA editar com o projeto aberto no Desktop** (Desktop sobrescreve ao salvar).
2. **IDs de página/visual**: seguir o padrão dos gerados pelo Desktop
   (identificadores únicos, pasta = id). Copiar o formato, não inventar.
3. **`definition.pbir` byPath** (modelo local na mesma pasta) é o cenário
   deste projeto; `byConnection` só para deploy via Fabric API (fase 2).
4. **Medidas DAX**: referenciar por `Entity` + `Property` com o nome exato do
   TMDL (equivalente ao `measure_ref` do projeto anterior).
5. **Commitar antes de gerar** — undo via `git restore`.

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
      "type":    { "expr": { "Literal": { "Value": "'ReportPage'" } } },
      "section": { "expr": { "Literal": { "Value": "'<id-da-pagina-tooltip>'" } } }
  } }
]
```

`section` é o **`name` (GUID) da página-tooltip**, não o `displayName`.

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
