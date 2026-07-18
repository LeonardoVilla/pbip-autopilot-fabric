---
name: pbip-context
description: Contexto técnico do formato PBIP (Power BI Project) - estrutura de pastas, TMDL, PBIR, o que versionar, armadilhas conhecidas. Injetar antes de qualquer geração com gerar-modelo-tmdl ou gerar-visuais-pbir.
allowed-tools: [Read, Glob, Grep]
version: 0.2.0
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
