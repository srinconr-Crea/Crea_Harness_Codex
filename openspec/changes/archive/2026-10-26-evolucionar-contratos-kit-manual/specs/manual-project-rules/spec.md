# Spec Delta

## Purpose

Permitir que el kit manual Crea aplique las mismas obligaciones del proyecto durante planificación, desarrollo y revisión, seleccionando únicamente las capas y capacidades pertinentes y preservando decisiones humanas verificables.

## ADDED Requirements

### Requirement: Selective shared rule context

El kit manual SHALL resolver reglas comunes, capas y capacidades declaradas por HU desde rutas configuradas y conservar IDs, revisiones y justificación de selección en el handoff. Planner, Developer y Reviewer SHALL consumir esa misma selección; las listas vacías SHALL requerir justificación cuando no aplique contexto de datos.

#### Scenario: Silver with Spark
- **WHEN** una HU declara capas `[silver]` y capacidades `[spark]`
- **THEN** selecciona comunes, Silver y Spark, sin cargar Gold, SQL, jobs o pipelines por mera disponibilidad

#### Scenario: Documentation without data layer
- **WHEN** una HU documental justifica capas y capacidades vacías
- **THEN** aplica solo las reglas comunes pertinentes sin inventar una capa ni pedir un runtime de datos

#### Scenario: Selection drifts between roles
- **WHEN** Developer recibe una revisión de reglas distinta de la presentada por Planner
- **THEN** informa la discrepancia y pide reconciliar el alcance antes de Apply; no sustituye silenciosamente la selección

### Requirement: Verifiable and bounded normative content

Cada regla normativa SHALL tener ID estable, condición, obligación, fundamento, evidencia, modo de comprobación y tratamiento de excepciones. El kit SHALL distinguir reglas justificadas, plantillas personalizables y especialidades pendientes, sin activar documentos vacíos ni convenciones de cliente supuestas.

#### Scenario: Initial common obligations
- **WHEN** se distribuyen reglas iniciales basadas en instrucciones vigentes del kit
- **THEN** conservan fundamento y evidencia, y los ejemplos extensos, parámetros y valores de ambiente permanecen fuera del núcleo normativo

#### Scenario: Pending layer policy
- **WHEN** no existe decisión de proyecto sobre conservación o identidad Silver
- **THEN** la plantilla identifica esa decisión pendiente y no presenta una política inventada como activa

### Requirement: Proportionate rule governance

El flujo SHALL elevar contradicciones normativas críticas al responsable del proyecto y conservar decisión, alcance y excepciones permitidas. Cambios de obligación, criterios, selección o excepciones sustantivas SHALL requerir aprobación aplicable; aclaraciones sin cambio de significado SHALL admitirse con revisión local. Ningún rol SHALL alterar reglas para aprobar su resultado.

#### Scenario: Functional contradiction
- **WHEN** una obligación de conservación entra en conflicto con un borrado solicitado
- **THEN** detiene la parte dependiente antes de Apply y solicita decisión; repetir comprobaciones no resuelve el conflicto

#### Scenario: Harmless clarification
- **WHEN** se corrige una errata sin cambiar obligación, evidencia o alcance
- **THEN** conserva el significado aprobado y documenta la revisión sin exigir otra HU de gobierno

#### Scenario: Unauthorized exception
- **WHEN** un rol declara una excepción no permitida o sin decisión del responsable
- **THEN** no la acepta como cumplimiento ni como autorización para cambiar criterios

### Requirement: Configuration is declarative context

La configuración de reglas SHALL localizar y activar documentos con rutas relativas verificables, sin instalar extensiones ni conceder permisos nativos. Ausencia de documentos activados SHALL producir un diagnóstico concreto; solo una decisión necesaria para definir comportamiento SHALL detener Propose, permitiendo conservar borrador y trabajo independiente.

#### Scenario: Missing active rule document
- **WHEN** una capa seleccionada apunta a un archivo inexistente
- **THEN** identifica documento y responsable de corregir la configuración sin crear reglas ficticias

#### Scenario: Unconfigured consumer
- **WHEN** un proyecto anterior no ha adoptado la extensión de reglas
- **THEN** conserva su flujo vigente y ofrece configuración revisable sin instalar o modificar archivos como efecto de lectura
