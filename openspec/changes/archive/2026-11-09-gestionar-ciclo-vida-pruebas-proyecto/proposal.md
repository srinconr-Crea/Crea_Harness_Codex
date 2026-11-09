# Proposal

## Why

El kit portable 0.1.6 ya selecciona y ejecuta checks locales con Git completo, JUnit, recibos y gates, pero no reconcilia de forma explícita las pruebas existentes, nuevas o retiradas con ese catálogo. El desarrollador necesita configurar ubicaciones y convenciones una vez, y que cada HU mantenga las pruebas aplicables sin editar manualmente todas las rutas de evidencia ni ejecutar baterías completas por rutina.

## What Changes

- Descubrir suites/configuración local durante onboarding sin ejecutar ni importar código; registrar su cobertura en el catálogo único existente y conservar estructuras propias.
- Definir un mínimo técnico aplicable por tecnología, sin inventar pruebas de negocio ni confundir tests del kit, tests del cliente y evals de agentes.
- Registrar ubicaciones, asociación suite/archivo-check y decisiones de mantenimiento; detectar pruebas nuevas, modificadas, movidas o potencialmente obsoletas antes del plan final.
- Reutilizar reglas de rutas e inputs; añadir selección explícita por criterios declarados y comprobar que las pruebas esperadas entran en la ejecución, sin un grafo semántico automático.
- Resolver argv y outputs exactos por HU/intento desde convenciones revisadas, congelándolos en el plan, sin reescribir la configuración permanente ni habilitar shell libre.
- Mantener plan/run/gate, recibos, assertions, TTL, intentos y límites actuales. Los controles de inventario nuevos empiezan informativos, con promoción expresa por condición; los gates técnicos previos mantienen su efecto.

## Capabilities

### New Capabilities

- `project-testing-lifecycle`: descubrimiento, registro, mantenimiento y reconciliación de pruebas del proyecto, con ejecución por HU sobre el framework portable existente.

### Modified Capabilities

Ninguna. `candidate-validation` y `evaluation-catalog` conservan sus contratos históricos; no se trasladan sus workers al kit. Las obligaciones de `manual-phase-contracts` y distribución siguen vigentes. La capacidad nueva posee la extensión opcional del catálogo y su preparación por HU.

## Impact

Fuente actual: `artifacts/crea-manual-kit-0.1.6/`; desarrollo futuro en candidato nuevo. Afecta skill Crea de pruebas, policy/execution y schemas, CLI/adaptadores actuales, handoff, transiciones, onboarding, perfiles, guías, validación y regresiones del kit. Añade un módulo local de catálogo y una plantilla técnica de pytest solo para proyectos sin equivalente aplicable; sin nuevo framework ni instalación implícita.

Puede implementarse y verificarse sin `gestionar-contexto-evolutivo-proyecto`; si ambos se adoptan, comparten referencias y combinan sus campos opcionales. No incluye runtime/Spark remoto, SAST, mutation, evals, CI, reutilización entre planes, Azure DevOps, hooks, despliegues ni publicación. Esta propuesta crea solo artefactos de planificación; no cambia código, configuración operativa, specs estables, ramas ni distribuciones.
