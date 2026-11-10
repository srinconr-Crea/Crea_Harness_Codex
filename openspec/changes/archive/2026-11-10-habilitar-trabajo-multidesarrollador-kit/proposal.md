# Proposal

## Why

El kit portable 0.1.8 permite trabajar por HU con contexto, reglas y pruebas versionados, pero vincula la base de la feature al destino del PR y no ofrece preparación local de otro desarrollador ni una observación vigente de compatibilidad con ese destino. El equipo necesita reutilizar un onboarding compartido desde sesiones independientes de Codex, detectar interferencias entre HUs y conservar sus decisiones humanas de integración.

## What Changes

- Separar `project.base_branch` y el nuevo `delivery.pr_target_branch`, opcional y con fallback al comportamiento anterior; comprobar referencias, SHA, alcance heredado y ramas protegidas.
- Incorporar compatibilidad opt-in frente al destino del PR: diferencias Git, componentes y consumidores, reglas/specs, documentación, catálogo y simulación textual aislada. Informar `compatible`, `requires_review`, `conflict_detected` o `undetermined`, con cobertura y vigencia independientes.
- Revalidar el snapshot del destino antes de crear/preparar el PR, conservando pruebas y aprobaciones no afectadas. No fusionar, rebasar ni actualizar automáticamente features para resolver hallazgos.
- Añadir preparación C para un proyecto ya configurado: entrada en prompt, skill/guía incluidas en el cliente, diagnóstico repetible y binding personal de entorno sin editar la configuración compartida.
- Reutilizar contexto 0.1.7, catálogo/plan/run/gate/lifecycle 0.1.8, handoffs y transiciones. Mantener roles secuenciales por checkout, aprobaciones, límites de corrección y adaptadores inactivos.
- Definir composición de copia y exclusiones desde onboarding; conservar recursos operativos, licencias, procedencia y evidencia requerida. Mantener inicialmente `tests/crea/` y manifest como procedencia; permitir al cliente prescindir del prompt extenso mediante una entrada local equivalente.
- Corregir la documentación operativa desalineada de 0.1.8 mediante una fe de erratas y el candidato nuevo; preservar los bytes de las distribuciones históricas. Destino de trabajo propuesto: un único candidato 0.1.9, no publicado.
- Entregar todo como **un solo cambio OpenSpec**, organizado en incrementos internos verificables. Esta propuesta autoriza únicamente artefactos de planificación.

## Capabilities

### New Capabilities

- `developer-local-preparation`: preparación de una persona sobre un checkout configurado, entorno personal limitado y lecturas de comprobación sin repetir onboarding.
- `hu-target-compatibility`: observación proporcional de compatibilidad de una HU con el destino real del PR, con hallazgos, límites, vigencia y acciones humanas.

### Modified Capabilities

- `manual-delivery-traceability`: origen y destino independientes, procedencia Git y alcance real de entrega con autorizaciones existentes.
- `manual-phase-contracts`: consumo de compatibilidad desde handoffs/transiciones sin vetos nuevos por divergencia ni invalidación indiscriminada.
- `project-context-lifecycle`: uso del mapa existente para impacto entre ramas y consumidores sin duplicar contexto ni activar la extensión.
- `project-testing-lifecycle`: binding local de intérprete y propuestas de revalidación por cambios del destino, preservando el catálogo y la identidad de cada plan.
- `manual-kit-distribution`: candidato derivado de 0.1.8, documentación A/B/C coherente, composición cliente y exclusiones incorporadas.

## Impact

La implementación afectará un staging nuevo `artifacts/crea-manual-kit-0.1.9/`: AGENTS, orquestador, configuración/schemas, entrega y plantillas, scripts de contexto/transiciones/testing, preparación local, guías y `.gitignore`. Añadirá helpers acotados, schemas de entorno/snapshot/informe/composición, fixtures Git y pruebas de regresión; un empaquetador nuevo preservará árboles, ZIP y hashes previos.

Se conservan Azure DevOps CLI, los mecanismos Git/GCM y los recursos Databricks AI Tools con sus licencias/procedencia. No se instala `harness_local` en el cliente ni se añade un orquestador central, catálogo alternativo, framework de pruebas o servicio. No se habilitan merge, auto-complete, deploy, promociones a `test`, pipelines, escrituras Boards o capacidades remotas inactivas.

La configuración anterior sigue funcionando sin las opciones nuevas. La adopción exige schemas y consumidores compatibles en conjunto; no migra HU, planes ni recibos históricos. Las modificaciones funcionales requieren una solicitud posterior de Apply; esta fase no publica ni modifica el kit.
