# Verificación de 05-databricks-validation-and-evidence

Fecha: 2026-10-13, America/Bogota. Baseline bf7fd93, kit 0.1.0,
rama codex/05-databricks-validation-and-evidence. Dependencia 04 implementada,
verificada y archivada en bf7fd93; evidencia hu-lifecycle-verification.md/json,
340 pruebas y smoke del wheel instalado. 05 no empieza con dependencia pendiente.

## Alcance y resultado remoto

El usuario seleccionó «Registrar blocked por falta de sandbox seleccionado».
No se seleccionó perfil ni se invocó autenticación/SQL/job de un workspace real.
CLI observado localmente: Databricks 1.18.0 (solo versión/ayuda). Docker ausente.
Smoke remoto genuino: **blocked**, reason=sandbox_not_selected. Backend Docker/
Spark genuino: **blocked**. Servicio doble: simulated=true, nunca certificación.
E07/E09/E10/E11/E12 conservan not_run, observed_output/scores=null: son protocolos
de agente con anotación/repeticiones posteriores, no resultados de pytest.

La ruta de bloqueo es un resultado real del adaptador y de la política elegida;
no se reemplaza smoke remoto por mocks. El criterio de salida permite y exige ese
bloqueo ante entorno ausente. Habilita implementación de 06 sobre capacidades
locales verificadas, preservando bloqueos de cualquier gate que exija runtime real.

## Trazabilidad de escenarios delta

| Escenario | Implementación | Prueba/protocolo |
| --- | --- | --- |
| Python logic | select_plan/python-unit L1 | test_pure_python_selects_behavior_without_remote, test_worker_decimal_and_clean_session_protocol |
| Delta behavior | delta-semantic L2, sandbox | test_selection_never_replaces_semantics_with_parser, synthetic_notebook MERGE; ejecución genuine blocked |
| Authorized sandbox | preflight/digest/allowlist | test_remote_selected_sandbox_and_result (doble); genuine blocked |
| Wrong target | rechazo previo a submit | test_wrong_preflight_has_zero_remote_writes, test_bundle_profile_host_target_checked_before_call |
| Matching result | request/result/identidad root | test_remote_selected_sandbox_and_result, test_cli_provider_uses_explicit_profile_and_idempotency |
| Mismatched result | hash/runtime/client/job | test_cross_identity_or_hash_never_receives_success, test_gate_checks_full_request_identity_and_result_hash |
| Offline YAML valid | L0 distinto bundle/runtime | test_yaml_offline_and_python_parse_are_only_l0, test_bundle_authorized_read_only_cli_result |
| Missing required runtime | blocked antes de código | test_missing_runtime_is_blocked_before_code_execution, test_missing_authorization_or_target_blocks_without_remote_call |

## Casos de calidad asignados

| Caso | Oráculo / evidencia y límite |
| --- | --- |
| T01 join_unique | Protocolo Spark notebook: 3 filas/30.00; genuine blocked |
| T02 join_duplicate crítico | Protocolo notebook rechaza duplicate keys; genuine blocked |
| T03 null_decimal | Protocolo notebook: 3 filas/2 non_null/30.00; genuine blocked |
| T04 empty_input | Protocolo notebook: 0 filas/0.00; genuine blocked |
| T05 rounding_contract | Protocolo Python real propiedad del harness: 0.30 y 0.00, no código cliente en host |
| T06 io_failure | test_timeout_cleans_only_owned_container; lost_submit/polling doubles, no recibo falso |
| T07 clean_session | Protocolo Python falla NameError en namespace limpio; Spark/notebook remoto blocked |
| T08 parameter_isolation crítico | Preflight matrix/host/job/resources/runtime/identidad; cero submit en negativos |
| T09 schema_rows | compare_result prueba nullability/schema/filas desordenadas; Spark genuine blocked |
| T10 rerun_idempotency | Protocolo Delta MERGE twice, 3 filas/30.00; genuine blocked |
| T11 unbounded_driver | test_static_controls_driver_cicd_and_relative_resources, collect/toPandas flagged |
| T12 relative_resource | Recurso ../src/job.py resuelto al bundle; missing falla/archivo real pasa |
| T13 target_mismatch crítico | Bundle/YAML auth separado, host prod rechazado antes de llamada |
| T14 failed_tests_gate crítico | Promoción sin needs o always() falla; gate evidencia failed bloquea |
| T18 test_not_run crítico | missing/not_run/blocked/failed/simulated/stale/duplicate bloquean required |

El catálogo empaquetado no se modifica para declarar passed de estos casos.
Cobertura determinista local y protocolos Spark se registran por separado.

## Revisión y comprobaciones

Revisión independiente read-only detectó error de parser SQL no capturado y
vinculación insuficiente de fuente/candidato. Se capturan errores SQL propios,
se verifican source hash y entradas reales del candidato al entregar a HU,
se impide degradar capa/scope/required y se verifica tool/data/command efectivo
en worker. El proveedor obtiene job/run de metadata del servicio. Nuevas pruebas
ejercitan negativos y controles limpios; ver módulos tests/test_validation*.

El wheel incluye cinco schemas y cuatro plantillas pasivas con manifest por bytes.
Smoke instalado usa Python -I fuera de src; no importa Spark/MLflow/Databricks/
SQLGlot al cargar contratos. No modifica configuración global ni clientes reales.
Schemas existentes, catálogos, kit Desktop e init/onboarding/HU v1 se conservan.

Resultados finales, logs, hashes de wheel y verificación estricta se consignan
en candidate-validation-verification.json y los archivos adjuntos de esta carpeta.
La ejecución real Spark/Databricks y evals Desktop permanecen bloqueada/not_run.

## Verificación OpenSpec final

| Dimensión | Resultado |
| --- | --- |
| Completitud | 10/10 tareas, 4/4 requisitos implementados y 8/8 escenarios trazados |
| Corrección | 398 passed in 777.97s; negativos de identidad/hash/fuente/runtime/timeout y gates comprobados |
| Coherencia | Contratos independientes, workers sin credenciales, estado segregado, autorización previa, evidencia simulated explícita |

La primera suite corrió mientras se modificaban contratos: 369 passed/28 failed.
Se conserva candidate-validation-prefinal-pytest.log: 26 fallos corresponden a
cambios concurrentes de código/tests; los otros son el control Git restringido
por el sandbox y recuperación de Desktop (repetición aislada: 2 passed).
El control Git fuera de sandbox pasó (1 passed). La suite final con código estable
y acceso al control sintético pasó completa fuera de sandbox: **398 passed**.
No se ocultan los resultados previos ni se usan como prueba del estado final.

Smokes finales de wheel: validación (5 schemas, 4 plantillas), HU y catálogos
aprobados. Se guardan con prefijo candidate-validation para conservar la evidencia
histórica de 01/04. OpenSpec strict del cambio aprobado; 12 main specs aprobadas;
sync exacto del Purpose, cuatro requisitos y ocho escenarios. No hay hallazgos
críticos ni warnings de implementación pendientes en la verificación. Los bloqueos
de runtime y evals no ejecutados se conservan y no son certificaciones nuevas.
