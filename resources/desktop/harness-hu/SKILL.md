---
name: harness-hu
description: Conducir una historia de usuario supervisada en un cliente preparado, con plan aprobado, candidato, gates locales, contexto persistido y revisión independiente.
---

Usar al iniciar o reanudar una HU en un checkout cliente preparado por onboarding.
Codex conserva conversación, herramientas y delegación; Python valida contratos y
registra decisiones. Las instrucciones no conceden permisos ni restringen Desktop.

## Selección y análisis

1. Leer AGENTS cliente; seleccionar target, policy, binding, story y recibo de
   onboarding. Exigir prepare completado y checkout limpio con base confirmada.
   Registrar el actor escritor principal explícito en start, incluso para HU pequeña.
2. Consultar load_quality() y load_desktop(). Recursos upstream son pasivos:
   descargarlos no permite ejecutar sus scripts, instalar ni autenticar.
   practices.json del paquete harness_local.quality_kit conserva reglas y fuentes.
3. Explorar/enriquecer definición, criterios y fuentes; identificar impacto, rutas,
   operaciones, tests y capacidades requeridas. Preguntar solo decisiones faltantes.
   Usar principal para cambios pequeños. Delegar analyst/impact-analyzer/planner
   únicamente cuando el impacto lo justifique, conservando revisión independiente.
4. Guardar fuentes user/local/template y decisiones en plan y handoff. No depender
   exclusivamente de la memoria conversacional. Si una fuente opcional falta,
   unavailable/not_checked; una capacidad requerida ausente bloquea.

## Contratos y comandos

Forma común: `harness hu ACTION --path TARGET --policy POLICY --binding BINDING
--story HU --operation OP --input INPUT.json --json`. INPUT incluye schema_version=1.
Status solo necesita selección y story. OP es único por acción lógica; repetir los
mismos datos revalida y no duplica el efecto. Datos distintos con el mismo OP fallan.
Consultar schemas empaquetados de harness_core y docs/hu-lifecycle.md del producto.

- start: onboarding_plan, writer_actor, simulation explícito; crea HU/intento draft.
- transition analyzing: explora sin autorizar edición.
- plan: criteria, paths, operations create/modify/delete, tests, required_capabilities,
  max_delegations (0–4), allow_worktrees, sources y decisions. Propose/update de
  OpenSpec produce artefactos; el plan registrado es el manifiesto de ejecución.
- approve: actor, confirmed, client_id, checkout_id, attempt, revision, plan_sha256.
  Obtener acción explícita del operador para el hash vigente; nunca inventar una
  aprobación humana ni reutilizar una autorización genérica de planificación.
- assign: role, actor, write_paths, isolation=checkout_id, delegation_depth 0–1.
  Registrar antes de delegar; no exceder límite acumulado, cuatro assignments ni
  un escritor por ruta. Revisores no escriben. Selección modelo/esfuerzo y permisos
  efectivos provienen del catálogo/observaciones; no inferirlos de archivos TOML.
- worktree: path externo, branch local nuevo, confirmed. Requiere allow_worktrees
  aprobado. El adaptador registra intención, desactiva hooks/filtros y crea solo
  checkout local. Un worktree necesita selección/binding propio antes de otra HU;
  no usarlo como bypass del manifiesto del checkout original.
- candidate: snapshot del HEAD base, bytes del working tree e índice Git. Incluye
  nuevos, modificados y eliminados. Edición externa fuera del manifiesto bloquea.
- transition implementing/validating/reviewing/ready_to_publish: gates de aprobación,
  identidad, capacidades, candidato actual y evidencia requerida.
- evidence: id, kind test/review/capability, actor, candidate_sha256, evidence_ref,
  status passed/failed/blocked/not_run/unavailable y simulated. No traducir ausencia
  de ejecución a passed. Capacidades requeridas necesitan observación real; guardar
  evidencia de capacidad al capturar candidato antes del gate validating.
- handoff: role, actor, plan_sha256, candidate_sha256 cuando corresponda, sources,
  decisions, findings y status completed/blocked/not_run. Developer entrega diff
  acotado; tester entrega ejecución y controles negativos; auditor entrega hallazgos;
  verifier compara requisitos, escenarios y evidencias. Revisores reciben snapshot
  inmutable y actor independiente de escritor/tester, con sandbox efectivo observado.
- correct: máximo dos correcciones de código por intento. Infraestructura falla
  mediante block(reason) sin consumir corrección; cambio de alcance vuelve a plan
  y exige nueva aprobación. No absorber una ampliación silenciosamente.
- resume: revalidar cliente/checkout, contexto, base, candidato y operaciones
  pendientes. No asumir éxito ni repetir efectos ante pérdida de proceso.
- transition failed/cancelled y attempt: un nuevo intento exige failed, base limpia
  y revalidación; reinicia aprobación/evidencia/límites, conservando historia.

## Validación y cierre

El candidato probado incluye índice y bytes exactos; después de editar, volver a
candidate y ejecutar tests/revisión. Evidencia stale/not_run/blocked bloquea.
HU sintética con simulation=true puede alcanzar ready_to_publish/partial con
evidencia simulated=true: publication_allowed=false y certified=false siempre.
En HU real, evidencia simulada no supera gates. No hay published ni PR en 04.

Presentar estado, hash, criterios, resultados reales, limitaciones y pendientes.
Skill/AGENTS/hooks no cubren todas las herramientas Desktop. Si un evento no está
observado/cubierto, declarar el límite y exigir permisos externos para garantías
adicionales. No afirmar nuevo certificado Desktop/Databricks.

E05/E06/E08/E19 requieren protocolo de agente, repeticiones y anotación según
catálogo. Pruebas Python de gates no sustituyen esa ejecución: mantener not_run,
observed_output/scores=null hasta reunir evidencia válida. No activar configuración
global, publicar ni ejecutar producción por inferencia.
