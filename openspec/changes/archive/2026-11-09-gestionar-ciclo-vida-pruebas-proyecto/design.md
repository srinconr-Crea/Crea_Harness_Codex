# Design

## Context

Ver `proposal.md` para la motivación. Baseline inspeccionada: HEAD `13a2e1e`, kit portable 0.1.6. Sus artefactos son la fuente cliente; `src/harness_local/validation*.py` contiene capacidades históricas que no se instalan con este kit. Esta extensión altera contratos, ejecución e integración y requiere diseño explícito.

| Evidencia del kit actual | Comportamiento que se conserva |
| --- | --- |
| `crea-pruebas/scripts/contract.py:build_plan` | Unión por rutas, inputs y checks fijos; unknown, missing y criterios sin check bloquean. |
| `scripts/crea/testing/workflow.py` | Plan final, huellas, entorno, ejecución pytest/local/local_execution y gate independiente. |
| `testing/{git_adapter,execution,reports,schemas}.py` | Git completo, argv sin shell, entorno mínimo, JUnit/coverage y schema estricto. |
| `docs/pruebas/policy.json`, `execution.json` | Catálogo vacío de fábrica; configuración revisada y outputs exactos. No materializa rutas por HU/intento. |
| `docs/pruebas/capabilities.json` | Runtime/Spark/SAST/mutation/evals/CI/reutilización entre planes inactivos. |
| Tests `test_contract`, `test_testing_adapters`, `test_content_v2`, `test_transiciones` | Regresiones existentes de selección, evidencia, vigencia, roles y publicación. |

El onboarding solicita completar catálogo y pruebas existentes, sin inventario reconciliable del ciclo de vida. Algunas referencias de crea-pruebas todavía llaman pendientes a adaptadores locales ya implementados: se alinearán sus límites sin reescribir el framework.

## Goals / Non-Goals

**Goals:** configurar ubicación, ejecutores y outputs una vez; mantener catálogo por impacto; demostrar inclusión de pruebas requeridas; conservar suites propias; soportar proyectos nuevos con mínimo técnico honesto.

**Non-Goals:** descubrir automáticamente todo consumidor dinámico, ejecutar un nuevo framework, reemplazar suites, instalar dependencias, acreditar runtime remoto o reutilizar recibos entre planes. No se ejecuta colección dentro de plan/discover. No se agrega CI, runner SQL directo o adaptador Spark/Databricks. No se exige la implementación del cambio de contexto.

## Decisions

### 1. Un catálogo con metadata opcional

Extender `policy.schema.json` con un bloque opcional `lifecycle`, versionado, que contenga convenciones `locations` y `test_inventory`. Los comandos permanecen exclusivamente en `checks[].argv`; `validation.required_checks` sigue siendo una lista de IDs. `locations` distingue tests y fixtures; conserva nombres y directorios reales del cliente. No obliga a adoptar `tests/` si ya usa otra estructura.

Registrar suites o archivos con ID, ruta/patrón, `check_ids`, propósito, procedencia y estado `active|retired`. Las parametrizaciones siguen en assertions/observación de ejecución, no en miles de filas permanentes. Una fila active debe resolver checks activos; una retired conserva IDs históricos como tales, definición/digest anterior y referencia de decisión, sin participar en selección ni fingir que el archivo debe existir. Las definiciones ejecutables activas siguen solo en checks.

El componente de impacto se obtiene de inputs/reglas existentes; si está instalado el cambio A se pueden referenciar sus IDs, sin duplicar su mapa ni exigirlo. Dependencias consumidas por un check deben estar en inputs (código, imports revisados, fixtures, locks, configuración); relaciones textuales observadas son sugerencias hasta revisión, no grafo acreditado.

Alternativas descartadas: un catalogo.json adicional duplica comandos y referencias; registrar cada caso dinámico permanentemente introduce mantenimiento innecesario; reconstruir el runner o activar el motor histórico añade otra autoridad de ejecución.

### 2. Descubrir estáticamente y ejecutar solo desde Tester

