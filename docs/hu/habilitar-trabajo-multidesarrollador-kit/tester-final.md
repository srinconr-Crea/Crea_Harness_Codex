# Informe independiente de Tester — intento 1 histórico

Fecha: 2026-11-10. Resultado actual: **BLOQUEADO; no acredita el candidato final**.

Se ejecutó una sola vez `../.integration-venv/Scripts/python.exe -B scripts/validate_manual_019.py run` desde `harness`, con el Python existente y permiso elevado para los pipes de Git for Windows en fixtures locales. No se editaron archivos de producción, no se instalaron paquetes, no se usaron servicios reales y no hubo commit, push ni publicación. No se regeneraron ni corrigieron recibos.

## Identidad y alcance

- Fixture: `../.test-data/v019-c949dd5b`, descrito en [fixture-019.json](fixture-019.json).
- Base: `2c4bf3d4353cce806f8093653d5fedc90848cb57`.
- Plan: `89182ef399a18d4a37eaffa316a9128f4b03c073018939b03cb2f3652b184666`.
- Candidate digest: `9b8e8db519c4dade088ce8af3f6427f6ad2cc241dc23ed3c09cea3517168b22e`.
- Check/input: `kit-regression` / `92aea282d904af0b11c09ff89240db98bff7a26fbcec921654e4c3315588e795`.
- Environment ID: `3b08527e38f11d9e01b617579faf1a8bf23063d2994335143c7ced565a02d1dd`.
- Ejecución: `2026-11-10T14:41:12.933331+00:00` a `2026-11-10T14:51:32.528373+00:00`.

El handoff de planificación autoriza `run_tests` para validar bytes exactos del portable 019 en un checkout local sintético. Esta revisión cubre ese intento y sus evidencias técnicas. No es un piloto nativo de roles, una HU de negocio, una validación de dos personas ni una prueba con servicios remotos reales. Las suites raíz y supplemental se ejecutan y reportan por separado.

## Resultado observado y diagnóstico

El proceso pytest terminó con código **0**, sin timeout ni truncamiento. [Stdout](pruebas/attempt-1/stdout-kit-regression.log) registra `198 passed, 37 subtests passed in 618.81s (0:10:18)`; stderr está vacío. El comando exterior terminó con código **1**, porque el [gate primario](pruebas/attempt-1/gate.json) quedó `blocked`.

Los bloqueos reales son:

- `CHECK_NOT_PASSED: kit-regression`
- `EMPTY_OR_INCONSISTENT_SUITE: kit-regression`
- `INVALID_OR_UNAVAILABLE_LOCAL_RECEIPT: kit-regression`
- `REQUIRED_ASSERTION_MISSING_OR_FAILED: kit-regression`

[Resultados](pruebas/attempt-1/resultados.json) registra `reason: MISSING_OR_INVALID_STRUCTURED_REPORT`, contadores en cero y `assertions: {}`. El [recibo](pruebas/attempt-1/receipt-kit-regression.json) conserva `exit_code: 0` y `report: {}`. Estos ceros reflejan el rechazo del reporte estructurado; no afirman que pytest no haya ejecutado pruebas.

La inspección del [JUnit primario](pruebas/attempt-1/junit-kit-regression.xml) encontró **198 elementos testcase, 198 IDs únicos, cero duplicados, cero failures/errors/skipped**, mientras su testsuite declara `tests="235"`. La diferencia es 37, igual al número de subtests aprobados que informa stdout. La llamada de lectura a `testing.reports.junit` importado desde el candidato congelado del fixture reproduce exactamente **`ValueError: JUNIT_COUNTER_MISMATCH`**, sin ejecutar suites ni modificar archivos.

El entorno existente usa **pytest 9.1.1**, con soporte builtin de subtests; `pytest-subtests` no está instalado. El runner de validación invoca pytest directamente. Se identifica una incompatibilidad de integración entre el JUnit producido en este entorno y el parser estricto del candidato. Este informe no relaja el parser, no transforma XML y no presenta el gate como aprobado.

## Inspección de aserciones y contrato plan/gate

