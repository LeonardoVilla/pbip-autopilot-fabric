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

## grid() — posicionamento em grade

Herdado direto do `gerar-pbix` (`references/template-script.md`) — é
matemática pura de layout, não depende do formato do arquivo (`.pbix` ou
PBIR usam o mesmo conceito de `x`/`y`/`w`/`h` no `position` do visual), por
isso não precisou de teste no Desktop pra portar.

```python
def grid(cols, rows, area_x=0, area_y=0, area_w=1280, area_h=720, gap=10):
    """
    Gera uma lista de (x, y, w, h) para uma grade cols×rows dentro de area_*.
    Uso:
        cells = grid(4, 1, area_x=10, area_y=116, area_w=1260, area_h=90)
        # cells[0] = (x, y, w, h) do primeiro visual da grade
    """
    cell_w = (area_w - gap * (cols - 1)) / cols
    cell_h = (area_h - gap * (rows - 1)) / rows
    cells = []
    for r in range(rows):
        for c in range(cols):
            cx = area_x + c * (cell_w + gap)
            cy = area_y + r * (cell_h + gap)
            cells.append((round(cx), round(cy), round(cell_w), round(cell_h)))
    return cells
```

No PBIR, o resultado de cada célula vai direto no `position` do
`visual.json`:
```json
"position": { "x": <cx>, "y": <cy>, "z": 0, "width": <cw>, "height": <ch>, "tabOrder": <N> }
```
(no `.pbix` legado era `{"x":cx,"y":cy,"z":z,"width":cw,"height":ch,"tabOrder":tab}`
dentro de `layouts[0].position` — mesmos campos, só o invólucro muda.)

## Filtros de página/visual com valor fixo (sem slicer)

Equivalente ao `equals_filter()` + `apply_page_filters()`/
`apply_visual_filters()` do `gerar-pbix`. Testado no Desktop (jul/2026):
aplicar um filtro de página (painel Filtros → campo → fixar valor) grava
em `page.json` um `filterConfig.filters[]` com **a mesma estrutura interna**
do formato legado `.pbix` (`From`/`Where`/`Condition`/`In`/`Values`) —
**a única mudança real é o invólucro**: no PBIR é objeto JSON nativo dentro
de `filterConfig`, não mais uma string serializada dentro de `"filters"`.

```json
{
  "filterConfig": {
    "filters": [
      {
        "name": "<slug-20-chars>",
        "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } },
        "type": "Categorical",
        "filter": {
          "Version": 2,
          "From": [ { "Name": "<alias-curto>", "Entity": "<Tabela>", "Type": 0 } ],
          "Where": [
            { "Condition": { "In": {
              "Expressions": [ { "Column": { "Expression": { "SourceRef": { "Source": "<alias-curto>" } }, "Property": "<Coluna>" } } ],
              "Values": [ [ { "Literal": { "Value": "'<valor>'" } } ] ]
            } } }
          ]
        },
        "howCreated": "User"
      }
    ]
  }
}
```

Onde aplicar:
- **Página inteira**: `filterConfig` é propriedade de `page.json` (nível
  raiz, irmã de `displayName`/`height`/`width`).
- **Um visual específico**: mesmo `filterConfig`, mas dentro do
  `visual.json` daquele visual (irmão de `visual`, mesmo padrão já visto
  no `filterConfig` do `slicer_vc`).

`Values` aceita mais de um literal por lista pra `IN (a, b, c)` (múltiplos
valores selecionados); pra valor numérico, omitir as aspas simples do
`Literal.Value` (mesma regra do `equals_filter` legado — `is_string`).

## kpi_card_villa — composto de KPI (barra + label + número + ícone)

Não é um tipo de visual novo — é a **composição** de 4 visuais já
validados acima (`shape_vc` + `textbox_vc` + `card_vc` + `image_vc`
opcional), portada 1:1 do preset `kpi_card_villa()` do `gerar-pbix`
(mesmos offsets relativos). Testado no Desktop (jul/2026): renderizou
corretamente.

