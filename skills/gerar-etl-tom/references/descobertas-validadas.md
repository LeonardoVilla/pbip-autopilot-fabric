# Descobertas técnicas validadas — TOM × Power BI Desktop

Registro do processo de validação (2026-07-08, máquina VILLA MT, Power BI Desktop
via Microsoft Store, .NET 6 SDK), para referência em caso de regressão futura.

## Arquitetura confirmada

1. Power BI Desktop (mesmo instalado como app UWP/Store) sobe um processo filho
   `msmdsrv.exe` — Analysis Services Tabular completo — ao carregar um `.pbix`.
2. A instância escuta em `127.0.0.1:<porta dinâmica>` (e `[::1]`), somente loopback.
   A porta muda a cada abertura. Descoberta: PID do msmdsrv → `netstat -ano` → linha
   `LISTENING` daquele PID.
3. Conexão: `Provider=MSOLAP;Data Source=localhost:<porta>;` — sem autenticação extra
   (a instância confia em conexões locais do mesmo usuário).
4. O modelo aparece como 1 Database com nome GUID (ex: `749503e6-...`). `Databases[0]`
   é sempre o modelo do arquivo aberto.

## Pacote NuGet correto

- `Microsoft.AnalysisServices.NetCore.retail.amd64` versão `19.84.1`
  (o nome sem `.NetCore` é a variante .NET Framework).
- Target framework: compila em `net6.0` (o pacote mira .NET Core 3.0; net9.0 NÃO resolve).
- `<LangVersion>11</LangVersion>` se usar raw string literals.
- Atenção: máquina sem fonte NuGet configurada dá `NU1100` enganoso — conferir
  `dotnet nuget list source` antes de suspeitar do pacote.

## Operações validadas ao vivo (Painel-RM.pbix, 15 tabelas)

| Operação | API | Resultado |
|---|---|---|
| Listar tabelas/colunas/medidas | `model.Tables` | OK — 15 tabelas lidas |
| Ler query M de partição | `(Partition.Source as MPartitionSource).Expression` | OK — SQL nativo íntegro, com `#(lf)` |
| Criar tabela com fonte M | `new Table + MPartitionSource` + `model.SaveChanges()` | OK |
| Executar o M (carga real) | `table.RequestRefresh(RefreshType.Full)` + `SaveChanges()` | OK — motor executou o M |
| Remover tabela | `model.Tables.Remove(t)` + `SaveChanges()` | OK — modelo idêntico ao original |

## Comportamentos observados

- O motor adiciona uma coluna interna `RowNumber` a cada tabela criada (contagem de
  colunas fica +1 em relação às declaradas). Normal, invisível na UI.
- `SaveChanges()` altera apenas o modelo EM MEMÓRIA do Power BI Desktop. O `.pbix` em
  disco só muda quando o usuário salva no app. Fechar sem salvar = rollback total.
- O Power BI Desktop reflete as mudanças feitas via TOM na UI (painel Campos) sem
  precisar reiniciar — às vezes exige clicar em outra área para re-renderizar.
- Leitura offline (arquivo fechado) das queries M é possível com `pbixray` (Python,
  read-only): o `DataModel` do .pbix é um backup ABF comprimido com XPress9 e não é
  editável offline com segurança — por isso a via TOM (arquivo aberto) é a única
  rota de ESCRITA viável de ETL.

## Tabela calendário — intervalo sempre dinâmico

Padrão de `dim_calendario` (T-SQL) documentado em detalhe em
`../../gerar-modelo-tmdl/SKILL.md` (seção "Tabela calendário"): `@DATA_INICIO`/
`@DATA_FIM` calculados via `MIN`/`MAX` da data-fonte da fato (ex: `DATAADMISSAO`),
nunca fixados como literal. Usar esse mesmo padrão ao ajustar `dim_calendario`
via TOM num modelo já aberto.
