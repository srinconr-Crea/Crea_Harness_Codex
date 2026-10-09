# Spec Delta

## Purpose

Aceptación end-to-end en Desktop con dos clientes y HU sintética. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: End-to-end desktop acceptance

Release SHALL exigir evidencia de usuario nuevo, dos clientes sintéticos aislados y HU hasta PR autorizado con roles/modelos/herramientas reales en Desktop.

#### Scenario: Two clients
- **WHEN** alpha y beta completan flujo con políticas distintas
- **THEN** evidencia demuestra ausencia de estado/aprobaciones cruzados

#### Scenario: Missing remote test
- **WHEN** prueba requerida del piloto queda blocked
- **THEN** no declara aceptación end-to-end

### Requirement: Restricted real client pilot

Piloto NaturaPet SHALL usar copia/alcance aprobado y datos/recursos sintéticos; MUST NOT modificar recursos reales ni llevar reglas de negocio al núcleo.

#### Scenario: Synthetic client pilot
- **WHEN** cliente autoriza HU pequeña y recursos aislados
- **THEN** conserva restricciones y publica solo resultado autorizado

#### Scenario: Real data requested by fixture
- **WHEN** un caso referencia catálogo productivo
- **THEN** bloquea operación y no convierte la referencia en permiso
