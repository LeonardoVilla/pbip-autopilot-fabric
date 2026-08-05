---
name: gerar-etl-tom
description: Cria/gerencia tabelas, medidas e ETL (Power Query M) dentro de um Power BI Desktop ABERTO, via TOM/XMLA na instancia local do Analysis Services. Use quando o usuario pedir para injetar query M, criar/editar medidas DAX, rodar uma query DAX de diagnostico, auditar se um KPI esta correto, ou automatizar o Power Query/modelo sem clicar na interface. Requer Power BI Desktop aberto com o .pbix carregado.
argument-hint: <comando: list | export-m | add-table | remove-table | refresh-table | update-measure | dax-query>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 1.1.0
---

# /gerar-etl-tom — ETL/Power Query via TOM (Analysis Services local)

Injeta e gerencia tabelas com fonte Power Query M diretamente no modelo Tabular que o
Power BI Desktop mantém em memória, usando a **API oficial da Microsoft** (TOM —
Tabular Object Model), a mesma usada por Tabular Editor, DAX Studio e SSMS.

**Não é RPA/automação de tela** — é conexão de protocolo (XMLA) na instância local
do Analysis Services (`msmdsrv.exe`) que o Power BI Desktop sobe ao abrir um `.pbix`.

## Pré-requisitos

1. **Power BI Desktop aberto** com o `.pbix` alvo carregado (a instância AS só existe enquanto o app está aberto).
2. **.NET 6 SDK** (compilar) — runtime 6 basta para executar o binário já compilado.
3. A ferramenta `etl-tom` compilada (ver `tools/EtlTom/` neste repositório): `dotnet build`.

## Fluxo de execução

### 1. Confirmar que o Power BI Desktop está aberto

```powershell
tasklist | findstr msmdsrv
```

Sem `msmdsrv.exe` rodando → pedir ao usuário para abrir o `.pbix` no Power BI Desktop primeiro.

### 2. Executar o comando

A porta é descoberta automaticamente (via netstat + PID do msmdsrv). Com mais de um
Power BI Desktop aberto, especificar `--port`.

```powershell
# Listar tabelas do modelo aberto
dotnet run --project tools/EtlTom -- list

# Exportar todas as queries M para arquivos .m (documentação/backup do ETL)
dotnet run --project tools/EtlTom -- export-m --out ./queries_m

# Criar tabela nova com ETL em M (arquivo .m) e carregar os dados
dotnet run --project tools/EtlTom -- add-table --name dim_nova --m ./dim_nova.m --columns "CODIGO:int64,NOME:string" --refresh

# Remover tabela
dotnet run --project tools/EtlTom -- remove-table --name dim_nova

# Recarregar dados de uma tabela existente
dotnet run --project tools/EtlTom -- refresh-table --name dim_nova

# Trocar o DAX de uma medida existente, preservando relacionamentos/dependentes
dotnet run --project tools/EtlTom -- update-measure --table dim_nova --name "Minha Medida" --dax ./medida.dax

# Rodar uma query DAX arbitraria contra o modelo aberto (validar hipoteses antes de mudar uma medida)
dotnet run --project tools/EtlTom -- dax-query --expr "EVALUATE ROW(\"Total\", COUNTROWS(dim_nova))"
```

### 3. Gerar o arquivo .m a partir de SQL

**Antes de escrever o SQL** — se houver qualquer servidor MCP com acesso à
fonte (procurar ferramentas `mcp__*` de mssql/mysql/oracle/database na sessão),
usá-lo para: listar schema, testar o SELECT com `TOP 10`/`LIMIT 10` (somente
leitura, nunca DDL/DML) e derivar o `--columns` dos nomes/tipos REAIS
retornados. Protocolo completo (detecção agnóstica de servidor, mapa de tipos
SQL→M, fallbacks): ver
[descoberta-schema-mcp.md](../gerar-modelo-tmdl/references/descoberta-schema-mcp.md).
Sem MCP disponível: não inventar schema — ponderar com o usuário (fornecer
schema/amostra, executar a query manualmente, ou seguir sem validação com
aval explícito, ciente de que o refresh pode falhar).

Padrão validado — embrulhar a query SQL nativa em `Sql.Database`:

```
let
    Fonte = Sql.Database("SERVIDOR", "BANCO", [Query="SELECT ... FROM ... WHERE ..."])
in
    Fonte
```

Regras ao gerar o M:
- Quebras de linha DENTRO da string Query viram `#(lf)` (é assim que o Power BI armazena).
- Aspas duplas dentro da query SQL viram `""` (escape de M).
- Os nomes/tipos passados em `--columns` devem bater EXATAMENTE com as colunas que o SQL retorna
  (mesmo raciocínio dos nomes Unicode exatos da skill gerar-pbix).
- Tipos disponíveis: `string | int64 | double | decimal | datetime | boolean`.

### 4. Persistir no arquivo

