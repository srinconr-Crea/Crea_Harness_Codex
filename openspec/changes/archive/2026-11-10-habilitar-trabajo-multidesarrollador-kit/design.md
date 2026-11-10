# Design

## Context

### Evidencia inspeccionada

La fuente de este diseño es el checkout `harness`, rama `Crea_Harness_Codex_MVP_0.1.8`, commit `c89e18b4fc26edacbc7fe38c3e7643b5e12a762c`. La referencia de seguimiento local coincide. Durante Explore se comprobaron los 464 archivos del manifest y la equivalencia árbol/ZIP; SHA-256 del ZIP: `623aa722ae22f0c18b4326d11a3a542458e75cdbe00bff9a056927d089d951cc`. La consulta remota falló por credenciales y el Python disponible no tenía PyYAML: esa inspección no acredita actualidad remota ni validación estricta ejecutada.

Los artefactos de esta propuesta son planificación. Las capacidades descritas como nuevas no están implementadas. Ver `proposal.md` para la motivación.

| Fuente 0.1.8 | Comportamiento observado | Consecuencia de diseño |
| --- | --- | --- |
| AGENTS y `.agents/skills/Crea/orquestador/SKILL.md` | Roles secuenciales, pausas OpenSpec, archivo/publicación autorizados | Conservar por checkout; no instalar coordinación central |
| `docs/proyecto.json`, schema, entrega y plantilla PR | `project.base_branch` gobierna creación y PR | Añadir un único destino independiente con fallback |
| `scripts/crea/testing/git_adapter.py` | Git completo, `collect()` exige base ancestro de HEAD, `verify_commit()` contrasta contenido/rango | No pasar una quality divergente como base técnica; separar procedencia |
| `scripts/crea/transiciones.py` | Digest de entrega ya incluye ramas; gate y verificaciones de commit/push/PR | Reutilizar instancia canónica y comprobar destino efectivo |
| `scripts/crea/contexto.py`, CONTEXTO | Mapa opcional, selección de dependencias, límites, impacto documental | Añadir recorrido inverso reutilizable, sin otro mapa ni activación |
| `testing/catalog.py`, attempts, workflow y CICLO-VIDA | Catálogo único, outputs HU/intento, selección, inventario y gate | Proponer checks existentes; no otro framework o adopción cruzada |
| `testing/execution.py`, `workflow.environment()` | Python absoluto, fingerprint de ubicación/intérprete/paquetes | Resolver entorno personal consistentemente antes de plan/run/gate |
| `testing/kit_validation.py` | Validación offline; manifest completo solo con original | Separar validación del cliente de integridad original |
| Prompt A/B y guía | Setup inicial y actualización; sin preparación de persona | Añadir C y una entrada incluida en el clon |
| Empaquetador 018 y pruebas de distribución | Staging dirigido e historia preservada | Candidato nuevo y baseline de las versiones anteriores |

El motor `src/harness_local` no está instalado por el kit manual. Se trabaja sobre los helpers portables y sus contratos. Las specs permanentes `manual-phase-contracts`, `manual-delivery-traceability`, `manual-kit-distribution`, `project-context-lifecycle` y `project-testing-lifecycle` se amplían, sin recrearlas.

### Matriz de cobertura actual

| Necesidad | Actual | Brecha cubierta aquí |
| --- | --- | --- |
| Reglas, perfiles, specs, catálogos compartidos | Implementado | Documentar revisiones e independencia de checkouts |
| Feature por HU y publicación autorizada | Implementado proceduralmente | Resolver destino independiente y comprobar referencias efectivas |
| Origen/destino independientes | Pendiente | Extensión de delivery |
| Contexto por componentes | Implementado opt-in 0.1.7 | Consumidores inversos y lectura entre revisiones |
| Pruebas por HU/intento sin cambiar setup | Implementado opt-in 0.1.8 | Resolución de intérprete por máquina y recomendaciones por destino |
| Dos HUs contra destino cambiante | Pendiente | Snapshot, informe, vigencia y casos A-F |
| Preparación del segundo desarrollador | Parcial | Entrada C, skill, diagnóstico y binding |
| Distribución/exclusiones | Parcial | Composición e integración inicial revisada |
| Integración humana, quality y test | Proceso del equipo | Conservar límites |

## Goals / Non-Goals

**Goals:** mantener una fuente versionada por tipo de contexto y un catálogo de pruebas; hacer explícitas identidades Git y de entorno; limitar inspecciones a cambios relevantes; permitir reanudación sin repetir evidencia o permisos intactos; entregar un candidato local nuevo y una migración revisable para clientes anteriores.

**Non-Goals:** sincronizar sesiones, asignar turnos globales, coordinar todos los Codex, implementar colaboración de edición, crear infraestructura/pipelines, ejecutar merge/rebase/cherry-pick resolutivos, auto-complete, promociones a test, despliegues o escrituras Boards. Tampoco se habilitan runtime, CI, SAST/mutation, evals o reutilización entre planes inactivos. Preparar la máquina no demuestra agentes nativos, hooks activos ni permisos de publicación.

## Decisions

### D1. Un cambio y un candidato; incremento interno sin publicación