Nuevo módulo `scripts/crea/testing/catalog.py`, expuesto por acciones `discover` y `reconcile` de la CLI existente. `discover` debe poder operar antes de setup_complete; no desbloquea plan/run por ello. Entradas: checkout y ubicaciones/configuración revisadas; al inicio, metadata Git y archivos de configuración conocidos permiten sugerir directorios, sin leer todos los cuerpos del repositorio.

En onboarding se hace inventario completo de las ubicaciones de tests. Por HU se inspeccionan solo paths cambiados y checks/dependencias seleccionados; no se vuelve a auditar todo el proyecto. Conservar rutas, hashes de configuración, procedencia y limitaciones; ni importar conftest ni ejecutar pytest --collect-only. Detectar configuraciones no soportadas como parciales. Excluir dependencias instaladas, upstream/kit, archivos sensibles y enlaces; el diff completo y los gates no se filtran por esas exclusiones.

Resultados propuestos `discovered|registered|unregistered|changed|moved|missing|retirement_candidate|unsupported`, ordenados con motivos. Son observaciones, no decisiones de negocio ni resultados passed. Ausencia de ejecución no se convierte en no-aplica. APIs/formatos de otras suites pueden descubrirse como metadata, pero la ejecución requerida sin adaptador soportado sigue blocked; se conserva el ejecutor del cliente sin instalar otro como sustitución implícita.

### 3. Mínimo técnico según aplicabilidad

| Tecnología observada | Propuesta técnica inicial | Límite |
| --- | --- | --- |
| Markdown/configuración | Referencias, JSON/YAML/TOML y schemas presentes, inventario pertinente | No prueba comportamiento de negocio. |
| Python | Sintaxis sin importación y suites existentes aplicables | Funciones/nuevos criterios requieren oráculos reales. |
| SQL | Parser/dialecto si ya existe herramienta revisada; contratos declarados | No acredita semántica SQL/Delta. Herramienta requerida ausente queda pendiente. |
| Notebooks/DABs | Formato, outputs/confidencialidad y configuración local aplicable | No declara bundle validate remoto ni ejecución de notebook. |
| Spark/Databricks | Plan separa estático/Python y necesidad de runtime por comportamiento | Adaptador inactivo requerido conserva blocked; sin recursos nuevos. |

Si no hay equivalente en la suite del cliente, ofrecer una plantilla pytest técnica en assets de crea-pruebas; se materializa durante setup autorizado en una ubicación revisada (por defecto `tests/proyecto/test_validaciones_tecnicas.py`). Solo incluye comprobaciones aplicables a archivos realmente presentes. La plantilla usa herramientas ya preparadas; si faltan, registra pendiente sin instalar. No emite tests vacíos, assertions triviales ni negocio supuesto. No se ejecutan automáticamente `tests/crea/` como batería de negocio por HU.

Las extensiones de la tabla son requisitos condicionales. Un proyecto existente conserva checks equivalentes; no añade suites duplicadas. `failure-modes.json` recibe solo riesgos/esperados reales del proyecto o HU, sin copiar ejemplos como reglas aprobadas.

### 4. Reconciliar altas, cambios y retiro antes del plan final

Planner identifica pruebas esperadas a partir de criterios y consumidores. Developer implementa tests/regresiones previstos y declara altas, cambios y candidatas a retiro. Principal contrasta declaración, Git completo y catálogo; informa discrepancias antes de generar el plan final. Reviewer valida oráculos y retiradas. Ningún rol cambia expectativas para aprobar su resultado.

Mantener unión determinista actual y añadir motivo `declared-required-criterion` para checks con `criteria` que correspondan a criterios requeridos de la HU. Esa relación usa IDs estables revisados; encontrar texto parecido no selecciona ni acredita un caso. Las rutas desconocidas siguen bloqueando por el contrato previo aunque se encuentre un input coincidente. No se ejecutan todos los checks porque sean del mismo lenguaje.

