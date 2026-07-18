# -*- coding: utf-8 -*-
"""
Gerador do relatorio PBIR do banco_edu - paginas e visuais escritos direto
em <PBIP>/<Nome>.Report/definition/pages/.

Traduz os "objects"/"vcObjects" ja validados em producao (VILLA, projeto
anterior, ver skills/gerar-pbix/references/template-script.md) do formato
classico Layout (.pbix) para o formato PBIR (visual.json por arquivo).

v2: KPIs com barra de destaque (shape+textbox+card, estilo kpi_card_villa),
pagina de Infraestrutura, graficos ricos usando as colunas calculadas
'Faixa Nota', 'Faixa Etária' e 'Período' (ver CALC_COLUMNS em
gerar_tmdl_banco_edu.py).

IMPORTANTE: schema do visualContainer ($schema da URL) e uma aproximacao -
validado abrindo no Desktop (v1 com 16 visuais simples abriu sem erro).
"""
import os
import sys
import json
import uuid

if len(sys.argv) < 2:
    print("uso: python gerar_pbir_banco_edu.py <caminho para banco_edu.Report>")
    raise SystemExit(1)

REPORT_DIR = sys.argv[1]
PAGES_DIR = os.path.join(REPORT_DIR, "definition", "pages")

VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"

def gid():
    return uuid.uuid4().hex[:20]

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def color(hex_):
    return {"solid": {"color": lit(f"'{hex_}'")}}

# ------------------------------------------------------------------
# Referencias de campo (PBIR usa Entity direto - sem alias/From)
# ------------------------------------------------------------------
def measure_field(table, name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}

def column_field(table, name):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}

def count_field(table, id_column):
    return {"Aggregation": {
        "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": id_column}},
        "Function": 3,  # Count (mesmo agg_map de template-script.md)
    }}

def proj(table, name, mode, native=None):
    """mode: True/"measure" -> Measure | False/"column" -> Column cru | "count" -> Aggregation Count."""
    if mode == "count":
        field = count_field(table, name)
        query_ref = f"Count({table}.{name})"
    elif mode is True or mode == "measure":
        field = measure_field(table, name)
        query_ref = f"{table}.{name}"
    else:
        field = column_field(table, name)
        query_ref = f"{table}.{name}"
    return {"field": field, "queryRef": query_ref, "nativeQueryRef": native or name}

# ------------------------------------------------------------------
# Escritor de visual
# ------------------------------------------------------------------
def write_visual(page_dir, x, y, w, h, visual_type, query_state=None, objects=None,
                  vc_objects=None, tab=0, z=0):
    vid = gid()
    vdir = os.path.join(page_dir, "visuals", vid)
    os.makedirs(vdir, exist_ok=True)
    doc = {
        "$schema": VISUAL_SCHEMA,
        "name": vid,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab},
        "visual": {"visualType": visual_type},
    }
    if query_state:
        doc["visual"]["query"] = {"queryState": query_state}
    if objects:
        doc["visual"]["objects"] = objects
    if vc_objects:
        doc["visual"]["visualContainerObjects"] = vc_objects
    with open(os.path.join(vdir, "visual.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    return vid

# ------------------------------------------------------------------
# Construtores por tipo
# ------------------------------------------------------------------
def shape(page_dir, x, y, w, h, fill_color, tab=0, z=0):
    objects = {
        "line": [{"properties": {"show": lit("false")}}],
        "fill": [{"properties": {"show": lit("true"), "fillColor": color(fill_color),
                                  "transparency": lit("0D")}}],
        "rotation": [{"properties": {"angle": lit("0D")}}],
    }
    vc_objects = {"background": [{"properties": {"show": lit("false")}}]}
    return write_visual(page_dir, x, y, w, h, "shape", None, objects, vc_objects, tab, z)

def textbox(page_dir, x, y, w, h, text, size="9pt", text_color="#15314F", bold=True,
            tab=0, z=0, pad_top=2, pad_left=6):
    style = {"fontSize": size, "color": text_color}
    if bold:
        style["fontWeight"] = "bold"
    objects = {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": text, "textStyle": style}]}
    ]}}]}
    vc_objects = {
        "background": [{"properties": {"show": lit("false")}}],
        "padding": [{"properties": {"top": lit(f"{pad_top}D"), "left": lit(f"{pad_left}D")}}],
    }
    return write_visual(page_dir, x, y, w, h, "textbox", None, objects, vc_objects, tab, z)

