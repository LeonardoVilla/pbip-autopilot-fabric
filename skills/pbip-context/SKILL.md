---
name: pbip-context
description: Contexto técnico do formato PBIP (Power BI Project) - estrutura de pastas, TMDL, PBIR, o que versionar, armadilhas conhecidas, diagnóstico de visual em branco, ciclo salvar/fechar/reabrir automatizado com o Desktop. Injetar antes de qualquer geração com gerar-modelo-tmdl ou gerar-visuais-pbir, ao investigar um visual/card que não mostra dado mesmo com o modelo aparentemente correto, ou ao editar um projeto PBIP existente alternando entre TOM (Desktop aberto) e PBIR (Desktop fechado).
allowed-tools: [Read, Glob, Grep]
version: 0.4.0
---

# pbip-context — Regras do formato PBIP

Equivalente ao `pbix-context` do projeto anterior, mas para o mundo novo:
as regras aqui evitam os erros que quebram um projeto PBIP.

## Anatomia de um projeto

```
MeuPainel.pbip                 # ponteiro (JSON pequeno) para as pastas abaixo
MeuPainel.SemanticModel/       # modelo (TMDL)  → skill gerar-modelo-tmdl
MeuPainel.Report/              # relatório (PBIR) → skill gerar-visuais-pbir
```

### Report "thick" vs "thin"

- **Thick report** (cenário padrão desta skill até agora): `.Report/` +
  `.SemanticModel/` juntos na mesma pasta, `definition.pbir` aponta o modelo
  por **`byPath`** (relativo, pasta local). Todo projeto gerado por
  `gerar-modelo-tmdl`/`gerar-visuais-pbir` até hoje (`banco_edu`, SIPLAN) é
  thick.
- **Thin report**: só `.Report/` — sem `.SemanticModel/` próprio — apontando
  via `definition.pbir` `byConnection` pra um modelo **já publicado** (no
  serviço/Fabric). Vários relatórios podem ser thin do mesmo modelo
  compartilhado (cenário de BI gerenciado: um modelo central, múltiplos
  relatórios de equipes diferentes reusando-o).
- Isso importa pra Fase 2 do roadmap (deploy via Fabric REST API): a API só
  aceita `byConnection`, então um projeto thick gerado localmente precisa
  virar thin (ou o `.pbir` trocar pra `byConnection`) na hora do deploy
  programático — ver detalhe em `gerar-modelo-tmdl/SKILL.md` (seção
  "`byPath` vs `byConnection`").

## Regras que NÃO podem ser violadas

1. **Desktop fechado durante a geração.** O Desktop mantém o projeto em
   memória e sobrescreve as pastas ao salvar — edições externas simultâneas
   são perdidas. (Substitui o "salvar com Ctrl+S" do mundo TOM: agora o
   perigo é o inverso.)
2. **`.pbi/` fora do git**: `localSettings.json` e `cache.abf` são locais.
   O `cache.abf` é só cache de dados — apagar não corrompe nada.
3. **Dados não vão no projeto.** PBIP versiona METADADOS. A carga acontece
   no Refresh (Desktop) ou no serviço. Todo pipeline termina com
   "abrir → Atualizar → salvar/publicar".
4. **`$schema` e versões**: copiar sempre de arquivos gerados pelo próprio
   Desktop instalado — nunca fixar versões de schema de memória.
5. **TMDL usa indentação TAB significativa**; PBIR usa JSON UTF-8 comum.
   Nada de UTF-16LE, SecurityBindings ou compress_type — esses problemas
   eram do `.pbix` e não existem aqui.
