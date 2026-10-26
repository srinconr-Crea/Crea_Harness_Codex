---
name: crea-orquestador
description: Use when starting or resuming a historia de usuario (HU) in a repository configured with the Crea manual kit, coordinating OpenSpec planner, developer, tester and reviewer stages.
---

# Orquestador Crea

## 1. Proposito y entrada

Conducir una HU hasta revision, archivo autorizado y entrega Git en rama de trabajo con PR creado en Azure DevOps Services o formulario de PR en GitHub. Entrada:
objetivo, criterios, restricciones y nombre de cambio si existe. Coordinar en el agente
principal; no lanzar otro orquestador. Para preguntas sueltas, responder sin fabricar una HU.

## 2. Preflight y contexto

Leer AGENTS.md, docs/proyecto.json, contexto-proyecto.md y practicas generales.
Comprobar inventario con archivos reales; no considerar las rutas de ejemplo existentes.
Leer solo skills/practicas que afecten a la HU. Si falta contexto imprescindible, pedirlo
y avanzar con exploracion independiente. No pasar al developer sin checks concretos.
Comprobar Git, CLI OpenSpec, root local y skills requeridas. No crear openspec/ como
efecto lateral: seguir el proyecto/store check de la skill; setup solo cuando sea autorizado.
Si hay varios cambios, seleccionar por contexto inequivoco o preguntar cual, sin usar el primero.
Antes de la primera escritura (incluida planificacion), leer docs/entrega-git.md y delivery.
Con delivery.enabled=true, principal comprueba remoto/base/HEAD y checkout limpio, y crea feature/<hu> desde la base
remota vigente. Si el slug de HU aun es incierto, hacer solo exploracion de lectura hasta
definirlo. Registrar rama y base. No cambiar de rama con trabajo ajeno pendiente ni inventar
una base si el repo no tiene commit/remoto inicial; seguir el bootstrap manual de la guia.
Para reanudar, comprobar la rama registrada y sus commits en lugar de crear otra o resetearla.

## 3. Delegacion real y aislamiento

Usar la herramienta de subagentes disponible en esta sesion. Cuando admita seleccionar
agentes personalizados, elegir planner/developer/tester/reviewer definidos en .codex/agents/.
Si la herramienta expuesta no tiene selector de rol pero permite instrucciones y perfil:
leer el TOML real, pasar developer_instructions completo como instrucciones de tarea y fijar
model=gpt-6.1-sol, reasoning_effort=medium segun ese TOML; usar contexto aislado si permite
overrides solo en ese modo. Esto es delegacion con perfil explicitado, no prueba de descubrimiento nativo.
Si ninguna herramienta puede crear un subagente con ese contrato, reportar blocked y pedir
a la persona habilitar la capacidad o autorizar expresamente trabajo en una sola sesion.
No inventar una llamada, un agent_type no admitido o un agente ejecutado.

Cada despacho debe incluir: HU/change, etapa, rutas de contexto y artefactos, criterios,
write_paths, checks, handoff previo y formato de salida docs/plantillas/handoff.md.
Esperar finalizacion real con la herramienta de espera disponible; registrar identificador y resultado.
Un agente activo por vez. Reutilizar el mismo agente para correcciones si la interfaz lo permite.
No subdelegacion. Respetar max_fix_rounds; agotar rondas devuelve decision a la persona.

## 4. Secuencia

1. Planner: leer perfil; usar explore si hace falta, propose para crear o update-change para
   revisar artefactos existentes. Conservar las pausas de las skills. En explore, solicitar a
   la persona la confirmacion de captura de artefactos si no esta autorizada explicitamente.
   En update-change, presentar las revisiones y transmitir las confirmaciones humanas antes
   de escribir. Un mensaje del principal al planner no sustituye a la persona.
   Tras propose, presentar artefactos, tareas por rol y plan preliminar de pruebas con checks y detenerse hasta recibir una NUEVA
   solicitud humana de apply. Una peticion inicial de ejecutar toda la HU no salta esa pausa.
   Registrar la respuesta y reanudar solo el cambio indicado; no inferirla por tiempo transcurrido.
   require_plan_approval=true explicita esta politica; cambiarlo no anula guardrails upstream.
2. Developer: aplicar con openspec-apply-change, implementar codigo/tests previstos y entregar
   ready_for_test. No completar tareas de ejecucion Tester por existencia de codigo. Si varia
   alcance, volver al planner via principal antes de implementar esa variacion.
