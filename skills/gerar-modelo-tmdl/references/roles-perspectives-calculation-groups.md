# Roles (RLS/OLS), Perspectives e Calculation Groups

> **STATUS: 📄 doc oficial — NUNCA testado por nós.** Diferente do resto desta
> skill (tabelas/medidas/relacionamentos, validados em produção no
> `banco_edu` e no SIPLAN), o conteúdo abaixo vem só da especificação TMDL
> pública — nenhum destes três recursos foi gerado e reaberto com sucesso no
> Power BI Desktop por este projeto ainda. Tratar como esqueleto de partida,
> não como padrão validado. Gerar um exemplo mínimo e testar no Desktop antes
> de usar em produção — e então promover a ✅ (mesmo processo já seguido pro
> resto da skill).

Estrutura alvo já previa a pasta (`cultures/ roles/` na seção "Estrutura
alvo" do `SKILL.md` principal), mas nunca detalhamos o conteúdo. Isso cobre a
lacuna.

## Roles — segurança em nível de linha (RLS) e coluna (OLS)

Arquivo: `definition/roles/<NomeRole>.tmdl` — um arquivo por role.

```tmdl
role 'Gerente Regional'
	modelPermission: read

	tablePermission Vendas = [Regiao] = "Sul"

	member 'dominio\usuario1'
	member 'dominio\usuario2'
```

- `modelPermission`: `none | read | readRefresh | refresh | administrator`.
- `tablePermission <Tabela> = <expressão DAX>`: o filtro de RLS — só linhas
  onde a expressão avalia `TRUE` ficam visíveis pro role. Um `role` pode ter
  várias `tablePermission`, uma por tabela filtrada.
- `columnPermission` (OLS, segurança de coluna) fica **dentro** de
  `tablePermission`, não direto no `role`.
- `member`: identidade (usuário/grupo) associada ao role — opcional gerar
  aqui; pode ser atribuído depois pelo admin do workspace no serviço.

## Perspectives — subconjuntos do modelo pra clientes específicos

Arquivo: `definition/perspectives/<Nome>.tmdl` — um arquivo por perspective.
Controla só **visibilidade ao conectar** (não é segurança — RLS/OLS é quem
restringe dado de verdade).

```tmdl
perspective 'Financeiro'

	perspectiveTable Vendas
		perspectiveMeasure 'Total Vendas'
		perspectiveColumn Valor

	perspectiveTable Clientes
		perspectiveColumn Nome
```

- `perspectiveTable` só lista os objetos que devem aparecer nessa
  perspective — omitir um objeto da tabela é como escondê-lo pra quem
  conecta filtrando por essa perspective.
- Objetos visíveis (tabelas/medidas/colunas) sem `Model.Perspectives.Any()`
  atribuídas disparam a regra `LAYOUT_ADD_TO_PERSPECTIVES` do Tabular Editor
  BPA (ver `validar-pbip`) — **só relevante se o modelo já tiver ao menos uma
  perspective**; sem nenhuma, a regra não se aplica.

## Calculation Groups — DAX reutilizável (ex.: seletor de Time Intelligence)

Ao contrário de roles/perspectives, **não tem pasta própria** — fica dentro
do arquivo da tabela que hospeda o grupo (convenção: uma tabela dedicada, ex.
`'Calculo Tempo'`), com `calculationGroup` aninhado em `table` e
`calculationItem` aninhado em `calculationGroup`:

```tmdl
table 'Calculo Tempo'
	lineageTag: guid-calc-group

	calculationGroup
		calculationItem 'Atual' = SELECTEDMEASURE()

		calculationItem 'Ano Anterior' =
				CALCULATE (
				    SELECTEDMEASURE(),
				    SAMEPERIODLASTYEAR ( 'Data'[Data] )
				)

		calculationItem 'YTD' =
				CALCULATE (
				    SELECTEDMEASURE(),
				    DATESYTD ( 'Data'[Data] )
				)

	column 'Nome Cálculo'
		dataType: string
		lineageTag: guid-calc-column
		sourceColumn: Nome Cálculo
```

- Cada `calculationItem` é uma "lente" DAX aplicada por cima de qualquer
  medida selecionada (`SELECTEDMEASURE()`), sem precisar duplicar a medida
  pra cada variação temporal.
- `formatStringDefinition` (expressão DAX que calcula o format string
  dinamicamente) é comum aqui — útil quando o formato varia por item
  selecionado (ex.: `%` pra crescimento, moeda pra valor absoluto).
- A tabela host do calculation group normalmente fica oculta/sem dados reais
  — só existe pra hospedar a coluna "seletora" que aparece como slicer no
  relatório.

## Quando vale investir nisso

Nenhum painel gerado por esta skill até agora (`banco_edu`, SIPLAN) precisou
de RLS, perspectives ou calculation groups — são recursos de modelo maduro
(múltiplos consumidores com acesso diferenciado, ou biblioteca de medidas
com muitas variações temporais). Se um projeto real pedir um desses, gerar o
esqueleto acima, testar no Desktop, documentar o que quebrou/funcionou aqui
mesmo (seguindo o padrão ✅/📄 já usado no resto da skill).
