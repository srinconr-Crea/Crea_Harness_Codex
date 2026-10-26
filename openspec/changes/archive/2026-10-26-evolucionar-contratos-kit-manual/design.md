# Design

## Context

La motivación está en `proposal.md`. Inspección local del 26 de octubre de 2026, sobre HEAD `96bf659`, inicialmente limpio en el repositorio Git anidado `harness/`. No hay AGENTS raíz aplicable a este cambio; el AGENTS de la distribución se analiza como parte del producto, no como configuración activa del repositorio de desarrollo.

### Base y evidencias observadas

| Fuente inspeccionada, relativa a `harness/` | Hecho que condiciona el diseño |
| --- | --- |
| `README.md`, `artifacts/crea-manual-kit-0.1.4/LEEME-CREA.md` | La entrega vigente es el kit manual 0.1.4; el consumidor copia/adapta sus archivos. No instala `harness_local`. |
| `artifacts/crea-manual-kit-0.1.4/` | Es el árbol mantenido y empaquetado actual. No se encontró otro árbol fuente del kit manual. |
| `scripts/integrate_testing_014.py`, `scripts/update_testing_docs_014.py` | Autoría/adaptación específica de 0.1.4 con destino fijo. No son un generador general reutilizable de una nueva versión. |
| `scripts/package_manual_014.py` | Valida, actualiza inventario/manifiesto, preserva 0.1.3 y upstream/licencias, audita neutralidad con entradas externas, crea ZIP/hash/informe. **Muta 0.1.4**: no ejecutar para producir la siguiente entrega. |
| `AGENTS.md`, `.codex/agents/{planner,developer,tester,reviewer}.toml`, `.agents/skills/Crea/orquestador/SKILL.md` dentro del kit | Cuatro roles secuenciales, un escritor, principal coordinador, pausas OpenSpec y entrega autorizada. Principal es una responsabilidad de la sesión: no hay `principal.toml` en el kit manual. |
| `docs/proyecto.json`, `docs/proyecto.schema.json` dentro del kit | Configuración versión 1, setup incompleto de fábrica, inventario y delivery declarativos; schema estricto y proveedor no configurado por defecto. |
| `scripts/crea/pruebas.py`, `scripts/crea/testing/{workflow,git_adapter,schemas,common,reports,execution}.py` | Ya existen plan/run/gate, Git completo, jsonschema Draft2020-12 offline, JSON estricto, integridad, entorno y caducidad de recibos. |
| `.agents/skills/Crea/crea-pruebas/{SKILL.md,scripts/contract.py,assets/}` | Catálogo único, selección y evaluación de checks; no es un runner remoto ni sustituye autorización. |
| `docs/plantillas/{handoff,evidencia-hu,pr,tareas-openspec}.md`, `docs/entrega-git.md` | Handoff humano, recibos canónicos, aprobación ligada al candidato, GitHub formulario y Azure Services CLI. Ya contemplan evitar autorreferencia del SHA y del recibo humano. |
| `tests/crea/{test_contract,test_testing_adapters,test_kit_validation,test_neutrality}.py` dentro del kit | Base de pruebas propia del kit reutilizable, separada de `harness/tests/` del motor histórico. |

En adelante, `K0 = artifacts/crea-manual-kit-0.1.4/` y **K1 propuesto** = `artifacts/crea-manual-kit-0.1.5/`, ambos relativos a `harness/`. Una ruta sin K es relativa a la raíz del **repositorio consumidor**. Por ejemplo, su `docs/proyecto.json` corresponde hoy a `K0/docs/proyecto.json` y se desarrollaría en `K1/docs/proyecto.json`. `harness/docs/proyecto.json` no es la fuente del kit. `openspec/changes/evolucionar-contratos-kit-manual/` contiene exclusivamente esta planificación.

### Diferencia con el motor histórico

`src/harness_core/` y `src/harness_local/` contienen descriptor/política/binding, estado de HU, workers, publicación y distribución anteriores. Las specs `hu-lifecycle`, `candidate-validation`, `client-configuration`, `story-pr-integration` y `harness-distribution` describen esos contratos y limitaciones. El kit usa archivos, sesión Codex y adaptadores locales propios; no hay conexión demostrada con ese estado, GitProvider, workers o certificados. No se importarán esos módulos ni sus aprobaciones, controles de acceso o certificaciones. Coinciden algunos objetivos; el comportamiento del kit necesita contratos propios. No se modificarán las specs históricas para hacerlas parecer implementadas por el kit.

Limitación relevante: `git_adapter.collect` calcula `input_digest` sobre base/HEAD, capas Git, índice y archivos modificados; solo excluye outputs de pruebas declarados y con nombres muy restringidos. `workflow.make_plan` añade hashes de configuración, ejecución y adaptadores. Por tanto, añadir handoffs, evidencia o cambios de cierre puede invalidar hoy un plan. No basta con decir «los metadatos no cuentan»: la adaptación de la proyección compartida se especifica abajo y debe probarse.

## Goals / Non-Goals

**Goals:** contratos útiles por fase; una selección de reglas; detección local reproducible; vigencia sin circularidad; salidas y entrega comprobables; adopción opcional y revisada. Elegir controles objetivos pequeños y conservar el criterio funcional humano.

**Non-Goals:** runtime propio, base de datos, orquestador alternativo, nuevas fases/agentes, interceptores globales, despliegues o cambios remotos en este incremento, Boards, evaluación avanzada de riesgo, dossier o auditoría adicional universal. Los tres ejemplos son escenarios de diseño; no acreditan agentes o pruebas reales. No se ejecutará Apply a partir de esta propuesta.

## Decisions

### 1. Evolucionar el árbol manual con adaptadores compartidos

Alternativas consideradas: (a) solo ampliar Markdown, sencillo pero no comprobable; (b) contratos JSON y un verificador pequeño sobre los adaptadores actuales; (c) reactivar el motor histórico, que añadiría instalación, estado y garantías sin conexión con el kit. Se propone **b**, por el objetivo solicitado. Esta es una elección de diseño pendiente de revisión, no una decisión ya aprobada por el usuario.

La siguiente versión mantendrá un árbol versionado como fuente revisable, siguiendo 0.1.3 → 0.1.4. No se introducirá en este incremento una segunda fuente genérica paralela en `src/` ni un sistema de generación nuevo.

