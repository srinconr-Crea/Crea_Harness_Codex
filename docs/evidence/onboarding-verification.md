# Verificación OpenSpec: apply-client-onboarding

## Resultado

| Dimensión | Resultado |
| --- | --- |
| Completeness | 20/21 tareas al iniciar la revisión; 6.3 completada por esta verificación. 16/16 requisitos implementados. |
| Correctness | 16/16 requisitos con implementación y 31/31 escenarios trazados a pruebas/evidencia. |
| Coherence | Seis decisiones del design contrastadas; separación core/local, contratos v1 conservados y recursos fijados. |

No hay requisitos REMOVED/RENAMED. Ningún check de verificación fue omitido.
La ausencia de comprobación de Desktop/auth es comportamiento explícito del
producto, probado como not_checked; no es una certificación remota pendiente
necesaria para cerrar este cambio.

## Mapeo de implementación

| Requisitos | Implementación |
| --- | --- |
| Explicit bounded plan application | application.selected/preconditions/_apply; OnboardingPlan |
| Authorized onboarding destinations | onboarding_plan.absolute_path/separate/authorize/denied; windows_fs.PinnedTree |
| Preserve existing client artifacts | onboarding.preview; regeneración y creación exclusiva en application |
| Concrete versioned OpenSpec preparation | resources.kit; openspec_kit/manifest.json |
| Idempotent local outcome and diagnostics | application.matching_runs/verify_completed/completed_result |
| Preview-only onboarding command | cli.main; onboarding.preview |
| Preview for prepared and unprepared clients | onboarding.preview; diagnostics.inspect_target |
| Preserve client-specific specifications | inspect_target y acciones existing/proposed/conflict; allowlist finita |
| Deterministic structured preview | canonical/OnboardingPlan; reporte sin tiempos/run_id hasta apply |
| No local or remote onboarding effects | preview sin escrituras salvo export solicitado; guard y snapshots |
| Proposed developer binding | preview valida Binding v1 propuesto sin persistirlo |
| Explicit plan export | PinnedTree.file con creación exclusiva, paths externos y sin mkdir |
| External durable execution journal | execution_state.persist; Journal; intent/completion de _apply |
| Exclusive checkout execution | CheckoutLock; process_identity; lock exclusivo |
| Conservative explicit recovery | recovery_inputs/_recover; identidad/hash por handle y borrado no recursivo |
| Client isolation and sanitized outcomes | selected/journal_matches; cli y report; fixtures alpha/beta |

La matriz detallada de 31 escenarios está en `apply-client-onboarding.md`.
Resultados reales: suite 177/177, otras dos pruebas añadidas 2/2, wheel 15 checks
con ambos clientes, schemas regenerados y validación OpenSpec estricta válida.

## Coherencia y revisión

El plan exportado es distinto del reporte y se compara con regeneración del
kit; applicabilidad y readiness se separan. No se sobrescriben artefactos del
cliente. OpenSpec solo se ejecutó en fixtures de build; runtime consume recursos
locales. El journal vive fuera del checkout y el binding es la última creación.
La recuperación usa plan explícito antes de que exista binding y preserva
propiedad incierta. No hay SQLite, llamadas remotas, modelos ni tests del cliente.

La revisión independiente reportó dos hallazgos Important; ambos se corrigieron
con regresiones RED→GREEN: raíz fijada antes del preflight y reaplicación tras
recuperación total. No se declinaron comportamientos ni quedaron minors pendientes.

**CRITICAL:** ninguno. **WARNING:** ninguno. **SUGGESTION:** ninguna.
Todos los checks ejecutados pasaron. Cambio listo para sync y archivo solicitados.