**CRÍTICO**: as alterações ficam no modelo EM MEMÓRIA do Power BI Desktop.
Instruir o usuário a **salvar (Ctrl+S) no Power BI Desktop** para gravar no `.pbix`.
Fechar sem salvar descarta tudo — o que também é o "undo" natural em caso de erro.

## Regras críticas

1. **Nunca rodar add-table/remove-table com nome de tabela que já existe/não existe** — a ferramenta valida, mas confira com `list` antes.
2. **`--refresh` executa o M de verdade** (conecta na fonte, roda a query SQL). Sem `--refresh`, a tabela é criada só como metadado e os dados são carregados quando o usuário atualizar no Power BI Desktop.
3. **Credenciais de fonte**: o refresh usa as credenciais que o Power BI Desktop já tem para aquela fonte. Fonte nova nunca usada antes pode exigir configurar a credencial uma vez na UI (Transformar dados → Configurações da fonte de dados).
4. **Um painel aberto por vez** é o cenário previsível. Vários abertos = várias instâncias AS = usar `--port` explícito.
5. **Não editar tabelas do modelo criadas como "grupo de medidas"** (tabelas só com medidas) sem necessidade — o valor está nas medidas, não na fonte M.

## Auditando a corretude de uma métrica antes de mudar o DAX

Quando o usuário desconfia de um KPI (ex.: "esse total parece inflado" ou pede uma
auditoria de um painel em produção), **medir antes de mudar** — `dax-query` deixa
rodar `EVALUATE` livre contra o modelo aberto, então dá para comparar duas versões
de uma métrica lado a lado sem tocar em nenhuma medida:

```powershell
dotnet run --project tools/EtlTom -- dax-query --expr "EVALUATE ROW(\"Bruto\", COUNTROWS(fato), \"Distinto\", DISTINCTCOUNT(fato[id_chave]))"
```

**Armadilha recorrente em tabelas fato vindas de um JOIN N:N** (ex.: fato de eventos
unida a uma tabela de vínculos/papéis, onde uma linha-mãe pode ter múltiplos
vínculos): qualquer `COUNTROWS`/`SUM` direto sobre essa tabela conta a linha-mãe
uma vez por vínculo, inflando totais, médias (`AVERAGEX` pesando o mesmo registro
mais de uma vez) e rankings por `SUMMARIZE`. O sintoma é sutil — a query M e o
relacionamento estão corretos, o "bug" é de granularidade, não de sintaxe. Antes
de aceitar um `COUNTROWS(tabela)` como "total de X", perguntar: essa tabela tem
uma linha por evento, ou uma linha por (evento × vínculo)? Se for a segunda,
trocar por `DISTINCTCOUNT(tabela[chave_do_evento])` (ou `CALCULATE(DISTINCTCOUNT(...), <mesmos filtros>)`
para medidas com filtro) — e para médias, agregar primeiro com `SUMMARIZE`/`MAX`
por chave antes do `AVERAGEX`, não direto sobre a tabela crua.

**Toda mudança de DAX que altera o valor exibido é uma decisão de negócio, não uma
correção silenciosa.** Medir com `dax-query` primeiro, reportar os números
antes/depois ao usuário, e só aplicar com `update-measure` após confirmação
explícita — mesmo quando a causa técnica (duplicação, agregação errada) é
inequívoca. Números históricos/capturas de tela já existem baseados no valor
antigo; trocar a fórmula sem avisar quebra a confiança no painel.

Isso é diferente de um bug de **binding/estado** (ver `pbip-context` — filtro
salvo desatualizado, slicer travado), que não muda o *significado* da métrica e
pode ser corrigido sem essa aprovação extra.

## Erros comuns

| Sintoma | Causa | Solução |
|---|---|---|
| "Nenhuma instancia local... encontrada" | Power BI Desktop fechado ou sem .pbix carregado | Abrir o .pbix e aguardar carregar |
| Refresh falha com erro de credencial | Fonte nova sem credencial salva | Configurar a credencial uma vez na UI do Power BI Desktop |
| Refresh falha com erro de coluna | `--columns` não bate com o que o SQL retorna | Conferir nomes/tipos exatos das colunas do SELECT |
| Alterações sumiram | Usuário fechou sem salvar | Sempre salvar (Ctrl+S) no Power BI Desktop após as alterações |
| 2+ portas descobertas | Mais de um Power BI Desktop aberto | Usar `--port` (netstat -ano \| findstr <PID do msmdsrv>) |

## Relação com a skill gerar-pbix

- `gerar-pbix` (offline): gera o **Layout/visuais** de um `.pbix` fechado, sem tocar no modelo de dados.
- `gerar-etl-tom` (online): gera o **modelo de dados/ETL** de um `.pbix` aberto, sem tocar nos visuais.
- Pipeline completo: `gerar-etl-tom` cria as tabelas → usuário salva o .pbix → esse arquivo vira o template do `gerar-pbix` para gerar os visuais.
