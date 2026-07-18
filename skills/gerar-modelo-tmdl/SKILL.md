---
name: gerar-modelo-tmdl
description: Gera/edita o modelo semântico de um projeto Power BI (PBIP) escrevendo arquivos TMDL - tabelas com ETL Power Query M, medidas DAX, colunas calculadas e relacionamentos. Usa qualquer MCP de banco disponível (MSSQL, MySQL, Oracle, PostgreSQL/Supabase, MongoDB, Firebase, SharePoint) ou chamada direta a APIs REST para descobrir schema e validar a consulta antes de embutir no M. Use quando o usuário pedir para criar tabela a partir de SQL, adicionar medida/relacionamento, ou montar o modelo de um painel sem abrir o Power BI Desktop. Não requer Desktop aberto; opera sobre a pasta *.SemanticModel do .pbip.
argument-hint: <pasta-do-projeto.pbip> <comando: add-table | add-measure | add-relationship | ...>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 0.2.0
---

# /gerar-modelo-tmdl — Modelo semântico como código (TMDL)

Escreve o modelo semântico diretamente nos arquivos TMDL do projeto PBIP,
sem Desktop aberto e sem TOM. Sucessora da skill `gerar-etl-tom` do
[PowerBI-Autopilot](https://github.com/LeonardoVilla/PowerBI-Autopilot).

> **STATUS: parcialmente validado.** Geração de tabelas/medidas/relacionamentos
> TMDL e conector MySQL validados em produção (banco_edu, jul/2026 — ver
> seção "Regras de TMDL validadas na prática"). **API REST com token também
> validada** (jul/2026, projeto SIPLAN — geração de PBIP do zero aberta com
> sucesso no Desktop; ver "✅ Regras validadas no Power BI Desktop" e "Padrão
> validado: fonte = API REST com token"). Demais conectores (Oracle,
> PostgreSQL, MongoDB) ainda vêm da documentação oficial (learn.microsoft.com);
> marcar com ✅ conforme forem validados.
>
> **Legenda de confiança:** trechos marcados **✅ validado** foram abertos com
> sucesso no Desktop por nós; trechos marcados **📄 doc oficial** vêm da
> documentação/sample da Microsoft mas ainda não foram re-testados aqui. Se uma
> melhoria 📄 quebrar em uso, o ponto estável anterior está no histórico do
> git (reverter para o commit imediatamente anterior à melhoria teórica).
>
> ✅ **Validado no Desktop em jul/2026** (PBIP de teste gerado da API do SIPLAN,
> 21 tabelas, aberto com sucesso): **`ref` opcional/omitido** (as 21 tabelas
> apareceram sem nenhuma linha `ref`), **`compatibilityLevel: 1601` +
> `compatibilityMode: powerBI`**, e **medida DAX multi-linha** (`var`/`return`
> indentado) — todas abriram sem erro de TMDL. As três deixam de ser 📄 e
> passam a ✅.

## Fontes canônicas (conferir antes de inventar sintaxe)

Estas são as referências oficiais/modernas que validam (ou corrigem) as regras
desta skill — sempre preferir copiar formato delas a fixar de memória:

- **Sample real da Microsoft** (um PBIP completo, formato de referência):
  [`microsoft/Analysis-Services` › `pbidevmode/fabricps-pbip/SamplePBIP`][sample].
  Tem `model.tmdl` (com `ref`), `database.tmdl` (compatibilityLevel 1601),
  `expressions.tmdl`, `relationships.tmdl` e `tables/`.
- **Skills oficiais de autoria (Microsoft)**:
  [`microsoft/skills-for-fabric`](https://github.com/microsoft/skills-for-fabric)
  — `skills/semantic-model-authoring/` e `common/ITEM-DEFINITIONS-CORE.md`.
- **Spec da linguagem**: [TMDL overview][tmdl-ov] e
  [SemanticModel definition (Fabric REST)](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/semantic-model-definition).
- **Schemas JSON p/ validar PBIR**:
  [`microsoft/json-schemas` › `fabric/item`](https://github.com/microsoft/json-schemas/tree/main/fabric/item).

> **`byPath` vs `byConnection`** (importante ao ir além do Desktop local): o
> `definition.pbism`/`definition.pbir` referencia o modelo por **`byPath`**
> (pasta local — cenário desta skill, abrir no Desktop) OU **`byConnection`**
> (modelo publicado). A **Fabric REST API só aceita `byConnection`** (não
> `byPath`); então um PBIP `byPath` gerado aqui abre no Desktop mas, para deploy
> programático via API do Fabric, é preciso trocar para `byConnection`.

## Estrutura alvo

```
<Projeto>.SemanticModel/
  definition.pbism
  definition/
    database.tmdl         # compatibilityLevel: 1601 + compatibilityMode: powerBI
    model.tmdl            # propriedades do model; `ref` é OPCIONAL (só ordena)
    expressions.tmdl      # parâmetros / expressões compartilhadas M
    relationships.tmdl    # todos os relacionamentos
    tables/
      <NomeTabela>.tmdl   # colunas, medidas, hierarquias, partição com o M
    cultures/  roles/     # (quando houver) — 1 arquivo por cultura/role
    perspectives/         # (quando houver) — 1 arquivo por perspective
  .pbi/                   # NÃO versionar (localSettings.json, cache.abf)
```

> **Roles (RLS/OLS), perspectives e calculation groups**: nenhum projeto
> gerado por esta skill até agora precisou desses recursos — ver
> [references/roles-perspectives-calculation-groups.md](references/roles-perspectives-calculation-groups.md)
> pro esqueleto de partida (marcado 📄 doc oficial, nunca testado por nós).

[sample]: https://github.com/microsoft/Analysis-Services/tree/master/pbidevmode/fabricps-pbip/SamplePBIP
[tmdl-ov]: https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview

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

## ✅ Regras validadas no Power BI Desktop (2026-07 — geração de PBIP do zero)

Validado gerando um PBIP inteiro por script e abrindo no Desktop (release
jun/2026). O Desktop dá o erro exato da linha, então cada item abaixo veio de um
erro real corrigido:

1. **`ref table`/`ref expression` no `model.tmdl` é OPCIONAL — ao gerar à mão,
   o mais seguro é OMITIR.** Confirmado na doc oficial ([tmdl-overview][tmdl-ov]):
   o `ref` serve **só para preservar a ordem das coleções** em roundtrips
   TOM↔TMDL. A composição do modelo vem da **presença dos arquivos**:
   > "Objects referenced in TMDL but with missing TMDL file, are ignored.
   > Objects not referenced but with existing TMDL file, are appended to the
   > end of the collection."

   Ou seja: um `model.tmdl` **só com as propriedades do modelo** (culture,
   defaultPowerBIDataSourceVersion, sourceQueryCulture) funciona — cada arquivo
   em `tables/` e cada expressão em `expressions.tmdl` é anexado ao modelo pela
   sua existência. O `ref` só define a ordem de exibição.

   ⚠️ **Correção de uma versão anterior desta skill:** dizíamos "NUNCA usar
   `ref`, causa erro". Errado — o próprio [sample oficial da Microsoft][sample]
   (`Sales.SemanticModel/definition/model.tmdl`) **usa** `ref table Calendar`,
   `ref table Sales`, etc. O erro real que vimos
   (`Unexpected line type: ReferenceObject`) veio de um `ref` **mal-formado /
   incompleto** (item sem arquivo correspondente ou sintaxe do bloco truncada),
   não do `ref` em si. **Regra prática:** se você não vai emitir o bloco `ref`
   completo e consistente com os arquivos, simplesmente **não escreva `ref`** —
   a ordem fica alfabética/por anexação, o que é aceitável em geração automática.

   [tmdl-ov]: https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview
   [sample]: https://github.com/microsoft/Analysis-Services/tree/master/pbidevmode/fabricps-pbip/SamplePBIP

2. **Partição M — formato exato (validado contra um PBIP real da Microsoft):**
   ```tmdl
   table Turma
   	partition Turma = m
   		mode: import
   		source =
   				let
   				    Fonte = ...
   				in
   				    Fonte

   	annotation PBI_ResultType = Table
   ```
   O M vai indentado com **4 tabs** sob `source =` (2 além de `source`), **sem
   backticks**, e a tabela termina com `annotation PBI_ResultType = Table`. Usar
   backticks (` ``` `) funciona mas não é o formato que o Desktop emite —
   preferir o formato acima.

3. **Parâmetros do Power Query (Web/servidor):**
   ```tmdl
   expression BaseUrl = "https://exemplo/api" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
   	annotation PBI_ResultType = Text
   ```
   Ficam em `expressions.tmdl` no nível do model. Expressões M compartilhadas
   (funções) usam `annotation PBI_ResultType = Function` e o M indentado com
   **2 tabs** sob a declaração `expression Nome =`.

4. **`definition.pbism`**: `{"version": "4.0", "settings": {}}` — a versão 4.0+
   habilita o formato TMDL (pasta `definition/`).

5. **`database.tmdl` — usar `compatibilityLevel` ≥ 1601 e `compatibilityMode`.**
   O [sample oficial da Microsoft][sample] emite:
   ```tmdl
   database Unknown
   	compatibilityLevel: 1601
   	compatibilityMode: powerBI
   ```
   `1601` é hoje o padrão para modelos novos (é o default do Tabular Editor
   também); nível mais alto destrava recursos mais novos (ex.: Format String
   Expression). **Não usar níveis antigos (1550/1567) em modelo novo** — só se
   for editar um modelo legado que já esteja nesse nível. A linha
   `compatibilityMode: powerBI` deve estar presente.

## Padrão validado: fonte = API REST com token (Web.Contents)

Quando a fonte não é banco mas uma **API REST** (ex.: consumir os endpoints de
um sistema web no Power BI), o padrão validado é:

- **Parâmetros** `BaseUrl`, e credenciais (ex.: `ClientId`/`ClientSecret`) como
  parâmetros do Power Query (bloco 3 acima). Podem vir com valor default
  embutido para o arquivo já abrir pronto.
- **Função `GetToken`** (expressão compartilhada) que faz `POST /token/` via
  `Web.Contents` com o corpo JSON e devolve o `access_token`.
- **Função `GetApi(rota)`** que chama `GetToken()`, faz o GET com
  `Headers = [ Authorization = "Bearer " & token ]`, e converte a resposta com
  `Table.FromList(...)`.
- Cada tabela = uma partição que chama `GetApi("<rota>")` e **expande os
  registros dinamicamente** (`Table.ExpandRecordColumn` com
  `Record.FieldNames(Fonte{0}[Column1])`), para que campos novos do endpoint
  apareçam sozinhos no Refresh — sem declarar colunas fixas.
- **Autenticação de rede**: o Desktop pede uma vez por máquina o nível de acesso
  à URL (escolher **Anônimo** quando a API autentica pelo corpo/header, não pela
  auth nativa do Power BI). Isso NÃO é configurável pelo arquivo — documentar
  para o usuário.

> **Gabarito completo e copiável** (estrutura de arquivos, TMDL de cada arquivo,
> report.json com tema e tabela de erros reais → correção):
> [references/pbip-api-rest.md](references/pbip-api-rest.md).

Exemplo real do `GetApi` (o `GetToken` segue a mesma ideia, com POST):
```
let
    GetApi = (rota as text) as table =>
        let
            token = GetToken(),
            resposta = Web.Contents(BaseUrl & "/" & rota & "/", [ Headers = [ Authorization = "Bearer " & token ] ]),
            json = Json.Document(resposta),
            tabela =
                if json is list then
                    Table.FromList(json, Splitter.SplitByNothing(), null, null, ExtraValues.Error)
                else
                    Table.FromList({json}, Splitter.SplitByNothing(), null, null, ExtraValues.Error)
        in
            tabela
in
    GetApi
```

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

## Regras de TMDL validadas na prática (banco_edu, jul/2026)

Descobertas via erro real do parser/engine do Desktop (não documentação) ao
gerar um modelo de 22 tabelas + 32 medidas + 28 relacionamentos programaticamente.
Ver o gerador de referência em `examples/banco_edu/gerar_tmdl_banco_edu.py`
(inclui os três validadores abaixo prontos para reuso).

### 1. Medida DAX: multi-linha É permitido — mas a INDENTAÇÃO tem de ser exata

A doc oficial ([tmdl-overview][tmdl-ov]) confirma que uma `measure` **pode** ter
expressão multi-linha:
> "The value is specified as a multi-line expression following the section
> header."

Ou seja, o formato canônico é o header seguido de linhas **indentadas**:
```tmdl
measure Quantidade =
	var resultado = SUMX ( ... )
	return resultado
```

O erro que vimos ao gerar à mão —
```
TMDL Format Error: Parsing error type - InvalidLineType
Detailed error - Unexpected line type: Other!
```
veio de **indentação inconsistente** da continuação (misturar a tabulação do
corpo com a do header), não de uma proibição de multi-linha.

**Atalho seguro à prova de erro (recomendado em geração automática):** escrever
toda `measure 'Nome' = <expressão DAX>` em **uma única linha**. DAX ignora quebra
de linha, então funciona sempre e elimina a classe inteira de erros de
indentação. Só investir na formatação multi-linha quando a legibilidade
importar (medida escrita para humano editar depois). Se optar por multi-linha,
indentar cada linha da expressão com **exatamente um TAB a mais** que o
`measure`, e nada de linha em branco no meio sem os backticks de bloco.

[tmdl-ov]: https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview

### 2. Relacionamento 1:1 exige `crossFilteringBehavior: bothDirections`

O motor Analysis Services **rejeita** um relacionamento `fromCardinality: one`
+ `toCardinality: one` sem `crossFilteringBehavior: bothDirections` explícito
— o padrão (`OneDirection`) é proibido especificamente para 1:1:

```
'<relacionamento>' tem a CrossFilterDirection definida como OneDirection.
A CrossFilterDirection para relacionamentos Um para Um deve sempre ser
definida como BothDirections.
```

Sempre que declarar `fromCardinality: one` + `toCardinality: one`, incluir
`crossFilteringBehavior: bothDirections` junto.

### 3. O grafo de relacionamentos ATIVOS precisa ser uma árvore (sem ciclos)

Se duas tabelas se conectam por **mais de um caminho ativo** (ex.: A→B→C e
A→D→C), o Desktop recusa o modelo:

```
Há caminhos ambíguos entre 'X' e 'Y': 'X'->'A'->'Y' e 'X'->'B'->'Y'
```

Isso acontece com mais frequência do que parece — qualquer tabela "ponte"
(fato de junção, tabela de dimensão compartilhada) que se liga a duas tabelas
já conectadas por outro caminho cria esse ciclo. **Validar isso ANTES de abrir
no Desktop**, com union-find sobre o grafo de relacionamentos ativos (tabela
= nó, relacionamento ativo = aresta; qualquer aresta que uniria dois nós já
no mesmo conjunto fecha um ciclo = ambiguidade):

```python
def validar_grafo_sem_ciclos(rels):
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
    assert not ciclos, f"Caminhos ambíguos: {ciclos}"
```

Ao decidir qual aresta do ciclo inativar, priorizar o vínculo **mais
operacional** (ex.: `turmas_disciplinas→disciplinas` fica ativo porque é
essencial para o modelo; `disciplinas→departamentos` fica inativo porque o
caminho via `cursos→departamentos` já é o oficial) — a escolha é semântica,
o validador só aponta ONDE está o ciclo, não qual lado cortar.

### 4. Rodar os 3 validadores localmente antes de qualquer abertura no Desktop

Além do grafo sem ciclos: (a) toda coluna referenciada em `relationships.tmdl`
existe de fato na tabela (cross-check simples via regex/parse dos `.tmdl`);
(b) parênteses de cada expressão de medida balanceados. Isso troca 4-5
ciclos de "gerar → abrir no Desktop → ler erro → corrigir" por um `assert`
que falha em segundos, localmente.

## Relação com as outras skills

- `gerar-visuais-pbir`: escreve o relatório (pasta `*.Report/`) — nunca as duas
  na mesma pasta ao mesmo tempo sem coordenar.
- `pbip-context`: regras do formato PBIP (ler antes da primeira geração).
- `gerar-etl-tom` (projeto anterior): ainda útil para ajuste fino num modelo
  JÁ aberto no Desktop (cenário interativo/hot-edit).
