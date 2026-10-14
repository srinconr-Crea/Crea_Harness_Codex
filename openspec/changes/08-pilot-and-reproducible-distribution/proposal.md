# Proposal

## Why

El producto solo cumple su objetivo cuando una persona nueva puede instalarlo, preparar un cliente y completar una HU con evidencia. Necesitamos demostrarlo y poder actualizar sin perder personalizaciones.

## What Changes

- Ejecutar piloto Windows en dos clientes sintéticos, seguido de copia NaturaPet con HU sintética y restricciones propias.
- Entregar instalador/launcher que prepara dependencias revisadas y expone onboarding guiado; login/confianza siguen siendo pasos visibles.
- Distribuir Skills/roles/recursos mediante paquete versionado y plugin opcional solo donde esté certificado.
- Implementar update preview/apply/recover con manifiesto de ownership, backups y conflictos de personalización.
- Orden 08. Por autorización del usuario del 2026-10-13, se permite implementar y probar localmente el código de este incremento sobre la base implementada de 07, aunque su aceptación remota siga pendiente. La certificación, el release y la habilitación del siguiente incremento requieren cerrar y verificar las dependencias de 06/07.
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

## Desarrollo anticipado autorizado

La base local de 07 está implementada y probada; su archivo con pendientes no certifica aceptación. Continúan pendientes las 144 evaluaciones reales de 06/07, la verificación del sandbox compatible de Local-Harness y el recorrido de publicación/reanudación con sus gates. El piloto NaturaPet HU-BRONZE-001 pasó 25 tests remotos y produjo un PR draft autorizado mediante Git/Codex; no sustituye esos protocolos ([evidencia](../../../docs/evidence/naturapet-hu-bronze-001-pilot.md)).

Esta revisión permite completar contratos, empaquetado candidato, bootstrap/launcher, update/recover, pruebas locales y preparación de protocolos. No concede instalación global, despliegue, efectos remotos ni publicación de producto. Código terminado con aceptación pendiente conserva estado explícito sin certificar, gate de release bloqueado y tareas remotas abiertas; el criterio de salida completo se mantiene.
