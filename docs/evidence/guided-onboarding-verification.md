# Verificación de 03-guided-client-onboarding

Fecha: 2026-10-09, America/Bogota. Implementación en rama
`codex/03-guided-client-onboarding`, baseline d175d84.

## Dependencia y decisiones

02 está implementado en 3963ac2 y archivado en d175d84. Verificación vigente:
`desktop-runtime-2026-10-09/verification.md`, `supervised-verification.json` y
aceptación explícita conservada en `human-annotation.json`. La certificación
estricta sigue false; el conflicto de escritura de auditor/verifier y defecto
aceptado de E04 permanecen intactos. El recibo empaquetado referencia hashes
de esas fuentes. No se reemplazan observaciones Desktop por tests simulados.

El plan existente es la especificación de implementación. Se decidió usar
CompositePreparationPlan separado porque init v1 rechaza AGENTS personalizado;
se preserva ese plan v1 no aplicable sin cambiar su ejecución. Integración usa
02 después de comprobar contra el preview compuesto cada byte y precondición.
Sus planes externos se ubican junto al binding porque 02 rechaza planes dentro
del estado. Los locks del run y del checkout tienen propósitos separados para
serializar etapas sin duplicar el lock del adaptador 02.

## Pruebas y alcance observado

TDD: tests de contratos y adaptador ejecutados primero con ausencia del módulo/API;
CLI ejecutado primero con ausencia del comando; negativos y repetición añadidos
antes de sus correcciones. Resultado base en sandbox: 262 passed, 1 failed en
control positivo de filtro Git, con warnings de ACL del cache. El control positivo
`test_git_status_never_executes_client_filter` pasó con acceso normal (1 passed);
no se cambió esa prueba ni código v1. Resultados finales y smoke se registran en
`guided-onboarding-verification.json` y `guided-onboarding-wheel-smoke.json`.

No se prueban clientes productivos ni conectividad remota. Pruebas de sandbox
conflictivo y aceptación usan observaciones sintéticas para verificar el evaluador,
no son una nueva certificación Desktop. Las observaciones originales de 02 y sus
limitaciones siguen siendo las mismas. Configuración global no es destino de las
operaciones; los tests comparan árboles de clientes/estado y un segundo cliente.

## Trazabilidad de los 11 escenarios delta

| Escenario | Prueba |
| --- | --- |
| Complete template | test_complete_template_no_redundant_questions; test_explicit_stages_repeat_recovery_and_context_separation |
| Ambiguous target | test_interview_unknown_target_and_discovery_no_inferred_permission; test_discovery_and_ambiguous_candidates_need_confirmation |
| New selections | test_separate_contracts_strict_version_and_no_secrets; test_explicit_stages_repeat_recovery_and_context_separation |
| Credential input | test_secret_answers_rejected_without_echo; test_cli_secret_redacted |
| Successful local stages | test_explicit_stages_repeat_recovery_and_context_separation |
| Interrupted integration | test_stage_fault_journal_no_fake_rollback_and_recovery (before_binding/after_binding/integration) |
| Custom AGENTS preserved | test_preview_snapshot_exclusive_export_and_custom_agents; test_explicit_stages_repeat_recovery_and_context_separation |
| Preview snapshot | test_preview_snapshot_exclusive_export_and_custom_agents |
| Existing export destination | test_preview_snapshot_exclusive_export_and_custom_agents; test_linked_export_and_preserved_identity_replacement |
| Prepared onboarding with accepted reviewer limitation | test_accepted_limitation_separate_from_certification_and_required_block |
| Phase requires failed isolation | test_accepted_limitation_separate_from_certification_and_required_block |

Negativos adicionales: bootstrap protegido, herramientas locales faltantes, cliente
cruzado, target modificado antes de aplicar, archivo propio editado, dos clientes,
flags sin autorización por etapa y schemas estrictos. Resultados de tests locales
no alteran estados de catálogos de diseño.

## Casos de calidad asignados

T15 se ejecuta localmente en test_protected_bootstrap_cross_client_and_missing_tools:
el cliente alpha con ToolBinding beta se rechaza y snapshots permanecen iguales;
los tests v1 mantienen además descriptor alpha/binding beta. Estado de esta evidencia:
passed para el control local, mientras el catálogo de diseño permanece not_run.