La persona pidió un único cambio extenso. Todos los incrementos apuntan al staging nuevo `artifacts/crea-manual-kit-0.1.9/` y a `scripts/package_manual_019.py`; la versión es la siguiente disponible observada y se registra como decisión de diseño, no como release publicado. Si aparece una colisión antes de Apply, resolver la identidad del candidato antes de escribirlo.

Se preservan 0.1.3-0.1.8, ZIP, manifest y hashes. El empaquetador nuevo no invoca scripts antiguos que muten sus árboles. La baseline captura los bytes de entrada reales y detecta personalizaciones; los archivos locales previos ajenos a este cambio no se incorporan a ciegas.

Alternativas: seis cambios independientes facilitarían entregas separadas, pero ya fueron descartados por la petición de un solo cambio; modificar 0.1.8 rompería su procedencia. Se conserva modularidad mediante tareas y contratos dentro del mismo expediente.

### D2. Una sesión por persona y checkout independiente

```text
Contexto, reglas, specs y catalogos versionados en remoto
                  |
          +-------+-------+
          v               v
    Checkout A       Checkout B
    Entorno A        Entorno B
    Codex A          Codex B
    Roles sec.       Roles sec.
          |               |
    feature/HU001   feature/HU002
          +-------+-------+
                  v
             PR a quality
                  |
          Revision/merge humanos
                  |
          Promocion a test del equipo
```

`workflow.max_active_agents=1` y un escritor por archivo se aplican a la sesión/checkout. Se pueden usar clones o worktrees independientes; no se permiten dos sesiones escritoras compartiendo el mismo árbol/index bajo la promesa de aislamiento. No se añade un lock distribuido ni una identidad de agente inventada. El nombre de feature identifica HU; si hay colisión, sufijo acordado y registro, no reutilización de rama ajena.

### D3. Configuración mínima de entrega y origen verificable

Añadir `delivery.pr_target_branch: string|null`, con null/ausencia como fallback exacto a `project.base_branch`. Continuar con `delivery.remote`, un único repositorio/remoto por entrega en este incremento. No se añade destino cross-repository ni evaluación genérica de punteros JSON. `base_branch_ref` heredado no se convierte en un lenguaje de resolución.

Añadir `delivery.compatibility` opcional con `enabled: boolean`, false en la plantilla. Ausente equivale a deshabilitado. No duplicar modo/enforcement dentro de esa sección: se usan `workflow.transitions` y sus promociones existentes. El perfil de equipo es una receta documentada de valores revisados de base/destino/protegidas y opt-in; no añade un selector de perfil ni habilita capacidades por inferencia.

El perfil de equipo propuesto usa base `sprint/XX`, destino `quality`, prefijo `feature/` y `protected_branches` que incluye `quality` y `test`; son ejemplos, no valores impuestos a todos los clientes. Tanto helpers como orquestador contrastan que la feature no sea base, destino o protegida; en perfil de equipo quality/test son reservadas para integración. Legacy sin perfil/opciones mantiene su comportamiento anterior.

`scripts/crea/entrega.py` será el helper común para resolución y diagnóstico, no un publicador autónomo. Valida refs con Git, nombres completos, remoto/repo configurados y reales, códigos de salida y SHA. No usa la configuración global como destino implícito. Principal mantiene la ejecución autorizada de creación de rama, stage, commit, push y proveedor.

Antes de la primera escritura: checkout/índice limpios, HEAD y base publicados, identidad de repositorio, feature libre local/remotamente y base remota comprobada. Reanudación verifica la rama y expediente originales; no crea otra ni hace stash/reset. `ls-remote` con código 2 representa ausencia; un error no representa ausencia. Un refspec que no actualice la tracking ref obliga a resolver el objeto correcto. Los remotos con credenciales en URL se rechazan o sanitizan sin persistir secretos.

Identidades diferenciadas:

| Identidad | Función | Persistencia |
| --- | --- | --- |
| B, `branch_start_sha` | SHA remoto desde el que nació la feature | Procedencia inmutable referenciada en el expediente |
| V, base técnica | Ancestro usado por el plan/verify_commit de un intento | `scope.base` y plan existentes; no cambiar silenciosamente |
| H, candidato | HEAD más observación completa de contenido durante trabajo; SHA final para entrega | Snapshot/candidate_digest y delivery existentes |
| Q, `target_sha` | Punta del destino al observarlo | Snapshot de destino con fecha y resultado de adquisición |

Añadir `scope.git_delivery` opcional al handoff con nombres de base/feature/remoto y B; añadir `evidence.compatibility` opcional como referencia al informe. El destino del PR sigue siendo solo `evidence.delivery.target_branch`. No modificar el significado de `scope.base`, candidate_digest o digest de entrega histórico.

Comparar commits alcanzables desde B ausentes de Q (`Q..B`), commits publicables desde H ausentes de Q y diferencias relevantes. Así se detecta trabajo heredado de sprint que el PR llevaría a quality. No descartarlo por ser ancestro de la HU ni ampliar approved_paths. Si está fuera de la autorización, mantener el pendiente de alcance; el equipo decide cómo alinear ramas. Tras integración manual externa, conservar B y acordar V nuevo solo si es ancestro real del nuevo H; nuevo plan donde proceda. `verify_commit()` conserva comprobaciones de contenido, rango e índice, sin una excepción general para commits ajenos.

