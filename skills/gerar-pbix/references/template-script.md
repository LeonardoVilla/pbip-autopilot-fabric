# Template de Script Python — Gerador de .pbix

Script completo e validado para gerar arquivos `.pbix` do Power BI. Copie e adapte para cada projeto.

## Dependências

Apenas biblioteca padrão do Python: `json`, `zipfile`, `os`, `copy`, `zlib`, `random`, `string`.

---

## Estrutura completa do script

```python
"""
Gerador de .pbix — <Nome do Projeto>
Template: <caminho do .pbix template>
Fonte: <caminho do .xlsx ou banco>
"""

import json, zipfile, os, copy, zlib, random, string

# ─── Utilitários ─────────────────────────────────────────────────────────────

def uid():
    return ''.join(random.choices(string.hexdigits[:16], k=20))

# OBRIGATÓRIO: alias fixos por tabela — NUNCA usar table[0].lower()
# Ajuste para as tabelas do seu projeto
TABLE_ALIAS = {
    "NOME_TABELA_1": "t1",
    "NOME_TABELA_2": "t2",
    # tabelas com espaços/acentos precisam de alias explícito:
    # "TABELA COM ESPAÇO ": "ts",  # inclua o espaço final se ele existir no nome
}

def get_src(table):
    return TABLE_ALIAS.get(table, table[:2].lower().replace(' ', '_'))

def pos(x, y, w, h, z=0, tab=0):
    return {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab}

def vc(x, y, w, h, cfg, z=0, tab=0):
    return {
        "x": x, "y": y, "z": z, "width": w, "height": h,
        "config": json.dumps(cfg, ensure_ascii=False, separators=(',', ':')),
        "filters": "[]", "tabOrder": tab
    }

# ─── Referências de campo: coluna agregada OU medida DAX ─────────────────────
# Toda função de visual abaixo aceita, no lugar de um nome de campo simples,
# um valor construído por measure_ref(). Isso permite usar medidas já criadas
# no modelo (ex: no DataModel do template) em vez de agregações de coluna crua.
#
#   card_vc(x, y, w, h, "TABELA", "Campo", "Label")               # coluna + agg
#   card_vc(x, y, w, h, "TABELA", measure_ref("Minha Medida"), "Label")  # medida
#
# A diferença interna: Column+Aggregation vira Measure, e a Function/agg
# deixa de ser usada (medidas já carregam sua própria agregação no DAX).

class MeasureRef:
    """Marca um nome de campo como referência a uma medida DAX, não uma coluna."""
    __slots__ = ("name",)
    def __init__(self, name):
        self.name = name

def measure_ref(name):
    return MeasureRef(name)

def _is_measure(field):
    return isinstance(field, MeasureRef)

def _select_entry(table, src, field, agg, native_name):
    """
    Monta a entrada 'Select' do prototypeQuery para um campo.
    - Se field for measure_ref(...): gera {"Measure": {...}} (sem Aggregation).
    - Se field for string e agg for None: gera {"Column": {...}} (sem agregação — para eixos/categoria).
    - Se field for string e agg for definido: gera {"Aggregation": {"Column": {...}}}.
    Retorna (select_entry, query_ref, native_ref).
    """
    agg_map = {"Count": 3, "CountNonNull": 5, "Sum": 0, "Max": 4, "Min": 2, "Average": 1}
    if _is_measure(field):
        prop = field.name
        query_ref = f"{table}.{prop}"
        entry = {
            "Measure": {
                "Expression": {"SourceRef": {"Source": src}},
                "Property": prop
            },
            "Name": query_ref,
            "NativeReferenceName": native_name or prop
        }
        return entry, query_ref, native_name or prop
    if agg is None:
        query_ref = f"{table}.{field}"
        entry = {
            "Column": {
                "Expression": {"SourceRef": {"Source": src}},
                "Property": field
            },
            "Name": query_ref,
            "NativeReferenceName": native_name or field
        }
        return entry, query_ref, native_name or field
    fn = agg_map.get(agg, 5)
    query_ref = f"{agg}({table}.{field})"
    entry = {
        "Aggregation": {
            "Expression": {"Column": {
                "Expression": {"SourceRef": {"Source": src}},
                "Property": field
            }},
            "Function": fn
        },
        "Name": query_ref,
        "NativeReferenceName": native_name or f"{agg} de {field}"
    }
    return entry, query_ref, native_name or f"{agg} de {field}"

# ─── Visuais ─────────────────────────────────────────────────────────────────

def shape_vc(x, y, w, h, color="#15314F", z=0, tab=0):
    """Retângulo colorido de fundo."""
    name = uid()
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "shape",
            "drillFilterOtherVisuals": True,
            "objects": {
                "line": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "fill": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "fillColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{color}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }}],
                "rotation": [{"properties": {"angle": {"expr": {"Literal": {"Value": "0D"}}}}}]
            },
            "vcObjects": {"background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]}
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def textbox_vc(x, y, w, h, text, size="10pt", color="#ffffff", bold=False, z=0, tab=0, pad_top=4, pad_left=8):
    """Caixa de texto estático."""
    name = uid()
    style = {"fontSize": size, "color": color}
    if bold:
        style["fontWeight"] = "bold"
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "textbox",
            "drillFilterOtherVisuals": True,
            "objects": {"general": [{"properties": {"paragraphs": [
                {"textRuns": [{"value": text, "textStyle": style}]}
            ]}}]},
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "padding": [{"properties": {
                    "top": {"expr": {"Literal": {"Value": f"{pad_top}D"}}},
                    "left": {"expr": {"Literal": {"Value": f"{pad_left}D"}}}
                }}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def card_vc(x, y, w, h, table, field, label, agg="CountNonNull", z=0, tab=0):
    """
    Card KPI. Fundo cinza claro, número escuro — legível em qualquer fundo.
    agg: "CountNonNull" | "Count" | "Sum" | "Max" | "Min"
    field aceita string (coluna) ou measure_ref("Nome da Medida").
    """
    name = uid()
    src = get_src(table)
    select_entry, ref, native_name = _select_entry(table, src, field, agg, label)
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": ref}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [select_entry]
            },
            "columnProperties": {ref: {"displayName": label}},
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryLabels": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#555555'"}}}}}
                }}],
                "labels": [{"properties": {
                    "fontSize": {"expr": {"Literal": {"Value": "28D"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}]
            },
            "vcObjects": {
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F2F2F2'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def donut_vc(x, y, w, h, table, cat_field, val_field, title="", agg="CountNonNull", z=0, tab=0):
    """Gráfico de rosca. cat_field = categoria (eixo), val_field = valor agregado (ou measure_ref(...))."""
    name = uid()
    src = get_src(table)
    val_entry, val_ref, _ = _select_entry(table, src, val_field, agg, None)
    cat_entry, cat_ref, _ = _select_entry(table, src, cat_field, None, None)
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "donutChart",
            "projections": {
                "Y": [{"queryRef": val_ref}],
                "Category": [{"queryRef": cat_ref, "active": True}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [val_entry, cat_entry]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "legend": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "position": {"expr": {"Literal": {"Value": "'BottomCenter'"}}},
                    "showTitle": {"expr": {"Literal": {"Value": "false"}}}
                }}],
                "labels": [{"properties": {
                    "labelStyle": {"expr": {"Literal": {"Value": "'Data value, percent of total'"}}}
                }}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12D"}}}
                }}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "border": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E5E9F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def bar_vc(x, y, w, h, table, cat_field, val_field, title="", agg="CountNonNull",
           orientation="horizontal", z=0, tab=0):
    """
    Gráfico de barras ou colunas.
    orientation: "horizontal" → barChart | "vertical" → columnChart
    val_field aceita measure_ref(...).
    """
    name = uid()
    src = get_src(table)
    val_entry, val_ref, _ = _select_entry(table, src, val_field, agg, None)
    cat_entry, cat_ref, _ = _select_entry(table, src, cat_field, None, None)
    vtype = "barChart" if orientation == "horizontal" else "columnChart"
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": vtype,
            "projections": {
                "Y": [{"queryRef": val_ref}],
                "Category": [{"queryRef": cat_ref, "active": True}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [val_entry, cat_entry]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "categoryAxis": [{"properties": {
                    "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}
                }}],
                "valueAxis": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}},
                    "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}
                }}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12D"}}}
                }}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "border": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E5E9F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def grouped_bar_vc(x, y, w, h, dim_table, dim_field, measures, title="", z=0, tab=0):
    """
    Colunas agrupadas (clusteredColumnChart) com VÁRIAS medidas como séries.
    Validado em produção: legenda no topo, eixo Y oculto, categoria = dimensão.
    measures: lista de nomes de medida em _Medidas (ex: ["Admitidos","Demitidos","Transferidos"]).
    """
    src_dim = get_src(dim_table)
    cat_e, cat_ref, _ = _select_entry(dim_table, src_dim, dim_field, None, None)
    select = [cat_e]
    y_proj = []
    froms = [{"Name": src_dim, "Entity": dim_table, "Type": 0}]
    seen = {dim_table}
    for mname in measures:
        m_e, m_ref, m_src = measure_entry("_Medidas", mname)
        select.append(m_e)
        y_proj.append({"queryRef": m_ref})
        if "_Medidas" not in seen:
            froms.append({"Name": m_src, "Entity": "_Medidas", "Type": 0}); seen.add("_Medidas")
    cfg = {
        "name": uid(), "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "clusteredColumnChart",
            "projections": {"Category": [{"queryRef": cat_ref, "active": True}], "Y": y_proj},
            "prototypeQuery": {"Version": 2, "From": froms, "Select": select},
            "drillFilterOtherVisuals": True, "hasDefaultSort": True,
            "objects": {
                "legend": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "position": {"expr": {"Literal": {"Value": "'Top'"}}}}}],
                "categoryAxis": [{"properties": {"showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}},
                    "showAxisTitle": {"expr": {"Literal": {"Value": "false"}}}}}],
                "labels": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]},
            "vcObjects": {
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12D"}}}}}],
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E5E9F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}}}}]}}}
    return vc(x, y, w, h, cfg, z, tab)

def slicer_vc(x, y, w, h, table, field, label=None, z=0, tab=0):
    """
    Filtro dropdown com a formatação validada em produção (painel VILLA).
    label: rótulo curto no header (default = nome do campo). Use para evitar
    nomes longos truncados, ex: label="Tipo de Contrato" para CLASSIFICACAO_CONTRATO.
    Para uma FAIXA de slicers alinhada e distribuída, gere as posições com grid():
        for (sx,sy,sw,sh),(t,f,l) in zip(
                grid(len(slicers),1, area_x=14, area_y=64, area_w=1252, area_h=42, gap=8), slicers):
            vcs.append(slicer_vc(sx,sy,sw,sh, t, f, label=l))
    Assim os slicers ficam com largura uniforme, sem colar nas bordas, e alinhados
    (x inicial e final) com os gráficos abaixo (que começam em x=14 e vão até 1266).
    Altura recomendada ~42px (menor corta o dropdown).
    """
    name = uid()
    src = get_src(table)
    col_ref = f"{table}.{field}"
    header_text = label if label is not None else field
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "slicer",
            "projections": {"Values": [{"queryRef": col_ref, "active": True}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [{"Column": {
                    "Expression": {"SourceRef": {"Source": src}},
                    "Property": field
                }, "Name": col_ref, "NativeReferenceName": field}]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "selection": [{"properties": {
                    "selectAllCheckboxEnabled": {"expr": {"Literal": {"Value": "false"}}},
                    "singleSelect": {"expr": {"Literal": {"Value": "false"}}}
                }}],
                "header": [{"properties": {
                    "text": {"expr": {"Literal": {"Value": f"'{header_text}'"}}},
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "textSize": {"expr": {"Literal": {"Value": "8D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": 0}}}}}
                }}],
                "items": [{"properties": {
                    "textSize": {"expr": {"Literal": {"Value": "8D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": -0.5}}}}},
                    "background": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": 0}}}}}
                }}]
            },
            "vcObjects": {
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }}],
                "title": [{"properties": {"titleWrap": {"expr": {"Literal": {"Value": "true"}}}}}],
                "padding": [{"properties": {
                    "top": {"expr": {"Literal": {"Value": "0D"}}},
                    "bottom": {"expr": {"Literal": {"Value": "0D"}}}
                }}],
                "border": [{"properties": {"width": {"expr": {"Literal": {"Value": "1D"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

# ─── Novos tipos de visual ────────────────────────────────────────────────────
# Seguem exatamente o mesmo padrão estrutural (singleVisual/projections/prototypeQuery)
# validado nos visuais acima. line_vc/area_vc reaproveitam o schema Category+Y de
# bar_vc/donut_vc (mesmo prototypeQuery, só muda visualType). table_vc foi extraído
# de um .pbix real (tableEx). gauge_vc foi adaptado de um gauge real de produção
# (formato PBIR) para o formato legado Report/Layout usado neste template.

def line_vc(x, y, w, h, table, cat_field, val_field, title="", agg="Sum", z=0, tab=0):
    """
    Gráfico de linha. Mesmo schema de bar_vc/donut_vc — Category (eixo X) + Y (valor).
    Útil para séries temporais. val_field aceita measure_ref(...).
    """
    name = uid()
    src = get_src(table)
    val_entry, val_ref, _ = _select_entry(table, src, val_field, agg, None)
    cat_entry, cat_ref, _ = _select_entry(table, src, cat_field, None, None)
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "lineChart",
            "projections": {
                "Y": [{"queryRef": val_ref}],
                "Category": [{"queryRef": cat_ref, "active": True}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [val_entry, cat_entry]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def area_vc(x, y, w, h, table, cat_field, val_field, title="", agg="Sum", z=0, tab=0):
    """Gráfico de área. Idêntico a line_vc, só muda visualType para areaChart."""
    name = uid()
    src = get_src(table)
    val_entry, val_ref, _ = _select_entry(table, src, val_field, agg, None)
    cat_entry, cat_ref, _ = _select_entry(table, src, cat_field, None, None)
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "areaChart",
            "projections": {
                "Y": [{"queryRef": val_ref}],
                "Category": [{"queryRef": cat_ref, "active": True}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [val_entry, cat_entry]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def combo_vc(x, y, w, h, table, cat_field, col_field, line_field, title="",
             col_agg="Sum", line_agg="Sum", z=0, tab=0):
    """
    Gráfico combinado (colunas + linha), visualType lineClusteredColumnComboChart.
    col_field vira barra, line_field vira linha (ambos aceitam measure_ref(...)).
    """
    name = uid()
    src = get_src(table)
    col_entry, col_ref, _ = _select_entry(table, src, col_field, col_agg, None)
    line_entry, line_ref, _ = _select_entry(table, src, line_field, line_agg, None)
    cat_entry, cat_ref, _ = _select_entry(table, src, cat_field, None, None)
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "lineClusteredColumnComboChart",
            "projections": {
                "Category": [{"queryRef": cat_ref, "active": True}],
                "Y": [{"queryRef": col_ref}],
                "Y2": [{"queryRef": line_ref}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": [cat_entry, col_entry, line_entry]
            },
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True,
            "objects": {
                "categoryAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "valueAxis": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}],
                "valueAxis2": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}}}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}],
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def table_vc(x, y, w, h, table, fields, title="", z=0, tab=0):
    """
    Tabela (tableEx). Extraído de um .pbix real de produção.
    fields: lista de nomes de coluna (strings) ou (field, agg) para colunas agregadas,
    ou measure_ref(...) para medidas. Ex:
        table_vc(x, y, w, h, "VENDAS", ["Cliente", ("Valor", "Sum"), measure_ref("Ticket Medio")])
    """
    name = uid()
    src = get_src(table)
    select = []
    projections = []
    for f in fields:
        if isinstance(f, tuple):
            field, agg = f
        else:
            field, agg = f, None
        entry, ref, native_name = _select_entry(table, src, field, agg, None)
        select.append(entry)
        projections.append({"queryRef": ref})
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": select
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "grid": [{"properties": {
                    "gridVertical": {"expr": {"Literal": {"Value": "false"}}},
                    "rowPadding": {"expr": {"Literal": {"Value": "2D"}}}
                }}],
                "columnHeaders": [{"properties": {
                    "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "backColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}],
                "values": [{"properties": {"fontSize": {"expr": {"Literal": {"Value": "9D"}}}}}]
            },
            "vcObjects": {
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}
                }}],
                "border": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E5E9F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}}
                }}],
                "title": [{"properties": {
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "show": {"expr": {"Literal": {"Value": "true" if title else "false"}}},
                    "titleWrap": {"expr": {"Literal": {"Value": "true"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12D"}}}
                }}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def matrix_vc(x, y, w, h, table, row_fields, col_fields, value_fields, title="", z=0, tab=0):
    """
    Matriz (pivot table) — visualType matrix. Mesma base estrutural do table_vc,
    mas com Rows/Columns/Values separados no prototypeQuery e projections.
    row_fields/col_fields: listas de nomes de coluna (strings).
    value_fields: lista de strings, (field, agg) ou measure_ref(...).
    """
    name = uid()
    src = get_src(table)
    select = []
    rows_proj, cols_proj, vals_proj = [], [], []

    for field in row_fields:
        entry, ref, _ = _select_entry(table, src, field, None, None)
        select.append(entry)
        rows_proj.append({"queryRef": ref, "active": True})
    for field in col_fields:
        entry, ref, _ = _select_entry(table, src, field, None, None)
        select.append(entry)
        cols_proj.append({"queryRef": ref, "active": True})
    for f in value_fields:
        if isinstance(f, tuple):
            field, agg = f
        else:
            field, agg = f, "Sum"
        entry, ref, _ = _select_entry(table, src, field, agg, None)
        select.append(entry)
        vals_proj.append({"queryRef": ref})

    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "pivotTable",
            "projections": {"Rows": rows_proj, "Columns": cols_proj, "Values": vals_proj},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": select
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "columnHeaders": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "backColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#118DFF'"}}}}}
                }}]
            },
            "vcObjects": {
                "background": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }}],
                "title": [{"properties": {
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "show": {"expr": {"Literal": {"Value": "true" if title else "false"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def gauge_vc(x, y, w, h, table, value_field, min_field=None, max_field=None,
             target_field=None, title="", z=0, tab=0):
    """
    Medidor estilo termômetro/gauge. Adaptado de um gauge real de produção
    (painel R&S — cota legal de PCD).

    value_field, min_field, max_field, target_field tipicamente são medidas DAX
    (use measure_ref("Nome da Medida")) — é raríssimo um gauge usar coluna crua,
    já que min/max/target normalmente são regras de negócio calculadas.
    Todos exceto value_field são opcionais.
    """
    name = uid()
    src = get_src(table)
    select = []
    projections = {"Y": []}

    val_entry, val_ref, _ = _select_entry(table, src, value_field, "Sum", None)
    select.append(val_entry)
    projections["Y"].append({"queryRef": val_ref})

    def _optional(field, proj_key):
        if field is None:
            return
        entry, ref, _ = _select_entry(table, src, field, "Sum", None)
        select.append(entry)
        projections[proj_key] = [{"queryRef": ref}]

    _optional(min_field, "MinValue")
    _optional(max_field, "MaxValue")
    _optional(target_field, "TargetValue")

    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "gauge",
            "projections": projections,
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": src, "Entity": table, "Type": 0}],
                "Select": select
            },
            "drillFilterOtherVisuals": True,
            "objects": {
                "dataPoint": [{"properties": {
                    "fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#094780'"}}}}}
                }}],
                "calloutValue": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "labelPrecision": {"expr": {"Literal": {"Value": "0L"}}}
                }}],
                "target": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true" if target_field else "false"}}},
                    "labelPrecision": {"expr": {"Literal": {"Value": "0L"}}}
                }}]
            },
            "vcObjects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true" if title else "false"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "alignment": {"expr": {"Literal": {"Value": "'center'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}}
                }}],
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

# ─── Grid helper: layout automático ──────────────────────────────────────────
# Reduz erro humano ao calcular x/y manualmente. Não substitui posicionamento
# fino — use quando quiser distribuir N visuais uniformemente numa área.

def grid(cols, rows, area_x=0, area_y=0, area_w=1280, area_h=720, gap=10):
    """
    Gera uma lista de (x, y, w, h) para uma grade cols×rows dentro de area_*.
    Uso:
        cells = grid(4, 1, area_x=10, area_y=116, area_w=1260, area_h=90)
        vcs.append(card_vc(*cells[0], "TABELA", "Campo1", "Label 1"))
        vcs.append(card_vc(*cells[1], "TABELA", "Campo2", "Label 2"))
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

# ─── Filtros de página / relatório ───────────────────────────────────────────
# slicer_vc cria um filtro visual (visível na tela). page_filter/report_filter
# abaixo criam filtros invisíveis aplicados no nível da página (section) ou
# somente documentam onde plugar um filtro — o campo "filters" de cada section
# e de cada visualContainer aceita uma lista de objetos FilterCard serializada
# como string JSON, no mesmo formato usado internamente pelo Power BI.

def equals_filter(table, field, value, is_string=True):
    """
    Filtro simples 'campo = valor', pronto para colocar em page['filters'] ou
    vc['filters'] (ambos são strings JSON de uma lista de filtros).
    """
    src = get_src(table)
    literal_value = f"'{value}'" if is_string else str(value)
    return {
        "name": uid(),
        "type": "Categorical",
        "field": {"Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": field
        }},
        "filter": {
            "Version": 2,
            "From": [{"Name": src, "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {
                    "Expression": {"SourceRef": {"Source": src}},
                    "Property": field
                }}],
                "Values": [[{"Literal": {"Value": literal_value}}]]
            }}}]
        },
        "howCreated": "User"
    }

def apply_page_filters(page_dict, filters):
    """Aplica uma lista de filtros (ex: [equals_filter(...), ...]) no nível da página."""
    page_dict["filters"] = json.dumps(filters, ensure_ascii=False, separators=(',', ':'))
    return page_dict

def apply_visual_filters(visual_container, filters):
    """Aplica uma lista de filtros no nível de um visualContainer específico."""
    visual_container["filters"] = json.dumps(filters, ensure_ascii=False, separators=(',', ':'))
    return visual_container

# ─── Página exemplo ───────────────────────────────────────────────────────────

def page_exemplo():
    """Adapte esta função para cada página do seu painel."""
    vcs = []
    t = [0]
    def nt():
        t[0] += 1000
        return t[0]

    # Header azul escuro
    vcs.append(shape_vc(0, 0, 1280, 66, "#15314F", z=0, tab=nt()))
    vcs.append(textbox_vc(0, 4, 860, 36, "Nome do Painel",
                          "17pt", "#FFFFFF", True, z=100, tab=nt(), pad_top=6, pad_left=24))
    vcs.append(textbox_vc(0, 42, 700, 22, "Subtítulo ou filtro ativo",
                          "9pt", "#A9C0D8", False, z=100, tab=nt(), pad_top=2, pad_left=24))

    # Faixa de slicers
    vcs.append(shape_vc(0, 66, 1280, 42, "#1B3F60", z=200, tab=nt()))
    vcs.append(slicer_vc(10, 70, 230, 34, "NOME_TABELA", "CAMPO_FILTRO", z=500, tab=nt()))

    # Cards KPI (sem shape por baixo — o card tem fundo próprio)
    vcs.append(card_vc(10, 116, 295, 90, "NOME_TABELA", "CAMPO_ID",
                       "Label do Card", agg="CountNonNull", z=300, tab=nt()))

    # Gráfico de rosca
    vcs.append(donut_vc(10, 216, 390, 310,
                        "NOME_TABELA", "CAMPO_CATEGORIA", "CAMPO_VALOR",
                        title="Título do Donut", agg="CountNonNull", z=300, tab=nt()))

    # Gráfico de barras
    vcs.append(bar_vc(410, 216, 860, 310,
                      "NOME_TABELA", "CAMPO_CATEGORIA", "CAMPO_VALOR",
                      title="Título das Barras", agg="CountNonNull",
                      orientation="horizontal", z=300, tab=nt()))

    page_cfg = json.dumps({"objects": {"background": [{"properties": {
        "transparency": {"expr": {"Literal": {"Value": "0D"}}},
        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#EEF1F6'"}}}}}
    }}]}}, ensure_ascii=False, separators=(',', ':'))

    return {
        "id": 0, "name": uid(), "displayName": "Nome da Pagina",
        "filters": "[]", "ordinal": 0, "width": 1280, "height": 720,
        "displayOption": 1, "visualContainers": vcs, "config": page_cfg
    }

# ─── Múltiplas páginas com navegação ──────────────────────────────────────────
# Padrão validado para um painel com várias páginas e uma faixa de "abas" de
# navegação (botões de texto que trocam de página). Cada página precisa de
# "ordinal" sequencial (0, 1, 2, ...) — é isso que define a ordem no Power BI
# Desktop; "displayName" é o que aparece na aba visualmente.

def nav_button_vc(x, y, w, h, text, target_page_name, active=False, z=1000, tab=0):
    """
    Botão de texto que navega para outra página ao clicar (bookmark/actionButton
    simplificado via textbox + ação de página). active=True apenas muda o estilo
    visual (não afeta a navegação em si).
    """
    name = uid()
    color = "#FFFFFF" if active else "#A9C0D8"
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "actionButton",
            "drillFilterOtherVisuals": True,
            "objects": {
                "text": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{text}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{color}'"}}}}}
                }}],
                "fill": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "outline": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]
            }
        },
        "action": {
            "type": "PageNavigation",
            "destination": target_page_name
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def build_pages_with_nav(page_builders):
    """
    page_builders: lista de funções (uma por página) que retornam o dict da página
    (sem 'ordinal' definido). Esta função atribui ordinal sequencial e retorna a
    lista final pronta para build_layout(pages).

    Uso:
        pages = build_pages_with_nav([page_resumo, page_headcount, page_afastamentos])
    """
    pages = [builder() for builder in page_builders]
    for i, page in enumerate(pages):
        page["ordinal"] = i
    return pages

# ─── Layout raiz ─────────────────────────────────────────────────────────────

def build_layout(pages):
    root_cfg = json.dumps({
        "version": "5.73",
        "themeCollection": {"baseTheme": {
            "name": "CY26SU05", "type": 2,
            "version": {"visual": "2.9.0", "report": "3.3.0", "page": "2.3.1"}
        }},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "linguisticSchemaSyncVersion": 2,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
            "useEnhancedTooltips": True,
            "exportDataMode": 1,
            "useDefaultAggregateDisplayName": True
        },
        "objects": {
            "section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}],
            "outspacePane": [{"properties": {"expanded": {"expr": {"Literal": {"Value": "false"}}}}}]
        }
    }, ensure_ascii=False, separators=(',', ':'))

    return {
        "id": 0,
        "resourcePackages": [{"resourcePackage": {
            "name": "SharedResources", "type": 2,
            "items": [{"type": 202, "path": "BaseThemes/CY26SU05.json", "name": "CY26SU05"}],
            "disabled": False
        }}],
        "sections": pages,
        "config": root_cfg,
        "layoutOptimization": 0
    }

# ─── Empacotar — NÃO alterar esta função ─────────────────────────────────────

# ─── Imagens: ícones e logo ──────────────────────────────────────────────────
# Um .pbix embute imagens em Report/StaticResources/RegisteredResources/<arquivo>
# e as declara em layout["resourcePackages"] (pacote "RegisteredResources").
# O visual "image" referencia o recurso por ItemName. Fluxo:
#   1. registre cada imagem com register_image() ANTES de montar o layout
#   2. use image_vc(...) nos visuais
#   3. gere com pack_pbix_with_images() (injeta os bytes no zip + resourcePackages)
#
# Padrão VILLA: ícones flat ~61×53px dentro do card (abaixo do label);
# logo branco ~100×42px no header à direita. Ver design-system-villa.md.

# Registro global de imagens a embutir: nome_lógico -> caminho no disco
_IMAGES = {}

def register_image(logical_name, file_path):
    """Registra uma imagem para ser embutida. logical_name é como você a referencia em image_vc."""
    _IMAGES[logical_name] = file_path
    return logical_name

def baixar_flaticon(icon_id, dest_path, size=512):
    """
    Baixa um ícone do Flaticon pelo ID, via CDN de imagens (sem abrir o site).
    A PÁGINA do Flaticon bloqueia scraping (403), mas o CDN de PNG responde.

    Da URL que o usuário fornece — ex:
        https://www.flaticon.com/free-icon/turnover_2910459
    o ID é o número final: 2910459.

    URL do CDN: https://cdn-icons-png.flaticon.com/{size}/{id[:4]}/{id}.png
    (os 4 primeiros dígitos do ID formam a "pasta").

    ATENÇÃO — licença: ícones grátis do Flaticon exigem ATRIBUIÇÃO ao autor
    (salvo plano pago). A responsabilidade de cumprir a licença é do usuário.
    Só PNG por esta via (o SVG fica atrás de login).
    """
    import urllib.request
    icon_id = str(icon_id).strip()
    folder = icon_id[:4]
    url = f"https://cdn-icons-png.flaticon.com/{size}/{folder}/{icon_id}.png"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as out:
        out.write(resp.read())
    print(f"[OK] Flaticon {icon_id} -> {dest_path}")
    return dest_path

def flaticon_id_da_url(url):
    """Extrai o ID numérico de uma URL do Flaticon (ex: '.../turnover_2910459' -> '2910459')."""
    import re
    m = re.search(r'_(\d+)(?:[?#].*)?$', url.strip())
    if not m:
        raise ValueError(f"Nao consegui extrair o ID do Flaticon da URL: {url}")
    return m.group(1)

# ─── Iconify: fonte de ícones RECOMENDADA ────────────────────────────────────
# Melhor que o Flaticon para uso automatizado:
#  - API pública sem bloqueio (api.iconify.design), COM busca
#  - 200k+ ícones, licença livre (MIT/Apache) na maioria — sem atribuição
#  - coleções coloridas prontas: "flat-color-icons", "twemoji", "fxemoji"
#    (estilo idêntico aos cards VILLA)
# Entrega SVG; convertemos para PNG com resvg-py (Rust, sem DLL de sistema).
#
# Dependência única:  pip install resvg-py
# (cairosvg falha no Windows por falta de libcairo; resvg-py não precisa dela.)

def iconify_buscar(termo, limit=20):
    """
    Busca ícones no Iconify. Retorna lista de nomes 'colecao:icone'.
    Ex: iconify_buscar('team')  -> ['mdi:account-group', 'flat-color-icons:conference-call', ...]
    Prefira coleções coloridas para os cards: filtre por 'flat-color-icons:' ou 'twemoji:'.
    """
    import urllib.request, urllib.parse, json
    url = f"https://api.iconify.design/search?query={urllib.parse.quote(termo)}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("icons", [])

def iconify_png(nome, dest_path, size=512):
    """
    Baixa um ícone do Iconify (nome 'colecao:icone') e salva como PNG.
    Ex: iconify_png('flat-color-icons:conference-call', 'team.png')
    Requer: pip install resvg-py
    """
    import urllib.request, urllib.parse
    colecao, icone = nome.split(":", 1)
    url = f"https://api.iconify.design/{colecao}/{icone}.svg?height={size}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        svg_bytes = resp.read()
    try:
        import resvg_py
        png = resvg_py.svg_to_bytes(svg_string=svg_bytes.decode("utf-8"))
    except ImportError:
        raise RuntimeError("Instale o conversor:  pip install resvg-py")
    with open(dest_path, "wb") as out:
        out.write(png)
    print(f"[OK] Iconify {nome} -> {dest_path}")
    return dest_path

def _resource_item_name(logical_name):
    """Nome do recurso dentro do pacote (mantém a extensão)."""
    return logical_name

def image_vc(x, y, w, h, logical_name, fit="Fit", z=0, tab=0, pad=4):
    """
    Visual de imagem (ícone/logo). logical_name deve ter sido passado a register_image().
    fit: "Fit" (encaixa mantendo proporção) | "Fill" | "Normal".
    """
    item = _resource_item_name(logical_name)
    cfg = {
        "name": uid(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "image",
            "drillFilterOtherVisuals": True,
            "objects": {"image": [{"properties": {
                "sourceFile": {"image": {
                    "name": {"expr": {"Literal": {"Value": f"'{logical_name}'"}}},
                    "url": {"expr": {"ResourcePackageItem": {
                        "PackageName": "RegisteredResources",
                        "PackageType": 1,
                        "ItemName": item
                    }}},
                    "scaling": {"expr": {"Literal": {"Value": "'Normal'"}}}
                }},
                "fit": {"expr": {"Literal": {"Value": f"'{fit}'"}}}
            }}]},
            "vcObjects": {"padding": [{"properties": {
                "top": {"expr": {"Literal": {"Value": f"{pad}D"}}},
                "bottom": {"expr": {"Literal": {"Value": f"{pad}D"}}}
            }}]}
        }
    }
    return vc(x, y, w, h, cfg, z, tab)

def kpi_card_villa(x, y, w, h, measure, label, accent, icon_logical=None, z=0, tab=0):
    """
    Preset completo de KPI no estilo VILLA (validado em produção):
    barra de acento à esquerda + label colorido + número escuro + ícone opcional.
    Retorna uma LISTA de visualContainers (shape de acento, textbox, card, [image]).
    measure = nome de uma medida DAX em _Medidas. accent = hex da cor do KPI.
    """
    parts = []
    # barra de acento (5px à esquerda)
    parts.append(shape_vc(x, y, 5, h, accent, z=z + 5, tab=tab))
    # label colorido, topo — altura 30px (validado: 22px corta o texto em fontes 9pt bold)
    parts.append(textbox_vc(x + 12, y + 10, w - 16, 30, label, "9pt", accent, True,
                            z=z + 10, tab=tab, pad_left=6, pad_top=0))
    # card com o número (usa kpi_card medida). Assumimos measure em _Medidas.
    entry, ref, src = measure_entry("_Medidas", measure)
    card_cfg = {
        "name": uid(),
        "layouts": [{"id": 0, "position": pos(x, y, w, h, z, tab)}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": ref}]},
            "prototypeQuery": {"Version": 2,
                "From": [{"Name": src, "Entity": "_Medidas", "Type": 0}], "Select": [entry]},
            "columnProperties": {ref: {"displayName": label}},
            "drillFilterOtherVisuals": True, "hasDefaultSort": True,
            "objects": {
                "categoryLabels": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "labels": [{"properties": {
                    "fontSize": {"expr": {"Literal": {"Value": "26D"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#15314F'"}}}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}}}}]},
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E5E9F0'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}]}
        }
    }
    parts.append(vc(x, y, w, h, card_cfg, z, tab))
    # ícone opcional (canto inferior esquerdo do card)
    if icon_logical:
        parts.append(image_vc(x + 8, y + 34, 56, 50, icon_logical, fit="Fit", z=z + 15, tab=tab))
    return parts

def measure_entry(table, name):
    """Entrada de query para uma medida DAX (usada por kpi_card_villa e visuais de medida)."""
    src = get_src(table)
    ref = f"{table}.{name}"
    return ({"Measure": {"Expression": {"SourceRef": {"Source": src}}, "Property": name},
             "Name": ref, "NativeReferenceName": name}, ref, src)

def pack_pbix(source_pbix, output_pbix, layout_json):
    """
    Substitui o Report/Layout e zera o SecurityBindings.
    NUNCA alterar a lógica de SecurityBindings ou compress_type.
    Se houver imagens registradas (register_image), use pack_pbix_with_images.
    """
    layout_str = json.dumps(layout_json, ensure_ascii=False, separators=(',', ':'))
    layout_bytes = layout_str.encode('utf-16-le')  # UTF-16 LE sem BOM — obrigatório

    if os.path.exists(output_pbix):
        os.remove(output_pbix)

    with zipfile.ZipFile(source_pbix, 'r') as zin:
        orig_info = next(i for i in zin.infolist() if i.filename == 'Report/Layout')
        new_info = copy.copy(orig_info)
        new_info.file_size = len(layout_bytes)
        new_info.CRC = zlib.crc32(layout_bytes) & 0xFFFFFFFF

        with zipfile.ZipFile(output_pbix, 'w', allowZip64=True) as zout:
            for item in zin.infolist():
                if item.filename == 'Report/Layout':
                    zout.writestr(new_info, layout_bytes, compress_type=orig_info.compress_type)
                elif item.filename == 'SecurityBindings':
                    # CRITICO: zerar DPAPI blob — sem isso Power BI rejeita com MashupValidationError
                    sb = copy.copy(item)
                    sb.file_size = 0
                    sb.CRC = zlib.crc32(b'') & 0xFFFFFFFF
                    zout.writestr(sb, b'', compress_type=item.compress_type)
                else:
                    zout.writestr(copy.copy(item), zin.read(item.filename),
                                  compress_type=item.compress_type)

    print(f"[OK] Gerado: {output_pbix}")

def pack_pbix_with_images(source_pbix, output_pbix, layout_json):
    """
    Como pack_pbix, mas também embute as imagens registradas com register_image():
    - injeta os bytes em Report/StaticResources/RegisteredResources/<nome>
    - declara o pacote RegisteredResources em layout["resourcePackages"]
    Chame register_image() para cada ícone/logo ANTES de montar o layout.
    """
    # 1. declarar o pacote RegisteredResources no layout (preservando SharedResources)
    if _IMAGES:
        items = [{"type": 100, "path": _resource_item_name(n), "name": _resource_item_name(n)}
                 for n in _IMAGES]
        pkgs = layout_json.setdefault("resourcePackages", [])
        # remover pacote RegisteredResources anterior se houver, e (re)adicionar
        pkgs = [p for p in pkgs if p.get("resourcePackage", {}).get("name") != "RegisteredResources"]
        pkgs.append({"resourcePackage": {
            "name": "RegisteredResources", "type": 1, "items": items, "disabled": False}})
        layout_json["resourcePackages"] = pkgs

    layout_bytes = json.dumps(layout_json, ensure_ascii=False, separators=(',', ':')).encode('utf-16-le')

    # extensoes de imagem a declarar no [Content_Types].xml (senao o Power BI IGNORA os PNGs
    # e mostra placeholder quebrado — bug tipico quando o template nunca teve imagem).
    exts = {os.path.splitext(n)[1].lstrip('.').lower() for n in _IMAGES}

    if os.path.exists(output_pbix):
        os.remove(output_pbix)

    # nomes dos recursos ja presentes no template (para nao duplicar)
    with zipfile.ZipFile(source_pbix, 'r') as zin:
        existing = set(zin.namelist())
        orig_info = next(i for i in zin.infolist() if i.filename == 'Report/Layout')
        new_info = copy.copy(orig_info)
        new_info.file_size = len(layout_bytes)
        new_info.CRC = zlib.crc32(layout_bytes) & 0xFFFFFFFF

        with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zout:
            for item in zin.infolist():
                if item.filename == 'Report/Layout':
                    zout.writestr(new_info, layout_bytes, compress_type=orig_info.compress_type)
                elif item.filename == 'SecurityBindings':
                    sb = copy.copy(item); sb.file_size = 0; sb.CRC = zlib.crc32(b'') & 0xFFFFFFFF
                    zout.writestr(sb, b'', compress_type=item.compress_type)
                elif item.filename == '[Content_Types].xml':
                    # CRITICO: declarar <Default Extension="png"/> etc — senao os icones nao carregam
                    ct = zin.read(item.filename).decode('utf-8-sig')
                    for ext in exts:
                        if f'Extension="{ext}"' not in ct:
                            decl = f'<Default Extension="{ext}" ContentType="" />'
                            marker = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                            ct = ct.replace(marker, marker + decl, 1)
                    zout.writestr(copy.copy(item), ct.encode('utf-8-sig'), compress_type=item.compress_type)
                else:
                    zout.writestr(copy.copy(item), zin.read(item.filename),
                                  compress_type=item.compress_type)
            # 2. injetar os bytes das imagens
            for logical, path in _IMAGES.items():
                res_path = f"Report/StaticResources/RegisteredResources/{_resource_item_name(logical)}"
                if res_path in existing:
                    continue  # ja veio do template
                with open(path, 'rb') as fh:
                    zout.writestr(res_path, fh.read())

    print(f"[OK] Gerado com {len(_IMAGES)} imagem(ns): {output_pbix}")

# ─── Validação pós-geração ───────────────────────────────────────────────────
# Reabre o .pbix gerado e verifica os invariantes que causam os erros mais
# comuns (ver tabela de erros no SKILL.md). Rodar logo após pack_pbix() e
# ANTES de abrir no Power BI Desktop — pega problemas em segundos em vez de
# via tentativa-e-erro na UI.

def validate_pbix(output_pbix, expected_page_count=None):
    """
    Verifica:
    1. SecurityBindings existe e está vazio (0 bytes).
    2. DataModel existe e está STORED (compress_type=0, não recomprimido).
    3. Report/Layout é decodificável como UTF-16LE e é JSON válido.
    4. Report/Layout não tem RemoteArtifacts (garantiria dados locais).
    5. (opcional) número de páginas (sections) bate com o esperado.

    Levanta AssertionError com mensagem clara na primeira falha.
    Retorna True se tudo passar.
    """
    with zipfile.ZipFile(output_pbix, 'r') as z:
        names = {i.filename: i for i in z.infolist()}

        assert 'SecurityBindings' in names, "SecurityBindings ausente no ZIP"
        sb_info = names['SecurityBindings']
        assert sb_info.file_size == 0, (
            f"SecurityBindings não está vazio ({sb_info.file_size} bytes) — "
            f"vai disparar MashupValidationError"
        )

        assert 'DataModel' in names, "DataModel ausente — .pbix sem dados embutidos"
        dm_info = names['DataModel']
        assert dm_info.compress_type == 0, (
            f"DataModel foi recomprimido (compress_type={dm_info.compress_type}, "
            f"esperado 0/STORED) — o Power BI vai reportar arquivo corrompido"
        )

        assert 'RemoteArtifacts' not in names, (
            "RemoteArtifacts presente — o DataModel está no cloud, não local; "
            "os visuais não terão dados"
        )

        assert 'Report/Layout' in names, "Report/Layout ausente"
        raw = z.read('Report/Layout')
        try:
            text = raw.decode('utf-16-le')
        except UnicodeDecodeError as e:
            raise AssertionError(f"Report/Layout não é UTF-16LE válido: {e}")

        try:
            layout = json.loads(text)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Report/Layout não é JSON válido: {e}")

        if expected_page_count is not None:
            actual = len(layout.get("sections", []))
            assert actual == expected_page_count, (
                f"Esperado {expected_page_count} página(s), encontrado {actual}"
            )

    print(f"[OK] Validação passou: {output_pbix}")
    return True

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SOURCE = r"CAMINHO\DO\TEMPLATE.pbix"   # template com DataModel local
    OUTPUT = r"CAMINHO\DE\SAIDA.pbix"

    pages = [page_exemplo()]
    layout = build_layout(pages)
    pack_pbix(SOURCE, OUTPUT, layout)
    validate_pbix(OUTPUT, expected_page_count=len(pages))
    print("Concluido!")
```