| Archivos existentes que cambiarían **solo en K1** | Cambio propuesto |
| --- | --- |
| `AGENTS.md`, `.agents/skills/Crea/orquestador/SKILL.md` | Selección de reglas, despacho y rutas por HU, contratos, paradas y comprobación antes de avanzar; principal sigue coordinando. |
| `.codex/agents/planner.toml`, `developer.toml`, `tester.toml`, `reviewer.toml` | Mismo contrato y contexto seleccionado; escritura por fase; no autoaprobación. Modelos/esfuerzos no cambian por este diseño. |
| `docs/proyecto.json`, `docs/proyecto.schema.json` | Extensiones opcionales de reglas/transiciones; delivery conserva proveedor y modos actuales. |
| `docs/plantillas/handoff.md`, `evidencia-hu.md`, `pr.md`, `tareas-openspec.md` | Organización común, proyección humana, inventario de objetos, contenido canónico del PR y responsabilidades. |
| `docs/entrega-git.md`, `docs/configuracion-manual.md`, `docs/extensiones.md`, `LEEME-CREA.md` | Adopción, contenido transportado, límites, permisos y cómo reanudar. |
| `docs/buenas-practicas/general.md` y referencias técnicas pertinentes | Enlazar reglas normativas canónicas; mantener ejemplos y consejos técnicos aquí, sin obligaciones duplicadas. |
| `scripts/crea/testing/git_adapter.py`, `workflow.py`, `schemas.py`, `kit_validation.py` | Exponer observación compartida, proyección de metadatos controlada y compatibilidad de extensiones; conservar plan/run/gate. |
| `.agents/skills/Crea/crea-pruebas/SKILL.md`, `scripts/contract.py`, `assets/plan.schema.json`, `docs/pruebas/README.md`, `INTEGRACION.json` | Integrar la proyección en construcción/evaluación del mismo plan y explicar procedencia, sin otro catálogo ni adopción entre planes. |
| `tests/crea/test_testing_adapters.py`, `test_kit_validation.py` | Regresiones de huellas, compatibilidad y empaquetado. |

| Archivos nuevos propuestos | Necesidad |
| --- | --- |
| `K1/docs/constituciones/README.md`, `comunes.md` | Selección/gobierno y obligaciones transversales justificadas. |
| `K1/docs/constituciones/capas/{bronze,silver,gold}.md` | Plantillas con preguntas y contratos de capa, expresamente inactivas hasta decisión del proyecto. |
| `K1/docs/constituciones/capacidades/{sql,spark}.md` | Reglas iniciales limitadas sustentadas en prácticas vigentes; parámetros/ejemplos siguen fuera. |
| `K1/docs/plantillas/handoff.schema.json` | Único schema base, `$defs` para contratos, snapshots e informe de transición. |
| `K1/scripts/crea/transiciones.py` | Entrada CLI pequeña que integra comprobación y renderizado determinista. |
| `K1/tests/crea/test_transiciones.py` | Casos de contrato, intervalo, decisiones, errores y preservación de evidencia. |
| `scripts/package_manual_015.py` | Empaquetado dirigido a K1 con guardas de preservación de 0.1.3/0.1.4; no reejecuta scripts 014. |

No se crearán `jobs.md` o `pipelines.md` vacíos: README los registra como especialidades pendientes. Se añadirán solo cuando haya contenido y responsable. No se modifican skills OpenSpec/Databricks upstream ni licencias. Tras una futura implementación, el empaquetado produciría `artifacts/crea-manual-kit-0.1.5.zip`, `.zip.sha256` y `.zip.validation.json`, además del manifiesto de K1. No se generan en Propose.

### 2. Reglas seleccionadas, sin inventar convenciones del cliente

`docs/constituciones/README.md` contendrá catálogo, estado (`active`, `template`, `pending`), selección por capas/capacidades, responsable, cambios y excepciones. Cada regla activa tendrá encabezado `### <ID>` estable, condición de aplicación, obligación/fundamento, evidencia y comprobación (`automatic`, `review`, `human_decision`); excepciones: prohibidas o autoridad, justificación, alcance y vencimiento/revisión. Los IDs no se reutilizan para otro significado; el hash del documento y revisión acompañan la selección.

Reglas iniciales justificadas por `AGENTS.md` y buenas prácticas actuales, todavía **propuestas**:

| ID | Aplicación y obligación | Evidencia / comprobación | Excepción |
| --- | --- | --- | --- |
| CREA-COM-001 | Toda HU: definir entradas, salidas y criterios antes de implementar; evita resolver otro problema. | Referencias de criterios y plan; revisión + presencia automática. | No omitir criterios; simplificarlos proporcionalmente por decisión del responsable. |
| CREA-COM-002 | Cuando se afirme ejecución: conservar estado real y evidencia ligada al candidato. | Plan/recibos/gate existentes; automática en su alcance. | No convertir not_run o mocks en ejecución real. |
| CREA-COM-003 | Toda escritura: preservar alcance y cambios ajenos; no introducir secretos. | Diff y revisión; detección automática de rutas, revisión del contenido. | Excepción de rutas solo con ampliación autorizada; ninguna excepción para versionar credenciales. |
| CREA-SPARK-001 | Si se cambia semántica Spark: identificar versión/entorno compatible y evidencia adecuada. | Plan y recibo de entorno requerido; review y gate. | Un mock no sustituye runtime requerido; ausencia queda blocked en el gate existente. |
| CREA-SQL-001 | Si se cambian joins/agregaciones: explicitar grano, claves y semántica antes de optimizar. | Criterios y tests pertinentes; revisión. | Cambiar semántica exige decisión de alcance, no excepción implícita. |

Las plantillas de Bronze/Silver/Gold incluyen campos sustantivos a decidir: propósito, granularidad, transformaciones permitidas/prohibidas, identidad, errores y conservación. No fijan PK, retención, nombres de catálogos o deduplicación universal. «Pendiente» no equivale a regla activa. Los ejemplos de este diseño asumen decisiones sintéticas explícitas, nunca reglas reales de un cliente.

Configuración mínima propuesta, fragmento ilustrativo de `docs/proyecto.json`:

```json
{
  "rules": {
    "enabled": true,
    "index_path": "docs/constituciones/README.md",
    "common": ["docs/constituciones/comunes.md"],
    "layers": {"silver": "docs/constituciones/capas/silver.md"},
    "capabilities": {"spark": "docs/constituciones/capacidades/spark.md"}
  },
  "workflow": {
    "transitions": {"mode": "informative", "blocking_conditions": []}
  }
}
```

