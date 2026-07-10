---
name: gerar-visuais-pbir
description: Gera o relatório de um projeto Power BI (PBIP) escrevendo os JSONs do formato PBIR - páginas, visuais (card, tabela, matriz, gauge, linha, área, combo, donut, barras, slicer), filtros e layout. Use quando o usuário pedir para criar/gerar os visuais de um painel programaticamente. Não requer Desktop aberto; opera sobre a pasta *.Report do .pbip.
argument-hint: <pasta-do-projeto.pbip> [nome-do-painel]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.1.0
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
