# Ayuda, metadata y compatibilidad

Investigado el 2026-11-06. Ayuda local real: Azure CLI 2.91.0, extensión azure-devops
1.0.9, doce comandos capturados en el cambio OpenSpec. No se consultó una organización.
Una ayuda o fixture no demuestra autenticación, permisos ni ejecución remota.

`boards work-item show` admite --id, --organization, --detect false, --expand all
y --output json; no --project. `repos pr show` tampoco admite --project o --repository.
`devops invoke` admite --area, --resource, --http-method, --api-version,
--route-parameters y --query-parameters. El helper fija todos esos campos; el usuario
no puede suministrar área, recurso, método ni comandos arbitrarios.

La grabación oficial de integración de Azure CLI conserva metadata OPTIONS del recurso:
área `wit`, resourceName `comments`, ID `608aac0a-32e1-4493-a863-b9cf4566d257`,
resourceVersion 4, ruta `{project}/_apis/wit/workItems/{workItemId}/comments/{commentId}`.
El GET de colección omite commentId. SDK oficial node getComments confirma project,
workItemId y ese location ID. Se conserva extracto mínimo con URL inmutable y hashes
en `azure-official-sources.json` de la evidencia del cambio, sin copiar respuestas ajenas completas.

La captura incorporada procede de la revisión inmutable
`2ee443d1f35a93bffbfe478281577c8493eb4ad7` del repositorio Azure/azure-devops-cli-extension:
[grabación fijada](https://github.com/Azure/azure-devops-cli-extension/blob/2ee443d1f35a93bffbfe478281577c8493eb4ad7/azure-devops/azext_devops/tests/latest/integrationtests/recordings/test_invoke_command_basic.yaml).
En esa metadata también existe un recurso legacy comments con ID distinto, maxVersion 5.0
y rutas id/revision; se usa el recurso moderno maxVersion 7.2 y workItemId/commentId.
El selector invoke compara versiones y conserva el recurso moderno para 7.1-preview.

Microsoft Learn documenta API `7.1-preview.4`. En invoke 1.0.9, apiVersionToFloat
rechaza sufijos de revisión (`7.1.4` no es float). La gramática oficial permite
`{major}.{minor}[-{stage}[.{resource-version}]]`; por ello el helper pide explícitamente
`7.1-preview`. La inspección del SDK confirma que no agrega por sí mismo `.4` si se omite.
Se registra esa diferencia y revisión de recurso observada unknown; nunca se afirma
que la versión exacta .4 ni permisos se verificaron en remoto. No se fuerza otra versión
por query, no se edita el SDK y no hay fallback a REST directo/MCP. Un servidor incompatible
produce failed/partial; no se cambia silenciosamente el transporte.

Fuentes oficiales:

- [Comentarios REST 7.1](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments/get-comments?view=azure-devops-rest-7.1).
- [Versionado REST](https://learn.microsoft.com/en-us/azure/devops/integrate/concepts/rest-api-versioning?view=azure-devops).
- [Metadata en grabación CLI](https://github.com/Azure/azure-devops-cli-extension/blob/master/azure-devops/azext_devops/tests/latest/integrationtests/recordings/test_invoke_command_basic.yaml).
- [Implementación invoke](https://github.com/Azure/azure-devops-cli-extension/blob/master/azure-devops/azext_devops/dev/team/invoke.py).
- [SDK CLI](https://github.com/Azure/azure-devops-cli-extension/blob/master/azure-devops/azext_devops/devops_sdk/client.py).
- [SDK node WorkItemTrackingApi](https://github.com/microsoft/azure-devops-node-api/blob/master/api/WorkItemTrackingApi.ts).
- [Ayuda work item](https://learn.microsoft.com/en-us/cli/azure/boards/work-item?view=azure-cli-latest).
- [Ayuda invoke](https://learn.microsoft.com/en-us/cli/azure/devops?view=azure-cli-latest#az-devops-invoke).
- [Ayuda PR](https://learn.microsoft.com/en-us/cli/azure/repos/pr?view=azure-cli-latest).
- [Microsoft boards-work-item-summary](https://github.com/microsoft/azure-devops-skills/blob/main/.github/skills/boards-work-item-summary/SKILL.md): orienta campos, vínculos y resumen; su preferencia MCP no se incorpora como requisito CLI.

Las URLs flotantes facilitan consulta; las fuentes incorporadas se identifican por revisión
y hash en evidencia. Si falta extensión/ayuda, documentar limitación; no instalar ni
afirmar verificación local. Descubrir parámetros mediante --help, nunca ejecutando la
operación como prueba exploratoria.
