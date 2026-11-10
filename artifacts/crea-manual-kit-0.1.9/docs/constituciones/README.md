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

## Configurar la selección

Primero completar las decisiones de cada capa necesaria, redactar sus reglas y obtener
la revisión del responsable; solo entonces marcarla `Estado: active` y asignar su revisión.
Revisar también comunes y capacidades. Los documentos activos no se consumen mientras
`rules.enabled=false`. Cambiar ese booleano tampoco habilita adaptadores de ejecución.

Ejemplo del bloque `rules` para un proyecto Silver/Spark **después** de completar y aprobar
Silver y revisar comunes/Spark; sustituir el bloque correspondiente en docs/proyecto.json,
sin reemplazar el resto de su configuración:

```json
{
  "enabled": true,
  "index_path": "docs/constituciones/README.md",
  "common": ["docs/constituciones/comunes.md"],
  "layers": {"silver": "docs/constituciones/capas/silver.md"},
  "capabilities": {"spark": "docs/constituciones/capacidades/spark.md"}
}
```

Las claves `silver` y `spark` deben coincidir con las declaradas en el contexto de la HU.
El mapa del proyecto registra documentos disponibles; Planner selecciona los pertinentes
para cada HU y congela sus referencias para los cuatro roles. No añadir capas sin completar
ni activar todas las capacidades por defecto. Para el procedimiento completo, ver la sección
5.1 de docs/configuracion-manual.md. La distribución conserva los mapas vacíos y reglas
desactivadas hasta que el cliente haga esta revisión.

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