Receita (todos compartilham o mesmo `x`,`y` de origem do card, `w`/`h` do
card definem a caixa toda):

| Peça | Posição relativa | z | Conteúdo |
|---|---|---|---|
| `shape_vc` (barra de acento) | `x, y, 5, h` | `z+5` | `fillColor` = cor do acento |
| `textbox_vc` (label) | `x+12, y+10, w-16, 30` | `z+10` | texto = nome do KPI, `9pt` bold, cor = acento |
| `card_vc` (número) | `x, y, w, h` | `z` (base, atrás dos outros) | medida DAX, `labels.fontSize: 26D`, cor `#15314F` |
| `image_vc` (ícone, opcional) | `x+8, y+34, 56, 50` | `z+15` | ícone do KPI |

O card fica **atrás** (menor z) e ocupa a área toda como "moldura" (fundo
branco + borda + número grande); a barra de acento e o label ficam por
cima, sobrepostos só na fatia onde não colidem visualmente com o número.
`w`/`h` recomendados: ~200-240 × ~90-100 (mesma proporção do preset
`.pbix` original).

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

## gauge_vc — medidor (`visualType: gauge`)

Uso: mostrar uma medida percentual/numérica contra uma escala 0-100 (ou
min/max implícito). Testado no Desktop (jul/2026): renderizou a escala
0,0%-100,0% e o valor central corretamente só com a role `Y`.

```json
{
  "visual": {
    "visualType": "gauge",
    "query": { "queryState": { "Y": { "projections": [
      { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida>" } },
        "queryRef": "<TabelaMedidas>.<Medida>", "nativeQueryRef": "<Medida>" }
    ] } } },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```
Não testamos ainda `MinValue`/`MaxValue`/`TargetValue` (roles opcionais pra
customizar a escala) — o exemplo acima usa só o default 0-100 do Desktop.

## slicer_vc — filtro em visual (`visualType: slicer`)

Uso: filtro interativo por coluna. Testado no Desktop (jul/2026): renderizou
como lista (formato padrão do Desktop quando não se especifica `objects`).
**Descoberta ao interagir no Desktop**: ao mover/redimensionar o slicer, o
Desktop regravou o arquivo e revelou dois detalhes que nosso JSON inicial
não tinha:

- `objects.general: [{ "properties": {} }]` — presente mesmo vazio.
- **`filterConfig` é irmão de `visual`** (não fica dentro dele) — repete a
  referência do campo com `type: "Categorical"` e um `name` (GUID/slug
  próprio, diferente do `queryRef`). Sem isso o slicer ainda funciona, mas
  o Desktop o adiciona sozinho ao salvar — incluir já formado evita um
  round-trip de gravação.
- `$schema` da versão `visualContainer` subiu de `2.3.0` pra `2.10.0` só
  neste arquivo ao ser regravado — os outros visuais do projeto continuam
  em `2.3.0` e abrem normalmente; não force o bump manualmente, deixe o
  Desktop decidir quando regravar.

```json
{
  "visual": {
    "visualType": "slicer",
    "query": { "queryState": { "Values": { "projections": [
      { "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } },
        "queryRef": "<Tabela>.<Coluna>", "nativeQueryRef": "<Coluna>" }
    ] } } },
    "objects": { "general": [{ "properties": {} }] },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}} } }]
    }
  },
  "filterConfig": {
    "filters": [
      { "name": "<slug-ou-guid-proprio>",
        "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } },
        "type": "Categorical" }
    ]
  }
}
```

Ainda não testamos como forçar modo **dropdown** especificamente (o design
system `gerar-pbix` usa dropdown, o teste acima renderizou como lista) —
precisa gerar um dropdown no Desktop e comparar a propriedade exata que
muda (provável candidato: mais alguma coisa dentro de `objects.general`
ou um objeto novo tipo `objects.selection`/`data`, ainda não confirmado).

## matrix_vc — matriz (`visualType: pivotTable`)

