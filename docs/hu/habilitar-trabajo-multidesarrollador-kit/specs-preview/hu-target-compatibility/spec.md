# hu-target-compatibility Specification

## Purpose

Informar cómo afectan los cambios del destino del PR a una HU concurrente mediante evidencia Git y revisión funcional proporcionadas, manteniendo las decisiones de reconciliación e integración en el equipo.

## Requirements

### Requirement: Optional target compatibility observation

La compatibilidad SHALL ser opt-in y usar el destino efectivo del PR. Ausente o deshabilitada SHALL conservar el flujo anterior sin fabricar evidencia. Adoptada SHALL comenzar informativa y MUST NOT bloquear por mera divergencia ni activar condiciones de enforcement automáticamente.

#### Scenario: Legacy project omits compatibility
- **WHEN** un proyecto no configura esta capacidad
- **THEN** mantiene su flujo vigente y no exige informes retroactivos a sus HU

#### Scenario: Divergence alone
- **WHEN** quality contiene commits adicionales independientes de la HU
- **THEN** informa la divergencia sin convertir su existencia en conflicto o veto automático

### Requirement: Exact source and target anchors

La observación SHALL identificar repositorio, remoto, feature, base de nacimiento, candidato y SHA verificado del destino, conservando origen y base técnica por separado. SHALL distinguir una observación remota actual de una referencia local almacenada. MUST NOT resolver nombres ambiguos ni inventar ancestros.

#### Scenario: Stale tracking reference
- **WHEN** la referencia local apunta a Q1 y el destino remoto verificable apunta a Q2
- **THEN** no acredita compatibilidad actual con Q1 y solicita obtener o analizar el snapshot de Q2

#### Scenario: No common history or incomplete history
- **WHEN** no puede establecer la relación de historia necesaria por clon parcial, ancestros ausentes o historias no relacionadas
- **THEN** informa el análisis de historia como indeterminado y la recuperación concreta sin cambiar ramas ni forzar una base

### Requirement: Separate story target and inherited changes

El informe SHALL separar cambios propios de la HU, cambios relevantes del destino y cambios heredados de la rama base ausentes del destino. SHALL conservar bajas, renombres, conflictos y rutas compartidas. MUST NOT presentar todo el alcance del PR como autoría o autorización de la HU.

#### Scenario: Sprint contains unrelated work absent from quality
- **WHEN** la feature nace de una base con commits que quality todavía no contiene
- **THEN** enumera el alcance heredado y requiere decidir su inclusión antes de afirmar que el PR corresponde solo a la HU

### Requirement: Dependency and consumer impact

La observación SHALL relacionar las rutas afectadas con componentes, dependencias, consumidores, contratos, documentos y checks declarados disponibles. SHALL señalar huecos y límites sin inventar arquitectura. MUST NOT considerar independencia por la sola ausencia de archivos compartidos.

#### Scenario: A independent concurrent stories
- **WHEN** HU001 se integra primero en quality y HU002 modifica otro componente sin relación declarada o funcional afectada dentro del alcance revisado
- **THEN** HU002 puede obtener compatible y continuar sin exigir repetir pruebas por la mera divergencia

#### Scenario: B changed consumed component
- **WHEN** HU001 cambia un componente que consume HU002
- **THEN** identifica el consumidor, los contratos y checks que requieren revisión o nueva validación y conserva resultados locales que no acreditan esa combinación como tales

### Requirement: Semantic review independent of textual conflicts

La observación SHALL separar conflictos Git de contradicciones funcionales. Los hallazgos semánticos SHALL referenciar requisitos, reglas u oráculos y decisiones contrastables; Reviewer SHALL revisar los pertinentes. MUST NOT inferir compatibilidad funcional de un merge textual limpio o de hashes diferentes.

#### Scenario: C incompatible edits of one rule
- **WHEN** las HU cambian una misma especificación o regla con resultados incompatibles
- **THEN** registra conflicto funcional, referencias de ambos estados y reconciliación humana necesaria

#### Scenario: D contradictory contracts in different files
- **WHEN** productor y consumidor quedan con unidades o contratos incompatibles aunque Git pueda integrarlos sin conflicto
- **THEN** informa la contradicción funcional y no declara compatible basándose en la integración textual

#### Scenario: Same file with compatible changes
- **WHEN** ambas HU modifican un documento en partes independientes sin contradicción sustentada
- **THEN** registra el solapamiento para revisión proporcional sin etiquetarlo automáticamente como conflicto funcional

### Requirement: Isolated textual integration inspection

La comprobación textual SHALL usar los SHA observados y separar cálculo de integración de integración efectiva. MUST NOT modificar feature, destino, índice o árbol de trabajo del usuario, ejecutar código cliente ni resolver conflictos. Artefactos temporales SHALL permanecer aislados y fuera de publicación.

#### Scenario: Textual conflict is observed
- **WHEN** el cálculo aislado encuentra un conflicto de modificación, borrado o renombre
- **THEN** informa sus rutas y tipo, conserva el checkout del usuario y propone resolución humana

