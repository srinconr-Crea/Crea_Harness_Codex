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
