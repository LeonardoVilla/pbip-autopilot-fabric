# Exemplo: banco_edu — dataset de teste do pipeline

Modelo de dados acadêmico/financeiro usado para validar o pipeline
`pbip-autopilot-fabric` ponta a ponta, do banco ao painel.

## Conteúdo

| Arquivo | O que é |
|---|---|
| `ddl_novas_tabelas.sql` | DDL das 3 tabelas adicionadas (`dim_calendario`, `matriz_curricular`, `mensalidades`) |
| `gerar_dados_banco_edu.py` | Gerador reproduzível (seed=42) que escala o banco com dados coerentes por 7 semestres |
| `medidas-dax.md` | Catálogo de medidas DAX — o que vive no modelo semântico do `.pbip` |
| `modelo-semantico.md` | Esquema (2 fatos + dimensões conformadas), relacionamentos e as armadilhas de ambiguidade |
| `dashboard_banco_edu.html` | Painel analítico interativo (referência visual dos visuais e KPIs) |

## Como reproduzir o banco

Pré-requisitos: MySQL/MariaDB local (testado no XAMPP, MariaDB 10.4), Python com `pymysql`.

```bash
# 1. Partir do banco banco_edu com o schema-semente (18 tabelas)
# 2. Criar as 3 tabelas novas
mysql -u root banco_edu < ddl_novas_tabelas.sql
# 3. Popular com dados coerentes (idempotente: aborta se já houver >10 alunos)
python gerar_dados_banco_edu.py
```

## O modelo em números (após o gerador)

~75 alunos · 1.425 matrículas · 1.850 aulas · 17.344 frequências · 4.260 notas ·
2.038 mensalidades · dim_calendario 2023-2026. Integridade validada: zero órfãos,
status da matrícula alinhado à média, `faltas` = ausências em frequências.

## Descobertas de integridade (por que este exemplo existe)

O `banco_edu` original tinha o schema íntegro (23 FKs, grafo conexo) mas 7 tabelas
vazias. Foi escalado para servir de modelo de teste realista. Ver
[modelo-semantico.md](modelo-semantico.md) para o ponto de atenção do caminho
duplo `alunos ↔ turmas` que exige decidir o relacionamento ativo no Power BI.

## Próximo passo do pipeline

Com o banco pronto, a skill `gerar-modelo-tmdl` escreve o modelo (tabelas +
partições M via `MySQL.Database`, medidas de `medidas-dax.md`, relacionamentos de
`modelo-semantico.md`) e a `gerar-visuais-pbir` escreve os visuais do painel —
gerando o `.pbip` que abre no Power BI Desktop.