El resto de `workflow` se conserva. El ejemplo supone que el proyecto **ya completó y aprobó** Silver; la distribución no activará esa plantilla de fábrica. En K1 se ofrece `rules.enabled=false`, mapas sin capas activas y `mode=informative` al adoptar transiciones. `schema_version: 1` se conserva: ambas secciones son opcionales en el schema nuevo; cuando aparecen son estrictas, con rutas relativas no vacías, listas sin duplicados, mapas de IDs válidos y `blocking_conditions` de un catálogo cerrado. Ausencia de `transitions` significa flujo anterior, sin contratos retroactivos; ausencia de `rules` significa selección previa de contexto, sin afirmar reglas nuevas adoptadas. Un lector 0.1.4 estricto no acepta secciones nuevas: actualizar conjuntamente herramientas/schema antes de escribirlas. Ninguna clave constituye sandbox, permisos nativos, hooks o autenticación.

La HU declara `layers` y `capabilities` como listas, con motivo de selección y no-aplicabilidad. Resolver comunes pertinentes + mapas activados de esas listas. Los IDs seleccionados, revisiones y hashes se congelan en planificación y se transmiten sin reinterpretar por rol. Las referencias técnicas se cargan solo cuando ayudan a la tarea, sin activar toda la capacidad por asociación de palabras. Una HU Silver/Spark no carga Gold o SQL automáticamente. Añadir una capacidad pertinente exige actualizar selección y autorización si amplía alcance.

Gobierno: el entorno impone sus restricciones reales; las instrucciones superiores y políticas vigentes siguen aplicando. Entre documentos normativos no se usa «último texto gana» ni «más específico siempre gana»: obligaciones compatibles se acumulan; una especialización solo reemplaza una regla cuando existe delegación/excepción expresa. Una contradicción crítica se identifica por IDs y contenido y se eleva al responsable; se pausa únicamente lo dependiente. Cambiar obligaciones, criterios, evidencias exigidas, excepciones sustantivas, selección con impacto o bloqueos requiere decisión del responsable y nueva autorización del alcance afectado. Una aclaración editorial sin cambio de significado requiere revisión/diff local, no otra HU de gobierno; si modifica una entrada técnica, se aplica la invalidación existente que corresponda. Ningún rol cambia esas reglas para aprobar su propia entrega.

### 3. Un contrato base, requisitos por transición

`docs/hu/<change>/handoffs/<fase>-<intento>.json` es canónico e inmutable una vez entregado. Fases de registro: `planificacion`, `implementacion`, `pruebas`, `revision`, `cierre`, `entrega`; son etiquetas de operaciones existentes, **no nuevas fases obligatorias**. Los intentos son enteros positivos crecientes por fase y el nombre debe concordar. Un intento corregido referencia `previous_handoff`; nunca se reemplaza evidencia previa. La ronda técnica global existente es otro contador: corregir un enlace no inicia un ciclo Developer/Tester ni reinicia rondas.

El schema base Draft2020-12 usa `additionalProperties:false`, `$defs` locales y condiciones por transición. No exige esquema distinto por rol. Organización común:

| Sección JSON | Campos y comprobación |
| --- | --- |
| `identity` | `hu_id` local no vacío, `external_story_id` opcional/nulo, `change`, `phase`, `attempt`, `sender`, `recipient`, `agent_id` real o nulo, `created_at`; rol principal/persona admitidos como destinatario. |
| `result` | `status` del vocabulario existente y `completed` con referencias concretas; nunca confundir passed de un check con aprobación de fase. |
| `scope` | Objetivo, referencias a criterios, candidatos de entrada/salida, base/HEAD reales o nulo justificado en planificación inicial, rutas de lectura/escritura y acciones permitidas, snapshots e intervalos. |
| `context` | `layers`, `capabilities`, justificaciones no-aplica, reglas `{id,path,revision,sha256,check_mode}`, excepciones y riesgo justificado simple; no puntuador de riesgo. |
| `evidence` | Referencias tipadas a artefactos/decisiones/plan/resultados/gate/recibos, hashes de evidencia primaria y objetos cuando apliquen. Un path existente no acredita por sí solo resultado. |
| `pending` | Bloqueos, advertencias, preguntas y excepciones con dueño y efecto. Un consejo no adoptado no se eleva a bloqueo automático. |
| `continuation` | `transition`, siguiente paso/destinatario, acciones ya autorizadas, decisión requerida o nula, referencia real a respuesta humana y contenido al que aplica. |

Versiones desconocidas, IDs contradictorios, JSON con claves duplicadas o referencias fuera de la raíz autorizada se diagnostican. Paths se normalizan y resuelven con las utilidades existentes; no se siguen symlinks/junctions ni referencias de schema remotas. Referencias OpenSpec archivadas se resuelven con un mapa de movimiento explícito, no escogiendo el primer expediente parecido. Las referencias de texto indican archivo y ancla/ID; las primarias técnicas incluyen hash comprobado. Un recibo de respuesta humana identifica conversación/mensaje si la herramienta lo proporciona; en caso contrario, cita exacta/resumen fiel, fecha y alcance identificables en la conversación. El JSON no prueba autenticidad criptográfica ni convierte una afirmación del modelo en autorización humana.

| Transición existente | Requisitos adicionales, además del contrato base |
| --- | --- |
| Propose → presentación | Artefactos requeridos del schema, decisiones/pendientes, criterios y plan preliminar; permite borrador con una decisión pendiente. No requiere resultados ni PR. |
| Planificación → Apply | Criterios y plan de validación concretos, selección de reglas, write scope aprobado, nueva solicitud humana de Apply para ese cambio; no exige tests ejecutados. |
| Developer → Tester | Candidato completo, tareas realizadas, diff/intervalo, criterios y reglas; principal usa plan final de `pruebas.py plan`. No pedir aprobación por esta transferencia ya cubierta. |
| Tester → Reviewer | Plan final, resultados y recibos contrastables, estados reales y gate vigente; si no se pueden ejecutar checks requeridos, no declarar ready_for_review técnico. |
| Reviewer → Sync | Revisión favorable, verify y gate vigentes; ningún resultado requerido failed/blocked/not_run. Sync no es Archive. |
| Sync → Archive | Diff de sync y expediente presentados, autorización explícita de cierre, mapa esperado de movimientos y candidato revisado. |
| Archive → commit/push → PR | Acciones/destino/contenido expresamente autorizados, alcance final completo, evidencia vigente, push confirmado antes de PR; cada operación comprueba sus precondiciones sin pedir otra confirmación si ya está cubierta. |

### 4. Acceso y observación de cambios por intervalo

Los perfiles describen responsabilidades; el principal concreta **cada despacho** con rutas reales. Ejemplo sintético para `normalizar-contactos`:

| Responsable | Lectura necesaria | Escritura asignable para esta HU |
| --- | --- | --- |
| Planner | Contexto, reglas seleccionadas, código afectado y specs pertinentes | `openspec/changes/normalizar-contactos/{proposal,design,tasks}.md`, `specs/<capacidad>/spec.md`; su `handoffs/planificacion-N.json` y documentación de HU asignada. No specs estables. |
| Developer | Plan/criterios/reglas y fuentes/tests afectados | `src/silver/contactos.py`, `tests/silver/test_contactos.py`, documentación técnica asignada, casillas de implementación en `tasks.md`, su handoff. |
| Tester | Candidato, plan y criterios/reglas inmutables | Outputs exactos de `docs/hu/normalizar-contactos/pruebas/attempt-N/`, su `handoffs/pruebas-N.json`; solo casillas de ejecución identificadas si se asignan. No editar tests, política o esperados. |
| Reviewer | Candidato completo, reglas y recibos Tester | Hallazgos/handoff propios; `openspec/specs/<capacidad>/spec.md` en Sync favorable; rutas origen/destino precisas de Archive autorizado. No corregir producción ni criterios. |
| Principal | Contexto y todos los handoffs pertinentes | Despachos, snapshots, informes y resúmenes derivados de la HU; paquete PR y entrega Git de rutas enumeradas, con autorización. No modifica reglas/criterios para aprobar. |

Las rutas de ejemplo no presuponen que esos archivos existan en este repo de desarrollo. Cada contrato enumera los reales, incluyendo altas/bajas y destino/origen de renombres. Un permiso general `docs/**` no sustituye a rutas concretas. Fuera de esas rutas, el rol propone el cambio y lo devuelve al principal. Cambios de criterio/reglas/política vuelven al responsable, nunca se autoautorizan.

El principal toma una referencia de entrada antes de cada escritor y compara con la observación final: base/HEAD, estado completo staged/unstaged/untracked, conflictos, paths/modes/blob del índice y hashes de archivos de trabajo, incluidos archivos rastreados que aún no estaban modificados. De lo contrario no detectaría que un rol posterior modifica un archivo previamente limpio o cambia por segunda vez un archivo ya tocado. Reutilizar `git_adapter` ampliando su observación compartida, sin otra implementación de Git. Restar nombres de archivos no es suficiente; comparar contenido/modos/ausencia por path y origen/destino de movimiento. Un snapshot inicial ausente no se inventa.

Snapshots se guardan como artefactos referenciados en `handoffs/<fase>-<intento>-entrada.json` y `...-salida.json`, validados con `$defs` del schema base. El snapshot de salida describe el estado inmediatamente anterior a emitir el handoff. El verificador observa también el handoff y las escrituras posteriores al snapshot: su propia generación debe estar declarada por path/rol y no se omite del control de alcance. Los snapshots no contienen su propio hash; el handoff referencia los archivos ya cerrados. No se crea un hash circular de snapshot/handoff/informe.

Tres garantías distintas: (1) perfiles/contratos **instruyen** lectura y escritura; (2) el comprobador **detecta** diferencias persistentes fuera de alcance al ejecutarse; (3) sandbox/ACL/permisos de herramienta **restringen técnicamente** solo lo que el entorno imponga. El kit no impide todas las lecturas ni detecta una escritura revertida entre snapshots. Con escritores externos concurrentes no se puede atribuir autoría a un rol: informar «cambio observado durante el intervalo» y reconciliar, sin acusación ficticia. Si no hay Git válido, informar error del verificador; no degradar a una lista de archivos supuesta.

### 5. Validador pequeño, informativo primero

Interfaz propuesta, aún no implementada:

```text
python scripts/crea/transiciones.py check --repo <raiz> --handoff <ruta>
    --transition <to_apply|to_test|to_review|to_sync|to_archive|to_publish|to_pr>
    [--out <nuevo-informe.json>]
python scripts/crea/transiciones.py render --repo <raiz> --handoff <ruta>
    [--out <nuevo-resumen.md>]
```

Modo y condiciones se leen de `workflow.transitions`; no hay override CLI para saltarse una política. Sin `--out`, solo salida estándar. Con `--out`, creación exclusiva en ruta exacta de la HU asignada, sin colisión con evidencia primaria ni symlinks/junctions. No escribe código, corrige handoffs, crea ramas, ejecuta suites, instala, autentica ni contacta proveedores. `render` usa las siete secciones, sin nueva interpretación del modelo.

Se reutiliza `testing.schemas.validate_schema` para el schema base, `common.read/safe_path/digest/file_hash` y observación `git_adapter`. Para vigencia técnica se usa `workflow.gate` con plan/resultados canónicos y contexto actual, o su resultado recalculado en la misma invocación si ya se obtuvo: no se implementan otra vez edad, entorno, hashes, JUnit, asserts o selección. No confiar en un `gate.json` pasado sin contrastarlo con el contexto actual. Antes de Apply se valida el plan preliminar y sus referencias, **sin llamar a un gate que exige resultados futuros**. La prioridad inicial de comprobación integrada es `to_apply`, `to_sync`, `to_archive`, `to_publish` y `to_pr`; las otras transferencias usan el mismo contrato sin añadir ceremonias.

Informe con `schema_version`, HU/cambio/handoff, transición, modo, `check_status` (`completed|validator_error`), `new_control_effect` (`allow|report_only|block|undetermined`), `existing_constraints` y lista de hallazgos. Cada hallazgo tiene `condition_id`, clase, esperado/observado sanitizado, motivo exacto, transición, corrección, responsable, `preserved_evidence` y `recheck`. No copiar valores secretos ni logs completos. Códigos de proceso propuestos: 0 comprobación completada sin bloqueo nuevo efectivo (también report_only), 2 incumplimiento objetivo bloqueante habilitado, 3 decisión humana necesaria para esa continuación, 4 error del validador. El informe diferencia siempre un 0 informativo de una aprobación; un 3 refleja una decisión necesaria, nunca una recomendación opcional.

**Consumo por el principal:** no interpretar cualquier código distinto de cero como «detener todo» ni aplicar un manejador genérico que aborte la HU. El principal combina código, modo configurado, efecto del informe y restricciones existentes. En `informative`, una inconsistencia nueva o el código 4 registra el diagnóstico y qué no pudo comprobarse, sin introducir automáticamente un veto nuevo ni acreditar validez. El código 3 pausa únicamente la continuación que depende de una decisión humana necesaria; no convierte recomendaciones u omisiones descriptivas en aprobaciones nuevas. El código 2 corresponde a un control nuevo bloqueante habilitado en `enforcing`, no al comportamiento ordinario del piloto. Los resultados de gates ya obligatorios se consumen según sus contratos propios: no se reinterpretan como meros avisos por ejecutar el nuevo validador en modo informativo.