def card(page_dir, x, y, w, h, table, name, label, is_measure=True, tab=0, z=0,
         hide_category=False, font_size="28D"):
    qs = {"Values": {"projections": [proj(table, name, is_measure, label)]}}
    objects = {
        "categoryLabels": [{"properties": {
            "show": lit("false" if hide_category else "true"), "fontSize": lit("9D"),
            "color": color("#555555")}}],
        "labels": [{"properties": {"fontSize": lit(font_size), "color": color("#15314F")}}],
    }
    vc_objects = {
        "background": [{"properties": {"show": lit("true"), "color": color("#F2F2F2"),
                                        "transparency": lit("0D")}}],
        "border": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("false")}}],
    }
    return write_visual(page_dir, x, y, w, h, "card", qs, objects, vc_objects, tab, z)

def kpi_villa(page_dir, x, y, w, h, table, name, label, accent, tab=0, is_measure=True):
    """KPI estilo VILLA: barra de destaque + label + numero. 3 visuais compostos."""
    shape(page_dir, x, y, 5, h, accent, tab=tab, z=5)
    textbox(page_dir, x + 12, y + 8, w - 16, 22, label, "9pt", accent, True, tab=tab, z=10)
    card(page_dir, x, y, w, h, table, name, label, is_measure, tab=tab, z=0,
         hide_category=True, font_size="24D")

def _cartesian_objects(title, legend_pos=None, hide_value_axis=True):
    objects = {
        "labels": [{"properties": {"show": lit("true")}}],
        "categoryAxis": [{"properties": {"showAxisTitle": lit("false")}}],
        "valueAxis": [{"properties": {"show": lit("false" if hide_value_axis else "true"),
                                       "showAxisTitle": lit("false")}}],
    }
    if legend_pos:
        objects["legend"] = [{"properties": {"show": lit("true"), "position": lit(f"'{legend_pos}'")}}]
    vc_objects = {
        "title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                   "fontColor": color("#15314F"), "fontSize": lit("12D")}}],
        "background": [{"properties": {"show": lit("true"), "color": color("#FFFFFF")}}],
        "border": [{"properties": {"show": lit("true"), "color": color("#E5E9F0"),
                                    "radius": lit("8D")}}],
    }
    return objects, vc_objects

def bar(page_dir, x, y, w, h, cat_table, cat_field, val_table, val_name, title,
        val_is_measure=True, tab=0):
    qs = {"Category": {"projections": [proj(cat_table, cat_field, False)]},
          "Y": {"projections": [proj(val_table, val_name, val_is_measure)]}}
    objects, vc_objects = _cartesian_objects(title)
    return write_visual(page_dir, x, y, w, h, "barChart", qs, objects, vc_objects, tab)

def column(page_dir, x, y, w, h, cat_table, cat_field, val_table, val_name, title,
           val_is_measure=True, tab=0):
    qs = {"Category": {"projections": [proj(cat_table, cat_field, False)]},
          "Y": {"projections": [proj(val_table, val_name, val_is_measure)]}}
    objects, vc_objects = _cartesian_objects(title)
    return write_visual(page_dir, x, y, w, h, "columnChart", qs, objects, vc_objects, tab)

