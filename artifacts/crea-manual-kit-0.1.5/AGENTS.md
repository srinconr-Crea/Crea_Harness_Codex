# Crea — instrucciones del proyecto

## 1. Inicio y fuentes de contexto

Al iniciar o reanudar una historia de usuario (HU), leer y seguir
`.agents/skills/Crea/orquestador/SKILL.md` (skill `crea-orquestador`).
Esta instruccion autoriza la delegacion local a planner, developer, tester y reviewer dentro
del alcance pedido por la persona. Para preguntas informativas no iniciar una HU.

Leer primero `docs/proyecto.json` y `docs/contexto-proyecto.md`; comprobar rutas
contra el checkout real. Leer `docs/buenas-practicas/general.md` y solo las practicas
de las herramientas afectadas. No cargar el catalogo completo de skills ni datos.
Leer project.repository y project.base_branch antes de operaciones Git; no inferir GitHub
por defecto. Azure Repos usa Git/GCM para clone/fetch/commit/push y Azure CLI con azure-devops para
consultar el repo y crear el PR en Services. Instalar solo durante el setup autorizado.
No invocar gh para Azure Repos. Sin Boards, pipelines, automatizaciones ni recursos Azure.
Si setup_complete=false, completar los datos imprescindibles antes de aplicar cambios;
se permite explorar y proponer sin inventar configuracion del cliente.

## 2. Flujo y responsabilidades

HU → planner → presentacion de artefactos → nueva indicacion humana de apply → developer
→ tester → reviewer → autorizacion humana de archivo/publicacion → archive → commit/push en feature → PR con az repos en Azure DevOps Services o enlace para crear PR en GitHub.
Principal: coordina y conserva decisiones; prepara rama de HU antes de la primera escritura
y realiza la entrega Git tras revision/archivo aprobados. No simula subagentes ejecutados.
Planner: explore opcional, propose o update del cambio existente; nunca codigo.
Developer: apply de OpenSpec, implementacion y tests previstos; entrega ready_for_test, sin completar tareas de ejecucion Tester ni archivar.
Tester: ejecuta la seleccion final con adaptadores locales, conserva recibos y entrega ready_for_review. No corrige produccion ni subdelega.
Reviewer: revision independiente de codigo, cobertura y recibos Tester; ejecuta verify.
No repite automaticamente la bateria: solo solicita al Tester checks invalidados, evidencia insuficiente o una regla fija de politica, con motivo registrado. Tras resultado favorable
ejecuta sync, presenta su diff y solicita aprobacion manual de archive a traves del principal.
Archive solo tras respuesta humana explicita para ese cambio/candidato.
Si las pruebas requeridas estan failed/blocked/not_run, no sincronizar ni archivar.

## 3. Reglas permanentes

- Un agente activo por vez; un escritor por archivo. Los roles no subdelegan.
- Respetar cambios previos y reglas del cliente; no sobrescribir configuracion ajena.
- No cambiar criterios para hacer pasar una prueba ni ocultar defectos.
- No incluir secretos, credenciales, salidas sensibles ni datos productivos en Git.
- Perfil Databricks elegido expresamente por la persona; comprobar identidad/host.
- Distinguir pruebas locales de ejecucion Spark/Databricks; un mock no prueba el runtime.
- No hacer deploy, push, merge, permisos ni escrituras remotas sin alcance autorizado.
- No instalar herramientas ni modificar configuracion global como parte implicita de una HU.
- Handoff con archivos, criterios, comandos, resultados y pendientes. Nunca afirmar passed sin evidencia.

## 4. Skills y contexto especializados

OpenSpec: seguir el SKILL.md real de cada operacion. `openspec update` actualiza
integraciones; `openspec-update-change` modifica artefactos del cambio, nunca codigo.
Conservar las pausas humanas de las skills: propose termina con artefactos y requiere una
nueva solicitud humana antes de apply; update-change pide confirmar sus revisiones antes de
escribirlas; explore pide confirmar la captura de artefactos salvo peticion explicita que la autorice.
El principal transmite estas solicitudes a la persona y espera su respuesta; su propio despacho
no constituye esa confirmacion. require_plan_approval no permite saltar guardrails upstream.
Si falta una skill requerida, detener esa fase y seguir la guia de configuracion.
Databricks: cargar databricks-core antes de CLI; especializar con dbsql, dabs, jobs,
pipelines, unity-catalog, python-sdk, apps o model-serving segun la tarea.
Consultar `docs/catalogo-skills.md`; no usar nombres de herramientas MCP supuestos.

## 5. Configuracion y extensiones

