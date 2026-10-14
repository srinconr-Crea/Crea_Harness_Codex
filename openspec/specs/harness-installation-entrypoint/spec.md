# harness-installation-entrypoint Specification

## Purpose

Instalar el runtime del harness y exponer su entrada conversacional antes de preparar un cliente, con procedencia, alcance de usuario y recuperación verificables.

## Requirements

### Requirement: Single command user installation

El producto SHALL proporcionar un comando documentado de instalación para Windows x64 que prepare un runtime aislado y una entrada invocable, reutilice herramientas compatibles y obtenga dependencias faltantes desde fuentes/versiones/hashes aprobados. SHALL separar instalación del producto, configuración de cliente, login y confianza. MUST NOT modificar herramientas globales ni instalar Codex implícitamente.

#### Scenario: Machine without product runtime
- **WHEN** un operador con Codex y PowerShell disponibles ejecuta el comando y autoriza el plan de instalación
- **THEN** prepara el runtime y entrada de usuario sin exigir que instale previamente Python, y entrega versiones, rutas y comprobaciones

#### Scenario: Missing network or unsupported platform
- **WHEN** falta acceso al artefacto fijado o la plataforma no está soportada
- **THEN** informa el bloqueo y alternativa offline cuando exista, sin sustituir versiones ni afirmar instalación completa

#### Scenario: Installation preview
- **WHEN** se invoca el modo preview sin exportación explícita
- **THEN** muestra alcance, fuentes y conflictos sin descargar, escribir, autenticar ni registrar recursos

### Requirement: Setup skill discoverable before client preparation

La instalación SHALL registrar una Skill genérica `harness-setup` en un ámbito de descubrimiento soportado por el host y comprobar por separado recurso instalado y descubrimiento observado en Codex. SHALL permitir invocarla sin checkout cliente preparado y MUST NOT copiar reglas de negocio o credenciales al ámbito de usuario.

#### Scenario: First invocation
- **WHEN** no hay cliente preparado y Codex descubre la Skill instalada
- **THEN** el operador puede iniciar setup desde el chat y la Skill resuelve el runtime registrado sin depender del directorio actual

#### Scenario: Resource installed but not discovered
- **WHEN** el recurso está presente pero el host no confirma su descubrimiento
- **THEN** informa skill_discovery_pending e instrucciones de recarga/comprobación sin declarar la experiencia lista

### Requirement: Owned reversible installation

El instalador SHALL registrar ownership, hashes y etapas; reutilizar sin duplicar una instalación intacta; preservar recursos ajenos o personalizados; recuperar únicamente recursos propios intactos y conservar estado/evidencias de clientes. SHALL mantener los gates de release existentes.

#### Scenario: Modified skill or occupied destination
- **WHEN** una ruta de instalación contiene recursos ajenos o modificaciones locales
- **THEN** presenta conflicto y no sobrescribe ni elimina esos recursos

#### Scenario: Interrupted installation
- **WHEN** falla una descarga o se interrumpe una etapa
- **THEN** conserva un diagnóstico por etapa y permite reanudar o recuperar sin declarar éxito ni borrar datos de clientes

#### Scenario: Candidate with historical gates pending
- **WHEN** se instala explícitamente un candidato para prueba y faltan evaluaciones requeridas
- **THEN** mantiene certified=false y release_allowed=false y muestra que instalar no equivale a certificar