3. Principal reconcilia criterios, consumidores y diff final completo (base/HEAD/staged/unstaged/
   untracked/renames/deletes/conflictos). Leer crea-pruebas y generar plan final determinista
   con scripts/crea/pruebas.py plan. Politica unica, rutas desconocidas o cambios de alcance
   pendientes bloquean antes de ejecutar. No usar solo git diff --name-only.
   Tester: ejecutar solo checks seleccionados/configurados mediante adaptador local, conservar
   recibos/IDs/assertions/hashes/entorno y devolver ready_for_review o blocked/needs_changes.
   Runtime/SAST/mutation/evals/CI o adopcion entre planes requeridos sin adaptador activo: blocked.
   Reviewer: contrastar codigo, rubrica, cobertura y recibos Tester; ejecutar gate sin repetir suites
   y openspec-verify-change. Reejecucion solo por entradas invalidadas, evidencia insuficiente
   o regla fija; registrarla y enviarla al Tester. Defectos al Developer, requisitos al Planner,
   siempre via principal. Contador max_fix_rounds global persistido: no reinicia por rol.
   No cerrar ni sync con checks blocked/not_run/failed ni hallazgos bloqueantes sin resolver.
4. Con revision favorable, reviewer ejecuta openspec-sync-specs y devuelve diff + ready_for_archive.
5. Presentar cambio, evidencia, pendientes, diff de sync, rama feature, base y remoto, mas
   titulo/cuerpo de PR y lista de archivos a versionar. Pedir aprobacion explicita para archivar
   Y hacer commit/push de ese alcance en esa rama, mas crear el PR Azure hacia la base
   con el titulo/cuerpo presentados. La aprobacion de push solo no autoriza crear PR. Detener el flujo hasta recibirla.
   Si aprueba solo archivo, no publicar. Registrar el texto/resumen y candidato aprobado
   en docs/hu/<change>/evidencia.md, sin falsificar aprobacion.
6. Reanudar reviewer con la aprobacion humana identificada para ejecutar openspec-archive-change.
   Si cambia el candidato, invalidar aprobacion y repetir revision/solicitud.
7. Solo con delivery.enabled=true y autorizacion expresa de publicacion, principal comprueba
   que archive solo movio/actualizo los artefactos previstos, finaliza
   docs/hu/<change>/pr.md con enlace y borrador, revisa el diff final y el alcance aprobado.
   Sigue docs/entrega-git.md: stage de rutas explicitas, commit, push ordinario de la rama
   feature y comprobacion del SHA remoto. Si falla un paso, informar el estado real sin
   duplicar commits ni simular publicacion. Cambios funcionales requieren nueva revision.
8. Azure DevOps Services: seguir docs/entrega-git.md para consultar duplicados, crear PR
   solo si fue autorizado y verificar ID/URL, repo y ramas. GitHub: entregar formulario y borrador.
   Entregar SHA, rama, base, push y estado real del PR. Sin merge, deploy ni automatizaciones.

## 5. Salida y reanudacion

Mantener docs/hu/<change>/evidencia.md con estado, referencias de los agentes, cambios,
checks y motivos de bloqueo. Usar docs/plantillas/evidencia-hu.md. Para reanudar, leer
este registro, git diff y estado OpenSpec real. Si el cambio ya se archivo, no crearlo de nuevo.
Informar resultado, ruta de archivo o aprobacion pendiente y limitaciones reales.
El commit/push requiere la aprobacion de publicacion indicada en el paso 5; el archivo
por si solo no basta. La entrega completa exige verificar que el remoto apunta al SHA
del commit local; un enlace construido antes del push es solo un borrador.
Reportar SHA y recibo de publicacion en la respuesta final, sin editar archivos versionados
despues del commit solo para incluir su propio SHA. El registro previo incluye el alcance
aprobado y el enlace determinable; no intentar una huella circular del commit.

## 6. Configuracion y extensiones

Consultar workflow, validation y extensions de docs/proyecto.json. Las politicas de archivo
manual y un escritor se mantienen. Agregar especialidades sin duplicar este flujo:
skills comunes en Crea, propias en Project, agentes en .codex/agents/.
MCP solo si aparece conectado en las herramientas reales. Hooks solo segun docs/extensiones.md;
una entrada JSON no instala nada. No modificar skills upstream para incorporar negocio.

## 7. Ejemplo de inicio

Solicitud: '$crea-orquestador HU: normalizar documentos de clientes; conservar ceros
iniciales, reportar entradas invalidas y cubrir casos vacios y duplicados'.
Leer contexto → planner define contrato y pruebas → persona solicita apply → developer aplica
→ principal plan final → tester ejecuta → reviewer consume recibos, verifica y sincroniza → persona autoriza archivo y publicacion → reviewer archiva
→ principal hace commit/push feature y crea PR Azure autorizado (GitHub: formulario).

## 8. Contratos de pruebas

Leer [pruebas](../crea-pruebas/SKILL.md) y docs/pruebas/README.md.
required_checks referencia IDs; no contiene comandos. Resolver skills por extensions.skills
antes de usar convencion raiz. Registrar plan_id/digest en handoff; recibos canonicos en
docs/hu/<change>/pruebas/. Separar tareas OpenSpec por rol sin editar skills upstream.
Mismo candidato/plan vigente: consumir evidencia existente. Otro candidato o plan: bloquear
adopcion cruzada; planificar y ejecutar de nuevo lo requerido. No retocar IDs o fechas de recibos.


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
