# Spec Delta

## MODIFIED Requirements

### Requirement: Portable tooling release preserves customized source

La nueva distribución SHALL derivar del árbol vigente 0.1.8 conservando su contexto y ciclo de pruebas, prompt y personalizaciones verificadas. SHALL registrar hashes de entrada y mantener intactos árboles, ZIP, manifiestos y hashes anteriores. MUST NOT regenerar versiones históricas para producir la entrega nueva.

#### Scenario: Source differs from published manifest
- **WHEN** la fuente 0.1.8 tiene modificaciones locales respecto a su manifiesto original
- **THEN** registra esa diferencia como baseline de entrada, conserva las personalizaciones y comprueba que no alteró los bytes de origen

#### Scenario: One new candidate for the whole change
- **WHEN** se implementan los incrementos internos de este cambio
- **THEN** todos se incorporan a un candidato nuevo identificado, con comprobación de preservación histórica y sin candidatos paralelos por cada mejora

### Requirement: Consistent portable setup documentation

README, LEEME, guías, prompt e inventario SHALL distinguir versión vigente, origen e historia y describir coherentemente A inicial, B actualización y C preparación personal. SHALL conservar selección Databricks, hooks opcionales y límites Azure. El prompt SHALL integrar el manifiesto de distribución, aunque no se copie al cliente.

#### Scenario: Configure project from bundled prompt
- **WHEN** se usa la sección A de la nueva distribución
- **THEN** conserva campos y restricciones, identifica selección portable y hooks opcionales y configura el proyecto sin ejecutar B o C como onboarding adicional

#### Scenario: Repository README links the candidate
- **WHEN** se entrega el candidato nuevo
- **THEN** README y LEEME identifican versión, prompt y límites reales sin presentar planificación o hooks incluidos como implementación o activación comprobadas

#### Scenario: Update an existing project with section B
- **WHEN** se actualiza un proyecto anterior hacia el candidato nuevo
- **THEN** B identifica versión origen y destino, compara distribución/proyecto/fuente verificable y preserva setup, modelos, reglas, catálogo, specs y evidencia mediante diff

#### Scenario: Prepare another developer with section C
- **WHEN** la persona elige C sobre un clon configurado
- **THEN** ejecuta la entrada local equivalente sin repetir A, actualizar el kit ni reinicializar OpenSpec

#### Scenario: Correct stale 0.1.8 version references
- **WHEN** se corrigen encabezados o la sección B heredada de 0.1.8
- **THEN** publica fe de erratas y contenido corregido en el candidato nuevo sin alterar hashes históricos ni renombrar revisiones upstream o cifras de pruebas anteriores

## ADDED Requirements

### Requirement: Explicit client installation composition

La distribución SHALL declarar qué se copia al cliente, qué queda solo en distribución y qué se conserva localmente, con motivos y consumidores comprobados. SHALL preservar recursos operativos, licencias, procedencia y validación. MUST NOT eliminar archivos solo para reducir volumen ni depender del motor histórico para operar el kit.

#### Scenario: Copy clean operational kit
- **WHEN** el onboarding instala el kit en un proyecto nuevo
- **THEN** usa la composición revisada, conserva AGENTS, skills, perfiles, schemas, guías, scripts y recursos necesarios, y no copia archivos reservados al empaquetador

#### Scenario: Existing project already tracks distribution files
- **WHEN** un cliente antiguo versiona archivos que la composición nueva deja fuera
- **THEN** propone una migración explícita por archivo, referencias e inventario sin borrarlos ni retirarlos del índice automáticamente

### Requirement: Preserve validation and provenance surfaces

El perfil cliente inicial SHALL conservar tests/crea, manifest original como procedencia y una guía de validación con alcance real. SHALL distinguir pruebas internas de pruebas de negocio. MUST NOT regenerar el manifest para declarar idéntico al ZIP un proyecto personalizado ni ejecutar pruebas internas como suite de negocio por defecto.

#### Scenario: Personalized project validation
- **WHEN** se valida un proyecto configurado
- **THEN** usa validación personalizada sin original, conserva procedencia y no exige que sus bytes coincidan con toda la distribución

#### Scenario: Internal tests remain available
- **WHEN** se requiere verificar una adaptación local de herramientas del kit
- **THEN** las regresiones internas permanecen disponibles y separadas del catálogo de negocio salvo incorporación explícita revisada

### Requirement: Initial local exclusions without hidden changes

El onboarding SHALL combinar exclusiones de entornos, cachés, secretos, binding personal, diagnósticos y temporales desde la instalación inicial. SHALL preservar reglas existentes y excepciones pertinentes. MUST NOT ignorar globalmente archivos operativos, documentación funcional, OpenSpec o expedientes de evidencia requeridos.

#### Scenario: First clone after onboarding
- **WHEN** otra persona crea su entorno, binding y diagnóstico locales
- **THEN** las exclusiones versionadas ya impiden su incorporación accidental sin pedir configurar manualmente nuevos patrones

#### Scenario: Required evidence uses log files
- **WHEN** una HU produce logs declarados como recibos obligatorios
- **THEN** las exclusiones no los descartan por una regla global de extensión y se conserva su revisión y publicación aplicables

### Requirement: Separate copy context ignore and publication controls

La composición, .gitignore, exclusiones de contexto y alcance explícito de publicación SHALL tener efectos distintos documentados y comprobables. Un archivo excluido del contexto SHALL seguir visible al control Git si cambia. MUST NOT usar gitignore para retirar archivos ya rastreados ni git add general para publicar.

#### Scenario: Already tracked local file
- **WHEN** una ruta personal ya versionada coincide con una exclusión nueva
- **THEN** advierte que sigue rastreada y propone retirada revisada sin ejecutar git rm automáticamente

#### Scenario: Excluded contextual content changes
- **WHEN** cambia un archivo que no debe leerse como contexto
- **THEN** conserva su detección para alcance y publicación sin leer o incorporar su contenido por esa coincidencia

### Requirement: Compatible reviewed team adoption and rollback

La adopción SHALL actualizar conjuntamente schemas, configuración y consumidores en un punto acordado, preservando modelos, reglas, context/lifecycle y expedientes. SHALL admitir omisión de opciones nuevas y reversión conjunta con historia conservada. MUST NOT habilitar servicios, capacidades, pipelines o permisos al actualizar.

#### Scenario: Older reader accepts an unknown project field
- **WHEN** un schema antiguo permite una propiedad que su consumidor no implementa
- **THEN** la preparación no declara soporte por validación sintáctica y exige verificar consumidores compatibles antes de usar la opción

#### Scenario: Rollback after new HU evidence exists
- **WHEN** se revierte la adopción al conjunto anterior
- **THEN** restaura herramientas/configuración compatibles, conserva evidencia nueva como historia no consumida y no migra recibos hacia atrás ni desactiva gates para aprobar
