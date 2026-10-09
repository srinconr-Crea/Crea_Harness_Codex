# Spec Delta

## Purpose

Preparación reversible y certificación de capacidades en la aplicación objetivo. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

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

### Requirement: Supervised preparation separate from certification

El producto SHALL emitir un resultado de preparación supervisada separado del certificado estricto, ligado a identidad seleccionada, catálogo y evidencia de versión. SHALL registrar capacidades observadas y conflict/unsupported/not_checked, motivos y aceptación explícita del operador. Preparación supervisada verificada MAY satisfacer la dependencia de onboarding preparado, pero MUST NOT transformar capacidades fallidas en passed ni alterar assess_certificate. Una fase que requiera una capacidad ausente o fallida SHALL permanecer blocked.

#### Scenario: Prepared with accepted sandbox limitation
- **WHEN** la integración local está verificada y el operador acepta la escritura observada de revisores para uso supervisado
- **THEN** permite preparación supervisada y conserva certified=false y el conflicto de sandbox en el informe

#### Scenario: Strict certification after supervised preparation
- **WHEN** se solicita certificación estricta tras aceptar limitaciones
- **THEN** evalúa las mismas observaciones sin excepciones y no certifica capacidades conflictivas

#### Scenario: Required capability unavailable
- **WHEN** una fase exige una capacidad conflictiva o no observada
- **THEN** bloquea esa fase aunque exista preparación supervisada

#### Scenario: Original eval evidence and human annotation
- **WHEN** se registran E03/E04 para aceptación supervisada
- **THEN** conserva inputs/outputs originales y procedencia de ejecución, requiere anotación humana y mantiene los resultados negativos sin falsos passed
