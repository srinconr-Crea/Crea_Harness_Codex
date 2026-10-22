# Flujo y estados

## 1. Preparación del cliente

Conservar herramientas → autenticación humana → clone/create repo → combinar kit en
raíz → OpenSpec init o conservación del root existente → personalización → comprobar
roles/configuración → commit separado del setup → primera HU con checkout limpio.
No introducir carpeta padre ni un segundo root. Python se prepara solo si se usará el
helper o tests Python; no instalar Semgrep/Cosmic Ray/Spark para todas las HU.

En personalización: elegir intérprete, suites, dependencias, comandos y presupuesto;
clasificar archivos; fijar reglas de runtime y gates; configurar efectos permitidos.
`setup_complete=false` bloquea, aunque el JSON sea válido. Herramientas faltantes no
se instalan implícitamente durante apply.

## 2. Secuencia por HU

| Etapa | Entrada | Salida / responsable |
|---|---|---|
| Explore/plan | HU, specs vigentes, código, catálogo de fallos | Planner: requisitos y escenarios; deltas, design/tasks, cobertura y nuevas pruebas justificadas |
| Selección preliminar | Manifiesto previsto y política | Principal/helper: plan preliminar; no es recibo del candidato final |
| Revisión humana | Artefactos y plan presentados | Nueva solicitud humana de apply; no inferir por silencio |
| Apply | Plan autorizado | Developer: código/tests previstos, ready_for_test, tareas de ejecución pendientes |
| Selección final | Diff real completo, base y huellas | Principal/helper: plan canónico, discrepancias contra manifiesto; cambio de alcance vuelve a planner |
| Prueba local | Plan final configurado | Tester: suites afectadas y recibos; fallos funcionales al developer, entorno blocked al principal |
| Integración condicional | Local favorable, runtime requerido | Tester: preflight, smoke del mecanismo y suite autorizada; inventario incluso si falla |
| Revisión | Candidato, plan/resultados, código y rúbrica | Reviewer: hallazgos estructurados y OpenSpec verify, sin repetir batería por defecto |
| Corrección | Hallazgo probado | Developer corrige; Tester repite checks invalidados; Reviewer reevalúa hallazgo |
| Sync | Todos los checks requeridos passed + revisión favorable | Reviewer sincroniza specs; valida la documentación modificada, no repite Spark por el sync |
| Archivo/publicación | Diff/candidato y destino presentados | Aprobación humana vigente, reviewer archive; principal commit/push/PR según proveedor y alcance |

El developer puede hacer diagnóstico focalizado para construir una regresión; el Tester
posee la ejecución oficial independiente. TDD que requiera RED/GREEN independiente
se planifica como alternancia secuencial Tester→Developer→Tester, solo cuando aplique.

No marcar una tarea mixta «implementar y verificar» antes de recibir evidencia. En el
plan nuevo separar tareas de código, pruebas y revisión; definir quién marca cada
casilla. No modificar retroactivamente criterios o skills OpenSpec para facilitar cierre.

## 3. Estados y evidencia

`ready_for_test` es estado Crea propuesto, no estado nativo de OpenSpec. Incorporarlo
al handoff y al orquestador. El progreso CLI se conserva tal como lo devuelve OpenSpec.
El helper emite ready/blocked para plan y passed/blocked para gate técnico. Es un
componente del cierre: no sustituye inspección de cobertura, verify, sync o aprobación.

`not_applicable` solo por una condición observable documentada. No usarlo para una
prueba requerida sin herramienta. Un resultado failed se preserva; corregir genera
otra ejecución, nunca reemplaza el fallo anterior ni convierte el historial en passed.

La decisión de no ejecutar un check se reconstruye de la política y las entradas:
el plan incluye reglas coincidentes para cada ruta y selected con IDs/snapshots.
El resumen explica checks no seleccionados por ausencia de reglas, sin llamarlos
«pruebas aprobadas». Para auditoría exhaustiva, el adaptador puede producir una vista
derivada decisiones.json; no mantener dos documentos canónicos divergentes.

## 4. Publicación y despliegue

El kit continúa sin deploy automático, merge ni pipelines implícitos. Candidato
verificado → publicación autorizada → PR → checks CI configurados → merge humano
→ despliegue al target autorizado → smoke → promoción controlada.

El adaptador CI es una ampliación del proyecto. Consume política/resultados del mismo
commit; no requiere instalar Codex ni ejecutar subagentes en CI para checks mecánicos.
Si se autoriza integrar CI, inspeccionar los eventos/ramas del cliente e identificar
validaciones premerge y efectos de publicación reales. No asumir nombres de ramas,
destinos o triggers a partir de otro repositorio. No desplegar desde PR.

Gate de entrega por target: checks predeploy requeridos + revisión/aprobación + SHA
identificado; bundle validate/plan según CLI real; deploy y smoke con recibos; smoke
fallido impide promoción siguiente. Rollback de código no revierte datos Delta por sí
solo. Recuperación de datos requiere procedimiento/alcance aprobado.
