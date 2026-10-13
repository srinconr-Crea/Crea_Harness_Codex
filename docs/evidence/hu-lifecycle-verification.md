# Verificación de 04-hu-lifecycle-and-development-gates

Fecha: 2026-10-13, America/Bogota. Baseline c005854, rama
`codex/04-hu-lifecycle-and-development-gates`, kit 0.1.0.

## Dependencia y decisiones

03 está implementado/verificado/archivado en c005854. Su evidencia
`guided-onboarding-verification.json` registra 298 passed y smoke de wheel instalado;
el archivo es `openspec/changes/archive/2026-10-13-03-guided-client-onboarding`.
Esta sesión repitió baseline: 297 passed y un fallo del control positivo de filtro
Git dentro del sandbox; el mismo control pasó fuera del sandbox (1 passed).
La preparación supervisada sigue separada de certificación estricta de Desktop.

El diseño existente es el plan de implementación. SQLite HU v1 es independiente
del journal de onboarding y migra solo una base vacía. Un artefacto JSON/hash es
exportación derivada: SQLite conserva la verdad durable tras pérdida de proceso.
El recibo de 03 se consume sin volver a aplicar un plan de una versión anterior;
se verifican sus archivos reales con su journal. No se cambia selected/apply v1.

La tarea sintética se resuelve con simulation=true: ready_to_publish es partial,
publication_allowed=false y certified=false. En HU real, simulated nunca supera
gates. No hay PR/ejecución remota. El push solicitado publica código del producto,
no una HU cliente mediante el adaptador.

El baseline guarda bytes de checkout junto con HEAD porque autocrlf puede
normalizar blobs; el candidato liga working tree e índice. Configuración global
se aísla en sondas Git; fixtures declaran autocrlf local. Gates detectan edición
externa persistente y declaran su cobertura en cada respuesta.

## Trazabilidad de los ocho escenarios delta

| Escenario | Implementación | Test/protocolo |
| --- | --- | --- |
| Approved plan | ApprovalRecord, approval_current, approve | test_revision_bound_approval_and_idempotency; test_wrong_approval_rejected |
| Changed scope | PlanRevision/context hash, invalidación | test_revision_bound_approval_and_idempotency; test_context_change_invalidates_and_requires_replanning; test_reused_adapter_reloads_policy_before_replanning |
| Same candidate | Candidate/evidence_gate | test_synthetic_ready_has_no_publication_authority; test_real_run_rejects_simulated_evidence |
| Edited candidate | double capture, fresh_candidate | test_candidate_edited_and_scope_bypass; test_idempotent_gate_revalidates_changed_candidate |
| Infrastructure failure | block sin consumir correct | test_limits_writer_and_infrastructure_recovery |
| Interrupted attempt | SQLite commit/rollback, pending worktree | test_committed_transaction_survives_process_loss; test_rollback_before_commit_and_unknown_database_version; test_real_process_loss_rolls_back_without_success; test_worktree_crash_reconciliation |
| Bypass detected | manifiesto sobre índice/working tree | test_candidate_edited_and_scope_bypass; test_index_cannot_hide_out_of_scope_diff; test_modified_deleted_and_new_files_in_candidate; test_crlf_baseline_and_external_byte_edit |
| Missing covered event | enforcement explícito en respuesta y Skill | test_hu_cli_status_and_invalid_requests comprueba respuesta del adaptador; protocolo below sobre límites, sin prometer interceptación Desktop |

Missing covered event: el adaptador no instala hooks ni declara eventos observados.
Cada respuesta expone enforcement='kit commands/adapters only; external Desktop
edits are detected at gates'. La Skill exige declarar ausencia y permisos externos
para garantías adicionales. Es un límite inspeccionado de interfaz/instrucciones;
no es una ejecución o certificación de hook real.

Negativos adicionales: schema desconocido/campos extra/secretos, identidad de
aprobación, test not_run/blocked/failed, capacidades requeridas ausentes, revisión
del escritor/tester, rol inactivo, colisión entre HUs, límite de delegación/correcciones,
worktree denegado, base/versiones de SQLite incorrectas, API y CLI JSON/texto.
Dos clientes se preparan mediante el flujo real de 03 y conservan estado segregado.

## Calidad asignada y evals

T16 (aprobación obsoleta) y T17 (candidato obsoleto) tienen controles locales
ejecutados con oráculo negativo. Su evidencia local se registra separada del
catálogo de diseño, que conserva not_run. Pruebas Python no certifican Desktop.

E05/E06/E08/E19: contratos/protocolos están entregados en la Skill y ejemplos,
incluyendo criterios/manifiesto, nueva aprobación, expansión de scope y HU pequeña.
Las ejecuciones de agente con repeticiones, anotación humana y holdout siguen
**not_run**, observed_output/scores=null. Los casos de contrato locales comprueban
sus gates deterministas; no se convierten en resultados passed de esos evals.
E01/E02/E24 y certificación estricta conflictiva de 02 no reciben resultados nuevos.

## Revisión independiente

La revisión read-only identificó cinco defectos reproducibles: salida humana de CLI
indexaba id ausente; replay devolvía candidato obsoleto; actor de prueba podía
autorrevisarse sin assignments; índice escondía cambios fuera de scope; instancia
reutilizada aplicaba política antigua. Se añadieron regresiones y correcciones.
Además se declaró escritor principal en Start/HuRun y se verifica catálogo activado
con check_assignments antes de delegar. El límite de tamaño ya era estricto en
Handle.read; el nuevo adaptador convierte ese rechazo en gate blocked persistido.

La comprobación posterior añadió regresiones para aprobar un plan cuyo contexto
ya cambió, repetir una cancelación después de editar el candidato y reservar un
directorio que contiene rutas de otro escritor. Se observó su fallo y luego su
paso (2 + 2 comprobaciones focalizadas). La Skill conserva practices.json, como
exige la compatibilidad del recurso existente (53 pruebas de configuración/Desktop
aprobadas). La fixture beta declara UTF-8 al leer el recibo, sin alterar el runtime.

## Resultados y verificación OpenSpec

Resultados reales de la suite, smoke instalado y validación estricta se conservan
en `hu-lifecycle-verification.json`, logs adjuntos y `hu-lifecycle-wheel-smoke.json`.
La verificación de OpenSpec inspecciona:

| Dimensión | Cobertura |
| --- | --- |
| Completitud | 10/10 tareas; 4/4 requisitos y 8/8 escenarios mapeados a implementación/tests/protocolo |
| Corrección | 340 pruebas aprobadas: aprobación exacta, contexto/política actual, candidato working tree/índice, evidencia y límites |
| Coherencia | Diseño respetado: contratos independientes, SQLite transaccional, artefactos externos, un escritor, dos correcciones, enforcement acotado |

Resultado final: `340 passed in 698.85s`; smoke del wheel instalado aprobado,
validación estricta del cambio aprobada, 11 main specs válidas y comparación de
sync exacta (Purpose, 4 requisitos, 8 escenarios, sin headers delta en main spec).
La revisión de completitud, corrección y coherencia no conserva hallazgos críticos
ni warnings de implementación pendientes. Las limitaciones de evals/certificación
se declaran arriba y no son resultados de ejecución de agentes.

El criterio de salida se cumple con suite y smoke verdes, validación estricta y
revisión de correspondencias. No exige certificar nuevas
capacidades de Desktop ni ejecutar evals pertenecientes al protocolo posterior.
05 solo se habilita después de ese criterio para implementar validadores propios;
su ejecución remota requiere evidencia/capacidades y autorización correspondientes.