### D4. Separar adquisición remota, inspección pura y simulación

Tres operaciones explícitas evitan ocultar efectos bajo un check:

1. `entrega.py snapshot --repo . --change <id> --attempt <id> --out <ruta>`: principal consulta el destino exacto con credenciales disponibles. Si requiere objetos, fetch de refs exactas a referencias auxiliares acotadas, nunca a ramas de trabajo. Contrasta el SHA obtenido con la respuesta remota. No login, instalación, merge ni uso de caché como actualidad. Si cambia durante adquisición, conservar observación no estable y terminar indeterminado; no bucle automático de reintentos.
2. `compatibilidad.py inspect --repo . --handoff <ruta> --target-snapshot <ruta> [--out <ruta>]`: solo lecturas de snapshots/objetos locales y stdout por defecto. Sin red, procesos de suite, creación de objetos o temporales.
3. `compatibilidad.py simulate --repo . --target-snapshot <ruta> --source-sha <SHA> --scratch <ruta-local> [--out <ruta>]`: cálculo Git explícito en almacenamiento temporal aislado, sin refs/index/worktree del usuario. Sus archivos temporales son un efecto declarado. La exportación persistente exige destino explícito nuevo en la HU.

Los nombres son interfaces a implementar y sus ayudas deberán exponer estos límites. El contrato no obliga a ejecutar comandos con placeholders.

Git `merge-tree --write-tree` crea objetos y reproduce detección de renombres/conflictos sin escribir índice/worktree ni crear un commit; por eso no se ejecuta en la inspección pura. Usar objetos temporales o repositorio auxiliar controlado, validando rutas absolutas, enlaces/junctions y configuración aplicable antes de operar. No cargar drivers externos, hooks ni comandos cliente sin revisión; si la equivalencia con las reglas reales del repo no puede acreditarse, declarar el límite. No usar `git merge`, `rebase`, `checkout` o `reset` como fallback. Referencia de diseño: https://git-scm.com/docs/git-merge-tree.

Múltiples merge-bases se registran; la simulación puede consolidarlas con el mecanismo Git soportado, pero el análisis de procedencia no elige arbitrariamente una. Historia parcial, objetos ausentes o relación no representable dejan la dimensión indeterminada. No usar `--allow-unrelated-histories` para forzar una respuesta.

### D5. Snapshot e informe, canónicos y acotados

Nuevos schemas en `docs/plantillas/`: `git-target-snapshot.schema.json` y `compatibilidad.schema.json`, con `schema_version="1.0"`, tipos cerrados y referencias existentes path/hash. Las rutas finales se crearán exclusivamente bajo `docs/hu/<change>/compatibilidad/attempt-<id>/`; snapshot, informe, simulación y revisión semántica tienen archivos distintos, sin sobrescritura o renumeración silenciosa.

Snapshot: HU/intento, repo/remoto/refs, Q o null, fecha UTC, resultado `verified|missing|access_denied|connection_error|unverified`, objetos disponibles, versiones/herramientas y límites. La clasificación del fallo solo será específica cuando esté sustentada; mensajes ambiguos quedan unverified. Una firma JSON no acredita identidad humana ni autenticidad frente a alteración coordinada.

Informe: anclas B/V/H/Q y digest del candidato local, merge-bases, grupos de cambios, componentes/relaciones, contratos/rule IDs, documentos, checks recomendados, evidencia usada, hallazgos y límites. Las referencias identifican revisión/objeto y hash del contenido; no contienen textos enteros, secretos o historia ajena. `semantic_review_ref` identifica la evaluación del Reviewer y sus límites; no es un passed generado por el parser.

Tres ejes independientes:

| Campo | Valores | Interpretación |
| --- | --- | --- |
| `outcome` | compatible, requires_review, conflict_detected, undetermined | Conclusión dentro del alcance comprobado |
| `coverage` | complete, partial | Dimensiones completadas; detallar las ausentes |
| `freshness` | current, stale, unverified | Coincidencia del destino con el instante contrastado |

Cada dimensión (`git`, `dependencies`, `contracts`, `documentation`, `test_impact`) informa complete/partial/not_run y hallazgos. Un conflicto conocido conserva conflict_detected aunque otra dimensión esté incompleta. Una decisión identificada sin resolver produce requires_review; una carencia material que impide concluir produce undetermined. Compatible exige ausencia de hallazgos pendientes y cobertura suficiente para el alcance declarado, incluyendo revisión semántica pertinente; no prueba ausencia universal de defectos. Sin mapa se puede acreditar un alcance Git/documental limitado, pero no independencia funcional por falta de relaciones.

### D6. Impacto proporcional y casos A-F

Calcular cambios propios desde B y la observación completa actual; cambios del destino desde sus ancestros comunes relevantes con B/H; alcance heredado B no contenido en Q; y cambios desde Q anterior cuando la relación sea verificable. Un force-update del destino obliga a recalcular desde las anclas, sin asumir avance lineal.

Reutilizar parser NUL y lectura de árboles de `git_adapter.py`. No llamar a `collect(root, Q, ...)` si Q no es ancestro de H. Comparar también ambas rutas en rename/delete, cambios de modo/tipo y rutas de specs, configuración e inventarios compartidos. La vista preliminar incluye index/worktree/untracked; la observación final para PR corresponde al SHA publicado y su contenido aprobado.

