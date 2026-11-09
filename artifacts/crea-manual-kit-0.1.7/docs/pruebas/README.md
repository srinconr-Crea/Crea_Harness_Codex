# Pruebas Crea 0.1.4

Kit y proyecto conviven en la raíz del repositorio. Los JSON iniciales son plantillas
neutrales: setup_complete=false bloquea planificación ejecutable. Personalizar
criterios, consumidores y comandos reales, sin inferirlos de un ejemplo.

## Fuente única y responsabilidades

`docs/proyecto.json.validation.testing.policy_path` apunta al catálogo único de
checks/argv/inputs/criterios/assertions/reglas. `validation.required_checks` contiene
exclusivamente IDs; un ID obligatorio debe estar seleccionado para la HU. El
selector aplica unión de reglas y dependencias; unknown o criterio sin check bloquea.

Planner define riesgos/criterios/consumidores/plan preliminar; Developer escribe
código y tests previstos, diagnóstico focalizado y regresiones justificadas;
Tester ejecuta el plan final; Reviewer contrasta código/cobertura/recibos y OpenSpec.
Un rol activo, sin subdelegación y contador global max_fix_rounds. No modificar
expected para aprobar. El plan técnico no concede permisos de operación.
Una ronda comienza cuando principal despacha una corrección tras needs_changes y
termina con su nueva ejecución/revisión; varios checks fallidos del mismo intento
no son varias rondas. Registrar round_id y candidatos inicial/final en handoff.

## Implementado y comprobable

| Módulo | Evidencia y límite |
|---|---|
| contract.py | Selector/gate puro; mismo input produce mismo plan; no Git ni procesos. |
| git_adapter.py | Base SHA ancestro, HEAD, staged, unstaged, untracked, rename/delete/type/conflictos; NUL y snapshot. No red ni descubrimiento automático de consumidores. |
| execution.py | argv revisado, intérprete explícito, cwd raíz, timeout, entorno mínimo, sin shell y logs acotados/redacción básica. No sandbox contra tests hostiles. |
| reports.py | IDs/contadores JUnit y criterios; skips/0 tests bloqueados; JSON coverage.py por archivo/umbral. No prueba cobertura semántica. |
| schemas.py | Draft2020-12 + formatos, offline; campos extra y referencias remotas rechazados. |
| workflow.py / pruebas.py | Plan/run/gate separados; Git/config/adaptadores, recibos, entorno, edad e integridad; Reviewer no relanza suites. |
| kit_validation.py | JSON/schema/TOML/YAML/referencias/paths anidados y bytes originales; no ejecuta negocio ni agentes. |

El entorno local registra huella de intérprete/plataforma/metadata de paquetes;
no acredita permisos remotos ni equivalencia con DBR. Incluir locks/config y
dependencias consumidas entre inputs; metadata no atesta todos sus bytes. TTL
único en execution.max_evidence_age_seconds. reuse_seconds es elegibilidad futura
entre planes, no caché activa. Recibos no son firmas: conservar evidencia primaria.

## Git y circularidad

Inventario total por capas y recibo de exclusiones con hashes. Solo se excluyen
outputs exactos declarados en execution.outputs bajo pruebas de una HU; nombres
restringidos a plan/git/resultados/gate/recibos/logs/JUnit/cobertura/resumen. No
excluir código/tests/fixtures/criterios/política. Un output que coincida con inputs
de un check bloquea. Un untracked nuevo invalida, aunque faltara en el plan anterior.
No basta git diff --name-only. Planificar nunca ejecuta suites.

## Ejecución y no repetición

Configurar execution.python_executable y reviewed_policy_digest después de revisar
el catálogo. Por ID: junit_path, assertion_tests y cobertura opcional. JUnit usa
classname::name completo, incluso parámetros. Exit 0 sin assertions/IDs requeridos
no pasa; todos los skips de la suite requerida bloquean aunque se cumpla min_tests.

Run solo admite pytest/local/local_execution en 0.1.4. Otras capacidades: blocked.
El runner emite reporte; el parser no lo inventa. XML/JSON malformado, reporte
ausente o recibo ajeno no pasan. Logs acotados/redactados no autentican assertions;
la redacción es básica: revisar datos antes de versionar.

