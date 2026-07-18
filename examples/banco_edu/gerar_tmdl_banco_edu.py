# -*- coding: utf-8 -*-
"""
Gerador do modelo semantico TMDL do banco_edu, a partir do schema MySQL real
(extraido via MCP) e das medidas/relacionamentos documentados em
medidas-dax.md e modelo-semantico.md.

Escreve diretamente em <PBIP>/<Nome>.SemanticModel/definition/tables/*.tmdl
e relationships.tmdl. Idempotente (sobrescreve).
"""
import os
import sys
import uuid

if len(sys.argv) < 2:
    print("uso: python gerar_tmdl_banco_edu.py <caminho para banco_edu.SemanticModel>")
    raise SystemExit(1)

SM_DIR = sys.argv[1]
TABLES_DIR = os.path.join(SM_DIR, "definition", "tables")
os.makedirs(TABLES_DIR, exist_ok=True)

MYSQL_HOST = "127.0.0.1:3306"
MYSQL_DB = "banco_edu"
# Odbc.Query em vez de MySQL.Database: nao depende do provedor ADO.NET
# 'MySql.Data.MySqlClient' (Connector/NET) - fala direto com o driver ODBC
# ja instalado e testado (MySQL ODBC 9.7 Unicode Driver).
# NAO incluir Uid/Pwd na connection string - o Power BI rejeita credencial
# embutida (erro "uid so pode ser fornecida usando credenciais"); a
# autenticacao e configurada separadamente na tela de credenciais da fonte
# (Editar credenciais -> Banco de dados -> usuario root, senha em branco).
ODBC_CONN_STR = (
    "Driver={MySQL ODBC 9.7 Unicode Driver};"
    "Server=127.0.0.1;Port=3306;Database=banco_edu;"
)

def lt():
    return str(uuid.uuid4())

# ------------------------------------------------------------------
# Tipos MySQL -> TMDL
# ------------------------------------------------------------------
def col(name, mysql_type, fmt=None):
    mysql_type = mysql_type.lower()
    if mysql_type.startswith(("bigint", "int", "tinyint")):
        dt, default_fmt = "int64", "0"
    elif mysql_type.startswith("decimal"):
        dt, default_fmt = "decimal", "0.00"
    elif mysql_type == "date":
        dt, default_fmt = "dateTime", "dd/MM/yyyy"
    elif mysql_type == "timestamp":
        dt, default_fmt = "dateTime", "dd/MM/yyyy hh:mm:ss"
    elif mysql_type == "time":
        dt, default_fmt = "string", None
    else:
        dt, default_fmt = "string", None
    return (name, dt, fmt or default_fmt)

# ------------------------------------------------------------------
# Schema: tabela -> (colunas, query SQL, [obs])
# ------------------------------------------------------------------
TABLES = {}

