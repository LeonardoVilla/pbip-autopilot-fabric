# Design System — padrão visual dos painéis

Extraído de um painel real em produção (Painel de Licenças MXM, ago/2026,
44 visuais / 4 páginas). Todos os valores abaixo foram aplicados à mão no
Power BI Desktop e depois lidos do PBIR — ou seja, **são o que o Desktop
grava**, não teoria.

Use como padrão ao gerar visuais novos, salvo pedido em contrário do usuário.

---

## 1. Paleta

| Papel | Hex | Onde usar |
|---|---|---|
| Azul institucional | `#15314F` | títulos, valores neutros, série principal |
| Verde | `#1BAF7A` | valores positivos, saldo disponível |
| Vermelho | `#C0392B` | risco / alerta (bloqueado, desligado) |
| Laranja | `#E67E22` | atenção intermediária |
| Cinza texto | `#555555` | rótulos de categoria, subtítulos |
| Cinza fundo | `#F2F2F2` | fundo de card neutro |
| Branco | `#FFFFFF` | fundo de gráfico/tabela |
| Borda | `#E6E6E6` | borda padrão (tema global) |

### Fundos semânticos de card
Sempre pareados com a cor do valor:

| Situação | Valor | Fundo |
|---|---|---|
| Neutro | `#15314F` | `#F2F2F2` |
| Positivo | `#1BAF7A` | `#EAF7F1` |
| Atenção | `#E67E22` | `#FEF5E7` |
| Risco | `#C0392B` | `#FDEDEC` |

---

## 2. Tema global (`customTheme`)

Arquivo em `StaticResources/RegisteredResources/<Nome>.json`, registrado
em `report.json` › `themeCollection.customTheme` **e** em
`resourcePackages` (tipo `RegisteredResources`, `type: CustomTheme`).

```json
{
  "name": "Custom",
  "visualStyles": {
    "*": {
      "*": {
        "border": [
          { "show": true, "color": { "solid": { "color": "#e6e6e6" } }, "radius": 5 }
        ]
      }
    },
    "page": {
      "*": {
        "background": [
          { "color": { "solid": { "color": "#f0e199" } }, "transparency": 90 }
        ]
      }
    }
  }
}
```

> **Borda arredondada (`radius: 5`) vem do tema, não do visual.** Por isso
> cada visual grava `border.show: false` no container — a borda visível é a
> do tema. Não "corrigir" isso.

> ⚠️ **Nunca remover `resourcePackages` do `report.json`.** Ele registra o
> tema custom. O lint `PBIP_THEME_FILE_MISSING` acusa erro quando o arquivo
> apontado não existe em `StaticResources/` — a correção é **criar/manter o
> arquivo**, não apagar a referência.

---

## 3. Tipografia

| Uso | Tamanho | Cor | Peso |
|---|---|---|---|
| Título de página | `16pt` | `#15314f` | bold |
| Subtítulo de página | `10pt` | `#555555` | normal |
| Nota / legenda | `9pt` ou `8pt` | `#555555` | normal |
| Título de visual | `12D` (11D em slicer) | `#15314F` | — |
| Valor de card | `28D` (30D em destaque) | semântica | — |
| Rótulo de card | `9D` | `#555555` | — |
| Texto de tabela/slicer | `9D` | — | — |

> Textbox usa `pt` (string); propriedades de visual usam `D` (double).

---

## 4. Card (KPI)

```json
"objects": {
  "categoryLabels": [{ "properties": {
    "show":     { "expr": { "Literal": { "Value": "true" } } },
    "fontSize": { "expr": { "Literal": { "Value": "9D" } } },
    "color":    { "solid": { "color": { "expr": { "Literal": { "Value": "'#555555'" } } } } }
  }}],
  "labels": [{ "properties": {
    "fontSize": { "expr": { "Literal": { "Value": "28D" } } },
    "color":    { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } }
  }}]
},
"visualContainerObjects": {
  "background": [{ "properties": {
    "show":         { "expr": { "Literal": { "Value": "true" } } },
    "color":        { "solid": { "color": { "expr": { "Literal": { "Value": "'#F2F2F2'" } } } } },
    "transparency": { "expr": { "Literal": { "Value": "0D" } } }
  }}],
  "border":     [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
  "dropShadow": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
  "title":      [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }]
}
```

Card **não usa título** — o rótulo vem de `categoryLabels` (o
`nativeQueryRef` da projeção). Sem sombra.

**Grid observado:** altura `105–110`, largura `195` (6 cards) ou `236`
(5 cards), `y = 88`, espaçamento de `12px` (passo 207 ou 248).

---

## 5. Gráficos (bar / column / clusteredBar)