Con contexto adoptado, construir el índice inverso del mismo catálogo `context_management.components[].dependencies`, con visitados. Mantener intacto el significado de `components_for()` legacy; exponer un helper puro compartido para dependencia/consumidor y motivos. Si la configuración del mapa difiere entre revisiones, contrastar las relaciones relevantes en ambos estados sin adoptar silenciosamente la del destino. Sin mapa, usar relaciones explícitas de catálogo y referencias OpenSpec disponibles y registrar límites. No crear otro inventario.

Contrastar requisitos y escenarios de specs, selección de constituciones, criterios y contratos productor/consumidor. Planner identifica intención y Reviewer juzga contradicciones con referencias; regex/IDs o hashes solo ayudan a localizar. Una modificación común de inventario puede ser aditiva y compatible. El análisis limita documentos a la unión pertinente, respeta budgets y exclusiones y no lee todas las HU archivadas.

| Caso/fixture de aceptación | Resultado requerido | Validación y acción |
| --- | --- | --- |
| A: misma base, HU001 integrada, componentes independientes | Compatible dentro del alcance comprobado | No bloquear por divergencia ni repetir suites intactas |
| B: HU001 cambia productor que consume HU002 | Requires_review | Mostrar relación, contrato y checks existentes; pedir candidato adecuado para combinación |
| C: misma spec/regla con resultados incompatibles | Conflict_detected funcional | Reconciliación humana con requisito y decisiones de ambos lados |
| D: archivos distintos, productor en centavos y consumidor en pesos | Conflict_detected funcional aunque Git esté limpio | No acreditar coherencia funcional por ausencia de conflicto textual |
| E: snapshot Q1, destino avanza a Q2 | Freshness stale y nueva observación | Recalcular solo impacto pertinente; conservar pruebas locales intactas |
| F: destino ausente/inaccesible/no verificable | Undetermined de lo no comprobado | Distinguir causas; trabajo local independiente puede continuar |

Los fixtures serán repositorios locales/snapshots sintéticos y revisiones semánticas explícitas, no un piloto real de dos personas ni evidencia de permisos remotos.

### D7. Selección de pruebas y conservación de evidencia

Consultar el catálogo único por inputs/reglas/criterios y el inventario lifecycle activo. El informe recomienda IDs con razones; no ejecuta checks, materializa suites ni altera policy. Relaciones no declaradas se informan; un check desconocido o runtime requerido inactivo conserva su pendiente/bloqueo existente.

Pruebas sobre H acreditan H y su entorno. La simulación Git no ejecuta ni valida semántica del árbol combinado. Si B requiere comportamiento combinado, el equipo prepara explícitamente un candidato autorizado y el flujo habitual produce plan/run/gate nuevos. Este cambio no implementa un runner de integración ni habilita adopción de recibos entre planes.

| Cambio observado | Conservación y revalidación |
| --- | --- |
| Q avanza en componente independiente; H/plan/inputs/entorno siguen iguales | Rehacer compatibilidad; conservar pruebas y permisos intactos |
| Corrección de enlace sin cambio funcional | Nuevo intento de handoff; revalidar contrato/gate sin run |
| Cambio de código/fixtures/configuración/criterios/expectativas o entorno consumido | Invalidación actual y nuevo plan donde corresponda; ejecutar selección existente, no importar recibos |
| Nuevo check obligatorio aceptado por impacto | Reconciliar alcance/plan y aprobación aplicables antes de ejecución |
| Expiración de evidencia según TTL existente | Aplicar el gate actual; no renovar fechas ni tratar el informe como sustituto |
| Cambio de título/cuerpo/repositorio/destino o alcance autorizado | Renovar solo la autorización afectada |

La identidad de plan actual puede invalidar el conjunto al cambiar una entrada. No se promete reutilización por check entre planes para aparentar invalidación selectiva. La proporcionalidad consiste en no crear invalidaciones por observación externa independiente y en seleccionar lo requerido del nuevo candidato con el mecanismo actual.

### D8. Handoffs, circularidad y transiciones

`scope.git_delivery` contiene procedencia declarada antes del plan y es funcional. `evidence.compatibility` es una ref opcional a un informe inmutable. Los informes ya existentes al congelar un plan conservan sus hashes. Un nuevo informe observacional previsto podrá tratarse como derivado exclusivamente mediante una regla explícita de proyección adoptada en el candidato nuevo; nunca por un wildcard de `docs/hu/` o `compatibilidad/`.

La regla registra identidad change/intento, tipo de artefacto y ruta exacta; mantiene snapshots Git completos y valida schema, anclas, digest del candidato, predecesor y references. Los bytes finalmente publicables se contrastan de forma independiente por `publication_paths` y `verify_commit`. No copiar al reporte un hash futuro de sí mismo, del plan o del commit que lo contiene. El SHA de resultado se entrega externamente según el contrato vigente.

Si el informe incorpora requisitos, checks, criterios o decisiones funcionales nuevos, no es un derivado inocuo: requiere reconciliar plan/contexto. La compatibilidad observacional y su timestamp no se añaden indiscriminadamente a `handoff_context()` ni al fingerprint técnico para invalidar todas las pruebas cuando cambia Q.