TABLES["departamentos"] = [
    col("departamento_id","bigint"), col("nome","varchar"), col("sigla","varchar"),
    col("ativo","tinyint"), col("criado_em","timestamp"),
]
TABLES["cursos"] = [
    col("curso_id","bigint"), col("departamento_id","bigint"), col("nome","varchar"),
    col("nivel","enum"), col("carga_horaria_total","int"), col("duracao_semestres","int"),
    col("ativo","tinyint"), col("criado_em","timestamp"),
]
TABLES["disciplinas"] = [
    col("disciplina_id","bigint"), col("departamento_id","bigint"), col("codigo","varchar"),
    col("nome","varchar"), col("creditos","int"), col("carga_horaria","int"),
    col("ementa","text"), col("ativo","tinyint"), col("criado_em","timestamp"),
]
TABLES["professores"] = [
    col("professor_id","bigint"), col("departamento_id","bigint"), col("nome","varchar"),
    col("email","varchar"), col("titulacao","enum"), col("data_admissao","date"),
    col("ativo","tinyint"), col("criado_em","timestamp"),
]
TABLES["blocos"] = [
    col("bloco_id","bigint"), col("nome","varchar"), col("localizacao","varchar"),
    col("criado_em","timestamp"),
]
TABLES["salas"] = [
    col("sala_id","bigint"), col("bloco_id","bigint"), col("codigo","varchar"),
    col("capacidade","int"), col("tipo","enum"), col("recursos","text"),
    col("ativa","tinyint"), col("criado_em","timestamp"),
]
TABLES["laboratorios"] = [
    col("laboratorio_id","bigint"), col("sala_id","bigint"), col("categoria","enum"),
    col("quantidade_maquinas","int"), col("software_instalado","text"),
    col("normas_uso","text"), col("criado_em","timestamp"),
]
TABLES["equipamentos_laboratorio"] = [
    col("equipamento_id","bigint"), col("laboratorio_id","bigint"), col("patrimonio","varchar"),
    col("descricao","varchar"), col("status","enum"), col("criado_em","timestamp"),
]
TABLES["turmas"] = [
    col("turma_id","bigint"), col("curso_id","bigint"), col("codigo","varchar"),
    col("semestre_letivo","varchar"), col("ano_letivo","int"), col("turno","enum"),
    col("status","enum"), col("criado_em","timestamp"),
]
TABLES["turmas_disciplinas"] = [
    col("turma_disciplina_id","bigint"), col("turma_id","bigint"), col("disciplina_id","bigint"),
    col("professor_id","bigint"), col("periodo","enum"), col("carga_horaria_planejada","int"),
    col("status","enum"), col("criado_em","timestamp"),
]
TABLES["alunos"] = [
    col("aluno_id","bigint"), col("turma_principal_id","bigint"), col("matricula","varchar"),
    col("nome","varchar"), col("email","varchar"), col("data_nascimento","date"),
    col("data_ingresso","date"), col("status","enum"), col("criado_em","timestamp"),
]
TABLES["matriculas"] = [
    col("matricula_id","bigint"), col("aluno_id","bigint"), col("turma_disciplina_id","bigint"),
    col("data_matricula","date"), col("status","enum"), col("faltas","int"),
    col("criado_em","timestamp"),
]
TABLES["aulas"] = [
    col("aula_id","bigint"), col("turma_disciplina_id","bigint"), col("sala_id","bigint"),
    col("data_aula","date"), col("horario_inicio","time"), col("horario_fim","time"),
    col("status","enum"), col("criado_em","timestamp"),
]
TABLES["avaliacoes"] = [
    col("avaliacao_id","bigint"), col("turma_disciplina_id","bigint"), col("tipo","enum"),
    col("titulo","varchar"), col("peso","decimal"), col("nota_maxima","decimal"),
    col("data_prevista","date"), col("data_aplicacao","date"), col("status","enum"),
    col("criado_em","timestamp"),
]
TABLES["notas"] = [
    col("nota_id","bigint"), col("avaliacao_id","bigint"), col("matricula_id","bigint"),
    col("nota","decimal"), col("criado_em","timestamp"), col("atualizado_em","timestamp"),
]
TABLES["frequencias"] = [
    col("frequencia_id","bigint"), col("aula_id","bigint"), col("matricula_id","bigint"),
    col("presente","tinyint"), col("criado_em","timestamp"),
]
TABLES["resumo_matriculas"] = [
    col("matricula_id","bigint"), col("media_ponderada","decimal"), col("total_avaliacoes","int"),
    col("status_final","enum"), col("atualizado_em","timestamp"),
]
TABLES["prerequisitos_disciplinas"] = [
    col("disciplina_id","bigint"), col("prerequisito_disciplina_id","bigint"),
    col("criado_em","timestamp"),
]
TABLES["matriz_curricular"] = [
    col("matriz_id","bigint"), col("curso_id","bigint"), col("disciplina_id","bigint"),
    col("semestre_sugerido","int"), col("obrigatoria","tinyint"), col("criado_em","timestamp"),
]
TABLES["mensalidades"] = [
    col("mensalidade_id","bigint"), col("aluno_id","bigint"), col("competencia","date"),
    col("valor","decimal",fmt="\\R$\\ #,0.00"), col("data_vencimento","date"),
    col("data_pagamento","date"), col("valor_pago","decimal",fmt="\\R$\\ #,0.00"),
    col("status","enum"), col("forma_pagamento","enum"), col("criado_em","timestamp"),
]
TABLES["dim_calendario"] = [
    col("data_id","int"), col("data","date"), col("ano","int"), col("mes","int"), col("dia","int"),
    col("trimestre","int"), col("semestre","int"), col("nome_mes","varchar"),
    col("nome_mes_abrev","varchar"), col("nome_dia_semana","varchar"), col("dia_semana","int"),
    col("fim_de_semana","tinyint"), col("ano_mes","varchar"), col("ano_semestre","varchar"),
]

