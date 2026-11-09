# Proposal

## Why

El kit portable 0.1.6 ya conserva reglas seleccionadas, handoffs, snapshots y gates, pero el mantenimiento del inventario y de la documentación pertinente sigue dependiendo de recordar instrucciones. Cada HU necesita identificar y reconciliar su impacto documental con un coste proporcional, para que configurar el proyecto una vez permita mantenerlo vigente sin revisar todo el repositorio.

## What Changes

- Añadir una configuración opcional basada en archivos para relacionar componentes, documentos canónicos y contexto por rol, reutilizando el inventario y las exclusiones existentes.
- Resolver una selección reproducible de referencias pertinentes, sin copiar documentos ni cargar automáticamente expedientes históricos.
- Incorporar impacto documental previsto en planificación y reconciliación final antes de Sync: actualizar solo lo afectado o justificar su conservación, con revisión semántica independiente.
- Integrar comprobaciones locales pequeñas en handoffs y transiciones existentes. Empezar en modo informativo; habilitar bloqueos objetivos solo mediante promoción expresa. Una recomendación documental no adoptada no impide avanzar.
- Conservar aprobaciones, hashes, intentos, reglas, límites de corrección y evidencia válida; no repetir pruebas por una comprobación documental ni crear pausas nuevas por transferencia.
- Mantener inspección sin efectos y medir el coste local sin imponer una revisión exhaustiva por HU.

## Capabilities

### New Capabilities

- `project-context-lifecycle`: selección, impacto y reconciliación proporcional del contexto vigente de un proyecto consumidor del kit portable.

### Modified Capabilities

Ninguna. Se extienden opcionalmente los contratos existentes sin sustituir los requisitos de `manual-phase-contracts`, `manual-project-rules`, `manual-delivery-traceability` ni `manual-kit-distribution`. La capacidad nueva posee las obligaciones específicas de mantenimiento documental.

## Impact

Fuente actual: `artifacts/crea-manual-kit-0.1.6/`, no `src/harness_local/`. Una implementación futura trabajará sobre un candidato versionado nuevo y preservará las distribuciones publicadas. Afecta configuración/schema del proyecto, handoff/schema, orquestador, perfiles, transiciones, adaptadores de proyección, validación, setup y guías; añade un helper local de contexto y regresiones propias. Sin servicios, nuevas dependencias de runtime ni cambios upstream.

Se coordina con `gestionar-ciclo-vida-pruebas-proyecto`, pero puede implementarse y verificarse sin ese cambio. No incorpora descubrimiento/ciclo de vida de tests, runners remotos, Azure DevOps, hooks, despliegues, publicación ni una reescritura general de la orquestación. Esta propuesta autoriza únicamente planificación: no crea candidato, código, rama, ZIP ni cambios en specs estables.
