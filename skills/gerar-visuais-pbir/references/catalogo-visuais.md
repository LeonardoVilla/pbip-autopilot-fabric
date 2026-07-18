# Catálogo de visuais PBIR — templates escolhíveis

Templates de `visual.json` extraídos de exemplos **nossos**, gerados de
verdade pelo Power BI Desktop no projeto `banco_edu` (não copiados de
terceiros — ver nota de licenciamento abaixo). Já saem com a identidade
visual do [design system VILLA](../../gerar-pbix/references/design-system-villa.md)
(mesma paleta usada na skill `gerar-pbix`: header/título `#15314F`, borda
`#E5E9F0`, radius `8D`).

**Isto é um cardápio, não uma substituição automática.** Cada função abaixo é
uma opção que a skill oferece ao gerar um visual NOVO — nunca sobrescreve um
visual já existente no projeto. Ao usar `gerar-visuais-pbir`, perguntar ao
usuário qual template aplicar (ou qual variação de cor/estilo) antes de
gerar, em vez de aplicar um padrão fixo por conta própria.

> **Nota de licenciamento**: existe um catálogo bem mais amplo (54 exemplos)
> no plugin `data-goblin/power-bi-agentic-development` (skill `pbir-format`),
> mas esse repositório é GPL-3.0 e o nosso não tem licença declarada — por
> isso não copiamos os arquivos deles. Os templates abaixo vêm só de
> exemplos que nós mesmos geramos no Desktop.

## card_vc — cartão de KPI (`visualType: card`)

Uso: destacar 1 medida (ex.: "Inadimplência %").

```json
{
  "visual": {
    "visualType": "card",
    "query": { "queryState": { "Values": { "projections": [
      { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<NomeMedida>" } },
        "queryRef": "<TabelaMedidas>.<NomeMedida>", "nativeQueryRef": "<NomeCurto>" }
    ] } } },
    "objects": {
      "categoryLabels": [{ "properties": {
        "show": { "expr": { "Literal": { "Value": "false" } } },
        "fontSize": { "expr": { "Literal": { "Value": "9D" } } },
        "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#555555'" } } } } }
      } }],
      "labels": [{ "properties": {
        "fontSize": { "expr": { "Literal": { "Value": "24D" } } },
        "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } }
      } }]
    },
    "visualContainerObjects": {
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#F2F2F2'"}}}}}, "transparency": {"expr":{"Literal":{"Value":"0D"}}} } }],
      "border": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
      "title": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }]
    }
  }
}
```
Variações possíveis a oferecer: fundo branco `#FFFFFF` + borda `#E5E9F0` em
vez de `#F2F2F2` sem borda (ver `kpi_card_villa` do `gerar-pbix` pra layout
com barra de acento lateral colorida + ícone).

## donut_vc — rosca (`visualType: donutChart`)

Uso: distribuição de uma medida por categoria (ex.: alunos por status).

```json
{
  "visual": {
    "visualType": "donutChart",
    "query": { "queryState": {
      "Category": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } }, "queryRef": "<Tabela>.<Coluna>", "nativeQueryRef": "<Coluna>" }] },
      "Y": { "projections": [{ "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida>" } }, "queryRef": "<TabelaMedidas>.<Medida>", "nativeQueryRef": "<Medida>" }] }
    } },
    "objects": {
      "legend": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "position": {"expr":{"Literal":{"Value":"'BottomCenter'"}}}, "showTitle": {"expr":{"Literal":{"Value":"false"}}} } }],
      "labels": [{ "properties": { "labelStyle": { "expr": { "Literal": { "Value": "'Data value, percent of total'" } } } } }]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```

## bar_vc / column_vc — barras/colunas (`visualType: barChart` ou `columnChart`)

Mesmo `objects`/`visualContainerObjects` para os dois — só muda `visualType`
(`barChart` = horizontal, `columnChart` = vertical). Padrão: eixo de valor
totalmente oculto (`valueAxis.show: false`), rótulos de dados substituem a
escala.

```json
{
  "visual": {
    "visualType": "barChart",
    "query": { "queryState": {
      "Category": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } }, "queryRef": "<Tabela>.<Coluna>", "nativeQueryRef": "<Coluna>" }] },
      "Y": { "projections": [{ "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida>" } }, "queryRef": "<TabelaMedidas>.<Medida>", "nativeQueryRef": "<Medida>" }] }
    } },
    "objects": {
      "labels": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }],
      "categoryAxis": [{ "properties": { "showAxisTitle": { "expr": { "Literal": { "Value": "false" } } } } }],
      "valueAxis": [{ "properties": { "show": {"expr":{"Literal":{"Value":"false"}}}, "showAxisTitle": {"expr":{"Literal":{"Value":"false"}}} } }]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```

## line_vc — linha, com múltiplas séries (`visualType: lineChart`)

