# Evidencia y verificación: bootstrap-codex-local-core

Fecha: 2026-10-08. Incremento implementado en Windows, Python 3.13.14.
Se usaron `openspec-apply-change`, pruebas antes de implementación, revisión
independiente y `openspec-verify-change` sobre el cambio spec-driven.

## Resultado

| Dimensión de verificación | Resultado |
| --- | --- |
| Completeness | 23/23 tareas; 15 requisitos identificados e implementados |
| Correctness | 15/15 requisitos y 26/26 escenarios con evidencia abajo |
| Coherence | Separación core/local, contratos explícitos y preview sin aplicación; agrupación de módulos documentada en design |

No quedan hallazgos críticos ni advertencias del incremento. Las capacidades
Desktop/remotas no verificadas son exclusiones explícitas de estas specs, no
capacidades certificadas por esta evidencia. El cierre y publicación requieren
autorización aparte de la verificación; se recibió el 2026-10-09.

## Comprobaciones ejecutadas

```text
.venv/Scripts/python.exe -m pytest -q --tb=line -p no:cacheprovider
47 passed in 16.26s

.venv/Scripts/python.exe -m build --wheel --no-isolation
Successfully built crea_local_harness-0.1.0-py3-none-any.whl

.smoke-venv/Scripts/python.exe -m pip install --no-deps --force-reinstall dist/crea_local_harness-0.1.0-py3-none-any.whl
Successfully installed crea-local-harness-0.1.0

.venv/Scripts/python.exe scripts/smoke_wheel.py
6 smoke checks passed; wheel resources and isolation verified

openspec validate bootstrap-codex-local-core --strict
Change 'bootstrap-codex-local-core' is valid
```

Resultado estructurado del wheel: [wheel-smoke.json](wheel-smoke.json). Contiene
SHA-256, archivos empaquetados, comandos/códigos y diagnóstico real. Se comprueba
que el módulo importado con `-I` proviene de `site-packages`, no de `src` ni de la
instalación editable. El wheel contiene matriz y plantilla, sin fixtures cliente.
Se usaron venvs dentro del producto; sin instalación global del harness.

Las pruebas sintéticas crean repos Git locales, un worktree, junction y un filtro
benigno que escribe un marcador dentro de `.test-data`. El control positivo con
`hash-object` confirma que el filtro está activo; la inspección comprueba argumentos
que anulan sus clean/process/required y ausencia del marcador. El sandbox de esta
sesión bloquea las tuberías del shell de Git: esa prueba se ejecutó fuera de dicho
sandbox con alcance limitado a fixtures; el código de doctor/preview no usa shell.

## Mapa de requisitos a implementación

| Requisitos | Implementación |
| --- | --- |
| Contratos separados/versionados | `src/harness_core/contracts.py`, schemas generados |
| Selección/integridad de política | `configuration.validate_configuration`, flags CLI |
| Consistencia cliente/repo | `validate_configuration`, `normalize_remote`, `diagnostics.checkout` |
| Entradas acotadas/seguras | `read_bytes`, `UniqueLoader`, `load_document`, `reject_secrets`, `safe_path` |
| Estado externo aislado | `validate_configuration`, comprobación de ruta y sufijo |
| Tool readiness | `diagnostics.probe`, `run_bounded`, `compatibility.json` |
| Capacidades Desktop explícitas | `doctor` checks pendientes, `inspect_target` presencia Codex |
| Target y validación opcional | `checkout`, `inspect_target`, `doctor` |
| Salida/códigos | `aggregate`, `report`, `cli.main` |
| Diagnóstico read-only | Sondas fijas, Git con locks/fsmonitor/filtros desactivados |
| Onboarding solo preview | `cli.main`, `onboarding.preview` |
| Preparado/no preparado | Descriptor explícito, plantilla y acciones de preview |
| Preservación de specs cliente | Detección de siete Skills; acciones existing/manual/conflict |
| Plan determinista | Orden de acciones, identidades, hashes de entradas/contenidos |
| Ausencia de efectos onboarding | Funciones sin escritura/instalación/auth; guardia de comandos y snapshots |

Los nombres de archivo agrupados difieren del árbol orientativo del design; se
actualizó su decisión 1. No se cambió el alcance ni se omitió un contrato.

## Trazabilidad de los 26 escenarios

Tests de configuración en `tests/test_configuration.py`; locales en
`tests/test_local.py`. Parametrizaciones aportan casos adicionales a los escenarios.

