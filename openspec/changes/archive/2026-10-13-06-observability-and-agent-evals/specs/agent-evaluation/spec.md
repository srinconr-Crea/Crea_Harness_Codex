# Spec Delta

## Purpose

Ejecución repetible de evals, scorers y promoción de configuraciones. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Reproducible role evaluation

El runner SHALL fijar dataset/config/kit/modelo/esfuerzo/runtime/herramientas, guardar outputs y ejecutar tres repeticiones por caso/configuración para comparación.

#### Scenario: Reproducible batch
- **WHEN** se evalúan dos perfiles sobre mismo dataset/runtime
- **THEN** reporta métricas, varianza y condiciones comparables

#### Scenario: Wrong execution surface
- **WHEN** se evalúa en CLI para declarar Desktop
- **THEN** rechaza esa certificación y etiqueta alcance CLI

### Requirement: Critical regression gate

El gate SHALL exigir todos los checks críticos y al menos 90% de no críticos; not_run/blocked MUST NOT contar como aprobados. Juicio LLM opcional SHALL estar calibrado y no sustituir checks críticos.

#### Scenario: Critical miss
- **WHEN** una repetición omite defecto crítico
- **THEN** rechaza promoción aunque promedio total sea alto

#### Scenario: Incomplete batch
- **WHEN** falta una repetición requerida
- **THEN** no promueve y reporta pendiente

### Requirement: Sanitized manual and automatic modes

El runner SHALL soportar evaluación manual documentada en Desktop y automática solo cuando interfaz soportada exista; resultados SHALL conservar evidencia y redactar datos.

#### Scenario: Manual desktop protocol
- **WHEN** persona ejecuta caso con captura/artefactos y configuración verificable
- **THEN** registra modo manual y scores comprobables

#### Scenario: Missing automation
- **WHEN** no hay interfaz compatible para automatizar Desktop
- **THEN** no usa APIs internas ni instala motor alternativo silenciosamente
