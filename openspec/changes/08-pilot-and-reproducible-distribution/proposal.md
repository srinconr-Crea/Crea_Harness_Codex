# Proposal

## Why

El producto solo cumple su objetivo cuando una persona nueva puede instalarlo, preparar un cliente y completar una HU con evidencia. Necesitamos demostrarlo y poder actualizar sin perder personalizaciones.

## What Changes

- Ejecutar piloto Windows en dos clientes sintéticos, seguido de copia NaturaPet con HU sintética y restricciones propias.
- Entregar instalador/launcher que prepara dependencias revisadas y expone onboarding guiado; login/confianza siguen siendo pasos visibles.
- Distribuir Skills/roles/recursos mediante paquete versionado y plugin opcional solo donde esté certificado.
- Implementar update preview/apply/recover con manifiesto de ownership, backups y conflictos de personalización.
- Orden 08. Dependencia de implementación: 07-story-and-pr-integrations. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `pilot-certification`: Aceptación end-to-end en Desktop con dos clientes y HU sintética.
- `harness-distribution`: Instalación/versionado/update/recover preservando configuración.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

installer/, distribución opcional plugin, wheel/lock, update, manual de nuevo desarrollador y evidencias de aceptación; no configura recursos reales NaturaPet.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Usuario nuevo completa onboarding y HU en Desktop, dos clientes permanecen aislados y update/recover preserva personalizaciones.
