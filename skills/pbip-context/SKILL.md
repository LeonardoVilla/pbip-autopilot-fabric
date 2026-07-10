---
name: pbip-context
description: Contexto técnico do formato PBIP (Power BI Project) - estrutura de pastas, TMDL, PBIR, o que versionar, armadilhas conhecidas. Injetar antes de qualquer geração com gerar-modelo-tmdl ou gerar-visuais-pbir.
allowed-tools: [Read, Glob, Grep]
version: 0.1.0
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

## Diferenças-chave vs. o mundo .pbix (projeto anterior)

| Aspecto | .pbix (antes) | .pbip (agora) |
|---|---|---|
| Editar modelo | TOM com Desktop ABERTO | arquivos TMDL, Desktop FECHADO |
| Editar visuais | ZIP + Layout UTF-16LE | JSONs PBIR documentados |
| SecurityBindings | zerar (`b''`) senão MashupValidationError | não existe |
| Erro de visual | .pbix pode corromper | erro isolado no visual |
| Undo | fechar sem salvar | `git restore` |
| Validação | `validate_pbix()` caseiro | abrir no Desktop (parser oficial) |

## Requisito de versão

Power BI Desktop release **maio/2026 ou superior** (PBIR como formato padrão).
Em versões anteriores, habilitar em Opções → Recursos em versão preliminar.
GA do PBIR previsto para Q3/2026 — após o GA, é o único formato suportado.
