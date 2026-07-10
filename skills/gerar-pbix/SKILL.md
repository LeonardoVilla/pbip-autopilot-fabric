---
name: gerar-pbix
description: Slash command para gerar um arquivo .pbix do Power BI via Python. Use quando o usuário digitar /gerar-pbix ou pedir para criar/gerar um painel Power BI programaticamente.
argument-hint: <nome-do-projeto> [arquivo-template.pbix] [--novo-layout | --copiar-layout]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 1.1.0
---

# /gerar-pbix — Gerador de Painéis Power BI

Gera um arquivo `.pbix` válido do Power BI Desktop via Python, partindo de um `.pbix` template existente.

## Fluxo de execução

Quando o usuário invocar `/gerar-pbix <projeto>`, siga estes passos na ordem:

### 0. Verificar objetivo do usuário

- **`--copiar-layout` (padrão)**: copia o template .pbix, zera SecurityBindings e valida.
  Preserva TODO o layout original (páginas, visuais, imagens, conexões). Útil para:
  - Gerar uma cópia funcional de um painel existente
  - Resolver erro "MashupValidationError"
  - Quando o usuário só quer abrir o .pbix sem crash

- **`--novo-layout`**: substitui o Report/Layout por visuais novos. Útil para:
  - Gerar um painel novo com o mesmo DataModel do template
  - Customizar páginas/visuais sem perder as queries do modelo

### 1. Coletar informações

Pergunte (se não fornecidas nos argumentos):
- **Nome do projeto** — será usado no nome do arquivo de saída
- **Arquivo template** `.pbix` — deve ser um arquivo local com DataModel embutido (não conectado ao cloud). Recomendado: um `.pbix` já conectado à fonte de dados com os relacionamentos criados.
- **Modo**: copiar layout (padrão) ou novo layout
- **Se novo layout**:
  - **Fonte de dados** — caminho da planilha Excel (`.xlsx`) ou banco de dados
  - **Páginas** — nomes das páginas do painel
  - **Visuais** de cada página — tipo (card, donut, barras, linha, área, combo, tabela, matriz, gauge, slicer), campos e tabelas
  - **Medidas DAX** — se o modelo já tiver medidas criadas, pergunte os nomes exatos; use `measure_ref("Nome")` em vez do nome de coluna

### 2. Inspecionar o template

Antes de gerar, leia os metadados do template:

```python
import zipfile
with zipfile.ZipFile(template_path, 'r') as z:
    entries = {i.filename: i for i in z.infolist()}
    # Verificacoes obrigatorias:
    tem_datamodel  = "DataModel" in entries
    tem_security   = "SecurityBindings" in entries
    tem_remote     = any("RemoteArtifacts" in name for name in entries)
    tem_layout     = "Report/Layout" in entries
    dm_compress    = entries["DataModel"].compress_type if tem_datamodel else -1
```

**BLOQUEANTE — NÃO usar o template se:**
- Contiver entrada `RemoteArtifacts` no ZIP → DataModel está no cloud, não local → os visuais não vão funcionar
- Estiver corrompido ou com senha
- `DataModel` não existir ou `compress_type` não for 0 (STORED) — indica .pbix corrompido

### 3. Gerar o script Python

Crie o script seguindo o template da referência. Consulte [template-script.md](references/template-script.md) para o código completo.

#### Se `--copiar-layout` (padrão):

O script vai:
1. Copiar TODAS as entradas do template para o output
2. SecurityBindings → gravar `b''` (zero bytes)
3. DataModel → preservar com `compress_type` original (STORED)
4. Report/Layout → preservar como está
5. Validar o resultado

#### Se `--novo-layout`:

O script vai:
1. Copiar todas as entradas EXCETO Report/Layout
2. SecurityBindings → gravar `b''`
3. DataModel → preservar STORED
4. Report/Layout → substituir pelo novo layout gerado via funções do template
5. Validar o resultado

### 4. Executar e testar

```powershell
python "C:\Users\LEONAR~1.VIL\AppData\Local\Temp\claude\gerar_pbix_<projeto>.py"
```

O script DEVE terminar chamando `validate_pbix(OUTPUT)` — isso reabre
o `.pbix` gerado e confere:
- SecurityBindings está zerado (0 bytes)
- DataModel está STORED (compress_type=0)
- Não há RemoteArtifacts
- Layout é JSON UTF-16 LE válido
- Se `--novo-layout`: número de páginas e visuais conferem

### 5. Instruções para o usuário

