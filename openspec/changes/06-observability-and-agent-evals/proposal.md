# Proposal

## Why

Necesitamos comparar versiones de roles/modelos con resultados y conocer la actividad por HU. Los catálogos de evals no constituyen evaluaciones ejecutadas y Desktop no garantiza medición exacta de tokens.

## What Changes

- Registrar tiempos, delegaciones, retries, pruebas y ejecuciones remotas por HU/intento/rol.
- Implementar adaptador de uso soportado con campos null cuando no exista medición atribuible.
- Ejecutar casos del 01 contra roles/configuraciones del 02 y herramientas del 05, guardando trazas sanitizadas y métricas.
- Establecer gates de evaluación para cambios en instrucciones, prácticas, herramientas, modelo o esfuerzo.
- Orden 06. Dependencia de implementación: 05-databricks-validation-and-evidence. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `development-observability`: Actividad por HU/rol y consumo observado con procedencia y alcance.
- `agent-evaluation`: Ejecución repetible de evals, scorers y promoción de configuraciones.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Adaptadores de eventos/hooks certificados, almacenamiento externo, runner de evals y reportes; MLflow opcional separado del núcleo. No invoca un motor API para sustituir Desktop sin cambio aprobado.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Evals ejecutados con trazabilidad y gate reproducible; tokens/costos desconocidos se mantienen null con motivo.
