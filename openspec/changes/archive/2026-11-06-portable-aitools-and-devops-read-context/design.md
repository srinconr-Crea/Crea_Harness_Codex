# Design

## Context

La fuente mantenida de esta evolución es `artifacts/crea-manual-kit-0.1.5/`; no es el snapshot pasivo de nueve skills en `resources/vendor` ni su copia de `harness_local`. Ver `proposal.md` y los tres deltas para alcance y requisitos.

La inspección observó 15 skills Databricks, una skill propia `Crea/creating-databricks-agents`, siete OpenSpec y procedencia mixta en `docs/skills-procedencia.json`. Hay una reparación local de enlace de Apps documentada. `docs/extensiones.md` ya permite skills registradas y referencias nativas, pero no instala hooks. `AGENTS.md` y `LEEME-CREA.md` prohíben Boards/pipelines; `docs/entrega-git.md` permite consultas de repo/PR y creación por principal tras aprobación.

0.1.5 tiene modificaciones preexistentes en LEEME, configuración, constituciones, manifiesto y archivos ZIP; su prompt de configuración todavía aparece como no rastreado. Estos bytes son entrada del usuario: preservar y no reconstruir desde HEAD. No heredar las restricciones de `scripts/package_manual_015.py` que exigen que upstream sea idéntico a 0.1.4: la nueva versión permite actualización upstream explícita, pero conserva las anteriores.

Investigación realizada el 6 de noviembre de 2026: Azure CLI 2.91.0, azure-devops 1.0.9, Databricks CLI 1.21.0. Ayuda Azure completa en `research/azure-cli-help.json`. No se consultó Azure DevOps remoto. Azure requirió configuración temporal en workspace y ruta explícita a la extensión existente por restricciones del sandbox; instalación dinámica desactivada. Las peticiones HTTP directas por PowerShell a GitHub fallaron por autenticación TLS; las fuentes públicas sí se consultaron con navegador web. No se ha fijado una nueva revisión Databricks ni descargado el paquete.

## Goals / Non-Goals

**Goals:** una distribución portable 0.1.6 coherente, con selección Databricks reproducible, integración opcional de hooks y una skill CLI Azure con lectura de contexto trazable. Las pruebas automatizadas verifican contratos propios y transportes con dobles; las instrucciones no se presentan como aislamiento del agente.

**Non-Goals:** modificar 0.1.5, activar globalmente plugins/hooks, cambiar modelos o flujo secuencial, conectar el motor histórico, ampliar Azure Pipelines/Boards generales, escribir work items/comentarios, vincularlos a PR, hacer login, instalar herramientas o publicar la entrega.

## Decisions

### 1. Una nueva distribución con dos bloques

Se acepta la elección del usuario: Databricks sigue dentro del kit portable. La alternativa de plugin externo simplifica mantenimiento upstream, pero duplicaría la selección ya distribuida y añade dependencia de configuración externa. Un candidato 0.1.6 reúne ambos bloques; dos releases sucesivas duplicarían cambios de configuración y documentación. No se reutiliza 0.1.5 como staging.

La raíz README se actualiza al implementar para apuntar al candidato y su prompt; `LEEME-CREA.md` es la guía de entrada del ZIP. El prompt original indicado por el usuario se copia a 0.1.6 antes de editarlo. El nuevo empaquetador conserva hashes de la baseline real de 0.1.5 y de distribuciones históricas, sin declarar que el árbol personalizado coincide con un manifiesto anterior cuando no sea así.

### 2. Selección Databricks y actualización controlada

La fuente única es `databricks/databricks-agent-skills`, usada por AI Tools. Resolver una revisión inmutable al comienzo de Apply, contrastar el manifest contra archivos de esa revisión y conservarla para skills, hooks y recursos de enrutamiento. No usar `main` flotante para descargas sucesivas. Si una skill existente fue retirada o renombrada, documentar su sustitución y actualizar consumidores, sin crear alias con una segunda implementación ni conservar silenciosamente una skill obsoleta.

