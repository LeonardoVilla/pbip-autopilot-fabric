# Roadmap — pbip-autopilot-fabric

## Fase 0 — Fundação (atual)
- [x] Estrutura do repositório e manifesto do plugin
- [x] Esqueleto das 3 skills (`gerar-modelo-tmdl`, `gerar-visuais-pbir`, `pbip-context`)
- [x] Converter um template real para `.pbip` e usar como projeto de referência
      — `banco_edu.pbip`/`.SemanticModel`/`.Report` (21 tabelas, 32 medidas, 28
      relacionamentos, 3 páginas de relatório). Commitado como fixture
      permanente do repo.

## Fase 1 — Paridade com o PowerBI-Autopilot
Validar em produção (mesmo critério do projeto anterior: VILLA MT).

### Modelo (gerar-modelo-tmdl) — v0.2.0, "parcialmente validado"
- [x] add-table com partição M — validado com `Odbc.Query`/MySQL (`banco_edu`)
      e API REST com token/`Web.Contents` (SIPLAN); `Sql.Database` (T-SQL)
      herdado do projeto anterior, ainda não re-testado nesta skill
- [x] add-measure / add-measure-table (grupo de medidas) — `banco_edu`, 32
      medidas em tabela `_Medidas`, incl. medidas DAX multi-linha
- [x] add-calc-column — `banco_edu` (`'Faixa Etária'`, `'Faixa Nota'` via SWITCH)
- [x] add-relationship — `banco_edu`, 28 relacionamentos incl. regra 1:1
      bidirecional e validador de ciclo (union-find) antes de abrir no Desktop
- [x] update-m — validado no `banco_edu` (tabela `blocos`): editar a expressão
      M da partição direto no `.tmdl` (query SQL alterada + coluna nova
      `nome_maiusculo`) e o Desktop carregou corretamente no Atualizar.
      Não foi testado o caso específico Excel local → SharePoint (fora do
      escopo do `banco_edu`, que é 100% MySQL), mas o mecanismo central —
      trocar a fonte M de uma tabela existente por texto — está confirmado.
- [x] export-m — trivial pelo formato: o M já é texto legível/editável direto
      no `.tmdl`, não exige implementação própria
- [x] PostgreSQL — validado (container Docker de teste, `PostgreSQL.Database`
      com navegação `Fonte{[Schema="public",Item="<tabela>"]}[Data]`,
      credencial de banco pedida na primeira carga). Ver achado sobre
      `double`/`summarizeBy: sum` abaixo.
