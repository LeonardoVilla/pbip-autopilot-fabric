# pbip-autopilot-fabric 🚀

**Power BI as Code** — do banco de dados ao painel pronto, sem tocar na interface.
TMDL + PBIR + Claude.

Sucessor do [PowerBI-Autopilot](https://github.com/LeonardoVilla/PowerBI-Autopilot),
migrado do formato binário `.pbix` para o formato **PBIP** (Power BI Project):
o modelo semântico vira **TMDL** e o relatório vira **PBIR** — tudo arquivo de texto,
versionável, gerável por script e por agentes de IA, de forma **oficialmente suportada**
pela Microsoft.

## A mudança de paradigma

### Antes (PowerBI-Autopilot, base `.pbix`)

```
abrir template no Desktop ──▶ injetar modelo via TOM (Desktop ABERTO)
──▶ Ctrl+S manual ──▶ fechar ──▶ cirurgia no ZIP do .pbix (Layout UTF-16LE,
SecurityBindings, compress_type) ──▶ reabrir o .pbix gerado
```

Duas aberturas do Desktop, um salvamento manual no meio, e um conjunto de
hacks não suportados para remendar o ZIP.

### Agora (pbip-autopilot-fabric, base `.pbip`)

```
gerar arquivos TMDL (modelo + ETL M) ──▶ gerar arquivos PBIR (páginas/visuais)
──▶ abrir o .pbip no Desktop UMA vez ──▶ Atualizar dados ──▶ salvar/publicar
```

Nenhum Desktop aberto durante a geração. Nenhum hack de ZIP. A única
intervenção manual é o refresh final (carga de dados exige o engine do
Desktop ou o serviço/Fabric).

## As skills

### Pipeline moderno (PBIP) — caminho principal

### `gerar-modelo-tmdl` — modelo semântico como código
Escreve os arquivos TMDL do `*.SemanticModel/definition/`: tabelas (com as
queries Power Query M embutidas nas partições), medidas DAX, colunas
calculadas e relacionamentos. Sucessora da `gerar-etl-tom` — sem precisar de
Desktop aberto nem de TOM.

### `gerar-visuais-pbir` — relatório como código
Escreve os JSONs PBIR do `*.Report/definition/`: páginas, visuais, filtros,
layout e tema, usando os schemas públicos documentados. Sucessora da
`gerar-pbix` — sem cirurgia de ZIP.

### `pbip-context` — regras críticas do formato PBIP
Estrutura de pastas, o que versionar e o que ignorar, `definition.pbir`
(byPath × byConnection), e as armadilhas conhecidas do formato.

### Pipeline legado (.pbix) — fallback validado em produção

As 3 skills originais do PowerBI-Autopilot continuam incluídas e funcionais,
para quando o alvo for um `.pbix` fechado (sem conversão para PBIP):

- **`gerar-etl-tom`** — injeta modelo/ETL via TOM num Power BI Desktop
  ABERTO (CLI C# em `tools/EtlTom`, .NET 6). Também segue útil no mundo PBIP
  para ajuste fino de um modelo já aberto (hot-edit).
- **`gerar-pbix`** — gera os visuais substituindo o `Report/Layout` do `.pbix`
  via Python (formato legado; será descontinuado pela Microsoft no GA do PBIR).
- **`pbix-context`** — regras críticas do `.pbix` (SecurityBindings, UTF-16LE,
  compress_type).

## Roadmap

Ver [docs/roadmap.md](docs/roadmap.md) — inclui o mapa de migração do
catálogo de visuais do projeto anterior (cards, tabelas, matriz, gauge,
linha, área, combo, donut, barras, slicers, preset KPI VILLA) para PBIR,
e a fase 2: deploy direto no Fabric via REST API (zero Desktop).

## Requisitos

- Windows + Power BI Desktop (release maio/2026+ — PBIR como formato padrão)
- Git (o `.pbip` é feito para versionamento)
- Opcional: [powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp)
  para ajustes interativos num modelo aberto
- Fase 2: capacidade Fabric ou workspace Pro (deploy via API, sem Desktop)
- Pipeline legado: .NET 6 SDK (CLI `etl-tom`) e Python 3.x (`gerar-pbix`)

## Estrutura

```
skills/
  gerar-modelo-tmdl/   modelo semântico via TMDL (SKILL.md)
  gerar-visuais-pbir/  relatório via PBIR (SKILL.md)
  pbip-context/        regras críticas do formato PBIP
  gerar-etl-tom/       [legado] ETL/modelo via TOM em .pbix aberto
  gerar-pbix/          [legado] visuais/.pbix via Python + design system
  pbix-context/        [legado] regras críticas do .pbix
tools/EtlTom/          [legado] CLI C# (.NET 6) — Analysis Services local
docs/
  roadmap.md           plano de migração e fases
plugin.json            manifesto do plugin
```