Actualizar las 15 existentes y seleccionar inicialmente nueve adicionales: `databricks-execution-compute`, `databricks-lakebase`, `databricks-unity-gateway`, `databricks-mlflow-tracing`, `databricks-ai-functions`, `databricks-aibi-dashboards`, `databricks-metric-views`, `databricks-spark-structured-streaming`, `databricks-lakeflow-connect`. Esta es una selección de diseño por ingeniería de datos, Apps, analítica y observabilidad, no una lista aprobada de operaciones remotas. Completar dependencias obligatorias transitivas de esas skills y las actuales; tratar `databricks-serverless` o cualquier nombre retirado según el manifest fijado y referencias efectivas. No incorporar automáticamente todo `experimental/`.

Usar `databricks aitools install --help` y las opciones observadas `--skills`/`--path` para extracción controlada cuando permita fijar/verificar revisión; si el CLI descarga una revisión flotante, recuperar directamente el bundle Codex de la revisión fijada. No ejecutar `aitools install` sin destino explícito: en CLI 1.21.0 instala plugins por defecto para ciertos agentes. No instalar plugin completo y skills individuales simultáneamente.

Una copia ejecutable por nombre queda en `.agents/skills/<name>/`. Procedencia registra upstream, revisión, ruta, hash original/distribuido, licencia y parches. Una copia pasiva de licencia/fuente no se añade a rutas de descubrimiento. Preservar la reparación de Apps solo si sigue siendo necesaria; no reintroducirla si upstream ya la corrigió. Un validador compara nombres/frontmatter, referencias locales y dependencias obligatorias; menciones opcionales quedan clasificadas, no fuerzan inclusión indiscriminada.

### 3. Hooks incluidos y activación separada

Conservar los scripts oficiales y sus datos en `resources/databricks-aitools/hooks/`, fuera de `.agents/skills/`. Incluir router, context, auth-helper, `_routing_data.json` y las dependencias que liste la revisión fijada. Guardar configuración upstream original y procedencia. Las adaptaciones Windows pertenecen a `scripts/crea/aitools.py` o recursos propios, nunca a una edición oculta del upstream.

`scripts/crea/aitools.py preview --config docs/proyecto.json` produce JSON por stdout: revisión, selección, duplicados detectados en superficies accesibles, diferencias y hooks incluidos/configurados/autorizados/observados. No autentica ni escribe. Cada campo no comprobable informa `unknown`, no ausencia de duplicados. `--out` exige archivo nuevo y ruta autorizada; no sobrescribe.

La activación nativa es un paso separado del setup. Antes de producirla, comprobar la superficie soportada en la versión/host Codex mediante ayuda y documentación oficial, eventos, payloads y política de confianza. Añadir configuración solo en el proyecto seleccionado y conservar hooks previos. El alcance de la propuesta no autoriza activación en esta sesión. El kit empaqueta un procedimiento revisable de activación/restauración, con launcher Windows si es necesario, que no requiere otro bundle con copias de las skills. Si el host no admite hooks por proyecto sin plugin, documentar no soportado y mantenerlos incluidos/inactivos; no simular una integración nativa con `agent_step`.

La sintaxis upstream `${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}` y `|| true` requiere shell compatible; no copiarla a PowerShell sin adaptación. Comprobar intérprete, rutas con espacios, JSON stdin/stdout, nombre real de la herramienta y formato de respuesta. Los hooks son informativos y tolerantes a fallos: el router no cambia gates ni selección de capacidades, context no selecciona perfil por su cuenta, auth-helper no inicia login. Distinguir pruebas con fixtures de cada evento de observación real en el host. La captura automática de evidencia de HU no es función de estos hooks.

### 4. Skill Azure y separación entre conocimiento y alcance

Crear `.agents/skills/Crea/azure-devops-cli/SKILL.md`, nombre `crea-azure-devops-cli`, con referencias separadas para ayuda/fuentes, matriz operativa y comentarios futuros. Registrarla en `extensions.skills`; Planner/Reviewer la usan para lectura, principal la consulta para el flujo de entrega existente. Developer/Tester consumen snapshots. Ningún registro convierte la skill en barrera de permisos.