# ------------------------------------------------------------------
# Colunas calculadas (DAX, nao vem do M) - para agrupar visuais que
# precisam de uma faixa/categoria que nao existe como coluna crua.
# table -> [(nome, expressao DAX EM UMA LINHA SO, dataType, formatString)]
# ------------------------------------------------------------------
CALC_COLUMNS = {
    "notas": [
        ("Faixa Nota",
         'SWITCH ( TRUE (), [nota] < 2, "0-2", [nota] < 4, "2-4", [nota] < 6, "4-6", [nota] < 8, "6-8", "8-10" )',
         "string", None),
    ],
    "alunos": [
        ("Faixa Etária",
         'VAR i = DATEDIFF ( [data_nascimento], TODAY (), YEAR ) '
         'RETURN SWITCH ( TRUE (), i < 20, "até 19", i < 23, "20-22", i < 26, "23-25", "26+" )',
         "string", None),
    ],
    "turmas": [
        ("Período",
         '[ano_letivo] & "/" & [semestre_letivo]',
         "string", None),
    ],
}

# ------------------------------------------------------------------
# Render de uma tabela .tmdl
# ------------------------------------------------------------------
def render_table(name, columns):
    out = []
    out.append(f"table {name}")
    out.append(f"\tlineageTag: {lt()}")
    out.append("")
    for cname, dtype, fmt in columns:
        out.append(f"\tcolumn {cname}")
        out.append(f"\t\tdataType: {dtype}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {lt()}")
        out.append("\t\tsummarizeBy: none")
        out.append(f"\t\tsourceColumn: {cname}")
        out.append("")
        out.append("\t\tannotation SummarizationSetBy = Automatic")
        out.append("")
    for cc_name, cc_expr, cc_type, cc_fmt in CALC_COLUMNS.get(name, []):
        assert "\n" not in cc_expr, f"coluna calculada '{cc_name}' tem quebra de linha - use uma unica linha"
        out.append(f"\tcolumn '{cc_name}' = {cc_expr}")
        out.append(f"\t\tdataType: {cc_type}")
        if cc_fmt:
            out.append(f"\t\tformatString: {cc_fmt}")
        out.append(f"\t\tlineageTag: {lt()}")
        out.append("\t\tsummarizeBy: none")
        out.append("")
        out.append("\t\tannotation SummarizationSetBy = Automatic")
        out.append("")
    col_list = ", ".join(f'"{c[0]}"' if False else c[0] for c in columns)
    select_cols = ", ".join(c[0] for c in columns)
    query = f"SELECT {select_cols} FROM {name}"
    query_escaped = query.replace('"', '""')
    out.append(f"\tpartition {name} = m")
    out.append("\t\tmode: import")
    out.append("\t\tsource =")
    out.append("\t\t\t\tlet")
    out.append(f'\t\t\t\t    Fonte = Odbc.Query("{ODBC_CONN_STR}", "{query_escaped}")')
    out.append("\t\t\t\tin")
    out.append("\t\t\t\t    Fonte")
    out.append("")
    out.append("\tannotation PBI_ResultType = Table")
    out.append("")
    return "\n".join(out)

