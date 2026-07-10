# Roadmap — pbip-autopilot-fabric

## Fase 0 — Fundação (atual)
- [x] Estrutura do repositório e manifesto do plugin
- [x] Esqueleto das 3 skills (`gerar-modelo-tmdl`, `gerar-visuais-pbir`, `pbip-context`)
- [ ] Converter um template real do projeto anterior para `.pbip` e commitar
      como projeto de referência (gabarito de TMDL e PBIR gerados pelo Desktop)

## Fase 1 — Paridade com o PowerBI-Autopilot
Validar em produção (mesmo critério do projeto anterior: VILLA MT).

### Modelo (gerar-modelo-tmdl)
- [ ] add-table com partição M (SQL nativo via `Sql.Database`)
- [ ] add-measure / add-measure-table (grupo de medidas)
- [ ] add-calc-column
- [ ] add-relationship
- [ ] update-m (troca de fonte: Excel local → SharePoint)
- [ ] export-m (agora trivial: o M já está em texto nos TMDL)

### Relatório (gerar-visuais-pbir) — mapa de portabilidade do catálogo
| Visual (gerar-pbix) | PBIR | Status |
|---|---|---|
| card_vc | visual.json tipo card | pendente |
| donut_vc / bar_vc / line_vc / area_vc / combo_vc | idem | pendente |
| table_vc / matrix_vc / gauge_vc | idem | pendente |
| slicer_vc / shape_vc / textbox_vc | idem | pendente |
| nav_button_vc / image_vc | idem + StaticResources | pendente |
| grid() / filtros página+visual | layout + filters.json | pendente |
| kpi_card_villa + design system | preset PBIR | pendente |

## Fase 2 — Fabric (zero Desktop)
- [ ] Deploy do PBIP via Fabric REST API (`definition.pbir` byConnection)
- [ ] Refresh do modelo via API (elimina a última intervenção manual)
- [ ] Avaliar semantic-link-labs / fabric-cicd como camada de deploy

## Fase 3 — Integrações
- [ ] powerbi-modeling-mcp para o cenário interativo (hot-edit de modelo aberto)
- [ ] Validador local de PBIR/TMDL (lint pré-abertura, sucessor do validate_pbix)
