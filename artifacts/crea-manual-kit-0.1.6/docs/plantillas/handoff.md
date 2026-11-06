# Handoff — contrato canónico y vista humana

Fuente única: `docs/hu/<change>/handoffs/<fase>-<intento>.json`, validado contra
`docs/plantillas/handoff.schema.json`. Crear exclusivamente; preservar intentos y enlazar
`previous_handoff`. Fases son etiquetas de las operaciones existentes, no agentes/fases nuevos.

Secciones JSON y presentación común: **HU y fase · resultado · alcance/candidato · reglas y
evidencia · bloqueos · decisión requerida · siguiente paso**. Usar `transiciones.py render`
para producir la vista humana desde el contrato; no mantener dos estados independientes.
El resto de esta guía detalla qué enlazar, no otro registro que se deba copiar a mano.

| Sección | Contenido |
| --- | --- |
| identity | HU local, change, fase/intento, emisor/destinatario, agent_id real o null, fecha. No inventar ID Boards o agente. |
| result | Estado real y qué se completó. |
| scope | Objetivo, criterios canónicos, candidate/base/HEAD, approved_paths globales, read_paths/write_paths del despacho, snapshots y acciones. |
| context | Listas de capas/capacidades, no-aplica justificado, reglas con ID/revisión/hash, decisiones funcionales y riesgo justificado. |
| evidence | Artefactos/decisiones, plan preliminar o recibos técnicos existentes, objetos y entrega cuando apliquen. |
| pending | Bloqueos, avisos, preguntas y excepciones con responsable y transiciones afectadas. |
| continuation | Transición, siguiente paso, decisión necesaria o null y respuesta humana aplicable. |

Antes de Apply se requieren criterios y `evidence.validation_plan`, no resultados futuros.
Desde Tester se requieren `evidence.tests.plan/results` y contraste con gate. Las aprobaciones
contienen acciones, response_ref y digest del contexto/candidato/paquete de entrega aplicables.
No permiten al JSON autenticar por sí solo la decisión humana: el principal la contrasta con
la conversación real. Planificación y cierre usan autorizaciones distintas.

`scope.git_inputs` declara por check las entradas Git funcionales (`HEAD`, `branch`, `index`)
o `[]` tras revisar independencia. Omitir una declaración no acredita independencia; otras
dependencias se declaran no soportadas por la equivalencia. `scope.moves/sync` contiene solo
transformaciones exactas revisadas, sin glob de todo OpenSpec. Los perfiles orientan acceso;
los snapshots detectan diferencias persistentes; el sandbox solo impone lo que el entorno permita.

Las secciones históricas siguientes sirven como lista de detalle a trasladar al JSON:

## 1. Identidad y estado
- HU/cambio:
- Rol e identificador real del agente:
- Estado: ready | ready_for_test | ready_for_review | passed | ready_for_archive | needs_changes | blocked
- Candidato: commit si existe + diff y lista de archivos actuales (incluir untracked).

## 2. Entrada y alcance
Objetivo, criterios, artefactos leidos, rutas permitidas y restricciones.

## 3. Resultado
Archivos modificados, decisiones, tareas completadas y criterios cubiertos.

## 4. Validacion
Por cada check: comando exacto, entorno, fecha, resultado, salida resumida y ruta de evidencia.
Estados de check: passed | failed | blocked | not_run | not_applicable (con motivo).

## 5. Hallazgos y siguiente paso
Problema concreto, archivo/linea cuando aplique, impacto y rol destinatario.

## 6. Configuracion y extensiones usadas
Skills, perfil, MCP o pasos adicionales realmente utilizados; sin secretos.

## 7. Pruebas canonicas
- plan_id / candidate_digest / base y HEAD reales:
- Rutas plan.json, git.json, resultados, gate y receipt por intento:
- Checks seleccionados y criterios/assertions cubiertos:
- Motivo concreto de cualquier reejecucion solicitada al Tester:
- Rondas globales usadas / workflow.max_fix_rounds y proximo rol:
- round_id / motivo / candidato inicial-final / resultado del ciclo de correccion:
Enlazar resumen/recibos; no copiar logs completos en cada handoff.

Intentos N>1: previous_handoff apunta al N-1 de la misma fase con sha256 obligatorio. Snapshots entry/exit incluyen hash. publication_paths enumera el expediente final autorizado; el principal comprueba commit y push por separado con --operation.
