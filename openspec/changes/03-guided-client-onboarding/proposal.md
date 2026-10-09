# Proposal

## Why

El CLI actual exige conocer flags y preparar archivos previamente. Una persona nueva necesita un asistente que descubra datos, pregunte lo faltante y entregue un plan concreto de preparación e integración.

## What Changes

- Crear Skill harness-client-onboarding que acepte entrevista o archivo/plantilla y solicite únicamente decisiones faltantes.
- Añadir configuración de contexto técnico/negocio, selección de roles/herramientas y plan de validación en contratos separados del descriptor v1.
- Orquestar diagnóstico, preparación e integración Desktop del 02 como etapas registradas con recuperación; reutilizar init solo cuando sea aplicable y usar un contrato compuesto nuevo para instrucciones personalizadas, sin relajar init v1.
- Emitir informe de onboarding que distinga archivos preparados, preparación supervisada aceptada, Desktop certificado y conectividad remota pendiente, conservando limitaciones y bloqueos por capacidad.
- Orden 03. Dependencia de implementación: 02-desktop-roles-and-tool-contracts. Debe estar implementada y verificada para preparación supervisada, con aceptación explícita de límites y evidencia, antes de aplicar este incremento. No exige certificación estricta completa para preparar onboarding; la existencia de artefactos o una planificación actualizada no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `guided-client-onboarding`: Asistente y plantillas de configuración con descubrimiento, revisión y aplicación explícita.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Skill, nuevos contratos ClientDevelopmentConfig y ClientToolBinding, plantillas, asistente CLI opcional y journal de etapas. No agrega campos desconocidos a descriptor/policy/binding v1.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Una persona nueva completa el flujo con plantilla o entrevista y recibe configuración trazable sin ampliar permisos por inferencia.
