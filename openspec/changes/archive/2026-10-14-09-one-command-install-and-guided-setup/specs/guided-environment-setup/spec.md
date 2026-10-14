# Spec Delta

## Purpose

Coordinar desde el chat los insumos, herramientas, permisos y preparación de un cliente, reutilizando contratos existentes y entregando capacidades comprobadas con límites explícitos.

## ADDED Requirements

### Requirement: Import inputs and ask only missing decisions

El setup SHALL aceptar descriptor, política, binding y URL de repositorio desde archivos o entrevista, normalizar la identidad remota y pedir solo información faltante o contradictoria. SHALL separar insumos portables de rutas/perfiles locales; MUST NOT reutilizar un binding de otra máquina sin revalidar identidad y regenerar selecciones locales aprobadas.

#### Scenario: Complete supplied inputs
- **WHEN** los archivos y decisiones locales son completos, coherentes y válidos
- **THEN** produce el plan sin repetir preguntas ni exigir editar archivos de comandos manualmente

#### Scenario: Foreign or ambiguous binding
- **WHEN** target, checkout, estado o remoto no coinciden con los insumos
- **THEN** pide resolver la selección y bloquea apply sin adoptar rutas ajenas

### Requirement: Explicit read and write scope

El setup SHALL aceptar un contrato adicional de rutas relativas permitidas para lectura/escritura con denegaciones prevalentes, validarlo junto con política v1 y limitar adaptadores propios y planes de HU a su intersección. SHALL rechazar escapes, enlaces y ambigüedad de rutas Windows. MUST NOT afirmar que ese contrato intercepta toda herramienta nativa de Desktop.

#### Scenario: Allowed read and denied write
- **WHEN** una ruta está permitida para lectura y no para escritura
- **THEN** los adaptadores propios permiten la lectura y rechazan la modificación

#### Scenario: Escape or deny overlap
- **WHEN** una operación escapa del checkout, usa un enlace o coincide con una denegación
- **THEN** rechaza la operación antes de leer/escribir el recurso y conserva un diagnóstico de alcance

#### Scenario: Legacy policy without allowlists
- **WHEN** el cliente aporta solo política v1
- **THEN** solicita o presenta para aprobación un contrato adicional de alcance sin asumir permiso total ni cambiar v1 silenciosamente

### Requirement: Unified setup plan and staged application

El setup SHALL presentar un único plan revisable con herramientas/descargas, fuentes/hashes, clonación o checkout existente, rutas, archivos gestionados, configuración externa, fases de autenticación y comprobaciones. La autorización SHALL quedar ligada a identidad, entradas y revisión del plan. SHALL revalidar precondiciones por etapa, preservar personalizaciones y registrar reanudación/recuperación conservadora.

#### Scenario: Authorized composite setup
- **WHEN** el usuario aprueba el plan vigente
- **THEN** aplica las etapas previstas sin repetir aprobación del mismo alcance y conserva las interacciones externas de login/confianza necesarias

#### Scenario: Scope drift or existing instructions
- **WHEN** cambian entradas relevantes o existe AGENTS/TOML personalizado incompatible con el plan
- **THEN** bloquea la etapa afectada y presenta el conflicto o plan actualizado sin sobrescribir ni reutilizar una autorización stale

#### Scenario: Setup preview
- **WHEN** se solicita preview sin exportación
- **THEN** no clona, descarga, crea bases, autentica ni modifica target, estado o configuración de usuario

### Requirement: Managed dependencies and guided authentication

El setup SHALL detectar versiones de herramientas requeridas por las capacidades seleccionadas, preparar las faltantes dentro del alcance aprobado y guiar autenticación nativa. SHALL mantener secretos fuera del chat, planes, logs y repositorio; informar instalaciones restringidas o login cancelado sin inventar perfiles, hosts ni permisos.

#### Scenario: Databricks capability selected without CLI
- **WHEN** la capacidad seleccionada exige CLI y falta una versión compatible
- **THEN** incluye una instalación fijada de usuario en el plan y verifica el binario antes de usar el perfil elegido

#### Scenario: OAuth cancelled or unauthorized remote
- **WHEN** el usuario cancela OAuth o el perfil no tiene permisos para la comprobación seleccionada
- **THEN** conserva la preparación local y marca la capacidad remota bloqueada sin ejecutar jobs, deploy ni cambios de datos

### Requirement: Capability-specific readiness

El informe SHALL separar recursos escritos, Skills descubiertas, agentes/modelos/herramientas observados, permisos efectivos, validación local, conectividad y certificación. SHALL explicar qué clase de HU puede iniciarse y qué requisitos faltan; MUST NOT inferir activación, aislamiento o acceso remoto a partir de archivos generados.

#### Scenario: Local preparation and absent remote evidence
- **WHEN** los recursos locales están preparados y no se ha comprobado el sandbox remoto
- **THEN** identifica la HU local posible, marca remote_not_checked y mantiene la fase remota bloqueada

#### Scenario: Agent configured but isolation failed
- **WHEN** existe configuración de agente pero una comprobación requerida de aislamiento falla
- **THEN** informa la limitación y bloquea la fase que exige aislamiento conservando certified=false