Si el informe falta, no puede leerse o contradice el código/modo, conservar el resultado como indeterminado y comprobar las restricciones existentes mediante sus mecanismos actuales; nunca asumir `passed` ni que una restricción ausente del informe está satisfecha. Si falta una aprobación o falla un gate obligatorio, mantener esa detención por su causa real. La imposibilidad de acreditar una condición previamente obligatoria tampoco queda resuelta por el modo informativo. Registrar el error del nuevo validador por separado evita convertir su fallo en un veto añadido o en una autorización implícita.

**Reanudación:** la continuación dependiente queda pendiente hasta resolver la duda, recibir la autorización aplicable o corregir la condición técnica correspondiente. Una vez satisfecha, el principal registra la resolución, comprueba que corresponde al alcance/candidato vigente y reanuda desde ese punto, conservando trabajo y evidencia válidos. Puede avanzar mientras tanto lo ya autorizado que no dependa del pendiente. No solicita otra vez la misma autorización vigente ni repite comprobaciones resueltas; vuelve a comprobar solo lo afectado por una corrección real o cambio de estado. El aval humano resuelve decisiones y permisos dentro de su alcance, pero no sustituye evidencia técnica obligatoria.

| Clase | Efecto |
| --- | --- |
| Advertencia | Continúa lo autorizado; corrige si procede. |
| Decisión humana pendiente | La parte dependiente espera por una decisión necesaria; el validador no decide negocio ni fabrica permisos. |
| Incumplimiento bloqueante | Solo bloquea automáticamente como control **nuevo** si su `condition_id` está habilitado y el modo es `enforcing`. En informative registra `would_block`, sin añadir bloqueo. |
| Error del validador | `undetermined`, exit 4; indica qué no comprobó. No prueba incumplimiento ni validez. En piloto no introduce veto nuevo; siguen aplicando controles previos y nunca se afirma que esta comprobación pasó. En enforcing una condición requerida no comprobable detiene esa continuación hasta resolverla o tomar decisión explícita, sin suponer un fallo del código. |

Condiciones iniciales objetivas: `IDENTITY_MATCH`, `TRANSITION_FIELDS`, `REFERENCE_EXISTS`, `EVIDENCE_CURRENT` (delegada a gate), `WRITE_SCOPE`, `AUTHORIZATION_SCOPE`, `NO_REQUIRED_BLOCKERS`. Las contradicciones semánticas las descubre revisión humana/roles y se registran; el script solo contrasta decisión/resolución y referencias. Campos meramente descriptivos y recomendaciones no se convierten en «todo el flujo blocked».

Introducción gradual: aplicar informative en tres HU representativas (datos, documental y una corrección controlada) y registrar sus diagnósticos en la evidencia normal. Usar fixtures válidas/inválidas por condición para demostrar detección, responsable y recuperación local. El responsable revisa discrepancias/falsos positivos y aprueba IDs concretos antes de pasar a `enforcing`. No hay promoción autónoma, porcentaje mágico ni plataforma de evals. `max_fix_rounds` existente se conserva para ciclos técnicos; no se crean bucles de autocorrección ni reintentos sin cambio real. Volver a comprobar solo tras una corrección, cambio de estado o una decisión recibida.

### 6. Vigencia, proyecciones y correcciones locales

Se distinguen tres vistas, dentro de los adaptadores existentes:

1. **Observación completa de alcance/entrega:** ningún archivo desaparece. Conserva Git, cambios de cada intervalo, metadatos y expediente final a publicar.
2. **Entradas técnicas de pruebas:** código, tests, fixtures, criterios, configuración/política, reglas aplicables, adaptadores y entorno relevantes. El plan sigue enlazando su candidato y checks. No se cambia el significado de recibos históricos.
3. **Paquete revisado/autorizado:** referencias a criterios, reglas, candidato técnico, verify, diff de Sync, decisiones y contenido de PR, acciones/destinos/rutas; excluye solo su recibo posterior y movimientos/metadatos derivados previamente enumerados.

K1 debe ampliar de forma explícita la proyección compartida de Git y su procedencia. **El plan congela la política de proyección, no los hashes de archivos futuros.** Su procedencia contiene versión de proyección, digest de reglas de clasificación/generadores y contexto aprobado (criterios, reglas, scope y decisiones funcionales canónicas). No contiene un recibo, hash o lista que deba crecer por cada handoff posterior. El schema del plan y `contract.py` se adaptan junto con `workflow`, en la misma cadena plan/run/gate.

La política delimita nombres de artefactos administrados por HU mediante gramática cerrada: fase permitida, intento entero, sufijos concretos de snapshot/informe y nombres de vistas derivados. No es un glob genérico sobre documentación. Al observar cada estado, el adaptador resuelve **paths exactos existentes**, contrasta schema/generador/entradas canónicas y produce un recibo de clasificación con path, hash observado, motivo y fuente, separado del plan. Ese recibo va al informe de transición o evidencia Git de esa observación; no participa del digest que describe ni incluye su propio hash. Así un intento futuro válido puede aparecer sin editar el plan o predecir su contenido. Paths sin esa gramática o contenido no verificable no se excluyen silenciosamente. Ningún output derivado puede ser input de un check: si lo es, se trata como entrada técnica y se planifica/probará en consecuencia. No usar exclusiones `docs/**`, `openspec/**` o todo `docs/hu/**`.

Un handoff no es completamente inocuo por tener nombre válido: sus criterios, selección/hash de reglas, alcance y decisiones relevantes deben concordar con el contexto congelado del plan. Esos campos se contrastan y cualquier cambio relevante invalida; los enlaces a recibos, ID real del agente, nuevos intentos o renderizados son metadatos posteriores. Código, tests, fixtures, configuración, política y specs/criterios canónicos siguen siendo entradas técnicas. La comprobación de contexto es determinista por referencias/hashes; una equivalencia semántica no demostrable requiere revisión, no una exención del modelo.

`evidencia.md` y resúmenes humanos son vistas derivadas de handoffs; criterios se enlazan a OpenSpec/solicitud canónicos. El inventario de objetos se conserva en `evidence.objects` del handoff autor correspondiente y las fases siguientes lo referencian/actualizan en nuevos intentos con su historia. No se editan dos inventarios independientes. Esos datos pueden avanzar estados solo con referencias primarias. El verificador comprueba el render determinista del Markdown y el enlace `derived_from` al handoff; una edición manual no reproducible no se clasifica como inocua. Handoffs enlazan recibos técnicos e intentos anteriores sin hashear el resumen que los referencia; evita ciclos. El paquete título/cuerpo PR se congela antes de presentarlo y de autorizarlo.

