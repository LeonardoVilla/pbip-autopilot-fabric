using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.AnalysisServices.Tabular;

// etl-tom — injeta e gerencia tabelas/ETL (Power Query M) no modelo Tabular
// da instancia local de Analysis Services que o Power BI Desktop mantem aberta.
//
// Comandos:
//   etl-tom list [--port N]
//   etl-tom export-m --out <dir> [--port N]
//   etl-tom add-table --name <nome> --m <arquivo.m> --columns "Col:tipo,..." [--refresh] [--port N]
//   etl-tom remove-table --name <nome> [--port N]
//   etl-tom refresh-table --name <nome> [--port N]
//
// Tipos de coluna: string | int64 | double | decimal | datetime | boolean

Console.OutputEncoding = Encoding.UTF8;

if (args.Length == 0)
{
    PrintUsage();
    return 1;
}

var command = args[0];
var opts = ParseOptions(args.Skip(1).ToArray());

int port;
if (opts.TryGetValue("port", out var portStr))
{
    port = int.Parse(portStr);
}
else
{
    var discovered = DiscoverPorts();
    if (discovered.Count == 0)
    {
        Console.Error.WriteLine("[ERRO] Nenhuma instancia local do Analysis Services (msmdsrv.exe) encontrada. O Power BI Desktop esta aberto com um .pbix carregado?");
        return 2;
    }
    if (discovered.Count > 1)
    {
        Console.Error.WriteLine($"[ERRO] {discovered.Count} instancias encontradas nas portas: {string.Join(", ", discovered)}. Especifique com --port.");
        return 2;
    }
    port = discovered[0];
    Console.WriteLine($"[INFO] Porta descoberta automaticamente: {port}");
}

using var server = new Server();
server.Connect($"Provider=MSOLAP;Data Source=localhost:{port};");

if (server.Databases.Count == 0)
{
    Console.Error.WriteLine("[ERRO] Instancia conectada mas sem modelo carregado.");
    return 2;
}

var db = server.Databases[0];
var model = db.Model;

try
{
    switch (command)
    {
        case "list":
            return CmdList(model);
        case "export-m":
            return CmdExportM(model, opts);
        case "add-table":
            return CmdAddTable(model, opts);
        case "remove-table":
            return CmdRemoveTable(model, opts);
        case "refresh-table":
            return CmdRefreshTable(model, opts);
        case "add-relationship":
            return CmdAddRelationship(model, opts);
        case "list-relationships":
            return CmdListRelationships(model);
        case "add-measure":
            return CmdAddMeasure(model, opts);
        case "add-measure-table":
            return CmdAddMeasureTable(model, opts);
        case "list-measures":
            return CmdListMeasures(model);
        case "add-calc-column":
            return CmdAddCalcColumn(model, opts);
        case "update-m":
            return CmdUpdateM(model, opts);
        default:
            Console.Error.WriteLine($"[ERRO] Comando desconhecido: {command}");
            PrintUsage();
            return 1;
    }
}
finally
{
    server.Disconnect();
}

// ─── Comandos ────────────────────────────────────────────────────────────────

static int CmdList(Model model)
{
    Console.WriteLine($"Modelo: {model.Database.Name}");
    foreach (Table t in model.Tables)
    {
        var kind = t.Partitions.Count > 0 && t.Partitions[0].Source is MPartitionSource ? "M" : "outro";
        Console.WriteLine($"  {t.Name} | colunas: {t.Columns.Count} | medidas: {t.Measures.Count} | fonte: {kind}");
    }
    return 0;
}

static int CmdExportM(Model model, Dictionary<string, string> opts)
{
    if (!opts.TryGetValue("out", out var outDir))
    {
        Console.Error.WriteLine("[ERRO] --out <dir> obrigatorio para export-m");
        return 1;
    }
    Directory.CreateDirectory(outDir);
    int count = 0;
    foreach (Table t in model.Tables)
    {
        foreach (Partition p in t.Partitions)
        {
            if (p.Source is MPartitionSource m)
            {
                var safe = string.Join("_", t.Name.Split(Path.GetInvalidFileNameChars()));
                var path = Path.Combine(outDir, $"{safe}.m");
                File.WriteAllText(path, m.Expression, Encoding.UTF8);
                Console.WriteLine($"[OK] {path}");
                count++;
            }
        }
    }
    Console.WriteLine($"[OK] {count} queries M exportadas para {outDir}");
    return 0;
}

