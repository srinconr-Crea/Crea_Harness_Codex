# Operación local de historias de usuario

El incremento 04 añade contratos v1 independientes en `harness_core.hu` y el
adaptador `harness_local.hu.HuService`. No modifica los contratos de onboarding.
Los comandos del kit registran gates; Codex conserva herramientas, conversación
y ejecución de agentes. El CLI no ejecuta código cliente, conecta producción ni
publica historias/PR. El push del repositorio del producto es una acción distinta.

## Preparación y selección

Usar target, policy y binding externos de un cliente preparado por 03. Start lee
el plan y journal completados y comprueba identidad y recursos creados/preservados.
Consume el recibo incluso si pertenece a una versión anterior del procedimiento
pasivo: no vuelve a aplicar ese plan ni relaja las comprobaciones de apply v1.
Require checkout limpio y HEAD existente. Las sondas Git aíslan configuración
global; declarar `core.autocrlf` localmente si el checkout depende de esa opción.
No cambiar política global para satisfacer el gate.

Cada operación recarga la selección. Cliente/checkout/target incorrectos bloquean;
no redirigen el estado de una instancia a otro cliente. Estado externo:
`<binding.state_dir>/hu.sqlite3` y `hu-artifacts/<story_id>.json`. La estructura
state_dir conserva sus dos últimos componentes cliente/checkout. El lock común
con onboarding evita que operaciones del kit se solapen durante una transacción.

## Comandos

```powershell
harness hu start --path C:/Clientes/alpha --policy C:/Config/policy.json --binding C:/Config/binding.json --story HU1 --operation start1 --input C:/Planes/start.json --json
harness hu plan --path C:/Clientes/alpha --policy C:/Config/policy.json --binding C:/Config/binding.json --story HU1 --operation plan1 --input C:/Planes/plan.json --json
harness hu status --path C:/Clientes/alpha --policy C:/Config/policy.json --binding C:/Config/binding.json --story HU1 --json
```

Todas las entradas incluyen `schema_version: 1`; campos extra/versiones desconocidas
son inválidos. Cada mutación necesita operation e input JSON. Status es lectura.
Salida común: schema_version, command=hu, status, checks, run, publication_allowed
y certified. Códigos: 0 ready/partial; 1 blocked/fallo/conflicto; 2 entrada inválida.
La salida de texto conserva los mismos estados. Entradas con secretos se rechazan
sin copiar su contenido al informe o estado.

Ejemplo start:

```json
{"schema_version":1,"onboarding_plan":"C:/Planes/onboarding.json","writer_actor":"developer-alice","simulation":true}
```

Ejemplo plan (rutas relativas, sin glob; un directorio incluye descendientes):

```json
{"schema_version":1,"criteria":["Sumar valores decimales por cliente"],"paths":["src/total.py","tests/test_total.py"],"operations":["create","modify","delete"],"tests":["T16"],"required_capabilities":[],"max_delegations":2,"allow_worktrees":false,"sources":{"story":"user"},"decisions":["HU pequeña: principal y revisión independiente"]}
```

Guardar el plan_sha256/revision devuelto. Approve exige actor, confirmed=true,
client_id, checkout_id, attempt, revision y plan_sha256 exactos. La persona debe
autorizar ese plan; un agente no puede inventar el actor/aprobación. Actor es una
referencia declarada por el operador, no autenticación ni firma criptográfica.
Cambios de criterio/ruta/operación/política/prácticas/kit/contexto invalidan aprobación,
candidato y evidencia. El nuevo plan debe volver a aprobarse.

Flujo: draft → analyzing → planned (plan) → approved (approve) → implementing →
validating → reviewing → ready_to_publish. Candidate inicia implementing después
de aprobación; transition también permite approved → implementing. Failed/cancelled
registran cierre fallido. Attempt, solo desde failed y base limpia, incrementa intento,
reinicia plan/aprobación/límites/evidencia y conserva toda la historia.

