# local-activity-ledger

## Purpose

Conservar y consultar actividad local atribuible al harness en SQLite, con importación idempotente, procedencia y cobertura que distingue actividad observada de consumo no disponible.

## Requirements

### Requirement: Initialize isolated durable activity store

El producto SHALL crear un almacén SQLite de actividad durante setup autorizado, fuera del repositorio y separado por cliente/checkout, conservando la base existente del ciclo HU. SHALL versionar su esquema y preservar datos ante reanudación, actualización y recuperación.

#### Scenario: First authorized setup
- **WHEN** se completa setup con estado local válido
- **THEN** la base de actividad existe antes de la primera HU y su consulta distingue actividad de setup de actividad de HU sin inventar consumo

#### Scenario: Two clients and existing HU state
- **WHEN** se preparan dos clientes o se añade el almacén a un cliente existente
- **THEN** sus informes permanecen aislados y la base del ciclo HU conserva estados y evidencia

### Requirement: Automatically record own operations

Los comandos mutantes y ejecutores propios SHALL registrar inicio y resultado con identificador estable, cliente/checkout, HU/intento/rol cuando corresponda, timestamps, duración observada, revisión/candidato, fuente y resultado. SHALL redactar secretos, acotar payloads e informar fallos de persistencia sin afirmar trazabilidad completa. Eventos previos a la HU SHALL conservar alcance de setup sin asignar HU ficticia.

#### Scenario: Successful or failed validation
- **WHEN** una validación se ejecuta mediante el kit
- **THEN** el informe muestra su resultado, duración y candidato real, incluyendo fallos sin contarlos como passed

#### Scenario: Duplicate replay and interrupted operation
- **WHEN** llega el mismo evento otra vez o un proceso termina sin resultado confirmado
- **THEN** cuenta el evento una vez y conserva la operación como incompleta hasta reconciliarla

#### Scenario: Busy or unavailable database
- **WHEN** no se puede persistir tras el límite acotado de espera
- **THEN** informa ledger_unavailable antes de iniciar una mutación nueva o deja una operación ya iniciada pendiente de reconciliación sin inventar un resultado

### Requirement: Query and export observed activity

El producto SHALL consultar por cliente/checkout/HU/intento/rol y rango temporal, mostrar duraciones, operaciones, resultados y cobertura, y exportar reportes mediante destino explícito. Consulta y preview SHALL ser de solo lectura, sin crear bases faltantes ni contaminar sus propios conteos.

#### Scenario: Report after resume
- **WHEN** se consulta una HU reanudada
- **THEN** agrega operaciones deduplicadas y distingue duraciones completas, incompletas y eventos importados

#### Scenario: Missing database or occupied export
- **WHEN** no existe el almacén o el destino de exportación ya existe
- **THEN** informa el diagnóstico correspondiente sin crear estado ni sobrescribir archivos

### Requirement: Supported usage and coverage only

El almacén SHALL persistir consumo solo con fuente soportada, unidades, alcance y asociación comprobable, usando null y motivo para tokens/costos no expuestos. SHALL distinguir imported, harness_commands y hooks observados. MUST NOT convertir cuotas globales, estimaciones de texto o costos de otra plataforma en consumo facturado de Codex Desktop.

#### Scenario: No attributable Desktop usage source
- **WHEN** no existe fuente soportada asociable a la HU
- **THEN** devuelve tokens/costos null con motivo y conserva el informe de actividad propia

#### Scenario: Valid import and wrong scope
- **WHEN** se importa consumo documentado asociado a una sesión o se recibe un evento de otro cliente
- **THEN** conserva el alcance real y deduplica el primero, y rechaza atribuir el segundo al cliente/HU consultado

### Requirement: Optional trusted host integration

La captura adicional mediante hooks SHALL usar únicamente eventos/payloads documentados y disponibles en el host y activación confiada por el usuario. SHALL conservar actividad propia sin hooks y declarar cobertura parcial para acciones no observadas. MUST NOT leer bases internas de Codex ni tratar hooks como frontera de seguridad.

#### Scenario: Hooks unavailable or untrusted
- **WHEN** el host no ofrece hooks compatibles o no se han confiado
- **THEN** continúa registrando comandos propios y muestra native_actions_not_observed sin afirmar captura completa

#### Scenario: Supported observed hook
- **WHEN** un hook autorizado entrega un evento documentado con asociación validada
- **THEN** lo registra como fuente separada e idempotente y conserva las limitaciones de cobertura
