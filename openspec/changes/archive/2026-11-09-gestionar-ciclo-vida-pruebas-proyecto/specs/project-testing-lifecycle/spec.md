# Spec Delta

## Purpose

Mantener las pruebas de un proyecto consumidor alineadas con su catálogo y cada HU, reutilizando selección, ejecución y evidencia del kit portable con configuración permanente y controles proporcionales.

## ADDED Requirements

### Requirement: Non executing onboarding discovery

El kit SHALL descubrir rutas de suites, fixtures, configuración y comandos declarados sin ejecutar ni importar código cliente. SHALL conservar procedencia, límites y estado no ejecutado, distinguiendo tests del kit, tests del proyecto y evals de agentes. MUST NOT instalar herramientas ni alterar suites por descubrirlas.

#### Scenario: Existing Python suite
- **WHEN** onboarding encuentra tests y configuración propios del repositorio
- **THEN** propone su registro con rutas y comandos observados, conservando su estructura sin afirmar que la suite pasó

#### Scenario: Dynamic collection needed
- **WHEN** conocer IDs reales requiere colección de pruebas que puede importar código
- **THEN** la declara como ejecución local revisada y no la realiza como efecto de descubrir archivos

#### Scenario: Missing discovery dependency
- **WHEN** falta una herramienta necesaria para inspeccionar una configuración
- **THEN** registra el descubrimiento parcial y la acción pendiente sin instalarla ni inventar pruebas

### Requirement: Applicable technical baseline

El onboarding SHALL proponer un mínimo técnico según archivos, tecnología y herramientas disponibles, reutilizando comprobaciones equivalentes existentes. SHALL diferenciar sintaxis, contratos y comportamiento. MUST NOT inventar reglas de negocio, dar cobertura funcional por pasar una validación técnica o exigir runtime por una extensión de archivo aislada.

#### Scenario: New project without tests
- **WHEN** un proyecto Python sin suites tiene código y contratos configurados
- **THEN** propone comprobaciones técnicas pertinentes y deja las pruebas de negocio pendientes de criterios reales

#### Scenario: Documentation only project
- **WHEN** el proyecto solo requiere validar documentos y configuración
- **THEN** selecciona comprobaciones locales aplicables sin exigir Spark, recursos Databricks o una suite de negocio ficticia

#### Scenario: Existing equivalent checks
- **WHEN** la suite propia ya comprueba el mínimo técnico aplicable
- **THEN** la reutiliza sin generar otra suite equivalente

### Requirement: One catalog and persistent placement conventions

El kit SHALL mantener comandos y checks en el catálogo único configurado, asociar suites o archivos de prueba a esos checks y registrar convenciones de ubicación revisadas. Los checks obligatorios SHALL seguir referenciándose por ID. MUST NOT mover suites propias ni requerir un catálogo duplicado por HU.

#### Scenario: Add a regression
- **WHEN** Developer añade una regresión dentro de una convención configurada
- **THEN** conserva su ubicación y reconcilia su asociación a checks sin pedir repetir todas las rutas del setup

#### Scenario: Unknown test location
- **WHEN** aparece una prueba fuera de las ubicaciones declaradas
- **THEN** informa la discrepancia con responsable y permite proponer su incorporación sin moverla automáticamente

### Requirement: Deterministic impact and criteria selection

La selección SHALL conservar la unión de reglas por rutas, dependencias de inputs y checks fijos, añadiendo checks asociados a criterios requeridos mediante relaciones declaradas. SHALL conservar motivos, ambas rutas de renombres y dependencias relevantes. MUST NOT eliminar bloqueos previos de rutas desconocidas, inputs ausentes o criterios sin check.

#### Scenario: Criterion selects an unchanged test
- **WHEN** un criterio requerido está asociado a un check cuyos archivos no cambiaron
- **THEN** selecciona ese check y explica el criterio que lo exige

#### Scenario: Dependency or fixture changes
- **WHEN** cambia un fixture, lockfile o configuración declarada como input de un check
- **THEN** selecciona sus checks consumidores aunque no cambie su archivo de prueba

#### Scenario: No approved behavior oracle
- **WHEN** un criterio no tiene una comprobación real configurada
- **THEN** conserva el diagnóstico de cobertura pendiente sin inventar assertions ni declarar passed