| Spec / escenario | Prueba o evidencia |
| --- | --- |
| client: Valid configuration set | `test_valid_configuration_and_transport_aliases`, `test_documented_fixtures_validate` |
| client: Unsupported configuration | `test_all_contracts_are_strict`, `test_validation_error_identifies_field_without_value` |
| client: Policy bytes changed | `test_changed_policy_is_rejected` |
| client: Repository attempts to override policy | `test_contracts_reject_unknown_version_and_fields` |
| client: Matching HTTPS and SSH identities | `test_valid_configuration_and_transport_aliases` |
| client: Cross-client binding | `test_cross_client_and_state_rejections` |
| client: Wrong or missing origin | `test_origin_rejection` |
| client: Invalid configuration file | `test_unsafe_documents_are_rejected`, `test_size_and_regular_file_limit`, `test_traversal_and_linked_ancestors` |
| client: Embedded credentials | `test_unsafe_documents_are_rejected`, `test_cli_doctor_exit_codes_and_sanitization` |
| client: State location inside target | `test_cross_client_and_state_rejections` |
| doctor: Tool absent | `test_probe_errors_and_limits`, `test_preview_tool_failure_preserves_other_checks` |
| doctor: Slow or unrecognized version probe | `test_probe_errors_and_limits` |
| doctor: Local configuration files exist | `test_codex_presence_and_divergent_workflow_preview` |
| doctor: Verify workflow absent | `test_inspection_and_workflow_conflicts` |
| doctor: Configuration inputs not supplied | wheel smoke `doctor --path . --json` incluye configuration_not_supplied |
| doctor: Partial diagnosis | `test_compatibility_and_aggregate`, `test_cli_doctor_exit_codes_and_sanitization` |
| doctor: Diagnosis without credentials | `test_native_diagnostic_and_preview_no_global_effects`, `test_doctor_injected_no_effects` |
| preview: Valid onboarding preview | `test_prepared_preview_deterministic_and_read_only` |
| preview: Missing target | `test_cli_json_and_invalid_flags`, `test_non_git_target_and_redundant_identity_flags` |
| preview: Client without descriptor | `test_unprepared_second_client` |
| preview: Descriptor identity unavailable | `test_unprepared_second_client` |
| preview: Existing project instructions | `test_prepared_preview_deterministic_and_read_only` |
| preview: Prepared client | `test_prepared_preview_deterministic_and_read_only` |
| preview: Divergent managed artifact | `test_codex_presence_and_divergent_workflow_preview` |
| preview: Repeated preview | `test_prepared_preview_deterministic_and_read_only` |
| preview: Snapshot unchanged | `test_native_diagnostic_and_preview_no_global_effects`, `test_unprepared_second_client` |

Además: límites de salida, versiones incompatibles, códigos 0/1/2, JSON parseable,
formato humano con contenidos/hashes, YAML alias y nesting extremo, UTF-8 inválido,
schema_version booleano, traversal, schemas/modelos, Git worktree y HEAD separado.

Los snapshots cubren target, política, binding, estado propuesto inexistente y
configuración global sintética. La prueba con sondas reales coloca HOME/APPDATA/
XDG/CODEX_HOME en esa configuración sintética y exige que permanezca igual. Una
guardia solo admite `--version` y lecturas Git seleccionadas; no admite comandos
de instalación, auth, red ni ejecución cliente. La fixture beta incluye un módulo
que fallaría si fuera importado; no se importa ni se ejecutan sus tests.

## Revisión independiente y límites prácticos

Se corrigieron los hallazgos de revisión: alias YAML de coste exponencial,
neutralización de filtros Git, información omitida en salida humana y errores de
frontmatter profundo/UTF-8. Sus pruebas forman parte de la suite final.

El diagnóstico real observa Python 3.13.14, Git 2.53.0.windows.3, Node 24.15.0,
OpenSpec 1.13.2 y Databricks CLI 1.18.0. El rango aceptado no equivale a probar todas
sus versiones. Se asumen herramientas instaladas confiables; no se certifica su
supply chain. El resultado real es `partial`: agentes/modelos/hooks en Desktop,
autenticación y conectividad Databricks permanecen pendientes.

Durante la implementación del 2026-10-08 no se crearon agentes/hooks operativos,
SQLite, recursos Databricks, repos remotos ni PR. La evidencia anterior corresponde
a ese incremento, antes de su publicación. No se alteró NaturaPet ni otro cliente real.

## Cierre autorizado, 2026-10-09

Se sincronizaron los 15 requisitos de las tres capacidades hacia `openspec/specs/`,
preservando sus 26 escenarios. Las tres specs pasaron validación estricta y se
compararon con los deltas antes de archivar. El cambio, con 23/23 tareas completas,
se movió a `openspec/changes/archive/2026-10-09-bootstrap-codex-local-core/`.
`openspec list --json` confirma que no quedan cambios activos.

La suite se volvió a ejecutar antes de publicar: **47 passed in 17.78s**.
Destino autorizado: `srinconr-Crea/Crea_Harness_Codex`, conservando el commit
inicial existente de `main`. La base publicada incluye código, schemas, Skills,
specs, tests y documentación; venvs, fixtures temporales y builds permanecen
excluidos mediante `.gitignore`. La publicación no activa capacidades Desktop
o Databricks adicionales.
