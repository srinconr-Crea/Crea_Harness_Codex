# evaluation-catalog Specification

## Purpose

Casos sintéticos y rúbricas separados de resultados y ejecutores. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## Requirements

### Requirement: Independent evaluation cases

El producto SHALL validar casos sintéticos con rol, tarea, input, checks, oráculo independiente, criticidad y versión. SHALL distinguir tests del kit, pruebas de una HU y evals de agentes.

#### Scenario: Valid cases
- **WHEN** se carga el catálogo de fixtures con IDs únicos
- **THEN** todos los casos resuelven sus datos, reglas y modo de ejecución

#### Scenario: Broken references
- **WHEN** un caso refiere fixture/check/regla inexistente
- **THEN** devuelve invalid sin lanzar agentes

### Requirement: No fabricated outcomes

Los casos SHALL comenzar como not_run y MUST NOT incluir scores de ejecución inventados. Un expected es un oráculo y no un resultado observado.

#### Scenario: Unexecuted catalog
- **WHEN** solo existen definiciones de casos
- **THEN** el reporte los identifica como diseñados y not_run

#### Scenario: Missing runtime
- **WHEN** se necesita Spark o Desktop no certificado
- **THEN** la ejecución queda blocked y no se considera aprobada

### Requirement: Golden and holdout split

El catálogo SHALL separar casos golden y holdout, fijar hashes y criterios de promoción. SHALL incluir defectos conocidos, controles limpios, ambigüedad y fallos de herramienta.

#### Scenario: Regression case
- **WHEN** un auditor omite un defecto crítico conocido
- **THEN** el check determinista falla aunque el texto parezca convincente

#### Scenario: Clean control
- **WHEN** un candidato limpio no contiene el defecto evaluado
- **THEN** penaliza hallazgos falsos según la rúbrica
