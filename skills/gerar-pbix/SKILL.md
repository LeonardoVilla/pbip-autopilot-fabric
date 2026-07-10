---
name: gerar-pbix
description: Slash command para gerar um arquivo .pbix do Power BI via Python. Use quando o usuário digitar /gerar-pbix ou pedir para criar/gerar um painel Power BI programaticamente.
argument-hint: <nome-do-projeto> [arquivo-template.pbix]
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, PowerShell]
version: 1.0.0
---

# /gerar-pbix — Gerador de Painéis Power BI

Gera um arquivo `.pbix` válido do Power BI Desktop via Python, partindo de um `.pbix` template existente e substituindo apenas o `Report/Layout`.

## Fluxo de execução

Quando o usuário invocar `/gerar-pbix <projeto>`, siga estes passos na ordem:

### 1. Coletar informações

Pergunte (se não fornecidas nos argumentos):
- **Nome do projeto** — será usado no nome do arquivo de saída
- **Arquivo template** `.pbix` — deve ser um arquivo local com DataModel embutido (não conectado ao cloud). Recomendado: um `.pbix` já conectado à fonte de dados com os relacionamentos criados.
- **Fonte de dados** — caminho da planilha Excel (`.xlsx`) ou banco de dados
- **Páginas** — nomes das páginas do painel
- **Visuais** de cada página — tipo (card, donut, barras, linha, área, combo, tabela, matriz, gauge, slicer), campos e tabelas
- **Medidas DAX** — se o modelo já tiver medidas criadas, pergunte os nomes exatos; use `measure_ref("Nome")` em vez do nome de coluna (ver seção "Referências de campo" no template)

### 2. Inspecionar o template

Antes de gerar, leia os metadados do template:

```python
import zipfile
with zipfile.ZipFile(template_path, 'r') as z:
    entries = [(i.filename, i.compress_type, i.file_size) for i in z.infolist()]
    # Verificar: tem 'SecurityBindings'? Tem 'DataModel'? Tem 'RemoteArtifacts'?
```

**BLOQUEANTE — NÃO usar o template se:**
- Contiver entrada `RemoteArtifacts` no ZIP → DataModel está no cloud, não local → os visuais não vão funcionar
- Estiver corrompido ou com senha

**Inspecionar os campos das tabelas** (se fonte for Excel):
```python
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile(xlsx_path, 'r') as z:
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
    ss_list = [''.join(t.text or '' for t in si.findall('.//m:t', ns)) for si in ss.findall('m:si', ns)]
    # Para cada sheet, ler a primeira linha (headers)
```

Sempre confirme os nomes exatos dos campos (incluindo acentos, espaços, símbolos Unicode como `Nº`, `Ação`) antes de usar no `prototypeQuery`.

### 3. Gerar o script Python

Crie o script em `C:\Users\LEONAR~1.VIL\AppData\Local\Temp\claude\gerar_pbix_<projeto>.py` seguindo o template da referência. Consulte [template-script.md](references/template-script.md) para o código completo.

### 4. Executar e testar

```powershell
python "C:\Users\LEONAR~1.VIL\AppData\Local\Temp\claude\gerar_pbix_<projeto>.py"
```

O script deve terminar chamando `validate_pbix(OUTPUT, expected_page_count=...)` — isso reabre
o `.pbix` gerado e confere SecurityBindings, compress_type do DataModel, RemoteArtifacts e se o
Layout é JSON válido, pegando os erros mais comuns antes de abrir no Power BI Desktop.

### 5. Instruções para o usuário

Após gerar:
1. Abrir o `.pbix` gerado no Power BI Desktop
2. Clicar **OK** no aviso "Risco potencial à segurança" — isso é normal e esperado
3. Verificar cada visual e reportar qualquer erro

---

## Regras críticas (NÃO violar)

Consulte [template-script.md](references/template-script.md) para detalhes de implementação. Resumo:

1. **SecurityBindings DEVE ser zerado** — gravar `b''` no lugar do blob DPAPI. Sem isso: `MashupValidationError`.
2. **Layout em UTF-16 LE** sem BOM — `json.dumps(...).encode('utf-16-le')`
3. **Preservar `compress_type`** de cada entrada do ZIP. DataModel deve ficar STORED (compress_type=0).
4. **Usar `copy.copy(ZipInfo)`** para cada entrada — nunca criar um `ZipInfo` do zero.
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
