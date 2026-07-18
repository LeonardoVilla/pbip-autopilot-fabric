---
name: validar-pbip
description: Roda um lint local (sem Desktop, sem Tabular Editor instalado) contra o modelo TMDL e o relatório PBIR de um projeto .pbip, antes de declarar algo "pronto para abrir". Cobre um subconjunto portável do Best Practice Analyzer do Tabular Editor (naming, format string, FK oculta, tipos float, TODO em DAX) mais as regras próprias já validadas em produção (compatibilityLevel, integridade de `ref`, relacionamento 1:1, tooltip/tema/pageBinding do PBIR). Use depois de gerar-modelo-tmdl / gerar-visuais-pbir, antes de pedir pro usuário abrir no Desktop.
argument-hint: <pasta-do-projeto.pbip> [--incluir-naming]
allowed-tools: [Read, Bash, PowerShell]
version: 0.1.0
---

# /validar-pbip — Lint local de TMDL/PBIR (sucessor do validate_pbix)

Roda `tools/validar_pbip/validar_pbip.py` contra a pasta do projeto e reporta
achados por severidade (Erro/Aviso/Info), sem precisar abrir o Power BI
Desktop nem instalar Tabular Editor. Papel equivalente ao `validate_pbix()` da
skill `gerar-pbix` (que valida a estrutura do .pbix antes de entregar) — aqui
a validação é sobre os arquivos de texto TMDL/PBIR.

## Quando rodar

Sempre como último passo de `gerar-modelo-tmdl` ou `gerar-visuais-pbir`, antes
de instruir o usuário a abrir o projeto no Desktop. Um achado de severidade
**Erro** normalmente corresponde a algo que trava a abertura ou o refresh —
vale corrigir antes de entregar.

## Uso

```powershell
python tools\validar_pbip\validar_pbip.py <pasta-do-projeto.pbip>
python tools\validar_pbip\validar_pbip.py <pasta>\<Nome>.SemanticModel
python tools\validar_pbip\validar_pbip.py <pasta>\<Nome>.Report
```

Saída: lista de achados ordenada por severidade + resumo com contagem de
erros/avisos/infos. Código de saída é `1` se houver algum **Erro**, `0` caso
contrário — dá pra encadear em pipeline.

Regras de nomenclatura PascalCase (`UPPERCASE_FIRST_LETTER_*`,
`NO_CAMELCASE_*`) ficam **desligadas por padrão**: modelos gerados a partir de
schema SQL (snake_case, ex. `aluno_id`) disparariam em quase toda coluna, o
que afoga os achados estruturais. Use `--incluir-naming` para reativá-las
quando o projeto aplicar renomeação PascalCase de propósito.

## Cobertura de regras

### Do Tabular Editor Best Practice Analyzer (`BPARules-PowerBI.json`)

Só o subconjunto checável via texto/estrutura do TMDL (sem motor DAX/TOM
rodando) foi portado:

| ID | O que checa |
|---|---|
| `META_AVOID_FLOAT` | coluna com `dataType: double` |
| `META_SUMMARIZE_NONE` | coluna numérica visível sem `summarizeBy: none` |
| `APPLY_FORMAT_STRING_COLUMNS` | coluna numérica/data visível sem `formatString` |
| `LAYOUT_HIDE_FK_COLUMNS` | coluna usada como `fromColumn` de relacionamento e ainda visível |
| `NO_CAMELCASE_*` / `UPPERCASE_FIRST_LETTER_*` | convenção de nome (desligado por padrão — ver acima) |
| `RELATIONSHIP_COLUMN_NAMES` | nomes de coluna divergentes nos dois lados do relacionamento |
| `DAX_TODO` | "TODO" na expressão de medida/coluna calculada |
| `DIABLE_AUTO_DATE/TIME` (sic) | annotation `__PBI_LocalDateTable` presente |
| `LAYOUT_COLUMNS_HIERARCHIES_DF` / `LAYOUT_MEASURES_DF` | tabela com >10 colunas/medidas visíveis sem `displayFolder` |
| `AVOID_SINGLE_ATTRIBUTE_DIMENSIONS` | dimensão de 1 atributo usada por 1 única fato |

Três regras são **heurísticas** (aproximam a regra original via regex, sem
o parser DAX/dependência real do Tabular Editor — podem ter falso positivo/negativo):

| ID | Heurística | Limite conhecido |
|---|---|---|
| `DAX_DIVISION_COLUMNS` | procura `/` fora de `DIVIDE(...)` | não distingue string literal contendo `/` |
| `DAX_COLUMNS_FULLY_QUALIFIED` / `DAX_MEASURES_UNQUALIFIED` | olha se `[Nome]` tem tabela na frente e se `Nome` está no conjunto de colunas ou medidas do modelo | nomes duplicados entre tabelas podem confundir |
| `PERF_UNUSED_COLUMNS` / `PERF_UNUSED_MEASURES` | procura `[Nome]`/`Tabela[Nome]` em todo o texto DAX do modelo | não detecta uso via query externa/relatório — mesma ressalva da regra original |
| `APPLY_FORMAT_STRING_MEASURES` | medida visível sem `formatString` | dataType de medida não é declarado no TMDL (só se sabe em runtime) — sinaliza mesmo quando a medida é texto; confira manualmente |