### Requirement: Final test inventory reconciliation

Antes del plan final, el kit SHALL contrastar Git completo, pruebas descubiertas y catálogo para identificar altas, modificaciones, movimientos, bajas y asociaciones pendientes. SHALL registrar la decisión por elemento afectado y distinguir cobertura de suite declarada de ejecución observada, sin auditar todas las pruebas históricas por cada HU.

#### Scenario: New test not registered
- **WHEN** el diff final añade una prueba sin check asociado
- **THEN** registra la omisión para reconciliarla conforme al modo configurado y conserva el gate técnico previo

#### Scenario: Broad inputs hide incomplete command
- **WHEN** una prueba modificada coincide con inputs pero el comando seleccionado no demuestra incluirla
- **THEN** no trata esa coincidencia como evidencia de ejecución y registra la discrepancia

### Requirement: Observed inclusion in executed suites

Para las suites locales soportadas, Tester SHALL conservar observaciones estructuradas de pruebas recogidas y ejecutadas con sus archivos o IDs contrastables. El gate SHALL comparar las pruebas requeridas esperadas con esa evidencia y rechazar su ausencia. Contadores globales, coincidencias de rutas o exit cero MUST NOT sustituir esa comparación.

#### Scenario: Required new regression is excluded
- **WHEN** una regresión requerida registrada no aparece en la ejecución por filtros o un comando incompleto
- **THEN** el gate la declara requerida no acreditada aunque otras pruebas pasen

#### Scenario: Complete selected execution
- **WHEN** la ejecución acredita archivos o IDs requeridos y satisface assertions, entorno, recibos y vigencia
- **THEN** acepta la evidencia sin ejecutar de nuevo la suite para verificar su inclusión

#### Scenario: Framework lacks a supported execution adapter
- **WHEN** una suite necesaria usa un ejecutor no soportado por el kit
- **THEN** conserva el descubrimiento y su límite, y no declara ejecución acreditada ni la sustituye por una suite ficticia

### Requirement: Reviewed retirement and replacement

El kit SHALL identificar pruebas potencialmente obsoletas mediante bajas, renombres y referencias declaradas, sin decidir obsolescencia semántica automáticamente. Retiro o sustitución SHALL conservar motivo, decisión y evidencia, y reconciliar reglas, checks, criterios y assertions. MUST NOT retirar pruebas para ocultar un defecto.

#### Scenario: Feature removed
- **WHEN** una HU elimina una funcionalidad con pruebas asociadas
- **THEN** propone conservar, sustituir o retirar esas pruebas y exige revisión de consumidores y referencias antes de aceptar el retiro

#### Scenario: A failing test is disabled
- **WHEN** un cambio intenta desactivar una prueba requerida sin decisión de alcance aprobada
- **THEN** conserva el incumplimiento técnico y no acepta la desactivación como passed

### Requirement: Configure outputs once and resolve per attempt

El kit SHALL resolver comandos y destinos exactos desde convenciones revisadas y la identidad HU/intento/check, congelándolos en el plan. MUST NOT reescribir configuración permanente por intento, ejecutar shell concatenado desde datos, aceptar variables arbitrarias o reutilizar destinos ocupados. El catálogo SHALL seguir siendo la fuente única de comandos.

#### Scenario: Second story after setup
- **WHEN** empieza otra HU con la misma política y convenciones
- **THEN** obtiene sus rutas exclusivas sin editar manualmente cada argv, JUnit y output del proyecto

#### Scenario: Unsafe identity or variable
- **WHEN** la expansión incluye traversal, una variable desconocida o un destino ajeno al expediente permitido
- **THEN** rechaza el plan antes de ejecutar o escribir evidencia

#### Scenario: Attempt already exists
- **WHEN** un intento propone un destino de evidencia ocupado
- **THEN** lo rechaza y conserva el intento anterior sin asignar silenciosamente otro destino

### Requirement: Preserve existing execution guarantees

