# Custom visuals em PBIP/PBIR

Use esta referencia quando o pedido envolver um visual AppSource,
organizacional ou um arquivo privado `.pbiviz`.

## Fluxo seguro

1. Identificar o tipo do visual, o GUID, a origem do pacote e os papeis de dados.
2. Procurar no `report.json` e em `RegisteredResources` a estrutura criada pelo Power BI Desktop para um visual equivalente.
3. Registrar o pacote seguindo essa estrutura. Nao copiar apenas o `visualType`.
4. Configurar as projections e os roles conforme o manifesto do `.pbiviz`.
5. Validar JSON, abrir no Desktop, revisar a pagina e testar no Service.

## Tipos de origem

- **AppSource:** depende do visual estar permitido no tenant e do GUID/versao registrados no relatorio.
- **Organizacional:** pode exigir pacote `_OrgStore` e configuracao do tenant.
- **Privado:** exige preservar o pacote e seus recursos no projeto PBIP.

## Limites

Esta skill pode registrar e configurar um pacote existente, mas nao cria um `.pbiviz` do zero. Sem o manifesto do visual, nao e seguro inventar nomes de roles, propriedades ou seletores.

## Referencia oficial

<https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/authoring/custom-visuals.md>