static int CmdAddTable(Model model, Dictionary<string, string> opts)
{
    if (!opts.TryGetValue("name", out var name) ||
        !opts.TryGetValue("m", out var mFile) ||
        !opts.TryGetValue("columns", out var columnsSpec))
    {
        Console.Error.WriteLine("[ERRO] add-table exige --name, --m <arquivo.m> e --columns \"Col:tipo,...\"");
        return 1;
    }
    if (model.Tables.Find(name) != null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{name}' ja existe no modelo. Use remove-table antes, ou outro nome.");
        return 1;
    }
    var mExpression = File.ReadAllText(mFile, Encoding.UTF8);

    var table = new Table { Name = name };
    table.Partitions.Add(new Partition
    {
        Name = name,
        Source = new MPartitionSource { Expression = mExpression }
    });

    foreach (var colDef in columnsSpec.Split(','))
    {
        var parts = colDef.Split(':', 2);
        if (parts.Length != 2)
        {
            Console.Error.WriteLine($"[ERRO] Definicao de coluna invalida: '{colDef}'. Formato: Nome:tipo");
            return 1;
        }
        table.Columns.Add(new DataColumn
        {
            Name = parts[0].Trim(),
            SourceColumn = parts[0].Trim(),
            DataType = ParseDataType(parts[1].Trim())
        });
    }

    model.Tables.Add(table);
    model.SaveChanges();
    Console.WriteLine($"[OK] Tabela '{name}' criada com {table.Columns.Count} coluna(s).");

    if (opts.ContainsKey("refresh"))
    {
        table.RequestRefresh(RefreshType.Full);
        model.SaveChanges();
        Console.WriteLine($"[OK] Refresh executado — o M foi processado pelo motor.");
    }
    else
    {
        Console.WriteLine("[INFO] Tabela criada sem refresh. Rode 'refresh-table' ou atualize no Power BI Desktop para carregar os dados.");
    }
    return 0;
}

static int CmdRemoveTable(Model model, Dictionary<string, string> opts)
{
    if (!opts.TryGetValue("name", out var name))
    {
        Console.Error.WriteLine("[ERRO] remove-table exige --name");
        return 1;
    }
    var table = model.Tables.Find(name);
    if (table == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{name}' nao encontrada.");
        return 1;
    }
    // Remover primeiro os relacionamentos que apontam para/desta tabela,
    // senao o SaveChanges falha com "Relationship points to deleted table".
    var deps = model.Relationships
        .OfType<SingleColumnRelationship>()
        .Where(r => r.FromTable == table || r.ToTable == table)
        .ToList();
    foreach (var r in deps)
    {
        Console.WriteLine($"[INFO] Removendo relacionamento dependente: {r.FromTable.Name}.{r.FromColumn.Name} -> {r.ToTable.Name}.{r.ToColumn.Name}");
        model.Relationships.Remove(r);
    }
    model.Tables.Remove(table);
    model.SaveChanges();
    Console.WriteLine($"[OK] Tabela '{name}' removida ({deps.Count} relacionamento(s) dependente(s) removido(s)).");
    return 0;
}

