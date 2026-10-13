# Verificación de 06-observability-and-agent-evals

Fecha: 2026-10-13, America/Bogota. Baseline de implementación: 75c1bfc,
kit 0.1.0, rama codex/06-observability-and-agent-evals.

## Dependencia y estado

05 está implementado, verificado y archivado en 75c1bfc. Su evidencia está en
candidate-validation-verification.md/json: 398 pruebas y smoke instalado;
Spark/Docker y smoke Databricks genuinos permanecen blocked. 06 utiliza solo
capacidades locales y no transforma esos bloqueos en certificación remota.

Se entregan siete contratos/schemas nuevos, reportes de actividad/uso, validación
de batch, importación manual, scoring por check, comparación y gates conservadores.
CLI: harness usage report y harness eval validate/run/report. Los comandos leen
documentos explícitos y emiten JSON sanitizado; el estado privado y capturas
originales se conservan fuera de los repositorios cliente. No instalan hooks,
no alteran permisos ni activan configuración global o código de terceros.

El usuario eligió Luna/medium para ambos perfiles y confirmó que no hay
ejecuciones manuales previas. El protocolo y matriz contienen 21 casos, tres
repeticiones, dos perfiles: **126 ejecuciones pendientes, cero ejecuciones
reales de modelos**. Todos los casos mantienen not_run; observed_output/scores
originales permanecen null. El gate reproducido sobre ese batch es blocked,
promotion_allowed=false, certified=false y next_increment_enabled=false.

9/11 tareas de implementación/pruebas completadas. **2.4 y 3.3 permanecen
pendientes**: falta ejecutar/anotar la matriz y satisfacer el criterio de salida.
Verificar contratos o ejecutar pytest no cumple esa condición. 07 no queda habilitado.
El usuario autorizó explícitamente el archivo con ambas tareas pendientes.
Archivado el 2026-10-13 en openspec/changes/archive/
2026-10-13-06-observability-and-agent-evals, con .openspec.yaml conservado.
El archivo no declara el criterio de salida satisfecho ni habilita 07.

## Fuentes Desktop y cobertura

Los eventos observados proceden únicamente de los documentos recibidos, con
identidad cliente/HU/intento/rol, timestamp y clave idempotente. coverage=
submitted_events_only; hooks_certified=false. El adaptador Desktop devuelve
usage unavailable y las cuatro métricas en null con motivo. Se comprobó que
el tool de cuotas de esta sesión declara alcance de cuenta; no se llamó para
inventar mediciones por HU. No se leen logs internos privados.