El cambio SHALL reutilizar plan/run/gate, recibos primarios, assertions, entorno, TTL e intentos existentes, sin habilitar reutilización entre planes. Reviewer SHALL consumir evidencia vigente sin relanzar suites por rutina. Cambios funcionales SHALL aplicar invalidación; correcciones de referencias sin cambio de entradas SHALL revalidar el contrato.

#### Scenario: Reviewer consumes valid receipts
- **WHEN** plan, candidato, entradas, entorno y recibos permanecen vigentes
- **THEN** verifica mediante gate sin repetir la batería seleccionada

#### Scenario: New candidate after correction
- **WHEN** una corrección genera otro plan
- **THEN** conserva resultados anteriores y ejecuta lo requerido para el plan nuevo sin importar o reetiquetar recibos previos

### Requirement: Honest runtime and effect boundaries

El kit SHALL separar comprobaciones técnicas locales, pruebas Python, validación SQL y requisitos Spark/Databricks. SHALL mantener inactivas las capacidades sin adaptador implementado y autorización aplicable. Una capacidad requerida inactiva SHALL bloquear el gate previo, aunque pasen mocks, sintaxis o suites locales.

#### Scenario: Runtime semantics required
- **WHEN** una HU requiere comprobar semántica Spark o Delta y no dispone de adaptador activo autorizado
- **THEN** conserva blocked sin crear recursos ni aceptar el parser como prueba de runtime

#### Scenario: Local technical check passes
- **WHEN** pasa una comprobación local de sintaxis o contratos
- **THEN** informa ese alcance sin afirmar ejecución Databricks, permisos remotos o equivalencia con el runtime

### Requirement: Proportionate informative lifecycle controls

Las condiciones nuevas de mantenimiento SHALL comenzar informativas y promoverse expresamente por ID con el mecanismo vigente. SHALL limitarse al impacto afectado y no crear aprobaciones por traspaso ni bucles de corrección. MUST NOT ejecutar toda la batería por defecto ni degradar gates técnicos anteriores a avisos.

#### Scenario: Informative catalog omission
- **WHEN** falta metadata de una suite y el control nuevo no está promovido
- **THEN** informa la corrección sin añadir bloqueo si se satisfacen los controles técnicos y autorizaciones existentes

#### Scenario: Promoted inventory discrepancy
- **WHEN** una condición promovida detecta un registro requerido sin reconciliar
- **THEN** bloquea solo la continuación dependiente y señala responsable, corrección y evidencia válida preservada

#### Scenario: Required execution has no evidence
- **WHEN** falta evidencia de una prueba requerida por el plan
- **THEN** mantiene el bloqueo técnico independientemente del modo informativo del inventario

### Requirement: Safe discovery and planning boundaries

Descubrimiento, reconciliación y planificación MUST NOT ejecutar suites, instalar herramientas o contactar servicios. SHALL devolver salida sin escritura por defecto; persistir un informe o plan requiere destino explícito permitido y creación exclusiva. SHALL rechazar enlaces, escapes y colisiones con evidencia primaria sin modificar el catálogo como efecto de inspección.

#### Scenario: Read only inspection
- **WHEN** se descubre o reconcilia sin destino de informe
- **THEN** no crea ni modifica archivos, no recoge tests dinámicos y no realiza llamadas remotas

#### Scenario: Colliding output
- **WHEN** el informe solicitado coincide con un recibo, archivo existente o ruta enlazada
- **THEN** rechaza esa escritura sin sobrescribir ni redirigir evidencia

### Requirement: Compatible independent adoption

La extensión SHALL ser opcional y adoptarse con catálogo, schemas y consumidores compatibles mediante diff revisado, preservando suites y evidencia anteriores. SHALL funcionar sin la gestión evolutiva del contexto y distribuirse en una versión nueva sin mutar árboles/ZIP históricos ni habilitar herramientas o capacidades adicionales automáticamente.

#### Scenario: Legacy configuration
- **WHEN** un consumidor no adopta la extensión ni convenciones nuevas
- **THEN** conserva el plan/run/gate anterior y no requiere inventarios o migración de recibos retroactivos

#### Scenario: Context extension is absent
- **WHEN** se adopta el ciclo de vida de pruebas sin el cambio de contexto
- **THEN** usa rutas, criterios, inputs y handoffs existentes sin depender de un mapa documental nuevo