Após gerar:
1. Abrir o `.pbix` gerado no Power BI Desktop
2. Clicar **OK** no aviso "Risco potencial à segurança" — isso é normal e esperado
3. Se aparecer diálogo de credenciais, configurar a fonte de dados
4. Clicar em **Atualizar**
5. Verificar cada visual e reportar qualquer erro

---

## Regras críticas (NÃO violar)

Consulte [template-script.md](references/template-script.md) para detalhes de implementação. Resumo:

1. **SecurityBindings DEVE ser zerado** — gravar `b''` no lugar do blob DPAPI. Sem isso: `MashupValidationError`.
2. **Layout em UTF-16 LE** sem BOM — `json.dumps(...).encode('utf-16-le')`
3. **Preservar `compress_type`** de cada entrada do ZIP. DataModel deve ficar STORED (compress_type=0).
4. **Usar `copy.copy(ZipInfo)`** para entradas do DataModel — nunca criar um `ZipInfo` do zero.
5. **Alias de tabela fixos** — nunca usar `table[0].lower()` como alias no `prototypeQuery`. Montar um dicionário `TABLE_ALIAS` explícito para cada tabela, especialmente as que têm espaços, acentos ou caracteres especiais.
6. **Nomes de campos com Unicode exato** — `Nº` = U+00BA, `AÇÕES`/`Ação` com cedilha e til. Sempre verificar no XML do Excel antes de usar.

---

## Erros comuns e soluções

| Erro ao abrir o .pbix | Causa | Solução |
|---|---|---|
| `MashupValidationError` | SecurityBindings não foi zerado | Gravar `b''` em SecurityBindings — `validate_pbix()` detecta antes de abrir |
| "arquivo corrompido" | DataModel recomprimido (DEFLATED) | Preservar compress_type=0 para DataModel — `validate_pbix()` detecta antes de abrir |
| `MashupValidationError` persistente | Template tem RemoteArtifacts | Trocar para template com DataModel local — `validate_pbix()` detecta antes de abrir |
| Visual vazio / "arraste campos" | Nome de tabela ou campo errado no prototypeQuery | Verificar nome exato no Excel XML |
| Visual com erro de alias | Tabela com espaço/acento e alias gerado automaticamente | Usar TABLE_ALIAS dictionary explícito |
| Aviso "Risco potencial" ao abrir | SecurityBindings zerado | Normal — clicar OK |
| Gauge/card com valor errado ou zerado | Usou coluna crua onde o modelo espera uma medida DAX | Trocar por `measure_ref("Nome da Medida")` |
| PBIP crasha ao abrir (`Non-null assertion failure: query`) | Bug da versão June 2026 do Desktop | Usar `--copiar-layout` para gerar .pbix diretamente (contorna o bug) |

## Catálogo de visuais

Além de `card_vc`, `donut_vc`, `bar_vc`, `slicer_vc`, `shape_vc`, `textbox_vc` (originais), o
template agora inclui: `line_vc`, `area_vc`, `combo_vc`, `table_vc`, `matrix_vc`, `gauge_vc`,
`nav_button_vc` (navegação entre páginas) e `image_vc` (ícones/logo). Todo campo de valor aceita
`measure_ref("Nome")` para usar uma medida DAX do modelo em vez de agregar uma coluna crua. Há
também `grid()` para calcular posições de uma grade automaticamente, e `equals_filter()` /
`apply_page_filters()` / `apply_visual_filters()` para filtros de página ou de visual sem slicer.
Ver [template-script.md](references/template-script.md) para assinaturas e exemplos de cada função.

## Imagens (ícones e logo) e estilo VILLA

- **Embutir imagens**: `register_image()` + `image_vc()` + `pack_pbix_with_images()` injetam
  ícones/logo no `.pbix` (arquivo em `RegisteredResources` + declaração em `resourcePackages`).
- **Buscar/baixar ícones**: `iconify_buscar()` / `iconify_png()` (RECOMENDADO — Iconify, licença
  livre, com busca) ou `baixar_flaticon()` (Flaticon, via URL que o usuário fornece). Iconify
  entrega SVG convertido para PNG por `resvg-py` (`pip install resvg-py`).
- **Preset VILLA**: `kpi_card_villa()` monta um KPI completo no estilo validado em produção —
  barra de acento colorida à esquerda + label colorido + número escuro + ícone opcional.
- **Design system**: cores, fontes, layout e assets em
  [design-system-villa.md](references/design-system-villa.md) e `assets/villa-turnover/`.