Un **nuevo intento de handoff** no implica nuevo plan de pruebas. Con las mismas entradas técnicas, mismos plan/recibos, configuración/entorno y edad vigentes, añadir una referencia o reemitir un resumen no cambia la huella técnica; produce un nuevo recibo de observación separado. Recalcular gate demuestra esa conservación. Las rutas de outputs de ejecución de pruebas continúan declaradas exactamente por la configuración existente: cambiar esas rutas, la política de proyección o cualquier configuración participante puede invalidar el plan. Si se necesita cambiar el plan, la adopción entre planes sigue desactivada en 0.1.4/K1; no se relabelan resultados viejos ni se promete reutilización selectiva que el adaptador aún no soporta.

**Paso de worktree probado a commit publicado:** la proyección nueva se identifica como `content-v2` y congela la base SHA, el conjunto de entradas/checks y un manifiesto canónico de contenido efectivo por path (hash, modo y bajas respecto de la base), incluido lo no rastreado pertinente. Los paths renombrados se normalizan por contenido respecto de esa base y los movimientos de expediente solo mediante el mapa revisado. HEAD, índice y capas Git siguen en observación completa para alcance/entrega, pero su mera redistribución al hacer stage/commit no cambia la identidad técnica. Las entradas completas de checks, criterios, reglas, configuración, adaptadores y entorno siguen contrastándose; no se limita la identidad a una lista de nombres cambiados.

**Límite de la equivalencia:** la conservación anterior solo aplica cuando permanecen iguales todas las entradas funcionales de cada check. Si un check consume rama, índice, HEAD, metadatos del commit u otro estado Git como entrada funcional, ese estado también participa en su vigencia: debe quedar identificado en el plan/evidencia y ser contrastable por el adaptador existente. Cambiar ese estado invalida el resultado afectado aunque los archivos sean iguales. Si el adaptador no puede representar y comprobar esa dependencia, declara el caso no soportado por la equivalencia `content-v2`; no conserva su aprobación por igualdad de contenido ni presume independencia por falta de declaración. No es necesario añadir soporte para todo estado Git en este incremento: se documenta el límite y se remite el caso al mecanismo de validación aplicable, sin declarar un gate satisfecho si la evidencia requerida no puede acreditarse. Para checks independientes del estado Git, mover contenido idéntico entre worktree, índice y commit sigue sin requerir suites nuevas por ese solo motivo.

Antes de commit se comprueba que el índice de las rutas a publicar coincide con el contenido revisado, incluido todo contenido funcional probado, y que solo añade registros derivados/movimientos autorizados; un staging parcial que publique otro código se rechaza. Después de commit, antes de push, se compara el árbol del SHA local con el manifiesto probado más las transformaciones autorizadas y se recalcula gate con `content-v2`, respetando las dependencias funcionales de estado Git y casos no soportados descritos arriba. Antes de declarar PR verificado se comprueba que el SHA remoto y el commit origen del PR son ese SHA, que el árbol relevante coincide y que los recibos no caducaron. Un hook de commit que cambie código, un modo distinto, archivos extra, un commit ajeno en el rango o un cambio de base no pasan esa equivalencia. Si vence evidencia o cambia una entrada real se vuelve a lo requerido por plan/run/gate. No se repiten suites solo porque cambió HEAD conservando contenido cuando ese estado no es una entrada funcional del check.

Los planes sin `content-v2` mantienen su verificación anterior y sus limitaciones: no se convierten ni se reescriben recibos para beneficiarse de la nueva identidad. K1 usa `content-v2` solo en HU adoptadas desde su plan inicial. Esta adaptación elimina la falsa invalidación por commit dentro del mismo plan, sin introducir adopción entre planes ni quitar la comprobación de entrega Git.

**Bloque técnico previo a la integración:** los cambios de identidad del candidato, clasificación de derivados y conservación de evidencia durante Sync/Archive/commit constituyen la refactorización de mayor riesgo del incremento, no solo una ampliación de plantillas o del pequeño CLI. Se implementan y verifican como bloque independiente en el grupo 4 de `tasks.md`: 4.3, 4.4 y 4.6 preceden a la verificación conjunta 4.5, cuyo resultado satisfactorio es precondición para conectar los roles del grupo 5. La comprobación de ese bloque usa los adaptadores y pruebas existentes, sin crear fases, agentes, componentes ni otra pausa humana obligatoria.

Sync y Archive: antes de aprobar cierre, se fija el diff estable de Sync y el mapa origen → destino esperado de Archive. El validador contrasta ese mapa y hashes de contenido, conserva todas las rutas en la vista de alcance y no vuelve a aplicar Sync. El candidato técnico sigue inmutable; los deltas con semántica o specs estables distintas de la proyección revisada invalidan el cierre. El estado de tareas solo puede avanzar casillas con evidencia referenciada, sin modificar su texto/criterios. Estas transformaciones se admiten mediante lista exacta y comparación de contenido, no exclusión global del directorio OpenSpec. Los recibos anteriores quedan asociados a la proyección vieja; no se migran silenciosamente.

| Cambio observado | Qué conserva validez | Corrección / recheck |
| --- | --- | --- |
| Falta enlace a un recibo íntegro que ya existe | Plan, resultados y recibo si gate confirma entradas/edad | Emisor corrige solo handoff en nuevo intento; revalidar schema, referencia y gate, cero suites. |
| Error de formato o resumen fuera de fecha | Evidencia primaria intacta | Regenerar desde contrato; revalidar render/estructura. No consume ronda técnica. |
| Código/test/fixture/config/regla relevante cambió tras probar | Intentos como historia; no su aprobación técnica sobre el nuevo candidato | Principal devuelve al mecanismo plan/run/gate y Tester ejecuta lo requerido; no ejecución desde transiciones. |
| Escritura fuera del alcance | Artefactos no afectados, sujeto al gate | Responsable resuelve esa ruta; si se conserva, ampliar/revisar/autorizar alcance; si se revierte, contrastar restauración y huellas. No resetear toda la HU. |
| Contradicción funcional | Trabajo independiente y evidencia que no depende de la decisión | Responsable decide; luego reconciliar criterios/selección/checks afectados. Repetir validación sin decisión no sirve. |
| Nuevo título/cuerpo, rama, repo o acciones PR | Pruebas técnicas si sus entradas no cambian | Volver a presentar solo el paquete de entrega alterado y su autorización; no repetir pruebas por título editorial. |
| Se añade recibo humano o movimiento previsto de Archive | Autorización del contenido ya presentado | Contrastar referencia humana, proyección y mapa; no pedir aprobación de la aprobación. |

