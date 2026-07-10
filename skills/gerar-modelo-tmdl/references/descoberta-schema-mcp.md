# Descoberta de schema e validação de SQL via MCP (agnóstico de servidor)

Protocolo para construir/validar o SQL que vai embutido no M, usando **qualquer**
servidor MCP de banco de dados disponível na sessão — sem nomes fixos.

## 1. Detectar o MCP disponível

Em runtime, examinar as ferramentas disponíveis com prefixo `mcp__`.
Candidatas a acesso de banco: nome do servidor ou da ferramenta contendo
`mssql`, `sqlserver`, `sql-server`, `mysql`, `mariadb`, `oracle`, `db`,
`database`, `sql`, `query`, ou descrição mencionando consulta a banco.

- **Uma candidata compatível com a fonte** → usar.
- **Várias candidatas** → perguntar ao usuário qual servidor MCP corresponde
  à fonte do painel (o mesmo banco pode ter mais de um MCP configurado).
- **Nenhuma** → NÃO inventar schema. Parar e ponderar com o usuário:

> "Não identifiquei nenhum servidor MCP com acesso a `<fonte>`. Para gerar um
> SQL confiável eu preciso validar nomes e tipos das colunas. Opções:
> (a) configurar/ativar um MCP para essa fonte e me avisar;
> (b) você me passa o schema (DDL, print do banco ou amostra de dados);
> (c) você executa o SELECT que eu montar e cola o resultado aqui;
> (d) sigo sem validação — o refresh pode falhar por divergência de
>     nome/tipo de coluna, e corrigimos depois. Qual prefere?"

Só seguir pela opção (d) com confirmação explícita.

## 2. Regras de uso do MCP (segurança)

- **Somente leitura**: `SELECT`, `SHOW`, `DESCRIBE` e consultas de metadados.
  NUNCA DDL/DML (INSERT/UPDATE/DELETE/CREATE/DROP) na fonte.
- Sempre limitar amostras: `TOP 10` (MSSQL), `LIMIT 10` (MySQL),
  `FETCH FIRST 10 ROWS ONLY` ou `ROWNUM <= 10` (Oracle).
- Chamadas MCP podem gerar prompt de permissão — é esperado; o usuário aprova.

## 3. Fluxo de construção do SQL

1. **Explorar o schema**: listar tabelas/colunas/tipos relevantes
   (ferramenta de schema do MCP, ou consulta a `INFORMATION_SCHEMA` /
   `ALL_TAB_COLUMNS` no Oracle).
2. **Rascunhar o SELECT** com o usuário (filtros, joins, agregações).
3. **Executar com limite** via MCP e conferir: nomes EXATOS das colunas
   retornadas (alias incluídos), tipos reais, nulos inesperados, volume.
4. **Derivar os tipos** do resultado validado (tabela abaixo) — gera o
   `--columns` (legado) ou as declarações `column` do TMDL sem chute.
5. Embutir o SQL validado no conector M da fonte (seção 5).

## 4. Mapa de tipos → TMDL / --columns

| TMDL / --columns | SQL Server | MySQL | Oracle |
|---|---|---|---|
| `int64` | int, bigint, smallint, tinyint | int, bigint, smallint | NUMBER(p,0) |
| `string` | varchar, nvarchar, char, text | varchar, char, text | VARCHAR2, NVARCHAR2, CHAR, CLOB |
| `decimal` | decimal, numeric, money | decimal, numeric | NUMBER(p,s) |
| `double` | float, real | float, double | BINARY_DOUBLE, FLOAT |
| `dateTime` | date, datetime, datetime2, smalldatetime | date, datetime, timestamp | DATE, TIMESTAMP |
| `boolean` | bit | tinyint(1) ⚠ | (não nativo — usar NUMBER(1) → int64) |

⚠ MySQL `tinyint(1)`: conferir na amostra se é booleano de fato ou contador.

## 5. Conectores M por fonte

**MSSQL** — ✅ validado em produção (VILLA MT):
```
Sql.Database("SERVIDOR", "BANCO", [Query="SELECT ..."])
```

**MySQL** — documentado, ainda não validado neste projeto. Requer o
Connector/NET da MySQL instalado na máquina (sem ele o Desktop nem lista a fonte):
```
MySQL.Database("servidor:3306", "banco", [Query="SELECT ..."])
```

**Oracle** — documentado, ainda não validado neste projeto. Requer o client
Oracle (ODP.NET/ODAC) instalado:
```
Oracle.Database("host:1521/SERVICO", [Query="SELECT ..."])
```

**Excel local** — validado no projeto anterior (inspeção de headers via XML do
`.xlsx` continua valendo como "MCP do pobre" quando não houver MCP de Excel):
```
let
    Fonte = Excel.Workbook(File.Contents("C:\caminho\planilha.xlsx"), null, true),
    Planilha = Fonte{[Item="NomeDaAba",Kind="Sheet"]}[Data],
    Promovido = Table.PromoteHeaders(Planilha, [PromoteAllScalars=true])
in
    Promovido
```

**SharePoint** — padrão do `update-m` do projeto anterior (Excel → SharePoint):
```
let
    Fonte = SharePoint.Files("https://tenant.sharepoint.com/sites/SITE", [ApiVersion=15]),
    Arquivo = Fonte{[Name="planilha.xlsx"]}[Content],
    Pasta = Excel.Workbook(Arquivo, null, true)
in
    ...
```

Regras de escape do SQL dentro do M (todas as fontes): aspas duplas viram `""`;
no mundo TOM/.pbix, quebras de linha viram `#(lf)`; no TMDL ficam literais.
