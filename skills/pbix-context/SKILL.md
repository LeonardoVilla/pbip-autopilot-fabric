---
name: pbix-context
description: Esta skill deve ser ativada automaticamente quando o usuário mencionar geração de Power BI via Python, arquivos .pbix, MashupValidationError, SecurityBindings, Report/Layout, ou pedir para criar painéis Power BI programaticamente. Fornece contexto técnico validado para evitar erros conhecidos.
version: 1.0.0
---

# Contexto: Geração de .pbix via Python

## Regras inegociáveis (violá-las quebra o arquivo)

1. **Zerar SecurityBindings** — sempre gravar `b''` na entrada `SecurityBindings` do ZIP. O blob DPAPI original assina o Layout; qualquer Layout diferente invalida a assinatura → `MashupValidationError`. O aviso "Risco potencial à segurança" ao abrir é normal e esperado.

2. **Layout em UTF-16 LE** — `json.dumps(layout).encode('utf-16-le')` — sem BOM, sem UTF-8.

3. **Preservar compress_type de cada entrada** — usar `copy.copy(ZipInfo)` e `compress_type=item.compress_type`. O `DataModel` deve ficar STORED (compress_type=0); recomprimi-lo quebra o arquivo.

4. **Template com DataModel local** — o `.pbix` template não pode ter entrada `RemoteArtifacts` no ZIP (indicativo de DataModel no cloud). Verificar antes com `[i.filename for i in zipfile.ZipFile(path).infolist()]`.

5. **Alias de tabela fixos** — montar `TABLE_ALIAS = {"NOME DA TABELA": "alias", ...}` explicitamente. Nunca derivar o alias com `table[0].lower()` — tabelas com espaços, acentos ou trailing spaces geram aliases errados que o Power BI rejeita silenciosamente (visual aparece vazio).

6. **Nomes de campos exatos** — sempre inspecionar o XML do `.xlsx` para confirmar Unicode exato antes de usar no `prototypeQuery`. Campos como `Nº` (U+00BA), `AÇÕES` (cedilha+til), `BRIGADA DE INCÊNDIO ` (Ê + espaço final) não são óbvios.

7. **Medidas DAX vs. colunas cruas** — quando o modelo já tem uma medida (ex: `Gauge Target Termometro`), referencie-a com `measure_ref("Nome da Medida")` em vez de agregar uma coluna. Isso gera `{"Measure": {...}}` no `prototypeQuery` em vez de `{"Aggregation": {"Column": {...}}}`. Gauges em particular quase sempre usam medidas para min/max/target — são regras de negócio, não colunas cruas.

8. **Validar antes de abrir** — depois de `pack_pbix()`, rodar `validate_pbix(output, expected_page_count=N)` reabre o ZIP e confirma SecurityBindings vazio, DataModel STORED, ausência de RemoteArtifacts e Layout como JSON UTF-16LE válido. Pega os erros da tabela abaixo em segundos, antes de testar na UI do Power BI Desktop.

## Template validado

O script completo e todas as funções de visual estão na skill `gerar-pbix`:
`skills/gerar-pbix/references/template-script.md` (deste mesmo plugin).

## Histórico de erros e soluções

| Sintoma | Causa raiz | Solução |
|---------|-----------|---------|
| `MashupValidationError` | SecurityBindings não zerado | `zout.writestr(sb, b'')` |
| "arquivo corrompido" | DataModel recomprimido | Preservar compress_type=0 |
| `MashupValidationError` persistente | Template tem RemoteArtifacts | Trocar template |
| Visual vazio / "arraste campos" | Nome de tabela/campo errado | Inspecionar XML do Excel |
| Visual com alias errado | `table[0].lower()` em tabela com espaço | Usar TABLE_ALIAS dict |
| `UnicodeEncodeError` no print | Emoji em terminal Windows cp1252 | Usar `[OK]` em vez de `✅` |
| Gauge/card com valor errado ou zerado | Coluna crua usada onde o modelo espera medida DAX | Trocar por `measure_ref("Nome da Medida")` |

## Visuais e helpers disponíveis (além dos originais)

`line_vc`, `area_vc`, `combo_vc` (colunas+linha), `table_vc` (tableEx), `matrix_vc` (pivotTable),
`gauge_vc`, `nav_button_vc` (navegação entre páginas). Helpers: `measure_ref()` (medida DAX em
qualquer campo de valor), `grid()` (posições automáticas), `equals_filter()` +
`apply_page_filters()`/`apply_visual_filters()` (filtros sem slicer visível), `validate_pbix()`
(checagem pós-geração), `build_pages_with_nav()` (ordinal automático para múltiplas páginas).