Uso: agrupamento hierárquico com totais automáticos. Nome interno no PBIR é
`pivotTable` — **diferente do rótulo "Matriz" da UI**, fácil de errar.
Testado no Desktop (jul/2026): renderizou corretamente, incluindo a linha
de **Total** no rodapé gerada automaticamente pelo Desktop (não precisa
declarar no JSON).

```json
{
  "visual": {
    "visualType": "pivotTable",
    "query": { "queryState": {
      "Rows": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<TabelaDimensao>" } }, "Property": "<ColunaDimensao>" } }, "queryRef": "<TabelaDimensao>.<ColunaDimensao>", "nativeQueryRef": "<ColunaDimensao>" }] },
      "Values": { "projections": [
        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida1>" } }, "queryRef": "<TabelaMedidas>.<Medida1>", "nativeQueryRef": "<Medida1>" },
        { "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida2>" } }, "queryRef": "<TabelaMedidas>.<Medida2>", "nativeQueryRef": "<Medida2>" }
      ] }
    } },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```
Não testamos ainda `Columns` (pivot de coluna, além do agrupamento de
linha) — o exemplo acima só usa `Rows` + `Values`.

## area_vc — área (`visualType: areaChart`)

Uso: série temporal com preenchimento, mesma estrutura de query do
`line_vc`. Testado no Desktop (jul/2026): renderizou corretamente com
`categoryAxis`/`valueAxis` visíveis.

```json
{
  "visual": {
    "visualType": "areaChart",
    "query": { "queryState": {
      "Category": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<TabelaCalendario>" } }, "Property": "<ColunaEixoX>" } }, "queryRef": "<TabelaCalendario>.<ColunaEixoX>", "nativeQueryRef": "<ColunaEixoX>" }] },
      "Y": { "projections": [{ "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<Medida>" } }, "queryRef": "<TabelaMedidas>.<Medida>", "nativeQueryRef": "<Medida>" }] }
    } },
    "objects": {
      "categoryAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }],
      "valueAxis": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }]
    },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```
`stackedAreaChart` (área empilhada, múltiplas séries) ainda não testado —
provável mesma estrutura de `Y` com múltiplas projeções, como no `line_vc`.

## combo_vc — combo linha+coluna (`visualType: lineClusteredColumnComboChart`)

Uso: duas medidas de escalas diferentes no mesmo gráfico (ex.: contagem em
coluna + percentual em linha, eixo Y secundário). **`"comboChart"` NÃO é o
nome nativo** — testado e confirmado que o Desktop recusa esse valor
("Para ver este visual personalizado, adicione-o a este relatório
primeiro"). O nome certo é `lineClusteredColumnComboChart` (Linha e coluna
agrupada) — testado no Desktop (jul/2026), renderizou com eixo Y duplo e
legenda no topo automaticamente, sem precisar declarar nada de eixo extra.

```json
{
  "visual": {
    "visualType": "lineClusteredColumnComboChart",
    "query": { "queryState": {
      "Category": { "projections": [{ "field": { "Column": { "Expression": { "SourceRef": { "Entity": "<Tabela>" } }, "Property": "<Coluna>" } }, "queryRef": "<Tabela>.<Coluna>", "nativeQueryRef": "<Coluna>" }] },
      "Y": { "projections": [{ "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<MedidaColuna>" } }, "queryRef": "<TabelaMedidas>.<MedidaColuna>", "nativeQueryRef": "<MedidaColuna>" }] },
      "Y2": { "projections": [{ "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "<TabelaMedidas>" } }, "Property": "<MedidaLinha>" } }, "queryRef": "<TabelaMedidas>.<MedidaLinha>", "nativeQueryRef": "<MedidaLinha>" }] }
    } },
    "visualContainerObjects": {
      "title": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "text": {"expr":{"Literal":{"Value":"'<Título>'"}}}, "fontColor": {"solid":{"color":{"expr":{"Literal":{"Value":"'#15314F'"}}}}}, "fontSize": {"expr":{"Literal":{"Value":"12D"}}} } }],
      "background": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#FFFFFF'"}}}}} } }],
      "border": [{ "properties": { "show": {"expr":{"Literal":{"Value":"true"}}}, "color": {"solid":{"color":{"expr":{"Literal":{"Value":"'#E5E9F0'"}}}}}, "radius": {"expr":{"Literal":{"Value":"8D"}}} } }]
    }
  }
}
```
`lineStackedColumnComboChart` (Linha e coluna empilhada) ainda não
testado — mesma estrutura de roles, provável.

