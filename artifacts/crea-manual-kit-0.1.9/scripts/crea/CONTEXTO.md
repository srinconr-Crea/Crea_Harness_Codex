# Gestión evolutiva de contexto 0.1.7

La extensión es opcional y llega con `enabled=false`; transiciones permanece `informative`, con `blocking_conditions=[]`. Ausente o desactivada mantiene contratos legacy. Configuración, schema, contexto.py, transiciones.py y testing se adoptan/revierten juntos mediante diff revisado. Preservar personalizaciones, constituciones, modelos, decisiones, HU e intentos históricos; no migrar recibos ni entregar contratos nuevos a herramientas antiguas.

## Configuración canónica

`docs/proyecto.json.context_management` contiene `schema_version="1.0"`, `enabled`, `components`, `impact_rules` y `limits`. Cada componente: ID estable, `paths` POSIX, IDs `dependencies` y `documents` con path, kind, roles y fases. Kinds: configuration (inventario/preparación), global (orientación), rule (obligación con catálogo vigente), spec (OpenSpec funcional), technical (explicación), hu (expediente actual), history (referencia histórica explícita). Los textos permanecen en su fuente. No duplicar requisitos funcionales ni decisiones en el inventario.

Cada regla de impacto: ID, componentes y/o patrones de rutas, triggers declarados (`path_change`, `behavior`, `architecture`, `dependency`, `configuration`, `tests`), documentos destino, reason y owner. Git acredita rutas; Planner declara los triggers semánticos y Reviewer contrasta significado. Los patrones usan fnmatchcase POSIX sensible a mayúsculas: `*` también cruza `/`. Ciclos se resuelven con visitados; IDs/dependencias desconocidos y rutas sin mapa se diagnostican sin inferir arquitectura. No se inventa documentación inexistente: falta/pending se registra.

Límites iniciales: `per_document_bytes=262144`, `total_bytes=2097152`. El helper lee solo referencias seleccionadas; el índice normativo se comprueba por existencia y las reglas se resuelven con `select_rules` mediante el mismo lector acotado. Las exclusiones existentes `inventory.exclude_from_context` prevalecen también para historia explícita. Prefijos terminados en `/` excluyen sus descendientes; otros valores usan fnmatchcase. Secretos no deben registrarse en el mapa. No copia contenidos a informes. Omite historia ajena salvo `--history` explícito; traversal, enlaces/junctions y escapes se rechazan. Exceso/falta deja `partial=true`, rutas y motivo, sin truncamiento acreditado.

## Operaciones

Desde la raíz del checkout consumidor, con Git local y dependencias de requirements-validation.txt ya disponibles:

```powershell
python -B scripts/crea/contexto.py select --repo . --change ejemplo --base HEAD --role planner --phase planificacion --component servicio
python -B scripts/crea/contexto.py impact --repo . --change ejemplo --base main --role developer --phase implementacion --handoff docs/hu/ejemplo/handoffs/implementacion-1.json
python -B scripts/crea/contexto.py check --repo . --change ejemplo --base main --role reviewer --phase revision --handoff docs/hu/ejemplo/handoffs/revision-1.json
```

`--trigger behavior` declara intención semántica; `--component` selecciona explícitamente. Sin handoff no se adivinan capas/capacidades normativas. Con handoff se conservan las reglas canónicas. Las tres operaciones devuelven fuentes e impacto para hacer verificable la decisión; ninguna ejecuta suites, servicios ni instalaciones. El inventario Git de rutas incluye HEAD/base, index, worktree, untracked, conflictos y ambos lados de rename/delete aunque estén excluidos de lectura. Esta observación de rutas no reemplaza el gate de contenido completo.

Por defecto solo stdout. `--out docs/hu/ejemplo/contexto/implementacion-1.json` crea exclusivamente un auxiliar acotado de esa HU; no sobrescribe ni concede exclusión de metadatos. Es un archivo funcional sujeto al plan y alcance, no otro estado canónico. Preferir integrar evidencia en el handoff. No proporcionar JSON manual como diff completo. Los contadores de archivos/bytes/procesos y duración están fuera de la identidad semántica; no hay garantía universal de milisegundos.

## Contrato y continuidad

