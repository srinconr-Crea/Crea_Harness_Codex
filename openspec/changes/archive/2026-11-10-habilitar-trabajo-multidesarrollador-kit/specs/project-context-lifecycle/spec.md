# Spec Delta

## ADDED Requirements

### Requirement: Shared versioned context across independent checkouts

El kit SHALL reutilizar las fuentes canónicas versionadas de configuración, reglas, specs y documentación en cada checkout. SHALL identificar la revisión de las fuentes observadas y conservar contenido manual. MUST NOT duplicar contexto en un servicio central ni prometer sincronización automática de sesiones o ramas.

#### Scenario: Developer uses an older feature checkout
- **WHEN** la feature conserva una revisión anterior a la configuración incorporada al destino
- **THEN** identifica las revisiones y cambios pertinentes al analizar compatibilidad sin reemplazar automáticamente el contexto de la feature

### Requirement: Reverse consumer impact from existing component mappings

Cuando esté adoptado el mapa de contexto, el análisis entre HU SHALL reutilizar sus componentes y dependencias para identificar también consumidores afectados por cambios del destino. SHALL conservar dirección y motivo de cada relación, resolver ciclos y señalar desconocidos. MUST NOT alterar la selección legacy ni exigir un mapa duplicado.

#### Scenario: Producer changes in target
- **WHEN** el destino cambia un componente del que depende otro afectado por la HU
- **THEN** identifica el consumidor y sus documentos pertinentes usando las relaciones existentes sin requerir una segunda declaración de arquitectura

#### Scenario: Cyclic dependencies
- **WHEN** dos componentes dependen entre sí
- **THEN** el recorrido termina con selección estable, sin duplicados y con las relaciones relevantes identificadas

### Requirement: Reference scoped cross revision reading

La lectura de contexto entre revisiones SHALL respetar exclusiones, límites e identidad de fuentes en ambos estados. SHALL comparar solo documentos pertinentes y conservar las rutas excluidas en la observación Git. MUST NOT cargar historia ajena, secretos o documentación completa por disponibilidad.

#### Scenario: Shared specification changes on target
- **WHEN** el destino modifica una spec pertinente a la HU
- **THEN** referencia los estados de esa spec y requisitos afectados sin cargar todos los expedientes ni copiar sus requisitos al inventario

#### Scenario: Excluded target path changes
- **WHEN** cambia una ruta excluida de lectura contextual
- **THEN** conserva su presencia en el diff y registra el límite sin leer su contenido para intentar completar la inspección

### Requirement: Useful compatibility without context activation

El análisis SHALL funcionar con Git, catálogo y referencias disponibles cuando context_management esté ausente o desactivado, declarando la cobertura limitada de componentes y semántica. MUST NOT habilitar la extensión, completar un mapa ficticio ni interpretar falta de relaciones como independencia demostrada.

#### Scenario: Context extension disabled
- **WHEN** se solicita compatibilidad en un proyecto sin mapa adoptado
- **THEN** informa solapamientos, contratos y checks comprobables, declara relaciones no verificadas y conserva la configuración desactivada