Criterio demostrable de resolución local: el único diff fuera de outputs derivados autorizados es cero; hash de candidato técnico/plan/criterios/reglas/configuración/entorno no cambia; recibos íntegros y vigentes; gate válido antes/después; informe muestra la referencia corregida y ninguna suite invocada. Si uno falla, no declarar corrección local. Una aprobación humana no reemplaza ninguna de esas comprobaciones técnicas.

### 7. Objetos y formato humano

`docs/plantillas/evidencia-hu.md` renderizará `docs/hu/<change>/evidencia.md` con inventario de objetos: `object_id` local estable, nombre/tipo, HU/change, capas/capacidades (o motivo no-aplica), operación prevista/real, rutas, criterios, reglas, referencias de implementación/entrega/verificación. Estados independientes: `planned`, `implementation` (`not_started|implemented|not_applicable`), `deployment` (`not_performed|evidenced|not_applicable`) y `verification` con objetivo (`code|deployed_object`), estado y evidencia. No se infiere un estado del anterior ni se exige desplegar para cerrar una HU cuyo alcance es código/documentación. No duplica contratos funcionales ni construye linaje operativo.

Formato común de handoff humano y salida del principal, generado desde sus campos:

```text
HU y fase: ...
Resultado: ...
Alcance/candidato: ...
Reglas y evidencia: ... [enlaces]
Bloqueos/pendientes: ...
Decisión requerida: ninguna / decisión concreta y referencia
Siguiente paso: ... [handoff canónico]
```

El resumen de Planner muestra criterios/plan; el de Tester resultados; el de cierre contenido/acciones autorizables. No afirma ejecución de un agente por existir su TOML; `agent_id=null` y explicación si se trabajó en una sesión autorizada. Esta propuesta no produce handoffs falsos ni un inventario de objetos como si los cambios estuvieran implementados.

### 8. Título y cuerpo del PR llegan al destino

`docs/plantillas/pr.md` es la fuente de **estructura** única para ambos proveedores. El principal materializa para la HU `pr-title.txt` y `pr-body.md` (solo contenido transportable), y `pr.md` como vista de identidad/estado/enlaces a esos archivos. Sus paths y SHA-256 se referencian en el handoff de entrega antes de autorización; no extraer la plantilla completa con sus instrucciones como descripción. No crear plantilla nativa GitHub en este incremento. Si se añade después, debe generarse desde la fuente canónica y verificarse por comparación, sin segunda edición manual.

Contenido paralelo para ambos: problema y comportamiento resultante, alcance, HU/OpenSpec archivado, pruebas realmente ejecutadas/limitaciones, reglas/excepciones pertinentes y referencias de objetos/entrega. La configuración `delivery.pr_template` sigue apuntando a la fuente canónica; `pr_creation.github=manual_link`, Azure Services `cli_after_explicit_approval` y Server formulario se mantienen. No se activa creación GitHub automática ni se instala una CLI por una HU.

GitHub: construir formulario real del repo con origen/base codificados y título/cuerpo de esos archivos. Comprobar que al decodificar sus parámetros recupera exactamente ambos textos; cuando la herramienta de navegador esté disponible, comprobar campos efectivamente preparados. Esa comprobación solo acredita el formulario. Si URL/contenido excede límites, existen restricciones o no puede verificarse el transporte, entregar título/cuerpo exactos por separado con instrucciones de pegado; marcar «borrador; formulario con contenido pendiente de confirmar», no «formulario preparado» completo. No adivinar límites fijos ni afirmar PR creado a partir del enlace. Si la persona lo crea, solo cambiar a creado/verificado tras lectura accesible del PR real.

Azure Services: cargar esos mismos archivos UTF-8 mediante argumentos estructurados, preservando saltos, Markdown, Unicode y caracteres especiales; no concatenar shell ni usar Invoke-Expression. Antes de crear, comprobar autorización, repo/origen/base y push/SHA confirmado, consultar PR existentes y seguir la CLI ya documentada. Tras crear, leer ID/URL, estado, repo, ramas, commit origen **y título/cuerpo**; comparar contenido exacto con normalización exclusiva CRLF/LF y un salto final, manteniendo espacios significativos. Discrepancia no se resuelve reescribiendo remoto sin permiso: se informa. Timeout exige reconciliar antes de reintentar. Falta CLI/login/permisos permite borrador/formulario con estado honesto, no instalar ni afirmar éxito.

Estados de entrega: `draft`, `form_prepared`, `creation_unconfirmed`, `created_verified`; la respuesta indica actor/método y límites. «PR en estado draft del proveedor» es una propiedad distinta de `draft` local. Archive solo no habilita push; push solo no habilita crear PR. Si una respuesta ya cubre cambio/candidato, acciones, remoto, ramas y título/cuerpo presentados, se consume sin confirmaciones repetidas. SHA/push/ID/URL finales van en la respuesta y recibo posterior separado si se solicita, sin editar el commit para insertar su propio SHA. Merge, auto-complete, borrado y deploy quedan fuera.

### 9. Paradas integradas

| Operación | Condición concreta | Continuación permitida |
| --- | --- | --- |
| Propose | Falta decisión necesaria para definir comportamiento | Conservar borrador y pregunta precisa; explorar lo independiente. |
| Apply | Falta nueva autorización aplicable, conflicto crítico o alcance diferente del aprobado | Reconciliar solo la parte afectada; nunca implementar lo pendiente. |
| Sync | Revisión desfavorable, evidencia requerida ausente/obsoleta o comportamiento no aprobado | Hallazgos al responsable, conservar resultados válidos. |
| Archive | Cierre no autorizado o expediente distinto del presentado | Presentar diferencia y obtener decisión del cambio relevante. |
| PR | Destino/contenido no autorizado, evidencia inválida o publicación no confirmada | Conservar borrador, verificar/reconciliar remoto; no duplicar efectos. |

Estas condiciones preservan las restricciones actuales, incluso en piloto informativo. Leer una skill, pasar a otro rol o ejecutar una transferencia ya cubierta no exige otra aprobación. Una omisión descriptiva no se equipara a falta real de permiso. No se confunde aprobación técnica con autorización de entrega.

### 10. Tres recorridos breves

