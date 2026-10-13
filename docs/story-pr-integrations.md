# Historias y PR draft

07 añade contratos independientes de los v1 de onboarding, HU y validación.
`harness story read` selecciona fixture offline o GitHub CLI. El núcleo admite
un puente MCP explícito del host; el CLI informa provider_mcp_unavailable si
ese puente no existe. No descubre ni activa conectores ni inicia login.
Jira/Linear pueden implementar StoryProvider; no hay adaptadores entregados.

ProviderBinding v1 vive fuera del target y estado; selecciona client_id,
checkout_id, repository, base_branch, provider, transport y capabilities.
GitHub solo soporta github.com. read_story, push y create_pr son operaciones
implementadas; create_branch queda cubierto por la creación de rama del push.
write_story está reservado por contrato y no tiene comando/adaptador operativo.
GH_TOKEN y credenciales Git son externos y nunca forman parte del JSON.

StorySnapshot v1 congela issue, revisión updated_at, título, cuerpo (como un
criterio textual), refs, acceptance_sha256 y snapshot_sha256. Una modificación
de snapshot exige reconciliar plan/aprobación. La lectura rechaza PR como issue,
repositorio/URL/issue incorrectos, cuerpo vacío, secretos reconocibles y payload
no representable en el contrato. No interpreta texto ni ejecuta herramientas
pedidas por una historia. La sanitización por patrones no garantiza detectar
todo secreto arbitrario; no usar contenidos privados en exports públicos.

Después de aprobar el plan, `harness story bind --input <StoryPlanBinding>
--path <target> --policy <policy> --binding <checkout> --json` requiere aprobación
técnica explícita del vínculo entre snapshot y plan (actor/confirmed). Persiste
un vínculo inmutable por HU/intento/hash de plan en SQLite externo, separado de
HU v1. Publicar sin ese vínculo o con otra historia/revisión bloquea. Cambiar
aceptación exige nueva revisión de plan y aprobación, no solo otro intent.

```powershell
harness story read --provider C:\estado\provider.json --source 17 --json
harness pr preview --input C:\estado\request.json --json
harness pr preview --input C:\estado\request.json --path C:\cliente --out C:\estado\nuevo-plan.json --json
```

PublicationRequest contiene schema_version=1, intent, authorization y evaluation.
PublicationIntent fija identidad HU/intento, snapshot, commits base/head, ramas,
hashes de contexto/plan/candidato, título/cuerpo, evidencia y draft=true.
intent_sha256 es la clave de idempotencia de contenido. La autorización fija
actor, confirmed, intent_sha256 y acciones push/create_pr; una aprobación de
plan no la sustituye. Cambiar título, destino, candidato o evidencia invalida
la autorización. Los ejemplos sintéticos y schemas están incluidos en el wheel
como story_kit y harness_core/schemas; no autorizan ninguna escritura.

Preview no llama proveedores, autentica, edita target/estado ni cambia
configuración global. Siempre publication_allowed=false porque no comprobó
el candidato final. Exportación crea exclusivamente un archivo nuevo fuera
del target, entradas y estado conocido; rechaza enlaces y archivos existentes.

Publicación usa la HU real ready_to_publish, aprobación vigente, evidencia
de tests/capacidades y revisión independiente del mismo candidato. Verifica
policy/binding actuales, repositorio, prefijo de rama, contexto, intento, hashes,
árbol limpio y un único commit sobre la base congelada. Compara todos los bytes
y modos del árbol contra baseline/candidato: cambios de sync/archive/specs o
evidencia después de aprobar exigen volver a capturar, validar y revisar.
Conservar los recibos HU v1; el receipt de publicación se almacena aparte.
Se comprueban bytes físicos del checkout y blobs Git; solo se admite la
normalización LF/CRLF seleccionada por configuración local core.autocrlf y text/eol. Filtros custom
y working-tree-encoding quedan blocked sin ejecutarlos.

Las evaluaciones se recalculan con el scorer de 06 usando EvalInput milestone=7,
purpose=promotion y execution_mode=manual. E21/E22/E23 y todos los casos anteriores
exigen capturas/anotaciones reales de los perfiles. No se acepta un booleano
passed suministrado por el llamador. Simulaciones, perfiles sin evidencia de
configuración y not_run/blocked no habilitan publicación. 08 sigue no disponible.

```powershell
harness eval report --input C:\estado\evals-07.json --json
harness pr publish --input C:\estado\request.json --path C:\cliente --policy C:\estado\policy.json --binding C:\estado\checkout.json --provider C:\estado\provider.json --json
harness pr reconcile --input C:\estado\request.json --path C:\cliente --policy C:\estado\policy.json --binding C:\estado\checkout.json --provider C:\estado\provider.json --json
```

Antes de mutar, consulta repo, snapshot, base, branch y PR abierto. Journal
SQLite externo por checkout con lock y receipt durable antes del push. El push
usa un lease que permite solo una rama ausente y desactiva hooks; no actualiza
ramas existentes. Resultado unknown requiere lectura/reconciliación antes de
reintentar. Un PR coincidente debe tener marker del intent, repo, base/head,
commit y draft exactos. Conserva receipt/URL y no repite creación. Ramas y PR
ajenos, conflictos de intent y múltiples PR bloquean. Reglas url.* de Git
(incluyendo pushInsteadOf heredadas) bloquean antes de mutar. El puente MCP
recibe expected_old_oid=null/creation_only=true y debe garantizar creación
atómica exclusiva; debe devolver created/previous_oid/branch/head comprobados.
No hace merge/despliegue
ni comentarios. CLI no dispone de gh en este entorno: sus protocolos de
transporte se prueban con dobles, sin certificación GitHub nueva.

El host puede aportar callback síncrono para attach_artifact. Solo devolver
True después de comprobar éxito real; cualquier otro valor/exception conserva
attached=false y attachment_status=failed. La Skill pasiva
harness-story-pr exige llamar la herramienta Codex con la URL verificada y
conservar su resultado real. CLI sin puente informa unavailable; no marca
attached. Una respuesta ambigua de attach se informa y puede reconciliarse;
el attach del app es idempotente. Configuración de conectores no concede permisos.

Resultados JSON conservan schema_version/command/status/checks y códigos 0
para lectura/preview comprobados o receipt publicado, 1 para blocked/unknown,
2 para entrada inválida. Errores externos se reducen a códigos públicos, sin
imprimir stderr ni credenciales. Los controles cubren estos comandos/adaptadores;
no son una frontera de seguridad para herramientas externas de Codex.
