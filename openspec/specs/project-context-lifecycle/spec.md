# project-context-lifecycle Specification

## Purpose

Mantener el contexto vigente de un proyecto consumidor del kit portable mediante selección reproducible, impacto documental por HU y reconciliación proporcional, conservando decisiones humanas y evidencia existente.

## Requirements

### Requirement: Canonical context responsibilities

El kit SHALL distinguir configuración e inventario, orientación global, reglas operativas, especificaciones funcionales, documentación técnica, contexto de HU e historia. SHALL referenciar sus fuentes canónicas y conservar contenido manual y decisiones aprobadas sin duplicar requisitos entre documentos.

#### Scenario: Functional rule changes
- **WHEN** una HU modifica una regla funcional documentada en OpenSpec
- **THEN** identifica el delta y los documentos explicativos afectados sin copiar el requisito al inventario ni reescribir todas las prácticas

#### Scenario: Approved manual content
- **WHEN** un documento contiene secciones manuales no afectadas por la HU
- **THEN** las conserva y propone solamente las modificaciones pertinentes

### Requirement: Configure once with explicit component mappings

El kit SHALL admitir una extensión opcional revisada que relacione componentes, rutas, dependencias y documentos, reutilizando inventario y exclusiones. SHALL señalar relaciones desconocidas sin inventar arquitectura y ofrecer su actualización únicamente cuando el proyecto incorpore cambios pertinentes.

#### Scenario: Existing configured component
- **WHEN** una HU posterior afecta a un componente registrado
- **THEN** resuelve sus documentos y dependencias sin pedir al desarrollador repetir la lista de archivos del setup

#### Scenario: New component has no mapping
- **WHEN** el diff contiene un componente sin correspondencia configurada
- **THEN** informa la ruta y la decisión pendiente con responsable, aplicando el modo configurado sin crear un mapa ficticio

### Requirement: Reproducible role specific selection

La selección SHALL producir referencias ordenadas y sin duplicados por rol y fase, con fuente y motivo. SHALL conservar las reglas seleccionadas mediante el mecanismo vigente e incluir únicamente componentes afectados, dependencias declaradas pertinentes y referencias históricas explícitas.

#### Scenario: Localized change
- **WHEN** una HU afecta un componente con una dependencia declarada
- **THEN** selecciona sus documentos pertinentes y los de esa dependencia, sin cargar componentes no relacionados ni todo el archivo histórico

#### Scenario: Same inputs
- **WHEN** se repite la selección con igual configuración, alcance y contenido
- **THEN** devuelve el mismo resultado semántico independientemente del orden de enumeración de archivos

### Requirement: Safe bounded context reading

El kit SHALL respetar exclusiones y rechazar referencias que escapen del checkout o atraviesen enlaces no admitidos. MUST NOT cargar secretos, datos productivos o historia por disponibilidad. Excluir un archivo del contexto MUST NOT ocultar sus cambios al inventario Git, a los gates ni a la revisión de alcance.

#### Scenario: Secret or external reference
- **WHEN** una referencia apunta a un archivo excluido de credenciales o fuera del repositorio
- **THEN** devuelve un diagnóstico acotado sin leer o copiar su contenido ni ampliar permisos

#### Scenario: Excluded changed file
- **WHEN** un archivo excluido del contexto aparece en el diff
- **THEN** preserva su detección para los controles Git y de alcance sin incorporarlo a la lectura contextual

### Requirement: Planned documentary impact

Durante planificación, el kit SHALL registrar componentes y documentos afectados, operación prevista, motivo y responsable en el contrato de HU. SHALL permitir declarar impacto nulo con justificación breve y no exigir resultados futuros ni autorización adicional por una transferencia ya autorizada.

#### Scenario: Planned path migration
- **WHEN** una HU prevé mover un componente
- **THEN** identifica inventario, referencias técnicas y documentos afectados por las rutas anterior y nueva antes de Apply

#### Scenario: No documentary change needed
- **WHEN** una corrección interna mantiene contratos, rutas y documentación vigentes
- **THEN** registra una justificación proporcional sin exigir editar archivos que ya son correctos

### Requirement: Final impact reconciliation

Antes de Sync, el kit SHALL contrastar el impacto previsto con el diff Git completo y registrar por documento actualización, conservación justificada, no aplicabilidad o pendiente. SHALL comprobar referencias y cambios observables; Reviewer SHALL revisar su coherencia semántica sin aceptar un hash distinto como prueba suficiente.

#### Scenario: Unexpected component change
- **WHEN** el candidato final afecta un componente no previsto
- **THEN** registra la discrepancia y la remite al responsable para reconciliar alcance y documentación según las autorizaciones vigentes