`context.management = contexto.logical(project, componentes, triggers)` congela versión, digest de política/exclusiones/reglas, componentes, destinos y pertinencia. No incluye hashes futuros. En planificación `evidence.context_review = contexto.review(observacion, "planned", filas, null_reason)` registra impacto previsto; las filas tienen estado pending y referencias vacías. Impacto nulo exige una razón breve. No exige resultados de Tester.

Después de Apply, principal contrasta el diff completo, añade destinos previstos a approved_paths y al write_paths del único escritor autorizado, y reconcilia alcance antes del plan final. La fila final contiene path, rule, reason, owner, operation (`create|update|delete|move|keep`), status (`updated|unchanged_justified|not_applicable|pending`), justification y references. `updated` requiere referencia hash del documento destino; delete exige ausencia comprobada y baja Git; move añade target_path únicamente para esa operación, ligada a rename observado o scope.moves exacto. Ambos extremos respetan exclusiones/historia/límites antes de leer; hash diferente por sí solo no acredita calidad. `unchanged_justified` explica por qué sigue vigente. Un impacto final vacío también requiere null_reason. Reviewer revisa semántica y dispone pendientes.

Cada context_review registra role/phase de origen y exige la selección completa correspondiente, permitiendo una selección distinta legítima al transferir a Tester/Reviewer. Las sources son observaciones históricas de path/fase/existencia/observed_sha256, ligadas a la observación de entrada; no son refs actuales que impidan una edición prevista. En final se contrastan con contenido actual y las references resuelven movimientos exactos. Los handoffs se validan por schema/identidad/predecesor/política antes de tratarlos como metadatos; los ya existentes quedan congelados por hash. Los documentos reales y la configuración son funcionales. Un Sync que cambie un destino seleccionado de contexto exige reconciliar plan/run/gate; nunca se oculta una carpeta documental. Archive conserva solo el mapa exacto de movimientos y bytes revisados.

Corregir un enlace en un nuevo intento preserva candidate/plan/evidencia si no cambia contenido funcional. No reiniciar max_fix_rounds ni pedir autorizaciones vigentes otra vez. La inspección revalida referencias; no relanza suites. La invariancia de plan/run/gate sigue siendo el control técnico independiente.

## Responsabilidades

Principal configura mapa real mediante diff revisado y concreta read_paths/write_paths. Planner selecciona Explore/Propose y declara impacto previsto. Developer edita únicamente código/docs/inventario asignados y entrega su handoff. Principal reconcilia antes del plan final sin ejecutar suites. Tester consume criterios y contexto interpretativo, escribe solo evidencia/handoff propios y ejecuta plan/run autorizado. Reviewer inspecciona semántica y condiciones, realiza Verify y Sync/Archive ya autorizados en sus rutas exactas. Ninguna selección amplía permisos, crea pausas por transferencia o simula delegación nativa.

## Condiciones y códigos

`CONTEXT_SOURCES_CURRENT` verifica selección/política y lectura/ref comprobables. `DOCUMENTATION_IMPACT_RECONCILED` verifica filas, responsables y justificaciones. Ambas comienzan sin promoción. Solo habilitar condiciones mediante decisión humana `promotion_ref` y casos positivos/negativos revisados. Recomendación editorial en informative no veta avance ni concede aprobación. Contradicciones funcionales se remiten al gobierno existente.

0: inspección completa sin bloqueo nuevo habilitado, puede contener avisos. 2: condición promovida incumplida. 3: decisión humana necesaria en transiciones (el helper no crea decisiones). 4: error/indeterminación; `consume` informativo no inventa cumplimiento ni añade veto, conserva gates/autorizaciones previos. Una condición promovida indispensable indeterminada impide acreditar su continuación; trabajo independiente autorizado continúa.

Los recorridos de aceptación son sintéticos (documental, movimiento Python, Silver/Spark con runtime requerido inactivo). Un blocked remoto permanece blocked. No acreditan piloto real, agentes nativos, hooks activos ni certificación remota.

## Equipo 0.1.9
La compatibilidad reutiliza este mismo mapa y su recorrido inverso para consumidores.
Sin activación conserva Git/catálogo y límites explícitos; no añade un mapa paralelo.
Lecturas entre revisiones conservan exclusiones/budgets e historia ajena fuera de selección.
