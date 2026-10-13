# Verificación de historias y PR — 07

Fecha: 2026-10-13, America/Bogota. Base de implementación: 54faea5.
Alcance: contratos, fixtures, lectura seleccionada, preview, adaptador de
publicación/reconciliación y gates locales. No certifica GitHub ni agentes.

## Dependencia y autorizaciones

06 conserva su infraestructura verificada (439 pruebas, smoke instalado,
specs sincronizadas en ec84193/54faea5). No se modifican sus recibos históricos,
126 evaluaciones Luna/medium not_run ni tareas 2.4/3.3 pendientes. La excepción
aprobada el 2026-10-13 autoriza implementación local de 07 y pruebas con dobles.
El usuario también autorizó explícitamente archivar 07 con pendientes
documentados; el archivo no satisface el criterio de salida ni habilita 08.

El push de esta rama al repositorio del producto fue solicitado por el usuario
y guarda el código y evidencia del incremento. No es el smoke de publicación
de una HU cliente ni certifica el adaptador: son operaciones distintas, con
destinos y criterios de aceptación distintos.

## Implementación y pruebas

Contratos StorySnapshot, ProviderBinding, PublicationIntent,
PublicationAuthorization, PublicationReceipt y StoryPlanBinding v1, más
PublicationRequest. Schemas derivados en raíz/paquete y ejemplos sintéticos
validados; recursos pasivos con hashes y atributos Git que preservan bytes.
Consultar [contratos y comandos](../story-pr-integrations.md).

Lectura GitHub implementada con operaciones acotadas de gh y puente MCP
explícito del host; lectura offline con fixture de dos revisiones e instrucción
maliciosa. No hay gh instalado en este entorno. Se probaron identidad incorrecta,
credenciales/herramienta/puente ausentes, issue incorrecta, secretos y selección
de capacidades con dobles. No se declara conectividad GitHub real verificada.

Preview conserva título/cuerpo/marker/candidato/evidencia y autorización por
hash, sin proveedor, login o escritura implícita. Export externo es exclusivo.
Evaluaciones not_run/blocked permiten preview y bloquean publicación incluso
con autorización. El gate recalcula la matriz del milestone 7, no acepta una
etiqueta passed aislada. Evaluaciones 08 siguen no disponibles.

Publicación registra intent antes del push en SQLite separado; lease de rama
ausente y precondición MCP explícita. Reconciliación consulta branch/head/PR
antes de repetir, incluyendo pérdida antes/después de crear rama y pérdida
después de crear PR. Rechaza repos/base/head/marker/draft incorrectos, ramas
ajenas, múltiples PR y conflictos de intent. Conserva URL y receipt; no escribe
comentarios, no merge ni despliegue. Todos los resultados positivos de este
flujo usan un doble declarado simulated=true y certified=false.

El gate final consume HU real de 04 y evidencia del candidato de 05. Comprueba
identidad, aprobación, evidencia de tests/capacidades y revisión independiente,
binding historia-plan inmutable, contexto, árbol y modos del commit final.
Se probaron cambios de specs, contexto y modo después de aprobación, y checkout
CRLF normalizado sin filtros. El procedimiento pasivo exige sync/archive antes
del freeze o recaptura/revalidación. Attach requiere callback del host que
devuelva True tras éxito observado; ausencia/error conserva estado explícito.

## Trazabilidad de escenarios y catálogos

| Escenario delta | Test/protocolo | Estado/evidencia |
| --- | --- | --- |
| Changed story | test_story_revision_and_acceptance_require_new_approval; test_final_committed_candidate_rechecked_after_openspec_changes[changed_story] | Determinista local; binding inmutable, revisión nueva exige plan/aprobación |
| Injected instructions | test_injected_story_is_data_and_does_not_select_repository; test_fixture_revision_and_injection | Datos externos sin capacidades ni efectos operativos |
| Authorized draft PR | test_authorized_draft_and_repeat_never_duplicates | passed con doble; smoke real blocked |
| No publication permission | test_no_publication_permission_preserves_preview_and_remote | passed, sin escrituras |
| Pending required agent evaluations | test_actual_pending_evaluations_block_publication_before_provider; test_cli_preview_pending_evals_never_authenticates_or_writes | Scorer real, 144 pendientes; publicación blocked |
| Interrupted PR creation | test_lost_response_reconciles_durable_intent[pr]; test_lost_push_before_remote_effect_retries_only_after_readback | T20 passed con doble, sin segundo PR |
| Foreign branch | test_foreign_branch_never_overwritten; test_second_intent_cannot_replace_branch_owner | passed, sin reemplazo |
| Preview snapshot | test_preview_does_not_create_state_or_call_provider | passed; snapshots/estado preservados |
| Existing export destination | test_export_existing_destination_is_exclusive; test_preview_linked_destination_rejected | passed; archivo/hardlink preservados |
| Preview with deferred evaluations | test_cli_preview_pending_evals_never_authenticates_or_writes[not_run/blocked] | Preview partial; gate blocked, sin login |

