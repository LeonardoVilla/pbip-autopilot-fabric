# Rename seguro de tabela/coluna/medida — checklist de cascata

Renomear um objeto do modelo (tabela, coluna ou medida) num projeto PBIP não é
uma operação local — o nome se espalha por dezenas de arquivos em
`*.SemanticModel/` e `*.Report/`, em formatos diferentes (TMDL, DAX-texto,
JSON aninhado, strings compactas). Esquecer um lugar não quebra a abertura do
Desktop na hora — quebra silenciosamente um visual, um bookmark ou um
drillthrough que só aparece muito depois. Este checklist existe porque cada
item abaixo já foi um bug real catalogado por terceiros
([`data-goblin/power-bi-agentic-development`](https://github.com/data-goblin/power-bi-agentic-development),
skill `pbip` › `rename-cascade.md`) — adaptado aqui para o nosso fluxo (edição
direta de texto via `Read`/`Edit`/`Grep`, sem CLI dedicado tipo `te`/`pbir`).

**Regra geral**: monte o mapa `nome antigo → nome novo` primeiro, aplique no
modelo (TMDL), depois no relatório (PBIR), e só então rode a checagem de
"sobrou alguma referência" no final. Não faça find-and-replace cego —
alguns lugares (`nativeQueryRef` num rename de TABELA, a chave de dicionário
em culture files) **não devem mudar**, e um replace ingênuo os corromperia.

## Renomear TABELA (ex.: `Customers` → `Customer`)

No modelo (`*.SemanticModel/definition/`):
1. Nome do arquivo: `tables/Customers.tmdl` → `tables/Customer.tmdl`
2. `table Customers` → `table Customer` (respeitar regra de aspas — só
   citar entre `'...'` se tiver espaço/começar com dígito/caractere especial)
3. `partition Customers = m` → `partition Customer = m` (nome da partição
   costuma coincidir com o da tabela)
4. `model.tmdl`: linha `ref table Customers` (se existir) **e** a
   `annotation PBI_QueryOrder = [...]` (lista de nomes — o nome antigo
   aparece ali como string)
5. `relationships.tmdl`: `fromColumn`/`toColumn` no formato
   `Tabela.'Coluna'` — trocar o lado que referencia a tabela renomeada
6. DAX em **todos** os `.tmdl` (medidas/colunas calculadas de qualquer
   tabela): o nome pode aparecer sem aspas (`Customers[Coluna]`) ou entre
   aspas simples (`'Customers'[Coluna]`) — DAX aceita as duas formas mesmo
   pra nomes sem espaço. Buscar as duas.

No relatório (`*.Report/definition/`), em **todo** `visual.json`/`page.json`:
7. `SourceRef.Entity` (toda referência de campo aponta pra uma entidade)
8. `queryRef` no formato `"Tabela.Coluna"` (a string inteira, não só o
   `Entity`)
9. `nativeQueryRef` **NÃO muda** num rename de tabela — só tem o nome da
   coluna/medida, sem prefixo de tabela. Não tocar.
10. `filterConfig.From[].Entity` (filtros de página e de visual)
11. Conditional formatting: `Entity` aninhado dentro de
    `objects.*.properties.*.expr.Conditional.Cases[].*.Measure.Expression.SourceRef.Entity`
12. `sortDefinition.sort[].field.*.Expression.SourceRef.Entity` — **fica fora**
    do `queryState`/projeções normais, é dos lugares mais esquecidos; buscar
    a string `"sortDefinition"` em todos os `visual.json` do projeto
13. SparklineData: string compacta
    `SparklineData(<Tabela>.<Medida>_[<TabelaAgrupamento>.<Hierarquia>.<Nível>])`
    **e** a versão estruturada em JSON (`field.SparklineData.Measure.Measure.Expression.SourceRef.Entity`
    + `field.SparklineData.Groupings[].HierarchyLevel...SourceRef.Entity`) —
    as duas formas coexistem, atualizar ambas
14. `bookmarks/*.bookmark.json` — **dois** lugares por filtro:
    `filter.From[].Entity` E `expression.Column.Expression.SourceRef.Entity`
    (são referências independentes, as duas citam a entidade)
15. `bookmarks/*.bookmark.json` → bloco `highlight` (quando existe): a
    **chave** de `dataMap` no formato `"Tabela.Coluna"` E o
    `filterExpressionMetadata.expressions[].Column.Expression.SourceRef.Entity`
16. `reportExtensions.json`: `entities[].name` (nome da entidade estendida)
    **e** `entities[].measures[].references.measures[].entity` — o campo de
    referência interno também cita o nome, é fácil esquecer
17. `semanticModelDiagramLayout.json`: chave `nodeIndex`
18. Culture files (`cultures/<locale>.tmdl`, bloco `linguisticMetadata` JSON):
    `Binding.ConceptualEntity`. **A chave do dicionário externo
    (`"customers.account_type"`) é só um lookup gerado — NÃO precisa bater
    com o nome real da tabela, só o `ConceptualEntity` interno importa.**
19. Arquivos `.dax` soltos em **duas pastas diferentes** —
    `<Nome>.SemanticModel/DAXQueries/*.dax` E
    `<Nome>.Report/DAXQueries/*.dax` — fácil esquecer a segunda

## Renomear MEDIDA (ex.: `# Customers` → `# Active Customers`)

Mais simples que tabela — não tem arquivo/partição pra renomear, mas
**`nativeQueryRef` MUDA aqui** (ao contrário do rename de tabela):

1. `measure '# Customers' = ...` → `measure '# Active Customers' = ...`
2. DAX de outras medidas que referenciam por `[# Customers]` (sem prefixo de
   tabela — medida é sempre referenciada sem qualificador)
3. Visual JSON: `Property: "# Customers"`, `queryRef: "Tabela.# Customers"`
   **e** `nativeQueryRef: "# Customers"` — as três mudam
4. `reportExtensions.json`: `{ "entity": "...", "name": "# Customers" }`

## Renomear COLUNA

Mesma lógica do rename de medida (Property/queryRef/nativeQueryRef mudam),
mas atenção a mais dois pontos específicos de coluna:
- `sourceColumn` no TMDL só muda se o nome da coluna NA FONTE (SQL/M) também
  mudou — não confundir com o nome de exibição (`column 'Nome Novo'` pode
  manter `sourceColumn: nome_antigo_no_banco`)
- `sortByColumn` de outras colunas pode referenciar a coluna renomeada

## Casos especiais

- **Nomes com caracteres especiais** (`Δ`, `%`, `;`, parênteses) em medidas
  são comuns — cuidado ao escapar em regex de busca.
- **Evitar match parcial**: ao renomear `Order` num modelo que também tem
  `Orders`/`Order Status`, usar fronteira de palavra
  (`grep -rP "\bOrder\b"`), não busca solta.
- **Rename em massa** (ex.: aplicar convenção de nomes em todas as tabelas):
  montar o mapa completo primeiro, aplicar UM rename por vez, rodar a
  checagem de "sobrou referência" (abaixo) antes do próximo — não empilhar
  vários renames sem validar entre eles.

## Verificação final (rodar depois de qualquer rename)

```
# Nome antigo não deveria sobrar em nenhum arquivo do projeto
grep -r "NomeAntigo" "Projeto.Report/" "Projeto.SemanticModel/" \
  --include="*.json" --include="*.tmdl" --include="*.dax"

# Com fronteira de palavra (evita falso positivo em nomes parecidos)
grep -rP "\bNomeAntigo\b" "Projeto.Report/" "Projeto.SemanticModel/"

# Referência entre aspas simples em DAX
grep -r "'NomeAntigo'" --include="*.tmdl" --include="*.dax"
```

Se a busca não voltar nada (exceto, no caso de tabela, a chave de dicionário
de culture files — item 18 acima, que é esperado ficar diferente), a cascata
está completa. **Fechar o Desktop antes de editar** (regra de sempre) e abrir
só depois de terminar o checklist inteiro, não a cada arquivo.
