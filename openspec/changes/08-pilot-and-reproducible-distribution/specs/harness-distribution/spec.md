# Spec Delta

## Purpose

Instalación/versionado/update/recover preservando configuración. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Reproducible installation

Distribución SHALL fijar versiones/hashes/licencias y distinguir dependencias, configuración, login y confianza. Plugin SHALL activar solo capacidades certificadas.

#### Scenario: Clean Windows machine
- **WHEN** faltan herramientas y usuario usa launcher
- **THEN** guía preparación con pasos revisables y pendientes explícitos

#### Scenario: Unsupported plugin capability
- **WHEN** plugin no distribuye agente/Python requerido
- **THEN** usa mecanismo separado revisado o informa unsupported

### Requirement: Personalization-preserving updates

Update SHALL comparar installed/upstream/local hashes, producir plan explícito y conservar backups/ownership. MUST NOT sobrescribir personalizaciones o borrar estado del desarrollador.

#### Scenario: Unmodified managed file
- **WHEN** existe actualización y hash local coincide instalado
- **THEN** presenta/aplica reemplazo revisado con backup

#### Scenario: Locally modified file
- **WHEN** cambia archivo gestionado respecto del instalado
- **THEN** marca conflicto y conserva contenido hasta resolución

### Requirement: Reversible verified release

Release SHALL incluir certificados y evals exigidos; recover SHALL restaurar solo recursos propios intactos y preservar estado/evidencia.

Un paquete candidato SHALL distinguir implementación local de aceptación real. Con evidencias requeridas de 06/07 u 08 not_run/blocked, SHALL conservar certified=false y release_allowed=false sin alterar los gates de publicación existentes.

#### Scenario: Accepted release
- **WHEN** pasan pruebas y evals requeridos en segundo entorno
- **THEN** distribuye manifiesto de resultados reales y limitaciones

#### Scenario: Modified post-update file
- **WHEN** archivo cambió después de actualizar
- **THEN** recuperación reporta conflicto sin sobrescribir

#### Scenario: Candidate with pending acceptance
- **WHEN** el código y las pruebas locales están completos pero faltan certificados, evals reales o protocolos remotos requeridos
- **THEN** permite preparar el paquete candidato con pendientes explícitos y bloquea su certificación y release

### Requirement: Side effect free preview

El producto SHALL ofrecer preview sin editar target, estado, configuración global ni sistemas remotos. Exportación explícita SHALL crear solo el plan externo solicitado mediante creación exclusiva.

#### Scenario: Preview snapshot
- **WHEN** se solicita preview sin exportación
- **THEN** conserva snapshots y no ejecuta escritura o autenticación

#### Scenario: Existing export destination
- **WHEN** el destino de exportación existe o está enlazado
- **THEN** rechaza sin sobrescribir o redirigir archivos
