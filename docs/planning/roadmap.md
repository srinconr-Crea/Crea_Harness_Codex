# Secuencia de implementación del harness

Actualizado: 13 de octubre de 2026. Estado: 01 verificado; 02 verificado para preparación supervisada, con conflicto de sandbox conservado; 03 archivado para onboarding preparado; 04 y 05 implementados/verificados y cerrados; 06–08 propuestos. 05 conserva smoke remoto blocked sin sandbox seleccionado.
Objetivo: usuario nuevo completa onboarding y HU en Desktop con roles, herramientas, validaciones y PR autorizado.
Baseline implementada: bootstrap-codex-local-core y apply-client-onboarding.

| Orden | Cambio | Dependencia inmediata | Criterio de salida |
| --- | --- | --- | --- |
| 01 | [Paquete de buenas prácticas y catálogo de evaluación](../../openspec/changes/archive/2026-10-09-01-quality-practices-and-eval-foundation/proposal.md) | Baseline archivada | Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios. |
| 02 | [Integración Desktop, roles y herramientas](../../openspec/changes/archive/2026-10-09-02-desktop-roles-and-tool-contracts/proposal.md) | 01 | Preparación supervisada implementada/verificada, matriz observada y límites aceptados, evals con anotación humana; certificación estricta separada. |
| 03 | [Onboarding conversacional y configuración del cliente](../../openspec/changes/archive/2026-10-13-03-guided-client-onboarding/proposal.md) | 02 | Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia. |
| 04 | [Flujo de HU, estado y controles de desarrollo](../../openspec/changes/archive/2026-10-13-04-hu-lifecycle-and-development-gates/proposal.md) | 03 | Cada transición queda registrada y los gates rechazan alcance, aprobación o evidencia incorrectos; no se publican cambios todavía. |
| 05 | [Pruebas Databricks y evidencia del candidato](../../openspec/changes/archive/2026-10-13-05-databricks-validation-and-evidence/proposal.md) | 04 | Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo. |
| 06 | [Observabilidad y ejecución de evals de agentes](../../openspec/changes/06-observability-and-agent-evals/proposal.md) | 05 | Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo. |
| 07 | [Integraciones de historias y publicación de PR](../../openspec/changes/07-story-and-pr-integrations/proposal.md) | 06 | HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación. |
| 08 | [Piloto completo y distribución reproducible](../../openspec/changes/08-pilot-and-reproducible-distribution/proposal.md) | 07 | Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones. |

Implementar en orden 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08. La dependencia es sobre comportamiento implementado y evidencia, no sobre documentos existentes. OpenSpec status no enforcea esta cadena: revisar dependencia en tarea 1.1. El cambio 01 queda verificado y archivado. 02 está implementado/verificado para preparación supervisada y habilita 03 para onboarding preparado, conservando conflictos. No exige certificado estricto completo ni habilita fases que requieran capacidades fallidas.

Cada carpeta contiene proposal.md, design.md, tasks.md y delta specs por capability. Las specs de 01–05 están sincronizadas; sync no certifica ejecución Desktop/Databricks. 03 entrega preparación por etapas, 04 gates locales de HU y 05 validación/evidencia con bloqueos remotos conservados; 06–08 siguen propuestos. La distribución para equipo nuevo y update llega en 08. GitHub es proveedor remoto inicial, configurable; Jira/Linear son extensiones posteriores.

## Recursos ya preparados

- [Prácticas y fuentes](quality/practices.json): 32 reglas con aplicabilidad, severidad y evidencia.
- [Casos de prueba](quality/test-cases.json): 24 casos iniciales con oráculo.
- [Evals](quality/eval-cases.json): 24 casos, ocho roles, golden/holdout, checks y resultados null.
- [Protocolo de calidad](quality/README.md): ejecución, scoring, límites y capas de prueba.
- [Snapshot oficial](../../resources/vendor/README.md): nueve Skills, dependencias documentales y hashes.
- [Arquitectura actualizada](../propuesta-harness-local-codex.md).

Antes de 06 se pueden ejecutar protocolos manuales para certificar roles; el runner/scorers llega en 06. Gate 06 usa capacidades ya implementadas; 07 añade casos de proveedores y 08 exige todos. El catálogo no contiene resultados passed inventados.

## Próxima acción

Implementar 06-observability-and-agent-evals sobre capacidades locales verificadas.
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