| Familia | Estado en 0.1.6 |
| --- | --- |
| `boards work-item show` | Lectura de IDs de la HU, Planner/Reviewer |
| `devops invoke` GET de comentarios | Solo mismo work item validado y ruta/API acotadas |
| `repos show`, `repos pr list/show/create` | Solo flujo de entrega y autorizaciones actuales del principal |
| `boards query`, área/iteración, gestión de relaciones | Fuera de alcance operativo nuevo |
| `boards work-item update --discussion`, create/update/delete | Referencia futura deshabilitada |
| `pipelines` y subgrupos | Documentación de capacidades, ninguna operación habilitada |

La ayuda local confirma que `work-item show` admite `--id`, `--organization`, `--detect false`, `--expand` y JSON; no admite `--project`. Comprobar `System.TeamProject` contra el nombre canónico del proyecto seleccionado antes de pedir comentarios. El setup conserva ID y nombre canónico de proyecto para comparar; si solo hay ID y no se puede comprobar el nombre, informar pendiente y no ampliar consultas de metadatos como efecto de esta excepción.

Forma de consulta de work item: `az boards work-item show --id <id> --organization <org> --detect false --expand all --output json`. No ejecutar placeholders. Para `repos pr show` tampoco añadir parámetros no soportados de proyecto/repositorio; comprobar esos campos en la respuesta como ya pide entrega Git. No activar `--work-items`, `--transition-work-items`, auto-complete ni bypass-policy en PR.

La referencia de Microsoft `boards-work-item-summary` orienta campos, vínculos y resumen, pero su instrucción de usar MCP no se copia como requisito CLI. No seguir automáticamente todos los vínculos ni leer work items relacionados fuera del conjunto de la HU seleccionado. Registrar enlaces sin consultar PR o pipelines desde Planner/Reviewer.

### 5. Helper mínimo de lectura y evidencia

Crear `scripts/crea/azure-devops.py` y módulo propio `scripts/crea/integrations/azure_devops_context.py`, usando biblioteca estándar. El helper no recibe cadenas shell ni comandos arbitrarios: construye argv con `subprocess`, valida operación/rol/destino y no implementa escrituras. Contratos CLI:

- `preview --config <config> --request <context-read-request>`: stdout JSON, sin red ni archivos.
- `read --config <config> --request <context-read-request> --out <archivo-nuevo>`: solo lectura remota; resultado local en expediente permitido.

Configuración opcional `integrations.azure_devops_context` en `docs/proyecto.json`/schema: `enabled` booleano (false por defecto), `organization`, `project_id`, `project_name`, `timeout_seconds` (30), `max_comment_pages` (100), `comments_page_size` (100). Organización/proyecto pueden inicializarse desde los datos Azure existentes del cliente con reconciliación explícita si difieren. El ID pertenece a la solicitud de cada HU, nunca a una lista global compartida entre historias. `enabled` permite el procedimiento, no concede permisos nativos.

Crear un contrato propio `docs/plantillas/azure-context-request.schema.json`, sin ampliar el handoff histórico: este representa una salida con sender/recipient y aún no existe al empezar Planner. El principal prepara antes del despacho `docs/hu/<change>/inputs/azure-devops/<fase>-<intento>.json` con `schema_version=1`, `request_id`, `hu_id`, `change`, `attempt`, `phase` (planificacion/revision), `executor_role` (planner/reviewer), `created_by=principal`, `created_at_utc`, `work_item_id` entero positivo, `organization`, `project_id`, `project_name`, `evidence_dir` y `previous_snapshot_ref` nullable. La pareja phase/executor_role debe ser planificacion/planner o revision/reviewer; los destinos deben coincidir con configuración y expediente de la HU. Creación exclusiva, sin campos result/completed ni aprobación de escritura remota.

Esta versión lee un work item principal por HU/solicitud; `identity.external_story_id` singular del handoff final conserva ese mismo ID. Vínculos a otros work items se documentan sin seguirlos. El resultado registra hash/referencia de la solicitud y el handoff final referencia snapshot/recibo, sin fingir un handoff completo para consultar contexto. Reviewer recibe una nueva solicitud con referencia al snapshot de Planner. Fases principal que representan Planner/Reviewer se identifican como tales, sin extender lectura al principal en cualquier momento. No aceptar una simple cadena `--role` como autorización. Los contratos orientan y el helper limita sus propias llamadas; no impide que una herramienta externa eluda el helper ni demuestra autoría por un campo JSON.

