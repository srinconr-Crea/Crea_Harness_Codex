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
