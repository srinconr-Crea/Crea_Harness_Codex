# Proposal

## Why

El flujo debe recibir HUs desde una fuente elegida y publicar resultados trazables sin duplicar acciones. No debemos confundir lectura de una historia con autorización para escribir o publicar.

## What Changes

- Definir StoryProvider y GitProvider con adapter local fixture como base y GitHub como primer proveedor remoto; Jira/Linear quedan opcionales por contrato.
- Conectar lectura de historias vía MCP/CLI/API seleccionado y congelar revisión/fuente sanitizada.
- Crear preview del PR y publicación explícitamente autorizada pasando gates del 04/05 y evals del 06.
- Reconciliar push/PR interrumpidos y vincular URL, head/base y evidencias a HU/intento.
- Orden 07. Dependencia de implementación: infraestructura local de 06-observability-and-agent-evals implementada y verificada (439 pruebas, smoke instalado y specs sincronizadas; commits ec84193/54faea5). El usuario autorizó el 2026-10-13 una excepción para iniciar la implementación local de 07 mientras siguen pendientes las tareas 2.4/3.3 de 06.
- La excepción permite desarrollar contratos, lectura de historias, preview y pruebas con dobles. No satisface el criterio de salida de 06 ni aprueba sus 126 evaluaciones Luna/medium; promoción y publicación permanecen bloqueadas hasta pasar los gates del candidato y las evaluaciones requeridas. Implementar el adaptador de escritura no autoriza activarlo contra un proveedor real.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `story-pr-integration`: Adaptadores de lectura de HU y publicación reconciliable con gates.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Adaptadores, configuración de conectores, Skill de cierre y tests con dobles/sandbox GitHub. No merge ni despliegue automáticos ni comentarios a terceros sin autorización.

Recursos de aceptación: [catálogo de pruebas](../../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../../docs/planning/quality/eval-cases.json), [prácticas](../../../../docs/planning/quality/practices.json) y [secuencia](../../../../docs/planning/roadmap.md). Criterio de salida: HU de fuente trazable a PR draft autorizado con evidencia; repetir o reanudar no duplica publicación.