No modificar semántica de `content-v2` de planes históricos. Añadir una proyección identificada nueva `content-v3` solo para planes nuevos que adopten las extensiones; soportar lectura y comportamiento anterior de content-v2. La nueva versión conserva todas las verificaciones de entradas Git consumidas, árbol, índice, archivo/sync y handoffs históricos. Su regresión debe demostrar que un cambio funcional no puede esconderse en un informe. Sin adopción nueva, sin proyección nueva.

La compatibilidad se ejecuta al preparar revisión/PR y se consume en `to_pr`; la confirmación final de Q ocurre justo antes de crear/formulario, por principal. `transiciones.py` permanece offline: consume el recibo, no hace fetch. Condición nueva propuesta `TARGET_COMPATIBILITY_CURRENT`, inicialmente sin promoción; añadirla al enum/schema y a su consumidor como una única condición objetiva de freshness. La evaluación semántica se tramita con pending/decisiones existentes y no se autopromueve a un veto.

Mantener códigos existentes de transiciones: 0 inspección completada, 2 condición explícitamente promovida incumplida, 3 decisión humana pendiente, 4 indeterminación/error. El inspector devuelve 0 si completa la inspección aun con hallazgos, y 4 si no completa por fallo técnico; su outcome se lee del informe, no se deduce de exit 0. Los gates técnicos mantienen sus códigos y bloqueos. Un destino inexistente impide acreditar la creación de un PR por el control de destino existente, aunque el aviso de compatibilidad no bloquee la HU completa.

### D9. Resolución local del entorno con consumidores consistentes

La opción compartida `execution.local_environment_path` apunta a `.crea/local.json`; es opcional y requiere `python_executable=null`. Si no existe la opción se mantiene el intérprete absoluto legacy. Declarar ambas fuentes activas es error; no decidir precedencia oculta. El path es relativo, permitido y sin enlaces; el archivo local no almacena comandos o credenciales.

Nuevo `docs/entorno-local.schema.json`, cerrado:

| Campo | Uso |
| --- | --- |
| `schema_version="1.0"` | Versión del binding |
| `python_executable` | Ruta absoluta existente al intérprete elegido |
| `databricks_profile` opcional/null | Alias local elegido por la persona, contrastado con host/identidad al usarlo |

No incluir repo destino, modelos, argv, configuración de hooks, secretos o switches de capabilities. Git identity se conserva en configuración local de Git, no en el JSON compartido. El alias Databricks solo se consume para operaciones ya aplicables/autorizadas y no cambia el host/proyecto/target compartidos; si no hay alias se conserva el perfil compartido existente. MCP y credenciales se verifican por conexión real sin replicar configuración personal en `.codex/config.toml`.

`scripts/crea/entorno_local.py` resuelve el binding. `testing/workflow.py` integra una única resolución antes de load/make_plan/resolved_settings/current/run/gate y de attempts.resolve; conserva digest de configuración fuente y configuración efectiva. Nuevos planes registran procedencia de resolución, intérprete efectivo y schema/herramienta; el fingerprint existente sigue incluyendo ejecutable, ubicación y metadata de paquetes. El digest técnico consume solo los campos relevantes a la ejecución: cambiar un alias Databricks no usado no invalida pruebas Python locales.

La resolución resuelve identidad, no ejecuta el intérprete por sí misma ni cambia la política. El ejecutor conserva argv revisado y entorno mínimo. El validador estructural distingue plantilla sin preparar de binding explícito requerido ausente. La preparación proporciona diagnóstico parcial cuando falta; plan/run bloquean ejecución no resoluble sin instalar. Un informe histórico de otra máquina puede leerse, pero el gate no acredita su ejecución actual por trasplantarlo: no se promete verificación portable completa de entorno ajeno en este incremento.

La comprobación de adopción contrasta schemas y consumidores, no solo el manifest original. Los helpers nuevos exponen identificación de versión/contratos mediante su ayuda o una salida offline `--describe-contracts`; la preparación verifica los contratos de destino independiente, binding, compatibilidad y proyección que vaya a usar. Una clave permitida por un schema antiguo o una versión nominal de paquete no acredita soporte; falta de identificación deja pendiente la capacidad afectada sin ejecutar una opción supuesta.

El archivo local queda fuera de Git/contexto y del contenido funcional de archivos versionados, pero sus campos efectivos sí participan en la identidad de ejecución. La proyección nueva no permite ignorarlos. No cambiar rutas revisadas de JUnit/outputs o el digest del catálogo por máquina.

### D10. Preparación C: entrada persistente y script limitado

Añadir `.agents/skills/Crea/preparar-desarrollador/SKILL.md` (nombre `crea-preparar-desarrollador`), registrada en extensions para principal, y `docs/preparar-desarrollador.md`, accesibles desde AGENTS. La sección C del prompt apunta a esa entrada y acepta checkout, alcance de instalaciones, Python/perfil elegidos y lecturas autorizadas. No vuelve a pedir datos ya versionados ni permite editar los modelos compartidos.

