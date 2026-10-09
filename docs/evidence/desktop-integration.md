# Evidencia parcial del incremento 02

Fecha: 2026-10-09, America/Bogota. Windows, Python 3.13. El usuario solicitó
apply/sync/archive/push y después indicó dejar las pruebas Desktop pendientes.
No se declara certificación ni criterio de salida cumplido.

## Dependencia

01-quality-practices-and-eval-foundation está implementado, verificado y
archivado en commit `52aacee74ea246b314086fef4c6e71ec9b81c4a6`, paquete 0.1.0.
Se revisaron quality-foundation.md y quality-verification.json: 215 pruebas,
36 de calidad, 12 escenarios y wheel aislado. Esto permite empezar 02.

## Implementación

Contratos estrictos/versionados en harness_core.desktop, seis schemas en dos
ubicaciones, ocho roles propios y Skill harness-hu pasivos con manifiesto/hash
y referencias a prácticas del 01. Los perfiles requieren modelo/esfuerzo de
cuenta explícitos; no hay fallback ni nombres universales preactivados.

Nuevos integrate y desktop-check. Plan/journal de integración propios; v1
conserva contratos y create-only. AGENTS/TOML preservados con plan explícito,
hash/identidad, backup durable externo y confinamiento Windows por handles.
Recover conserva conflictos y valida backups; reconoce restores/deletes
anteriores al reanudar. Se conservan directorios vacíos. No es transacción
atómica; un contenido parcialmente escrito distinto requiere resolución manual.

Documentación, errores, uso y protocolo: docs/desktop-integration.md. Ningún
cliente real ni global se modificó. No se ejecutaron modelos, scripts upstream,
MCP productivos ni sistemas remotos durante las pruebas.

## Trazabilidad

Los nombres siguientes pertenecen a tests/test_desktop.py. Cuando un escenario
necesita observación de app, el test valida el evaluador de declaraciones;
la aceptación efectiva permanece separada.

| Capability / Scenario | Test o protocolo | Estado |
| --- | --- | --- |
| desktop / Custom instructions | test_custom_agents_and_toml_preserved_and_recovered | Local probado |
| desktop / Drift before apply (T21) | test_drift_rejected_before_any_target_or_state_write | Local probado |
| desktop / Observed role | test_matching_desktop_observations_certify_only_requested_roles; protocolo por rol | Evaluador probado, Desktop not_checked |
| desktop / Unsupported surface (T24) | test_files_cli_never_certify_and_missing_required_tool_blocks | Rechazo files/CLI probado; selector personalizado no expuesto |
| desktop / Intact applied file | test_custom_agents_and_toml_preserved_and_recovered; test_interrupted_recovery_resumes_persisted_recovered_records | Local probado |
| desktop / User modification | test_recovery_modification_and_replacement_identity_conflict; test_hashed_equal_replacement_is_not_owned | Local probado |
| desktop / Preview snapshot | test_preview_snapshot_and_exclusive_export | Local probado |
| desktop / Existing export destination | test_preview_snapshot_and_exclusive_export; test_export_hardlink_and_target_junction_rejected | Local probado |
| roles / Small story | test_assignment_single_writer_nested_case_alias_and_isolation | Local probado |
| roles / Writer collision | test_assignment_single_writer_nested_case_alias_and_isolation | Local probado |
| roles / Available configuration | test_catalog_and_templates_have_bounded_roles_and_passive_practices; test_matching_desktop_observations_certify_only_requested_roles | TOML/evaluador probados; efectivo not_checked |
| roles / Unavailable model | test_no_silent_model_fallback_and_no_unselected_profiles | Local probado |
| roles / Missing required tool | test_files_cli_never_certify_and_missing_required_tool_blocks | Local probado |
| roles / Read-only reviewer | test_effective_permission_and_hook_coverage_are_independent | Evaluador probado; permiso real not_checked |

7 requisitos y 14 escenarios trazados. E03/E04 permanecen not_run, sin outputs
ni scores inventados. Protocolo manual define inputs, anotación humana y tres
repeticiones. El E04 público no es holdout operativo reservado.

## Revisión y pruebas

requesting-code-review exigió revisión independiente con subagente read-only;
identificó tres hallazgos, reproducidos RED antes de corregir:

- Credenciales TOML: reject_secrets se aplica al objeto parseado antes del plan.
  test_toml_credential_field_never_exported RED→GREEN.
- Retry recover: reconoce estado ya recuperado; prueba parametrizada interrumpe
  antes/después de persistir. RED→GREEN.
- Tamaño UTF-8: límites de bytes en preview y contrato consistentes con recover.
  test_multibyte_payload_is_bounded_for_recovery RED→GREEN.

Sin menores diferidos. Solo observación real Desktop quedó fuera de la revisión,
y sigue pendiente; no se acepta como verificada por el autor.

Primera prueba falló por API inexistente antes de implementar. Resultados finales
en desktop-verification.json. desktop-wheel-smoke.json comprueba 8 roles, dos
perfiles sintéticos, seis schemas y 10 checks desde site-packages con Python -I.
Construcción/lectura del wheel requirieron salir del sandbox por ACL temporales
Windows. La suite completa también usa ejecución fuera del sandbox por el
control positivo Git Bash documentado en 01; no se alteró la prueba.

OpenSpec: cambio válido --strict; nueve main specs válidas. Sync autorizado de
desktop-integration (4 requisitos/8 escenarios) y role-tool-catalog
(3 requisitos/6 escenarios), conservando Purpose y todos los bloques sin
encabezados delta ni TBD. Sync actualiza el contrato; no certifica Desktop.

## Verificación OpenSpec

Se aplicó openspec-verify-change leyendo status/contextFiles y contrastando
código, tests y design. Completitud parcial: tareas locales marcadas; ejecución
real y criterio de salida abiertos. Correctness local probada, aceptación
Desktop no verificada. Coherence: núcleo separado, recursos pasivos, backup
externo, perfiles explícitos y journal independiente. Certificado y disponibilidad
son declaraciones manuales, no firmas ni autenticación.

Esta sesión no ofrece agent_type para seleccionar las plantillas generadas
ni observación de configuración efectiva. Rol/modelo/esfuerzo/Skill y sandbox/MCP
efectivos permanecen not_checked. Hooks no habilitados; cobertura not_checked.
Versión CLI observada 0.162.0-alpha.17.2 no se usa como certificación Desktop.

El criterio de salida completo no se cumple y 03 no se habilita. Al presentar
las cinco tareas pendientes, el usuario eligió **conservar el cambio activo
hasta completar Desktop**. No se archiva. Sync y push están autorizados.

## Actualización posterior: adaptación supervisada

Las afirmaciones anteriores describen la verificación local original. El usuario
aportó después ejecuciones en Desktop y aprobó el alcance supervisado y la
anotación humana con defecto de E04 conservado. La verificación vigente es
[desktop-runtime-2026-10-09/verification.md](desktop-runtime-2026-10-09/verification.md).
Se conserva el conflicto de sandbox y certificado estricto false; el progreso
posterior no convierte los antiguos not_run en passed ni altera sus fuentes.