for tname, cols in TABLES.items():
    content = render_table(tname, cols)
    path = os.path.join(TABLES_DIR, f"{tname}.tmdl")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"escrito: {tname}.tmdl ({len(cols)} colunas)")

# ------------------------------------------------------------------
# _Medidas (tabela hospedeira das medidas DAX)
# ------------------------------------------------------------------
MEASURES = [
 ("Total Alunos", "DISTINCTCOUNT ( alunos[aluno_id] )", None),
 ("Alunos Ativos", 'CALCULATE ( [Total Alunos], alunos[status] = "ativo" )', "0"),
 ("Alunos Evadidos", 'CALCULATE ( [Total Alunos], alunos[status] = "evadido" )', "0"),
 ("Total Matrículas", "COUNTROWS ( matriculas )", "#,0"),
 ("Total Turmas", "DISTINCTCOUNT ( turmas[turma_id] )", "#,0"),
 ("Total Professores", "DISTINCTCOUNT ( professores[professor_id] )", "#,0"),
 ("Total Disciplinas", "DISTINCTCOUNT ( disciplinas[disciplina_id] )", "#,0"),
 ("Total Cursos", "DISTINCTCOUNT ( cursos[curso_id] )", "#,0"),
 ("Matrículas Avaliadas", "COUNTROWS ( resumo_matriculas )", "#,0"),
 ("Aprovados", 'CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "aprovado" )', "#,0"),
 ("Reprovados", 'CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "reprovado" )', "#,0"),
 ("Recuperação", 'CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "recuperacao" )', "#,0"),
 ("Taxa de Aprovação", "DIVIDE ( [Aprovados], [Matrículas Avaliadas] )", "0.0%"),
 ("Taxa de Reprovação", "DIVIDE ( [Reprovados], [Matrículas Avaliadas] )", "0.0%"),
 ("Média Global", "AVERAGE ( resumo_matriculas[media_ponderada] )", "0.00"),
 ("Nota Média", "AVERAGE ( notas[nota] )", "0.00"),
 ("Média Ponderada",
  "DIVIDE ( SUMX ( notas, notas[nota] * RELATED ( avaliacoes[peso] ) ), SUMX ( notas, RELATED ( avaliacoes[peso] ) ) )", "0.00"),
 ("Presenças", "CALCULATE ( COUNTROWS ( frequencias ), frequencias[presente] = 1 )", "#,0"),
 ("Frequência Média %", "DIVIDE ( [Presenças], COUNTROWS ( frequencias ) )", "0.0%"),
 ("Total Faltas", "SUM ( matriculas[faltas] )", "#,0"),
 ("Faltas Média por Matrícula", "DIVIDE ( [Total Faltas], [Total Matrículas] )", "0.00"),
 ("Receita Prevista", "SUM ( mensalidades[valor] )", "\\R$\\ #,0.00"),
 ("Receita Recebida", 'CALCULATE ( SUM ( mensalidades[valor_pago] ), mensalidades[status] = "pago" )', "\\R$\\ #,0.00"),
 ("Taxa de Recebimento", "DIVIDE ( [Receita Recebida], [Receita Prevista] )", "0.0%"),
 ("Mensalidades Vencidas", "CALCULATE ( COUNTROWS ( mensalidades ), mensalidades[data_vencimento] <= TODAY () )", "#,0"),
 ("Mensalidades em Atraso", 'CALCULATE ( COUNTROWS ( mensalidades ), mensalidades[status] = "atrasado" )', "#,0"),
 ("Inadimplência %", "DIVIDE ( [Mensalidades em Atraso], [Mensalidades Vencidas] )", "0.0%"),
 ("Valor em Atraso", 'CALCULATE ( SUM ( mensalidades[valor] ), mensalidades[status] = "atrasado" )', "\\R$\\ #,0.00"),
 ("Ticket Médio", "DIVIDE ( [Receita Prevista], DISTINCTCOUNT ( mensalidades[aluno_id] ) )", "\\R$\\ #,0.00"),
 ("Receita Recebida YTD", "TOTALYTD ( [Receita Recebida], dim_calendario[data] )", "\\R$\\ #,0.00"),
 ("Receita Mês Anterior",
  "CALCULATE ( [Receita Recebida], DATEADD ( dim_calendario[data], -1, MONTH ) )", "\\R$\\ #,0.00"),
 ("Receita MoM %",
  "DIVIDE ( [Receita Recebida] - [Receita Mês Anterior], [Receita Mês Anterior] )", "0.0%"),
]

