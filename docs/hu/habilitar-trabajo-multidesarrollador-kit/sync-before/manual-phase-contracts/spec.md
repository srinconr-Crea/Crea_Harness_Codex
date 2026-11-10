# manual-phase-contracts Specification

## Purpose

Hacer comprobables las transferencias del kit manual Crea mediante contratos por transición, con alcance de escritura y evidencia vinculados al candidato, sin añadir fases o ejecutar pruebas durante la validación del contrato.

## Requirements

### Requirement: One phase aware handoff contract

El kit SHALL conservar handoffs por HU, fase e intento bajo un schema base versionado con identidad, resultado, alcance/candidato, contexto, evidencia, pendientes y continuación. Los requisitos SHALL depender de la transición y los IDs externos o de agente SHALL ser nulos cuando no existan. Los intentos anteriores MUST NOT sobrescribirse.

#### Scenario: Planning has no execution results
- **WHEN** Planner entrega criterios, alcance y plan de validación antes de Apply
- **THEN** exige esas referencias y no resultados de pruebas aún no ejecutadas

#### Scenario: Tester hands over evidence
- **WHEN** Tester entrega ready_for_review
- **THEN** exige referencias contrastables a plan, candidato y recibos de los checks requeridos, sin aceptar passed por declaración

#### Scenario: Single session or local story
- **WHEN** no existe ID de Boards o ejecución de subagente
- **THEN** conserva identidad local y campos externos nulos, sin simular delegación

### Requirement: Deterministic transition inspection

Antes de continuar, el principal SHALL invocar una comprobación local de identidad, campos por transición, referencias, vigencia, alcance, autorización y bloqueos pertinentes. Esta SHALL reutilizar la validación técnica existente y MUST NOT ejecutar suites, decidir corrección funcional por JSON válido o interceptar herramientas globalmente.

#### Scenario: Required evidence is stale
- **WHEN** el candidato cambió después de las pruebas
- **THEN** consume el diagnóstico del gate existente y remite a selección/revalidación de checks, sin iniciar pruebas desde el validador

#### Scenario: Tool dependency unavailable
- **WHEN** no puede leer Git o cargar el validador de schemas
- **THEN** informa error del validador y comprobaciones no realizadas, sin atribuir incumplimiento ni emitir un pase técnico

### Requirement: Gradual explicit enforcement

El principal SHALL consumir código, modo e informe sin tratar todo código no cero como veto global. En modo informativo las condiciones nuevas SHALL informar sin añadir bloqueos; errores MUST NOT acreditar validez. Aprobaciones, restricciones y gates existentes SHALL seguir vigentes. Bloqueos nuevos SHALL habilitarse solo por configuración explícita aprobada para condiciones objetivas comprobadas con casos válidos e inválidos.

#### Scenario: Informative pilot
- **WHEN** una HU representativa presenta una omisión descriptiva del handoff
- **THEN** informa la corrección sin bloquear automáticamente una transición ya autorizada y técnicamente válida

#### Scenario: Informative validator error does not add a veto
- **WHEN** el nuevo validador devuelve código 4 durante el piloto informativo y los controles previamente obligatorios están satisfechos
- **THEN** el principal registra el error y qué no pudo comprobarse, sin detener automáticamente toda la HU ni afirmar que la comprobación pasó

#### Scenario: Unreadable informative report
- **WHEN** falta el informe o no puede leerse durante el piloto informativo
- **THEN** conserva resultado indeterminado y comprueba las restricciones existentes con sus mecanismos actuales, sin convertir el error por sí solo en veto ni asumir aprobaciones o gates satisfechos

#### Scenario: Existing approval missing
- **WHEN** el modo es informativo pero no existe la nueva solicitud humana de Apply
- **THEN** el flujo conserva la detención existente y no usa el modo informativo para implementarlo

#### Scenario: Existing required gate still blocks
- **WHEN** el nuevo validador está en modo informativo pero un gate técnico previamente obligatorio falla o no puede acreditarse
- **THEN** mantiene la detención de la continuación dependiente por esa condición previa, sin degradarla a advertencia

#### Scenario: No autonomous promotion
- **WHEN** el modelo observa varias HU sin incidencias
- **THEN** no activa bloqueos por sí mismo; conserva el modo configurado hasta decisión expresa

### Requirement: Actionable distinct outcomes

La comprobación SHALL distinguir advertencia, decisión humana pendiente, incumplimiento bloqueante habilitado y error del validador. Cada inconsistencia SHALL informar condición, observación, motivo exacto, transición, corrección, responsable, evidencia que sigue válida y comprobaciones que deben repetirse. Una recomendación no adoptada MUST NOT bloquear por sí sola.

#### Scenario: Critical functional ambiguity
- **WHEN** la continuación depende de una decisión funcional no resoluble automáticamente
- **THEN** identifica la decisión y conserva el trabajo independiente; no convierte repetir validaciones en solución

#### Scenario: Objective blocking control enabled
- **WHEN** una condición habilitada encuentra una ruta escrita fuera del alcance
- **THEN** impide esa transición y asigna la corrección concreta, sin reiniciar toda la HU

### Requirement: Role and HU specific write scope

Cada despacho SHALL concretar lectura, escritura y acciones permitidas por HU y rol. La comprobación SHALL contrastar cambios Git completos con una referencia de entrada y otra de salida, distinguiendo cambios previos de los del intervalo observado, incluidos renombres, borrados y no rastreados. MUST NOT afirmar atribución de autoría que Git no acredita.

#### Scenario: Previous role already changed code
- **WHEN** Tester escribe recibos y el código de Developer ya está en la referencia de entrada
- **THEN** no atribuye esos cambios previos a Tester; evalúa sus nuevas diferencias contra sus rutas asignadas

