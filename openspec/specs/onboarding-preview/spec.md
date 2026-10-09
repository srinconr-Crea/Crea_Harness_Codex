# onboarding-preview Specification

## Purpose

Permitir revisar un plan concreto de incorporación de un cliente sobre un checkout existente antes de habilitar escrituras, instalaciones o autenticaciones del futuro onboarding.

## Requirements

### Requirement: Preview-only onboarding command

`harness init --dry-run` SHALL aceptar un checkout existente y política/binding explícitos, validar identidad y producir un plan. Invocar `harness init` sin `--dry-run` en esta versión SHALL devolver `apply_not_supported` con código 2 y sin efectos laterales.

#### Scenario: Valid onboarding preview
- **WHEN** el checkout y las configuraciones cumplen las validaciones
- **THEN** el comando devuelve acciones propuestas y comprobaciones pendientes sin aplicar ninguna

#### Scenario: Missing target
- **WHEN** la carpeta target no existe o no es un checkout Git
- **THEN** el comando devuelve `target_not_found` o `not_git_checkout`, sin crearla ni clonar

### Requirement: Preview for prepared and unprepared clients

El plan SHALL distinguir archivos/configuraciones `proposed`, `existing`, `conflict` y acciones `manual`. Para un cliente sin descriptor SHALL permitir `--repo` y `--base-branch` explícitos como datos del descriptor propuesto, sujetos a la política; MUST NOT inferir permisos ni rama base desde la conversación.

#### Scenario: Client without descriptor
- **WHEN** falta `.harness/client.yaml` y se proporcionan identidad y rama base válidas
- **THEN** el plan incluye el descriptor propuesto con contenido revisable y hash, sin escribirlo

#### Scenario: Descriptor identity unavailable
- **WHEN** falta el descriptor y no se proporcionan datos explícitos suficientes
- **THEN** el comando devuelve `descriptor_input_required` sin inventar valores

#### Scenario: Existing project instructions
- **WHEN** el target contiene un `AGENTS.md` personalizado
- **THEN** el plan lo preserva y presenta una integración manual como `conflict`, sin sobrescribir ni afirmar que se fusionó

### Requirement: Preserve client-specific specifications

El plan SHALL reutilizar OpenSpec existente y las Skills compatibles, y SHALL proponer preparación únicamente para los elementos ausentes. Los siete workflows requeridos son explore, propose, update, apply, verify, sync y archive. MUST NOT incluir reglas de negocio o recursos concretos de otro cliente en las propuestas genéricas.

#### Scenario: Prepared client
- **WHEN** OpenSpec y las siete Skills compatibles ya existen
- **THEN** el plan marca esos elementos como `existing` y no propone reinicializarlos

#### Scenario: Divergent managed artifact
- **WHEN** un artefacto existente es incompatible o distinto del esperado por el kit
- **THEN** el plan informa `conflict` y exige revisión sin proponer sustitución automática

### Requirement: Deterministic structured preview

El comando SHALL ofrecer salida humana y JSON con `schema_version`, `command`, `status`, identidades, hashes de entrada, `actions` y `checks`. Cada acción SHALL incluir tipo, ruta cuando aplique, motivo y contenido/hash cuando el kit pueda determinar el archivo propuesto. Con los mismos datos de entrada SHALL producir el mismo plan semántico sin fechas o identificadores aleatorios. SHALL devolver 0 para plan sin bloqueos, 1 para conflictos/preparación incompleta y 2 para entrada inválida.

#### Scenario: Repeated preview
- **WHEN** el comando se ejecuta dos veces con el mismo checkout/configuración
- **THEN** devuelve el mismo plan semántico y conserva sin cambios los archivos y estado local

### Requirement: No local or remote onboarding effects

El preview MUST NOT escribir en target, estado local o configuración global, instalar, clonar, registrar bindings, autenticar, invocar modelos, ejecutar pruebas del cliente, ejecutar jobs, desplegar o publicar en GitHub. Las operaciones futuras o no autorizadas SHALL aparecer únicamente como acciones manuales o propuestas.

#### Scenario: Snapshot unchanged
- **WHEN** se compara el target, configuración global y ubicación de estado antes y después de un preview
- **THEN** no hay archivos creados/modificados/eliminados ni llamadas remotas realizadas por el comando
