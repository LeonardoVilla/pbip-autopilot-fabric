---
name: gerar-etl-tom
description: Cria/gerencia tabelas, medidas, relacionamentos e ETL (Power Query M) dentro de um Power BI Desktop ABERTO, via TOM/XMLA na instancia local do Analysis Services. Use quando o usuario pedir para injetar query M, criar/editar medidas DAX, rodar uma query DAX de diagnostico, auditar se um KPI esta correto, investigar por que um relatorio publicado no Servico difere do Desktop, ou automatizar o Power Query/modelo sem clicar na interface. Requer Power BI Desktop aberto com o .pbix carregado.
argument-hint: <comando: list | export-m | add-table | remove-table | refresh-table | update-measure | dax-query | set-column-type>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 1.2.0
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

# Remover um relacionamento (ex.: antes de recriar apontando para outra coluna)
dotnet run --project tools/EtlTom -- remove-relationship --from "fato.data_x" --to "dim_calendario.Data BR"

# Corrigir o tipo de uma coluna existente (ex.: uma coluna de data que ficou como texto)
dotnet run --project tools/EtlTom -- set-column-type --column "dim_calendario.Data" --type datetime

# Definir a ordenacao de uma coluna categorica por outra coluna (ex.: nome do dia por numero do dia)
dotnet run --project tools/EtlTom -- set-sort-by-column --column "dim_dias.NomeDia" --by "dim_dias.Ordinal"
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

## TODAY()/data corrente divergindo entre Desktop e Serviço publicado (validado ago/2026)

Sintoma: uma medida ou tabela calculada que depende de "hoje" (`TODAY()` em
DAX, `DateTime.LocalNow()` em M) mostra dias/valores diferentes no Power BI
Desktop local e no mesmo relatório publicado no Serviço — mesmo depois de
publicar de novo e confirmar via histórico que o refresh rodou com sucesso.

**Causa**: `TODAY()`/`LocalNow()` refletem o relógio e o fuso horário de quem
está **processando** o cálculo — no Desktop é a máquina do usuário; no Serviço
é o datacenter/gateway, que pode estar em outro fuso (ou UTC). Um chamado
"fechado hoje" no fuso do Brasil pode já ser "amanhã" no fuso de quem calcula
no Serviço, deslocando toda uma janela de "semana atual" por um ou mais dias.
O fuso configurado nas Configurações do dataset (seção "Atualizar") **não
corrige isso** — essa configuração só regula o horário do agendamento e o
comportamento de partições de atualização incremental, não o valor retornado
por `TODAY()`/`LocalNow()` dentro das fórmulas.

**Correção**: nunca usar `TODAY()`/`DateTime.LocalNow()` puro em medidas ou
tabelas calculadas que dependem de "o dia de hoje" ser consistente entre
ambientes. Usar `UTCNOW()` (DAX) ou `DateTimeZone.UtcNow()` (M) com um offset
fixo somado manualmente:
```dax
VAR HojeCorrigido = DATE(YEAR(UTCNOW()-TIME(4,0,0)), MONTH(UTCNOW()-TIME(4,0,0)), DAY(UTCNOW()-TIME(4,0,0)))
```
```m
AgoraLocal = DateTimeZone.SwitchZone(DateTimeZone.UtcNow(), -4, 0),
Hoje = DateTime.Date(DateTimeZone.RemoveZone(AgoraLocal))
```
(o offset `-4`/`-4,0` é um exemplo — usar o offset do fuso relevante ao
negócio). UTC é o mesmo em qualquer processo, então o resultado fica idêntico
não importa onde a query rode.

## Coluna com tipo divergente entre M e TMDL — funciona no Desktop, quebra no Serviço (validado ago/2026)

Sintoma parecido ao de cima, mas a causa é outra: uma coluna gerada por M
(`add-table --columns "Col:datetime,..."` ou similar) fica com o tipo errado
no modelo — por exemplo, uma coluna de data acaba `dataType: string` no TMDL
em vez de `dataType: dateTime`, apesar da query M produzir valores de data.
Isso pode acontecer mesmo passando o tipo certo no comando (um refresh
subsequente pode reverter, ou a tabela ter sido criada por um caminho que não
respeitou o tipo pedido) — **sempre conferir o `dataType:` real no `.tmdl`
depois de criar/alterar uma tabela calculada**, não assumir que bateu com o
que foi pedido.

Uma coluna assim usada num filtro cruzado (`TREATAS`, relacionamento) entre
tabelas pode **funcionar por coincidência no Desktop** — mesma engine, mesma
cultura, comparação texto-contra-data feita com conversão implícita tolerante
— e **divergir no Serviço**, onde o motor de query pode tratar essa mesma
comparação de forma diferente o suficiente para nunca casar nenhuma linha (ou
casar a linha errada). O sintoma característico é: a query isolada via
`dax-query` no Desktop retorna o valor certo, o visual no Desktop mostra
certo, mas o mesmo relatório publicado mostra outra coisa — sem nenhum erro
visível em lugar nenhum.

**Diagnóstico**: `grep dataType` no `.tmdl` da tabela suspeita antes de gastar
ciclos publicando/comparando — conferir se cada coluna usada em `TREATAS`/
relacionamento tem o tipo que a lógica espera (data como `dateTime`, não
`string`; número como `int64`/`double`, não `string`).

**Correção**: `set-column-type --column "Tabela.Coluna" --type datetime`
seguido de `refresh-table --name Tabela` (o refresh é necessário para os
valores já carregados como texto serem reconvertidos — só mudar o tipo
declarado não reprocessa os dados existentes).

## "Publiquei e não mudou nada no Serviço" — roteiro de eliminação (validado ago/2026)

Quando uma correção aplicada e publicada não aparece no relatório do Serviço,
mesmo após publicar de novo, investigar NESTA ordem antes de suspeitar de algo
mais exótico — cada passo é mais barato que o próximo e descarta uma classe
inteira de causa:

1. **Cache do navegador**: `Ctrl+Shift+R` (recarregamento forçado) na aba do
   relatório antes de qualquer outra coisa.
2. **Item errado**: workspaces acumulam relatórios com nomes parecidos (cópias
   de teste, versões antigas renomeadas). Conferir que o link/item aberto é
   mesmo o publicado agora — abrir a partir do link de sucesso que o próprio
   Desktop mostra ao publicar, não de um favorito/aba antiga.
3. **Refresh de dados não rodou ainda**: Publicar atualiza a *definição*
   (modelo, medidas, visuais) — os *dados* só recalculam num refresh do
   dataset. Conferir "Histórico de atualização" nas configurações do dataset:
   se a última atualização bem-sucedida é anterior à publicação, disparar
   "Atualizar agora" e esperar completar antes de checar de novo.
4. **Cache de consulta do dataset**: seção "Cache de Consulta" nas
   configurações do dataset — se ativado, pode servir resultado antigo mesmo
   com dado novo. Confirmar que está "Inativo" ou desativado explicitamente
   antes de descartar essa causa.
5. **Fuso horário do cálculo** (ver seção acima) — se a métrica depende de
   "hoje", o valor pode estar correto para o fuso de quem calculou, só que
   esse fuso não é o esperado.
6. **Tipo de coluna divergente** (ver seção acima) — o caso mais difícil de
   suspeitar porque não gera nenhum erro, só um resultado sutilmente errado
   só num dos dois ambientes.

Só depois de eliminar 1-6 vale suspeitar de algo específico do ambiente
(permissão de gateway, versão de driver, etc.).

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