6. **UTF-8 SEM BOM em todo arquivo gerado** (TMDL e JSON) — um BOM prefixado
   quebra o parser de alguns caminhos (ex.: leitura via ferramentas de
   terceiros que não esperam o marcador). Ao escrever com Python, usar
   `encoding="utf-8"` (nunca `"utf-8-sig"`, que adiciona BOM) e
   `newline="\n"` explícito — caso contrário o modo texto padrão do Windows
   converte `\n` para `\r\n` na gravação. Os geradores de referência
   (`examples/banco_edu/gerar_*.py`) já seguem esse padrão; replicar em
   scripts novos. O `.gitattributes` do repo normaliza quebra de linha no
   histórico (`* text=auto eol=lf`) — isso não impede o Desktop de regravar
   em CRLF ao salvar, só evita que o diff do git fique ruidoso por causa
   disso.

## Diferenças-chave vs. o mundo .pbix (projeto anterior)

| Aspecto | .pbix (antes) | .pbip (agora) |
|---|---|---|
| Editar modelo | TOM com Desktop ABERTO | arquivos TMDL, Desktop FECHADO |
| Editar visuais | ZIP + Layout UTF-16LE | JSONs PBIR documentados |
| SecurityBindings | zerar (`b''`) senão MashupValidationError | não existe |
| Erro de visual | .pbix pode corromper | erro isolado no visual |
| Undo | fechar sem salvar | `git restore` |
| Validação | `validate_pbix()` caseiro | abrir no Desktop (parser oficial) |

## Renomear tabela/coluna/medida com segurança

Um rename se espalha por dezenas de arquivos (TMDL, JSON de visual, bookmark,
tema de relatório) em formatos diferentes — esquecer um lugar não quebra a
abertura na hora, quebra silenciosamente um visual/bookmark/drillthrough
muito depois. Antes de renomear qualquer objeto do modelo, seguir o checklist
completo em [references/rename-cascade.md](references/rename-cascade.md)
(19 pontos pra rename de tabela, incluindo os mais fáceis de esquecer:
`sortDefinition`, SparklineData, os dois `Entity` de cada bookmark, e os
dois locais de `DAXQueries/`).

## Ciclo salvar → fechar → editar → reabrir com autonomia (validado ago/2026)

