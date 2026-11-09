# Tasks

Estado de tareas verificado; las casillas completas corresponden a evidencia local. Los roles indican responsabilidad, no obligan a un despacho o aprobación por casilla. Developer escribe código y regresiones; sus diagnósticos no sustituyen recibos Tester. Usar la fuente versionada nueva definida en design.md; nunca modificar 0.1.6 para implementar este cambio.

## 1. Contratos opcionales y preservación

- [x] 1.1 Principal: registrar baseline de la fuente portable realmente vigente y preparar candidato versionado nuevo; verificar hashes de árboles/ZIP históricos y ausencia de cambios en el motor histórico.
- [x] 1.2 Developer: extender configuración y schemas con mapa de componentes, impacto, selección lógica y observaciones por fase; añadir casos legacy, documentos pendientes, campos inválidos y ausencia de hashes futuros; verificar fixtures válidos/inválidos y documentar campos en la guía de configuración.
- [x] 1.3 Developer: añadir las dos condiciones opcionales a los enums/consumidores y mantener informative sin promoción inicial; verificar mediante casos de extensión ausente y condiciones no promovidas, documentando qué no bloquea.

## 2. Selección e impacto proporcionales

- [x] 2.1 Developer: implementar select/impact en contexto.py sobre Git/rutas seguras existentes con orden estable, deduplicación, dependencias declaradas y motivos; verificar casos de mismo input, ciclo, componente nuevo, rename/delete y documentación conservada con justificación en test_contexto.py.
- [x] 2.2 Developer: aplicar exclusiones y límites de lectura sin filtrar el diff Git; verificar que credenciales, enlaces, rutas externas y documentos no relacionados no se leen, que un exceso queda parcial y que no se pierde detección de cambios excluidos.
- [x] 2.3 Developer: documentar invocaciones y responsabilidades canónicas junto al helper; verificar ejemplos resueltos en fixtures y corregir la plantilla de contexto únicamente en la nueva distribución.
- [x] 2.4 Tester: ejecutar los casos de esta sección con conteo de lecturas, bytes y procesos; conservar recibos que demuestren cero suites/remoto desde inspección y ausencia de lectura de contenido ajeno, sin afirmar un tiempo universal.

## 3. Handoffs, vigencia y transiciones

- [x] 3.1 Developer: integrar impacto previsto/final en contrato y render existente, con observaciones iniciales distintas de referencias actuales; verificar conservación de contenido manual, intentos, predecesores y ausencia de resultados futuros en planificación; actualizar la plantilla de handoff.
- [x] 3.2 Developer: integrar check y condiciones en transiciones/consume sin nuevos vetos informativos; verificar omisión editorial, condición promovida, error de dependencia y bloqueo técnico previo, documentando códigos 0/2/3/4.
- [x] 3.3 Developer: extender proyección, procedencia, adapter_digest y validación solo cuando se adopte la extensión; verificar historia congelada, edición documental prevista, cambio funcional posterior, referencia corregida, movimiento Archive y target funcional de Sync sin exclusiones amplias.
- [x] 3.4 Tester: ejecutar regresiones de contrato/transiciones/content-v2 pertinentes y los casos nuevos; conservar evidencia de reanudación sin reiniciar rondas ni relanzar suites válidas por corregir enlaces.

## 4. Integración de roles y adopción

- [x] 4.1 Developer: integrar selección por fase, impacto en Propose y reconciliación antes del plan final/Sync en orquestador y cuatro perfiles, preservando upstream; verificar fixtures de read_paths/write_paths y tareas por rol, sin nuevas pausas de aprobación ni delegaciones simuladas.
- [x] 4.2 Developer: actualizar setup, guías, validación del kit y plantillas para adopción opcional y reversión conjunta; verificar diff de un cliente personalizado y que config/schema/herramientas nuevos se adoptan juntos, sin migración de HU históricas.
- [x] 4.3 Tester: verificar recorridos sintéticos documental, movimiento Python y Silver/Spark con runtime inactivo requerido; conservar evidencia de decisiones de impacto y de blocked remoto sin ejecutar recursos externos ni afirmar piloto real.

## 5. Verificación integrada y entrega local

- [x] 5.1 Developer: adaptar o crear empaquetador exclusivo del candidato nuevo y pruebas de preservación/árbol-ZIP; verificar que rechaza destinos históricos y documentar versión/baseline sin publicar.
- [x] 5.2 Tester: ejecutar regresión integrada focalizada, validación original/personalizada y empaquetado del candidato; entregar recibos y límites, sin repetir la suite histórica completa salvo causa nueva justificada.
- [x] 5.3 Reviewer: contrastar criterios de project-context-lifecycle con código, configuración, documentación y recibos; ejecutar gate sin run y OpenSpec verify, dejando hallazgos concretos o revisión favorable y comprobando que no se activaron condiciones por defecto.

## Workflow follow-up

- Tras verificación favorable, Reviewer realiza Sync según el flujo vigente y presenta su diff; no hacerlo como efecto de completar esta planificación.
- Archive requiere autorización humana aplicable al expediente/candidato. Principal realiza commit/push/PR únicamente si se autorizan además esas acciones y destino; este cambio no autoriza publicación ni despliegue.
- El cambio de ciclo de vida de pruebas puede aplicarse después por conveniencia, sin ser una dependencia necesaria de esta capacidad.
