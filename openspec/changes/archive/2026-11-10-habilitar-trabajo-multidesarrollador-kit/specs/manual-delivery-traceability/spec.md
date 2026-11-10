# Spec Delta

## ADDED Requirements

### Requirement: Independent feature origin and PR target

La entrega SHALL crear features desde project.base_branch y resolver el destino mediante delivery.pr_target_branch opcional. Ausente o null SHALL usar project.base_branch como antes. SHALL conservar el remoto configurado y la política por proveedor. MUST NOT inferir un destino distinto desde defaults globales.

#### Scenario: Sprint source and quality target
- **WHEN** la base es sprint/XX y el destino separado es quality
- **THEN** prepara la feature desde el SHA remoto de sprint/XX y presenta o crea el PR autorizado hacia quality

#### Scenario: Legacy destination fallback
- **WHEN** no se declara destino separado
- **THEN** conserva project.base_branch como origen de feature y destino del PR sin exigir migración de HU históricas

### Requirement: Verified Git delivery provenance

La entrega SHALL validar nombres, repositorio, remoto, referencias exactas y SHA reales antes de crear la feature y publicar. SHALL conservar base de nacimiento y base técnica sin confundirlas con el destino. MUST NOT usar referencias ambiguas, caché no verificada o errores remotos como evidencia de rama libre.

#### Scenario: Feature name collision
- **WHEN** la feature propuesta ya existe local o remotamente y no pertenece a la HU reanudada
- **THEN** no la reutiliza ni sobrescribe y propone otro nombre identificable antes de escribir

#### Scenario: Custom fetch refspec
- **WHEN** el fetch no actualiza la referencia de seguimiento esperada
- **THEN** resuelve y contrasta la referencia correcta y su SHA antes de crear la feature sin asumir que el nombre local está vigente

### Requirement: Protected development and publication branches

El perfil de equipo SHALL impedir desarrollo o push de HU directamente sobre la base, el destino del PR, quality, test y las ramas protegidas configuradas. SHALL comprobar rama actual y ref de push efectiva. MUST NOT cambiar protecciones del servidor ni usar force-push para resolver colisiones.

#### Scenario: Requested feature equals protected target
- **WHEN** el nombre de la feature coincide con quality, test, la base o una rama protegida
- **THEN** rechaza preparar o publicar esa rama e informa la alternativa de feature

#### Scenario: Branch changes before push
- **WHEN** la rama actual o destino efectivo difiere de la feature autorizada
- **THEN** no ejecuta el push y conserva el trabajo local sin switch, reset o stash automático

### Requirement: Reviewed effective PR scope

La entrega SHALL distinguir los commits propios desde la base y el alcance efectivo hacia el destino. Los cambios heredados ausentes del destino SHALL presentarse para decisión antes de autorizar su inclusión. MUST NOT ampliar publication_paths ni atribuir commits ajenos a la HU para satisfacer un verificador.

#### Scenario: Base is ahead of target
- **WHEN** sprint/XX contiene trabajo adicional que quality no contiene
- **THEN** presenta ese alcance separado y mantiene pendiente su publicación como parte de la HU hasta resolver la autorización aplicable

#### Scenario: Approved independent story only
- **WHEN** el destino contiene la base y el rango publicable pertenece a la HU aprobada
- **THEN** publica solo el alcance revisado sin bloquear por otros commits independientes presentes en el destino

### Requirement: Canonical target bound authorization

El destino resuelto SHALL contrastarse con evidence.delivery.target_branch, el contenido presentado, su digest y la lectura posterior del PR. Cambiar destino, contenido o alcance aprobados SHALL requerir la autorización afectada. MUST NOT repetir una autorización completa vigente ni ampliar por esta opción las operaciones del proveedor.

#### Scenario: Target changed after human approval
- **WHEN** la configuración cambia el destino del PR aprobado de quality a otra rama
- **THEN** no crea ese PR usando la aprobación anterior y presenta el nuevo destino y contenido para decisión

#### Scenario: Existing provider policies
- **WHEN** se entrega una HU con destino independiente y aprobaciones vigentes
- **THEN** Azure DevOps Services usa su CLI autorizada y verificación posterior; GitHub y Server conservan formulario/borrador, sin merge, auto-complete, pipelines o promoción
