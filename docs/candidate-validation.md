# Validación de candidatos v1

El incremento 05 añade `harness validate` y contratos independientes, sin migrar
init, onboarding, HU o catálogos v1. Todas las operaciones reciben un documento
JSON explícito con `schema_version: 1`; los schemas se entregan en el wheel.
El catálogo de diseño conserva `not_run`: los resultados observados viven en
evidencias separadas. La aprobación de una HU debe incluir los IDs required que
devuelve la selección antes de implementar el candidato.

## Selección y alcance

| Tecnología/impacto | Required | Alcance |
| --- | --- | --- |
| Python puro | python-static, python-unit | L0 sintaxis y L1 función/comportamiento aislado |
| SQL | sql-static, sql-semantic | L0 parser opcional, L2 runtime seleccionado |
| PySpark | pyspark-static, spark-unit | L0 controles driver y L1 Spark con versión fijada |
| Notebook | notebook-static, notebook-integration | L0 formato/celdas, L3 nuevo job cluster |
| YAML DABs | yaml-dabs-static | L0 YAML y recursos relativos si se aporta root |
| YAML + integración | bundle-validate | L3 CLI autenticado, sin deploy ni notebook ejecutado |
| CI/CD | cicd-static | L0 promoción dependiente de éxito, rechazo always() |
| Delta/runtime/integración | delta-semantic/runtime-semantic/job-integration | L2/L3, nunca sustituidos por parser |
| Performance | performance | Advisory sin baseline; required con hash del baseline |

Los IDs, tecnología, capa y scope son coherentes por contrato. Solo performance
puede ser advisory. La tolerancia aplica exclusivamente a floats finitos;
decimales se serializan como strings y se comparan exactamente. La comparación
de filas puede ignorar orden; schema y nullability siguen siendo exactos.
Performance requiere un protocolo con baseline y perfil comparable en un job
revisado; no se activa un benchmark universal ni optimizaciones sin evidencia.

## Comandos y contratos

```powershell
harness validate plan --input selection.json --json
harness validate static --input static.json --json
harness validate worker --input worker.json --json
harness validate remote --input remote.json --json
harness validate bundle --input bundle.json --json
harness validate gate --input gate.json --json
harness validate attach --input attach.json --json
```

`plan`: SelectionInput con cliente/run/intento/candidato/revisión, tecnologías e
impactos. `static`: plan/request/source_path y root opcional. `worker` añade
runtime, function, cases (args por caso), expected y tolerancias. `remote` añade
target, state_dir externo, mode, expected, tolerancias y source_path opcional.
`bundle` usa el mismo envelope, mode=bundle y source_path requerido. `gate` recibe
plan/records; `attach` añade target_path/policy_path/binding_path/story_id/operation/actor.
Los campos adicionales se rechazan, incluidas credenciales y versiones desconocidas.
Ejemplos de contratos en `docs/examples/validation`: son sintéticos y unauthorized.

Cada request liga plan/candidato/prácticas, runtime/datos/tool, comando y source
hash opcional. Cada evidencia incluye scope, observed, simulated, estado,
timestamps UTC, resultado/hash/URI y remote_run_id si existe. El gate rechaza
missing/not_run/blocked/failed, duplicados, hashes/identidades obsoletos, scope
incompatible y simulated fuera de simulación. `attach` compara identidad con la
HU actual, revisión y tests aprobados, prácticas vigentes, hash de fuente probada
con entradas del candidato y reusa la captura fresca/gates del incremento 04.
No entrega autoridad de publicación: publication_allowed=false.

Salida JSON conserva schema_version/command/status/checks. Código 0: comprobación
observada sin bloqueo; 1: fallo/bloqueo; 2: entrada inválida. Mensajes y logs del
cliente no se copian. Errores SQL propios del parser se convierten en failed.
SQLGlot es un extra opcional (`.[sql]`); si falta, sql-static queda blocked.

## Worker local

Código cliente solo se ejecuta con Docker Linux seleccionado, imagen por digest
y versiones Python/Spark explícitas. No se descarga una imagen ni se instala
Spark automáticamente. El comando usa network=none, read-only, cap-drop=ALL,
no-new-privileges, usuario no root, límites de memoria/CPU/PIDs y tmpfs. No monta
el checkout, home, credenciales o socket Docker. Recibe solo código/datos por stdin,
filtra environment, fija entrypoint y comprueba digest, runtime, tool, comando,
data y source hash cuando está declarado. El resultado se compara con un oráculo.
Timeout retira exactamente el contenedor con nombre UUID propio; fallo de retiro
queda worker_cleanup_required. Recursos Python/PySpark se empaquetan pasivamente.
El protocolo Python propio se puede verificar separadamente con datos sintéticos;
esa verificación no certifica el backend Docker. En esta sesión Docker/Spark están
ausentes y su ejecución genuina se conserva blocked.

## Sandbox Databricks y reconciliación

Usar la habilidad databricks-core para seleccionar perfil; nunca inferirlo.
SandboxTarget exige host/caller/run_as/job/task/runtime/managed volume/resources,
hash de settings y notebook, modos permitidos y autorización sintética explícita.
El adaptador consulta auth/current-user/job/volume y exporta notebook para comprobar
contenido antes de ejecutar. Solo admite un notebook task en nuevo job cluster,
sin cluster persistente, libraries, init scripts, env vars o mounts auxiliares.
La identidad separada debe tener permisos externos limitados a esos recursos;
una allowlist en Python no reemplaza ACLs/IAM ni confina código arbitrario en Spark.
La ausencia o discrepancia bloquea antes de run-now.

SQL/notebook/Delta/job comparten un job sintético revisado. La plantilla
`resources/validation/synthetic_notebook.py` prueba decimal/null/empty/schema,
join y rechazo de duplicados, sesión limpia y MERGE repetido. Para probar código
candidato recibe candidate source con hash y llama
`run_validation(spark, fixture, scratch_path)`; el resultado debe corresponder al
oráculo seleccionado. Sin source es solo smoke de infraestructura y `attach`
rechaza su uso como evidencia de código candidato. Todo borrado se limita al
directorio UUID propio bajo el volume seleccionado, incluso tras excepción.
No se instalan jobs/notebooks ni se despliega un bundle como efecto implícito.

El journal `validation.sqlite3` es separado del de HU/onboarding. Persiste intent
antes del envío; usa request hash como idempotency_token. Un timeout ambiguo no
resubmite: busca ejecuciones del mismo job/request y exige una coincidencia única.
Ausencia en búsqueda limitada no demuestra cancelación. Polling es acotado y una
reinvocación retoma el mismo run. Reusar clave con otro request, destino u oráculo
produce conflict. Identidad root de resultados viene del servicio y datos/runtime/
ejecutor/request/source/hash se comprueban antes de conservar passed.

Bundle validate es otra operación autenticada: restringe YAML a bundle/workspace/
jobs allowlisted, rechaza include/scripts/sync/targets implícitos y discrepancias
de host. Valida en un staging UUID propio y lo retira. Configuraciones fuera del
subset producen blocked, sin intentar resolver efectos desconocidos. El resultado
declara notebook_executed=false y deploy_executed=false.

Estas operaciones siguen la [API de idempotencia Jobs](https://docs.databricks.com/api/jobs/v2/run-now)
y la [referencia de aislamiento Docker](https://docs.docker.com/reference/cli/docker/container/run/).
Los límites de búsqueda/CLI/modelos se registran honestamente y no certifican un
runtime no observado.