def stacked_column(page_dir, x, y, w, h, cat_table, cat_field, val_table, measures, title, tab=0):
    """Colunas empilhadas com VARIAS medidas como series (stackedColumnChart)."""
    qs = {
        "Category": {"projections": [proj(cat_table, cat_field, False)]},
        "Y": {"projections": [proj(val_table, m, True) for m in measures]},
    }
    objects, vc_objects = _cartesian_objects(title, legend_pos="Top", hide_value_axis=True)
    return write_visual(page_dir, x, y, w, h, "stackedColumnChart", qs, objects, vc_objects, tab)

def line(page_dir, x, y, w, h, cat_table, cat_field, val_table, val_names, title,
         val_is_measure=True, tab=0):
    """val_names: string (1 serie) ou lista (varias series/linhas)."""
    names = val_names if isinstance(val_names, list) else [val_names]
    qs = {
        "Category": {"projections": [proj(cat_table, cat_field, False)]},
        "Y": {"projections": [proj(val_table, n, val_is_measure) for n in names]},
    }
    objects = {
        "categoryAxis": [{"properties": {"show": lit("true")}}],
        "valueAxis": [{"properties": {"show": lit("true")}}],
    }
    if len(names) > 1:
        objects["legend"] = [{"properties": {"show": lit("true"), "position": lit("'Top'")}}]
    vc_objects = {
        "title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                   "fontColor": color("#15314F")}}],
        "background": [{"properties": {"show": lit("true"), "color": color("#FFFFFF")}}],
        "border": [{"properties": {"show": lit("false")}}],
    }
    return write_visual(page_dir, x, y, w, h, "lineChart", qs, objects, vc_objects, tab)

def donut(page_dir, x, y, w, h, cat_table, cat_field, val_table, val_name, title,
          val_is_measure=True, tab=0):
    qs = {"Category": {"projections": [proj(cat_table, cat_field, False)]},
          "Y": {"projections": [proj(val_table, val_name, val_is_measure)]}}
    objects = {
        "legend": [{"properties": {"show": lit("true"), "position": lit("'BottomCenter'"),
                                    "showTitle": lit("false")}}],
        "labels": [{"properties": {"labelStyle": lit("'Data value, percent of total'")}}],
    }
    vc_objects = {
        "title": [{"properties": {"show": lit("true"), "text": lit(f"'{title}'"),
                                   "fontColor": color("#15314F"), "fontSize": lit("12D")}}],
        "background": [{"properties": {"show": lit("true"), "color": color("#FFFFFF")}}],
        "border": [{"properties": {"show": lit("true"), "color": color("#E5E9F0"),
                                    "radius": lit("8D")}}],
    }
    return write_visual(page_dir, x, y, w, h, "donutChart", qs, objects, vc_objects, tab)