Fuente de rutas y extensiones: `docs/proyecto.json`. Catalogo ejecutable unico:
`validation.testing.policy_path`; required_checks contiene solo IDs de ese catalogo.
Leer `.agents/skills/Crea/crea-pruebas/SKILL.md` antes de planificar o validar pruebas.
Principal regenera el plan final desde Git completo antes de Tester; gate revalida Git,
configuracion, entorno, vigencia y recibos. Desconocidos bloquean; nunca omitir una capacidad requerida por estar inactiva.
Modelos/esfuerzos: `.codex/config.toml` y `.codex/agents/*.toml`.
Skills comunes: `.agents/skills/Crea/`; propias: `.agents/skills/Project/`.
Agregar skills/agentes/MCP/hooks siguiendo `docs/extensiones.md` y actualizar el inventario.
El JSON orienta al agente; no es una barrera tecnica de permisos ni registra hooks nativos.
Las skills upstream se conservan sin cambios; overrides propios se documentan en Crea o Project.

## 6. Cierre y reanudacion

Guardar evidencia en `docs/hu/<change>/evidencia.md`, sin secretos. Usar plantillas
de `docs/plantillas/`. Reanudar desde artefactos y estado real, no desde tareas imaginadas.
Respetar workflow.max_fix_rounds (2 por defecto): contador global persistido por HU; cambiar de rol no lo reinicia. Al agotarlo, informar bloqueo y pedir decision concreta.
Una ronda es un ciclo de correccion despachado por principal tras needs_changes de
Tester/Reviewer: empieza al devolver el candidato al responsable y termina con
su nueva ejecucion/revision. Varios checks fallidos del mismo intento no cuentan
como rondas distintas. Registrar round_id, motivo, candidato inicial/final y
resultado; el principal incrementa al iniciar la correccion y no reinicia por rol.
Seguir docs/entrega-git.md y delivery en docs/proyecto.json. El alcance maximo configurado
es commit y push en una rama feature/<hu>, con creacion de PR por az repos en Azure DevOps Services tras aprobacion expresa; en GitHub, enlace y borrador manual.
Con delivery.enabled=true, antes de la primera escritura principal prepara la rama desde la base remota real con un
checkout limpio. No trabajar ni publicar en project.base_branch ni ramas protegidas.
La confirmacion manual debe nombrar archivo, diff/candidato, remoto, rama origen/destino y
publicacion commit/push y creacion del PR Azure con titulo/cuerpo previstos. Si la persona aprueba solo archivo, no inferir permiso para publicar.
No usar git add . ni incluir cambios ajenos; no force-push, merge, borrado de ramas o despliegue.
En Azure comprobar ID, URL, estado y ramas con az repos pr show antes de afirmar PR creado.
En GitHub el enlace solo abre el formulario. No completar PR ni activar auto-complete. La rama temporal se conserva
hasta que la persona complete el PR; no se borra durante el cierre de la HU.

## 7. Tareas y capacidades de prueba

Separar en OpenSpec tareas de implementacion/tests (Developer), ejecucion/recibos
(Tester) y revision/verify/sync/archive autorizado (Reviewer). Ver docs/plantillas/tareas-openspec.md.
No inventar estados CLI. Un passed tecnico no autoriza archive, publicacion, merge
ni deploy. Runtime solo por comportamiento o politica aprobada; ver docs/pruebas/README.md.
Las capacidades desactivadas en capabilities.json bloquean si son requeridas.


## Contratos y reglas 0.1.5
Leer la selección congelada del handoff: capas y capacidades son listas, no cargar Gold
ni otras capacidades por disponibilidad. Resolver docs/constituciones/README.md y solo
los documentos activados pertinentes. Las plantillas de capa no son reglas aprobadas.
No modificar criterios, reglas o política para aprobar su propio resultado.
El principal concreta read_paths/write_paths y acciones por HU, captura snapshots de entrada
y salida y conserva los cambios previos de otros roles. Perfiles instruyen; snapshots detectan
cambios persistentes; solo el entorno impone restricciones técnicas. No afirmar autoría ante
escrituras externas concurrentes ni inventar IDs de agentes.
Entregar contrato canónico docs/hu/<change>/handoffs/<fase>-<intento>.json, según
handoff.schema.json, y vista humana derivada. Preservar intentos y referencias a recibos;
no copiar logs. Los estados de objeto previstos, implementados, desplegados y verificados
son independientes. No afirmar despliegue por existir código o una spec.
Una detención afecta la continuación dependiente. Resolver la duda, recibir autorización
aplicable o corregir la condición técnica permite reanudar desde ese punto, conservando
trabajo/evidencia válidos. Puede avanzar lo independiente ya autorizado. El aval humano no
sustituye pruebas obligatorias ni se pide otra vez la misma autorización vigente.

