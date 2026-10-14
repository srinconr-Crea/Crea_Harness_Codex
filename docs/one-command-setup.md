# Instalación de un comando y setup guiado

Este flujo instala un **candidato de prueba** para Windows x64. Codex Desktop
debe estar instalado y autenticado. Instalación, preparación local, descubrimiento
en Codex y certificación tienen evidencias distintas; los gates históricos de
06–08 siguen pendientes. `certified=false` y `release_allowed=false` se conservan.

## Kit y comando de instalación

El kit contiene el wheel, seis wheels transitivos, el lock de Python, Python
3.13.7 oficial, Git portátil 2.51.0, Node 22.20.0, OpenSpec 1.13.2 con su cierre
de 70 paquetes npm y CLI Databricks 0.292.0. Se conservan licencias y NOTICE.
Las versiones y hashes se fijan en `official-tools.json`, el lock npm y el
manifiesto del kit; no se resuelven versiones `latest` al instalar.

Construcción del candidato desde el repositorio:

```powershell
.venv/Scripts/python.exe scripts/prepare_distribution.py
.venv/Scripts/python.exe scripts/prepare_installation.py
```

Revisar primero el preview, que verifica los archivos sin escribir ni descargar:

```powershell
& './dist/install-kit/install-harness.ps1' -Kit './dist/install-kit' -Preview
```

Después de revisar el manifiesto y su hash, un comando prepara el runtime y
registra la Skill. Sustituir `HASH_REVISADO` por el SHA256 del manifiesto:

```powershell
& './dist/install-kit/install-harness.ps1' -Kit './dist/install-kit' -ManifestSha256 HASH_REVISADO -Tools @('git','node','openspec','databricks') -Apply
```

El default es `%LOCALAPPDATA%/LocalHarness/installations/0.1.0` y la Skill va
a `$HOME/.agents/skills/harness-setup`. `-InstallRoot` y `-SkillRoot` permiten
probar otro ámbito explícito. Python compatible se reutiliza, o se prepara
Python oficial por usuario con `InstallAllUsers=0`, `PrependPath=0`,
`AssociateFiles=0` y sin launcher ni atajos. No se cambia PATH, execution policy
global ni instalación/configuración de Codex. Un bloqueo corporativo se informa.

Para un canal online revisado, conservar el punto de entrada y `fs-guard.dll`
del kit juntos, y pasar `-KitUrl URL_HTTPS_FIJADA -KitSha256 HASH_DEL_ZIP`.
Preview muestra URL, checksum, caché y destinos sin descargar. El canal/URL
público definitivo depende de una publicación posterior; aquí no se publica.
El kit offline permite operar sin descargar durante la instalación.

Protocolo local repetible del wheel instalado (usar una carpeta de prueba nueva):

```powershell
& 'RUTA_RUNTIME/Scripts/python.exe' -I -B './scripts/verify_installed_setup.py' --installation-record 'RUTA_INSTALACION/installation.json' --scratch 'RUTA_PRUEBA_NUEVA'
```

Comprueba procedencia del módulo instalado, recursos, preparación, ocho roles,
commit local, baseline limpia e idempotencia con un cliente sintético. No aporta
observación de Desktop ni OAuth real.

## Primera conversación

Una vez instalado, comprobar `$harness-setup` en un chat local antes de preparar
un cliente. La ruta de descubrimiento soportada es la documentada para Skills
de usuario. Si no aparece, recargar/reiniciar Codex y comprobar de nuevo.
`resource_installed` prueba presencia; `skill_discovery_pending` conserva la falta
de observación en Codex. La Skill usa `invoke-setup.ps1` y un runtime absoluto
registrado, con verificación de ownership y sin depender del cwd.

Conversación sugerida: «Prepara este repositorio con los archivos de descriptor,
política y binding adjuntos, esta URL y este alcance; pregunta solo lo faltante».
El agente importa referencias o valores y crea un JSON tipado temporal. Nunca
pide editar comandos manualmente ni solicitar PAT/passwords en el chat.

```powershell
harness setup interview --input setup-input.json --json
harness setup preview --input setup-input.json --json
harness setup preview --input setup-input.json --plan-out setup-plan.json --json
harness setup apply --plan setup-plan.json --authorize HASH_DEL_PLAN --json
harness setup status --plan setup-plan.json --json
harness setup recover --plan setup-plan.json --authorize HASH_DEL_PLAN --json
```

Desde la Skill se usan los mismos argumentos mediante `invoke-setup.ps1`; el
comando `harness` anterior ilustra la API, sin exigir añadirlo a PATH. Preview
sin exportación no clona, instala, autentica, crea SQLite ni modifica target,
estado o configuración de usuario. Exportación crea exclusivamente el padre,
que contiene los hijos/recetas, sus hashes y efectos. Una autorización cubre
esa revisión; drift requiere revisarla otra vez. Login/confianza del host
continúan siendo interacciones externas del operador.

## Contratos y alcance

Los cinco contratos nuevos son `InstallationRecord`, `SetupInput`, `AccessScope`,
`SetupPlan` y `SetupReport`; sus schemas están en `schemas/` y en el wheel.
Descriptor, política y binding v1 conservan sus schemas publicados.