static int CmdUpdateM(Model model, Dictionary<string, string> opts)
{
    // --name <tabela> --m <arquivo.m> [--refresh]
    // Troca SO a expressao M da particao (fonte de dados), preservando
    // colunas calculadas, medidas e relacionamentos da tabela.
    if (!opts.TryGetValue("name", out var name) || !opts.TryGetValue("m", out var mFile))
    {
        Console.Error.WriteLine("[ERRO] update-m exige --name e --m <arquivo.m>");
        return 1;
    }
    var table = model.Tables.Find(name);
    if (table == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{name}' nao encontrada.");
        return 1;
    }
    // achar a particao com fonte M
    Partition? mPart = null;
    foreach (Partition p in table.Partitions)
    {
        if (p.Source is MPartitionSource)
        {
            mPart = p;
            break;
        }
    }
    if (mPart == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{name}' nao tem particao com fonte M (Power Query).");
        return 1;
    }
    var novaM = File.ReadAllText(mFile, Encoding.UTF8);
    ((MPartitionSource)mPart.Source).Expression = novaM;
    model.SaveChanges();
    Console.WriteLine($"[OK] Expressao M de '{name}' atualizada (colunas calculadas e relacionamentos preservados).");

    if (opts.ContainsKey("refresh"))
    {
        table.RequestRefresh(RefreshType.Full);
        model.SaveChanges();
        Console.WriteLine($"[OK] Refresh de '{name}' concluido.");
    }
    else
    {
        Console.WriteLine("[INFO] Sem refresh. Rode refresh-table ou atualize no Power BI Desktop.");
    }
    return 0;
}

static int CmdRefreshTable(Model model, Dictionary<string, string> opts)
{
    if (!opts.TryGetValue("name", out var name))
    {
        Console.Error.WriteLine("[ERRO] refresh-table exige --name");
        return 1;
    }
    var table = model.Tables.Find(name);
    if (table == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{name}' nao encontrada.");
        return 1;
    }
    table.RequestRefresh(RefreshType.Full);
    model.SaveChanges();
    Console.WriteLine($"[OK] Refresh de '{name}' concluido.");
    return 0;
}

static int CmdAddRelationship(Model model, Dictionary<string, string> opts)
{
    // --from "Tabela.Coluna" --to "Tabela.Coluna"
    // Cria relacionamento M:1 (padrao estrela: from=fato/many, to=dimensao/one).
    if (!opts.TryGetValue("from", out var fromSpec) || !opts.TryGetValue("to", out var toSpec))
    {
        Console.Error.WriteLine("[ERRO] add-relationship exige --from \"Tabela.Coluna\" e --to \"Tabela.Coluna\"");
        return 1;
    }

    var (fromTable, fromCol) = SplitTableColumn(fromSpec);
    var (toTable, toCol) = SplitTableColumn(toSpec);

    var ft = model.Tables.Find(fromTable);
    var tt = model.Tables.Find(toTable);
    if (ft == null) { Console.Error.WriteLine($"[ERRO] Tabela '{fromTable}' nao encontrada."); return 1; }
    if (tt == null) { Console.Error.WriteLine($"[ERRO] Tabela '{toTable}' nao encontrada."); return 1; }
    if (ft.Columns.Find(fromCol) == null) { Console.Error.WriteLine($"[ERRO] Coluna '{fromCol}' nao existe em '{fromTable}'."); return 1; }
    if (tt.Columns.Find(toCol) == null) { Console.Error.WriteLine($"[ERRO] Coluna '{toCol}' nao existe em '{toTable}'."); return 1; }

    var rel = new SingleColumnRelationship
    {
        FromColumn = ft.Columns[fromCol],
        ToColumn = tt.Columns[toCol],
        FromCardinality = RelationshipEndCardinality.Many,
        ToCardinality = RelationshipEndCardinality.One,
        CrossFilteringBehavior = CrossFilteringBehavior.OneDirection,
        IsActive = true
    };
    model.Relationships.Add(rel);
    model.SaveChanges();
    Console.WriteLine($"[OK] Relacionamento criado: {fromTable}.{fromCol} (M) -> {toTable}.{toCol} (1)");
    return 0;
}

static int CmdListRelationships(Model model)
{
    if (model.Relationships.Count == 0)
    {
        Console.WriteLine("(sem relacionamentos)");
        return 0;
    }
    foreach (var r in model.Relationships)
    {
        if (r is SingleColumnRelationship scr)
        {
            var active = scr.IsActive ? "ativo" : "inativo";
            Console.WriteLine($"  {scr.FromTable.Name}.{scr.FromColumn.Name} -> {scr.ToTable.Name}.{scr.ToColumn.Name} ({active})");
        }
    }
    return 0;
}

