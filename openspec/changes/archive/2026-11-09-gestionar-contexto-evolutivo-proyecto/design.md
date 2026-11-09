# Design

## Context

Ver `proposal.md` para la motivación. Inspección de 0.1.6 sobre HEAD `13a2e1e`; fuente distribuible `artifacts/crea-manual-kit-0.1.6/`. No existe AGENTS raíz aplicable en el repositorio de desarrollo. El AGENTS del kit se analiza como producto, no obliga a iniciar otra HU para esta planificación.

| Evidencia actual, relativa al kit | Consecuencia |
| --- | --- |
| `docs/proyecto.json`: inventario `manual-reviewed`, `update_on_path_change`, exclusiones | Son datos declarativos; no hay reconciliación documental por HU. |
| `scripts/crea/testing/kit_validation.py` | Comprueba algunas rutas, no completitud ni significado documental. |
| `scripts/crea/transiciones.py`, `docs/plantillas/handoff.schema.json` | Ya existen selección de reglas, inspección por transición, modos, autorización y contratos estrictos. |
| `scripts/crea/testing/git_adapter.py`, `workflow.py` | Git completo, proyección content-v2, historia congelada, movimientos/sync exactos e invalidación. |
| `.codex/agents/*.toml`, orquestador y plantillas | Roles secuenciales; Developer puede editar documentación asignada; Tester/Reviewer no corrigen producción. |

OpenSpec conserva comportamiento funcional y archivo; el harness selecciona contexto, comprueba reconciliación y consume sus gates. Las specs históricas de `src/harness_local/` no acreditan capacidades instaladas en el portable. El nuevo diseño es transversal y altera contratos, por lo que corresponde crear este documento.

## Goals / Non-Goals

**Goals:** un mapa pequeño configurado una vez; selección e impacto deterministas; actualización por roles autorizados; bajo trabajo repetitivo; reanudación y compatibilidad verificables.

**Non-Goals:** redactar documentación automáticamente desde un diff, inferir todas las dependencias del código, imponer una constitución nueva, escanear semánticamente todo el repositorio, cargar todos los expedientes, instalar herramientas, ejecutar pruebas o controlar el contexto interno exacto de Codex. El ciclo de vida de pruebas se especifica por separado.

## Decisions

### 1. Extender el inventario y el contrato existente

Se propone `docs/proyecto.json.context_management`, opcional y desactivable. Contendrá `enabled`, `schema_version`, `components`, `impact_rules` y límites de lectura. No incorpora otro modo de bloqueo: se usa `workflow.transitions`.

Cada componente tendrá ID estable, patrones de rutas POSIX, IDs de dependencias declaradas y documentos con `path`, `kind` y roles/fases pertinentes. Los kinds distinguen configuración, orientación global, regla, spec, documentación técnica, HU e historia. Las reglas se resuelven con `select_rules`, no se crea otro catálogo normativo. Los documentos pueden enlazar decisiones existentes; no duplican sus textos.

Cada regla de impacto tendrá ID, componentes/patrones, disparadores declarativos (`path_change`, `behavior`, `architecture`, `dependency`, `configuration`, `tests`), documentos destinatarios y motivo. Git demuestra cambios de ruta; los disparadores semánticos son declaraciones del Planner contrastadas por Reviewer, no inferencias automáticas acreditadas. Se usa la misma semántica fnmatch POSIX sensible a mayúsculas del selector actual, documentando que `*` cruza `/`.

Alternativas: otro índice JSON duplicaría rutas y responsabilidades; instrucciones adicionales no permiten reconstruir decisiones; memoria vectorial/servicio no aporta garantías necesarias. Una extensión opcional y un helper bastan.

### 2. Separar fuentes canónicas de su mantenimiento