- [x] Oracle — validado (container Docker `gvenzl/oracle-free`, `Oracle.Database`
      com `[Query="SELECT ..."]`). Também confirmou o fix de `Currency.Type`
      (ver achado #5 no `gerar-modelo-tmdl/SKILL.md`): coluna `saldo`
      permaneceu `decimal` após Atualizar, diferente de `produtos_pg_teste`
      (sem o fix, virou `double` sozinha).
- [x] MongoDB — validado (conta Atlas real do usuário, federated database +
      Atlas SQL Interface). Exige um passo extra que não estava documentado:
      gerar o schema SQL primeiro (`sqlGenerateSchema` via mongosh, contra o
      database `admin`) — sem isso a coleção carrega "sem colunas com tipos
      suportados". Função M real: `MongoDBAtlasODBC.Contents(uri, database,
      [])` + navegação `{[Name=...,Kind="Database"]}[Data]` →
      `{[Name=...,Kind="Table"]}[Data]`. Array aninhado do MongoDB
      (ex.: lista de subdocumentos) chega como **string JSON serializada**,
      não expande em linhas/colunas.

### Relatório (gerar-visuais-pbir) — v0.5.0, "esqueleto em validação"
Infraestrutura JSON (estrutura de pastas, `themeCollection`, drillthrough,
tooltip de página, convenção de nomes de pasta/id, limites do serviço) está
validada em campo (VILLA MT). Catálogo de visuais herdado do `gerar-pbix`,
portado pra PBIR em [references/catalogo-visuais.md](../skills/gerar-visuais-pbir/references/catalogo-visuais.md)
— **14 de 14 tipos nativos com template real**, catálogo completo:
| Visual (gerar-pbix) | PBIR | Status |
|---|---|---|
| card_vc | visual.json tipo card | ✅ template real |
| donut_vc | visual.json tipo donutChart | ✅ template real |
| bar_vc / column_vc | visual.json tipo barChart/columnChart | ✅ template real |
| line_vc | visual.json tipo lineChart (multi-série) | ✅ template real |
| table_vc | visual.json tipo tableEx | ✅ template real |
| shape_vc | visual.json tipo shape | ✅ template real |
| textbox_vc | visual.json tipo textbox | ✅ template real |
| gauge_vc | visual.json tipo gauge | ✅ template real (escala default 0-100) |
| slicer_vc | visual.json tipo slicer | ✅ template real (modo lista; dropdown ainda não) |
| matrix_vc | visual.json tipo pivotTable | ✅ template real (Total automático) |
| area_vc | visual.json tipo areaChart | ✅ template real |
| combo_vc | visual.json tipo lineClusteredColumnComboChart | ✅ template real (nome nativo != "comboChart", achado corrigido) |
| image_vc | visual.json tipo image + StaticResources | ✅ template real |
| nav_button_vc | visual.json tipo actionButton | ✅ template real (ação em `visualContainerObjects.visualLink`, não em `objects` — achado corrigido) |

- [x] `grid()` de layout — portado direto do `gerar-pbix` (matemática pura, sem precisar de teste no Desktop)
- [x] Filtros de página/visual com valor fixo — testado no Desktop: `filterConfig.filters[]` no PBIR usa a mesma estrutura `From/Where/Condition/In/Values` do `equals_filter()` legado, só sem serialização em string

- [x] Preset `kpi_card_villa` completo (barra de acento + label + número + ícone) — testado no Desktop, composição de 4 visuais já validados

**Fase 1 (modelo + relatório) está completa.**
| grid() / filtros página+visual | layout + filters.json | pendente |
| kpi_card_villa + design system | preset PBIR (barra de acento + ícone) | pendente |

## Fase 2 — Fabric (zero Desktop)
- [ ] Deploy do PBIP via Fabric REST API (`definition.pbir` byConnection)
- [ ] Refresh do modelo via API (elimina a última intervenção manual)
- [ ] Avaliar semantic-link-labs / fabric-cicd como camada de deploy

## Fase 3 — Integrações
- [x] Cenário interativo (hot-edit de modelo aberto) — `tools/EtlTom` revivido:
      SDK ausente + net6.0 (EOL, pacotes não resolviam) corrigidos, retarget
      p/ net8.0, comando `remove-measure` adicionado (faltava). Testado ao
      vivo contra `banco_edu.pbip` aberto no Desktop: descoberta de porta,
      leitura (list/list-measures) e escrita (add-measure/remove-measure)
      via TOM, tudo confirmado. Ainda não avaliamos powerbi-modeling-mcp como
      alternativa/complemento — EtlTom cobre o caso de uso por ora.
- [x] Validador local de PBIR/TMDL (lint pré-abertura, sucessor do validate_pbix)
      — skill `validar-pbip`, subconjunto portável do Tabular Editor BPA +
      regras próprias (compatibilityLevel, ref, tooltip/tema/pageBinding),
      testado contra o fixture real `banco_edu`
      - [x] Melhoria (achado do skill `pbip` do data-goblin): `PBIP_THEME_FILE_MISSING`
            checa se o arquivo que `themeCollection.baseTheme` aponta existe
            de verdade em `StaticResources/`, testado com fixture sintético
- [x] Guia de rename seguro (tabela/coluna/medida) — `pbip-context/references/rename-cascade.md`
- [x] Documentação de roles/RLS/perspectives/calculation groups — `gerar-modelo-tmdl/references/roles-perspectives-calculation-groups.md`
      (📄 esqueleto de doc oficial, nunca testado — nenhum projeto real pediu ainda)
- [x] Higiene de repositório (achado do skill `pbip` do data-goblin): geradores
      já usavam `encoding="utf-8"` + `newline="\n"` (sem BOM, confirmado);
      `.gitattributes` criado (`* text=auto eol=lf` + binários); regra
      documentada em `pbip-context/SKILL.md`
- [x] Terminologia thick vs. thin report documentada em `pbip-context/SKILL.md`
