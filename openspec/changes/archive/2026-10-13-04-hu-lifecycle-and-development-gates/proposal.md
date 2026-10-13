# Proposal

## Why

Skills aisladas no conservan por sí mismas el alcance, aprobación o candidato probado de una HU. Necesitamos un flujo persistido que vincule trabajo de roles con decisiones y evidencia.

## What Changes

- Completar harness-hu con explore, enrich, impacto, propose/update, aprobación, apply, test, audit/verify y cierre.
- Registrar story/run/attempt/revision, manifiesto, aprobación y hashes en estado externo por cliente/checkout.
- Crear gates deterministas de alcance, aprobación vigente y evidencia para operaciones del harness.
- Introducir límites de delegación, correcciones y exclusión de escritores; preparación de publicación sin efectos remotos.
- Orden 04. Dependencia de implementación: 03-guided-client-onboarding. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `hu-lifecycle`: Estado por HU/intento, aprobación de plan y gates de candidato con recuperación.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Nuevos modelos y comandos de HU en harness_core/local, Skills del 02, SQLite/JSON de negocio y tests de transición. El journal de onboarding conserva su formato.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Cada transición queda registrada y los gates rechazan alcance, aprobación o evidencia incorrectos; no se publican cambios todavía.
