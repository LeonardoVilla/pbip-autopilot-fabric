---
name: gerar-modelo-tmdl
description: Gera/edita o modelo semântico de um projeto Power BI (PBIP) escrevendo arquivos TMDL - tabelas com ETL Power Query M, medidas DAX, colunas calculadas e relacionamentos. Usa qualquer MCP de banco disponível (MSSQL, MySQL, Oracle, PostgreSQL/Supabase, MongoDB, Firebase, SharePoint) ou chamada direta a APIs REST para descobrir schema e validar a consulta antes de embutir no M. Use quando o usuário pedir para criar tabela a partir de SQL, adicionar medida/relacionamento, ou montar o modelo de um painel sem abrir o Power BI Desktop. Não requer Desktop aberto; opera sobre a pasta *.SemanticModel do .pbip.
argument-hint: <pasta-do-projeto.pbip> <comando: add-table | add-measure | add-relationship | ...>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.1.0
---

# /gerar-modelo-tmdl — Modelo semântico como código (TMDL)

Escreve o modelo semântico diretamente nos arquivos TMDL do projeto PBIP,
sem Desktop aberto e sem TOM. Sucessora da skill `gerar-etl-tom` do
[PowerBI-Autopilot](https://github.com/LeonardoVilla/PowerBI-Autopilot).

> **STATUS: esqueleto em validação.** As regras abaixo vêm da documentação
> oficial (learn.microsoft.com). Conforme forem validadas em produção,
> marcar com ✅ (padrão do projeto anterior).

## Estrutura alvo

```
<Projeto>.SemanticModel/
  definition.pbism
  definition/
    database.tmdl
    model.tmdl            # referências às tabelas, annotations
    expressions.tmdl      # parâmetros / expressões compartilhadas M
    relationships.tmdl    # todos os relacionamentos
    tables/
      <NomeTabela>.tmdl   # colunas, medidas, hierarquias, partição com o M
  .pbi/                   # NÃO versionar (localSettings.json, cache.abf)
```

## Fluxo de execução

1. **Localizar o projeto**: encontrar a pasta `*.SemanticModel/definition/` a
   partir do `.pbip` informado. Se o usuário só tem `.pbix`, instruir:
   abrir no Desktop → Arquivo → Salvar como → `.pbip` (uma única vez).
2. **Construir/validar o SQL via MCP de banco** (quando a tabela vem de
   MSSQL/MySQL/Oracle): seguir o protocolo agnóstico de servidor em
   [descoberta-schema-mcp.md](references/descoberta-schema-mcp.md) —
   detectar qualquer MCP disponível para a fonte, explorar o schema,
   testar o SELECT com limite e derivar os tipos das colunas do resultado
   real. **Sem MCP disponível, não inventar schema**: parar e ponderar as
   opções com o usuário (configurar MCP, fornecer schema/amostra, executar
   a query manualmente, ou seguir sem validação com aval explícito).
3. **Ler o estado atual**: `model.tmdl` e `tables/` existentes antes de
   qualquer escrita — nomes exatos importam (mesma regra Unicode do projeto
   anterior: `Nº`, `Ação`, acentos).
4. **Escrever o TMDL** (tabela nova = arquivo novo em `tables/` + referência
   em `model.tmdl` se o padrão do projeto exigir).
5. **Validar**: abrir o `.pbip` no Desktop (ou usar o powerbi-modeling-mcp)
   e conferir; erros de sintaxe TMDL aparecem na abertura.
6. **Carga de dados**: instruir o usuário a clicar **Atualizar** no Desktop
   (ou agendar refresh no serviço). A geração cria só metadados.

## Padrão de tabela com ETL SQL (herdado e validado no projeto anterior)

O M continua o mesmo — muda só o invólucro (partição TMDL em vez de TOM):

```tmdl
table dim_exemplo
	column CODIGO
		dataType: int64
		summarizeBy: none
		sourceColumn: CODIGO

	column NOME
		dataType: string
		summarizeBy: none
		sourceColumn: NOME

	partition dim_exemplo = m
		mode: import
		source =
				let
				    Fonte = Sql.Database("SERVIDOR", "BANCO", [Query="SELECT ..."])
				in
				    Fonte
```

Regras herdadas do projeto anterior que continuam valendo para o M:
- Aspas duplas dentro da query SQL viram `""` (escape de M).
- Nomes/tipos das colunas declaradas devem bater EXATAMENTE com o retorno do SQL.
- Tipos: `string | int64 | double | decimal | dateTime | boolean`.

Regras novas (TMDL):
- Indentação com TAB é significativa — seguir exatamente o padrão dos
  arquivos existentes no projeto.
- Quebras de linha no M ficam literais dentro do bloco `source =` (não usar
  `#(lf)` como era necessário via TOM).

## Tabela calendário (dim_calendario) — SEMPRE dinâmica, nunca fixar datas

Ao criar uma tabela de datas, o intervalo (`@DATA_INICIO`/`@DATA_FIM`) tem que
ser calculado dinamicamente a partir da própria data-fonte da fato principal
do painel (ex: `MIN`/`MAX` de `DATAADMISSAO`, `data_matricula`, etc.) — **nunca
hardcodar** um ano/intervalo fixo (`'2023-01-01'`...`'2026-12-31'`). Isso
garante que o calendário sempre cobre exatamente o período dos dados reais,
sem precisar editar a query manualmente a cada novo painel ou a cada virada
de ano/mês.

Padrão validado (T-SQL, ver `Painel-RM-Turnover-GERT`), adaptar o
`FROM <fato> WHERE <coluna_data> IS NOT NULL` para a fonte de cada projeto:

```sql
DECLARE @DATA_INICIO DATE;
DECLARE @DATA_FIM DATE;

SELECT @DATA_INICIO = DATEADD(DAY, 1 - DAY(MIN(<coluna_data>)), MIN(<coluna_data>)),
       @DATA_FIM    = EOMONTH(MAX(<coluna_data>))
FROM <tabela_fato>
WHERE <coluna_data> IS NOT NULL;

SELECT
    DATEADD(DAY, N.N, @DATA_INICIO) AS DATA,
    YEAR(DATEADD(DAY, N.N, @DATA_INICIO)) AS ANO,
    MONTH(DATEADD(DAY, N.N, @DATA_INICIO)) AS MES,
    -- NOMEMES, NOMEMES_ABREV, ANOMES, TRIMESTRE, DIASEMANA,
    -- NOMEDIASEMANA, NOMEDIASEMANA_ABREV, PRIMEIRODIAMES, ULTIMODIAMES
    ...
FROM (
    SELECT a.N + b.N*10 + c.N*100 + d.N*1000 + e.N*10000 AS N
    FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) a(N)
    CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) b(N)
    CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) c(N)
    CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) d(N)
    CROSS JOIN (VALUES (0),(1)) e(N)
) N
WHERE DATEADD(DAY, N.N, @DATA_INICIO) <= @DATA_FIM;
```

- `@DATA_INICIO` = 1º dia do mês da menor data da fato (`DATEADD(DAY, 1 - DAY(MIN(...)), MIN(...))`).
- `@DATA_FIM` = último dia do mês da maior data da fato (`EOMONTH(MAX(...))`).
- Tally table de dígitos (cross join `a..e`) gera até 200.000 dias — cobre qualquer intervalo real sem precisar de tabela auxiliar de números no banco.
- Se a fonte não for MSSQL, replicar a mesma ideia (calcular MIN/MAX dinamicamente, gerar série de datas) na sintaxe do dialeto (ex: `generate_series` no Postgres, `List.Dates` nativo do M).
- Se houver múltiplas fatos com datas, calcular `@DATA_INICIO`/`@DATA_FIM` como o MIN/MAX entre todas (`UNION ALL` das colunas de data antes do MIN/MAX), não só da fato principal.

## Regras críticas

1. **NUNCA editar os arquivos com o projeto aberto no Desktop** — o Desktop
   sobrescreve a pasta ao salvar; fechar antes de gerar.
2. **Não versionar `.pbi/`** (localSettings.json, cache.abf) — já está no
   `.gitignore` do repositório.
3. **Commitar antes de gerar** — o "undo" natural é `git restore`.
4. **Medidas**: ficam dentro do arquivo da tabela dona (`measure 'Nome' = <DAX>`);
   tabelas "grupo de medidas" seguem a mesma convenção do projeto anterior.

## Relação com as outras skills

- `gerar-visuais-pbir`: escreve o relatório (pasta `*.Report/`) — nunca as duas
  na mesma pasta ao mesmo tempo sem coordenar.
- `pbip-context`: regras do formato PBIP (ler antes da primeira geração).
- `gerar-etl-tom` (projeto anterior): ainda útil para ajuste fino num modelo
  JÁ aberto no Desktop (cenário interativo/hot-edit).