`SetupInput` lleva los contratos v1, URL opcional, alcance, capacidades y fuentes
(`file`, `user`, `local`, `template`). `guided_request` referencia la preparación
v1, incluyendo decisiones de desarrollo, herramientas y perfiles de los roles.
`installation_record`/`installation_kit` seleccionan el producto y fuentes
fijadas; `clone`, `commit_local` y `remote_read` son decisiones independientes.

`AccessScope` contiene `client_id`, `policy_sha256`, `read_allow`, `write_allow`
y `deny`. Rutas relativas con `/` final permiten descendientes; sin `/` final
identifican un archivo exacto. No se admiten globs, ADS, traversal, nombres
reservados, aliases Windows ni reparse points. Deny prevalece, política v1
restringe adicionalmente y el plan delimita las operaciones. No hay permiso
general por defecto. La integración técnica tiene destinos exactos revisables;
no amplía silenciosamente el alcance de negocio. El alcance portable queda
en `.harness/access-scope.json`; la vinculación de setup permanece junto al
binding externo. No intercepta toda herramienta nativa de Desktop.

Al mover de máquina, volver a seleccionar target, checkout, estado y perfil;
revalidar identidad/remoto y regenerar el binding local. No copiar credenciales,
estado o rutas ajenas a ciegas. Los ejemplos son genéricos y deben sustituirse
por decisiones locales: `docs/examples/setup/complete.json` y `partial.json`.

## Etapas, recuperación y capacidades

Las etapas son validate → tools → checkout → prepare → integrate → auth → check
→ report. Los adaptadores conservan sus journals, locks y precondiciones; setup
añade su journal padre y comprueba hashes/identidad antes de cada etapa.
Preparación y autenticación cancelada pueden coexistir. Nunca se hace push,
ejecutan jobs, deploy o escrituras de datos como parte de setup.

`commit_local=true` requiere un índice sin cambios ajenos y una identidad Git
ya configurada. Solo añade archivos gestionados revisados; no inventa usuario
ni email. La baseline limpia y los gates de HU siguen siendo requisitos aparte.
Una recuperación conserva personalizaciones y recursos ajenos. Una fase externa
incompleta puede necesitar una nueva revisión; no se promete rollback transaccional.
El instalador reanuda en un runtime nuevo dentro de su raíz verificada y conserva
los restos parciales. `-Update` usa otra raíz seleccionada y verifica la Skill
anterior antes de respaldar/reemplazar recursos propios intactos.

Para Databricks se prepara la CLI fijada y se usa OAuth nativo con host/perfil
seleccionados. `remote_read=true` permite únicamente la comprobación de identidad
`current-user me`; cancelación o denegación conserva `prepared` local. Tokens
y salida de login no se registran en planes, logs ni repositorio. Autenticación
no prueba permisos de jobs ni compatibilidad de fixtures remotas.

El informe separa prepared, available, blocked, not_checked y unsupported.
La evidencia registra identidad, versión, fecha, hash y vigencia; una configuración
presente no prueba activación ni aislamiento. Agentes standalone usan `name`,
`description`, `developer_instructions`, modelo/esfuerzo seleccionados y heredan
permisos del padre; `sandbox_mode` por agente se omite por ser ignorado.
Configuraciones incompatibles se rechazan preservando su contenido.

| Código | Significado |
| --- | --- |
| 0 | Operación completada/preparada; no implica certificación |
| 2 | Entrada o identidad inválida |
| 3 | Capacidad, autenticación o acceso bloqueado |
| 4 | Conflicto/precondición o plan stale |
| 5 | Integridad/infraestructura |
| 6 | Recuperación requerida |

Los motivos estructurados incluyen `invalid_input`, `identity_mismatch`,
`access_denied`, `tool_unavailable`, `download_integrity_failed`,
`skill_discovery_pending`, `auth_pending`, `permission_conflict`, `plan_stale`,
`owned_resource_conflict`, `recovery_required` y `remote_not_checked`. Los códigos
legacy permanecen en sus interfaces; setup no redefine sus contratos.

## Interfaz para 10 y evidencia real

10 puede importar `SetupReport`, usar `client_id`/`checkout_id`/`plan_sha256`,
consultar capabilities/receipts vigentes y conservar los gates existentes. Debe
revalidar antes de una HU y no convertir prepared, archivo o push en certificación.

La prueba en una segunda máquina Windows (5.3) queda `not_run`, por autorización
expresa del usuario del 14 de octubre de 2026 para archivar ese pendiente.
Pruebas locales y dobles no sustituyen descubrimiento real, modelos/permisos,
OAuth observado ni ese protocolo. Pendientes históricos de 06–08 se conservan.

Fuentes revisadas: [Skills de usuario](https://learn.chatgpt.com/docs/build-skills),
[formato e herencia de agentes](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[Python oficial](https://www.python.org/downloads/release/python-3137/),
[Git portátil](https://github.com/git-for-windows/git/releases/tag/v2.51.0.windows.1),
[CLI Databricks fijada](https://github.com/databricks/cli/releases/tag/v0.292.0).