Conservar intentos: para reejecutar, outputs nuevos bajo attempt-<id>/ y plan
regenerado. No sobrescribir receipts ni retocar fechas/plan_id. No hay importación
entre planes. Reviewer usa gate sin run; solicita al Tester reejecución solo por
invalidación, evidencia insuficiente o regla fija, registrando motivo. Gate vuelve
a obtener Git/reportes para detectar inputs nuevos o evidencia alterada.
CLI exige nombres por rol (plan.json/resultados.json/gate.json/git.json), bloquea
colisiones con evidencia primaria y preserva planes/recibos de intentos anteriores.

## Capacidades por fases

capabilities.json/schema registran entrega/inactividad. Habilitar requiere
desarrollo, fixtures, revisión y nueva versión; cambiar un booleano no implementa.
Si un check requiere una capacidad inactiva, bloquea aunque una suite local pase.

| Capacidad inactiva | Integración futura requerida |
|---|---|
| Runtime / Spark local | Manifest autorizado, preflight → smoke → suite, API/DBR, IDs/versiones/huellas/assertions, inventario aun con fallo y cierre aprobado. |
| Semgrep / triage | JSON scanner; errores separados de vulnerabilidades; positivos/negativos/FP conocidos; reglas consultivas hasta promoción humana. |
| Mutation local | Copia aislada, baseline verde, viable/killed/survived/incompetent, triage y presupuesto; nunca mutar checkout productivo/remoto. |
| Reviewer evals | Dataset humano independiente, FP/FN/acuerdo/costos, calibration.json único, promoción/override humano, sin autopromoción. |
| Reutilización entre planes | Linaje plan/resultado origen, hashes/definiciones iguales, entorno/TTL/autorizaciones; can_reuse no basta. |
| CI | Opt-in por integración específica; no instalar workflows en setup. |

Runtime por comportamiento/política, no por extensión: solo MD no activa Spark.
Mock/Spark local no prueba UC/ADLS/DBR; bundle validate no prueba ejecución. Sin
crear cluster/catalog por HU. Perfil/host/identidad/rutas/negocio por cliente.
Ver [runtime](runtime.md). CI: PR/checks sin deploy → merge humano → deploy autorizado
del SHA → smoke → promoción. No asumir ramas/triggers ni operar jobs/tablas/permisos.

## Catálogo, rúbrica y adversariales

Completar failure-modes.json: riesgo → requisito → expected independiente →
fixture/test. Nulos/tipos/límites/duplicados/grano/concurrencia/replay/autorización
solo si aplican. Revisar consumidores desde imports/llamadores/config/notebooks;
un grep vacío no demuestra ausencia de consumidores dinámicos.

Reviewer: corrección, seguridad, rendimiento, tests faltantes, estilo/documentación;
especialidad Python/Spark/SQL/infra por aplicabilidad. Archivo/línea/evidencia por
hallazgo; rendimiento con medición. review.schema.json separa suggested_action y
effective_stage. Umbrales únicos en calibration.json; stage=block sin promoción
humana bloquea. Evals/promoción automáticos inactivos, sin autopromoción por JSON.
Overrides en review-history.json conservan decisión IA/humana, motivo/evidencia,
candidato/regla y regresión si aplica.

Adversariales pasan al rechazar ataque **y** permitir control legítimo: rutas,
catálogos, SQL/argumentos, secretos, dependencias y superficie LLM si aplica. Fixtures
locales prueban traversal, XML con entidades, argv no revisado, recibos ajenos y
controles legítimos; no acreditan seguridad de un servicio o producto remoto.
No ejecutar todas las herramientas por HU; instalar solo en setup autorizado.

## Verificar esta distribución

```powershell
& $python -B -m unittest discover -s tests/crea -v
& $python -B scripts/crea/validar-kit.py --original
```

Tests crean repositorios Git sintéticos y procesos locales sin red. No equivalen
a cuatro agentes despachados; piloto real Codex/runtime autorizado queda pendiente.
Setup y comandos: [configuración manual](../configuracion-manual.md).