**Não portado** (exige `cultures/`/`perspectives` reais ou motor DAX completo,
raro em projeto gerado do zero): `LAYOUT_ADD_TO_PERSPECTIVES`,
`LAYOUT_LOCALIZE_DF`, `TRANSLATE_DESCRIPTIONS`,
`TRANSLATE_HIDEABLE_OBJECT_NAMES`, `TRANSLATE_HIERARCHY_LEVEL_NAMES`,
`TRANSLATE_OTHER_NAMES`, `DAX_COLUMNS_FULLY_QUALIFIED`/`DAX_MEASURES_UNQUALIFIED`
em KPIs.

### Regras próprias (validadas em produção — ver `gerar-modelo-tmdl/SKILL.md` e `gerar-visuais-pbir/SKILL.md`)

| ID | O que checa | Por quê |
|---|---|---|
| `PBIP_DB_COMPATIBILITY` | `database.tmdl` com `compatibilityLevel: 1601` + `compatibilityMode: powerBI` | padrão validado no Desktop jul/2026 (commit `03fe519`) |
| `PBIP_MODEL_REF_INTEGRITY` | toda `ref table`/`ref expression` do `model.tmdl` aponta pra um arquivo/expressão que existe | `ref` malformado quebra com `Unexpected line type: ReferenceObject` |
| `PBIP_EXPRESSION_TABLE_COLLISION` | nome de `expression` (em `expressions.tmdl`) não coincide com nome de `table` | `expression` e `table` compartilham namespace — colisão quebra o load com `'duplicate member <nome>'` (achado do skill `tmdl` do [`data-goblin/power-bi-agentic-development`](https://github.com/data-goblin/power-bi-agentic-development)) |
| `PBIP_ONE_TO_ONE_BIDIRECTIONAL` | relacionamento `one`/`one` tem `crossFilteringBehavior: bothDirections` | Analysis Services rejeita `OneDirection` em 1:1 |
| `PBIP_DUPLICATE_COLUMN_NAME` | nome de coluna/medida não se repete dentro da mesma tabela | achado na prática (edição manual + gravação do Desktop duplicaram uma coluna `_id`) — comportamento indefinido/rejeição |
| `PBIP_REPORT_BASETHEME` | `report.json` tem `themeCollection.baseTheme` | falta trava a renderização (`Cannot read properties of undefined (reading 'customTheme')`) |
| `PBIP_THEME_FILE_MISSING` | o arquivo que `baseTheme` referencia (via `resourcePackages`) existe de verdade em `StaticResources/<tipo>/<path>` | achado do skill `pbip` do [`data-goblin/power-bi-agentic-development`](https://github.com/data-goblin/power-bi-agentic-development): apontar pra um recurso ausente também trava a abertura, e só checar a chave `baseTheme` não pega esse caso |
| `PBIP_TOOLTIP_TYPE` | `visualTooltip.type` de página é `Canvas`, não `ReportPage` | achado de campo (VILLA MT) — `ReportPage` mantém o tooltip nativo |
| `PBIP_TOOLTIP_EXTRA_PROPS` | `visualTooltip` sem `sentenceTemplate`/`showChartSpecificTooltips`/`showSentenceFormat`/`showTooltipFieldsOnly` | essas propriedades travam a ABERTURA do relatório inteiro se o `$schema` não reconhecer |
| `PBIP_PAGEBINDING_UNIQUE` | `pageBinding.name` é único no relatório inteiro | causa raiz documentada pela Microsoft para conflito de drillthrough/tooltip |
| `PBIP_FOLDER_ID_CONVENTION` | pasta de página/visual com até 20 caracteres, só `[A-Za-z0-9_-]` | limite aplicado pelo serviço PBIR |

## Fonte das regras BPA

Cópia local em [`references/BPARules-PowerBI.json`](references/BPARules-PowerBI.json),
baixada de
[`TabularEditor/BestPracticeRules`](https://github.com/TabularEditor/BestPracticeRules)
(arquivo `BPARules-PowerBI.json` do repo). **Sem arquivo de licença explícito
no repositório de origem** — a cópia aqui é só para referência interna de
quais regras existem e como estão descritas; antes de redistribuir esse JSON
fora deste projeto, confirmar os termos direto com os autores. Se a
Microsoft/Tabular Editor publicar novas regras, revisitar o arquivo e avaliar
quais entram no subconjunto portável de `validar_pbip.py`.

## Limitações

Isso **não** é um substituto do Tabular Editor real: não valida DAX
sintaticamente, não abre o modelo no Analysis Services, não pega erro de
`ReferenceObject` que não seja `ref` malformado (ex.: TMDL com erro de
indentação genuína só aparece ao abrir no Desktop). É um lint rápido pra
pegar os erros já catalogados antes de gastar o ciclo "abrir Desktop, ver erro,
fechar, corrigir".