---

## Inspecionar campos de um Excel

Script auxiliar para descobrir nomes exatos de campos antes de montar o painel:

```python
import zipfile, xml.etree.ElementTree as ET

xlsx_path = r"CAMINHO\PARA\PLANILHA.xlsx"

with zipfile.ZipFile(xlsx_path, 'r') as z:
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    ss_list = [''.join(t.text or '' for t in si.findall('.//m:t', ns))
               for si in ss.findall('m:si', ns)]

    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = [(s.get('name'), s.get('sheetId'))
              for s in wb.findall('.//m:sheet', ns)]

    for sheet_name, sheet_id in sheets:
        sheet_file = f'xl/worksheets/sheet{sheet_id}.xml'
        try:
            sheet_xml = ET.fromstring(z.read(sheet_file))
        except KeyError:
            continue
        rows = sheet_xml.findall('.//m:row', ns)
        if not rows:
            continue
        headers = []
        for c in rows[0].findall('m:c', ns):
            v = c.find('m:v', ns)
            if v is not None:
                val = ss_list[int(v.text)] if c.get('t') == 's' else v.text
                headers.append(repr(val))
        print(f"{repr(sheet_name)}: {headers}")
```

---

## Cores padrão recomendadas

| Uso | Hex |
|-----|-----|
| Header principal | `#15314F` |
| Faixa de slicer | `#1B3F60` |
| Fundo da página | `#EEF1F6` |
| Fundo do card | `#F2F2F2` |
| Texto principal | `#15314F` |
| Label secundário | `#555555` |
| Texto sobre azul | `#FFFFFF` |
| Detalhe azul claro | `#A9C0D8` |

