# Secuencia de implementación del harness

Actualizado: 13 de octubre de 2026. Estado: 01 verificado; 02 verificado para preparación supervisada, con conflicto de sandbox conservado; 03 archivado para onboarding preparado; 04 y 05 implementados/verificados y cerrados; 06 con infraestructura implementada y evals manuales pendientes; 07 implementado localmente y archivado con pendientes autorizados, publicación bloqueada; 08 propuesto. 05 conserva smoke remoto blocked sin sandbox seleccionado.
Objetivo: usuario nuevo completa onboarding y HU en Desktop con roles, herramientas, validaciones y PR autorizado.
Baseline implementada: bootstrap-codex-local-core y apply-client-onboarding.

| Orden | Cambio | Dependencia inmediata | Criterio de salida |
| --- | --- | --- | --- |
| 01 | [Paquete de buenas prácticas y catálogo de evaluación](../../openspec/changes/archive/2026-10-09-01-quality-practices-and-eval-foundation/proposal.md) | Baseline archivada | Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios. |
| 02 | [Integración Desktop, roles y herramientas](../../openspec/changes/archive/2026-10-09-02-desktop-roles-and-tool-contracts/proposal.md) | 01 | Preparación supervisada implementada/verificada, matriz observada y límites aceptados, evals con anotación humana; certificación estricta separada. |
| 03 | [Onboarding conversacional y configuración del cliente](../../openspec/changes/archive/2026-10-13-03-guided-client-onboarding/proposal.md) | 02 | Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia. |
| 04 | [Flujo de HU, estado y controles de desarrollo](../../openspec/changes/archive/2026-10-13-04-hu-lifecycle-and-development-gates/proposal.md) | 03 | Cada transición queda registrada y los gates rechazan alcance, aprobación o evidencia incorrectos; no se publican cambios todavía. |
| 05 | [Pruebas Databricks y evidencia del candidato](../../openspec/changes/archive/2026-10-13-05-databricks-validation-and-evidence/proposal.md) | 04 | Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo. |
| 06 | [Observabilidad y ejecución de evals de agentes](../../openspec/changes/archive/2026-10-13-06-observability-and-agent-evals/proposal.md) | 05 | Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo. Archivo autorizado con 2.4/3.3 pendientes; criterio aún no satisfecho. |
| 07 | [Integraciones de historias y publicación de PR](../../openspec/changes/archive/2026-10-13-07-story-and-pr-integrations/proposal.md) | Infraestructura verificada de 06; excepción para desarrollo local | HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación. Archivo autorizado con 2.3/2.5/3.3 pendientes; publicación y cierre completo requieren gates/evals. |
| 08 | [Piloto completo y distribución reproducible](../../openspec/changes/archive/2026-10-14-08-pilot-and-reproducible-distribution/proposal.md) | 07 | Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones. |

Implementar en orden 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08. La dependencia es sobre comportamiento implementado y evidencia, no sobre documentos existentes. OpenSpec status no enforcea esta cadena: revisar dependencia en tarea 1.1. El cambio 01 queda verificado y archivado. 02 está implementado/verificado para preparación supervisada y habilita 03 para onboarding preparado, conservando conflictos. No exige certificado estricto completo ni habilita fases que requieran capacidades fallidas.

Cada carpeta contiene proposal.md, design.md, tasks.md y delta specs por capability. Las specs de 01–08 están sincronizadas; sync no certifica ejecución Desktop/Databricks. 03 entrega preparación por etapas, 04 gates locales de HU y 05 validación/evidencia con bloqueos remotos conservados; 06 entrega infraestructura con evals pendientes, 07 entrega implementación local y está archivado con pendientes; 08 entrega distribución candidata y update/recover locales y está archivado con aceptación pendiente. GitHub es proveedor remoto inicial, configurable; Jira/Linear son extensiones posteriores.

Excepción aprobada el 2026-10-13: la infraestructura de 06 (439 pruebas, smoke
instalado, commits ec84193/54faea5) habilita implementar 07 localmente. La
dependencia de evaluación para promoción/publicación sigue pendiente. Esta
decisión posterior no modifica los snapshots históricos de 06 ni habilita 08.

## Recursos ya preparados

- [Prácticas y fuentes](quality/practices.json): 32 reglas con aplicabilidad, severidad y evidencia.
- [Casos de prueba](quality/test-cases.json): 24 casos iniciales con oráculo.
- [Evals](quality/eval-cases.json): 24 casos, ocho roles, golden/holdout, checks y resultados null.
- [Protocolo de calidad](quality/README.md): ejecución, scoring, límites y capas de prueba.
- [Snapshot oficial](../../resources/vendor/README.md): nueve Skills, dependencias documentales y hashes.
- [Arquitectura actualizada](../propuesta-harness-local-codex.md).

