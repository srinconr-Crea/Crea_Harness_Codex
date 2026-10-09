# Evidencia: apply-client-onboarding

## Alcance y implementación

Implementación local sobre Windows; fixtures sintéticos alpha y beta. Los
contratos descriptor/política/binding v1 se conservan. Nuevos contratos
OnboardingPlan/Journal/LockOwner y schemas generados; recursos OpenSpec 1.13.2
empaquetados con licencia MIT y manifiesto. Ver `openspec-generation.json` y
`onboarding-wheel-smoke.json` para ejecuciones reales y hashes del wheel.

Módulos: `harness_core.onboarding_plan` valida contratos, destinos y límites;
`harness_local.onboarding` produce/exporta el plan; `application` aplica y
recupera; `windows_fs` fija handles y crea exclusivamente; `execution_state`
mantiene journal y lock; `resources` verifica el kit offline.

## Trazabilidad de escenarios

| Capability / Scenario | Prueba o evidencia |
| --- | --- |
| application / Apply reviewed plan | test_apply_repeat_doctor_and_recovery_preserves_existing; smoke alpha/beta |
| application / Stale or redirected plan | test_preflight_rejection_no_client_writes, cinco variantes |
| application / Tampered plan payload | test_preflight_rejection_no_client_writes[payload]; test_strict_plan_duplicate_secret_version_and_size |
| application / Policy denies bootstrap file | test_policy_applies_to_bootstrap; test_policy_limits |
| application / Linked destination | test_ancestor_rename_and_junction_rejected; test_target_cannot_be_replaced_between_preflight_and_journal |
| application / Existing custom instructions | test_unprepared_beta_existing_code_specs_and_prepared_conflict; test_prepared_preview_deterministic_and_read_only |
| application / Compatible prepared client | test_unprepared_beta_existing_code_specs_and_prepared_conflict; test_prepared_preview_deterministic_and_read_only |
| application / Unprepared checkout | test_unprepared_beta_existing_code_specs_and_prepared_conflict; smoke alpha/beta |
| application / Missing or incompatible kit resources | test_kit_resource_integrity_and_missing |
| application / Repeated completed application | test_apply_repeat_doctor_and_recovery_preserves_existing; smoke alpha/beta |
| application / Local files prepared but remote access unknown | test_runtime_command_guard_and_optional_tool_readiness; smoke alpha/beta |
| preview / Valid onboarding preview | test_prepared_preview_deterministic_and_read_only; test_binding_proposal_export_determinism |
| preview / Missing target | test_cli_json_and_invalid_flags |
| preview / Client without descriptor | test_unprepared_second_client; test_unprepared_beta_existing_code_specs_and_prepared_conflict |
| preview / Descriptor identity unavailable | test_unprepared_second_client |
| preview / Existing project instructions | test_prepared_preview_deterministic_and_read_only |
| preview / Prepared client | test_prepared_preview_deterministic_and_read_only |
| preview / Divergent managed artifact | test_codex_presence_and_divergent_workflow_preview |
| preview / Repeated preview | test_prepared_preview_deterministic_and_read_only; test_binding_proposal_export_determinism |
| preview / Snapshot unchanged | test_native_diagnostic_and_preview_no_global_effects; test_binding_proposal_export_determinism; smoke snapshots |
| preview / Developer without binding | test_binding_proposal_export_determinism; test_cli_binding_proposal_and_human_hashes |
| preview / Ambiguous binding inputs | test_export_overlap_and_missing_binding_fields; test_cli_apply_recover_and_exclusive_modes |
| preview / Export reviewed preview | test_binding_proposal_export_determinism; smoke alpha/beta |
| preview / Existing export destination | test_binding_proposal_export_determinism |
| recovery / Failure after a file creation | test_failure_recovery_before_binding_and_modified_owned_file; test_each_durable_boundary_preserves_uncertain_files |
| recovery / Ambiguous interrupted creation | test_ambiguous_partial_and_foreign_journal; test_each_durable_boundary_preserves_uncertain_files |
| recovery / Concurrent apply | test_checkout_lock_process_identity; test_real_second_process_lock_rejects_apply |
| recovery / Recover unchanged owned files | test_apply_repeat_doctor_and_recovery_preserves_existing; smoke alpha/beta |
| recovery / Preserve developer changes | test_failure_recovery_before_binding_and_modified_owned_file; test_nonempty_directory_and_changed_policy_preserved |
| recovery / Recovery dry-run | test_apply_repeat_doctor_and_recovery_preserves_existing; test_ambiguous_partial_and_foreign_journal; smoke snapshots |
| recovery / Foreign journal | test_ambiguous_partial_and_foreign_journal |

## Comprobaciones adicionales

Pruebas de aliases Windows, patrones `**` con cero componentes, límites de
bytes/operaciones, ausencia de SQLite/configuración global, recursos del wheel,
procesos simultáneos y lock huérfano/PID reciclado. La matriz de journal recorre
42 fronteras de persistencia antes y después (84 casos), preservando archivos
sin prueba durable de propiedad. Guard de subprocess permite solo sondas de
versión y lecturas Git durante runtime.

Revisión independiente detectó y se corrigieron dos problemas: reaplicación de
un plan determinista después de recovered y sustitución de raíz después del
preflight. Ambos tienen pruebas de regresión que fallaron antes del cambio y
pasaron después. La raíz y entradas seleccionadas se fijan antes de validar.

## Reproducción

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe scripts/generate_schemas.py
.venv/Scripts/python.exe -m build --wheel --no-isolation
.smoke-venv/Scripts/python.exe -m pip install --no-deps --force-reinstall dist/crea_local_harness-0.1.0-py3-none-any.whl
.venv/Scripts/python.exe scripts/smoke_onboarding_wheel.py
openspec validate apply-client-onboarding --strict
```

En este host el sandbox bloquea los pipes de sh.exe del control positivo de
filtros Git y temporales del backend build. Esas comprobaciones se ejecutaron
fuera del sandbox; no se debilitó la prueba. Una primera matriz tuvo un fallo
operacional antes de alcanzar una frontera; se repitió ese caso y la suite final
conserva su resultado real. Los resultados finales se adjuntan al cerrar la
verificación, sin considerar los runs anteriores como aprobación definitiva.

Límites: preparación no verifica Desktop ni auth Databricks. El journal no es
una firma frente a un operador que controla el estado; ownership incierto se
conserva. No se promete atomicidad distribuida ni recuperación total cuando
existen conflictos. No se hicieron cambios sobre repositorios cliente reales.

## Resultado final de pruebas

Suite completa: **177 passed in 465.85s**, código 0, con los 84 casos de
fronteras del journal. Dos pruebas añadidas posteriormente (raíz OpenSpec relativa
y exportación enlazada) pasaron por separado: **2 passed in 9.66s**. No se
omitió ninguna prueba. Wheel reconstruido e instalado offline en .smoke-venv:
**15 comprobaciones**, alpha y beta completados y recuperados. Validación
estricta del cambio: válida. La revisión independiente no dejó hallazgos
pendientes después de corregir sus dos incidencias con RED→GREEN.