def render_medidas():
    out = []
    out.append("table _Medidas")
    out.append(f"\tlineageTag: {lt()}")
    out.append("")
    for mname, expr, fmt in MEASURES:
        # o parser TMDL do Desktop nao aceita medida DAX quebrada em varias
        # linhas com continuacao "solta" (so indentada) - só o "source =" do M
        # aceita esse estilo. Forcar expressao de medida em uma unica linha.
        assert "\n" not in expr, f"medida '{mname}' tem quebra de linha - use uma unica linha"
        out.append(f"\tmeasure '{mname}' = {expr}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tlineageTag: {lt()}")
        out.append("")
    out.append("\tcolumn Value")
    out.append("\t\tdataType: int64")
    out.append("\t\tisHidden")
    out.append(f"\t\tlineageTag: {lt()}")
    out.append("\t\tsummarizeBy: none")
    out.append("\t\tsourceColumn: Value")
    out.append("")
    out.append("\t\tannotation SummarizationSetBy = Automatic")
    out.append("")
    out.append("\tpartition _Medidas = calculated")
    out.append("\t\tmode: import")
    out.append('\t\tsource = ROW ( "Value", 1 )')
    out.append("")
    out.append("\tannotation PBI_ResultType = Table")
    out.append("")
    return "\n".join(out)

content = render_medidas()
path = os.path.join(TABLES_DIR, "_Medidas.tmdl")
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print(f"escrito: _Medidas.tmdl ({len(MEASURES)} medidas)")

print(f"\nTotal: {len(TABLES)+1} tabelas escritas em {TABLES_DIR}")

