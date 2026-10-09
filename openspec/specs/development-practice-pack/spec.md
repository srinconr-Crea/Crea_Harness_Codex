# development-practice-pack Specification

## Purpose

Buenas prácticas versionadas por tecnología con procedencia y extensiones del cliente. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## Requirements

### Requirement: Traceable technology practices

El producto SHALL resolver prácticas por SQL, Python, notebook, PySpark, YAML/DABs y CI/CD con rule_id, versión, fuente, aplicabilidad y evidencia requerida. MUST NOT presentar recomendaciones condicionales de rendimiento como obligaciones universales.

#### Scenario: Applicable rule
- **WHEN** se selecciona una transformación PySpark
- **THEN** devuelve reglas aplicables y sus IDs sin reglas de un cliente distinto

#### Scenario: Unsupported recommendation
- **WHEN** se propone cache/broadcast sin medición o runtime compatible
- **THEN** la recomendación queda advisory y no se ejecuta ni certifica una mejora

### Requirement: Pinned third party resources

El producto SHALL comprobar commit, tamaño y SHA-256 de los archivos upstream y conservar LICENSE/NOTICE. MUST NOT ejecutar scripts, instalar globalmente ni activar conectores por cargar una Skill.

#### Scenario: Intact snapshot
- **WHEN** los archivos corresponden al manifiesto fijado
- **THEN** el paquete identifica fuente y licencia con integridad comprobada

#### Scenario: Altered resource
- **WHEN** falta o cambia un archivo requerido
- **THEN** rechaza el paquete antes de instalarlo o aplicarlo

### Requirement: Reviewed client extensions

El producto SHALL componer base y extensión cliente con precedencia explícita, registrar excepciones técnicas y bloquear ampliaciones de permisos operativos.

#### Scenario: Stricter client rule
- **WHEN** el cliente exige pruebas adicionales compatibles
- **THEN** las añade al plan efectivo conservando IDs/fuentes

#### Scenario: Policy bypass
- **WHEN** una extensión pide editar rutas prohibidas o saltar aprobación
- **THEN** rechaza la ampliación y conserva la política