E01, E02 y E24 son protocolos Desktop con anotación humana, no tests Python.
La Skill entrega el procedimiento para E01 (preguntar definición neto/bruto y
período), E02 (conservar contrato y evitar preguntas repetidas) y E24 (explicar
prepared/desktop_pending/remote_pending sin declarar HU completa). Sus controles
de contrato locales tienen tests; las ejecuciones de agentes, tres repeticiones,
anotación humana y holdout E24 permanecen **not_run**, con observed_output/scores=null.
No se convierten not_run/blocked en passed. El runner de evals/observabilidad llega
en 06 y el piloto humano completo en 08, como define el roadmap.

## Criterio de salida y límites

El flujo de una persona nueva se prueba con plantilla completa y entrevista
incompleta sobre clientes sintéticos: decisiones faltantes producen preguntas,
decisiones confirmadas producen preview, prepare crea contexto trazable y solo
integrate autorizado añade la configuración Desktop. Dos clientes permanecen
separados y el contexto no se copia al núcleo. Es evidencia funcional automatizada;
no afirma una nueva prueba de usabilidad humana ni ejecución de evals Desktop.
04 queda habilitado para implementar gates sobre onboarding preparado, conservando
requisitos de capacidades y evidencia propios. No se habilita ejecución de HUs o
validaciones remotas por inferencia.

## Verificación OpenSpec

| Requisito | Implementación | Verificación |
| --- | --- | --- |
| Interview or configuration file | guided.collect, guided_onboarding.discover/preview, Skill | Plantilla, entrevista, fuentes y target ambiguo |
| Separate portable and local configuration | ClientDevelopmentConfig, ClientToolBinding, GuidedRequest | Schemas/version, v1 intacto, secretos y cruce de clientes |
| Staged preparation and certification | GuidedOnboardingPlan, OnboardingRun, apply/recover | Etapas explícitas, journal, fallos, repetición, custom AGENTS |
| Side effect free preview | preview/export, PinnedTree | Snapshots, destino existente/hardlink y bootstrap protegido |
| Preserve supervised limitations | certify_stage/response, evaluadores de 02 | Aceptación ligada, conflicto conservado, capacidad requerida fallida y drift |

Completitud: contratos independientes, cinco requisitos implementados y 11 escenarios
trazados. Corrección: comparación de preview/aplicación, identidad, recuperación y
estados negativos. Coherencia: decisiones de diseño sobre v1, separación del cliente,
políticas y observaciones se mantienen. La revisión independiente, validación estricta
del cambio, validación de main specs y smoke final se registran antes de archivo.

Revisión independiente: tres hallazgos importantes reproducidos RED→GREEN:
recovery de integración con drift ya no indexa un campo ausente; recovery de
prepare en formato humano tiene reason y salida estable; certificado Desktop
estricto positivo no certifica onboarding si el candidato cambió, y el informe
expone candidate_comparison. Prueba adicional de repetición conserva aceptación
y limitaciones. El smoke detectó directorios vacíos retenidos por 02: el adaptador
compuesto retira únicamente directorios de integración con identidad demostrada,
vacíos y registrados, antes de recuperar sus padres; contenido ajeno se conserva.
Un flag incompleto en salida humana también quedó cubierto RED→GREEN.

## Cierre del 13 de octubre de 2026

| Dimensión | Resultado |
| --- | --- |
| Completitud | 11/11 tareas, 5/5 requisitos, 11/11 escenarios trazados |
| Corrección | Suite completa: 298 passed; smoke instalado: 18 checks; reanudación: 20 passed |
| Coherencia | Contratos v1 conservados; siete decisiones de diseño respetadas; revisión independiente corregida |

Validación estricta del cambio y las 10 main specs aprobadas. Sync verificado por
comparación completa del delta: mismo Purpose, cinco requisitos y 11 escenarios.
No hay issues críticos ni warnings de implementación pendientes en la verificación
de completitud/corrección/coherencia. Los protocolos de evals humanos E01/E02/E24
siguen not_run; no se cuentan como controles runtime aprobados ni como certificación.
La suite completa y el smoke se ejecutaron el 9 de octubre; el 13 se revisó su
resultado y se volvieron a ejecutar 20 pruebas de contratos/CLI y las validaciones
OpenSpec. No hubo cambios de implementación entre esas ejecuciones.
Archivo: `openspec/changes/archive/2026-10-13-03-guided-client-onboarding/`.