Para comentarios, `az devops invoke --help` confirma `--area`, `--resource`, `--route-parameters`, `--http-method`, `--api-version`, `--query-parameters`. Microsoft documenta GET `/{project}/_apis/wit/workItems/{workItemId}/comments`, API `7.1-preview.4`, con token de continuación. Implementación debe contrastar el nombre de recurso CLI con metadata/SDK oficial de la versión; no presentar `--resource comments` u otro nombre supuesto como smoke exitoso. Registrar esa correspondencia en referencias. Solo área WIT, recurso de comentarios comprobado, GET y ruta del ID ya validado; no exponer invoke genérico ni usar el default de API 5.0. Ruling de implementación: azure-devops 1.0.9 rechaza el sufijo `.4` al convertir la versión a float; usar `--api-version 7.1-preview`, forma admitida por la gramática oficial con revisión de recurso opcional. Conservar `7.1-preview.4` como versión de referencia Learn y registrar revisión negociada como unknown hasta observarla; no afirmar un smoke remoto. La metadata oficial del CLI identifica `wit/comments` con location ID `608aac0a-32e1-4493-a863-b9cf4566d257` y resourceVersion 4. No fallback silencioso a otro transporte.

Recuperar páginas hasta completar o alcanzar límite explícito y declarar `partial`. Validar cada página, detectar token repetido y paginación inconsistente, deduplicar por ID/versión e informar conflictos. No pedir comentarios eliminados por defecto. Conservar ID, versión, fechas y texto necesario; nombres de autor solo si se necesitan, sin correo/tokens ni respuestas crudas de diagnóstico. Con 403/timeout/formato inesperado informar failed o partial, nunca `no_comments` por error.

Resultado local versionado: `schema_version`, `hu`, `attempt`, `role`, `observed_at_utc`, `operation`, `organization`, `project_id/name`, `work_item_id`, `work_item_rev`, `cli_versions`, `status`, `comments_coverage`, `page_count`, `snapshot_sha256`, `snapshot_ref`, `errors`. Snapshot normalizado incluye título, descripción/criterios, revisión y comentarios confirmados; evidencia del handoff referencia ese archivo/hash sin duplicar logs. Resultado y snapshot se crean exclusivamente bajo `docs/hu/<change>/evidence/azure-devops/<fase>-<intento>/`; rechazo de archivos existentes, enlaces, rutas fuera de expediente y secretos reconocibles. Los filtros no prometen sanitización perfecta: evidencia privada permanece local salvo publicación expresamente revisada.

Códigos propuestos del helper: 0 lectura completa o preview válido; 1 fallo de consulta, parcial o capacidad no disponible; 2 entrada/alcance inválido. Código no cero no prueba cero efectos ni exige reintentar ciegamente. No escritura remota en ningún caso. No login ni instalación dinámica; ayuda/consultas usan configuración existente o directorio temporal explícito si hace falta evitar escrituras globales de sesión del CLI.

El conjunto work item/comentarios no es una transacción atómica. Guardar intervalo de observación y hashes, releer revisión del work item al terminar; si cambió, marcar contexto inestable. Una revisión igual no garantiza comentarios inmutables: Reviewer vuelve a contrastar contenido/hash de comentarios. Cambio material de criterios/decisiones requiere reconciliar plan; un comentario informativo nuevo se registra sin invalidar automáticamente toda la evidencia técnica.

### 6. Escrituras futuras solo como referencia

La ayuda comprobó `az boards work-item update --discussion`; la referencia futura explica que publicar exige una nueva capacidad aprobada, destino/texto exactos presentados, autorización concreta, verificación posterior e idempotencia/reconciliación. El helper no acepta esa operación, y la skill no da un procedimiento ejecutable habilitado. Pedir una modificación ahora permite preparar borrador local y señalar el límite, sin pedir una aprobación que esta versión todavía no puede aplicar.