| Cambio observado/declarado | Documentos candidatos a revisar, solo si aplican |
| --- | --- |
| Alta, baja o movimiento de componente | Inventario/rutas y referencias técnicas. |
| Arquitectura, contratos o dependencias | Orientación global, documentación técnica y manifiestos reales; decisiones existentes enlazadas. |
| Comportamiento funcional | Delta OpenSpec; documentación funcional/técnica explicativa. |
| Obligación operativa | Constitución/práctica/AGENTS realmente dueña de esa obligación; requiere gobierno vigente. |
| Pruebas o configuración | Referencias de validación y guía de preparación afectada; el catálogo ejecutable pertenece al cambio B. |

La tabla es una pauta del kit. El cliente registra destinos reales; no activa documentos inexistentes. `openspec/config.yaml` conserva contexto conciso y referencias: no se añade una narración de cada HU ni se sincroniza con todas las specs por duplicación. Buenas prácticas contienen orientación técnica, no otra copia de las obligaciones. El inventario de objetos del handoff mantiene sus estados actuales y no se convierte en catálogo global de componentes desplegados.

### 3. Resolver referencias, no copiar dossiers

Nuevo `scripts/crea/contexto.py` con operaciones `select`, `impact` y `check`. Entradas: checkout, cambio exacto, rol/fase, configuración, handoff y observación Git del candidato. Salida JSON ordenada: fuentes seleccionadas, motivos, componentes, impacto, avisos y comprobaciones no realizadas. Sin fecha aleatoria en la identidad semántica.

Partir de rutas observadas y componentes explícitos de la HU; resolver únicamente dependencias declaradas alcanzables, con conjunto de visitados para ciclos. Deduplicar por ruta/finalidad; ordenar por ID/ruta. Reutilizar las funciones de Git, rutas seguras y schemas existentes; aceptar observaciones internas solo tras contrastar su identidad/vigencia. No aceptar un manifiesto manual como prueba de diff completo. Ningún resultado reemplaza el gate Git.

Leer primero metadatos y solo después archivos seleccionados. Reutilizar `inventory.exclude_from_context`; añadir como historia no seleccionada por defecto `openspec/changes/archive/` y otras HU. Una referencia histórica explícita permite lectura acotada salvo exclusión sensible. Las exclusiones nunca filtran Git, alcance ni entradas funcionales de pruebas. Rutas externas, traversal, symlinks/junctions y conflictos se diagnostican mediante los mecanismos seguros existentes.

Límites iniciales propuestos: 256 KiB por documento y 2 MiB de contenido seleccionado por operación, configurables tras revisión. Un exceso deja selección parcial con rutas omitidas, sin truncamiento silencioso ni aprobación ficticia; no añade veto en informative. No se intenta detectar todos los secretos por nombre: el helper evita superficies excluidas y no copia contenido a informes; el rol mantiene la revisión de confidencialidad existente.

### 4. Un contrato lógico congelado y observaciones por intento

Extender opcionalmente `handoff.schema.json` y el schema de procedencia del plan:

- `context.management`: versión, digest de política seleccionada, componentes, destinos documentales y motivos/roles. Solo obligaciones lógicas aprobadas, sin hashes futuros ni fechas variables.
- `evidence.context_review`: impacto previsto o revisión final, observación Git vinculada, fuentes consumidas y filas documentales. Fila: documento, regla/motivo, responsable, operación, estado `updated|unchanged_justified|not_applicable|pending`, justificación y referencias disponibles de revisión.
- Observaciones de fuentes: ruta, fase, hash observado y existencia. El hash inicial es una observación histórica vinculada al snapshot de entrada, no un `$defs/ref` que exija que el archivo actual siga teniendo bytes anteriores. Las referencias finales apuntan al contenido actual.

Antes de Apply se conserva impacto previsto, no resultados finales. El principal incorpora las rutas de actualización previstas a `approved_paths` y los `write_paths` del escritor autorizado. El plan final se genera después de reconciliar las modificaciones de código, inventario y documentos. Cambiar obligaciones, selección o alcance material vuelve al Planner y a las autorizaciones aplicables; un hash observado nuevo de una edición ya prevista no inventa una autorización ni obliga por sí solo a otro ciclo de preguntas.

