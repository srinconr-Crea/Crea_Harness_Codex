# Proposal

## Why

Un candidato local y una revisión LLM no demuestran ejecución correcta en Spark o Databricks. Debemos exigir pruebas adecuadas al cambio y vincular sus resultados al candidato exacto.

## What Changes

- Resolver ValidationPlan por tipo/impacto y prácticas del 01 para SQL, Python, notebooks, PySpark, YAML y CI/CD.
- Implementar adaptadores de comprobación estática, unit tests aislados y sandbox remoto sintético autorizado.
- Registrar resultados passed/failed/blocked/not_run con candidato, runtime, datos y comando efectivos.
- Reconciliar ejecuciones remotas interrumpidas y comprobar identidad/hash de resultados antes del gate.
- Orden 05. Dependencia de implementación: 04-hu-lifecycle-and-development-gates. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `candidate-validation`: Validación por tecnología, ejecución sintética aislada y evidencia con identidad/hash.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Adaptadores locales/Databricks, schemas de evidencias, scripts/fixtures sintéticos y tests de contrato. No ejecuta recursos productivos ni despliega bundle cliente automáticamente.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Evidencia determinista y remota genuina donde se exige, ligada al candidato; sin credenciales o runtime disponibles se registra bloqueo.
