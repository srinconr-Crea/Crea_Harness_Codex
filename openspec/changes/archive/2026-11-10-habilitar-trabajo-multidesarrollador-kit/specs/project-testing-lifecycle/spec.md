# Spec Delta

## ADDED Requirements

### Requirement: Optional local execution environment resolution

El catálogo y configuración permanente SHALL poder compartirse sin rutas personales de intérprete cuando se adopte el binding local. Plan, run y gate SHALL resolver el mismo entorno efectivo y conservar huellas de intérprete y dependencias. MUST NOT aceptar cambios locales de comandos, assertions, obligaciones o salidas revisadas.

#### Scenario: Two machines share one execution configuration
- **WHEN** dos checkouts usan la misma configuración versionada y bindings de Python diferentes
- **THEN** cada uno planifica y ejecuta con su intérprete comprobado sin editar execution.json y obtiene evidencia ligada a su entorno efectivo

#### Scenario: Local interpreter changes after planning
- **WHEN** cambia el intérprete efectivo o una dependencia funcional del entorno
- **THEN** el gate detecta la invalidación aplicable y no conserva passed por igualdad de código

#### Scenario: Legacy absolute interpreter
- **WHEN** no se adopta binding y existe un intérprete absoluto configurado
- **THEN** conserva la resolución y comprobaciones anteriores sin exigir configuración personal nueva

### Requirement: Catalog based target impact recommendations

El análisis del destino SHALL proponer checks del catálogo vigente mediante relaciones de inputs, criterios, contratos y consumidores, con motivo y procedencia. MUST NOT crear un catálogo paralelo, ejecutar suites al inspeccionar ni registrar automáticamente requisitos nuevos para aprobar la HU.

#### Scenario: Changed dependency affects an unchanged test
- **WHEN** un cambio del destino altera una entrada declarada de un check consumidor de la HU
- **THEN** identifica ese check y la entrada afectada aunque el archivo de prueba permanezca igual

#### Scenario: Target references an unknown check
- **WHEN** una recomendación depende de un check que no existe en el catálogo vigente de la feature
- **THEN** informa mantenimiento o decisión pendiente sin inventar un comando ni declarar la validación realizada

### Requirement: Distinct feature and combined candidate evidence

Los resultados SHALL identificar el candidato realmente ejecutado. Pruebas de la feature MUST NOT acreditar un árbol combinado con el destino que no se ejecutó. Una nueva validación SHALL reutilizar plan/run/gate sobre un candidato autorizado, conservando intentos previos sin adopción cruzada.

#### Scenario: Local feature passed before provider contract changed
- **WHEN** las pruebas de HU002 pasaron en su feature y quality cambió el contrato que consume
- **THEN** conserva ese resultado histórico y solicita los checks pertinentes sobre el candidato adecuado sin afirmarlos pasados contra quality

#### Scenario: New plan after manual integration
- **WHEN** el equipo prepara manualmente otro candidato para validar la combinación
- **THEN** registra su base técnica y procedencia reales y produce plan y recibos nuevos sin reutilizar los del candidato anterior

### Requirement: Selective rechecking within existing guarantees

Una observación del destino sin cambio en entradas locales SHALL conservar pruebas vigentes y limitarse a revisar compatibilidad. Cambios funcionales SHALL usar la invalidación y selección existentes, sin relajar su identidad global ni activar reutilización entre planes. Reviewer MUST NOT repetir suites por rutina.

#### Scenario: Informational report reference corrected
- **WHEN** se corrige una referencia de compatibilidad sin cambiar obligaciones ni entradas funcionales
- **THEN** revalida el contrato y conserva recibos vigentes sin ejecutar pruebas

#### Scenario: Required runtime remains inactive
- **WHEN** una incompatibilidad requiere ejecución Spark o remota sin adaptador activo autorizado
- **THEN** conserva blocked y no sustituye esa ejecución por mocks, simulación Git o sintaxis