#### Scenario: Deleted or renamed component
- **WHEN** se elimina o renombra un componente
- **THEN** comprueba ambas rutas y sus referencias declaradas, preservando la justificación de cada documento conservado o modificado

### Requirement: Informative adoption and scoped blocking

Las condiciones nuevas SHALL comenzar informativas y usar la promoción expresa de transiciones existente. Solo una condición objetiva habilitada SHALL bloquear su continuación dependiente. Una recomendación editorial no adoptada MUST NOT bloquear, y el modo informativo MUST NOT desactivar gates o aprobaciones anteriores.

#### Scenario: Informative omission
- **WHEN** falta una justificación documental y no está promovida su condición
- **THEN** emite aviso con corrección concreta y permite continuar si los controles previos están satisfechos

#### Scenario: Promoted missing reconciliation
- **WHEN** falta una reconciliación requerida por una condición habilitada para Sync
- **THEN** detiene solo Sync y su continuación dependiente, permitiendo trabajo independiente autorizado

#### Scenario: Existing required test fails
- **WHEN** la revisión documental es informativa pero falla un gate de pruebas previamente obligatorio
- **THEN** conserva el bloqueo técnico existente

### Requirement: Proportionate local checking

El kit SHALL limitar la inspección documental a metadatos necesarios y referencias afectadas, reutilizando observaciones vigentes. MUST NOT ejecutar suites, acceder a servicios, instalar herramientas ni iniciar bucles de reparación durante esta comprobación. SHALL informar límites o comprobaciones incompletas sin afirmar cumplimiento.

#### Scenario: Small documentation change
- **WHEN** solo se aclara un documento de un componente
- **THEN** no relee todos los documentos ni solicita ejecución Spark o repetición de suites por esa comprobación

#### Scenario: Missing local dependency
- **WHEN** falta Git o una dependencia requerida por el validador
- **THEN** informa error e indeterminación; en modo informativo no añade un veto ni declara pasado el control, y conserva las restricciones previas

### Requirement: Evidence continuity without circularity

El kit SHALL conservar el impacto y su reconciliación por intento en handoffs canónicos, separando observaciones iniciales de referencias actuales. SHALL congelar entradas funcionales antes del plan final y aplicar la invalidación existente cuando cambien. MUST NOT ocultar documentación funcional como metadatos ni migrar recibos históricos automáticamente.

#### Scenario: Resume after test execution
- **WHEN** se reanuda una HU con contexto, candidato, política, entorno y recibos vigentes
- **THEN** revalida las referencias pertinentes y continúa sin reiniciar rondas, repetir aprobaciones vigentes o relanzar suites por rutina

#### Scenario: Evidence reference correction
- **WHEN** se corrige un enlace en un nuevo intento sin modificar entradas funcionales
- **THEN** conserva la evidencia técnica válida y revalida solo el contrato afectado

#### Scenario: Functional documentation changes after testing
- **WHEN** cambia una entrada documental funcional del plan después de Tester
- **THEN** reconcilia el candidato mediante plan/run/gate sin reetiquetar recibos de otro plan

### Requirement: Side effect free inspection

La inspección SHALL devolver su resultado sin escribir archivos por defecto. Una salida solicitada SHALL crearse exclusivamente en una ruta permitida de la HU y rechazar sobrescrituras, enlaces o escapes. MUST NOT modificar documentación, configuración, permisos, ramas o recursos remotos como efecto de inspeccionar.

#### Scenario: Inspection without output
- **WHEN** se ejecuta la inspección sin destino de informe
- **THEN** no modifica el checkout ni estado global y no ejecuta pruebas

#### Scenario: Existing output destination
- **WHEN** se solicita un informe en una ruta ocupada o enlazada
- **THEN** rechaza esa escritura conservando la evidencia existente

### Requirement: Compatible portable evolution

La extensión SHALL ser opcional para consumidores anteriores y adoptarse con schema y consumidores compatibles mediante diff revisado. La entrega SHALL preservar fuentes, ZIP y manifiestos anteriores, no exigir reconstruir HU históricas y permanecer independiente del motor Python histórico y del cambio de ciclo de vida de pruebas.

#### Scenario: Legacy consumer
- **WHEN** un proyecto no declara gestión evolutiva del contexto
- **THEN** conserva su comportamiento vigente sin generar contratos o bloqueos nuevos retroactivos

#### Scenario: New portable release
- **WHEN** se prepara una distribución que incorpora esta capacidad
- **THEN** usa un candidato versionado nuevo y acredita integridad y regresión local sin afirmar piloto nativo o validación remota
