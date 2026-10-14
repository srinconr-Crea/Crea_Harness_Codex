# pilot-certification Specification

## Purpose

Aceptación end-to-end en Desktop con dos clientes y HU sintética. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## Requirements

### Requirement: End-to-end desktop acceptance

Release SHALL exigir evidencia de usuario nuevo, dos clientes sintéticos aislados y HU hasta PR autorizado con roles/modelos/herramientas reales en Desktop.

SHALL exigir además cierre verificado de las dependencias de aceptación de 06/07. La autorización para desarrollar 08 con esas dependencias pendientes SHALL permitir implementación y pruebas locales, sin satisfacer aceptación, certificar release ni habilitar el siguiente incremento.

#### Scenario: Two clients
- **WHEN** alpha y beta completan flujo con políticas distintas
- **THEN** evidencia demuestra ausencia de estado/aprobaciones cruzados

#### Scenario: Missing remote test
- **WHEN** prueba requerida del piloto queda blocked
- **THEN** no declara aceptación end-to-end

#### Scenario: Local development before predecessor acceptance
- **WHEN** existe autorización de desarrollo anticipado y la base de 07 está implementada, pero sus evaluaciones o protocolos de aceptación siguen pendientes
- **THEN** permite avanzar código y pruebas locales con pendientes registrados, manteniendo bloqueadas certificación, release y habilitación del siguiente incremento

#### Scenario: Manual pilot does not certify harness publication
- **WHEN** una HU se prueba en sandbox y su PR draft se publica mediante Git/Codex con autorización de piloto, sin recorrer los gates y la reconciliación del harness
- **THEN** conserva esa evidencia como antecedente y mantiene pendiente la aceptación del recorrido de publicación/reanudación del harness

### Requirement: Restricted real client pilot

Piloto NaturaPet SHALL usar copia/alcance aprobado y datos/recursos sintéticos; MUST NOT modificar recursos reales ni llevar reglas de negocio al núcleo.

#### Scenario: Synthetic client pilot
- **WHEN** cliente autoriza HU pequeña y recursos aislados
- **THEN** conserva restricciones y publica solo resultado autorizado

#### Scenario: Real data requested by fixture
- **WHEN** un caso referencia catálogo productivo
- **THEN** bloquea operación y no convierte la referencia en permiso
