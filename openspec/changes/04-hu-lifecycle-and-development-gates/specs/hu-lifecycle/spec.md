# Spec Delta

## Purpose

Estado por HU/intento, aprobación de plan y gates de candidato con recuperación. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Revision-bound human approval

El producto SHALL persistir HU/intento/revisión/manifiesto y aprobación explícita de actor vinculada a hash/cliente/checkout. Cambio relevante SHALL invalidar aprobación.

#### Scenario: Approved plan
- **WHEN** el operador aprueba revisión vigente
- **THEN** habilita implementación dentro de ese manifiesto

#### Scenario: Changed scope
- **WHEN** se añade una ruta/criterio o cambia política relevante
- **THEN** vuelve a planned y exige aprobación vigente

### Requirement: Candidate-bound gates

El producto SHALL calcular candidato incluyendo archivos nuevos/eliminados y enlazar pruebas/revisión a hash exacto. Evidencia stale, simulada o not_run MUST NOT habilitar publicación.

#### Scenario: Same candidate
- **WHEN** todas las pruebas requeridas pertenecen al hash actual
- **THEN** permite pasar el gate de validación

#### Scenario: Edited candidate
- **WHEN** cambia código tras las pruebas
- **THEN** invalida evidencia y bloquea cierre/publicación

### Requirement: Bounded work and recovery

El flujo SHALL limitar a dos correcciones por intento, un escritor por rutas compartidas y delegaciones configuradas. Reanudación SHALL revalidar estado, identidad y operaciones pendientes.

#### Scenario: Infrastructure failure
- **WHEN** la herramienta no está disponible
- **THEN** registra blocked_reason sin consumir corrección de código ni marcar passed

#### Scenario: Interrupted attempt
- **WHEN** un proceso termina antes de confirmar operación
- **THEN** reconcilia estado sin asumir éxito ni duplicar efectos

### Requirement: Scoped enforcement

Los gates SHALL controlar comandos/adaptadores del kit; MUST NOT afirmar cobertura total de herramientas Desktop solo por AGENTS, Skills o hooks.

#### Scenario: Bypass detected
- **WHEN** aparece diff fuera del manifiesto por edición externa
- **THEN** el gate lo rechaza y registra evidencia

#### Scenario: Missing covered event
- **WHEN** un hook no cubre una herramienta
- **THEN** informa el límite y exige permisos externos para garantías adicionales