---

## Dimensões de referência (canvas 1280×720)

| Elemento | X | Y | W | H |
|---------|---|---|---|---|
| Header | 0 | 0 | 1280 | 66 |
| Faixa slicers | 0 | 66 | 1280 | 42 |
| 4 cards (row) | 10/315/620/925 | 116 | 295/295/295/345 | 90 |
| Gráfico grande | 10 | 216 | 1260 | 300 |
| 2 gráficos lado a lado | 10 / 640 | 216 | 620 / 630 | 296 |
| Barra de rodapé | 10 | 522 | 1260 | 186 |

---

## Catálogo de visuais disponíveis

| Função | visualType | Uso |
|---|---|---|
| `shape_vc` | shape | retângulo colorido de fundo |
| `textbox_vc` | textbox | texto estático |
| `card_vc` | card | KPI único |
| `donut_vc` | donutChart | proporção categórica |
| `bar_vc` | barChart / columnChart | comparação categórica |
| `slicer_vc` | slicer | filtro dropdown visível |
| `line_vc` | lineChart | série temporal / tendência |
| `area_vc` | areaChart | série temporal com volume |
| `combo_vc` | lineClusteredColumnComboChart | duas métricas em escalas diferentes |
| `table_vc` | tableEx | lista detalhada de linhas |
| `matrix_vc` | pivotTable | tabela cruzada (linhas × colunas × valores) |
| `gauge_vc` | gauge | progresso vs. meta (min/max/target) |
| `nav_button_vc` | actionButton | navegação entre páginas |