Para los tests nuevos bajo un patrón ya aprobado, el principal genera la observación del intento sin pedir al desarrollador editar manualmente todas las filas. Una asociación nueva, un comando o un cambio de política sí requiere revisión; no se autorregistra como decisión aprobada. Un criterio sin oráculo ejecutable se eleva para decisión de política antes de Apply, sin inventar un check que pase.

El retiro registra fuente, causa y sustitución o conservación, más decisión referenciada. Reconciliar rules, inputs, criterios, required_checks y assertion_tests; los checks que ya no aplican se retiran del catálogo activo con definición histórica enlazada en la fila retired. `configured=false` de un check requerido sigue bloqueando. La obsolescencia semántica la decide la revisión de alcance, no un grep vacío.

### 5. Observar qué pytest recogió y ejecutó

Los contadores y classname de JUnit no siempre identifican por sí solos archivos; no se deduce ejecución desde argv. Añadir un plugin pequeño `scripts/crea/testing/pytest_inventory.py`, cargado explícitamente con el pytest ya usado. Es un adaptador de evidencia, no otro framework ni una instalación global. Se invoca solo en ejecución Tester; no durante discover/plan/gate.

El plugin produce un JSON estructurado por check con nodeid, ruta relativa normalizada y estado: recogido, deseleccionado, ejecutado, omitido/fallido cuando corresponda; captura la colección antes de filtros y la ejecución del mismo proceso. Guarda versión/identidad del formato y datos de error de colección, sin copiar código ni valores sensibles. Una ejecución incompleta no se rellena con resultados supuestos.

El plan congela por check los archivos y, para regresiones/criterios requeridos, IDs esperados provenientes de la asociación revisada. No basta que otro test del mismo archivo pase. Los casos dinámicos/parametrizados deben concretarse con evidencia y oráculo revisados; cuando solo pueda acreditarse cobertura por suite/archivo, se informa ese nivel y no se afirma haber probado una función específica. La primera ejecución puede revelar una discrepancia: se conserva y se reconcilia, no se afloja la expectativa para pasar.

`reports.py` valida el inventario y lo contrasta con JUnit/recibo, archivos e IDs esperados; `workflow.run/gate` incluyen hashes y revalidan sin subprocess desde gate. Para suites esperadas completas, la deselección debe quedar visible; filtros parciales requieren selección de IDs explícita aprobada. Una requerida ausente mantiene la obligación técnica de evidencia real. Metadata de una suite no requerida sin registrar es un aviso nuevo, no motivo para certificar cobertura mayor ni para lanzar más tests automáticamente.

Inventario de ejecución y recibos prueban coherencia local, no son firmas ni una frontera contra alteración coordinada de datos. Reviewer conserva la revisión independiente actual.

### 6. Configuración permanente y resolución exclusiva por intento

Mantener el formato exacto actual como rama legacy. Para opt-in, extender `execution.schema.json` con `attempt_templates`: patrón de expediente, outputs por check, JUnit, coverage opcional e inventario de ejecución. Política conserva argv como plantilla revisada; ejecución conserva solo destinos, mappings y entorno, nunca comandos duplicados.

Para el modo nuevo, plan recibe HU/intento exactos y base; valida slugs seguros y resuelve, por ejemplo, `docs/hu/<change>/pruebas/attempt-<attempt>/junit-<check>.xml`. Variables permitidas: change, attempt, check_id, evidence_dir, junit_path, coverage_path e inventory_path, solo en campos/posiciones de argv definidos por el schema; ninguna expansión general de código, environment o shell. Se permiten tokens exactos y flags de reporte reconocidos, no texto arbitrario evaluado. Validar antes y después de expansión mediante safe_path/validate_outputs.

Generar lista exacta de outputs únicamente para checks seleccionados, incluyendo plan.json/git.json/resultados.json/gate.json, JUnit, receipt/stdout/stderr/coverage y `inventory-<check>.json`. Ampliar la gramática de este último nombre de forma exacta, sin permitir glob o excluir source/tests. Cualquier output coincidente con inputs bloquea como hoy. Preservar rechazo de symlink/junction/hardlink alias y colisión con evidencia primaria. Repetir un intento ocupado falla; otro intento se solicita explícitamente, sin contadores silenciosos.