#### Scenario: Same file changed again
- **WHEN** Tester modifica después de su entrada un archivo que Developer ya había cambiado
- **THEN** detecta la diferencia de contenido del intervalo aunque la lista de nombres sea idéntica

#### Scenario: No trusted baseline
- **WHEN** falta la referencia de entrada o hay una escritura externa concurrente
- **THEN** informa alcance o atribución no comprobables y pide reconciliarlo, sin inventar la identidad del escritor

### Requirement: Local corrections preserve valid work

Una corrección de formato o referencia SHALL resolverse en un nuevo intento de handoff conservando la evidencia técnica si candidato, criterios, política, entorno y recibos siguen vigentes. Cambios técnicos SHALL volver al mecanismo existente de invalidación. El flujo MUST NOT iniciar bucles automáticos de reparación o reintento.

#### Scenario: Missing link to existing receipt
- **WHEN** se añade la referencia correcta a un recibo existente e íntegro sin cambiar sus entradas
- **THEN** revalida el contrato y gate sin repetir pruebas ni consumir una ronda técnica de corrección

#### Scenario: Code changed after tests
- **WHEN** se modifica una entrada técnica del plan
- **THEN** conserva intentos anteriores y aplica plan/run/gate a lo requerido; no cambia IDs o fechas para adoptar resultados de otro plan

### Requirement: Non circular evidence and approval binding

El kit SHALL separar entradas técnicas, contenido revisado y registros derivados mediante reglas explícitas y comprobables. Agregar recibos propios, resúmenes derivados o movimientos previstos de Archive SHALL preservar aprobación solo si no cambian alcance, criterios, reglas, resultados o contenido revisado. MUST NOT excluir documentación funcional para estabilizar hashes.

#### Scenario: Append approval receipt
- **WHEN** se añade la respuesta humana al registro previsto conservando el contenido aprobado
- **THEN** no invalida esa aprobación por autorreferencia, pero comprueba que corresponde a las acciones y candidato presentados

#### Scenario: Material change hidden in metadata
- **WHEN** una edición del registro derivado altera criterios o resultados revisados
- **THEN** detecta la diferencia, invalida la aprobación correspondiente y no la trata como actualización inocua

#### Scenario: Future handoff without circular plan updates
- **WHEN** se genera un nuevo intento de handoff conforme a la política congelada y sin cambiar entradas técnicas
- **THEN** conserva plan y recibos, registrando la observación nueva sin añadir hashes futuros al propio plan

### Requirement: Tested and published content equivalence

El kit SHALL comprobar equivalencia conservando base, todas las entradas funcionales y evidencia vigente. El estado Git consumido por un check SHALL participar en su vigencia o declararse no soportado por la equivalencia. Stage o commit con todas esas entradas iguales SHALL preservar la identidad técnica en planes que adopten esa proyección. MUST NOT extenderla a contenido distinto, evidencia caducada o planes históricos sin migración explícita.

#### Scenario: Commit preserves tested content
- **WHEN** se versiona exactamente el contenido probado más los metadatos y movimientos autorizados, sin cambiar ninguna entrada funcional de los checks, incluido estado Git cuando aplique
- **THEN** comprueba árbol local/remoto y gate vigente sin repetir suites por cambiar HEAD o capas Git

#### Scenario: Check consumes functional Git state
- **WHEN** un check depende de rama, índice, HEAD u otro estado Git y ese estado cambia aunque los archivos permanezcan iguales
- **THEN** la igualdad de contenido no conserva su vigencia; contrasta esas entradas y remite la evidencia afectada al mecanismo de validación aplicable

#### Scenario: Git dependency cannot be represented
- **WHEN** el adaptador no puede representar y contrastar el estado Git que consume un check
- **THEN** declara ese caso no soportado por la equivalencia y no conserva su aprobación por igualdad de archivos ni presume independencia por falta de declaración

#### Scenario: Commit hook changes code
- **WHEN** un hook o staging parcial produce contenido funcional diferente del probado
- **THEN** rechaza equivalencia y detiene publicación hasta reconciliar el candidato y la evidencia requerida

### Requirement: Phase specific stopping conditions

El flujo SHALL detener la parte dependiente en Propose por decisión necesaria, Apply por autorización/conflicto crítico/alcance, Sync por revisión o evidencia inválida, Archive por cierre no autorizado o expediente distinto y PR por destino/contenido no autorizado, evidencia invalidada o publicación no confirmada. MUST NOT añadir pausas por cada transferencia ya autorizada.

#### Scenario: Only archive approved
- **WHEN** la persona autoriza Archive sin push o creación de PR
- **THEN** permite únicamente el cierre autorizado y conserva publicación pendiente

#### Scenario: Work not dependent on pending decision
- **WHEN** falta una decisión para una parte de la HU
- **THEN** conserva borrador y permite exploración o trabajo ya autorizado que no dependa de resolverla

#### Scenario: Resume after the pending decision is resolved
- **WHEN** se resuelve la duda o llega la autorización humana aplicable y siguen satisfechas las condiciones técnicas obligatorias
- **THEN** registra la resolución, comprueba alcance y candidato vigentes y reanuda desde el punto pendiente, conservando trabajo y evidencia válidos sin repetir la misma autorización

#### Scenario: Human approval does not replace technical evidence
- **WHEN** llega un aval humano pero continúa ausente o inválida una comprobación técnica previamente obligatoria
- **THEN** mantiene pendiente la continuación que depende de esa evidencia y permite el trabajo independiente ya autorizado