O ciclo de trabalho real com PBIP alterna entre dois modos que se excluem: o
Desktop **aberto** (para editar modelo/medidas via TOM, `gerar-etl-tom`) e o
Desktop **fechado** (para editar PBIR, regra #1 acima). Boa parte desse ciclo
dá para automatizar sem pedir para o usuário clicar em nada — o único passo
sem API oficial é o "Ctrl+S" dentro do Desktop, mas mesmo esse dá para
simular. Guia completo, do mais para o menos confiável:

1. **Abrir o `.pbip`**: `Start-Process "<caminho>\Projeto.pbip"` (PowerShell).
2. **Aguardar carregar**: fazer polling do processo `msmdsrv.exe` (o motor
   Analysis Services local só sobe depois que o Desktop termina de abrir o
   modelo) em vez de um `sleep` fixo — carregar pode levar de alguns segundos
   a alguns minutos dependendo do tamanho do modelo:
   ```bash
   for i in $(seq 1 24); do
     tasklist 2>/dev/null | grep -qi msmdsrv && break
     sleep 10
   done
   ```
3. **Salvar (Ctrl+S) sem clique manual**: ativar a janela do processo e
   enviar o atalho via PowerShell:
   ```powershell
   Add-Type -AssemblyName Microsoft.VisualBasic
   Add-Type -AssemblyName System.Windows.Forms
   [Microsoft.VisualBasic.Interaction]::AppActivate(<PID>)
   Start-Sleep -Milliseconds 500
   [System.Windows.Forms.SendKeys]::SendWait("^s")
   ```
   Validado em campo: `AppActivate` pode retornar vazio mesmo quando funciona
   (não é um indicador confiável de sucesso) — a forma de confirmar que
   salvou de verdade é conferir o **timestamp de modificação** de um arquivo
   PBIR conhecido (ex. `visual.json` que acabou de ser editado) depois de
   alguns segundos, não confiar no retorno do comando. **Risco conhecido**:
   `SendKeys` depende da janela estar em primeiro plano/não minimizada — se
   isso falhar silenciosamente (nenhum arquivo muda de timestamp), cair para
   pedir o Ctrl+S manual ao usuário como fallback, não insistir tentando de
   novo às cegas.
4. **Fechar sem salvar** (para descartar um estado intermediário/de teste, ou
   antes de editar PBIR depois de já ter confirmado o save do passo 3):
   `Stop-Process -Id <PID> -Force`. Não pede confirmação de diálogo porque o
   projeto já foi salvo no passo anterior — só fecha o processo.
5. **Editar os arquivos PBIR/TMDL** normalmente (Desktop já fechado).
6. **Reabrir e validar**: repetir o passo 1-2, e usar `gerar-etl-tom`
   `dax-query` para validar os números via medida antes de pedir confirmação
   visual — economiza um ciclo inteiro de "abrir → olhar → relatar engano"
   quando o problema não é visual, é de dado/fórmula (ver seção de
   diagnóstico abaixo).

**O que continua exigindo o usuário, e por quê**: só a **confirmação visual
final** (o print da tela) — nenhuma API oficial (TOM, ADOMD, ODBC) renderiza
o layout do relatório como o motor de visuais do Desktop faz, então não tem
como "ver" um gráfico programaticamente. Deixar claro ao usuário, ao pedir
essa validação, que já foi tudo testado numericamente antes (via `dax-query`)
e que o print é só a checagem final de layout/formatação — não uma repetição
do trabalho de diagnóstico.

## Diagnosticando um visual "(Em branco)" quando a medida calcula certo (validado ago/2026)

Sintoma: um card/gráfico mostra "(Em branco)" ou "0,00", mas outros visuais na
mesma página que usam medidas de outras tabelas funcionam normalmente. Antes de
suspeitar do DAX ou do relacionamento, **isolar a medida do visual**:

1. Com o Desktop aberto, rodar a medida sozinha via `gerar-etl-tom` `dax-query`:
   ```powershell
   dotnet run --project tools/EtlTom -- dax-query --expr "EVALUATE ROW(\"x\", [NomeDaMedida])"
   ```
   Se o valor vier correto isolado, **o modelo/DAX está saudável** — o problema
   é de contexto de filtro no relatório, não de fórmula. Testar também com
   `SUMMARIZECOLUMNS` (a forma real que o Power BI gera para a maioria dos
   visuais) para descartar diferença de comportamento entre `ROW` e a query
   real do visual.
2. Se isolado funciona mas o visual na tela não, **procurar um slicer com
   seleção travada** — inclusive slicers `isHidden: true` (usados como
   filtro de controle interno, invisíveis na tela, então o usuário não tem
   como notar ou desmarcar a seleção pela UI). No `visual.json` do slicer,
   `objects.general[].properties.filter.filter.Where[].Condition.In.Values`
   guarda a seleção salva — se tiver um valor fixo (ex.: um ano específico)
   e esse valor não bater mais com `TODAY()`/dado atual, todo visual cujo
   filtro efetivo dependa dessa coluna fica vazio, mesmo sem nenhum
   `filterConfig` visível nos próprios visuais afetados nem na página.
   Correção: remover o bloco `filter` inteiro de dentro de `general`
   (Desktop fechado) — o slicer volta a não ter seleção (mostra tudo).
3. Um segundo padrão, mais raro: um `filterConfig.filters[]` do tipo
   `"Advanced"` **sem nenhuma condição** (`Values`/`Where` vazios ou
   ausentes) no próprio visual quebrado. Um filtro Advanced vazio é tratado
   como "excluir tudo", não "sem filtro" — remover o bloco `filterConfig`
   inteiro se não houver seleção real dentro dele.
4. Ao investigar, **não confiar cegamente no relato de um agente auxiliar**
   sobre qual campo/valor está travado — reabrir o `visual.json` apontado e
   ler o `Property`/`Value` reais antes de aplicar a correção. Um relatório
   com o campo ou o valor trocado (ex.: apontar "Mês" quando o travado é
   "Ano") leva a mexer no arquivo errado.

Esse padrão (dado correto no modelo, ausente na tela) é diferente de um
`(Blank)` genuíno por falta de dado — sempre validar com `dax-query` antes de
decidir qual dos dois é o caso.

## Requisito de versão

Power BI Desktop release **maio/2026 ou superior** (PBIR como formato padrão).
Em versões anteriores, habilitar em Opções → Recursos em versão preliminar.
GA do PBIR previsto para Q3/2026 — após o GA, é o único formato suportado.

## Erros de abertura do Desktop que NÃO são do projeto (validado jul/2026)

Ao abrir/atualizar um `.pbip` com fontes externas reais (banco, API), nem
todo erro do Desktop é do TMDL/PBIR — dois de ambiente confirmados na prática,
que custaram várias rodadas de "abrir → erro → corrigir o modelo" até se
revelarem **não relacionados ao modelo**:

### `OutOfMemoryException` em pontos aleatórios e não relacionados

Se o Desktop trava/crasha com `System.OutOfMemoryException` em componentes
completamente diferentes a cada tentativa (ex.: `WebView2Interop.BuildInteropCall`
parseando JSON, `PowerBITelemetryUserActionHelper.CreateEventForActionId`,
`ReportException` capturando GDI) **enquanto os dados/modelo carregam com
sucesso todas as vezes** (a seção "Formulas" do relatório de erro mostra as
queries M avaliadas normalmente) — o problema não é o modelo. É quase certeza
**falta de arquivo de paginação (page file) no Windows**.

Diagnóstico (PowerShell):
```powershell
$os = Get-CimInstance Win32_OperatingSystem
$os | Select-Object @{n='CommitLimitGB';e={[math]::Round($_.TotalVirtualMemorySize/1MB,2)}}, `
                     @{n='CommitFreeGB';e={[math]::Round($_.FreeVirtualMemory/1MB,2)}}
```
Se `CommitLimitGB` ≈ RAM física total (sem margem de swap) e `CommitFreeGB`
estiver na casa de poucas centenas de MB — mesmo com RAM física "livre"
aparentando folga no Gerenciador de Tarefas — é isso: o commit limit do
Windows inteiro está no talo, e QUALQUER processo pode estourar OOM em
qualquer alocação, não só o Power BI.

Correção: reativar o gerenciamento automático do page file e reiniciar o
Windows (a mudança só vale após reboot):
```powershell
Invoke-CimMethod -ClassName Win32_PageFileSetting -MethodName Create `
    -Arguments @{Name="C:\pagefile.sys"; InitialSize=8192; MaximumSize=16384}
```
(o método `Win32_ComputerSystem.Put()` para `AutomaticManagedPagefile` costuma
falhar com "Falha genérica" via WMI — criar o pagefile diretamente funciona e
liga o gerenciamento automático como efeito colateral.)

### Cache do WebView2 corrompido

Sintoma parecido (crash na camada de UI, ex. erro em `globalize.cultures.js`
ou outro componente WebView2) mas com o commit de memória saudável. Fix
independente do acima, também seguro e reversível — fechar o Desktop e
apagar a pasta (recriada sozinha na próxima abertura):
```
%LOCALAPPDATA%\Microsoft\Power BI Desktop\WebView2\
```

### Ordem de investigação recomendada

Quando o Desktop crashar/travar ao abrir um `.pbip` com fonte externa real
(não um erro de parsing/engine claro, tipo os do `gerar-modelo-tmdl`):
1. Ler a mensagem — se citar TMDL/relacionamento/medida, é o modelo (ver
   `gerar-modelo-tmdl/SKILL.md`).
2. Se for `OutOfMemoryException` em código de telemetria/UI/interop, ou
   travamento sem mensagem, **checar o commit de memória primeiro** (acima)
   antes de suspeitar do modelo ou de drivers.
3. Só depois, se o commit de memória estiver saudável, investigar cache do
   WebView2 ou driver da fonte de dados.
