# onboarding-recovery Specification

## Purpose

Conservar evidencia local por cliente y checkout que permita detectar ejecuciones incompletas y recuperar solo sus creaciones intactas, sin borrar trabajo posterior del desarrollador.

## Requirements

### Requirement: External durable execution journal

Cada aplicación SHALL mantener registro versionado fuera del target, en el estado del binding, con identidad, hash del plan, operaciones previstas, resultados y hashes de archivos creados. SHALL distinguir `in_progress`, `completed`, `failed`, `recovered` y `recovery_conflict`; MUST NOT guardar credenciales ni activar SQLite.

#### Scenario: Failure after a file creation
- **WHEN** falla una operación tras crear un archivo identificado en el registro
- **THEN** se conserva evidencia suficiente para detectar la ejecución incompleta y proponer recuperación

#### Scenario: Ambiguous interrupted creation
- **WHEN** una interrupción deja un archivo cuya propiedad no puede probarse con el registro
- **THEN** se preserva y se informa revisión manual en lugar de asumir que puede borrarse

### Requirement: Exclusive checkout execution

Apply y recuperación SHALL usar exclusión mutua por cliente/checkout. Un segundo proceso SHALL rechazar una operación concurrente. Un lock huérfano SHALL requerir recuperación explícita y verificación de que el dueño no sigue activo; MUST NOT eliminar locks automáticamente por antigüedad solamente.

#### Scenario: Concurrent apply
- **WHEN** otro proceso mantiene la ejecución activa sobre el mismo checkout
- **THEN** el segundo informa `onboarding_locked` sin modificar el target

### Requirement: Conservative explicit recovery

`harness recover --path TARGET --policy FILE --run ID --dry-run`, con binding explícito existente o plan explícito validado que contenga el binding propuesto, SHALL mostrar acciones revisables; `--apply` SHALL revalidar identidad, política, rutas y registro y eliminar solo archivos cuya creación pertenece inequívocamente a esa ejecución y cuyo hash actual coincide. SHALL quitar únicamente directorios vacíos creados por esa ejecución. MUST NOT eliminar archivos preexistentes ni recorrer/borrar directorios recursivamente.

#### Scenario: Recover unchanged owned files
- **WHEN** el registro identifica archivos creados por esa ejecución y siguen intactos
- **THEN** se eliminan únicamente esas creaciones y se registra la recuperación

#### Scenario: Preserve developer changes
- **WHEN** el desarrollador modificó uno de los archivos después de la aplicación
- **THEN** ese archivo se conserva y se registra `recovery_conflict` con la revisión pendiente

#### Scenario: Recovery dry-run
- **WHEN** se solicita recuperación sin aplicar
- **THEN** se reportan acciones y conflictos sin cambiar target, binding, journal ni locks

### Requirement: Client isolation and sanitized outcomes

Los registros y recuperación SHALL mantenerse aislados por cliente/checkout y rechazar referencias externas o un registro de otro binding. Los reportes humano/JSON SHALL incluir operaciones efectivas, pendientes y conflictos con mensajes sanitizados; MUST NOT afirmar recuperación completa ante operaciones ambiguas.

#### Scenario: Foreign journal
- **WHEN** el registro corresponde a otro cliente, checkout o destino
- **THEN** se rechaza antes de borrar o crear cualquier archivo
