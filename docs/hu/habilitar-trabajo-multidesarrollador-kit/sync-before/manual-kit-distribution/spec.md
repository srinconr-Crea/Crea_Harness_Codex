# manual-kit-distribution Specification

## Purpose

Permitir la evolución del kit manual Crea con entregas independientes y verificables, preservando las distribuciones anteriores y las personalizaciones de proyectos consumidores sin depender del motor Python histórico.

## Requirements

### Requirement: Separate versioned manual kit candidate

La siguiente entrega SHALL prepararse en un árbol versionado nuevo a partir del kit vigente, conservando intactos árboles, ZIP, manifiestos y hashes anteriores. SHALL identificar fuente mantenida, composición y salidas de empaquetado. MUST NOT presentar componentes del motor histórico como capacidades instaladas del kit sin conexión comprobada.

#### Scenario: Prepare next release after approval
- **WHEN** se autoriza implementar la evolución de 0.1.4
- **THEN** prepara un staging nuevo y empaquetador dirigido a esa versión sin ejecutar scripts de autoría que muten 0.1.4

#### Scenario: Planning only
- **WHEN** se solicita únicamente esta propuesta OpenSpec
- **THEN** crea solo artefactos del cambio y no modifica plantillas, código, distribuciones, ramas, sistemas remotos ni estado estable del producto

### Requirement: Reviewed compatible adoption

Las extensiones nuevas de configuración SHALL ser opcionales para proyectos anteriores y comenzar en modo informativo cuando se adopten. La migración SHALL mostrar diferencias y preservar reglas, perfiles, evidencia e intentos existentes. MUST NOT afirmar que herramientas antiguas aceptan contratos nuevos ni sobrescribir personalizaciones automáticamente.

#### Scenario: Existing version one project config
- **WHEN** un proyecto 0.1.4 omite reglas y transiciones nuevas
- **THEN** los adaptadores nuevos conservan el flujo anterior sin exigir handoffs retroactivos; la adopción de nuevas secciones requiere actualizar conjuntamente schema y consumidores

#### Scenario: Personalized profiles conflict
- **WHEN** la actualización encuentra reglas o perfiles propios modificados
- **THEN** presenta una combinación revisable y conserva ambos antecedentes hasta resolución, sin reemplazo silencioso

### Requirement: Proportionate local verification and honest limits

La entrega SHALL comprobar contratos, transiciones válidas/inválidas, regresión de plan/run/gate, integridad del paquete y preservación de upstream/licencias. SHALL distinguir pruebas sintéticas de piloto real y capacidades remotas. El modo de inspección SHALL carecer de efectos sobre cliente, remoto y configuración global salvo salida de informe expresamente elegida.

#### Scenario: Local tests pass without remote pilot
- **WHEN** pasan las pruebas locales y no se ha ejecutado una HU real o runtime remoto
- **THEN** informa ese límite sin certificar agentes nativos, despliegues, Spark ni permisos del cliente

#### Scenario: Inspection without report output
- **WHEN** se inspecciona una transición sin indicar destino de informe
- **THEN** devuelve el diagnóstico sin crear archivos, ejecutar pruebas, instalar dependencias, publicar o corregir contratos

#### Scenario: Explicit report destination already exists
- **WHEN** se solicita guardar un informe en una ruta ocupada o fuera del expediente autorizado
- **THEN** rechaza esa escritura sin sobrescribir evidencia ni redirigir el destino

### Requirement: Portable tooling release preserves customized source

La nueva distribución SHALL derivar del árbol vigente 0.1.5 conservando su prompt y cambios locales previamente existentes. SHALL registrar los hashes de entrada y mantener intactos árboles, ZIP, manifiestos y hashes anteriores. MUST NOT regenerar versiones históricas para producir la nueva entrega.

#### Scenario: Source differs from published manifest
- **WHEN** 0.1.5 tiene modificaciones locales o un prompt nuevo respecto a su manifiesto original
- **THEN** registra esa diferencia como baseline de entrada, incorpora su contenido en el nuevo candidato y comprueba que no alteró esos bytes de origen

### Requirement: Consistent portable setup documentation

README, guía de inicio, prompt de configuración, inventario y documentación de extensiones SHALL describir la misma selección Databricks, estados de hooks y matriz Azure DevOps. El prompt SHALL comprobar versiones/ayuda y duplicados sin reinstalación global implícita ni ampliar alcance remoto. SHALL formar parte del manifiesto de la nueva entrega.

#### Scenario: Configure project from bundled prompt
- **WHEN** se usa el prompt de configuración de la nueva versión
- **THEN** conserva los campos y restricciones vigentes e identifica selección portable, activación opcional de hooks y lecturas Boards exclusivas de Planner/Reviewer

#### Scenario: Repository README links the candidate
- **WHEN** se entrega el candidato nuevo
- **THEN** README raíz y LEEME identifican su versión, prompt y límites reales sin presentar la planificación o los hooks incluidos como implementación o activación comprobadas

### Requirement: Verify tooling changes without remote mutation

La validación SHALL cubrir unicidad/procedencia, dependencias, contratos, compatibilidad Windows, matriz de operaciones y evidencia de lecturas con dobles. SHALL comprobar preservación de versiones previas y coherencia árbol/ZIP. MUST NOT ejecutar escrituras remotas, login o pipelines para satisfacer estas pruebas.

#### Scenario: Offline verification passes
- **WHEN** pasan casos sintéticos y validación de empaquetado
- **THEN** informa verificación local y mantiene separadas las lecturas reales o ejecuciones nativas de hooks aún no observadas

#### Scenario: Preview distribution adoption
- **WHEN** se inspecciona adoptar la distribución sin salida de informe explícita
- **THEN** no modifica cliente, fuentes históricas, sistemas remotos ni configuración global