`scripts/crea/preparar-desarrollador.py inspect --repo . [--online] [--out .crea/diagnosticos/<id>.json]` diagnostica sin imports cliente ni suites. Offline por defecto; online solo lecturas explícitas de repositorio/identidad/servicios aplicables con credenciales disponibles. No usa consultas Boards de bootstrap, pipelines ni escrituras de prueba. Una lectura no demuestra permiso de push/PR. Las ayudas y versiones reales gobiernan los comandos soportados, sin inventar flags.

El script no implementa un instalador universal: la skill realiza instalaciones concretas solo si están autorizadas y después de presentar herramientas/alcance necesarios; revisa dependencias en el intérprete elegido. Credenciales/MFA/confianza las realiza la persona; un aviso o comando disponible no autoriza login. `bind --repo . --python <ruta> [--databricks-profile <alias>]` es una operación explícita local que valida el schema, muestra diff y conserva bytes si son equivalentes; cambios permitidos se escriben de forma segura sin tocar archivos compartidos. Diagnósticos se exportan en rutas nuevas, sin sobrescritura.

Comprobar raíz, rama, remoto y versiones adoptadas; setup_complete de proyecto y política, schemas, registros, recursos requeridos, OpenSpec existente y opciones realmente soportadas por sus consumidores. Si falta onboarding, declarar blocked para iniciar Apply; C no lo completa. Si hay una HU activa, preparar solo lo que no invalide su entorno; cualquier actualización que lo cambie queda identificada y requiere tratar su efecto, sin migrar el plan.

Estados: ready (prerrequisitos locales aplicables comprobados), partial (pendientes/no comprobados y trabajo independiente posible), blocked (no puede empezar la continuación solicitada por un prerrequisito real). Código 0 diagnóstico completo, 3 intervención humana necesaria, 4 fallo de inspección. El estado ready no es certificación Desktop/runtime ni autorización de publicación.

Si falta una lectura personal que el proyecto exige para iniciar la HU, la inspección offline deja partial o blocked para esa continuación, no ready por omisión. Comprobaciones opcionales no solicitadas se identifican not_run y no se convierten en una exigencia nueva. El diagnóstico mínimo de dependencias usa la biblioteca estándar e imports diferidos: faltar PyYAML/jsonschema debe permitir informar ese pendiente de forma estructurada, sin instalar o abortar antes de producir diagnóstico útil.

Windows: Python explícito de `.venv/Scripts/python.exe` sin Activate; usar `npm.cmd` y `openspec.cmd` donde el wrapper ps1 no esté permitido. No cambiar ExecutionPolicy o defaults globales. No forzar instalación de GitHub CLI para Azure; no usar gh para crear PR GitHub en este contrato. No reinstall skills, init OpenSpec, hooks nativos o actualizaciones upstream desde C. Capacidad de agentes se verifica separadamente de TOML válido y se informa como no observada si no hubo piloto.

### D11. Composición de distribución y exclusiones desde A

Añadir `kit-composition.json` y su schema bajo docs con grupos `client_required`, `distribution_only`, `local_only`; enumeración/patrones POSIX revisados y comprobación de cobertura de cada entrada del manifest. Manifest conserva hashes del ZIP completo; composición describe qué se instala, no vuelve a inventariar negocio. El empaquetador y las pruebas comprueban dependencias/referencias/licencias. El prompt A consume esa composición mediante copia revisada, no una copia masiva.

| Grupo | Archivos y decisión inicial |
| --- | --- |
| Operación y configuración compartida | AGENTS, `.agents/skills`, `.codex` perfiles/config aprobados, docs proyecto/schema/contexto/prácticas/constituciones/plantillas/pruebas, scripts, requirements, recursos portables |
| Procedencia/validación compartida | `kit-manifest.json`, `kit-composition.json`, schemas, locks, `docs/licencias/` y NOTICE, docs de procedencia; guía VALIDACION resumida; `tests/crea/` disponible |
| Solo distribución | `Prompt_configurar-kit-proyecto.txt`, `LEEME-CREA.md`; ZIP/hash/recibos del empaquetador se conservan en el mantenedor |
| Negocio del cliente | Su código, suites/fixtures, docs funcionales, OpenSpec inicializado y expedientes; no forman parte de una plantilla ficticia |
| Local no versionado | `.crea/local.json`, `.crea/diagnosticos/`, `.crea/tmp/`, entornos/cachés/credenciales y estado propio de herramientas |

El prompt ya ordena no copiar LEEME; el nuevo perfil también deja el prompt fuera, tras sustituir sus consumidores por guía/skill persistentes. Inventario cliente omite sus `exists=true`; observed_kit_file_types conserva la observación del paquete como tal. `docs/configuracion-manual.md` describe A/B y enlaza C local sin enlaces rotos al prompt no copiado. El README de prácticas conserva la referencia al manifest como procedencia. VALIDACION describe el alcance actual y cómo acceder al paquete/evidencia del mantenedor sin afirmar que hay archivos de empaquetado dentro del clon.

`tests/crea/` se conserva porque documenta y prueba los helpers; no pertenece automáticamente al catálogo de negocio. Retirarlo será otra decisión fuera de esta composición inicial. El manifest no se exige como identidad de bytes del cliente ni se regenera con la personalización. `--original` se usa solo sobre distribución íntegra; sin ese flag, validador cliente comprueba estructura/referencias de su composición. La validación cliente no requiere prompt/LEEME ausentes.

