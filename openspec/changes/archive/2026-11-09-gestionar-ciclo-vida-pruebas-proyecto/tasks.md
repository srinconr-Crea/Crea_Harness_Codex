# Tasks

Las tareas completas están respaldadas por la evidencia local de implementación y revisión. Los roles indican responsabilidad dentro de las fases existentes, no un despacho o aprobación por casilla. Developer escribe regresiones y diagnósticos focalizados; Tester conserva la ejecución oficial. Implementar solo en candidato versionado nuevo, preservando 0.1.6 y fuentes históricas.

## 1. Contratos y descubrimiento sin ejecución

- [x] 1.1 Principal: registrar baseline/versionado vigente y preparar candidato nuevo independiente o combinado con contexto; verificar hashes históricos y que ninguna modificación exige instalar el motor Python histórico.
- [x] 1.2 Developer: extender policy/schema y configuración con lifecycle, ubicaciones y metadata active/retired opcionales; añadir fixtures de catálogo legacy, IDs inválidos y referencias históricas; verificar validación y documentar cómo declarar suites propias.
- [x] 1.3 Developer: implementar catalog.py/discover y su entrada CLI antes de setup_complete, sin importar código ni ejecutar colección; verificar casos con suite existente, conftest con efectos, configuración no soportada, enlaces y superficie excluida en test_catalog.py.
- [x] 1.4 Developer: documentar descubrimiento parcial, pruebas del kit/cliente/evals y conservar las estructuras propias; verificar ejemplos de onboarding sin writes ni comandos cliente y sin afirmar resultados ejecutados.
- [x] 1.5 Tester: ejecutar fixtures de descubrimiento y compatibilidad; conservar evidencia de cero imports/subprocess de suites, ausencia de cambios sin --out y rechazo de colisiones/traversal.

## 2. Mínimo técnico y mantenimiento del catálogo

- [x] 2.1 Developer: preparar plantilla técnica condicional y resolución de aplicabilidad para documental/configuración, Python, SQL y notebooks; verificar casos sin tests, con suite equivalente y sin herramienta necesaria, sin negocio inventado ni runtime inferido por extensión; documentar su materialización opcional en setup.
- [x] 2.2 Developer: implementar reconcile sobre Git completo y pruebas afectadas, con altas/modificaciones/movimientos/bajas y asociaciones por patrones aprobados; verificar que una prueba nueva no asociada queda visible y que no se releen cuerpos de suites ajenas al impacto.
- [x] 2.3 Developer: ampliar selección por criterios declarados conservando unión/rutas desconocidas/input dependencies; verificar criterio que selecciona test intacto, fixture/lock modificado, rename y criterio sin oráculo; actualizar referencias de crea-pruebas sin tocar upstream.
- [x] 2.4 Developer: implementar disposición de retiro/sustitución y reconciliación de rules/inputs/required_checks/assertions; verificar que desactivar una requerida no la convierte en passed y conservar la definición/decisión histórica; documentar quién puede revisar el retiro.
- [x] 2.5 Tester: ejecutar casos de baseline, selección y mantenimiento, incluyendo runtime requerido inactivo; conservar recibos con límites de sintaxis/negocio/runtime y sin instalar herramientas ni operar remoto.

## 3. Outputs por HU e intento desde configuración permanente

- [x] 3.1 Developer: extender schema de execution/plan y resolución de attempt_templates con variables/posiciones permitidas, argv concretos y digests de origen/resolución; verificar igualdad determinista, segunda HU sin editar configuración y rechazo de variables arbitrarias, traversal y shell evaluado.
- [x] 3.2 Developer: integrar plan/run/gate con reconstrucción de settings resueltos y mantener rama legacy exacta; verificar outputs nuevos exclusivos, destino ocupado, colisiones con inputs/evidencia primaria, enlaces y cambio real de política; documentar invocaciones y revisión de digest.
- [x] 3.3 Tester: ejecutar dos HU/intentos sintéticos con la misma configuración permanente; conservar evidencia de hashes estables de policy/execution, planes distintos y preservación de intentos, sin reutilizar recibos entre planes.

## 4. Inclusión observada y recibos

- [x] 4.1 Developer: implementar plugin pytest explícito y schema de inventario de colección/ejecución, sin nueva instalación global; verificar fixtures reales de parametrización, deselección, ejecución, skip, fallo y error de colección con rutas/IDs contrastables; documentar el nivel de cobertura acreditable.
- [x] 4.2 Developer: integrar parser/recibos/gate y gramática exacta de inventory-<check>.json; verificar requerida fuera del comando, caso del mismo archivo que no basta, reporte alterado/ajeno y plan/gate sin subprocess, conservando los controles JUnit y TTL.
- [x] 4.3 Tester: ejecutar el recorrido plan/run/gate con plugin y filtros parciales revisados; conservar evidencia de ausencia requerida bloqueante y de gate favorable sin repetir la suite, diferenciando inventario informativo de obligación técnica.

## 5. Roles, transiciones y adopción proporcional

- [x] 5.1 Developer: integrar revisión del inventario en handoff/procedencia/adapter_digest y las dos condiciones opcionales de transición; verificar informative sin veto nuevo, promoción por ID, error de dependencia y persistencia de gates previos; documentar códigos distintos de inspección y plan/run/gate.
- [x] 5.2 Developer: actualizar orquestador, perfiles, setup y guía de pruebas con ubicación/declaración/selección/verificación y retiro; verificar tareas por rol, ausencia de pausas adicionales y aislamiento de escritura Tester/Reviewer mediante fixtures actuales.
- [x] 5.3 Developer: adaptar validador original/personalizado y guía de migración/reversión conjunta; verificar configuración legacy, cliente personalizado y adopción sin gestión de contexto, sin migrar intentos/recibos ni habilitar capacidades inactivas.
- [x] 5.4 Tester: verificar reanudación, referencia corregida sin nueva suite y cambios funcionales que invalidan; conservar pruebas de max_fix_rounds global y de ejecución limitada al impacto, sin afirmar reutilización entre planes.

## 6. Verificación integrada y distribución local

- [x] 6.1 Developer: adaptar o crear empaquetador del candidato nuevo con regresiones de preservación, plugin y plantilla incluidos; verificar rechazo de destinos históricos, equivalencia árbol-ZIP e inventario/manifiesto, sin publicar.
- [x] 6.2 Tester: ejecutar integración focalizada de contratos, selección, outputs, inclusión, transiciones y empaquetado; entregar recibos, lecturas/procesos y tiempos observados, sin barrido histórico completo salvo causa nueva justificada ni promesa universal de duración.
- [x] 6.3 Reviewer: contrastar project-testing-lifecycle con código, guías, escenarios y evidencia; ejecutar gate sin run y OpenSpec verify, registrar hallazgos o revisión favorable y comprobar que no se promovieron condiciones ni activaron capacidades por defecto.

## Workflow follow-up

- Sync se realiza por Reviewer solo tras verificación favorable, presentando su diff y conservando la invalidación cuando cambia una entrada funcional.
- Archive exige autorización humana aplicable; commit/push/PR requieren además su alcance y destino autorizados. No se autoriza publicación, instalación ni despliegue mediante esta propuesta.
- El cambio de contexto puede aplicarse primero por conveniencia, pero no es prerrequisito de este incremento. Si ambos comparten candidato, verificar cada capacidad y los campos combinados antes de empaquetar.
