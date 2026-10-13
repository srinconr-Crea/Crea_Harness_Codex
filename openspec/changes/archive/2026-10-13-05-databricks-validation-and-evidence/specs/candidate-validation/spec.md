# Spec Delta

## Purpose

Validación por tecnología, ejecución sintética aislada y evidencia con identidad/hash. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Impact-based validation plan

El producto SHALL seleccionar validación estática, unit tests, semántica Spark/SQL e integración según tecnología/impacto y distinguir required/advisory.

#### Scenario: Python logic
- **WHEN** solo cambia función pura
- **THEN** exige pruebas de comportamiento apropiadas sin forzar job remoto irrelevante

#### Scenario: Delta behavior
- **WHEN** cambia lógica MERGE o runtime específico
- **THEN** exige prueba en entorno compatible y no la sustituye por parser SQL

### Requirement: Isolated execution identity

Código cliente SHALL ejecutarse en worker local aislado sin credenciales o sandbox Databricks seleccionado con identidad/resources explícitos. MUST NOT ejecutar en recursos reales del cliente por defecto.

#### Scenario: Authorized sandbox
- **WHEN** host/job/runtime/datos sintéticos cumplen selección/política
- **THEN** ejecuta solo ese plan de pruebas

#### Scenario: Wrong target
- **WHEN** perfil o destino no coincide
- **THEN** rechaza antes de ejecutar código o escribir recursos

### Requirement: Reconciled trustworthy evidence

La evidencia SHALL incluir candidato, revisión, práctica, runtime/datos, comando, estado y hash/identidad de resultado. Timeout ambiguo SHALL exigir reconciliación antes de repetir.

#### Scenario: Matching result
- **WHEN** resultado remoto corresponde a request/candidato/job
- **THEN** se acepta como evidencia observada

#### Scenario: Mismatched result
- **WHEN** resultado tiene hash/cliente/run incorrectos
- **THEN** se rechaza y candidato queda blocked/failed

### Requirement: Honest validation coverage

Parsing/lint, YAML offline y bundle validate SHALL informar alcance diferente. Una prueba requerida no ejecutada MUST NOT contar como passed.

#### Scenario: Offline YAML valid
- **WHEN** solo se comprueba sintaxis/configuración local
- **THEN** no afirma ejecución notebook ni validación remota

#### Scenario: Missing required runtime
- **WHEN** falta runtime Spark/Databricks exigido
- **THEN** marca blocked y gate rechaza candidato
