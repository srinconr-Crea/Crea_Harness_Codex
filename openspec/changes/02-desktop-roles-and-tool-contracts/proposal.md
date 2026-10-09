# Proposal

## Why

Los archivos creados hoy no activan roles ni prueban su descubrimiento en Desktop. Necesitamos configurar y verificar la superficie real antes de ofrecer onboarding completo.

## What Changes

- Crear plantillas para principal, analyst/enrich-HU, impact-analyzer, planner, developer, tester, auditor y verifier.
- Crear Skill harness-hu como punto de entrada inicial y contratos de delegación; la coordinación completa llega en 04.
- Diseñar integración revisable de AGENTS.md, .codex/config.toml y .codex/agents/*.toml, preservando personalizaciones y preferencias globales.
- Configurar matriz rol/Skill/MCP/CLI/modelo/esfuerzo y comprobar ejecución en Desktop mediante casos sintéticos del 01.
- Separar preparación supervisada y certificación estricta. Con aceptación explícita del operador, permitir preparación con limitaciones observadas; conservar conflict/unsupported/not_checked y certified=false donde corresponda.
- Registrar identidad y contenido del candidato antes/después de revisión supervisada; detectar drift y bloquear aceptación, sin prometer impedir escritura.
- Orden 02. Dependencia de implementación: 01-quality-practices-and-eval-foundation. Debe estar implementada y verificada antes de aplicar este incremento; la existencia de sus artefactos no satisface esa dependencia.
- Esta propuesta define capacidades futuras; crear sus artefactos no instala, implementa ni autoriza efectos remotos.

## Capabilities

### New Capabilities

- `desktop-integration`: Preparación reversible y certificación de capacidades en la aplicación objetivo.
- `role-tool-catalog`: Roles, modelos, esfuerzos y herramientas requeridas/opcionales versionados.

### Modified Capabilities

Ninguna. Conserva contratos y comportamiento v1; las nuevas operaciones tienen contratos separados.

## Impact

Futuros agent_templates/, skills/, adaptador de configuración Desktop y certificaciones externas por versión. init v1 y configuración global permanecen intactos.

Recursos de aceptación: [catálogo de pruebas](../../../docs/planning/quality/test-cases.json), [catálogo de evals](../../../docs/planning/quality/eval-cases.json), [prácticas](../../../docs/planning/quality/practices.json) y [secuencia](../../../docs/planning/roadmap.md). Criterio de salida: Preparación supervisada implementada y verificada, matriz de capacidades observadas y limitaciones aceptadas explícitamente, y evidencia de evals con anotación humana; la certificación estricta se informa por separado y no es requisito para preparar onboarding. Archivos presentes nunca equivalen a certificación.