static (string table, string column) SplitTableColumn(string spec)
{
    var idx = spec.LastIndexOf('.');
    if (idx < 0) throw new ArgumentException($"Formato invalido: '{spec}'. Use \"Tabela.Coluna\".");
    return (spec[..idx], spec[(idx + 1)..]);
}

static int CmdAddMeasureTable(Model model, Dictionary<string, string> opts)
{
    // Cria uma tabela vazia (sem linhas) para hospedar medidas — padrao "measure table".
    // --name <nome>
    if (!opts.TryGetValue("name", out var name))
    {
        Console.Error.WriteLine("[ERRO] add-measure-table exige --name");
        return 1;
    }
    if (model.Tables.Find(name) != null)
    {
        Console.WriteLine($"[INFO] Tabela '{name}' ja existe — reutilizando para medidas.");
        return 0;
    }
    // Tabela calculada com uma linha dummy (padrao para measure-only tables no Power BI)
    var table = new Table { Name = name };
    table.Partitions.Add(new Partition
    {
        Name = name,
        Source = new CalculatedPartitionSource { Expression = "{BLANK()}" }
    });
    table.Columns.Add(new CalculatedTableColumn
    {
        Name = "Coluna",
        SourceColumn = "[Value1]",
        DataType = DataType.String,
        IsHidden = true
    });
    model.Tables.Add(table);
    model.SaveChanges();
    Console.WriteLine($"[OK] Tabela de medidas '{name}' criada.");
    return 0;
}

static int CmdAddMeasure(Model model, Dictionary<string, string> opts)
{
    // --table <tabela host> --name <nome medida> --dax <arquivo.dax> [--format "0.0%"]
    if (!opts.TryGetValue("table", out var tableName) ||
        !opts.TryGetValue("name", out var measureName) ||
        !opts.TryGetValue("dax", out var daxFile))
    {
        Console.Error.WriteLine("[ERRO] add-measure exige --table, --name e --dax <arquivo.dax>");
        return 1;
    }
    var table = model.Tables.Find(tableName);
    if (table == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela host '{tableName}' nao encontrada. Crie com add-measure-table antes.");
        return 1;
    }
    if (table.Measures.Find(measureName) != null)
    {
        Console.Error.WriteLine($"[ERRO] Medida '{measureName}' ja existe em '{tableName}'.");
        return 1;
    }
    var dax = File.ReadAllText(daxFile, Encoding.UTF8).Trim();
    var measure = new Measure { Name = measureName, Expression = dax };
    if (opts.TryGetValue("format", out var fmt))
        measure.FormatString = fmt;
    table.Measures.Add(measure);
    model.SaveChanges();
    Console.WriteLine($"[OK] Medida '{measureName}' criada em '{tableName}'.");
    return 0;
}

static int CmdAddCalcColumn(Model model, Dictionary<string, string> opts)
{
    // --table <tabela> --name <nome coluna> --dax <arquivo.dax>
    // Cria uma coluna CALCULADA (DAX) numa tabela existente. Serve de eixo/categoria.
    if (!opts.TryGetValue("table", out var tableName) ||
        !opts.TryGetValue("name", out var colName) ||
        !opts.TryGetValue("dax", out var daxFile))
    {
        Console.Error.WriteLine("[ERRO] add-calc-column exige --table, --name e --dax <arquivo.dax>");
        return 1;
    }
    var table = model.Tables.Find(tableName);
    if (table == null)
    {
        Console.Error.WriteLine($"[ERRO] Tabela '{tableName}' nao encontrada.");
        return 1;
    }
    if (table.Columns.Find(colName) != null)
    {
        Console.Error.WriteLine($"[ERRO] Coluna '{colName}' ja existe em '{tableName}'. Remova ou use outro nome.");
        return 1;
    }
    var dax = File.ReadAllText(daxFile, Encoding.UTF8).Trim();
    var column = new CalculatedColumn
    {
        Name = colName,
        Expression = dax,
        DataType = DataType.String
    };
    table.Columns.Add(column);
    model.SaveChanges();
    Console.WriteLine($"[OK] Coluna calculada '{colName}' criada em '{tableName}'.");
    return 0;
}

