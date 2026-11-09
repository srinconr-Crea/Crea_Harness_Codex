# Ciclo de vida de pruebas (opt-in 0.1.8)

El catálogo único sigue siendo `docs/pruebas/policy.json`: comandos solo en
`checks[].argv`, checks requeridos por ID en `validation.required_checks`.
Sin `lifecycle` ni `attempt_templates` se conserva la rama anterior. La gestión
de contexto es independiente: puede estar ausente o deshabilitada.

## Ubicar y descubrir durante setup

`python -B scripts/crea/pruebas.py discover --repo .` funciona antes de
setup_complete. Lee nombres y configuración conocida; no importa conftest,
ejecuta pytest, instala herramientas, mueve suites ni afirma passed.
Configuración no soportada aparece parcial; IDs dinámicos requieren ejecución
Tester revisada. Tests del proyecto, `tests/crea` y evals tienen superficies
distintas; dependencias, vendor, enlaces y sensibles quedan fuera de discovery,
pero no se filtra el Git completo ni se degrada su gate.

El setup puede declarar `lifecycle` con `schema_version: "1.0"`, `locations`
(objetos `path`, `kind: tests|fixtures|evals`) y `test_inventory`. Cada fila tiene
`id`, `pattern`, `check_ids`, `purpose`, `provenance`, `state: active|retired`.
Una active referencia checks configurados. Se conservan directorios propios.
Las dependencias de código, fixtures, configuración y locks pertenecen a inputs;
una coincidencia textual es sugerencia hasta revisión.

`catalog.baseline` propone comprobaciones condicionales de documentos/config,
sintaxis Python sin importación, SQL con parser/dialecto preparado y notebooks
sin outputs. No exige runtime por extensión ni inventa negocio. Un check con
criterio técnico equivalente (`documents`, `python`, `sql`, `notebook`) evita
duplicarlo. SQL sin herramienta preparada queda pendiente. Solo durante setup
autorizado se puede invocar `catalog.materialize_baseline(root, paths,
"tests/proyecto/test_validaciones_tecnicas.py")`; la plantilla técnica incluye
solo archivos existentes aplicables y no se materializa vacía. No instala nada.
YAML, schemas de negocio y runtime necesitan sus herramientas/oráculos revisados.

## Declarar, seleccionar y reconciliar cada HU

Planner declara criterios y oráculos reales. Developer escribe las regresiones
autorizadas y propone altas/modificaciones/retiros; principal contrasta Git
base/HEAD/index/worktree/untracked/conflictos con el catálogo:

`python -B scripts/crea/pruebas.py reconcile --repo . --base <SHA-exacto>`

No relee cuerpos de suites ajenas al diff. Informa movimientos, bajas, asociaciones
por patrones y pruebas no registradas incluso fuera de ubicaciones conocidas.
No registra automáticamente una decisión nueva. Cada criterio requerido selecciona
checks por relación declarada (`declared-required-criterion`) además de reglas,
inputs y checks fijos. Unknown, input ausente y criterio sin check siguen bloqueando.
El plan congela archivos afectados asociados y `expected_files`,
`expected_nodeids`, `complete_files` opcionales del inventario activo. Una regresión
crítica usa nodeid exacto; pasar otro caso del mismo archivo no basta. Suite completa
exige que todos los IDs recogidos de ese archivo hayan pasado; filtros parciales
requieren selección explícita revisada. No acredita consumidores dinámicos no declarados.

## Resolver outputs una sola vez

`execution.attempt_templates` usa exactamente estos campos revisados:

```json
{"schema_version":"1.0","evidence_dir":"docs/hu/{change}/pruebas/attempt-{attempt}",
 "junit_path":"{evidence_dir}/junit-{check_id}.xml",
 "inventory_path":"{evidence_dir}/inventory-{check_id}.json","coverage_path":null}
```

Para coverage JSON opcional, `coverage_path` es
`{evidence_dir}/coverage-{check_id}.json`. Los mappings/assertions siguen en
`execution.checks`; `outputs: []` sirve como configuración permanente. El argv
revisado del check puede usar `--junitxml={junit_path}`,
`--crea-inventory={inventory_path}`, `--cov-report=json:{coverage_path}`; JUnit e
inventario también aceptan valor exacto tras el flag correspondiente. Ninguna
expansión arbitraria de entorno, shell, código o traversal está permitida.

