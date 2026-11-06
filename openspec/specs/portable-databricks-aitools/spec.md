# portable-databricks-aitools Specification

## Purpose

Distribuir y mantener una selección de Databricks AI Tools dentro del kit portable, con procedencia reproducible, dependencias completas y hooks opcionales cuya activación y cobertura sean comprobables.

## Requirements

### Requirement: Reproducible portable skill selection

El kit SHALL incluir las skills Databricks seleccionadas con revisión upstream inmutable, hashes, licencias y decisión de inclusión. SHALL actualizar las existentes por identidad y conservar adaptaciones locales documentadas. MUST NOT requerir una instalación global o un segundo plugin para disponer de esas mismas skills.

#### Scenario: Update existing skill
- **WHEN** una skill existente tiene una revisión oficial nueva aprobada para el candidato
- **THEN** sustituye su copia en la nueva distribución, registra procedencia y diferencias y conserva la distribución anterior

#### Scenario: Official source unavailable
- **WHEN** no puede recuperar o verificar la revisión seleccionada
- **THEN** informa la selección pendiente y no presenta una mezcla incompleta como actualización verificada

### Requirement: Unique active identities and closed dependencies

La selección SHALL contener una sola implementación activa por nombre y resolver referencias obligatorias a archivos y skills. SHALL justificar las incorporaciones por capacidad o dependencia. La adopción MUST NOT sobrescribir skills personalizadas ni activar capacidades por mera disponibilidad.

#### Scenario: Missing skill referenced by included guidance
- **WHEN** una skill seleccionada requiere otra ausente
- **THEN** incorpora su dependencia o informa una limitación revisada que impide declarar completa esa capacidad

#### Scenario: Client already has a different skill revision
- **WHEN** el cliente ya contiene una skill del mismo nombre con diferencias
- **THEN** muestra el conflicto y conserva ambas procedencias sin instalar dos implementaciones activas ni sobrescribir la personalización

### Requirement: Optional native hook integration

El kit SHALL incluir los tres hooks oficiales y sus recursos requeridos, distinguiendo incluido, configurado, autorizado y observado. La activación SHALL usar una superficie nativa documentada compatible con el host y autorización aplicable. MUST NOT considerar una entrada declarativa o una prueba sintética como ejecución nativa real.

#### Scenario: Compatible host and authorized activation
- **WHEN** el host soporta los eventos y se autoriza la configuración propuesta
- **THEN** configura únicamente esa integración, conserva hooks previos y registra resultado y cobertura observados por evento

#### Scenario: Unsupported host or shell
- **WHEN** no se comprueba compatibilidad del host, intérprete o sintaxis en Windows
- **THEN** conserva los recursos incluidos, informa integración no verificada y mantiene utilizable el kit sin hooks activos

### Requirement: Advisory hooks preserve workflow authority

Los hooks SHALL aportar solo contexto, enrutamiento y avisos de autenticación, sin sustituir al orquestador, autorizar acciones ni iniciar login automático. SHALL conservar su comportamiento tolerante a fallos y documentar sus efectos locales. MUST NOT atribuir captura de evidencia de HU a estos hooks sin un mecanismo observado independiente.

#### Scenario: Authentication failure hint
- **WHEN** un resultado genera una sugerencia de autenticación
- **THEN** presenta el aviso sin iniciar login ni cambiar perfil, permisos o alcance de la HU

#### Scenario: Hook fails
- **WHEN** un hook falla o no produce contexto
- **THEN** el flujo conserva sus gates y selección explícita de skills sin declarar cobertura inexistente

### Requirement: Side effect free adoption preview

La inspección de actualización SHALL mostrar selección, duplicados, conflictos e integración prevista sin instalar, autenticar, activar hooks ni modificar cliente o configuración global. Exportar el informe SHALL exigir destino explícito nuevo dentro del alcance autorizado.

#### Scenario: Preview without output
- **WHEN** se inspecciona el estado de adopción sin destino de informe
- **THEN** devuelve las diferencias y pendientes sin modificar archivos del cliente ni configuración nativa
