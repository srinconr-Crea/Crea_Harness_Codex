# Constituciones del proyecto

Son reglas de proyecto, no permisos nativos de Codex. Se activan en `docs/proyecto.json`
solo después de revisión del responsable. La distribución deja `rules.enabled=false`.

| Documento | Estado inicial | Selección |
| --- | --- | --- |
| comunes.md | Reglas iniciales justificadas por AGENTS y prácticas vigentes | Comunes pertinentes |
| capas/bronze.md | template, necesita decisiones reales | Solo Bronze declarada |
| capas/silver.md | template, necesita decisiones reales | Solo Silver declarada |
| capas/gold.md | template, necesita decisiones reales | Solo Gold declarada |
| capacidades/sql.md | Reglas iniciales justificadas | Solo SQL declarada |
| capacidades/spark.md | Reglas iniciales justificadas | Solo Spark declarada |

Jobs y pipelines son especialidades pendientes: no se distribuyen documentos vacíos.
Añadirlos cuando existan obligaciones justificadas y responsable. Nunca activar una plantilla
como si contuviera reglas de cliente ya aprobadas.

Cada documento activo declara `Estado: active`, `Revisión: <revisión>` y encabezados
`### <ID-estable>`. Cada regla incluye Aplicación, Obligación, Fundamento, Evidencia,
Comprobación (`automatic`, `review`, `human_decision`) y Excepciones. Mantener IDs sin
reutilizarlos para otro significado; referencias extensas y parámetros quedan en buenas prácticas.

Planner selecciona comunes + capas/capacidades de la HU, con justificación, revisión y hash.
Developer, Tester y Reviewer reciben esa misma selección. Una HU Silver/Spark no carga Gold,
SQL, jobs ni pipelines por disponibilidad. Listas vacías se justifican para HU documentales.

El responsable del proyecto completa las plantillas, decide contradicciones críticas y aprueba
cambios de obligación, criterios, excepciones sustantivas, selección con impacto y activación
de bloqueos. Una aclaración editorial sin cambio de significado admite revisión/diff local,
sin otra HU de gobierno. Conservar decisiones y renovar solo autorizaciones afectadas.

Obligaciones compatibles se acumulan. Una especialización reemplaza una regla común solo
con delegación o excepción explícita; no aplicar «último texto gana». Las políticas superiores
y restricciones reales del entorno siguen vigentes. Ningún rol modifica criterios o reglas
para hacer aprobar su propio resultado. Conflictos se elevan al responsable y solo detienen
el trabajo dependiente. Excepciones permitidas citan regla, motivo, dueño, respuesta humana,
alcance y fecha de revisión/vencimiento; no sustituyen evidencia técnica obligatoria.