Integrar desde A exclusiones específicas `.crea/local.json`, `.crea/diagnosticos/`, `.crea/tmp/` y sus equivalentes de contexto, junto con las exclusiones existentes para `.venv`, caches, secretos y outputs temporales. No ignorar `.crea/` completa si pudiera contener recursos compartidos futuros, ni `.codex/`, `.agents/`, docs, openspec o `*.log` globalmente. Los outputs declarados en `docs/hu` siguen siendo evidencia según sus contratos.

| Control | Efecto | Lo que no acredita |
| --- | --- | --- |
| Composición | Define qué se copia desde el paquete | Autorización de publicar cualquier archivo |
| .gitignore | Omite untracked locales coincidentes | Retirada de archivos ya versionados |
| exclude_from_context | Evita lectura contextual de contenido | Invisibilidad al inventario Git/alcance |
| approved/publication_paths + índice explícito | Restringe contenido revisado a publicar | Permiso para merge/deploy |

B muestra diff de exclusiones y composición contra el cliente; no elimina prompts, tests ni otros archivos ya rastreados sin decisión de migración específica. Un archivo personal ya rastreado se diagnostica y se propone corregir; no `git rm`, limpieza o retirada automática. La preparación C nunca realiza esta migración.

### D12. Flujos operativos completos

**Primer onboarding A:** preparar rama de setup separada; comprobar herramientas/autorizaciones; instalar por composición y combinar archivos; inicializar OpenSpec solo si corresponde al setup autorizado; configurar fuentes reales, catálogo y opcionales revisados; modelos/reglas del responsable, exclusiones y binding local; verificar original en staging y personalizado en cliente; commit local solo si se autorizó. Publicar/integrar el setup en la base compartida por el proceso del equipo; A no añade push/PR/merge implícitos.

**Segundo desarrollador C:** clonar o verificar el checkout ya clonado; abrirlo; localizar entrada en AGENTS; inspección local y versiones adoptadas; binding personal y herramientas dentro del alcance; autenticaciones interactivas; lecturas aplicables; diagnóstico. Configuración, modelos y reglas compartidos conservan bytes. Sin init, reinstalación de skills o actualización de kit.

**HU:** leer configuración y contexto del checkout; comprobar repo/base remota y crear feature libre desde B antes de escritura; Planner Explore/Propose y aprobación humana para Apply; Developer código/tests/documentos; principal reconcilia Git/criterios/inventario y plan final; Tester run, Reviewer gate/verify y semántica; snapshot/compatibilidad pertinente antes de cierre/PR; Sync y revisión de su diff con reconciliación funcional si corresponde; presentar candidato, contenido PR, alcance completo e informe; aprobación de archive/commit/push/PR según proveedor; Archive con mapa exacto; comprobaciones de índice, commit, push y SHA remoto; confirmar Q y compatibilidad antes de crear/formulario; verificar PR en Azure o preparar formulario/manual en GitHub/Server. Si Q cambió, nuevo informe antes de continuar lo dependiente, sin repetir permisos intactos. No editar evidencia versionada después solo para incluir su propio commit SHA.

Tras PR: termina el alcance del harness. Reviewer humano integra a quality y el equipo promueve a test mediante sus prácticas. El kit no configura políticas remotas ni pipelines y no garantiza que quality permanezca quieta después de la lectura final.

### D13. Corrección editorial sin alterar contratos históricos

Crear en el mantenedor `docs/erratas-kit-0.1.8.md`, con tabla de texto obsoleto, significado correcto y referencia a evidencia. Corregir en el nuevo staging encabezados LEEME 0.1.7, configuración 0.1.6, VALIDACION 0.1.7 y pruebas README 0.1.4; identificar versión vigente frente a versión de introducción.

Sección B pasa a indicar versión origen detectada y destino 0.1.9. Incluye comparación de tres vías verificable y adopción conjunta de contexto 0.1.7, lifecycle 0.1.8 y extensiones nuevas; no presupone que todos los clientes parten de 0.1.6 o ya adoptaron opcionales. A/B/C son independientes y se elige una. A conserva campos/autorizaciones existentes; C no pide cambiar modelos; B no resetea setup, reglas o catálogos.

No sustituir globalmente números: `source_version=0.1.7` de 0.1.8 es correcto, igual que revisiones upstream, contratos por versión y resultados anteriores. VALIDACION nueva distingue nueva evidencia de antecedentes, no reutiliza cifras anteriores como pruebas de código nuevo. La fe de erratas no reempaqueta 0.1.8. Actualizar README del mantenedor para que el candidato y sus límites sean inequívocos, sin borrar secciones históricas válidas.

### D14. Superficie exacta de archivos y pruebas

Todos los paths de kit de esta tabla son relativos al staging 0.1.9 futuro, no permiso para editar 0.1.8.

