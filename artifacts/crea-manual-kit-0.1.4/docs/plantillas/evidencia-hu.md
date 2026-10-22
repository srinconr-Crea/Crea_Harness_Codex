# Evidencia de HU — <change>

## 1. Solicitud y criterios
Solicitud, cambio OpenSpec seleccionado y criterios verificables.

## 2. Estado y coordinacion
Etapa actual; identificadores reales de planner/developer/tester/reviewer; rondas de correccion.
No afirmar ejecucion de agentes a partir de archivos de configuracion.

### Confirmaciones de planificacion
Artefactos presentados por planner y nueva solicitud humana para apply; confirmaciones
de explore/update cuando correspondan. No confundir con la aprobacion final de archivo.

## 3. Candidato revisado
Commit si existe, diff y archivos modificados/nuevos. Si no hay commit, conservar un diff
revisable y hashes de los archivos del candidato incluidos los no rastreados. La vista de pruebas excluye solo outputs generados declarados en docs/hu/<change>/pruebas/
y conserva recibo de exclusiones. No excluir codigo, tests, fixtures o criterios para estabilizar hashes.

## 4. Plan y resultados de pruebas
plan_id, candidate_digest, base/HEAD e inventario Git completo; enlaces a plan, resultados,
gate, recibos y resumen por intento. Comando, entorno, version/runtime, fecha y resultado por criterio. Guardar solo evidencia
permitida. Registrar failed/blocked/not_run y el motivo; no tratarlos como passed.

## 5. Revision y sync
Hallazgos, correcciones, resultado verify, specs sincronizadas y diff presentado.

## 6. Aprobacion humana de archivo y publicacion
Estado inicial: PENDIENTE. Registrar respuesta humana, fecha, cambio y candidato al recibirla.
Identificar expresamente si autoriza commit/push, remoto, rama feature, base y archivos incluidos.
Una aprobacion solo de archivo mantiene publicacion pendiente.
Si se modifica el candidato o las specs, invalidar esta aprobacion y revisar de nuevo.
Agregar la propia respuesta humana y metadatos previstos de archivo/publicacion no
invalida la aprobacion si no se alteran alcance, criterios ni resultados revisados.

## 7. Archivo y pendientes
Operacion ejecutada, ruta final del cambio y limitaciones. Indicar rama feature, base,
remoto y rutas aprobadas antes del commit. El resultado de commit/push y su SHA se entregan
en la respuesta final: no editar este registro despues solo para incluir su propio commit.
Registrar si la aprobacion incluye crear PR Azure, con repo, ramas y titulo/cuerpo.
ID/URL y verificacion del PR se entregan en la respuesta final; no hay merge ni deploy.

## 8. Configuracion y extensiones
Referencias de skills, agentes, MCP o pasos usados en esta HU; sin credenciales.

## 9. Responsabilidades de tareas
Developer completa implementacion/tests y entrega ready_for_test. Tester completa
ejecucion con recibos y entrega ready_for_review. Reviewer completa revision/verify
y cierre autorizado. Una casilla de ejecucion requiere evidencia, no existencia de codigo.