Extender `handoff_context` para congelar la selección y política lógicas cuando se adopte la extensión; mantener la identidad anterior en planes legacy. Las observaciones de fase no hacen crecer el plan. Su exclusión como metadatos solo procede al validar schema, identidad, predecesor y consistencia con ese contexto. Los documentos reales, criterios y configuración permanecen funcionales. No excluir directorios documentales enteros ni usar un informe como autoridad semántica.

El nuevo módulo también participa en `adapter_digest`. Todos los handoffs ya existentes se congelan por el mecanismo actual. No se reescriben contratos ni recibos históricos.

### 5. Dos revisiones pequeñas dentro del flujo vigente

| Fase / dueño | Consume | Puede escribir | Comprobación / evidencia / continuidad |
| --- | --- | --- | --- |
| Onboarding / principal + responsable | Archivos, contexto y decisiones existentes | Configuración y combinación revisada | Mapa real y pendientes; no inventar decisiones. |
| Explore / Planner | Fuentes pertinentes y código | Solo captura autorizada por su skill | Discusión; no exige expediente nuevo. |
| Propose / Planner | HU, mapa, reglas y specs | Cambio y HU asignados | Impacto previsto; puede justificar ninguno. Nueva solicitud de Apply vigente. |
| Apply / Developer | Plan y selección aprobados | Código/docs/inventario asignados y handoff propio | Actualiza solo lo afectado; ampliaciones se reconcilian vía principal. |
| Preparación final / principal | Diff completo y handoff Developer | Contratos/plan propios | Contrasta impacto observado antes del plan final; no ejecuta suites. |
| Tester | Criterios, contratos y contexto de interpretación | Evidencia/handoff propios | Consume plan/run; no corrige documentos de producción. |
| Verify / Reviewer | Diffs, revisión documental y recibos | Hallazgos/handoff propios | Coherencia semántica y gate; registra disposición de pendientes. |
| Sync / Reviewer | Deltas y revisión favorable | Specs estables asignadas | Reconciliación final; diffs exactos previstos. |
| Archive / Reviewer | Autorización y expediente revisado | Movimientos previstos | Referencias por mapa exacto; sin conducta funcional nueva. |
| Entrega / principal | Contenido final aprobado | Git/PR dentro de autorización | Revalidar referencias y contenido publicado, sin repetir suites por rutina. |

Si la comprobación consume una spec modificada por Sync, no puede usar la equivalencia que excluye targets funcionales de checks: debe validarse el contenido resultante y, si invalida el plan, reconciliarlo explícitamente antes de cierre. Para referencias no funcionales se usa el mapa exacto de Sync/Archive existente, nunca equivalencia libre de documentos.

### 6. Política de fricción baja y códigos existentes

Registrar dos condiciones nuevas y opcionales: `CONTEXT_SOURCES_CURRENT` (referencias requeridas y lectura comprobables) y `DOCUMENTATION_IMPACT_RECONCILED` (impacto final resuelto). Extender enums y consumidores juntos. Arrancan sin promoción; para habilitarlas se requieren casos positivos/negativos y referencia humana. Reutilizar `promotion_ref`; no habilitarlas por número de HU exitosas.

Para las operaciones del helper y su consumo por transiciones: 0 = comprobación completa sin nuevo bloqueo habilitado (puede incluir avisos), 2 = condición promovida incumplida, 3 = decisión humana necesaria para la transición, 4 = error/indeterminación. Conservar clasificación y semántica de `consume`; un 0 no concede aprobación. El error informativo no crea un veto ni borra gates anteriores. Un error con condición promovida indispensable impide acreditar esa continuación concreta.

