# Referência — PBIP conectado a API REST com token (validado)

Gerador de um projeto PBIP "só modelo" (sem visuais) onde **cada tabela é um
endpoint** de uma API REST, conectada ao vivo via Power Query. Validado abrindo
no Power BI Desktop (jun/2026). Padrão extraído do projeto SIPLAN (Django + DRF).

## Estrutura de arquivos gerada

```
<Projeto>.pbip                       # ponteiro
<Projeto>.SemanticModel/
  definition.pbism                   # {"version":"4.0","settings":{}}
  definition/
    database.tmdl                    # database <Nome> \n \tcompatibilityLevel: 1567
    model.tmdl                       # SÓ propriedades do modelo (sem ref!)
    expressions.tmdl                 # parâmetros + funções GetToken/GetApi
    tables/<Tabela>.tmdl             # 1 por endpoint (partição M)
<Projeto>.Report/
  definition.pbir                    # {"version":"4.0","datasetReference":{"byPath":{"path":"../<Projeto>.SemanticModel"}}}
  report.json                        # report vazio COM themeCollection.baseTheme
```

## model.tmdl (sem `ref` — crítico)

```tmdl
model Model
	culture: pt-BR
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: pt-BR
```

## expressions.tmdl (parâmetros + funções)

```tmdl
expression BaseUrl = "https://exemplo/api" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
	annotation PBI_ResultType = Text

expression ClientId = "SEU_ID" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
	annotation PBI_ResultType = Text

expression ClientSecret = "SEU_SECRET" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
	annotation PBI_ResultType = Text

expression GetToken =
		let
		    GetToken = () =>
		        let
		            corpo = "{""client_id"":""" & ClientId & """,""client_secret"":""" & ClientSecret & """}",
		            resposta = Web.Contents(BaseUrl & "/token/", [ Headers = [#"Content-Type" = "application/json"], Content = Text.ToBinary(corpo) ]),
		            json = Json.Document(resposta),
		            token = json[access_token]
		        in
		            token
		in
		    GetToken
	annotation PBI_ResultType = Function

expression GetApi =
		let
		    GetApi = (rota as text) as table =>
		        let
		            token = GetToken(),
		            resposta = Web.Contents(BaseUrl & "/" & rota & "/", [ Headers = [ Authorization = "Bearer " & token ] ]),
		            json = Json.Document(resposta),
		            tabela = if json is list then Table.FromList(json, Splitter.SplitByNothing(), null, null, ExtraValues.Error) else Table.FromList({json}, Splitter.SplitByNothing(), null, null, ExtraValues.Error)
		        in
		            tabela
		in
		    GetApi
	annotation PBI_ResultType = Function
```

(Indentação: M com 2 tabs sob `expression Nome =`.)

## tables/<Tabela>.tmdl (partição que chama GetApi + expand dinâmico)

```tmdl
table Turma
	partition Turma = m
		mode: import
		source =
				let
				    Fonte = GetApi("turmas"),
				    Expandida =
				        if Table.RowCount(Fonte) = 0 then Fonte
				        else Table.ExpandRecordColumn(Fonte, "Column1", Record.FieldNames(Fonte{0}[Column1]), Record.FieldNames(Fonte{0}[Column1]))
				in
				    Expandida

	annotation PBI_ResultType = Table
```

(M com 4 tabs sob `source =`. Sem declarar colunas: o expand dinâmico faz campos
novos do endpoint aparecerem sozinhos no Refresh.)

## report.json (vazio, mas com tema — senão erro de render)

```json
{
  "config": "{\"version\":\"5.43\",\"themeCollection\":{\"baseTheme\":{\"name\":\"CY23SU04\",\"version\":\"5.43\",\"type\":2}},\"activeSectionIndex\":0,\"settings\":{\"useStylableVisualContainerHeader\":true}}",
  "layoutOptimization": 0,
  "resourcePackages": [],
  "sections": [
    { "name": "pagina1", "displayName": "Página 1", "displayOption": 1, "filters": "[]", "ordinal": 0, "width": 1280, "height": 720, "config": "{\"visibility\":0}", "visualContainers": [] }
  ]
}
```

## Credenciais e refresh

- Os parâmetros podem vir com **valor default embutido** (client_id/secret) para o
  arquivo já abrir pronto. Se as credenciais forem sensíveis, gere o arquivo por
  um endpoint que **rotaciona o secret a cada download** (não guarda o secret em
  claro) — o download mais recente é o válido.
- **Autenticação de rede** (diálogo Anônimo/Windows/...): o Desktop pede uma vez
  por máquina. Para API que autentica pelo corpo/header, escolher **Anônimo**.
  Não é configurável pelo arquivo — documentar para o usuário.

## Erros reais que este padrão evita

| Erro no Desktop | Causa | Correção |
|---|---|---|
| `Unexpected line type: ReferenceObject` | `ref table`/`ref expression` no model.tmdl | remover as linhas `ref` |
| `Cannot read properties of undefined (reading 'customTheme')` | report.json sem `themeCollection` | adicionar `themeCollection.baseTheme` |
| modelo abre mas tabela vazia | JSON não expandido | `Table.ExpandRecordColumn` com `Record.FieldNames` |
