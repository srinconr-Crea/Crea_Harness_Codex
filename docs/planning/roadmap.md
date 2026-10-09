# Secuencia de implementación del harness

Fecha: 9 de octubre de 2026. Estado: incremento 01 implementado; 02–08 pendientes.
Objetivo: usuario nuevo completa onboarding y HU en Desktop con roles, herramientas, validaciones y PR autorizado.
Baseline implementada: bootstrap-codex-local-core y apply-client-onboarding.

| Orden | Cambio | Dependencia inmediata | Criterio de salida |
| --- | --- | --- | --- |
| 01 | [Paquete de buenas prácticas y catálogo de evaluación](../../openspec/changes/archive/2026-10-09-01-quality-practices-and-eval-foundation/proposal.md) | Baseline archivada | Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios. |
| 02 | [Integración Desktop, roles y herramientas](../../openspec/changes/02-desktop-roles-and-tool-contracts/proposal.md) | 01 | Configuración concreta revisable y evidencia en Desktop de cada capacidad habilitada; archivos presentes nunca equivalen a certificación. |
| 03 | [Onboarding conversacional y configuración del cliente](../../openspec/changes/03-guided-client-onboarding/proposal.md) | 02 | Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia. |
| 04 | [Flujo de HU, estado y controles de desarrollo](../../openspec/changes/04-hu-lifecycle-and-development-gates/proposal.md) | 03 | Cada transición queda registrada y los gates rechazan alcance, aprobación o evidencia incorrectos; no se publican cambios todavía. |
| 05 | [Pruebas Databricks y evidencia del candidato](../../openspec/changes/05-databricks-validation-and-evidence/proposal.md) | 04 | Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo. |
| 06 | [Observabilidad y ejecución de evals de agentes](../../openspec/changes/06-observability-and-agent-evals/proposal.md) | 05 | Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo. |
| 07 | [Integraciones de historias y publicación de PR](../../openspec/changes/07-story-and-pr-integrations/proposal.md) | 06 | HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación. |
| 08 | [Piloto completo y distribución reproducible](../../openspec/changes/08-pilot-and-reproducible-distribution/proposal.md) | 07 | Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones. |

Implementar en orden 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08. La dependencia es sobre comportamiento implementado y evidencia, no sobre documentos existentes. OpenSpec status no enforcea esta cadena: revisar dependencia en tarea 1.1. El cambio 01 queda verificado y archivado; 02–08 mantienen sus tareas pendientes.

Cada carpeta contiene proposal.md, design.md, tasks.md y delta specs por capability. Las specs del cambio 01 están sincronizadas; los cambios 02–08 aún no modifican main specs. La preparación guiada aparece en 03; la distribución para equipo nuevo y update en 08. GitHub es proveedor remoto inicial, configurable; Jira/Linear son extensiones posteriores.

## Recursos ya preparados

- [Prácticas y fuentes](quality/practices.json): 32 reglas con aplicabilidad, severidad y evidencia.
- [Casos de prueba](quality/test-cases.json): 24 casos iniciales con oráculo.
- [Evals](quality/eval-cases.json): 24 casos, ocho roles, golden/holdout, checks y resultados null.
- [Protocolo de calidad](quality/README.md): ejecución, scoring, límites y capas de prueba.
- [Snapshot oficial](../../resources/vendor/README.md): nueve Skills, dependencias documentales y hashes.
- [Arquitectura actualizada](../propuesta-harness-local-codex.md).

Antes de 06 se pueden ejecutar protocolos manuales para certificar roles; el runner/scorers llega en 06. Gate 06 usa capacidades ya implementadas; 07 añade casos de proveedores y 08 exige todos. El catálogo no contiene resultados passed inventados.

## Próxima acción

Revisar/aplicar 02-desktop-roles-and-tool-contracts usando openspec-apply-change. Su dependencia 01 queda implementada con evidencia de catálogos y recursos; todavía no se han configurado roles ni herramientas en clientes. Crear estas propuestas no autoriza instalación global, ejecución remota o publicación.