Una ausencia editorial emite aviso; una contradicción funcional sustantiva se trata con gobierno vigente. No hay confirmaciones por cada traspaso, nueva HU de gobierno para una errata, bucles automáticos ni reinicio de `max_fix_rounds`. Corregir referencias no consume una ronda técnica cuando no cambia candidato funcional.

No se releen documentos no seleccionados ni se ejecutan tests desde el helper. Registrar conteo de archivos/bytes leídos y duración aparte del digest. La aceptación usa fixtures con mucho contenido no relacionado para acreditar ausencia de lecturas, una ejecución Git compartida por inspección y cero procesos de suites; no inventa una promesa de milisegundos para todos los equipos. Revalidaciones de fronteras de fase y publicación se conservan.

### 7. Archivos y entregable mínimo

Modificar únicamente en el futuro candidato: `docs/proyecto.json` y schema; handoff/schema y plantillas de evidencia/tareas; `AGENTS.md`; orquestador; cuatro perfiles; `scripts/crea/transiciones.py`; `testing/{git_adapter,workflow,kit_validation}.py`; schema de plan cuando requiera procedencia; setup, contexto general, guías y tests pertinentes. Corregir la secuencia sin Tester y numeración duplicada de la plantilla como coherencia de esa guía.

Nuevos: `scripts/crea/contexto.py`, `tests/crea/test_contexto.py` y empaquetador de versión nueva. Los `$defs` del schema existente contienen los contratos nuevos: no se añade otro catálogo ni JSON por rol. Informes persistidos se integran en handoffs nuevos; la CLI solo puede crear un informe auxiliar permitido con `--out` explícito, validado como observación derivada exacta, o devolver stdout. No pasa a ser otro estado canónico.

Independencia del cambio B: no depende de sus schemas ni de un catálogo de tests nuevo. Cada cambio conserva sus campos opcionales. El segundo se aplica sobre la fuente realmente vigente y combina solo los puntos compartidos; una entrega conjunta puede usar 0.1.7 si sigue libre. Entregas separadas usan versiones sucesivas y una baseline explícita, nunca mutan una versión ya publicada.

## Risks / Trade-offs

- [Mapa incompleto] -> diagnóstico de desconocidos, revisión por impacto e incorporación solo de lo pertinente; no prometer descubrimiento semántico total.
- [Falso cumplimiento documental] -> separar evidencia automática de coherencia semántica revisada; una justificación vacía no satisface un control promovido.
- [Circularidad] -> obligación lógica congelada, observaciones por intento y documentos funcionales dentro del candidato.
- [Bloqueos excesivos] -> informative inicial, solo dos condiciones opcionales y continuidad independiente; no revisiones exhaustivas.
- [Contrato incompatible] -> extensiones opcionales y schema/adaptadores actualizados juntos; no migración retrospectiva.
- [Permisos supuestos] -> perfiles y snapshots orientan/detectan; solo el entorno impone aislamiento. El helper no es una frontera global.

## Migration Plan

1. En Apply autorizado, registrar baseline real y preparar una fuente versionada nueva desde 0.1.6 o su sucesora adoptada; preservar históricos.
2. Entregar helper y contratos como opt-in, con configuración ausente compatible e informative al adoptar. Combinar mediante diff sin cambiar modelos, constituciones ni decisiones del cliente.
3. Verificar recorridos sintéticos: HU documental, movimiento Python y HU Silver/Spark con runtime requerido inactivo; este último conserva blocked sin invocar remoto. Demostrar reanudación, refs corregidas, modo informativo y promovido.
4. Ejecutar regresiones focalizadas del kit y empaquetado/bytes; mantener separado el piloto real, sin declararlo ejecutado por tener fixtures.
5. Ofrecer promoción únicamente como decisión revisable del responsable; no activarla como efecto de instalar. Reversión conjunta de herramientas/schema/configuración mediante diff; preservar HU/recibos y no alimentar herramientas antiguas con contratos nuevos.

No hay tareas de instalación, push, PR, deploy ni adopción en un proyecto real autorizadas por esta propuesta.
