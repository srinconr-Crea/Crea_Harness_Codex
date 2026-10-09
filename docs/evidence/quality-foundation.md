# Evidencia y verificación del cambio 01

Fecha: 2026-10-09. Windows, Python 3.13. Implementación local de
`01-quality-practices-and-eval-foundation`, usando apply, sync y archive
solicitados por el usuario. Publicación autorizada en origin/main.

## Dependencias

Base 0.1.0: `bootstrap-codex-local-core`, commit `ccaee8a`, y
`apply-client-onboarding`, commit `a72377e`. Ambos están archivados con
evidencia en `docs/evidence/`; origin/main partía de `a72377e604b26df4360ae85b1ac1e6f21c306963`.
Se revisaron sus specs, contratos y evidencias; esta implementación no modifica
descriptor/política/binding ni el comportamiento de init/recover.

## Implementación y coherencia

`harness_core.quality` define modelos estrictos, límites, composición y
validación semántica. `harness_local.quality_resources` comprueba el paquete
offline antes de devolver catálogos/fixture. Schemas generados en el paquete
y `schemas/`; generador actualizado. Recursos íntegros con LICENSE/NOTICE
Databricks; carga pasiva y sin dependencias Spark/MLflow.

Se conservan IDs/fuentes/oráculos. Las extensiones seleccionan cliente y versión
base, añaden evidencias y registran excepciones con motivo/scope/revisión.
No pueden sustituir reglas base ni modificar permisos. Los metadatos de revisión
no son autenticación; el flujo de aprobación verificable pertenece al cambio 04.
Definiciones siempre not_run; resultados de tests del kit viven en esta evidencia.

## Trazabilidad de requisitos y escenarios

| Capability / Scenario | Prueba en tests/test_quality.py |
| --- | --- |
| practices / Applicable rule | test_loads_complete_offline_catalogs_and_selects_pyspark |
| practices / Unsupported recommendation | test_loads_complete_offline_catalogs_and_selects_pyspark: SP-03/SP-04 advisory, ejecución not_run |
| practices / Intact snapshot | test_loads_complete_offline_catalogs_and_selects_pyspark; wheel smoke |
| practices / Altered resource | test_tampered_resources_rejected: alter/missing, SOURCE y manifiesto inválidos |
| practices / Stricter client rule | test_extension_adds_and_strengthens_without_mutating_base_or_policy |
| practices / Policy bypass | test_extension_conflicts_and_policy_bypass_rejected: permissions/skip_gate; política no es entrada mutable de la API |
| evaluation / Valid cases | test_loads_complete_offline_catalogs_and_selects_pyspark; test_synthetic_oracles_are_independent_of_agent_outputs |
| evaluation / Broken references | test_invalid_definitions_fail_before_any_execution; test_fixture_paths_resolve_and_missing_fixture_blocks_loading |
| evaluation / Unexecuted catalog | test_definition_report_never_certifies_runtime_or_agent; invented_score/output/passed_definition |
| evaluation / Missing runtime | test_definition_report_never_certifies_runtime_or_agent: blocked con ejecución not_run |
| evaluation / Regression case | test_rubric_rejects_missed_defect_and_false_positive: defecto conocido omitido |
| evaluation / Clean control | test_rubric_rejects_missed_defect_and_false_positive: hallazgo inventado y control limpio |

6 requisitos y 12 escenarios cubiertos. T23 del catálogo se ejecuta en
`test_tampered_resources_rejected[alter]`, cambiando la Skill databricks-core.
Los tests/evals futuros conservan not_run; no hay ejecución de agentes ni HU.
Golden/holdout, tres repeticiones y gates son definiciones comprobadas; ejecutar
un agente y reservar un holdout operativo sigue correspondiendo al cambio 06.

## Comprobaciones

Pruebas primero: 34 casos fallaron por ausencia de la API; después pasó el
comportamiento. Se añadieron controles de schemas/secretos/tamaño, se observó
su fallo y se implementaron: 36 pruebas de calidad pasan.

La primera suite en sandbox terminó con 214 passed / 1 failed: el control
positivo de `test_git_status_never_executes_client_filter` no pudo crear el
signal pipe de Git Bash (Win32 error 5). Se reprodujo la causa con hash-object;
la prueba completa pasó fuera del sandbox sin modificar test ni producto.
La repetición completa fuera del sandbox terminó: **215 passed in 1070.60s**,
sin fallos. Comando: `.venv/Scripts/python.exe -m pytest -q --tb=line -p no:cacheprovider`.

Wheel construido e instalado con --no-deps en `.smoke-venv`; Python -I carga
desde site-packages. `quality-wheel-smoke.json` conserva hash del wheel,
dataset, manifest y upstream commit, 32 reglas / 24 tests / 24 evals,
activation=false y agent_execution=not_run. No importa pyspark/mlflow/databricks.
El smoke de onboarding conserva 15 checks con clientes sintéticos alpha/beta;
solo se permite en wheel el fixture de calidad explícito, sin fixtures cliente.

OpenSpec validación estricta inicial: 15/15 elementos válidos (8 cambios y
7 main specs tras sync). Dos notas INFO de longitud corresponden a specs
anteriores; sin errores del cambio 01. Las dos nuevas main specs conservan todos
los requisitos/escenarios del delta y usan ## Requirements.

`.gitattributes` conserva los recursos con hashes sin conversión de bytes,
manteniendo las reglas anteriores de openspec_kit. Se comprobó el contenido
real de 231 blobs preparados en Git contra sus manifiestos; todos coinciden.
Se conserva whitespace upstream original, sin alterar archivos oficiales.

## Verificación OpenSpec antes de archivo

Se aplicó `openspec-verify-change` leyendo status, apply/contextFiles, código,
tests y evidencia. Completeness: 9/9 tareas, 6/6 requisitos. Correctness:
6/6 requisitos y 12/12 escenarios trazados a comportamiento comprobado.
Coherence: contratos core separados de carga local, v1 conservado, upstream
íntegro, extensiones pasivas y not_run conforme a design. Sin hallazgos
críticos, advertencias ni checks aplicables sin verificar del incremento 01.
Los runtimes/roles futuros quedan fuera del alcance; no son checks omitidos de
una capacidad entregada. Criterio de salida cumplido; el cambio 02 puede empezar
tras su propia comprobación de dependencia. Este reporte no lo implementa.

## Alcance

No se certifica Desktop, agentes, Databricks ni rendimiento. No se instala una
Skill global, cambia un cliente real o ejecuta un script upstream. El wheel
contiene datos pasivos; su integridad no es una firma. La API y su uso/errores
se documentan en `docs/quality-foundation.md`. Los cambios 02–08 siguen propuestos.