Todas as funções que recebem um campo de valor (`val_field`, `field`, `value_field`, etc.)
aceitam tanto uma string (coluna crua, agregada internamente) quanto `measure_ref("Nome da Medida")`
para usar uma medida DAX já definida no modelo. Ver seção "Referências de campo" no script.

---

## Erros comuns e soluções

| Erro ao abrir o .pbix | Causa | Solução |
|---|---|---|
| `MashupValidationError` | SecurityBindings não foi zerado | Gravar `b''` em SecurityBindings — `validate_pbix()` pega isso antes de abrir o arquivo |
| "arquivo corrompido" | DataModel recomprimido (DEFLATED) | Preservar compress_type=0 para DataModel — `validate_pbix()` pega isso |
| `MashupValidationError` persistente | Template tem RemoteArtifacts | Trocar para template com DataModel local — `validate_pbix()` pega isso |
| Visual vazio / "arraste campos" | Nome de tabela ou campo errado no prototypeQuery | Verificar nome exato no Excel XML |
| Visual com erro de alias | Tabela com espaço/acento e alias gerado automaticamente | Usar TABLE_ALIAS dictionary explícito |
| Aviso "Risco potencial" ao abrir | SecurityBindings zerado | Normal — clicar OK |
| Gauge/card mostrando valor errado ou zerado | Usou coluna crua quando deveria ser medida DAX | Trocar `field` por `measure_ref("Nome da Medida")` |
| PBIP crasha ao abrir (`Non-null assertion failure: query`) | Bug da versão June 2026 do Desktop (2.155.756.0) | Gerar .pbix diretamente via `pack_pbix_copy()` em vez de PBIP |
| `writestr()` corrompe DataModel | Chamou `writestr(entry, data)` sem `copy.copy(ZipInfo)` no DataModel | Usar `new_entry = copy.copy(entry)` e `zout.writestr(new_entry, data)` para DataModel |
| Layout substituído quando o usuário só queria copiar | Usou `pack_pbix()` (que substitui Layout) em vez de `pack_pbix_copy()` | Usar `pack_pbix_copy()` para preservar layout original |