### 7. README y prompt forman parte de aceptación

En el nuevo prompt conservar los campos/editables y pasos actuales. Ajustar el paso Databricks para usar selección portable fijada y comparar diferencias; actualización a otra revisión durante setup requiere un diff y autorización de ese alcance, no actualización global implícita. Registrar versión, ayuda real, deduplicación y dependencias. Reemplazar la oferta vaga de instalar tres hooks por inspección de compatibilidad y oferta de activación concreta, con estados/resultados verificables y conservación de hooks del cliente.

Añadir configuración Azure de lectura, proyecto canónico e IDs por HU, credenciales ya disponibles y límites por fase. No leer HU de negocio durante bootstrap salvo petición concreta; dejar listo el procedimiento. Registrar versiones/comandos/fuentes/evidencia, distinguir configuración, prueba local y ejecución real. Mantener prohibiciones de login, instalación no autorizada, push/PR de setup y cambios de constituciones. Revisar AGENTS, LEEME, guía, entrega Git y README para que ninguna prohibición genérica de Boards contradiga la excepción precisa ni parezca habilitar pipelines.

## Risks / Trade-offs

- Upstream/README/CLI divergen: priorizar ayuda de la versión ejecutada para sintaxis y registrar discrepancias con las fuentes, sin seguir una página mutable como lock.
- Actualización amplia introduce cambios de comportamiento: revisión por skill, parches declarados y prueba de referencias/dependencias; selección de capacidades sigue siendo por HU.
- Host no soporta registro nativo portable: distribuir recursos y estado no soportado en vez de instalar un plugin duplicado o afirmar activación.
- Datos privados o prompt injection en comentarios: tratarlos como datos, minimizar snapshot, no ejecutar contenido ni publicar automáticamente.
- Snapshot incompleto o concurrente: cobertura explícita, límites de paginación, revisión posterior y reconciliación material.
- Modificaciones del usuario durante empaquetado: baseline por bytes y comprobación posterior; conflicto conserva fuentes y detiene solo empaquetado afectado.

## Migration Plan

1. Capturar baseline de fuentes existentes, incluyendo prompt no rastreado; crear staging 0.1.6 sin tocar históricos.
2. Resolver revisión y selección Databricks, incluir hooks pasivos y contratos de inspección; verificar procedencia/duplicados.
3. Añadir skill/helper/configuración Azure y casos con dobles; actualizar roles/orquestación y referencias de evidencia.
4. Actualizar README, guías y prompt en el candidato; verificar árbol, manifiesto, ZIP y preservación de baseline.
5. Adopción en cliente por preview y diff revisado, sin sobrescritura de personalizaciones ni activación de hooks implícita. Rollback restaura solo configuración añadida que siga coincidiendo con hashes propios; nunca borra hooks/skills ajenos.

## References

- Databricks: https://github.com/databricks/databricks-agent-skills y https://github.com/databricks/databricks-agent-skills/blob/main/manifest.json
- Hooks: https://github.com/databricks/databricks-agent-skills/blob/main/hooks/codex-hooks.json
- Microsoft skills: https://github.com/microsoft/azure-devops-skills y `.github/skills/boards-work-item-summary/SKILL.md` en ese repositorio.
- Work items: https://learn.microsoft.com/en-us/cli/azure/boards/work-item?view=azure-cli-latest
- Invoke: https://learn.microsoft.com/en-us/cli/azure/devops?view=azure-cli-latest#az-devops-invoke
- Comentarios: https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments/get-comments?view=azure-devops-rest-7.1
- Repos/PR: https://learn.microsoft.com/en-us/cli/azure/repos/pr?view=azure-cli-latest
- Pipelines, solo referencia: https://learn.microsoft.com/en-us/cli/azure/pipelines?view=azure-cli-latest

Las URLs `main` son referencias investigadas, no lockfiles. Al implementar se conservan revisión/fecha/hash de los recursos realmente incorporados. Ayuda local comprobada no certifica permiso remoto ni compatibilidad nativa de Codex.