Uso: série temporal (ex.: Receita Prevista vs. Recebida por mês). Ao
contrário do bar/donut, aqui os eixos ficam **visíveis** (`categoryAxis.show`
e `valueAxis.show: true`) e a legenda vai no topo.

```json
{
  "visual": {
    "visualType": "lineChart",
    "query": { "queryState": {
      "Category": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<TabelaCalendario>" } }, "Property": "<ColunaEixoX>" } }, "queryRef": "<TabelaCalendario>.<ColunaEixoX>", "nativeQueryRef": "<ColunaEixoX>" }] },
      "Y": { "projections": [
        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida1>" } }, "queryRef": "<TabelaMedidas>.<Medida1>", "nativeQueryRef": "<Medida1>" },
        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida2>" } }, "queryRef": "<TabelaMedidas>.<Medida2>", "nativeQueryRef": "<Medida2>" }
      ] }
    } },
    "objects": {
      "categoryAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }],
      "valueAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }],
      "legend": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "position": {"expr":{"Literal":{"Value":"'Top'"}}} } }]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }]
    }
  }
}
```
Nota: aqui a borda ficou desligada (`border.show: false`) no exemplo real —
oferecer as duas opções (com/sem borda) ao usuário.

## table_vc — tabela (`visualType: tableEx`)

Uso: 1ª coluna = dimensão, demais colunas = medidas (linha de Total no
rodapé é automática quando há medidas).

```json
{
  "visual": {
    "visualType": "tableEx",
    "query": { "queryState": { "Values": { "projections": [
      { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<TabelaDimensao>" } }, "Property": "<ColunaDimensao>" } }, "queryRef": "<TabelaDimensao>.<ColunaDimensao>", "nativeQueryRef": "<Rótulo>" },
      { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida1>" } }, "queryRef": "<TabelaMedidas>.<Medida1>", "nativeQueryRef": "<Medida1>" }
    ] } } },
    "objects": {
      "grid": [{ "properties": { "gridVertical": {"expr":{"Literal":{"Value":"false"}}}, "rowPadding": {"expr":{"Literal":{"Value":"2D"}}} } }],
      "columnHeaders": [{ "properties": { "fontSize": {"expr":{"Literal":{"Value":"9D"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}}, "backColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}} } }],
      "values": [{ "properties": { "fontSize": { "expr": { "Literal": { "Value": "9D" } } } } }]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```

## shape_vc — forma/barra de destaque (`visualType: shape`)

Uso: barra de acento colorida (ex.: 5px de largura ao lado de um card), sem
consulta ao modelo (não tem `query`).

```json
{
  "visual": {
    "visualType": "shape",
    "objects": {
      "line": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
      "fill": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "fillColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'<CorAcento>'"}}}}}, "transparency": {"expr":{"Literal":{"Value":"0D"}}} } }],
      "rotation": [{ "properties": { "angle": { "expr": { "Literal": { "Value": "0D" } } } } }]
    },
    "visualContainerObjects": {
      "background": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }]
    }
  }
}
```

## textbox_vc — rótulo de texto (`visualType: textbox`)

Uso: label acima de um card/KPI, ou título solto na página.

```json
{
  "visual": {
    "visualType": "textbox",
    "objects": { "general": [{ "properties": { "paragraphs": [{ "textRuns": [
      { "value": "<Texto>", "textStyle": { "fontSize": "9pt", "color": "<CorAcento>", "fontWeight": "bold" } }
    ] }] } }] },
    "visualContainerObjects": {
      "background": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
      "padding": [{ "properties": { "top": {"expr":{"Literal":{"Value":"2D"}}}, "left": {"expr":{"Literal":{"Value":"6D"}}} } }]
    }
  }
}
```
Nota de unidade: `textbox` usa string com unidade explícita (`"9pt"`), ao
contrário dos outros visuais que usam sufixo `D` (`"9D"`) — ver
[design-system-villa.md](../../gerar-pbix/references/design-system-villa.md).

## Ainda pendente — sem exemplo real nosso ainda

Estes tipos estão no mapa de portabilidade do `docs/roadmap.md` mas **ainda
não foram gerados no Desktop por nós** — não inventar o JSON a partir de
documentação de terceiros; gerar um exemplo mínimo no Desktop primeiro,
salvar, e só então documentar o padrão aqui (mesma disciplina usada pros
tipos acima):

- `matrix_vc` (`visualType: pivotTable` no PBIR — nome diferente do rótulo
  "Matriz" da UI)
- `gauge_vc` (`visualType: gauge`)
- `slicer_vc` (`visualType: slicer` — variantes dropdown/lista/avançado)
- `combo_vc` (`visualType: comboChart`)
- `area_vc` (`visualType: areaChart` ou `stackedAreaChart`)
- `nav_button_vc` (botão de navegação — `visualType: actionButton` no PBIR)
- `image_vc` (`visualType: image`, + `StaticResources/` pro arquivo)