# ------------------------------------------------------------------
# Paginas
# ------------------------------------------------------------------
def write_page(page_id, display_name, builder_fn):
    page_dir = os.path.join(PAGES_DIR, page_id)
    os.makedirs(page_dir, exist_ok=True)
    page_doc = {
        "$schema": PAGE_SCHEMA, "name": page_id, "displayName": display_name,
        "displayOption": "FitToPage", "height": 720, "width": 1280,
    }
    with open(os.path.join(page_dir, "page.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(page_doc, f, ensure_ascii=False, indent=2)
    builder_fn(page_dir)
    print(f"pagina escrita: {display_name} ({page_id})")

# PAGINA 1 — Visao Geral (8 KPIs estilo VILLA: barra + label + numero)
def build_visao_geral(pd):
    kpis = [
        ("Alunos Ativos", "Alunos Ativos", "#2A78D6"),
        ("Total Matrículas", "Matrículas", "#4A3AA7"),
        ("Média Global", "Média Global", "#EDA100"),
        ("Taxa de Aprovação", "Taxa de Aprovação", "#0CA30C"),
        ("Frequência Média %", "Frequência", "#1BAF7A"),
        ("Receita Recebida", "Receita Recebida", "#008300"),
        ("Inadimplência %", "Inadimplência", "#D03B3B"),
        ("Total Professores", "Professores", "#15314F"),
    ]
    x0, w, gap = 10, 150, 6
    for i, (measure, label, accent) in enumerate(kpis):
        kpi_villa(pd, x0 + i * (w + gap), 10, w, 100, "_Medidas", measure, label, accent, tab=i)

# PAGINA 2 — Academico
def build_academico(pd):
    stacked_column(pd, 10, 10, 620, 300, "turmas", "Período", "_Medidas",
                    ["Aprovados", "Recuperação", "Reprovados"],
                    "Resultado por Período", tab=0)
    column(pd, 640, 10, 630, 300, "notas", "Faixa Nota", "notas", "nota_id",
           "Distribuição de Notas", val_is_measure="count", tab=1)
    bar(pd, 10, 320, 620, 300, "departamentos", "nome", "_Medidas", "Total Cursos",
        "Cursos por Departamento", tab=2)
    donut(pd, 640, 320, 300, 300, "alunos", "status", "_Medidas", "Total Alunos",
          "Alunos por Situação", tab=3)
    column(pd, 950, 320, 320, 300, "alunos", "Faixa Etária", "_Medidas", "Total Alunos",
           "Alunos por Faixa Etária", tab=4)

# PAGINA 3 — Financeiro
def build_financeiro(pd):
    line(pd, 10, 10, 900, 300, "dim_calendario", "ano_mes", "_Medidas",
         ["Receita Prevista", "Receita Recebida"], "Receita Mensal — Previsto vs. Recebido", tab=0)
    donut(pd, 920, 10, 350, 300, "mensalidades", "status", "_Medidas", "Receita Prevista",
          "Receita por Situação de Pagamento", tab=1)
    column(pd, 10, 320, 420, 300, "mensalidades", "forma_pagamento", "_Medidas",
           "Receita Recebida", "Recebido por Forma de Pagamento", tab=2)
    line(pd, 440, 320, 420, 300, "dim_calendario", "ano_mes", "_Medidas",
         "Inadimplência %", "Inadimplência Mensal", tab=3)
    bar(pd, 870, 320, 400, 300, "alunos", "status", "_Medidas", "Receita Prevista",
        "Receita Prevista por Situação do Aluno", tab=4)

# PAGINA 4 — Infraestrutura
def build_infraestrutura(pd):
    column(pd, 10, 10, 410, 340, "salas", "tipo", "salas", "sala_id",
           "Salas por Tipo", val_is_measure="count", tab=0)
    donut(pd, 430, 10, 410, 340, "laboratorios", "categoria", "laboratorios", "laboratorio_id",
          "Laboratórios por Categoria", val_is_measure="count", tab=1)
    column(pd, 850, 10, 420, 340, "equipamentos_laboratorio", "status",
           "equipamentos_laboratorio", "equipamento_id", "Equipamentos por Situação",
           val_is_measure="count", tab=2)

PAGES = [
    ("visao-geral-banco-edu", "Visão Geral", build_visao_geral),
    ("academico-banco-edu", "Acadêmico", build_academico),
    ("financeiro-banco-edu", "Financeiro", build_financeiro),
    ("infraestrutura-banco-edu", "Infraestrutura", build_infraestrutura),
]

# limpa paginas antigas para regenerar do zero (idempotente)
import shutil
if os.path.isdir(PAGES_DIR):
    for entry in os.listdir(PAGES_DIR):
        full = os.path.join(PAGES_DIR, entry)
        if os.path.isdir(full):
            shutil.rmtree(full)
os.makedirs(PAGES_DIR, exist_ok=True)

for page_id, display_name, fn in PAGES:
    write_page(page_id, display_name, fn)

pages_doc = {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": [p[0] for p in PAGES],
    "activePageName": PAGES[0][0],
}
with open(os.path.join(PAGES_DIR, "pages.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(pages_doc, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {len(PAGES)} paginas escritas em {PAGES_DIR}")