#### Scenario: Simulation capability is unavailable
- **WHEN** Git no soporta el mecanismo o no puede producir un resultado comprobable
- **THEN** declara esa dimensión indeterminada sin ejecutar un merge real como fallback

### Requirement: Actionable compatibility report

El informe SHALL separar outcome compatible, requires_review, conflict_detected o undetermined de coverage y freshness. SHALL incluir anclas, motivos, responsables, límites, checks propuestos y evidencia conservada. MUST NOT ocultar un conflicto conocido por otras comprobaciones incompletas ni equiparar compatible a garantía de corrección total.

#### Scenario: Known conflict with incomplete component mapping
- **WHEN** existe un conflicto Git comprobado pero parte del mapa está incompleta
- **THEN** conserva conflict_detected e informa cobertura parcial y análisis no completados

#### Scenario: Missing semantic coverage
- **WHEN** falta información material para decidir la compatibilidad funcional
- **THEN** informa undetermined o requires_review según la decisión identificable y no presenta una garantía funcional

### Requirement: Target freshness at PR preparation and creation

El principal SHALL contrastar el destino antes de presentar el PR y justo antes de crearlo o preparar su formulario. Un SHA cambiado SHALL marcar obsoleta la observación y exigir recalcular su impacto, sin invalidar automáticamente pruebas locales intactas. MUST NOT prometer actualidad posterior al instante observado.

#### Scenario: E target changes after first inspection
- **WHEN** el informe usa Q1 y antes del PR se observa Q2
- **THEN** marca stale, analiza Q2 y conserva evidencia/aprobaciones no afectadas, solicitando nueva decisión solo si cambian su contenido o alcance aplicables

#### Scenario: Target changes after creation
- **WHEN** quality avanza después de crear el PR
- **THEN** el recibo conserva su SHA y momento observados y deja revisión final y merge al proceso del equipo sin afirmar compatibilidad continua

### Requirement: Missing and unverifiable target handling

La adquisición SHALL distinguir rama inexistente, acceso denegado, error de red, respuesta ambigua y objetos no disponibles. Tales resultados SHALL producir indeterminación de lo no comprobado. MUST NOT crear quality, cambiar destino, equiparar error a ausencia ni usar caché como verificación remota actual.

#### Scenario: F target is missing
- **WHEN** una consulta correcta confirma que la rama destino no existe
- **THEN** informa destino ausente y acción al responsable sin crear la rama ni seleccionar otra

#### Scenario: F target cannot be accessed or verified
- **WHEN** falla la consulta por red, autenticación o permisos
- **THEN** informa verificación no realizada con su causa y permite trabajo local independiente autorizado sin declarar compatible

### Requirement: Preserve valid evidence without cross plan adoption

Los cambios del destino SHALL afectar primero a la observación de compatibilidad. Si alteran entradas, criterios o candidato, SHALL aplicarse la invalidación existente y un plan nuevo cuando corresponda. MUST NOT importar recibos entre planes, máquinas o árboles diferentes ni ejecutar suites desde el inspector.

#### Scenario: Unrelated target update
- **WHEN** Q2 no altera entradas ni contratos de la HU y su plan sigue vigente
- **THEN** renueva la observación sin relanzar suites o repetir autorizaciones intactas

#### Scenario: Combined behavior needs testing
- **WHEN** una dependencia cambiada exige comprobar código combinado
- **THEN** identifica checks y candidato necesario, sin afirmar que las pruebas ejecutadas solo en la feature validaron esa combinación

### Requirement: Human reconciliation and integration boundary

La salida SHALL proponer acciones concretas y conservar pendientes por continuación. MUST NOT ejecutar merge, rebase, cherry-pick, actualización resolutiva de ramas, auto-complete, deploy o promoción a test. Una actualización manual de la feature SHALL exigir reconciliar candidato, procedencia y evidencia sin reescribir intentos históricos.

#### Scenario: Developer manually resolves a conflict
- **WHEN** el equipo aporta una feature actualizada mediante una decisión externa al inspector
- **THEN** registra la nueva observación y contrasta base técnica, contenido, checks y autorizaciones afectados sin asumir equivalencia con el candidato anterior

### Requirement: Bounded inspection and immutable report export

El inspector SHALL operar sobre snapshots locales comprobables y devolver stdout sin escritura por defecto. Una exportación SHALL exigir destino nuevo permitido en la HU y rechazar enlaces, escapes o colisiones. Adquirir datos remotos o crear temporales para simulación SHALL ser operaciones explícitas separadas de la inspección pura.

#### Scenario: Pure inspection
- **WHEN** se inspeccionan snapshots existentes sin salida ni simulación
- **THEN** no escribe, contacta servicios, instala herramientas o ejecuta pruebas

#### Scenario: Existing output path
- **WHEN** el informe solicitado ya existe o apunta a evidencia primaria
- **THEN** rechaza la exportación y conserva los bytes existentes