El plan añade procedencia opcional `execution_resolution`: versión, identidad HU/intento, digest de plantillas originales y configuración resuelta por check. Sus argv concretos participan en selección/input_digest y recibos; settings resueltos participan en el digest de ejecución. Run/gate reconstruyen desde el origen permanente vigente y exigen igualdad con el plan, además de las invariantes actuales. Revisar argv/template inicial y congelar su digest una vez; no recalcular reviewed_policy_digest por cambiar solo HU/intento. Si cambia política, sí requiere revisión nueva.

Esta extensión elimina cambios manuales permanentes por intento, no permite usar evidencia de otro plan. Plan/run mantienen sus escrituras explícitas y creación exclusiva; discover/reconcile devuelven stdout salvo --out permitido. Los informes auxiliares de descubrimiento que se conserven viven en handoffs, no dentro de listas genéricas excluidas del candidato.

### 7. Evidencia canónica, modos y roles

Extender opcionalmente el handoff con `evidence.test_inventory_review`: observación de entrada/final, elementos afectados, disposiciones, refs de retiro y comprobación de inclusión. Las obligaciones esperadas congeladas participan en el contexto lógico del plan; observaciones posteriores se tratan como metadatos solo tras schema, identidad y correspondencia con esa obligación. Nunca excluir pruebas, fixtures, política o configuración para estabilizar la identidad. Incorporar plugin/catálogo a adapter_digest y a la validación original/personalizada.

Condiciones nuevas opcionales: `TEST_INVENTORY_RECONCILED` y `TEST_RETIREMENT_REVIEWED`, promovibles por separado con los mecanismos existentes. Informative inicial; no auto-promoción ni pausa por cada traspaso. Los bloqueos previos por unknown, criterio no cubierto, runtime inactivo, recibos ausentes o required test no ejecutado siguen siendo técnicos, no se degradan a avisos de inventario.

Discover/reconcile usan clasificación/códigos de transiciones: 0 completo sin veto habilitado (puede contener avisos), 2 condición promovida incumplida, 3 decisión humana necesaria, 4 error/indeterminado. Las acciones plan/run/gate y el helper puro conservan sus códigos legacy. Documentar la distinción; nunca usar un no-cero informativo como orden de detener toda la HU. Dependencia ausente impide afirmar validación; no instala nada.

| Fase / dueño | Entradas | Escrituras | Evidencia / continuidad |
| --- | --- | --- | --- |
| Onboarding / principal + responsable | Suites, configs y herramientas observadas | Catálogo, convenciones y baseline aplicable autorizados | Descubrimiento y estado real; no passed sin run. |
| Explore / Planner | HU, código y pruebas pertinentes | Solo captura autorizada | Cobertura/riesgos, sin colección implícita. |
| Propose / Planner | Criterios, oráculos, consumidores y catálogo | Artefactos y expediente asignados | Plan preliminar con casos/checks; nueva solicitud humana de Apply. |
| Apply / Developer | Plan aprobado | Código/tests/catalogación autorizada y tareas propias | Altas/modificaciones/retiradas propuestas; sin cambiar criterios por conveniencia. |
| Plan final / principal | Diff completo, catálogo y entregas | Plan/observación propios | Reconciliación y outputs exactos; no ejecuta pruebas. |
| Tester | Plan final e intérprete revisado | Evidencia y handoff propios | Suites seleccionadas, inventario observado, JUnit y recibos; no corrige producción ni catálogo para pasar. |
| Verify / Reviewer | Casos, retiro y recibos | Hallazgos/handoff propios | Gate sin run, oráculos, inclusión y verify. |
| Sync / Reviewer | Revisión y deltas favorables | Specs asignadas | No repite batería por rutina; aplica invalidación si se modifica una entrada funcional. |
| Archive / Reviewer | Expediente y autorización | Movimientos exactos | Preserva refs, intentos, evidencia y aprobaciones vigentes. |
| Git/PR / principal | Contenido autorizado | Entrega dentro de permiso vigente | Índice/commits/push/PR existentes; sin merge o deploy. |