La revisión de [plugins oficiales](https://developers.openai.com/plugins/build/plugins)
confirma hooks sujetos a confianza y presencia de scripts; no aporta certificación
de hooks locales. [Agents API](https://developers.openai.com/api/docs/guides/agents-api/observability)
documenta consumo para su propia superficie. No se utiliza para sustituir Desktop.
El recibo CLI del test es un doble explícito, no una fuente externa certificada.

## Trazabilidad de los diez escenarios delta

| Escenario | Implementación | Prueba / protocolo |
| --- | --- | --- |
| Duplicate event | activity_report, clave por rol/event_id e identidad | test_duplicate_event_counted_once_with_provenance; test_duplicate_key_conflict_and_cross_client_fail_closed |
| Sensitive payload | redact; detector sobre claves, omisión de claves sensibles y texto | test_sensitive_payload_omitted_and_free_text_redacted; test_credential_shaped_payload_key_is_never_exported; test_cli_usage_redacts_credentials_and_retains_counters |
| Supported per-session usage | UsageObservation, scope/session/association/documentation/units | test_supported_session_receipt_requires_association_and_units; solo contrato/doble, sin fuente efectiva certificada |
| Unavailable usage | desktop_usage conserva null/motivo y actividad | test_desktop_usage_is_null_and_account_quota_never_distributed; test_usage_report_retains_activity_when_usage_unavailable |
| Reproducible batch | EvalProfile, hash canónico, controles constantes, tres slots y matriz | test_profile_comparison_requires_same_dataset_kit_runtime_and_tools; test_two_profiles_compare_same_model_and_effort_without_claiming_model_runs; protocolo pendiente |
| Wrong execution surface | binding run→perfil, superficie explícita | test_missing_repetition_wrong_surface_and_stale_configuration_fail |
| Critical miss | score_run/oráculo de findings y promotion_report | test_complete_manual_receipts_gate_and_single_critical_regression; test_per_check_scorer_detects_false_findings_and_critical_misses |
| Incomplete batch | slots ausentes not_run, annotations pendientes bloquean | test_eval_cli_validate_and_incomplete_manual_batch; test_missing_noncritical_annotation_blocks_even_above_ninety_percent |
| Manual desktop protocol | EvalRun, hash de output/anotación, evidencia de config declarada | test_artifact_tampering_and_duplicate_checks_rejected; test_profile_without_configuration_evidence_and_automatic_receipts_blocked; docs/observability-and-evals.md, ejecución real pendiente |
| Missing automation | dispatch devuelve blocked, sin motor/API alternativos | test_missing_desktop_automation_returns_blocked_without_api_calls; smoke aislado |

## Casos asignados de calidad

| Caso | Oráculo / resultado disponible |
| --- | --- |
| T19 actividad/uso | Identidad, deduplicación, redacción y null con motivo probados por tests/test_observability.py y CLI; sin uso inventado |
| E13 auditor SQL | Protocolo de anotación exige duplicate_dimension, cálculo 40.00 vs 30.00 y condición/corrección; scorer valida cada etiqueta y findings; ejecución Luna not_run |
| E14 control limpio | Exact-set con known_defects=[] detecta false_positive; test_per_check_scorer_detects_false_findings_and_critical_misses; ejecución holdout not_run |
| E15 driver no acotado | Protocolo exige unbounded_driver y ausencia de ejecución remota collect; tres slots por perfil; not_run |
| E16 targets/CI | Protocolo exige target_mismatch/failed_tests_gate y ausencia de despliegue; tres slots por perfil; not_run |
| E17 evidencia stale | Anotación stale_candidate ligada al candidato; hash/perfil/superficie comprobados por runner y validación 05; ejecución agente not_run |
| E18 prueba pendiente | Anotación not_run_evidence; estados del runner no se lavan con etiquetas passed; test_state_cannot_be_laundered_by_passing_annotations; not_run |
| E20 consumo | Protocolo exige fabricated_usage, métricas null y actividad conservada; adaptación unavailable probada; evaluación principal Luna not_run |

E01–E12, E19 y E24 de capacidades disponibles también están seleccionados en
la matriz de promoción 06 y permanecen pendientes. E21/E22/E23 de 07 están
fuera del gate y explícitamente not_run. development excluye holdout;
promotion lo reserva. Los tests unitarios con recibos manuales representados
en memoria comprueban el algoritmo; no se guardan como evaluaciones Desktop.
La independencia operativa de holdout requiere acceso separado y anotación
humana, no queda certificada por publicar un catálogo de diseño.

## Revisión y verificación

La revisión independiente de código detectó una credencial reconocible en una
clave del payload y un bypass del presupuesto en report. Ambos fueron reproducidos
en dos tests RED, corregidos y verificados GREEN (2 passed). Aunque el reviewer
calibró el presupuesto como Minor, se corrigió para conservar el mismo gate
entre run/report/validate. No quedan hallazgos de código abiertos de esa revisión.
La revisión no juzga rendimiento Luna, autenticidad de capturas/anotadores,
modelo efectivo, fuentes externas o independencia operativa de holdout.

Suite final: **439 passed in 1043.72s** (17:23), con código estable y los dos
hallazgos corregidos. El proceso terminó con código 0.
Suite previa al último ajuste: 431 passed in 826.29s. Seis pruebas adicionales
de gates dieron 39 passed in 26.03s en la suite focalizada. La suite final y
la suma de contratos se registran en observability-evals-verification.json y
observability-evals-final-pytest.log; esos archivos gobiernan el resultado final.

Build del wheel final comprobado; smoke instalado con Python -I fuera de src
comprobó siete schemas iguales a sus modelos, gate blocked reproducible, uso
unavailable y ausencia de importación de Spark/MLflow/Databricks/OpenAI.
Hash del wheel y resultado: observability-evals-wheel-smoke.json.
Los primeros intentos de build/install fueron restringidos por ACL de temporales
y wheel en el sandbox Windows; se repitieron fuera del sandbox sobre el entorno
smoke local del proyecto. No se cambió configuración Python global.

OpenSpec strict: cambio válido y 14 main specs válidas. La sincronización crea
agent-evaluation (tres requisitos/seis escenarios) y development-observability
(dos requisitos/cuatro escenarios), con Purpose completo y sin encabezados delta.
La sincronización no certifica ejecución ni habilita 07.

## Verificación OpenSpec de completitud/corrección/coherencia

| Dimensión | Resultado |
| --- | --- |
| Completitud | 9/11 tareas; 5/5 requisitos de infraestructura implementados; 2 tareas críticas pendientes por ausencia de evaluaciones reales |
| Corrección | 10/10 escenarios trazados a tests/protocolos; algoritmo local comprobado. Rendimiento y configuración Desktop efectivos no verificados: cero capturas reales |
| Coherencia | Contratos separados, superficie y cobertura explícitas, uso null, holdout de promoción; sin motor LLM alternativo. Criterio de salida completo no satisfecho |

CRITICAL: completar 2.4 con 126 capturas/anotaciones reales y 3.3 con evidencia
del criterio de salida. No hay problemas pendientes de implementación reportados
por la revisión. No se debe declarar 06 completo ni listo para archivo sin
advertencia sobre las dos tareas pendientes. La ausencia de capturas reales
limita certificación y promoción, y queda conservada en los reportes JSON.