---

## pack_pbix_copy — Modo cópia funcional (preserva layout)

Quando o usuário não especificar `--novo-layout`, use `pack_pbix_copy()` em vez de `pack_pbix()`.
Esta função **não substitui o layout** — apenas zera SecurityBindings e valida.

```python
def pack_pbix_copy(source_pbix, output_pbix):
    """
    Copia .pbix template preservando TODO o layout original.
    Apenas zera SecurityBindings (obrigatório para abrir sem MashupValidationError).
    Preserva compress_type=0 do DataModel (STORED).

    Uso: pack_pbix_copy(template, output)
    """
    import os
    if os.path.exists(output_pbix):
        os.remove(output_pbix)

    with zipfile.ZipFile(source_pbix, 'r') as zin:
        with zipfile.ZipFile(output_pbix, 'w', zipfile.ZIP_DEFLATED) as zout:
            for entry in zin.infolist():
                data = zin.read(entry.filename)

                if entry.filename == "SecurityBindings":
                    # Zera SecurityBindings (CRITICO)
                    zout.writestr(entry, b"")
                elif entry.filename == "DataModel":
                    # Preserva compress_type original (STORED) via copy.copy
                    new_entry = copy.copy(entry)
                    zout.writestr(new_entry, data)
                else:
                    # Todos os outros arquivos: preserva como estão
                    zout.writestr(entry, data)

    # Validar resultado
    print("\n=== Validando pbix gerado ===")
    validate_pbix(output_pbix, expected_page_count=None)
```

