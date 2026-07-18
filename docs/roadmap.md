# Roadmap — pbip-autopilot-fabric

## Fase 0 — Fundação (atual)
- [x] Estrutura do repositório e manifesto do plugin
- [x] Esqueleto das 3 skills (`gerar-modelo-tmdl`, `gerar-visuais-pbir`, `pbip-context`)
- [x] Converter um template real para `.pbip` e usar como projeto de referência
      — `banco_edu.pbip`/`.SemanticModel`/`.Report` (21 tabelas, 32 medidas, 28
      relacionamentos, 3 páginas de relatório). **Ainda não commitado** —
      existe só no working tree local; decidir se entra no repo como fixture
      permanente ou fica como projeto de teste descartável.

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
- [ ] update-m (troca de fonte: Excel local → SharePoint) — não testado ainda
- [x] export-m — trivial pelo formato: o M já é texto legível/editável direto
      no `.tmdl`, não exige implementação própria
- [ ] Conectores ainda não validados por nós (vêm só da doc oficial): Oracle,
      PostgreSQL/Supabase, MongoDB

### Relatório (gerar-visuais-pbir) — v0.5.0, "esqueleto em validação"
Infraestrutura JSON (estrutura de pastas, `themeCollection`, drillthrough,
tooltip de página, convenção de nomes de pasta/id, limites do serviço) está
validada em campo (VILLA MT). Catálogo de visuais herdado do `gerar-pbix`,
portado pra PBIR em [references/catalogo-visuais.md](../skills/gerar-visuais-pbir/references/catalogo-visuais.md)
— 7 tipos nativos com template real (extraído do `banco_edu`, identidade
VILLA), 7 ainda faltam (sem exemplo real gerado no Desktop ainda):
| Visual (gerar-pbix) | PBIR | Status |
|---|---|---|
| card_vc | visual.json tipo card | ✅ template real |
| donut_vc | visual.json tipo donutChart | ✅ template real |
| bar_vc / column_vc | visual.json tipo barChart/columnChart | ✅ template real |
| line_vc | visual.json tipo lineChart (multi-série) | ✅ template real |
| table_vc | visual.json tipo tableEx | ✅ template real |
| shape_vc | visual.json tipo shape | ✅ template real |
| textbox_vc | visual.json tipo textbox | ✅ template real |
| matrix_vc | visual.json tipo pivotTable | pendente — sem exemplo real |
| gauge_vc | visual.json tipo gauge | pendente — sem exemplo real |
| slicer_vc | visual.json tipo slicer | pendente — sem exemplo real |
| combo_vc | visual.json tipo comboChart | pendente — sem exemplo real |
| area_vc | visual.json tipo areaChart/stackedAreaChart | pendente — sem exemplo real |
| nav_button_vc | visual.json tipo actionButton | pendente — sem exemplo real |
| image_vc | visual.json tipo image + StaticResources | pendente — sem exemplo real |
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
