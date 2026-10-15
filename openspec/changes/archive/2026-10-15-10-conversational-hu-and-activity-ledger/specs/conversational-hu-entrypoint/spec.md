# Spec Delta

## Purpose

Permitir iniciar y reanudar HU desde una Skill en el chat que reutiliza la preparación del cliente y conduce el ciclo existente con aprobaciones y evidencia verificables.

## ADDED Requirements

### Requirement: Reuse prepared client from chat

La Skill `harness-hu` SHALL resolver el runtime y binding vigentes, aceptar una HU en texto o referencia explícita, preguntar solo decisiones faltantes y producir un plan legible junto a los contratos de máquina requeridos. MUST NOT exigir al usuario crear manualmente JSON intermedios en el recorrido habitual.

#### Scenario: Prepared client and new story
- **WHEN** el usuario invoca la Skill con una historia y preparación válida
- **THEN** reutiliza las selecciones locales y propone criterios, rutas, validaciones y límites de la HU sin repetir setup

#### Scenario: Unprepared or foreign checkout
- **WHEN** la preparación falta o el binding no corresponde al checkout
- **THEN** bloquea el inicio y guía hacia setup o selección correcta sin adoptar permisos de otro cliente

### Requirement: Native supervised coordination

La integración SHALL definir en AGENTS.md instrucciones del coordinador de Codex para los roles configurados, comprobar capacidades necesarias y conducir comandos de HU existentes. SHALL conservar revisiones/aprobaciones ligadas a hashes, rutas autorizadas, un escritor por rutas compartidas y límite de correcciones. MUST NOT declarar agentes ejecutados o revisiones independientes sin evidencia real.

#### Scenario: Valid plan approval
- **WHEN** el operador aprueba la revisión vigente y sus capacidades están comprobadas
- **THEN** conduce implementación, validación y revisión dentro del alcance y evidencia del ciclo existente

#### Scenario: Missing delegation or isolation
- **WHEN** falta delegación nativa o una fase exige aislamiento no disponible
- **THEN** registra la capacidad ausente y bloquea esa fase, ofreciendo únicamente alternativas supervisadas compatibles y explícitas

#### Scenario: Candidate changed after validation
- **WHEN** cambia una ruta, política o candidato relevante después de aprobar o validar
- **THEN** invalida autorización o evidencia afectada y exige la revisión vigente sin declarar cierre/publicación

### Requirement: Persistent recovery and honest completion

La Skill SHALL reanudar desde estado persistido, revalidar identidad y reconciliar operaciones pendientes antes de repetir efectos. SHALL presentar estados local/remoto/revisión/publicación independientes y mantener los gates históricos existentes.

#### Scenario: New chat after interruption
- **WHEN** se solicita continuar una HU interrumpida desde otro chat sobre el mismo checkout
- **THEN** lee el estado y evidencia persistidos, identifica la próxima acción válida y no exige repetir todo el setup

#### Scenario: Remote unavailable and local checks successful
- **WHEN** las pruebas locales pasan y falta validación remota exigida
- **THEN** informa éxito local y bloqueo remoto sin marcar la HU lista para publicar

#### Scenario: Conversational preview
- **WHEN** se pide plan o diagnóstico sin autorizar mutaciones
- **THEN** no inicializa una HU, escribe bases, modifica código ni publica recursos
