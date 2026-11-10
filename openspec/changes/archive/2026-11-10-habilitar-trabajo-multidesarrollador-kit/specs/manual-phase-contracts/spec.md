# Spec Delta

## ADDED Requirements

### Requirement: Session scoped sequential roles

El flujo de equipo SHALL mantener roles secuenciales y un escritor por archivo dentro de cada checkout/HU. Las sesiones independientes SHALL compartir contexto por revisiones Git sin un coordinador central ni bloqueos globales. MUST NOT afirmar coordinación o autoría entre máquinas que la evidencia local no acredita.

#### Scenario: Independent developers work concurrently
- **WHEN** dos personas ejecutan HU diferentes en checkouts independientes
- **THEN** cada sesión conserva su secuencia y expedientes sin esperar un turno global ni modificar la sesión de la otra persona

### Requirement: Canonical compatibility reference

Los handoffs adoptados SHALL referenciar el informe de compatibilidad con identidad y hash comprobables, conservando informes e intentos anteriores. Las vistas humanas SHALL derivar de esa referencia. MUST NOT duplicar su estado, modificar un informe para aparentar vigencia ni tratar documentos funcionales como metadata descartable.

#### Scenario: New target observation after a handoff
- **WHEN** se produce otra observación del destino sin cambio funcional de la HU
- **THEN** un intento nuevo referencia el nuevo informe y conserva los anteriores y la evidencia técnica que sigue vigente

### Requirement: Informative compatibility transition consumption

Las transiciones SHALL consumir resultado, cobertura y vigencia sin convertir divergencia, aviso o error del inspector en veto global. SHALL conservar gates y aprobaciones previos, y representar reconciliaciones necesarias como decisiones humanas por continuación. Un bloqueo nuevo SHALL requerir promoción explícita y casos comprobados.

#### Scenario: Informative inspection error
- **WHEN** el inspector no puede completar una dimensión y las restricciones previas están satisfechas
- **THEN** registra indeterminación y acciones sin inventar passed o detener automáticamente todo el trabajo independiente

#### Scenario: Critical contradiction needs a decision
- **WHEN** el PR depende de reconciliar una regla funcional contradictoria
- **THEN** registra la decisión pendiente y su responsable mediante el mecanismo existente sin interpretar una repetición de pruebas como esa decisión

#### Scenario: Missing real destination
- **WHEN** el destino no existe o no puede acreditarse para crear el PR
- **THEN** conserva el pendiente de entrega por destino no comprobado, aunque la inspección informativa no agregue un veto nuevo al trabajo local

### Requirement: Scoped invalidation and unchanged approvals

Las transiciones SHALL distinguir una nueva observación del destino de un cambio en candidato, criterios, política, entorno o paquete autorizado. SHALL conservar evidencia y autorizaciones intactas y revalidar solo lo afectado mediante contratos existentes. MUST NOT reiniciar max_fix_rounds, reetiquetar recibos o pedir permisos por cada transferencia.

#### Scenario: Only target snapshot changes independently
- **WHEN** cambia el snapshot de quality pero no el contenido, alcance ni las entradas de la HU
- **THEN** actualiza compatibilidad en un nuevo intento y revalida referencias sin relanzar suites ni pedir la misma aprobación

#### Scenario: Functional candidate changes during reconciliation
- **WHEN** resolver una incompatibilidad modifica código, reglas, criterios o entradas funcionales
- **THEN** conserva los intentos previos y remite candidato y autorizaciones afectados a planificación, pruebas y revisión aplicables

### Requirement: Non circular compatibility evidence binding

La incorporación de informes de compatibilidad SHALL usar una equivalencia explícita y acotada para derivados, sin debilitar el candidato técnico ni permitir publicar bytes distintos de los revisados. Un informe que añada requisitos u obligaciones funcionales SHALL requerir reconciliar el plan. MUST NOT excluir una carpeta completa del gate para evitar circularidad.

#### Scenario: Informational report added after testing
- **WHEN** se añade un informe previsto que solo observa el destino y no cambia obligaciones funcionales
- **THEN** conserva la identidad técnica mediante la regla exacta adoptada y comprueba por separado sus bytes publicables y referencias

#### Scenario: Report introduces a new required check
- **WHEN** el análisis requiere una nueva obligación técnica aceptada para el candidato
- **THEN** reconcilia el plan mediante el mecanismo existente y no la oculta como actualización de metadata