## image_vc — imagem (`visualType: image`)

Uso: ícone/logo a partir de um arquivo registrado em `StaticResources/`.
Testado no Desktop (jul/2026): renderizou corretamente.

Duas partes obrigatórias:

1. **Arquivo físico** em `<Report>/StaticResources/RegisteredResources/<arquivo>`
2. **Declaração em `report.json`** (`resourcePackages`, nível do relatório —
   não do visual):
   ```json
   {
     "name": "RegisteredResources",
     "type": "RegisteredResources",
     "items": [ { "name": "<arquivo>", "path": "<arquivo>", "type": "Image" } ]
   }
   ```

```json
{
  "visual": {
    "visualType": "image",
    "objects": {
      "image": [{ "properties": {
        "sourceFile": { "image": {
          "name": { "expr": { "Literal": { "Value": "'<arquivo>'" } } },
          "url": { "expr": { "ResourcePackageItem": {
            "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": "<arquivo>"
          } } },
          "scaling": { "expr": { "Literal": { "Value": "'Normal'" } } }
        } },
        "fit": { "expr": { "Literal": { "Value": "'Fit'" } } }
      } }]
    },
    "visualContainerObjects": {
      "background": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }]
    }
  }
}
```
Estrutura idêntica à usada no `.pbix` legado (`gerar-pbix`/`image_vc()`) —
só muda o invólucro (visual.json em vez de layout embutido no ZIP).

## nav_button_vc — botão de navegação (`visualType: actionButton`)

Uso: botão com ícone e/ou texto que executa uma ação (voltar, ir pra
página, limpar filtros). **Primeira tentativa (chute) falhou** — havíamos
colocado a ação em `objects.visualLink`, e o botão renderizou vazio, sem
preenchimento/texto/ação. Corrigido gerando de verdade pela galeria
**Inserir → Botões** do Desktop (`"howCreated": "InsertVisualButton"` no
JSON resultante confirma a origem):

```json
{
  "visual": {
    "visualType": "actionButton",
    "objects": {
      "icon": [
        { "properties": { "shapeType": { "expr": { "Literal": { "Value": "'back'" } } } }, "selector": { "id": "default" } }
      ]
    },
    "visualContainerObjects": {
      "visualLink": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "type": { "expr": { "Literal": { "Value": "'Back'" } } }
          }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  },
  "howCreated": "InsertVisualButton"
}
```

**Achado principal**: a ação do botão (`visualLink`) fica em
**`visual.visualContainerObjects.visualLink`** — não em `visual.objects`
(nosso chute original). O ícone (`objects.icon[].properties.shapeType`) e o
texto (`objects.text[].properties.text`) são independentes da ação.

`visualLink.properties.type` confirmados no Desktop: `'Back'` (botão
Voltar) e `'ClearAllSlicers'` (botão Limpar segmentações — nesse caso vem
também `tooltipPlaceholderText`). **`'PageNavigation'` com
`navigationSection: '<nome-da-página>'` ainda não confirmado** — é a
inferência lógica pro botão "Ir para página" da mesma galeria, mas não foi
testado; gerar um antes de confiar cegamente nessa forma.

Texto com múltiplos estados (base + `selector: {"id": "default"}`) — o
botão "Limpar segmentações" tem duas entradas em `objects.text[]`, uma sem
`selector` (estado base) e outra com `selector.id: "default"` carregando o
texto/alinhamento de fato. Replicar essa duplicação ao gerar botões com
texto.
