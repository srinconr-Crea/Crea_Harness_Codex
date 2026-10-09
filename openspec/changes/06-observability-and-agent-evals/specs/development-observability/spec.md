# Spec Delta

## Purpose

Actividad por HU/rol y consumo observado con procedencia y alcance. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Attributed activity

El producto SHALL registrar eventos por cliente/HU/intento/rol con timestamps, source e idempotency key y redactar secretos.

#### Scenario: Duplicate event
- **WHEN** llega el mismo evento dos veces
- **THEN** lo cuenta una vez conservando procedencia

#### Scenario: Sensitive payload
- **WHEN** un evento contiene credenciales
- **THEN** omite/redacta valores y conserva diagnóstico

### Requirement: Observed usage only

Tokens/costos SHALL conservar alcance y fuente soportada; valores no expuestos SHALL ser null con motivo. MUST NOT atribuir cuotas de cuenta, texto estimado o costos API como facturación Desktop.

#### Scenario: Supported per-session usage
- **WHEN** fuente documentada devuelve uso con asociación comprobada
- **THEN** registra valores/unidades y alcance real

#### Scenario: Unavailable usage
- **WHEN** solo existe cuota global o no hay fuente soportada
- **THEN** registra null/unavailable y conserva métricas de actividad