## Transiciones y evidencia 0.1.5

`python scripts/crea/transiciones.py check --repo <raiz> --handoff
 docs/hu/<change>/handoffs/<fase>-<intento>.json --transition to_apply`
(inscribir en una línea). `render` usa el mismo --repo/--handoff y devuelve la vista humana.
Sin --out no escribe; --out crea exclusivamente un nuevo informe/resumen permitido de esa HU.
Si ya existe, conservarlo y usar otro intento o revisar explícitamente la actualización de la
vista derivada; los JSON canónicos nunca se sobrescriben. Snapshots: `git_adapter.observe`
antes/después del escritor; guardar JSON de entrada/salida en sus rutas asignadas.

El principal consume código, modo e informe, no `exit != 0 → detener todo`. Exit 0 no es
aprobación; 2 significa condición nueva bloqueante habilitada; 3 espera solo la decisión humana
necesaria para esa continuación; 4 es error e indeterminación. En informative, 4 o informe
ilegible no añaden veto ni certifican cumplimiento. Comprobar por sus mecanismos actuales los
gates y aprobaciones anteriores; si faltan/fallan/no se acreditan, se conserva esa detención.
`transiciones.consume(report, code, mode, existing_constraints, blocking_conditions)` permite
comprobar esa interpretación. En error/informe ilegible, existing_constraints debe provenir de
las comprobaciones previas independientes; `None` devuelve can_continue=None, no aprobación.
Una lista vacía se pasa solo cuando se comprobó que no hay restricción previa pendiente.
blocking_conditions procede de la configuración vigente; enforcing sin condiciones habilitadas
no crea por sí solo un bloqueo nuevo ante un error. Se permite trabajo independiente autorizado.
Resolver duda, autorización o condición técnica permite reanudar desde ese punto sin repetir
permisos ni trabajo válido. Un aval humano no reemplaza evidencia técnica obligatoria.

Para adoptar content-v2, tools/schema deben actualizarse juntos y el contrato de planificación
inicial debe existir antes del plan final. Se infiere la HU desde outputs exactos de pruebas.
El plan congela política/contexto, no hashes futuros: handoffs nuevos con contexto idéntico se
clasifican por schema; cada observación conserva paths/hashes/generador y digest de contexto.
Un nuevo plan puede congelar hashes de contratos históricos que ya existían con otro contexto:
no se modifican esos contratos ni se añade esa lista al emitir futuros handoffs. Las entradas
funcionales del check nunca se excluyen por parecer metadatos. Un resultado de otro plan no se
adopta ni reetiqueta. HEAD/rama/índice funcionales se declaran en scope.git_inputs por check;
[] exige revisar independencia. Otro estado no representable es no soportado por la equivalencia.
Los planes antiguos siguen su verificación anterior. Verificar índice/árbol y commits del rango
antes de publicar: `git_adapter.verify_index` y `verify_commit`, además del gate vigente.

Recorridos proporcionales:
- Silver/Spark: completar/activar Silver con responsable, seleccionar comunes+Silver+Spark,
  criterios/plan → Apply humano → código/tests → Tester y recibos → Reviewer/gate/verify →
  Sync favorable → cierre/entrega autorizados. Spark/runtime inactivo requerido queda blocked;
  este recorrido sintético no acredita runtime remoto.
- Documental: layers/capabilities vacíos justificados, comunes pertinentes y checks documentales
  concretos según política, sin Spark obligatorio; objeto documental y despliegue no-aplica.
- Evidencia obsoleta o escritura fuera de alcance: reportar candidato/ruta/intervalo, responsable,
  corrección concreta y evidencia conservada; no reiniciar HU. Enlace faltante a recibo íntegro
  se corrige localmente y revalida sin suites. Cambios técnicos vuelven a plan/run/gate.

Introducción: tres HU representativas en informative con evidencia normal. Tras casos válidos e
inválidos y revisión de falsos positivos, el responsable puede promover IDs concretos mediante
mode=enforcing, blocking_conditions y promotion_ref. No promoción autónoma ni plataforma extra.


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
