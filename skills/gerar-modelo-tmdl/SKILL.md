---
name: gerar-modelo-tmdl
description: Gera/edita o modelo semântico de um projeto Power BI (PBIP) escrevendo arquivos TMDL - tabelas com ETL Power Query M, medidas DAX, colunas calculadas e relacionamentos. Use quando o usuário pedir para criar tabela a partir de SQL, adicionar medida/relacionamento, ou montar o modelo de um painel sem abrir o Power BI Desktop. Não requer Desktop aberto; opera sobre a pasta *.SemanticModel do .pbip.
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
2. **Ler o estado atual**: `model.tmdl` e `tables/` existentes antes de
   qualquer escrita — nomes exatos importam (mesma regra Unicode do projeto
   anterior: `Nº`, `Ação`, acentos).
3. **Escrever o TMDL** (tabela nova = arquivo novo em `tables/` + referência
   em `model.tmdl` se o padrão do projeto exigir).
4. **Validar**: abrir o `.pbip` no Desktop (ou usar o powerbi-modeling-mcp)
   e conferir; erros de sintaxe TMDL aparecem na abertura.
5. **Carga de dados**: instruir o usuário a clicar **Atualizar** no Desktop
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