Los siguientes IDs aparecen en el XML sin failure, error ni skipped. Esta lectura independiente no sustituye las aserciones rechazadas por el gate.

| Criterio | ID real en JUnit (prefijo común `candidate.tests.crea.`) | Estado XML |
| --- | --- | --- |
| CA01 | `test_team_delivery.TeamDeliveryTests::test_independent_target_and_legacy_fallback` | passed |
| CA02 | `test_local_environment.LocalEnvironmentTests::test_shared_binding_plan_is_rebuilt_and_alias_does_not_change_python_identity` | passed |
| CA03 | `test_developer_preparation.DeveloperPreparationTests::test_bind_preview_and_repeat_are_local_and_idempotent` | passed |
| CA04 | `test_target_compatibility.TargetCompatibilityTests::test_A_independent_stories_continue_with_current_bounded_evidence` | passed |
| CA05 | `test_target_compatibility.TargetCompatibilityTests::test_C_same_rule_incompatible_and_D_clean_git_contradiction` | passed |
| CA06 | `test_content_v3.ContentV3Tests::test_real_plan_run_gate_remains_current_after_declared_observation` | passed |
| CA07 | `test_client_composition.ClientCompositionTests::test_client_has_local_entry_without_distribution_prompts` | passed |

También aparece aprobado `candidate.tests.crea.test_testing_lifecycle.LifecycleTests::test_attempts_two_hu_unchanged_configuration_real_run_gate`. El código de este test intercepta `workflow.execution.run_process` durante `plan` y `gate`; la observación retenida en el fixture, `candidate/.test-work/retained/process-observations.json`, registra `plan_suite_calls: 0` y `gate_suite_calls: 0`, con hashes de policy/execution sin cambios. Los planes internos observados son `5ed25b351a31f4f9f10cd6064d6862bd54d02057fc6856e64c840baedbdc7240` y `456e3b9c0adc34d6147a8835537967e7a7b7e44a4b719a5d625f8c75d86d89bc`.

La propiedad de no ejecutar suites durante plan/gate está cubierta por ese contrato automatizado local. No se afirma una observación de procesos en un piloto nativo ni una prueba de todo entorno posible.

## Integridad e invalidación posterior

Antes de la ejecución, una comparación independiente confirmó **492/492 archivos idénticos por SHA-256** tanto en `artifacts/crea-manual-kit-0.1.9` como en `fixture/candidate`, frente al inventario congelado. Después de la ejecución, el fixture conserva los 492 hashes originales. Los ocho outputs copiados al repositorio son byte a byte idénticos a sus originales en el fixture.

Hashes primarios relevantes:

- JUnit: `6d93beac90ff6c9e41cb62786735f56aae69e38bbfd263294281a7400bd2639f`.
- Receipt: `1391ffe991473a1f85d0ce630fcda5080fc68e8dd84bf8e48546ff7fb5138832`.
- Resultados: `876a9ffdb100f2a164b4e37edadef5b52da96707151afa1d3607b469d0945385`.
- Gate: `a28c6f435a2818b3df2fe5b11560af1ca2dd2c22162b6597da3846c7ad2c6607`.
- Stdout: `f0ace3357ee597e99dbdb856128af9a4081be1e86c9b997812a040b402a34735`.
- Stderr vacío: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

La comparación posterior detectó divergencia de la fuente actual frente al inventario de intento 1 en `kit-manifest.json`, `scripts/crea/preparar-desarrollador.py` y `tests/crea/test_developer_preparation.py`. El coordinador notificó una corrección posterior para distinguir estados de conexión Azure (403/network/timeout), que invalida este candidato como versión final. El Tester no realizó esos cambios y no ensayó la fuente corregida en este intento.

**Conclusión acotada:** las pruebas del candidato congelado produjeron stdout/JUnit sin fallos, pero la integración de evidencia bloqueó el gate. El intento 1 permanece histórico, íntegro y no aprobatorio. Una ejecución futura requiere un intento nuevo; sus resultados no pueden inferirse de esta evidencia.