Candidate captura HEAD base, baseline de bytes, cambios rastreados/nuevos/eliminados,
working tree e índice Git. Dos capturas consecutivas deben coincidir. CRLF legítimo
del baseline se preserva; cambiar bytes después de pruebas invalida evidencia.
Diff fuera del manifiesto, rutas protegidas/denegadas y operaciones no autorizadas
bloquean, incluso si el cambio está solo en el índice. No ejecuta filtros/diff drivers.
Límites: 4096 archivos baseline/listado, 2 MiB por archivo, 16 MiB baseline, 256
entradas de candidato y límites max_files/max_bytes de política sobre cambios.
Submódulos, symlinks, entradas Git no soportadas o unmerged son bloqueo.

Evidence requiere id, kind (test/review/capability), candidate_sha256, status,
simulated, actor y evidence_ref sanitizado. Cada test requerido debe tener passed
para el candidato actual. Capacidades requeridas exigen passed real incluso en
simulación. Capability puede registrarse en implementing antes de validating;
tests/review se registran en validating/reviewing. Review necesita actor distinto
del escritor principal, assignments escritores, handoffs de escritura y testers.
Evidence es un contrato de importación: no certifica por sí misma una ejecución.

Simulation=true permite el ensayo sintético hasta ready_to_publish/partial. Una HU
real rechaza evidencia simulada. Not_run/blocked/failed/unavailable y evidencia stale
no superan validación. Publication_allowed=false y certified=false siempre en 04;
transition published devuelve bloqueo. No se crea PR ni se ejecuta validación remota.

## Roles, contexto y límites

Start declara al escritor principal incluso sin fanout. Sources/decisions del plan
y Handoff persistidos documentan explore/enrich/impacto/propose/update/apply/test/
audit/verify. Handoff contiene role, actor, hashes, fuentes, decisiones, findings y
status; no concede aprobación ni produce evidencia de pruebas por sí solo.

Assign registra role, actor, write_paths, isolation=checkout_id y delegation_depth.
Revisores son read-only; asignaciones concurrentes se limitan a cuatro y profundidad
uno, con máximo acumulado aprobado por intento. El manifiesto aprobado de otra HU
activa reserva sus rutas; assignments de la misma HU no pueden solaparse. La
asignación explícita transfiere responsabilidad del principal al escritor delegado
en esas rutas; el principal debe respetar esa transferencia. El adaptador no puede
impedir que una herramienta Desktop externa escriba: detecta el diff en gates.

Worktree necesita allow_worktrees aprobado, path externo, branch local nuevo y
confirmed=true. Solo crea localmente; desactiva hooks y filtros Git. Registra intención
antes del efecto y reanuda observando path/branch/HEAD, sin recrearlo. Un worktree
necesita preparación/binding propios para operar otra HU; no amplía el manifiesto
del checkout original. No borra worktrees, ramas o datos durante recovery.

Correct consume una de las dos correcciones permitidas por intento e invalida
candidato/evidencia. Block(reason=tool_unavailable) registra infraestructura sin
consumir corrección ni declarar passed. Una tercera corrección exige cerrar failed
y comenzar otro intento limpio o replantear alcance con aprobación nueva.

## Transacciones y recuperación

SQLite migra solo base vacía user_version=0 → 1, sin reutilizar journal v1.
Versiones/tablas desconocidas son conflicto. BEGIN IMMEDIATE y synchronous=FULL
confirman estado e historial en la misma transacción. Fallo previo a commit revierte;
fallo posterior no duplica efectos al repetir operation. Mismo identificador con
datos diferentes falla. Artefactos JSON/hash son exportaciones derivadas reemplazadas
atómicamente; una repetición después de crash reconstruye la exportación desde DB.

Resume revalida selección, preparación, contexto, base, candidato y worktree pendiente.
Si no se puede demostrar que una creación ocurrió, conserva bloqueo y no la repite
silenciosamente. Los locks muertos se reconocen mediante PID/tiempo de proceso.
Estas garantías cubren escritores del kit. Un actor con acceso al estado externo
puede modificarlo; hash es integridad, no firma. No se promete interceptar Desktop,
detectar una edición restaurada entre capturas ni protección ante administrador.

La ausencia de evento/hook observado se declara en enforcement y Skill; permisos
externos son necesarios para garantías adicionales. Certificación estricta de 02 y
evals manuales conservan sus límites. Ver evidencia y trazabilidad en
[verificación de 04](evidence/hu-lifecycle-verification.md).
