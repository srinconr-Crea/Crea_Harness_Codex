# onboarding-application Specification

## Purpose

Preparar archivos locales de un checkout cliente mediante un plan revisado y autorizado, preservando su contenido y separando sus instrucciones del producto y del estado personal.

## Requirements

### Requirement: Explicit bounded plan application

`harness init --apply --plan FILE --path TARGET --policy FILE` SHALL aceptar únicamente un plan exportado compatible y un checkout/política seleccionados explícitamente. SHALL revalidar los contratos, origin, integridad, identidades y todas las precondiciones antes de escribir archivos del cliente. MUST NOT interpretar el plan como autorización para comandos arbitrarios o para seleccionar otra política.

#### Scenario: Apply reviewed plan
- **WHEN** el plan corresponde al target y política seleccionados y todas sus precondiciones se mantienen
- **THEN** se crean exclusivamente sus archivos ausentes autorizados y se devuelve un registro de resultados

#### Scenario: Stale or redirected plan
- **WHEN** cambian política, binding, archivos comparados, ausencias previstas, target u origin desde la exportación
- **THEN** se rechaza con `stale_plan` o error específico de identidad antes de escribir archivos cliente

#### Scenario: Tampered plan payload
- **WHEN** el plan incorpora contenido, destino, versión, acciones o recursos distintos de los que admite el kit
- **THEN** se rechaza como `invalid_plan` sin ejecutar su contenido ni concederle nuevos permisos

### Requirement: Authorized onboarding destinations

La aplicación SHALL respetar `read_only_paths`, `denied_paths`, `max_files` y `max_bytes` de la política para las creaciones dentro del target. SHALL limitar escrituras externas al binding y estado seleccionados del mismo cliente/checkout, rechazando traversal, enlaces y destinos solapados. MUST NOT relajar la política automáticamente para preparar archivos protegidos.

#### Scenario: Policy denies bootstrap file
- **WHEN** una creación prevista, incluso `.harness/client.yaml`, está bajo una restricción de política o excede un límite
- **THEN** el plan queda bloqueado y la aplicación conserva el target sin cambios

#### Scenario: Linked destination
- **WHEN** un destino o ancestro es symlink/junction o se sustituye por uno durante la ejecución
- **THEN** se rechaza o interrumpe la operación sin escribir a través del enlace

### Requirement: Preserve existing client artifacts

La aplicación SHALL crear solo archivos ausentes incluidos en el plan y conservar los existentes. AGENTS personalizado o artefactos incompatibles SHALL bloquear la aplicación con integración manual, sin opción de sobrescritura automática. MUST NOT editar specs, cambios, código, configuración global o TOML existente del cliente.

#### Scenario: Existing custom instructions
- **WHEN** AGENTS contiene instrucciones distintas de la plantilla del kit
- **THEN** se informa conflicto y no se aplica ninguna creación cliente hasta resolverlo y regenerar el plan

#### Scenario: Compatible prepared client
- **WHEN** los archivos compatibles ya existen
- **THEN** se conservan byte a byte y no se reinicializa OpenSpec

### Requirement: Concrete versioned OpenSpec preparation

Para los elementos OpenSpec ausentes el kit SHALL proporcionar contenido genérico inspeccionable, fijado a una versión soportada, para configuración spec-driven y los siete workflows explore, propose, update, apply, verify, sync y archive. MUST NOT descargar dependencias, inicializar sobre el cliente mediante un proceso opaco ni incorporar conocimiento de otro cliente.

#### Scenario: Unprepared checkout
- **WHEN** faltan configuración OpenSpec y sus siete Skills y los recursos del kit están completos y autorizados
- **THEN** el plan contiene su contenido/hash y apply crea únicamente esos elementos

#### Scenario: Missing or incompatible kit resources
- **WHEN** los recursos empaquetados no cumplen el manifiesto/versiones requeridos
- **THEN** la preparación queda bloqueada antes de escribir el target con un diagnóstico específico

### Requirement: Idempotent local outcome and diagnostics

Aplicar otra vez el mismo plan ya completado SHALL reconocer su resultado intacto sin recrear archivos ni duplicar el registro de ejecución. Una modificación posterior SHALL producir conflicto. Tras las escrituras SHALL ejecutarse diagnóstico local read-only, diferenciando aplicación completa de herramientas ausentes y verificaciones Desktop/remotas pendientes. MUST NOT ejecutar pruebas del cliente, auth, modelos, red, commit, push ni despliegues.

#### Scenario: Repeated completed application
- **WHEN** existe un registro completo del mismo plan y sus resultados siguen intactos
- **THEN** se devuelve el resultado ya aplicado sin efectos adicionales

#### Scenario: Local files prepared but remote access unknown
- **WHEN** la preparación termina correctamente y no se han probado Desktop ni Databricks
- **THEN** se informa preparación aplicada y esas verificaciones permanecen `not_checked`
