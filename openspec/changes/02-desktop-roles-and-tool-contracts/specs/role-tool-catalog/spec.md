# Spec Delta

## Purpose

Roles, modelos, esfuerzos y herramientas requeridas/opcionales versionados. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Versioned role responsibilities

El catálogo SHALL definir principal, analyst, impact-analyzer, planner, developer, tester, auditor y verifier con entradas, salidas, rutas asignadas y criterios de delegación.

#### Scenario: Small story
- **WHEN** la HU tiene análisis acotado
- **THEN** el principal puede resolver fases sin lanzar todos los roles

#### Scenario: Writer collision
- **WHEN** dos assignments del kit incluyen la misma ruta de escritura
- **THEN** rechaza el segundo o requiere aislamiento

### Requirement: Explicit model and effort

Cada perfil activado SHALL seleccionar modelo y esfuerzo soportados y registrar configuración efectiva. MUST NOT degradar silenciosamente si falta el modelo.

#### Scenario: Available configuration
- **WHEN** modelo y esfuerzo superan comprobación Desktop
- **THEN** el rol usa esa configuración y conserva evidencia

#### Scenario: Unavailable model
- **WHEN** el modelo fijado no está disponible
- **THEN** bloquea ese rol e informa remedio sin sustituirlo

### Requirement: Capabilities and effective permissions

Cada rol SHALL declarar herramientas required/optional y su propósito; configuración efectiva y permisos SHALL verificarse separadamente de instrucciones. Hooks SHALL registrar cobertura real.

#### Scenario: Missing required tool
- **WHEN** falta el conector requerido para esa fase
- **THEN** la fase queda blocked sin invocar alternativas no seleccionadas

#### Scenario: Read-only reviewer
- **WHEN** la instrucción dice read-only pero permisos efectivos permiten escritura
- **THEN** no certifica restricción efectiva y exige resolver configuración
