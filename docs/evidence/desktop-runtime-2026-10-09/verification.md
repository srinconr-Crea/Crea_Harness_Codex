# Verificación de la adaptación de 02

Fecha: 2026-10-09, America/Bogota. El alcance aprobado distingue preparación
supervisada verificada y certificación estricta por capacidades.

## Completitud, corrección y coherencia

Dos contratos/schemas nuevos y comandos review-snapshot, review-compare y
supervised-prepare. Core evalúa aceptación sin relajar assess_certificate;
adaptador Windows valida identidad y configuración seleccionadas, integración
aplicada intacta y contenido del candidato. No activa modelos ni MCP/hooks.
Código de nuevos controles probado primero con fallos de import/API y luego
con pruebas positivas/negativas; un fallo de Windows case alias detectado por
revisión independiente se reprodujo RED y quedó GREEN.

Las ocho ejecuciones de roles conservadas en original-role-probes.json muestran
instrucciones de rol activas, Skill descubierta, lectura de fixture y Git.
La sesión padre conserva el registro de selección. Algunos agentes confundieron
catálogo pasivo con configuración efectiva o usaron Python sin dependencias:
se conservan esos resultados, sin convertirlos en aprobación de calidad.
role-runtime-probes.md registra agent_type y contrato runtime para auditor,
verifier e impact-analyzer sin overrides. Su self-report exacto no está expuesto.
No se infiere modelo efectivo de los otros cinco roles desde el chat padre.

Permisos: auditor/verifier crearon los probes, conflicto observado. Los otros
roles no hicieron prueba de escritura; MCP/hooks no se ejecutaron. Una sesión
padre read-only no se probó: el control no es observable/operable desde este
executor y la automatización de la app está excluida. Este ensayo opcional no
es condición de éxito de preparación supervisada ni prueba de imposibilidad
general. Matriz completa: desktop-certificate.json con procedencia referida.

Aceptación humana: human-annotation.json conserva la respuesta explícita del
usuario y los checks por repetición. Seis inputs/outputs originales, con
identidades de ejecución, en raw-eval-export.json. E03 cumple los dos checks
en las tres respuestas; E04-C1 falla en dos y se acepta como defecto conocido.
No se declara passed para esas repeticiones. No hay holdout operativo reservado,
tokens/costos exactos ni efectos remotos afirmados.

supervised-preparation.json valida sobre el cliente sintético una integración
aplicada intacta y candidato identificado, con aceptación ligada a identidad,
catálogo y evidencia: prepared=true, certified=false. required-isolation-blocked.json
conserva el bloqueo cuando la fase exige auditor:permissions. Esta comprobación
local no es una nueva ejecución de roles ni certificación Desktop. La captura
es posterior a las ejecuciones antiguas: no demuestra retrospectivamente que
aquellas mantuvieron intacto el candidato. El procedimiento futuro captura
antes de delegar y compara después; sus controles locales están probados.

## Trazabilidad de las 21 situaciones

| Capability / Scenario | Prueba o evidencia |
| --- | --- |
| desktop / Custom instructions | test_custom_agents_and_toml_preserved_and_recovered |
| desktop / Drift before apply | test_drift_rejected_before_any_target_or_state_write |
| desktop / Observed role | original-role-probes.json; role-runtime-probes.md; test_matching_desktop_observations_certify_only_requested_roles |
| desktop / Unsupported surface | test_files_cli_never_certify_and_missing_required_tool_blocks; matriz Desktop parcial |
| desktop / Intact applied file | test_custom_agents_and_toml_preserved_and_recovered |
| desktop / User modification | test_recovery_modification_and_replacement_identity_conflict |
| desktop / Preview snapshot | test_preview_snapshot_and_exclusive_export |
| desktop / Existing export destination | test_preview_snapshot_and_exclusive_export |
| desktop / Prepared with accepted sandbox limitation | test_preparation_requires_intact_applied_integration; supervised-preparation.json |
| desktop / Strict certification after supervised preparation | test_intact_supervised_review_keeps_strict_conflict |
| desktop / Required capability unavailable | test_failed_capability_blocks_phase_despite_acceptance; required-isolation-blocked.json |
| desktop / Original eval evidence and human annotation | raw-eval-export.json; human-annotation.json |
| roles / Small story | test_assignment_single_writer_nested_case_alias_and_isolation |
| roles / Writer collision | test_assignment_single_writer_nested_case_alias_and_isolation |
| roles / Available configuration | test_catalog_and_templates_have_bounded_roles_and_passive_practices; contrato runtime referido |
| roles / Unavailable model | test_no_silent_model_fallback_and_no_unselected_profiles |
| roles / Missing required tool | test_files_cli_never_certify_and_missing_required_tool_blocks |
| roles / Read-only reviewer | probes reales; test_effective_permission_and_hook_coverage_are_independent |
| roles / Supervised review with intact candidate | test_intact_supervised_review_keeps_strict_conflict |
| roles / Reviewer changes candidate | test_candidate_drift_blocks_without_reverting (change/add/delete/absent) |
| roles / Missing or stale operator acceptance | test_stale_or_missing_acceptance_blocks (7 variantes) |

## Límites y evaluación

Preparación supervisada no es una frontera de seguridad. Comparar hashes no
impide escrituras ni detecta necesariamente cambios restaurados o fuera de los
scopes. Aceptación/certificado son declaraciones manuales ligadas a evidencia,
sin firma ni autenticación. La integración y snapshots mantienen los límites
Windows y de tamaño, no transacciones atómicas del conjunto.

No hay contradicción entre aceptar el uso supervisado y conservar sandbox
conflictivo. 03 puede usar este alcance verificado únicamente para preparación;
capacidad requerida fallida sigue bloqueando su fase. Certificación estricta
incompleta, MCP/hooks no observados y defecto de E04 son limitaciones aceptadas,
no fallos de implementación ocultados. Los criterios del piloto 08 permanecen
más exigentes y no se relajan por este resultado.

Resultados finales de pruebas y wheel: supervised-verification.json y
../desktop-wheel-smoke.json. Los tres planos (test local, evidencia Desktop,
aceptación humana) se mantienen separados.
