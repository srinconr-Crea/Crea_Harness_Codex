# desktop-integration Specification

## Purpose

Preparación reversible y certificación de capacidades en la aplicación objetivo. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## Requirements

### Requirement: Reviewable project integration

El producto SHALL producir un plan de creación/edición de configuración de proyecto con contenidos, old/new hashes, backups y ownership. MUST NOT modificar configuración global o personalizaciones sin plan explícito.

#### Scenario: Custom instructions
- **WHEN** existe AGENTS personalizado
- **THEN** presenta integración revisable preservando reglas cliente

#### Scenario: Drift before apply
- **WHEN** cambia un archivo desde el preview
- **THEN** rechaza la edición antes de reemplazarlo

### Requirement: Observed desktop capabilities

El producto SHALL certificar descubrimiento y ejecución de roles, Skills, modelos/esfuerzos y herramientas en Desktop mediante tareas sintéticas y evidencia de versión. Archivos o CLI MUST NOT equivaler a certificación Desktop.

#### Scenario: Observed role
- **WHEN** Desktop ejecuta el rol/modelo/esfuerzo esperado
- **THEN** registra resultado y versión en certificado

#### Scenario: Unsupported surface
- **WHEN** la app no permite seleccionar un rol o herramienta
- **THEN** marca unsupported/not_checked y no declara onboarding certificado

### Requirement: Conservative integration recovery

La recuperación SHALL restaurar solo archivos propios cuyo estado aplicado permanezca intacto; cambios posteriores SHALL producir conflict sin sobrescritura.

#### Scenario: Intact applied file
- **WHEN** se solicita recover y coincide identidad/hash aplicados
- **THEN** restaura backup validado o retira creación propia

#### Scenario: User modification
- **WHEN** la persona editó el TOML después de integrar
- **THEN** conserva el archivo y registra conflicto

### Requirement: Side effect free preview

El producto SHALL ofrecer preview sin editar target, estado, configuración global ni sistemas remotos. Exportación explícita SHALL crear solo el plan externo solicitado mediante creación exclusiva.

#### Scenario: Preview snapshot
- **WHEN** se solicita preview sin exportación
- **THEN** conserva snapshots y no ejecuta escritura o autenticación

#### Scenario: Existing export destination
- **WHEN** el destino de exportación existe o está enlazado
- **THEN** rechaza sin sobrescribir o redirigir archivos