## validate_pbix melhorada

A função `validate_pbix()` deve ser chamada SEMPRE ao final de qualquer script, seja `pack_pbix` ou `pack_pbix_copy`. Ela detecta os erros mais comuns antes de abrir no Desktop:

```python
def validate_pbix(path, expected_page_count=None):
    """
    Abre o .pbix gerado e confere:
      - SecurityBindings zerado (0 bytes)
      - DataModel STORED (compress_type=0)
      - Ausência de RemoteArtifacts
      - Layout é JSON UTF-16 LE válido
      - (opcional) número esperado de páginas e visuais

    Se expected_page_count for None, apenas valida a estrutura sem conferir quantidade.
    """
    errors = []
    with zipfile.ZipFile(path, 'r') as z:
        entries = {i.filename: i for i in z.infolist()}

        if "SecurityBindings" in entries:
            sb = z.read("SecurityBindings")
            if len(sb) > 0:
                errors.append("SecurityBindings tem %d bytes (deveria ser 0)" % len(sb))
            else:
                print("[OK] SecurityBindings zerado")
        else:
            errors.append("SecurityBindings nao encontrado")

        if "DataModel" in entries:
            dm = entries["DataModel"]
            if dm.compress_type != 0:
                errors.append("DataModel compress_type=%d (deveria ser 0-STORED)" % dm.compress_type)
            else:
                print("[OK] DataModel STORED")
        else:
            errors.append("DataModel nao encontrado")

        if any("RemoteArtifacts" in name for name in entries):
            errors.append("RemoteArtifacts encontrado — DataModel no cloud")
        else:
            print("[OK] Sem RemoteArtifacts")

        if "Report/Layout" in entries:
            try:
                import json
                lay = json.loads(z.read("Report/Layout").decode('utf-16-le'))
                pages = lay.get('sections', [])
                total_vc = sum(len(s.get('visualContainers', [])) for s in pages)
                print("[OK] Layout: %d paginas, %d visuais" % (len(pages), total_vc))

                if expected_page_count and len(pages) != expected_page_count:
                    errors.append("Esperava %d paginas, encontrou %d" % (expected_page_count, len(pages)))
            except Exception as e:
                errors.append("Layout invalido: %s" % e)
        else:
            errors.append("Report/Layout nao encontrado")

    if errors:
        print("\n[ERROS ENCONTRADOS]")
        for e in errors:
            print("  - %s" % e)
        return False
    else:
        print("\n[VALIDACAO OK] Pronto para abrir no Power BI Desktop")
        return True
```

## Checklist final obrigatório

Antes de informar o usuário que o .pbix está pronto, o script deve:

1. ✅ `validate_pbix()` passou sem erros
2. ✅ SecurityBindings = 0 bytes
3. ✅ DataModel compress_type = 0 (STORED)
4. ✅ Sem RemoteArtifacts
5. ✅ Layout é JSON UTF-16 LE válido
