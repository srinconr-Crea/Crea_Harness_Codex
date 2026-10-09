# Proposal

## Why

El onboarding actual no entrega una base común de calidad ni casos que permitan comprobar los roles. Antes de distribuir agentes necesitamos reglas trazables, fixtures sintéticos y criterios de aceptación independientes del cliente.

## What Changes

- Empaquetar un catálogo de prácticas SQL, Python, notebooks, PySpark, YAML/DABs y CI/CD con IDs, aplicabilidad y evidencias.
- Incorporar nueve Skills oficiales fijadas por commit y hashes como dependencia Databricks opcional, conservando licencia y referencias.
- Formalizar los catálogos de pruebas y evals preparados en docs/planning/quality; distinguir diseño de ejecución.
- Definir extensiones del cliente y cambios de reglas revisables, sin editar las copias upstream.
- Orden 01. Dependencia de implementación: Base implementada: bootstrap-codex-local-core y apply-client-onboarding. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `development-practice-pack`: Buenas prácticas versionadas por tecnología con procedencia y extensiones del cliente.
- `evaluation-catalog`: Casos sintéticos y rúbricas separados de resultados y ejecutores.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

resources/vendor/, futuros recursos de calidad del paquete, schemas, tests de recursos y documentación. No instala Skills ni ejecuta LLM o Databricks.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Catálogos cargables, íntegros y trazables; ningún recurso activa herramientas o produce resultados ficticios.