## Principal: consumo de transiciones y entrega 0.1.5
Usar scripts/crea/transiciones.py check antes de continuar, con prioridad antes de Apply,
Sync, Archive y publicación/PR. No abortar toda la HU por cualquier exit distinto de cero.
Leer código, modo e informe; exit 0 informativo tampoco es autorización. En informative,
un error exit 4/informe ilegible queda indeterminado, sin nuevo veto ni certificación.
Comprobar aprobaciones y gates previos mediante sus mecanismos actuales: si faltan/fallan,
la continuación dependiente sigue detenida. Exit 3 espera solo la decisión humana necesaria.
Reanudar al resolver su causa, sin repetir permisos vigentes ni comprobaciones no afectadas.
En enforcing solo bloquear condiciones explícitamente promovidas con casos válidos/inválidos
y referencia de decisión del responsable. Nunca autopromover ni ejecutar bucles de reparación.
Si falta un enlace a recibo válido, corregir el handoff y revalidar; no repetir suites.
Si cambia código/fixture/configuración/criterios, usar plan/run/gate y lo requerido por Tester.
content-v2 conserva solo entradas funcionales iguales. Declarar dependencias Git por check;
HEAD/rama/índice consumidos afectan vigencia. Lo no representable es no soportado, nunca
passed por igualdad de archivos. No migrar recibos antiguos ni adoptar entre planes.
Antes de otro escritor: snapshot de entrada y rutas concretas; después: salida y contraste
completo, incluyendo índice, untracked, bajas y renombres. No restar solo nombres de archivos.
Propose espera decisiones necesarias; Apply espera autorización/conflictos/alcance; Sync espera
revisión y evidencia válidas; Archive espera cierre del expediente revisado; PR espera destino,
contenido, autorización y push confirmados. Las transferencias ya autorizadas no añaden pausas.
PR usa docs/plantillas/pr.md y evidence.delivery como contenido canónico: materializar título y
cuerpo exactos, con digest aprobado. GitHub sigue manual: comprobar campos del formulario;
un enlace no es PR creado. Azure Services usa la CLI ya autorizada y lectura posterior de
ID/URL, repo, ramas, SHA y título/cuerpo; tolerar solo CRLF/LF y salto final documentado.
Archive o push solos no autorizan crear PR. Autorización completa vigente evita confirmaciones
repetidas. Estados draft/form_prepared/creation_unconfirmed/created_verified son distintos.
Sin merge, despliegue, auto-complete, borrado automático ni nuevas integraciones remotas.


## Comprobaciones finales de entrega e intervalos
Antes de commit: `transiciones.py check ... --transition to_publish --operation commit`.
Después de commit y ANTES de push: repetir con `--operation push`; se contrasta gate vigente,
SHA local, árbol probado, derivados publicados y todos los commits desde la base. La comprobación
de PR posterior no sustituye este punto. El índice completo no puede incluir rutas adicionales.
La autorización puede enumerar `publication_paths` finales, separadas del alcance funcional
congelado: añadir registros derivados previstos no obliga a cambiar el candidato técnico.
Los bytes derivados comprometidos deben coincidir con los revisados; excluirlos del digest
técnico no autoriza publicar otra versión. Un registro de resultado nuevo puede quedar fuera
del commit; no editar lo versionado para insertar su propio SHA.

La pareja entrada/salida delimita el trabajo del rol. Salida→actual es un intervalo posterior,
con dueño principal para reconciliar, no una atribución retrospectiva al emisor. Sin salida se
informa intervalo abierto y autoría incierta. HEAD, rama e índice observados se contrastan con
acciones del despacho (commit, switch_branch, stage), además de las rutas asignadas.

Al crear el plan se congelan hashes de TODOS los handoffs ya existentes, incluso con contexto
idéntico. Futuros intentos no hacen crecer el plan: el intento N>1 debe referenciar el intento
N-1 de esa fase con hash e identidad comprobados; no sobrescribirlo. Esto comprueba integridad
local respecto de una referencia, no autenticidad humana ni aislamiento. Las referencias de
OpenSpec tras Archive usan el mapa exacto con hash, sin buscar expedientes similares.

Opcionalmente, un movimiento de tasks.md puede declarar normalization=task_checkboxes antes
del plan. Su sha256 es el del contenido canónico que cambia únicamente casillas numeradas
[x]/[X] a [ ], manteniendo texto/criterios y bytes restantes. Esto no acredita que las tareas
se hayan completado: exige recibos/revisión de la fase correspondiente. Si un check consume
ese estado como entrada funcional, no se aplica esta equivalencia. Otras normalizaciones no
están soportadas. El mapa sigue siendo exacto; no se excluye todo openspec/.