static int CmdListMeasures(Model model)
{
    int total = 0;
    foreach (Table t in model.Tables)
    {
        foreach (Measure mea in t.Measures)
        {
            Console.WriteLine($"  [{t.Name}] {mea.Name}");
            total++;
        }
    }
    if (total == 0) Console.WriteLine("(sem medidas)");
    return 0;
}

// ─── Utilitarios ─────────────────────────────────────────────────────────────

static DataType ParseDataType(string type) => type.ToLowerInvariant() switch
{
    "string" => DataType.String,
    "int64" or "int" => DataType.Int64,
    "double" => DataType.Double,
    "decimal" => DataType.Decimal,
    "datetime" or "date" => DataType.DateTime,
    "boolean" or "bool" => DataType.Boolean,
    _ => throw new ArgumentException($"Tipo de coluna desconhecido: '{type}'. Use: string|int64|double|decimal|datetime|boolean")
};

static Dictionary<string, string> ParseOptions(string[] args)
{
    var opts = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
    for (int i = 0; i < args.Length; i++)
    {
        if (args[i].StartsWith("--"))
        {
            var key = args[i][2..];
            if (i + 1 < args.Length && !args[i + 1].StartsWith("--"))
            {
                opts[key] = args[++i];
            }
            else
            {
                opts[key] = "true"; // flag sem valor (ex: --refresh)
            }
        }
    }
    return opts;
}

static List<int> DiscoverPorts()
{
    var ports = new List<int>();
    var pids = Process.GetProcessesByName("msmdsrv").Select(p => p.Id).ToHashSet();
    if (pids.Count == 0) return ports;

    var psi = new ProcessStartInfo("netstat", "-ano")
    {
        RedirectStandardOutput = true,
        UseShellExecute = false,
        CreateNoWindow = true
    };
    using var proc = Process.Start(psi)!;
    var output = proc.StandardOutput.ReadToEnd();
    proc.WaitForExit();

    // linhas do tipo:  TCP    127.0.0.1:57505   0.0.0.0:0   LISTENING   19252
    var rx = new Regex(@"TCP\s+127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING\s+(\d+)");
    foreach (Match m in rx.Matches(output))
    {
        var port = int.Parse(m.Groups[1].Value);
        var pid = int.Parse(m.Groups[2].Value);
        if (pids.Contains(pid) && !ports.Contains(port))
            ports.Add(port);
    }
    return ports;
}

static void PrintUsage()
{
    Console.WriteLine("""
        etl-tom — ETL/Power Query no Power BI Desktop via TOM (Analysis Services local)

        Uso:
          etl-tom list [--port N]
          etl-tom export-m --out <dir> [--port N]
          etl-tom add-table --name <nome> --m <arquivo.m> --columns "Col:tipo,..." [--refresh] [--port N]
          etl-tom remove-table --name <nome> [--port N]
          etl-tom refresh-table --name <nome> [--port N]
          etl-tom add-relationship --from "Tabela.Coluna" --to "Tabela.Coluna" [--port N]
          etl-tom list-relationships [--port N]
          etl-tom add-measure-table --name <nome> [--port N]
          etl-tom add-measure --table <host> --name <nome> --dax <arq.dax> [--format "0.0%"] [--port N]
          etl-tom add-calc-column --table <tabela> --name <nome> --dax <arq.dax> [--port N]
          etl-tom update-m --name <tabela> --m <arq.m> [--refresh] [--port N]
          etl-tom list-measures [--port N]

        Tipos de coluna: string | int64 | double | decimal | datetime | boolean
        Relacionamento: --from = lado "muitos" (fato), --to = lado "um" (dimensao).
        Sem --port, a porta e descoberta automaticamente (exige exatamente 1 instancia aberta).

        IMPORTANTE: as alteracoes ficam no modelo em memoria do Power BI Desktop.
        Salve o arquivo no Power BI Desktop (Ctrl+S) para persistir no .pbix.
        """);
}
