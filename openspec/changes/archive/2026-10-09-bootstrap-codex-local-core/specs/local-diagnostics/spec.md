# Spec Delta

## Purpose

Ofrecer al desarrollador un diagnóstico local verificable del equipo y del repositorio antes de intentar incorporar un cliente, sin afirmar conectividad o capacidades de Desktop no comprobadas.

## ADDED Requirements

### Requirement: Local tool readiness report

`harness doctor` SHALL informar disponibilidad y versión observada de Python, Git, Node, OpenSpec y Databricks CLI mediante comprobaciones locales acotadas. SHALL distinguir `ready`, `missing`, `unsupported`, `error` y `not_checked`, aplicando una matriz versionada del kit.

#### Scenario: Tool absent
- **WHEN** una herramienta requerida no está disponible
- **THEN** el informe la marca `missing`, explica cómo resolverlo y continúa con las comprobaciones independientes

#### Scenario: Slow or unrecognized version probe
- **WHEN** una sonda supera el timeout o devuelve una versión no interpretable
- **THEN** el informe registra `error` sin bloquear indefinidamente ni instalar la herramienta

### Requirement: Desktop capability verification remains explicit

El diagnóstico SHALL tratar descubrimiento de Skills, selección de agentes/modelos y cobertura de hooks en Desktop como `not_checked` cuando solo hay evidencia de archivos o versión del CLI. MUST NOT presentar autenticación o acceso Databricks como verificados sin una prueba remota autorizada, ausente en este incremento.

#### Scenario: Local configuration files exist
- **WHEN** doctor encuentra archivos Codex pero no se ha realizado una prueba en la aplicación
- **THEN** informa su presencia y deja las capacidades de ejecución Desktop como `not_checked`

### Requirement: Target readiness and optional configuration validation

`harness doctor --path <target>` SHALL comprobar que existe un checkout Git, informar rama/estado local, existencia de OpenSpec y Skills de los siete workflows. SHALL distinguir archivos ausentes de presentes pero incompatibles y preservar archivos existentes. Con política y binding explícitos SHALL incluir la validación de configuración cliente.

#### Scenario: Verify workflow absent
- **WHEN** el target tiene OpenSpec pero no la Skill `openspec-verify-change`
- **THEN** doctor informa preparación incompleta y la acción recomendada, sin generar archivos

#### Scenario: Configuration inputs not supplied
- **WHEN** doctor se ejecuta sin política y binding
- **THEN** reporta las herramientas y estructura disponibles y marca validación operativa como `not_checked`

### Requirement: Stable output and exit semantics

Doctor SHALL ofrecer salida humana y JSON con `schema_version`, `command`, `status` y `checks`, incluyendo códigos y mensajes sanitizados. SHALL devolver 0 sin fallos comprobados, 1 ante falta/incompatibilidad/error de una comprobación y 2 ante invocación o configuración inválida. Los estados `not_checked` MUST NOT interpretarse como verificación exitosa.

#### Scenario: Partial diagnosis
- **WHEN** hay comprobaciones correctas y una herramienta ausente
- **THEN** el JSON conserva todos los resultados y el proceso termina con código 1

### Requirement: Read-only diagnostic execution

Doctor MUST NOT instalar dependencias, clonar, modificar archivos, autenticar, consultar recursos remotos ni escribir estado persistente. SHALL ejecutar sondas con argumentos separados, timeout y sin shell interpolado; las lecturas Git SHALL deshabilitar actualizaciones opcionales del índice.

#### Scenario: Diagnosis without credentials
- **WHEN** se ejecuta doctor en un equipo sin login Databricks o GitHub
- **THEN** el diagnóstico local termina sin solicitar login y sin llamadas de red
