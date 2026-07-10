# Catálogo de medidas DAX — banco_edu

Medidas que alimentam o [painel analítico](https://claude.ai/code/artifact/5dbff90f-c1ec-4865-a329-de5e35b9b93d).
São o que vive na tabela de medidas do modelo semântico (TMDL) do `.pbip` — cada
KPI e visual do dashboard mapeia 1:1 para uma medida abaixo.

Convenção: criar uma tabela vazia `_Medidas` (grupo de medidas) e hospedar todas
nela. Nomes com espaços e acento seguem o padrão do modelo (Unicode exato).

## 1. Contagens base

```dax
Total Alunos       = DISTINCTCOUNT ( alunos[aluno_id] )
Alunos Ativos      = CALCULATE ( [Total Alunos], alunos[status] = "ativo" )
Alunos Evadidos    = CALCULATE ( [Total Alunos], alunos[status] = "evadido" )
Total Matrículas   = COUNTROWS ( matriculas )
Total Turmas       = DISTINCTCOUNT ( turmas[turma_id] )
Total Professores  = DISTINCTCOUNT ( professores[professor_id] )
Total Disciplinas  = DISTINCTCOUNT ( disciplinas[disciplina_id] )
```

## 2. Desempenho acadêmico

```dax
Matrículas Avaliadas = COUNTROWS ( resumo_matriculas )

Aprovados   = CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "aprovado" )
Reprovados  = CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "reprovado" )
Recuperação = CALCULATE ( [Matrículas Avaliadas], resumo_matriculas[status_final] = "recuperacao" )

Taxa de Aprovação  = DIVIDE ( [Aprovados],  [Matrículas Avaliadas] )
Taxa de Reprovação = DIVIDE ( [Reprovados], [Matrículas Avaliadas] )

Média Global = AVERAGE ( resumo_matriculas[media_ponderada] )
Nota Média   = AVERAGE ( notas[nota] )

-- Nota média ponderada pelo peso da avaliação (fonte da verdade quando houver reabertura)
Média Ponderada =
DIVIDE (
    SUMX ( notas, notas[nota] * RELATED ( avaliacoes[peso] ) ),
    SUMX ( notas, RELATED ( avaliacoes[peso] ) )
)
```

## 3. Frequência

```dax
Presenças = CALCULATE ( COUNTROWS ( frequencias ), frequencias[presente] = 1 )
Frequência Média % = DIVIDE ( [Presenças], COUNTROWS ( frequencias ) )
Total Faltas = SUM ( matriculas[faltas] )
Faltas Média por Matrícula = DIVIDE ( [Total Faltas], [Total Matrículas] )
```

## 4. Financeiro

```dax
Receita Prevista = SUM ( mensalidades[valor] )
Receita Recebida = CALCULATE ( SUM ( mensalidades[valor_pago] ), mensalidades[status] = "pago" )
Taxa de Recebimento = DIVIDE ( [Receita Recebida], [Receita Prevista] )

Mensalidades Vencidas = CALCULATE ( COUNTROWS ( mensalidades ), mensalidades[data_vencimento] <= TODAY () )
Mensalidades em Atraso = CALCULATE ( COUNTROWS ( mensalidades ), mensalidades[status] = "atrasado" )
Inadimplência % = DIVIDE ( [Mensalidades em Atraso], [Mensalidades Vencidas] )

Valor em Atraso = CALCULATE ( SUM ( mensalidades[valor] ), mensalidades[status] = "atrasado" )
Ticket Médio = DIVIDE ( [Receita Prevista], DISTINCTCOUNT ( mensalidades[aluno_id] ) )
```

## 5. Time intelligence (exigem `dim_calendario` marcada como tabela de datas)

Marcar `dim_calendario` como *tabela de datas* (coluna `data`) e criar o
relacionamento com as colunas de data dos fatos (ver [modelo-semantico.md](modelo-semantico.md)).

```dax
Receita Recebida YTD = TOTALYTD ( [Receita Recebida], dim_calendario[data] )

Receita Mês Anterior =
CALCULATE ( [Receita Recebida], DATEADD ( dim_calendario[data], -1, MONTH ) )

Receita MoM % =
DIVIDE ( [Receita Recebida] - [Receita Mês Anterior], [Receita Mês Anterior] )

Matrículas Acumuladas =
CALCULATE ( [Total Matrículas], DATESYTD ( dim_calendario[data] ) )

Inadimplência Média 3M =
AVERAGEX ( DATESINPERIOD ( dim_calendario[data], MAX ( dim_calendario[data] ), -3, MONTH ), [Inadimplência %] )
```

## 6. Medidas de apresentação (formatação / dinâmicas)

```dax
-- Rótulo KPI de aprovação com cor condicional (usar em "Cor da fonte" via regra)
Aprovação Status =
VAR t = [Taxa de Aprovação]
RETURN SWITCH ( TRUE (), t >= 0.75, "🟢", t >= 0.6, "🟡", "🔴" )

-- Título dinâmico
Título Período =
"Período letivo — " & MIN ( turmas[ano_letivo] ) & " a " & MAX ( turmas[ano_letivo] )
```

## Mapa medida → visual do dashboard

| Visual | Medida(s) |
|---|---|
| KPI Alunos ativos | `Alunos Ativos`, `Total Alunos` |
| KPI Média global | `Média Global` |
| KPI Aprovação | `Taxa de Aprovação`, `Taxa de Reprovação` |
| KPI Frequência | `Frequência Média %` |
| KPI Receita recebida | `Receita Recebida`, `Taxa de Recebimento` |
| KPI Inadimplência | `Inadimplência %`, `Mensalidades em Atraso` |
| Resultado por semestre | `Aprovados`, `Recuperação`, `Reprovados` × `dim_calendario`/`turmas` |
| Média por semestre | `Média Global` |
| Distribuição de notas | `COUNTROWS(notas)` por faixa (coluna calculada de faixa) |
| Receita mensal | `Receita Prevista`, `Receita Recebida` × `dim_calendario[ano_mes]` |
| Inadimplência mensal | `Inadimplência %` × `dim_calendario` |
| Receita por departamento | `Receita Prevista`, `Receita Recebida` × `departamentos` |