| Área | Modificar | Añadir |
| --- | --- | --- |
| Configuración/orquestación | `AGENTS.md`, `docs/proyecto.json`, `docs/proyecto.schema.json`, orquestador, cuatro perfiles solo para instrucciones pertinentes | Sin nuevos roles |
| Entrega | `docs/entrega-git.md`, `docs/plantillas/pr.md`, handoff.md/schema, `scripts/crea/transiciones.py` | `scripts/crea/entrega.py`, snapshot schema |
| Compatibilidad | `scripts/crea/contexto.py`, CONTEXTO, consumers de transiciones/proyección | `scripts/crea/compatibilidad.py`, compatibilidad schema y guía |
| Entorno/pruebas | `testing/workflow.py`, `attempts.py`, `git_adapter.py`, `schemas.py`, ejecución si requiere adaptar firmas, `pruebas.py`, execution.json/schema, `contract.py` solo si consume nuevos campos | `scripts/crea/entorno_local.py`, `docs/entorno-local.schema.json` |
| Preparación | Registros/extensions, catálogo de skills, configuración manual, prompt A/B/C | Skill preparar-desarrollador, script y guía local |
| Composición | `.gitignore`, exclude_from_context, inventario, `testing/kit_validation.py`, wrapper verificador y guías | `kit-composition.json` y `docs/kit-composition.schema.json` |
| Distribución mantenedor | README; evidencia nueva solo del cambio | Empaquetador 019, baseline y pruebas 019, fe de erratas |
| Regresión portable | Tests de contratos, transiciones, contenido, contexto, lifecycle, kit | Tests de entrega, compatibilidad y preparación/entorno |

No editar skills upstream OpenSpec/Databricks, hashes upstream, modelos/esfuerzos o hooks del cliente para introducir el flujo. Documentar excepciones locales existentes y preservarlas; no confundir soporte de varios hilos abiertos con simultaneidad de roles.

## Risks / Trade-offs

- [Inspección Git limpia con contradicción funcional] → Revisión semántica referenciada, cobertura explícita y casos C/D; compatible acotado.
- [Rama base lleva trabajo no integrado al destino] → Mostrar `Q..B` y alcance heredado; no atribuirlo a la HU ni autorizarlo por omisión.
- [Quality cambia entre lectura y creación/merge] → Comprobar justo antes del PR, registrar anclas/momento y dejar revisión final al equipo; no prometer atomicidad remota.
- [Refspec, shallow clone o force-update confunden historia] → SHA exactos, límites y diagnóstico específico; no merge-base arbitrario ni fallback a HEAD.
- [Scripts de merge o configuración ejecutable del cliente] → Simulación aislada, sin drivers no revisados ni ejecución de código cliente; resultado limitado si no es representativo.
- [Proyección excluye evidencia funcional] → Versión nueva opt-in, rutas exactas, schemas, anclas y verificación de bytes publicables; pruebas negativas de manipulación.
- [Binding personal debilita reproducibilidad] → Allowlist, resolución única, huellas efectivas y rechazo de evidencia de entorno distinto; sin overrides de política.
- [Adopción invalida una HU en curso] → Migrar en un punto acordado, conservar planes/handoffs y herramientas compatibles; no mezclarlos automáticamente.
- [Composición deja referencias rotas] → Validar instalación de cliente sin prompt/LEEME y conservar tests/licencias/procedencia; ninguna retirada automática en clientes antiguos.
- [Todo en un cambio aumenta revisión] → Incrementos internos con dependencias, fixtures y criterios; revisión final transversal, sin presentar tareas parciales como producto terminado.

## Migration Plan

1. En Apply autorizado, capturar baseline y crear staging 0.1.9 preservando fuentes y personalizaciones. No publicar.
2. Adoptar origen/destino y schemas/consumidores; probar fallback legacy y alcance heredado antes de integrar compatibilidad.
3. Integrar binding de entorno y resolución plan/run/gate; después preparación C. Clientes sin opción nueva mantienen camino antiguo.
4. Integrar snapshot/inspección/simulación, mapa inverso e informe; luego proyección/handoffs/transiciones, inicialmente informativos y compatibility.enabled=false en plantilla. A puede proponer activación opt-in revisada para el equipo.
5. Aplicar composición, exclusiones y documentación/errata. La instalación nueva conserva recursos operativos y deja prompt/LEEME en la distribución.
6. Probar fixtures nuevos y legacy, validación estricta original/personalizada, composición de copia, integridad árbol/ZIP y preservación 0.1.3-0.1.8. El empaquetado no instala, hace login o llama a remoto.
7. Para cliente existente, B compara fuente exacta/proyecto/candidato y combina config/schema/helpers juntos, preservando activaciones previas, reglas/modelos y evidencia. Si falta baseline exacta, documentar el límite y conservar personalización incierta. No resetear setup o activar opcionales.
8. Rollback: restaurar conjuntamente herramientas, schemas y configuración anteriores mediante diff revisado; conservar nuevos expedientes como historia no consumida. No reutilizar recibos nuevos en herramientas antiguas, borrar evidencia o desactivar gates para simular éxito.

La aceptación local del candidato requiere la matriz de `tasks.md` y todos los escenarios A-F. Una prueba real de dos desarrolladores, hooks, Azure o runtime solo se declara con autorización/evidencia separadas; su ausencia queda not_run y no se disfraza de certificación con fixtures. La validación de esta propuesta comprueba estructura y cobertura de planificación, no estos resultados de implementación.