El runner/scorers de 06 valida recibos manuales; la matriz de promoción aún está pendiente. Gate 06 usa capacidades ya implementadas; 07 añade casos de proveedores y 08 exige todos. El catálogo no contiene resultados passed inventados.

## Próxima acción

08 tiene desarrollo local anticipado autorizado el 13 de octubre e implementación
local verificada el 14 de octubre: candidato, bootstrap/launcher, update/recover y
gate de release, con 52 pruebas propias y smoke instalado. Ocho de trece tareas
completas; 3.1–3.4 y 4.3 permanecen pendientes en el archivo. El 14 de octubre,
el usuario autorizó archivar 08 con esos pendientes para realizar la prueba real
y gestionar defectos o mejoras mediante nuevos cambios. Las specs están
sincronizadas sin certificar release.
Ver [evidencia de 08](../evidence/distribution-verification.md). Los bloqueos
históricos descritos abajo continúan como dependencias de aceptación y release;
la autorización posterior permite únicamente código y comprobación local de 08.

Completar las 144 evaluaciones manuales de 06/07 y seleccionar/autorizar el
smoke de escritura sintético real después de pasar los gates. 07 está archivado
con 2.3/2.5/3.3 pendientes por autorización expresa; el archivo no satisface
el criterio de salida ni habilita 08. Su [evidencia](../evidence/story-pr-verification.md)
registra 507 pruebas aprobadas, smoke instalado y cuatro requisitos/diez
escenarios sincronizados. Los controles se comprueban con dobles; no hay nueva
certificación de agentes ni de GitHub.
La infraestructura local de observabilidad, importación manual y gates está
implementada; specs de agent-evaluation/development-observability sincronizadas.
06 fue archivado con las tareas 2.4/3.3 pendientes por autorización expresa del
usuario; el archivo no equivale a aprobar la matriz. La decisión posterior
habilita únicamente el desarrollo local de 07.
El protocolo conserva 126 ejecuciones not_run para dos perfiles Luna/medium,
cero capturas reales y promoción blocked. Tareas 2.4/3.3 pendientes; publicación
de 07 y habilitación de 08 permanecen bloqueadas.
Ver [evidencia de 06](../evidence/observability-evals-verification.md) y
[protocolo manual](../observability-and-evals.md). Los tests del runner no
sustituyen evaluaciones de modelos.
05 entrega selección por impacto, workers con runtime explícito, adaptadores
autorizados, journal de reconciliación y evidencia ligada a fuente/candidato.
[Evidencia de 05](../evidence/candidate-validation-verification.md): 398 pruebas
aprobadas, smoke instalado de validación/HU/catálogos y cuatro requisitos/ocho
escenarios trazados. Smoke Databricks genuine blocked por decisión del usuario
sin sandbox seleccionado; Docker/Spark genuine blocked. Todo gate que requiera
esas capacidades sigue bloqueado. E07/E09/E10/E11/E12 permanecen not_run.
04 entrega estado SQLite por cliente/checkout/HU/intento, plan/aprobación ligados,
candidato de working tree/índice, revisión independiente y recuperación conservadora.
[Evidencia de 04](../evidence/hu-lifecycle-verification.md): 340 pruebas aprobadas,
smoke del wheel instalado y cuatro requisitos/ocho escenarios trazados.
La HU sintética llega a ready_to_publish/partial, con publicación bloqueada.
E05/E06/E08/E19 siguen not_run como protocolos de agentes, sin ejecución remota nueva.
03 entrega plantilla/entrevista, contexto portable, binding de herramientas externo,
preview compuesto y aplicación/recuperación por etapa con autorización explícita.
[Evidencia de 03](../evidence/guided-onboarding-verification.md): 298 pruebas aprobadas,
smoke de wheel instalado y cinco requisitos/11 escenarios trazados. El cierre del
13 de octubre añade 20 comprobaciones de contratos/CLI y valida las 10 main specs.
No se han configurado clientes productivos ni certificado conectividad remota.
La [evidencia Desktop de 02](../evidence/desktop-runtime-2026-10-09/verification.md)
conserva conflicto de sandbox, certificación estricta false y defecto aceptado de E04.
Aceptar límites no certifica aislamiento: 04 debe bloquear capacidades fallidas o
no observadas cuando la fase las requiera. E01, E02 y E24 siguen not_run en el
protocolo Desktop; el piloto humano completo y su distribución pertenecen a 08.
