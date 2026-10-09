# client-configuration Specification

## Purpose

Separar la identidad portable de cada cliente, la política seleccionada por el operador y la configuración local del desarrollador para evitar mezclar permisos o datos entre repositorios.

## Requirements

### Requirement: Separate versioned configuration contracts

El producto SHALL reconocer contratos separados de descriptor cliente, política operativa y binding local, todos con `schema_version: 1`, y SHALL rechazar versiones desconocidas, campos no admitidos o valores inválidos antes de generar un plan.

#### Scenario: Valid configuration set
- **WHEN** los tres documentos cumplen sus esquemas versión 1
- **THEN** el producto devuelve sus identidades e integridad validadas sin persistir ni activar configuración

#### Scenario: Unsupported configuration
- **WHEN** un documento tiene una versión no soportada o un campo desconocido
- **THEN** el producto devuelve un error estructurado con documento y campo afectados, sin incluir su contenido completo

### Requirement: Explicit policy selection and integrity

El producto SHALL recibir la ruta de política mediante selección explícita del operador y SHALL comprobar su SHA-256 contra el binding. El descriptor y contenido del repositorio MUST NOT seleccionar por sí solos una política activa ni ampliar sus autorizaciones.

#### Scenario: Policy bytes changed
- **WHEN** los bytes de la política difieren del hash esperado del binding
- **THEN** el producto rechaza la configuración con `policy_hash_mismatch`

#### Scenario: Repository attempts to override policy
- **WHEN** el descriptor contiene permisos o un selector de política fuera de su esquema
- **THEN** el producto rechaza el campo y conserva como única fuente operativa la política explícita

### Requirement: Client and repository consistency

El producto SHALL comprobar que cliente, repositorio y rama base del descriptor y política coinciden, que el binding pertenece al mismo cliente y que su target corresponde al checkout seleccionado. SHALL comparar la identidad del remote `origin` local con el repositorio configurado sin contactar al proveedor Git.

#### Scenario: Matching HTTPS and SSH identities
- **WHEN** el remote usa HTTPS o SSH sin credenciales inline para el mismo repositorio GitHub configurado
- **THEN** la comprobación identifica el mismo repositorio sin depender del formato de transporte

#### Scenario: Cross-client binding
- **WHEN** el binding pertenece a otro cliente o checkout
- **THEN** el producto rechaza la configuración con `client_mismatch` o `target_mismatch`

#### Scenario: Wrong or missing origin
- **WHEN** `origin` no existe o identifica otro repositorio
- **THEN** el producto devuelve `origin_missing` o `repository_mismatch` y no produce un plan ejecutable

### Requirement: Bounded safe configuration inputs

El producto SHALL leer únicamente archivos regulares de configuración de hasta 128 KiB, sin enlaces simbólicos o junctions en sus rutas. SHALL rechazar YAML/JSON malformado, secretos reconocibles, rutas de política relativas que escapen mediante traversal y patrones de rutas de repositorio absolutos o con traversal. Los errores MUST NOT revelar credenciales o valores completos de entrada.

#### Scenario: Invalid configuration file
- **WHEN** un archivo excede el tamaño, es un enlace o contiene datos malformados
- **THEN** el producto devuelve un error de configuración acotado sin continuar con la planificación

#### Scenario: Embedded credentials
- **WHEN** un documento contiene campos de token, password, secret o private key, o valores reconocibles de clave privada/token
- **THEN** el producto rechaza el documento y redacta sus valores en todos los diagnósticos

### Requirement: Isolated proposed local state

El binding SHALL declarar una ubicación de estado que identifique cliente y checkout, externa al árbol de trabajo target. La validación SHALL comprobar dicha separación sin crear carpetas ni bases de datos.

#### Scenario: State location inside target
- **WHEN** el binding ubica el estado dentro del checkout o sin la separación cliente/checkout exigida
- **THEN** el producto devuelve `state_path_invalid` sin crear ni modificar esa ubicación