### 8. Archivos mínimos y coste operativo

Nuevos en candidato: `scripts/crea/testing/catalog.py`, `pytest_inventory.py`, `tests/crea/test_catalog.py` (incluye casos de plugin/plantillas) y `crea-pruebas/assets/project-baseline.template.py`. Esta última solo se materializa en el cliente si no existe equivalente aplicable. Empaquetador de versión nueva puede compartirse si se entregan ambos cambios juntos.

Modificar: `scripts/crea/pruebas.py`, `testing/{workflow,reports,git_adapter,kit_validation}.py`, helper contract.py para selección por criterio/esperados, schemas policy/execution/plan/resultados si se añaden campos, proyecto/schema, handoff/schema, transiciones, skill Crea/referencias, orquestador, perfiles, prompt/guías y tests pertinentes. No cambiar las skills OpenSpec/Databricks upstream ni instalar plugins de terceros. `requirements-validation.txt` conserva dependencias actuales salvo incompatibilidad demostrada que exija otra propuesta.

La unidad de trabajo normal es el check ya configurado, no un caso que obliga a un despacho por sí mismo. Si una suite propia es indivisible se ejecuta esa suite; el informe explica ese coste. Medir lecturas/procesos y tiempo sin incluir duraciones en digests. Acreditar con fixtures grandes que reconcile no lee todos los cuerpos históricos y plan/gate no ejecutan suites. No prometer tiempos fijos ni importar recibos entre planes para aparentar menor coste.

## Risks / Trade-offs

- [Colección dinámica ejecuta código] -> solo en run revisado de Tester, observación en el mismo proceso, nunca desde discover/plan.
- [Nuevo test queda fuera del comando] -> expectativas por IDs/archivos revisados e inventario real; límites de cobertura visibles cuando no pueda identificarse un caso.
- [Retiro oculta regresiones] -> decisión/consumidores/criterios y definición histórica, sin cambiar expected para aprobar.
- [Templates alteran hashes] -> resolver una vez por plan y reconstruir en gate; legacy no adopta el formato nuevo automáticamente.
- [Fricción por metadata] -> controles nuevos informativos, por impacto, sin degradar obligaciones técnicas ni lanzar todo por defecto.
- [Framework propio no soportado] -> conservar estructura/descubrimiento y límite explícito; el requisito de ejecutarlo queda blocked sin un adaptador demostrado.
- [Contratos estrictos] -> schema y consumidores evolucionan juntos; ensayar configuraciones legacy y personalizadas.

## Migration Plan

1. En Apply autorizado registrar fuente vigente y crear candidato nuevo. Si el cambio A ya está incorporado, conservarlo y combinar únicamente campos propios; de lo contrario, este cambio opera solo. Una entrega conjunta puede ser 0.1.7 si está libre; entregas independientes usan nuevas versiones sucesivas, sin mutar una publicada.
2. Incorporar metadata opcional, templates y plugin con fixtures locales; no modificar catálogos clientes ni interpretar que las pruebas del kit ejecutadas son pruebas de negocio de otro repositorio.
3. Ofrecer diff de adopción informativa con suite existente, proyecto sin tests y proyecto con runtime requerido inactivo. Revisar catálogo/convenciones una vez; mantener intérprete, permisos y herramientas reales.
4. Verificar pipeline completo local e inclusión/retirada/outputs, regresiones de gates y bytes del paquete. Registrar límites de recursos/roles/remoto como no ejecutados cuando corresponda.
5. Promoción humana por condición después de casos positivos/negativos, sin requisito de repetir un número fijo de HU reales. Reversión conjunta de schema/herramientas/configuración; preservar intentos y no reetiquetar recibos ni alimentar herramientas antiguas con planes nuevos.

Ninguna fase de esta propuesta autoriza instalación, escritura remota, publicación o despliegue.