**HU Silver/Spark válida:** `normalizar-contactos`, ID local, sin ID Boards. Proyecto sintético ha aprobado la identidad, nulos, conservación y deduplicación de su Silver. Planner selecciona comunes+Silver+Spark, define criterios y checks del catálogo; presenta `planificacion-1.json` sin resultados. La persona solicita Apply para ese candidato/alcance. Principal comprueba `to_apply` en informative y despacha Developer con rutas exactas. Developer entrega código/tests, principal genera plan final y Tester ejecuta checks disponibles autorizados; un runtime requerido solo avanza si hay adaptador habilitado y evidencia real. Reviewer consume gate/recibos y verify, hace Sync favorable. Persona autoriza cierre y acciones de publicación expresamente presentadas. Se validan Archive y entrega sin otra pausa por rol. Inventario acredita código y sus pruebas, sin deducir despliegue. Este recorrido es condicional: 0.1.4 trae Spark/runtime inactivos; no afirma que puedan ejecutarse hoy.

**HU documental:** `aclarar-guia`, `layers=[]`, `capabilities=[]`, motivo «solo documentación de instalación, sin datos ni runtime». Aplica comunes pertinentes; Planner asigna `docs/configuracion-manual.md` y el expediente, con revisión de enlaces/instrucciones y checks documentales proporcionales del catálogo. Si no hay un check pertinente, se define/revisa antes de Apply conforme a la política existente, sin inventar un passed. Handoff y resumen no piden pruebas Spark; objeto `guia-instalacion`, implementación documental, despliegue no-aplica. Mantiene revisión y cierre autorizados.

**Transición detenida y corrección focalizada:** antes de Sync, gate observa que `src/silver/contactos.py` cambió después del recibo. Informe `EVIDENCE_CURRENT`: esperado candidato X, observado Y, causa `GIT_OR_CONFIGURATION_CHANGED`, responsable principal/Tester según selección; conserva recibos X como historia y trabajo no afectado; exige plan final y evidencia requerida del candidato Y. Gate existente ya impide Sync incluso en informative. Variante: Tester escribió `src/silver/contactos.py` desde su snapshot de entrada; `WRITE_SCOPE` informa path/hash/intervalo, no atribuye el diff anterior de Developer. En enforcing con esa condición habilitada bloquea la transición; en informative registra would_block y se mantienen las restricciones actuales del rol. Resolver solo ese cambio (restauración revisada o ampliación autorizada y nueva revisión), sin reiniciar toda la HU. Si el problema era únicamente un enlace faltante a un recibo vigente, nuevo handoff y gate bastan, sin nueva suite.

## Risks / Trade-offs

- [Proyección demasiado permisiva oculta cambios] → Lista exacta, generadores deterministas, entradas canónicas y recibos de exclusión; vista completa intacta y casos de inyección de criterios en Markdown derivado.
- [Proyección demasiado estricta repite pruebas por metadatos o commit] → Casos antes/después de handoff, aprobación, Sync/Archive y stage/commit; política congelada, recibos de observación separados, misma huella técnica por contenido y gate sin suites. No activar bloqueos nuevos antes de probar ambos sentidos.
- [Confundir JSON válido con resultado correcto] → Separar schema, integridad, gate, revisión funcional y autorización; conservar límites y estados sin ejecución.
- [Atribución imposible por escritores externos] → Un escritor secuencial, snapshots verificables y diagnóstico de incertidumbre; no prometer aislamiento de Codex.
- [Duplicación normativa y de resúmenes] → Obligaciones en constituciones; ejemplos en buenas prácticas; resúmenes derivados de handoff; referencias en vez de logs o specs copiadas.
- [Fuente versionada dentro de artifacts resulta menos cómoda] → Mantener convención real ahora; guardas contra sobrescribir versiones. Una reorganización de fuente se trataría por separado.
- [GitHub formulario o Azure altera contenido] → Comprobar transporte y lectura real cuando proceda, conservar borrador con limitación si falla; no confundir preparación y creación.
- [Conservadurismo de plan/run/gate impide adopción selectiva entre planes] → Declarar el límite, preservar historia y ejecutar lo requerido por plan vigente; no ampliar cross-plan reuse en este incremento.

## Migration Plan

1. Solo después de una nueva solicitud humana de Apply: preparar K1 desde K0 en staging independiente; registrar hashes base y preservar ZIP/manifiestos 0.1.3/0.1.4. No ejecutar autoría/packaging 014 sobre versiones previas.
2. Actualizar herramientas y schemas de K1 juntos; extender configuración de manera opcional. Probar ausencia de extensiones con una configuración 0.1.4 intacta. La política/catálogo de checks y gates existentes no se degradan.
3. Adoptar en repositorios consumidores mediante diff revisado de AGENTS, perfiles, schemas y plantillas; conservar personalizaciones, no copiar configuración genérica encima de valores del proyecto. No importar handoffs o aprobaciones antiguas como nuevos.
4. Empezar nuevas HU con informative y reglas activadas solo donde el responsable las haya completado. No exigir reconstruir retrospectivamente expedientes cerrados. HU en curso conserva herramientas/contratos iniciales hasta un punto de migración explícito, sin mezclar planes/recibos de proyecciones distintas.
5. Verificar casos locales de las cuatro specs, regresión de pruebas y paquete: inventario/hash, ZIP, neutralidad, upstream/licencias e integridad de K0. Actualizar README de desarrollo y documentación de validación solo en implementación autorizada, con resultados reales.
6. Piloto en HU representativas y revisión del responsable usando evidencia normal; promover únicamente condiciones objetivas seleccionadas. El empaquetado local no autoriza publicar release ni realizar cambios remotos.
7. Reversión: conservar fuente anterior y diff de personalizaciones. Retirar las secciones opcionales nuevas junto con restaurar herramientas/schema anteriores de forma revisada; conservar expedientes nuevos como evidencia no consumida por la versión antigua. No borrar resultados ni fingir que aprobaciones de K1 pertenecen a 0.1.4. Volver de enforcing a informative requiere decisión explícita; nunca desactivar controles técnicos existentes para sortear un fallo.

## Open Questions

No hay una decisión funcional pendiente que impida redactar esta propuesta. Son elecciones **propuestas, aún no aprobadas**: versión candidata 0.1.5, árbol mantenido versionado, contratos opcionales con informative y transporte por proveedor conservado. Su revisión forma parte de la aprobación del diseño; no se iniciará Apply automáticamente.

Antes de adopción real quedan datos del proyecto que no pueden inventarse: responsable autorizado, reglas específicas de cada capa/capacidad, excepciones permitidas, rutas por HU y checks/entornos habilitados. El responsable elegirá las HU representativas y, después de observarlas, los IDs que habilita como bloqueantes. Esas decisiones se registrarán en el expediente correspondiente; no añaden una fase, plataforma o HU de gobierno obligatoria.