```json
"objects": {
  "categoryAxis": [{ "properties": { "showAxisTitle": { "expr": { "Literal": { "Value": "false" } } } } }],
  "valueAxis":    [{ "properties": {
      "show":          { "expr": { "Literal": { "Value": "false" } } },
      "showAxisTitle": { "expr": { "Literal": { "Value": "false" } } }
  }}],
  "labels": [{ "properties": { "show": { "expr": { "Literal": { "Value": "true" } } } } }]
},
"visualContainerObjects": {
  "title": [{ "properties": {
    "show":      { "expr": { "Literal": { "Value": "true" } } },
    "text":      { "expr": { "Literal": { "Value": "'Título do gráfico'" } } },
    "fontSize":  { "expr": { "Literal": { "Value": "12D" } } },
    "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } }
  }}],
  "background": [{ "properties": {
    "show":  { "expr": { "Literal": { "Value": "true" } } },
    "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } } } }
  }}]
}
```

Regra do padrão: **eixo de valor oculto + rótulos de dado visíveis**. O
número aparece na barra, não no eixo — menos ruído.

Títulos de eixo sempre ocultos (a categoria já se explica).

### Série múltipla
`legend`: `show: true`, `position: 'Top'`, `showTitle: false`.
Cor por série via `dataPoint.fill` com `selector.metadata` = queryRef da
medida.

---

## 6. Slicer

```json
"objects": {
  "data":   [{ "properties": { "mode": { "expr": { "Literal": { "Value": "'Dropdown'" } } } } }],
  "header": [{ "properties": { "show": { "expr": { "Literal": { "Value": "false" } } } } }],
  "items":  [{ "properties": { "textSize": { "expr": { "Literal": { "Value": "9D" } } } } }]
},
"visualContainerObjects": {
  "title": [{ "properties": {
    "show":      { "expr": { "Literal": { "Value": "true" } } },
    "text":      { "expr": { "Literal": { "Value": "'Rótulo'" } } },
    "fontSize":  { "expr": { "Literal": { "Value": "11D" } } },
    "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } }
  }}]
}
```

Modo **Dropdown** (economiza espaço), cabeçalho nativo **oculto** — o rótulo
vem do título do container, `11D`.

---

## 7. Tabela (`tableEx`)

```json
"objects": {
  "values":      [{ "properties": { "fontSize": { "expr": { "Literal": { "Value": "9D" } } } } }],
  "columnWidth": [{ "properties": { "value": { "expr": { "Literal": { "Value": "130D" } } } } }]
},
"visualContainerObjects": {
  "title": [{ "properties": {
    "show":      { "expr": { "Literal": { "Value": "true" } } },
    "text":      { "expr": { "Literal": { "Value": "'Detalhe — ...'" } } },
    "fontSize":  { "expr": { "Literal": { "Value": "12D" } } },
    "fontColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#15314F'" } } } } },
    "titleWrap": { "expr": { "Literal": { "Value": "true" } } }
  }}]
}
```

---

## 8. Layout de página

Canvas `1280 x 720`, `displayOption: FitToPage`.

```
y=12    título da página (16pt bold)
y=48    subtítulo (10pt #555555)
y=88    faixa de KPIs (altura 105–110)
y=210   gráficos + slicers (altura ~250)
y=470   tabela de detalhe (altura ~230)
```

Margem lateral `20px`, gutter `12px`. Largura útil `1240`.

---

## 9. Convenções de escrita (PBIR)

- Valor **string** em `Literal.Value` leva aspas simples internas:
  `"'#15314F'"`, `"'Top'"`.
- Valor **numérico** leva sufixo `D`: `"12D"`, `"0D"`.
- Booleano é string sem aspas internas: `"true"`, `"false"`.
- Cor: sempre `{"solid": {"color": {"expr": {"Literal": {"Value": "'#RRGGBB'"}}}}}`.
- Título de página/subtítulo são **textbox**, não `title` de página.

---

## 10. Armadilhas confirmadas em campo

1. **O Desktop reescreve o TMDL ao salvar.** Criar consulta pelo Power Query
   num projeto gerado pode duplicar tabela (`MXM (2)`) e **apagar as
   declarações de coluna** da original. Preferir editar o TMDL direto.
2. **Tipos numéricos voltam para `double`.** Oracle devolve `NUMBER`
   genérico; o Desktop grava `double` e o lint acusa `META_AVOID_FLOAT`.
   Reaplicar `int64`/`decimal` após cada salvamento do Desktop.
3. **Relacionamento auto-detectado.** Ao remover uma tabela, o Desktop deixa
   `relationship AutoDetected_<guid>` órfão → o projeto **não abre**.
   Limpar `relationships.tmdl` junto.
4. **`resourcePackages` não é lixo** — ver seção 2.
5. **Preservar formatação do usuário.** Ao editar visuais já ajustados à
   mão, alterar só `query`/`position`; nunca sobrescrever `objects` e
   `visualContainerObjects` inteiros.
