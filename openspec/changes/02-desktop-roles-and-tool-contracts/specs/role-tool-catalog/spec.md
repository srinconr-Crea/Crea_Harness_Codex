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

### Requirement: Supervised reviewer acceptance

El producto SHALL distinguir prohibición de editar por instrucciones de restricción efectiva del sandbox. Cuando el aislamiento falle, SHALL permitir únicamente revisión supervisada aceptada explícitamente por el operador para un cliente/checkout, catálogo, candidato y versión de evidencia identificados. SHALL comparar contenido y rutas del candidato antes/después, bloquear aceptación ante drift y conservar el conflicto de permisos. MUST NOT presentar esta detección como prevención de escritura ni certificación read-only.

#### Scenario: Supervised review with intact candidate
- **WHEN** el operador acepta las limitaciones observadas y el candidato permanece intacto tras la revisión
- **THEN** registra revisión supervisada sin certificar aislamiento ni habilitar fases que lo requieran

#### Scenario: Reviewer changes candidate
- **WHEN** la comparación detecta cambios, creaciones o eliminaciones en el candidato revisado
- **THEN** rechaza la aceptación, conserva diferencias/evidencia y no revierte silenciosamente

#### Scenario: Missing or stale operator acceptance
- **WHEN** falta aceptación o corresponde a otro cliente, checkout, catálogo, candidato o evidencia
- **THEN** bloquea revisión supervisada hasta obtener aceptación válida

## MODIFIED Requirements

### Requirement: Capabilities and effective permissions

Cada rol SHALL declarar herramientas required/optional y su propósito; configuración efectiva y permisos SHALL verificarse separadamente de instrucciones. Hooks SHALL registrar cobertura real.

#### Scenario: Missing required tool
- **WHEN** falta el conector requerido para esa fase
- **THEN** la fase queda blocked sin invocar alternativas no seleccionadas

#### Scenario: Read-only reviewer
- **WHEN** la instrucción dice read-only pero permisos efectivos permiten escritura
- **THEN** registra conflict y no certifica restricción efectiva; exige resolverla para fases que requieran aislamiento, o aceptación explícita del modo supervisado para fases que lo admitan
