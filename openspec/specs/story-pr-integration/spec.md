# story-pr-integration Specification

## Purpose

Adaptadores de lectura de HU y publicación reconciliable con gates. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## Requirements

### Requirement: Versioned story sources

StoryProvider SHALL leer HU/revisión/criterios y congelar snapshot sanitizado; datos externos MUST NOT autorizar nuevas herramientas o escrituras.

#### Scenario: Changed story
- **WHEN** cambia aceptación de la HU desde planificación
- **THEN** exige reconciliar plan y aprobación

#### Scenario: Injected instructions
- **WHEN** historia pide ignorar gates o usar otro repo
- **THEN** trata contenido como datos y no ejecuta instrucciones operativas

### Requirement: Authorized final candidate publication

GitProvider SHALL publicar solo con autorización explícita para push/PR, identidad correcta y gates vigentes del candidato final con specs/evidencia, incluidos los de evaluación requeridos de 06. La habilitación de implementación local MUST NOT omitir ese gate ni contar not_run/blocked como passed.

#### Scenario: Authorized draft PR
- **WHEN** plan final y candidato pasan gates y usuario autoriza publicación
- **THEN** crea PR draft en repo/base/head seleccionados

#### Scenario: No publication permission
- **WHEN** hay aprobación técnica pero falta autorización para publicar
- **THEN** mantiene preview preparado y no hace push/PR ni comentarios

#### Scenario: Pending required agent evaluations
- **WHEN** el usuario autoriza publicación pero evaluaciones requeridas de 06 permanecen not_run o blocked
- **THEN** bloquea push, creación de PR y comentarios, conservando el motivo; la excepción de implementación local no sustituye el gate

### Requirement: Idempotent remote reconciliation

Una operación remota unknown SHALL reconciliar branch/head/PR antes de reintentar y persistir receipt/URL. MUST NOT duplicar PR ni sobrescribir ramas ajenas.

#### Scenario: Interrupted PR creation
- **WHEN** el proveedor creó PR pero respuesta se perdió
- **THEN** encuentra PR por intento/head y reutiliza receipt

#### Scenario: Foreign branch
- **WHEN** rama remota pertenece a otro intento
- **THEN** rechaza actualización y conserva rama

### Requirement: Side effect free preview

El producto SHALL ofrecer preview sin editar target, estado, configuración global ni sistemas remotos. Exportación explícita SHALL crear solo el plan externo solicitado mediante creación exclusiva.

#### Scenario: Preview snapshot
- **WHEN** se solicita preview sin exportación
- **THEN** conserva snapshots y no ejecuta escritura o autenticación

#### Scenario: Existing export destination
- **WHEN** el destino de exportación existe o está enlazado
- **THEN** rechaza sin sobrescribir o redirigir archivos

#### Scenario: Preview with deferred evaluations
- **WHEN** está habilitada la implementación local de 07 y evaluaciones de 06 siguen pendientes
- **THEN** permite preview sin efectos, informa el gate de publicación blocked y conserva las evaluaciones en not_run/blocked
