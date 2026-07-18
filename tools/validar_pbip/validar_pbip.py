#!/usr/bin/env python3
"""
Validador local de PBIP (TMDL + PBIR) — lint pré-abertura no Power BI Desktop.

Cobre dois conjuntos de regras:
1. Subconjunto portável de skills/gerar-modelo-tmdl/references/BPARules-PowerBI.json
   (Tabular Editor Best Practice Analyzer) — apenas regras que dá pra checar
   via texto/estrutura do TMDL, sem motor DAX/TOM. Regras que exigem inferência
   de tipo em runtime (ex.: dataType de measure) ou dependem de cultures/
   perspectives ausentes no projeto ficam de fora — ver README.md ao lado.
2. Regras próprias já validadas em produção (ver skills/gerar-modelo-tmdl/SKILL.md
   e skills/gerar-visuais-pbir/SKILL.md), agora codificadas em vez de só prosa.

Uso:
    python validar_pbip.py <pasta>          # autodetecta *.SemanticModel/*.Report
    python validar_pbip.py <pasta.SemanticModel>
    python validar_pbip.py <pasta.Report>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SEVERITY_LABEL = {1: "Info", 2: "Aviso", 3: "Erro"}

# Regras de nomenclatura (PascalCase) do BPARules-PowerBI assumem convenção que
# projetos gerados a partir de schema SQL (snake_case) violam em quase toda
# coluna — ficam desligadas por padrão para não afogar os achados estruturais.
# Ative com --incluir-naming quando o modelo aplicar renomeação PascalCase.
NAMING_RULES = {
    "UPPERCASE_FIRST_LETTER_COLUMNS_HIERARCHIES",
    "UPPERCASE_FIRST_LETTER_MEASURES_TABLES",
    "NO_CAMELCASE_COLUMNS_HIERARCHIES",
    "NO_CAMELCASE_MEASURES_TABLES",
}

CAMEL_CASE_RE = re.compile(
    r"[A-Z]([A-Z0-9]*[a-z][a-z0-9]*[A-Z]|[a-z0-9]*[A-Z][A-Z0-9]*[a-z])[A-Za-z0-9]*"
)
FORMAT_STRING_TYPES = {"int64", "datetime", "double", "decimal"}
BARE_FLAGS = {
    "isHidden", "isKey", "keepUniqueRows", "isAvailableInMdx",
    "isDefaultLabel", "isDefaultImage", "isNameInferred",
}
KNOWN_PROP_PREFIXES = (
    "dataType", "formatString", "lineageTag", "summarizeBy", "sourceColumn",
    "displayFolder", "dataCategory", "sortByColumn", "annotation",
    "formatStringDefinition", "changedProperty", "extendedProperty",
    "description", "encoding", "state", "alignment",
)


class Finding:
    __slots__ = ("rule", "severity", "scope", "obj", "message")

    def __init__(self, rule, severity, scope, obj, message):
        self.rule = rule
        self.severity = severity
        self.scope = scope
        self.obj = obj
        self.message = message

    def __repr__(self):
        return f"[{SEVERITY_LABEL[self.severity]}] {self.rule} ({self.scope}: {self.obj}) — {self.message}"


# --------------------------------------------------------------------------
# Parser TMDL (leve, baseado em indentação — não é um parser TMDL completo)
# --------------------------------------------------------------------------

def _indent(line: str) -> int:
    return len(line) - len(line.lstrip("\t"))


def _split_name_expr(rest: str):
    rest = rest.strip()
    if rest.startswith("'"):
        # Aspa simples embutida é escapada dobrando-a: 'Customer''s Name'
        chars = []
        i = 1
        while i < len(rest):
            if rest[i] == "'":
                if i + 1 < len(rest) and rest[i + 1] == "'":
                    chars.append("'")
                    i += 2
                    continue
                i += 1
                break
            chars.append(rest[i])
            i += 1
        name = "".join(chars)
        remainder = rest[i:].strip()
    else:
        m = re.match(r"^([^\s=]+)(.*)$", rest)
        name = m.group(1)
        remainder = m.group(2).strip()
    expr = None
    if remainder.startswith("="):
        expr = remainder[1:].strip()  # pode ser "" quando a expressão é multi-linha
    return name, expr


def _new_object(kind, rest):
    name, expr = _split_name_expr(rest)
    return {"kind": kind, "name": name, "expr": expr or "", "props": {}, "flags": set()}


def parse_tmdl_table(text: str) -> dict:
    table = {"name": None, "columns": [], "measures": [], "hierarchies": []}
    current = None
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        ind = _indent(raw_line)
        content = raw_line.strip()

        if ind == 0 and content.startswith("table "):
            table["name"], _ = _split_name_expr(content[len("table "):])
            current = None
            continue
        if ind == 1 and content.startswith("column "):
            current = _new_object("column", content[len("column "):])
            table["columns"].append(current)
            continue
        if ind == 1 and content.startswith("measure "):
            current = _new_object("measure", content[len("measure "):])
            table["measures"].append(current)
            continue
        if ind == 1 and content.startswith("hierarchy "):
            current = _new_object("hierarchy", content[len("hierarchy "):])
            table["hierarchies"].append(current)
            continue
        if ind == 1 and content.startswith(("partition ", "annotation ")):
            current = None
            continue

        if ind >= 2 and current is not None:
            if content.startswith("annotation "):
                m = re.match(r"annotation\s+([^=]+?)\s*=\s*(.*)$", content)
                if m:
                    current["props"].setdefault("annotations", {})[m.group(1)] = m.group(2)
                continue
            if content in BARE_FLAGS:
                current["flags"].add(content)
                continue
            m = re.match(r"^([A-Za-z][A-Za-z0-9]*):\s*(.*)$", content)
            if m and m.group(1) in KNOWN_PROP_PREFIXES:
                current["props"][m.group(1)] = m.group(2)
                continue
            # Não é propriedade conhecida -> continuação de expressão DAX multi-linha
            current["expr"] = (current["expr"] + "\n" + content) if current["expr"] else content
    return table


def parse_relationships(text: str) -> list:
    rels = []
    current = None
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        ind = _indent(raw_line)
        content = raw_line.strip()
        if ind == 0 and content.startswith("relationship "):
            current = {"id": content[len("relationship "):].strip()}
            rels.append(current)
            continue
        if ind >= 1 and current is not None and ":" in content:
            key, _, value = content.partition(":")
            current[key.strip()] = value.strip()
    return rels


def load_semantic_model(sm_dir: Path) -> dict:
    tables_dir = sm_dir / "definition" / "tables"
    tables = {}
    for f in sorted(tables_dir.glob("*.tmdl")):
        t = parse_tmdl_table(f.read_text(encoding="utf-8"))
        t["_file"] = f
        tables[t["name"]] = t

    rel_file = sm_dir / "definition" / "relationships.tmdl"
    relationships = parse_relationships(rel_file.read_text(encoding="utf-8")) if rel_file.exists() else []

    db_file = sm_dir / "definition" / "database.tmdl"
    database_props = {}
    if db_file.exists():
        for raw_line in db_file.read_text(encoding="utf-8").splitlines():
            content = raw_line.strip()
            if ":" in content:
                k, _, v = content.partition(":")
                database_props[k.strip()] = v.strip()

    model_file = sm_dir / "definition" / "model.tmdl"
    model_text = model_file.read_text(encoding="utf-8") if model_file.exists() else ""
    refs = re.findall(r"^ref\s+(table|expression)\s+(.+)$", model_text, flags=re.MULTILINE)

    expr_file = sm_dir / "definition" / "expressions.tmdl"
    expression_names = set()
    if expr_file.exists():
        expression_names = set(re.findall(r"^expression\s+'?([^'\n]+?)'?\s*=", expr_file.read_text(encoding="utf-8"), flags=re.MULTILINE))

    cultures_dir = sm_dir / "definition" / "cultures"
    has_cultures = cultures_dir.exists() and any(cultures_dir.glob("*.tmdl"))

    return {
        "tables": tables,
        "relationships": relationships,
        "database_props": database_props,
        "refs": refs,
        "expression_names": expression_names,
        "has_cultures": has_cultures,
    }


# --------------------------------------------------------------------------
# Regras — subconjunto portável do BPARules-PowerBI.json (Tabular Editor)
# --------------------------------------------------------------------------

def check_semantic_model(model: dict) -> list:
    findings = []
    tables = model["tables"]
    relationships = model["relationships"]

    fk_from_columns = {r["fromColumn"] for r in relationships if "fromColumn" in r}

    all_column_names = set()
    all_measure_names = set()
    for t in tables.values():
        all_column_names.update(c["name"] for c in t["columns"])
        all_measure_names.update(m["name"] for m in t["measures"])

    for tname, t in tables.items():
        n_cols_no_folder = 0
        n_measures_no_folder = 0

        seen_col_names = set()
        for c in t["columns"]:
            if c["name"] in seen_col_names:
                findings.append(Finding("PBIP_DUPLICATE_COLUMN_NAME", 3, "Table", f"{tname}.{c['name']}",
                                         "Nome de coluna duplicado na mesma tabela — Desktop rejeita ou o comportamento fica indefinido."))
            seen_col_names.add(c["name"])
        seen_measure_names = set()
        for m in t["measures"]:
            if m["name"] in seen_measure_names:
                findings.append(Finding("PBIP_DUPLICATE_COLUMN_NAME", 3, "Table", f"{tname}.{m['name']}",
                                         "Nome de medida duplicado na mesma tabela — Desktop rejeita ou o comportamento fica indefinido."))
            seen_measure_names.add(m["name"])

        # --- NO_CAMELCASE / UPPERCASE_FIRST_LETTER para tabelas ---
        if CAMEL_CASE_RE.search(tname) and " " not in tname:
            findings.append(Finding("NO_CAMELCASE_MEASURES_TABLES", 2, "Table", tname,
                                     "Nome de tabela em CamelCase — considere espaços ou tradução."))
        if tname and tname[0].islower():
            findings.append(Finding("UPPERCASE_FIRST_LETTER_MEASURES_TABLES", 2, "Table", tname,
                                     "Nome de tabela começa com letra minúscula."))

        for c in t["columns"]:
            cname = c["name"]
            is_visible = "isHidden" not in c["flags"]
            dtype = c["props"].get("dataType", "").lower()
            fmt = c["props"].get("formatString", "")
            summarize_by = c["props"].get("summarizeBy", "").lower()
            has_folder = bool(c["props"].get("displayFolder"))
            qualified_name = f"{tname}.{cname}"

            if is_visible and not has_folder:
                n_cols_no_folder += 1

            if dtype == "double":
                findings.append(Finding("META_AVOID_FLOAT", 3, "Column", qualified_name,
                                         "Tipo 'double' pode causar imprecisão — usar decimal/fixed decimal."))

            if is_visible and dtype in ("double", "decimal", "int64") and summarize_by != "none":
                findings.append(Finding("META_SUMMARIZE_NONE", 1, "Column", qualified_name,
                                         "Coluna numérica visível sem summarizeBy: none — risco de soma indevida no client."))

            if is_visible and not fmt.strip() and dtype in FORMAT_STRING_TYPES:
                findings.append(Finding("APPLY_FORMAT_STRING_COLUMNS", 2, "Column", qualified_name,
                                         "Coluna numérica/data visível sem formatString."))

            if is_visible and qualified_name in fk_from_columns:
                findings.append(Finding("LAYOUT_HIDE_FK_COLUMNS", 1, "Column", qualified_name,
                                         "Coluna usada como lado 'muitos' de um relacionamento deveria ficar oculta."))

            if CAMEL_CASE_RE.search(cname) and " " not in cname and is_visible:
                findings.append(Finding("NO_CAMELCASE_COLUMNS_HIERARCHIES", 2, "Column", qualified_name,
                                         "Nome de coluna em CamelCase."))
            if is_visible and cname and cname[0].islower():
                findings.append(Finding("UPPERCASE_FIRST_LETTER_COLUMNS_HIERARCHIES", 2, "Column", qualified_name,
                                         "Nome de coluna começa com letra minúscula."))

            if "TODO" in c["expr"].upper():
                findings.append(Finding("DAX_TODO", 1, "CalculatedColumn", qualified_name,
                                         "Expressão contém 'TODO'."))

            # PERF_UNUSED_COLUMNS (heurística) — feita depois, precisa do texto de todas as expressões

        for m in t["measures"]:
            mname = m["name"]
            is_visible = "isHidden" not in m["flags"]
            fmt = m["props"].get("formatString", "")
            has_folder = bool(m["props"].get("displayFolder"))
            qualified_name = f"{tname}.{mname}" if tname != "_Medidas" else mname

            if is_visible and not has_folder:
                n_measures_no_folder += 1

            if is_visible and not fmt.strip():
                findings.append(Finding("APPLY_FORMAT_STRING_MEASURES", 2, "Measure", qualified_name,
                                         "Medida visível sem formatString (dataType não é inferível do TMDL — confira manualmente se é numérica)."))

            if CAMEL_CASE_RE.search(mname) and " " not in mname and is_visible:
                findings.append(Finding("NO_CAMELCASE_MEASURES_TABLES", 2, "Measure", qualified_name,
                                         "Nome de medida em CamelCase."))
            if is_visible and mname and mname[0].islower():
                findings.append(Finding("UPPERCASE_FIRST_LETTER_MEASURES_TABLES", 2, "Measure", qualified_name,
                                         "Nome de medida começa com letra minúscula."))

            if "TODO" in m["expr"].upper():
                findings.append(Finding("DAX_TODO", 1, "Measure", qualified_name,
                                         "Expressão contém 'TODO'."))

            # DAX_DIVISION_COLUMNS (heurística): '/' fora de DIVIDE(...) e fora de literais numéricos
            for tok in re.finditer(r"(?<![\d.])/(?![\d.]*\s*\))", m["expr"]):
                before = m["expr"][:tok.start()]
                if re.search(r"\bDIVIDE\s*\([^)]*$", before, flags=re.IGNORECASE):
                    continue
                findings.append(Finding("DAX_DIVISION_COLUMNS", 3, "Measure", qualified_name,
                                         "Uso de '/' fora de DIVIDE() — risco de erro em divisão por zero."))
                break

            # DAX_COLUMNS_FULLY_QUALIFIED / DAX_MEASURES_UNQUALIFIED (heurística)
            for ref_m in re.finditer(r"(\w+)?\[([^\]]+)\]", m["expr"]):
                qualifier, ident = ref_m.group(1), ref_m.group(2)
                if ident in all_measure_names and qualifier:
                    findings.append(Finding("DAX_MEASURES_UNQUALIFIED", 2, "Measure", qualified_name,
                                             f"Referência à medida [{ident}] está qualificada com tabela — medidas devem ser não-qualificadas."))
                elif ident in all_column_names and not qualifier:
                    findings.append(Finding("DAX_COLUMNS_FULLY_QUALIFIED", 2, "Measure", qualified_name,
                                             f"Referência à coluna [{ident}] não está qualificada com a tabela."))

        if n_cols_no_folder + len([h for h in t["hierarchies"] if "isHidden" not in h["flags"]]) > 10:
            findings.append(Finding("LAYOUT_COLUMNS_HIERARCHIES_DF", 1, "Table", tname,
                                     f"{n_cols_no_folder} colunas/hierarquias visíveis sem displayFolder (>10)."))
        if n_measures_no_folder > 10:
            findings.append(Finding("LAYOUT_MEASURES_DF", 1, "Table", tname,
                                     f"{n_measures_no_folder} medidas visíveis sem displayFolder (>10)."))

    # --- RELATIONSHIP_COLUMN_NAMES ---
    pair_counts = defaultdict(int)
    for r in relationships:
        if "fromColumn" not in r or "toColumn" not in r:
            continue
        from_table = r["fromColumn"].split(".")[0]
        to_table = r["toColumn"].split(".")[0]
        pair_counts[(from_table, to_table)] += 1
    for r in relationships:
        if "fromColumn" not in r or "toColumn" not in r:
            continue
        from_table, from_col = r["fromColumn"].split(".", 1)
        to_table, to_col = r["toColumn"].split(".", 1)
        n = pair_counts[(from_table, to_table)]
        ok = (from_col == to_col) if n == 1 else from_col.endswith(to_col)
        if not ok:
            findings.append(Finding("RELATIONSHIP_COLUMN_NAMES", 2, "Relationship", r["id"],
                                     f"{r['fromColumn']} -> {r['toColumn']}: nomes de coluna deveriam coincidir (ou terminar igual, se houver múltiplos relacionamentos entre as tabelas)."))

        # --- Regra própria: 1:1 exige crossFilteringBehavior: bothDirections ---
        if r.get("fromCardinality") == "one" and r.get("toCardinality") == "one" and r.get("crossFilteringBehavior") != "bothDirections":
            findings.append(Finding("PBIP_ONE_TO_ONE_BIDIRECTIONAL", 3, "Relationship", r["id"],
                                     "Relacionamento 1:1 sem crossFilteringBehavior: bothDirections — o Analysis Services rejeita isso (OneDirection não é permitido em 1:1)."))

    # --- AVOID_SINGLE_ATTRIBUTE_DIMENSIONS ---
    to_table_counts = defaultdict(int)
    for r in relationships:
        if "toColumn" in r:
            to_table_counts[r["toColumn"].split(".")[0]] += 1
    cols_used_in_rel = fk_from_columns | {r["toColumn"] for r in relationships if "toColumn" in r}
    for tname, t in tables.items():
        visible_unrelated = [c for c in t["columns"]
                              if "isHidden" not in c["flags"] and f"{tname}.{c['name']}" not in cols_used_in_rel]
        if len(visible_unrelated) <= 1 and to_table_counts.get(tname) == 1:
            findings.append(Finding("AVOID_SINGLE_ATTRIBUTE_DIMENSIONS", 2, "Table", tname,
                                     "Dimensão com um único atributo usada por uma única tabela fato — considere desnormalizar."))

    # --- PERF_UNUSED_COLUMNS / PERF_UNUSED_MEASURES (heurística) ---
    all_expr_text = "\n".join(
        (c["expr"] for t in tables.values() for c in t["columns"])
    ) + "\n" + "\n".join(
        (m["expr"] for t in tables.values() for m in t["measures"])
    )
    cols_in_relationships = fk_from_columns | {r["toColumn"] for r in relationships if "toColumn" in r}
    for tname, t in tables.items():
        for c in t["columns"]:
            qualified_name = f"{tname}.{c['name']}"
            if ("isHidden" in c["flags"]
                    and qualified_name not in cols_in_relationships
                    and f"[{c['name']}]" not in all_expr_text
                    and f"{tname}[{c['name']}]" not in all_expr_text):
                findings.append(Finding("PERF_UNUSED_COLUMNS", 1, "Column", qualified_name,
                                         "Coluna oculta sem referências aparentes em DAX/relacionamentos (não detecta uso via query externa)."))
        for m in t["measures"]:
            qualified_name = f"{tname}.{m['name']}" if tname != "_Medidas" else m["name"]
            if "isHidden" in m["flags"] and f"[{m['name']}]" not in all_expr_text:
                findings.append(Finding("PERF_UNUSED_MEASURES", 1, "Measure", qualified_name,
                                         "Medida oculta sem referências aparentes (não detecta uso via query externa)."))

    # --- Regra própria: database.tmdl compatível com o padrão validado ---
    db = model["database_props"]
    compat = db.get("compatibilityLevel", "")
    if compat.isdigit() and int(compat) < 1601:
        findings.append(Finding("PBIP_DB_COMPATIBILITY", 2, "Database", "database.tmdl",
                                 f"compatibilityLevel: {compat} — padrão validado em produção é 1601."))
    if "compatibilityMode" not in db:
        findings.append(Finding("PBIP_DB_COMPATIBILITY", 1, "Database", "database.tmdl",
                                 "compatibilityMode: powerBI ausente — presente no sample oficial da Microsoft."))

    # --- Regra própria: integridade de `ref` no model.tmdl ---
    for kind, name in model["refs"]:
        name = name.strip()
        if kind == "table" and name not in tables:
            findings.append(Finding("PBIP_MODEL_REF_INTEGRITY", 3, "Model", name,
                                     f"'ref table {name}' não corresponde a nenhum tables/*.tmdl — vai quebrar com ReferenceObject no Desktop."))
        if kind == "expression" and model["expression_names"] and name not in model["expression_names"]:
            findings.append(Finding("PBIP_MODEL_REF_INTEGRITY", 3, "Model", name,
                                     f"'ref expression {name}' não corresponde a nenhuma expression em expressions.tmdl."))

    # --- Regra própria: expression e table compartilham namespace ---
    colliding = model["expression_names"] & tables.keys()
    for name in colliding:
        findings.append(Finding("PBIP_EXPRESSION_TABLE_COLLISION", 3, "Model", name,
                                 f"'{name}' é nome de expression E de table — Desktop falha o load com 'duplicate member {name}'. Renomear uma delas (convenção: sufixo ' Query' na expression)."))

    return findings


# --------------------------------------------------------------------------
# Regras PBIR (relatório)
# --------------------------------------------------------------------------

FORBIDDEN_TOOLTIP_PROPS = {
    "sentenceTemplate", "showChartSpecificTooltips",
    "showSentenceFormat", "showTooltipFieldsOnly",
}
FOLDER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def check_report(report_dir: Path) -> list:
    findings = []

    report_json = report_dir / "definition" / "report.json"
    if report_json.exists():
        data = json.loads(report_json.read_text(encoding="utf-8"))
        base_theme = data.get("themeCollection", {}).get("baseTheme")
        if base_theme is None:
            findings.append(Finding("PBIP_REPORT_BASETHEME", 3, "Report", "report.json",
                                     "themeCollection.baseTheme ausente — Desktop falha com 'Cannot read properties of undefined (reading customTheme)'."))
        else:
            theme_name = base_theme.get("name")
            theme_type = base_theme.get("type")
            resolved = False
            for pkg in data.get("resourcePackages", []):
                if pkg.get("type") != theme_type:
                    continue
                for item in pkg.get("items", []):
                    if item.get("name") == theme_name and item.get("type") == "BaseTheme":
                        theme_path = report_dir / "StaticResources" / theme_type / item.get("path", "")
                        if theme_path.is_file():
                            resolved = True
                        else:
                            findings.append(Finding("PBIP_THEME_FILE_MISSING", 3, "Report", "report.json",
                                                     f"themeCollection.baseTheme aponta pra '{theme_path.relative_to(report_dir)}', que não existe — relatório não abre."))
                        break
            if not resolved and not any(f.rule == "PBIP_THEME_FILE_MISSING" for f in findings):
                findings.append(Finding("PBIP_THEME_FILE_MISSING", 2, "Report", "report.json",
                                         f"themeCollection.baseTheme (name={theme_name!r}, type={theme_type!r}) não corresponde a nenhum item em resourcePackages — checar se o tema resolve."))

    pages_dir = report_dir / "definition" / "pages"
    if not pages_dir.exists():
        return findings

    page_binding_names = defaultdict(list)

    for page_dir in pages_dir.iterdir():
        if not page_dir.is_dir():
            continue
        if len(page_dir.name) > 20 or not FOLDER_ID_RE.match(page_dir.name):
            findings.append(Finding("PBIP_FOLDER_ID_CONVENTION", 2, "Page", page_dir.name,
                                     "Nome de pasta de página deveria ter até 20 caracteres, só letras/dígitos/_/-."))

        page_json = page_dir / "page.json"
        if page_json.exists():
            data = json.loads(page_json.read_text(encoding="utf-8"))
            pb = data.get("pageBinding", {}).get("name")
            if pb:
                page_binding_names[pb].append(str(page_json))

        visuals_dir = page_dir / "visuals"
        if not visuals_dir.exists():
            continue
        for visual_dir in visuals_dir.iterdir():
            if not visual_dir.is_dir():
                continue
            if len(visual_dir.name) > 20 or not FOLDER_ID_RE.match(visual_dir.name):
                findings.append(Finding("PBIP_FOLDER_ID_CONVENTION", 2, "Visual", visual_dir.name,
                                         "Nome de pasta de visual deveria ter até 20 caracteres, só letras/dígitos/_/-."))

            visual_json = visual_dir / "visual.json"
            if not visual_json.exists():
                continue
            data = json.loads(visual_json.read_text(encoding="utf-8"))

            pb = data.get("pageBinding", {}).get("name")
            if pb:
                page_binding_names[pb].append(str(visual_json))

            tooltip = data.get("visual", {}).get("visualTooltip") or data.get("visualTooltip")
            if tooltip:
                if tooltip.get("type") == "ReportPage":
                    findings.append(Finding("PBIP_TOOLTIP_TYPE", 3, "Visual", visual_dir.name,
                                             "visualTooltip.type = 'ReportPage' — o valor correto para tooltip de página é 'Canvas' (achado de campo, ReportPage mantém o tooltip nativo)."))
                extra = FORBIDDEN_TOOLTIP_PROPS & tooltip.keys()
                if extra:
                    findings.append(Finding("PBIP_TOOLTIP_EXTRA_PROPS", 3, "Visual", visual_dir.name,
                                             f"visualTooltip com propriedades não reconhecidas pelo $schema: {sorted(extra)} — pode travar a ABERTURA do relatório inteiro."))

    for name, files in page_binding_names.items():
        if len(files) > 1:
            findings.append(Finding("PBIP_PAGEBINDING_UNIQUE", 3, "Report", name,
                                     f"pageBinding.name '{name}' duplicado em: {', '.join(files)} — deve ser único no relatório inteiro."))

    return findings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _resolve_targets(path: Path):
    if path.name.endswith(".SemanticModel"):
        return path, None
    if path.name.endswith(".Report"):
        return None, path
    sm = next(path.glob("*.SemanticModel"), None)
    rp = next(path.glob("*.Report"), None)
    return sm, rp


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("caminho", help="Pasta do projeto .pbip, ou direto a *.SemanticModel/*.Report")
    parser.add_argument("--incluir-naming", action="store_true",
                         help="Inclui regras de nomenclatura PascalCase (UPPERCASE_FIRST_LETTER_*, NO_CAMELCASE_*), "
                              "desligadas por padrão porque disparam em quase toda coluna de um schema SQL snake_case.")
    args = parser.parse_args()

    base = Path(args.caminho).resolve()
    sm_dir, report_dir = _resolve_targets(base)

    all_findings = []
    if sm_dir and sm_dir.exists():
        print(f"Validando modelo semântico: {sm_dir}")
        model = load_semantic_model(sm_dir)
        all_findings += check_semantic_model(model)
    if report_dir and report_dir.exists():
        print(f"Validando relatório: {report_dir}")
        all_findings += check_report(report_dir)

    if not sm_dir and not report_dir:
        print(f"Nenhum *.SemanticModel ou *.Report encontrado em {base}", file=sys.stderr)
        sys.exit(2)

    if not args.incluir_naming:
        n_naming = sum(1 for f in all_findings if f.rule in NAMING_RULES)
        all_findings = [f for f in all_findings if f.rule not in NAMING_RULES]
        if n_naming:
            print(f"({n_naming} achado(s) de nomenclatura PascalCase ocultos — use --incluir-naming para exibi-los)\n")

    all_findings.sort(key=lambda f: -f.severity)

    print(f"\n{len(all_findings)} achado(s):\n")
    for f in all_findings:
        print(f" {f}")

    n_erros = sum(1 for f in all_findings if f.severity == 3)
    print(f"\nResumo: {n_erros} erro(s), "
          f"{sum(1 for f in all_findings if f.severity == 2)} aviso(s), "
          f"{sum(1 for f in all_findings if f.severity == 1)} info.")

    sys.exit(1 if n_erros else 0)


if __name__ == "__main__":
    main()
