---
name: gerar-etl-tom
description: Cria/gerencia tabelas e ETL (Power Query M) dentro de um Power BI Desktop ABERTO, via TOM/XMLA na instancia local do Analysis Services. Use quando o usuario pedir para injetar query M, criar tabela a partir de SQL, exportar as queries M de um painel, ou automatizar o Power Query sem clicar na interface. Requer Power BI Desktop aberto com o .pbix carregado.
argument-hint: <comando: list | export-m | add-table | remove-table | refresh-table>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 1.0.0
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
```

### 3. Gerar o arquivo .m a partir de SQL

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