T20 se asigna a 07 en el catálogo de diseño y se comprueba mediante doble.
El catálogo original permanece not_run; esta evidencia independiente registra
su ejecución determinista. E21 (contexto malicioso), E22 (PR existente/timeout)
y E23 (falta de autorización) tienen controles de código comprobados y protocolo
de agente separado. Sus 18 capturas/anotaciones reales permanecen not_run,
además de las 126 de 06: **144 requeridas, cero ejecutadas**. No se convierten
tests Python en evaluaciones de modelos. El holdout sigue reservado a promoción.

## Revisión independiente

Una revisión independiente de código detectó tres problemas Important:
redirección de push por url.* Git, ausencia de vínculo entre historia y plan,
y comparación incorrecta de blobs LF contra checkout CRLF. Se corrigieron con
rechazo de rewrites antes del push, contrato/SQLite StoryPlanBinding separado,
y comprobación de bytes físicos junto con normalización LF/CRLF explícita.
Se precisaron también creación atómica en MCP y éxito explícito de attach.
Los tests reprodujeron los fallos de destino/MCP/attach y ausencia de binding;
el caso CRLF necesitó corregir la fixture para no editar recursos de onboarding
propios, cuyo contrato v1 correctamente detectaba drift. Su prueba final cubre
una baseline y un candidato CRLF reales. No afirmar RED de la normalización
desde un fallo de preparación o importación.

Otros regresores reprodujeron y corrigieron attach repetido, reintento de push
sin efecto y aparición concurrente de PR. No se prometen aislamiento absoluto
entre herramientas ni capacidades del puente sin una implementación real.
El veredicto y las correcciones locales no certifican el rendimiento de Luna,
la autenticidad de capturas, proveedor real o independencia humana de holdout.

La primera suite completa se interrumpió al reproducir una regresión CLI:
un import local de preview de PR ocultaba el preview de onboarding en main,
provocando UnboundLocalError al llamar init. Se reprodujo en
test_cli_json_and_invalid_flags (1 failed, 3 passed con -x), se corrigió con
alias pr_preview y se verificó esa prueba (1 passed). Se conservan el log parcial
story-pr-prefinal-pytest.log y la traza story-pr-regression-investigation.log;
no representan una suite completada. El smoke final comprueba también init
y la suite final gobierna la afirmación de regresión resuelta.
Los indicadores de fallo del primer log parcial corresponden a
test_cli_json_and_invalid_flags, test_human_preview_represents_json,
test_cli_doctor_exit_codes_and_sanitization,
test_cli_binding_proposal_and_human_hashes y
test_git_status_never_executes_client_filter. Este último falla en su control
positivo antes de llamar al kit: sh.exe no puede crear signal pipe dentro del
sandbox (Win32 error 5). Se reproduce la causa con la fixture sintética y el
test pasa fuera del sandbox (1 passed in 1.15s). No se debilita ni omite el
control; la suite final se ejecuta con esa misma autorización de entorno.
El intento parcial posterior y el grupo CLI dentro del sandbox se conservan
como story-pr-sandbox-prefinal-pytest.log y story-pr-cli-sandbox-regressions.log.
La prueba CRLF se comprueba también con una mutación aislada en memoria que
reproduce la proyección incorrecta al hash del blob LF (1 failed con
candidate_changed); no modifica código de producción ni la suite concurrente.
La prueba normal pasa (story-pr-crlf-green.log) y la suite final vuelve a
comprobarla. Los logs de intentos fallidos permanecen identificados como tales.

## Verificación y límites de cierre

Suite final: **507 passed in 981.48s (0:16:21)**, proceso terminado con código 0.
La suite final, duración, código de salida y hash del log se registran en
story-pr-verification.json y story-pr-final-pytest.log. El smoke instalado con
Python -I verifica siete contratos nuevos, cuatro contratos HU previos,
recursos, preview, gate de evals blocked y el protocolo 06 de 126 ejecuciones.
La instalación solo utiliza .smoke-venv del proyecto. Build/install/hash
requirieron escalación por ACL Windows de temporales/wheel; sin cambios Python
globales ni recursos cliente reales. Las salidas históricas de 06 se conservan.

OpenSpec strict verifica el delta; se sincronizan cuatro requisitos y diez
escenarios en story-pr-integration con Purpose completo y sin headers delta.
Los quince main specs se validan. El archivo se efectúa únicamente tras comparar
el resultado sincronizado con el delta y comprobar los pendientes de tareas.

| Dimensión | Resultado |
| --- | --- |
| Completitud | 7/10 tareas locales verificables; CRITICAL pendientes 2.3, 2.5, 3.3 |
| Corrección | 4/4 requisitos con implementación, 10/10 escenarios trazados; ejecución GitHub y evaluaciones de agente no verificadas |
| Coherencia | Contratos nuevos separados, gates vigentes, estado simulado explícito y ausencia de motor LLM; criterio de salida completo no satisfecho |

Pendientes CRITICAL de aceptación: 2.3 requiere smoke de escritura en repo
sintético real con gates y autorización específica; 2.5 requiere capturas y
anotaciones E21/E22/E23 y gate final; 3.3 requiere HU fuente → PR draft real
autorizado y evidencia de reanudación sin duplicado. No falta una etiqueta
de tarea: falta esa evidencia. Se archiva con advertencias por autorización
expresa del usuario. **publication_allowed=false, certified=false,
next_increment_enabled=false y exit_criterion_satisfied=false**.