Ejemplo de entrada explícita con pytest ya preparado:
`["python", "scripts/crea/run_pytest.py", "-c", "pytest.ini", "tests/proyecto",
"--junitxml={junit_path}", "--crea-inventory={inventory_path}"]`.
La entrada carga `testing.pytest_inventory` explícitamente y no instala plugin
global. Si se usa pytest-cov, ese plugin debe estar preparado y cargado explícitamente.

Principal: `python -B scripts/crea/pruebas.py plan --repo . --base <SHA> --change mi-hu --attempt 1 --criteria CA01`.
Tester: `python -B scripts/crea/pruebas.py run --repo . --plan docs/hu/mi-hu/pruebas/attempt-1/plan.json`.
Reviewer: `python -B scripts/crea/pruebas.py gate --repo . --plan docs/hu/mi-hu/pruebas/attempt-1/plan.json`.

La política/execution permanentes no cambian entre HU. El digest revisado acredita
el origen; `execution_resolution` congela HU/intento, argv y configuración resueltos.
Run y gate reconstruyen ambos. Un destino ocupado (también solo stdout/JUnit), enlace,
alias o colisión con input/evidencia primaria impide crear otro intento. Solicitar
otro intento explícitamente; nunca renumerar ni reutilizar recibos entre planes.

## Verificar inclusión y mantener límites

El plugin observa colección antes de filtros, deselección y fases setup/call/teardown
del mismo proceso. Sus propiedades `crea.nodeid`/`crea.run_id` enlazan JUnit con JSON
sin deducir rutas desde classname. Parametrizados conservan IDs concretos y rutas
relativas al repositorio incluso con rootdir propio. Skip, fallo, error de colección,
ID requerido ausente o ejecución incompleta no acreditan cumplimiento. El gate lee
inventario/recibo/JUnit, hashes, entorno y TTL sin repetir suites. Esta evidencia
coherente local no es una firma contra alteración coordinada de todos los archivos.

`evidence.test_inventory_review` del handoff contiene versión, `expected` por check
(`files`, `nodeids`, `complete_files`), `reconciled`, `affected`, `dispositions` e
`inclusion_ref`. Expectativas forman el contexto lógico y su digest: no se pueden
borrar o suavizar como metadata para aprobar. Referencias corregidas sin cambio
funcional se revalidan; producción, configuración, expectativas o inputs cambiados
invalidan y requieren un plan nuevo con evidencia nueva. `max_fix_rounds` sigue
siendo global; no se reinicia por traspaso ni se ejecuta toda la batería por rutina.

## Retirar y revisar

Developer propone retiro/sustitución; Reviewer revisa alcance y consumidores.
Una fila retired conserva check_ids históricos, `retirement.source`, `reason`,
`decision_ref` con hash, `replacement_ids`, `previous_definition` y
`previous_digest`. Reconciliar reglas, checks/inputs, criterios, required_checks y
assertion_tests. Checks históricos no ejecutables no deben continuar en rules.
Desactivar una requerida conserva blocked, nunca passed. Una baja o pérdida de
asociación por movimiento requiere disposición revisada; no prueba obsolescencia.

`TEST_INVENTORY_RECONCILED` y `TEST_RETIREMENT_REVIEWED` empiezan informativas y se
promueven por ID con referencia explícita mediante transiciones existentes. Se
limitan al impacto afectado. Informative no agrega veto; unknown, runtime inactivo
y requerida sin ejecución conservan sus bloqueos técnicos. No hay pausas nuevas por
cada handoff ni nuevas capacidades activadas.

Discover/reconcile: 0 inspección completa (puede avisar), 4 error indeterminado;
las decisiones/promociones se consumen mediante `transiciones.py` con códigos
0 completo, 2 incumplimiento promovido, 3 decisión humana pendiente, 4 error.
Plan/run/gate conservan códigos legacy (0 o 2); helper puro también conserva los suyos.

## Adopción y reversión

Actualizar juntos schemas, catálogo opcional, ejecución, plugin/entrada, contract,
CLI, handoff/transiciones y guías desde 0.1.8 mediante diff revisado. Validador
`--original` acredita bytes de distribución; sin ese flag valida la configuración
personalizada, también sin gestión de contexto. Conservar suites, reglas y modelos
propios; no migrar intentos/recibos previos. Revertir el conjunto al staging anterior,
sin borrar evidencia, ni desactivar requisitos para aprobar. 0.1.7, ZIP/hashes y motor
histórico permanecen intactos. Candidato local; runtime/Spark/Databricks, evals,
SAST/mutation, CI, hooks y certificación de roles nativos siguen sin activarse.