# ------------------------------------------------------------------
# relationships.tmdl
# fromColumn = lado "muitos" (FK) ; toColumn = lado "um" (PK/unico)
# ------------------------------------------------------------------
# (fromTable, fromCol, toTable, toCol, active, oneToOne)
#
# turmas_disciplinas alcanca departamentos por 3 caminhos paralelos (via
# cursos, via disciplinas, via professores) - so um pode ficar ativo, senao
# o motor rejeita como caminho ambiguo. Mantido ativo o caminho estrutural
# (curso->departamento, "quem e dono do programa"); os vinculos disciplina/
# professor->departamento ficam inativos (a ligacao operacional de
# turmas_disciplinas->disciplinas/professores continua ativa e intacta).
# Mesma logica para matriz_curricular: cursos e disciplinas ja se conectam
# via turmas_disciplinas, entao o segundo vinculo (disciplina) fica inativo.
RELS = [
 ("cursos","departamento_id","departamentos","departamento_id", True, False),
 ("disciplinas","departamento_id","departamentos","departamento_id", False, False),
 ("professores","departamento_id","departamentos","departamento_id", False, False),
 ("turmas","curso_id","cursos","curso_id", True, False),
 ("turmas_disciplinas","turma_id","turmas","turma_id", True, False),
 ("turmas_disciplinas","disciplina_id","disciplinas","disciplina_id", True, False),
 ("turmas_disciplinas","professor_id","professores","professor_id", True, False),
 ("matriculas","turma_disciplina_id","turmas_disciplinas","turma_disciplina_id", True, False),
 ("matriculas","aluno_id","alunos","aluno_id", True, False),
 ("notas","avaliacao_id","avaliacoes","avaliacao_id", True, False),
 ("notas","matricula_id","matriculas","matricula_id", True, False),
 ("frequencias","aula_id","aulas","aula_id", True, False),
 ("frequencias","matricula_id","matriculas","matricula_id", True, False),
 ("resumo_matriculas","matricula_id","matriculas","matricula_id", True, True),
 ("aulas","sala_id","salas","sala_id", True, False),
 # aulas tambem se liga a turmas_disciplinas, mas matriculas ja alcanca
 # turmas_disciplinas diretamente e frequencias ja liga a aulas E a
 # matriculas - ativar as duas fecharia um 4o ciclo (aulas-TD-matriculas-
 # frequencias-aulas). Relacionamento existe (schema real) mas fica inativo.
 ("aulas","turma_disciplina_id","turmas_disciplinas","turma_disciplina_id", False, False),
 ("salas","bloco_id","blocos","bloco_id", True, False),
 ("laboratorios","sala_id","salas","sala_id", True, True),
 ("equipamentos_laboratorio","laboratorio_id","laboratorios","laboratorio_id", True, False),
 ("mensalidades","aluno_id","alunos","aluno_id", True, False),
 ("matriz_curricular","curso_id","cursos","curso_id", True, False),
 ("matriz_curricular","disciplina_id","disciplinas","disciplina_id", False, False),
 ("prerequisitos_disciplinas","disciplina_id","disciplinas","disciplina_id", True, False),
 ("prerequisitos_disciplinas","prerequisito_disciplina_id","disciplinas","disciplina_id", False, False),
 ("alunos","turma_principal_id","turmas","turma_id", False, False),
 ("mensalidades","competencia","dim_calendario","data", True, False),
 ("matriculas","data_matricula","dim_calendario","data", False, False),
 ("aulas","data_aula","dim_calendario","data", False, False),
]

def validar_grafo_sem_ciclos(rels):
    """O motor Analysis Services exige que o subgrafo de relacionamentos
    ATIVOS seja uma arvore/floresta (no maximo 1 caminho entre 2 tabelas
    quaisquer). Usa union-find; falha alto se sobrar ciclo (ambiguidade)."""
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    ciclos = []
    for ft, fc, tt, tc, active, _ in rels:
        if not active:
            continue
        ra, rb = find(ft), find(tt)
        if ra == rb:
            ciclos.append((ft, fc, tt, tc))
        else:
            parent[ra] = rb
    assert not ciclos, (
        "Caminhos ambiguos detectados (relacionamentos ativos formam ciclo): "
        + "; ".join(f"{a}.{b} -> {c}.{d}" for a, b, c, d in ciclos)
    )

validar_grafo_sem_ciclos(RELS)
print("Validacao de ciclos: grafo de relacionamentos ativos e uma arvore - ok")

def render_relationships(rels):
    out = []
    for (ft, fc, tt, tc, active, one_to_one) in rels:
        out.append(f"relationship {lt()}")
        out.append("")
        if one_to_one:
            out.append("\tfromCardinality: one")
            out.append("\ttoCardinality: one")
            # o motor Analysis Services exige bothDirections para relacionamentos 1:1
            # (rejeita OneDirection/default com erro PFE_TM_ONE2ONE_REL_CF_DIR_ONEWAY)
            out.append("\tcrossFilteringBehavior: bothDirections")
        if not active:
            out.append("\tisActive: false")
        out.append(f"\tfromColumn: {ft}.{fc}")
        out.append(f"\ttoColumn: {tt}.{tc}")
        out.append("")
    return "\n".join(out)

rel_content = render_relationships(RELS)
rel_path = os.path.join(SM_DIR, "definition", "relationships.tmdl")
with open(rel_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(rel_content)
print(f"escrito: relationships.tmdl ({len(RELS)} relacionamentos, "
      f"{sum(1 for r in RELS if not r[4])} inativos, {sum(1 for r in RELS if r[5])} 1:1)")
