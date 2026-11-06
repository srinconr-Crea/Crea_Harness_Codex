# Spec Delta

## ADDED Requirements

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
