# Modelo semântico — banco_edu (para o `.pbip`)

Como as tabelas do `banco_edu` se organizam no modelo tabular do Power BI, e as
decisões de relacionamento que o Desktop vai exigir. Este é o insumo da skill
`gerar-modelo-tmdl` para escrever os relacionamentos em TMDL.

## Esquema (dois fatos, dimensões conformadas)

```
                 dim_calendario (tabela de datas)
                        │ (data → colunas de data dos fatos)
                        │
  departamentos ──< cursos ──< turmas ──< turmas_disciplinas ──< matriculas >── alunos
        │                                        │  │                 │            │
        │                                        │  └─ professores    │            │
        └──< disciplinas ──────────────< ────────┘                    │            │
                                                                       │            │
   FATO ACADÊMICO:  matriculas ──< notas >── avaliacoes                │            │
                    matriculas ──< frequencias >── aulas ── salas ── blocos         │
                    matriculas ──1:1── resumo_matriculas                            │
                                                                                    │
   FATO FINANCEIRO: mensalidades >──────────────────────────────────────────────── alunos
```

- **Grão acadêmico**: `matriculas` (aluno × oferta de disciplina). `notas`,
  `frequencias` e `resumo_matriculas` penduram nela.
- **Grão financeiro**: `mensalidades` (aluno × competência mensal).
- **Dimensões conformadas** (compartilhadas pelos dois fatos): `alunos`,
  `dim_calendario`.

## Relacionamentos a declarar (todos 1→N, filtro único)

| De (1) | Para (N) | Coluna | Ativo? |
|---|---|---|---|
| departamentos | cursos | departamento_id | sim |
| departamentos | disciplinas | departamento_id | sim |
| departamentos | professores | departamento_id | sim |
| cursos | turmas | curso_id | sim |
| turmas | turmas_disciplinas | turma_id | sim |
| disciplinas | turmas_disciplinas | disciplina_id | sim |
| professores | turmas_disciplinas | professor_id | sim |
| turmas_disciplinas | matriculas | turma_disciplina_id | sim |
| alunos | matriculas | aluno_id | sim |
| avaliacoes | notas | avaliacao_id | sim |
| matriculas | notas | matricula_id | sim |
| aulas | frequencias | aula_id | sim |
| matriculas | frequencias | matricula_id | sim |
| matriculas | resumo_matriculas | matricula_id | sim |
| salas | aulas | sala_id | sim |
| blocos | salas | bloco_id | sim |
| alunos | mensalidades | aluno_id | sim |
| **alunos** | **turmas** | **turma_principal_id** | **INATIVO** ⚠ |
| dim_calendario | mensalidades | data → competencia | sim |
| dim_calendario | matriculas | data → data_matricula | INATIVO (2ª data) |
| dim_calendario | aulas | data → data_aula | INATIVO (2ª data) |

## ⚠ As duas armadilhas de ambiguidade

1. **Caminho duplo alunos ↔ turmas** (o ponto que levantei na análise do banco):
   - direto: `alunos[turma_principal_id] → turmas`
   - indireto: `alunos → matriculas → turmas_disciplinas → turmas`

   O Desktop não deixa os dois ativos. **Decisão adotada:** manter ativo o caminho
   pela **matrícula** (é o que dá o desempenho por turma/curso real) e deixar
   `turma_principal_id` **inativo**, ativando sob demanda com `USERELATIONSHIP`
   quando precisar da "turma principal" do aluno:

   ```dax
   Alunos por Turma Principal =
   CALCULATE ( [Total Alunos], USERELATIONSHIP ( alunos[turma_principal_id], turmas[turma_id] ) )
   ```

2. **`dim_calendario` com vários fatos/datas**: uma tabela de datas só tem um
   relacionamento ativo por fato. Ativo em `mensalidades[competencia]` e em
   `matriculas`/`aulas` a data fica inativa — usar `USERELATIONSHIP` nas medidas
   que precisam filtrar aquele fato por data. Alternativa (mais simples para
   dashboards): uma cópia de `dim_calendario` por fato (role-playing).

## Colunas calculadas úteis (no TMDL)

```dax
-- em 'notas', para o histograma de distribuição
Faixa Nota =
SWITCH ( TRUE (),
    notas[nota] < 2, "0-2", notas[nota] < 4, "2-4",
    notas[nota] < 6, "4-6", notas[nota] < 8, "6-8", "8-10" )

-- em 'alunos', faixa etária
Faixa Etária =
VAR i = DATEDIFF ( alunos[data_nascimento], TODAY (), YEAR )
RETURN SWITCH ( TRUE (), i < 20, "até 19", i < 23, "20-22", i < 26, "23-25", "26+" )
```

## Marcar tabela de datas

`dim_calendario` → **Marcar como tabela de datas** usando a coluna `data`
(contínua 2023-01-01 a 2026-12-31, sem lacunas — validado). Sem isso, as medidas
de time intelligence da seção 5 de [medidas-dax.md](medidas-dax.md) não funcionam.
