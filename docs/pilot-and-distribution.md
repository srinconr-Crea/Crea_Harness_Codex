# Distribución candidata y aceptación Desktop

El incremento 08 entrega preparación local y update/recover. La base es
`ce75d69` (0.1.0), que contiene la implementación 07 `af9d645` y el antecedente
del piloto manual NaturaPet. La autorización del 13 de octubre de 2026 permite
desarrollo local anticipado; no cierra las dependencias de aceptación 06/07.

El candidato **no está certificado**. Las 144 capturas reales, el sandbox
compatible, la publicación/reanudación del harness, el usuario nuevo, los dos
clientes y la instalación en otro equipo siguen pendientes. El PR del piloto
manual es un antecedente: no aprueba publicación del harness ni release.

## Preparación Windows desde equipo limpio

1. Obtener el candidato desde el repositorio seleccionado. Revisar el manifiesto,
   las licencias/NOTICE, el launcher y las seis dependencias exactas de
   `runtime-lock.txt`; los SHA comprueban integridad, no firma o confianza.
2. Ejecutar `powershell -File launcher.ps1` para inventario sin escritura. Sin
   herramientas, muestra las ausencias; no cambia execution policy ni instala.
3. Preparar Python 3.13 y Git con instaladores revisados. Node/OpenSpec y
   Databricks CLI se preparan separadamente cuando el proyecto los requiere.
   Detección en PATH no certifica versión/funcionalidad; login y confianza
   Desktop requieren observación explícita. No hay plugin certificado.
4. Revisar y ejecutar instalación local explícita con `-Apply -Python ...
   -ProjectRoot ... -Wheelhouse ... -Venv ... -Lock ... -Wheel ... -WheelSha256 ...`.
   El venv debe estar ausente y su ubicación debe ser local al proyecto.
   Se instala desde wheelhouse offline con hashes, sin perfiles preexistentes.
   La ubicación debe estar dentro del checkout seleccionado; se rechazan
   junctions/links y la configuración global de Codex. Si Windows bloquea scripts
   por su política, el operador debe revisar el mecanismo de ejecución; el
   launcher no cambia la política. Las pruebas usan RemoteSigned solo en su proceso.
5. Abrir el checkout cliente en Desktop. Seleccionar política y binding externos,
   distintos por cliente; seguir `onboard --dry-run`, revisar y aplicar por etapas.
   Login, confianza, modelos y sandbox no se heredan de otro cliente.

Reproducción en este repo (Python 3.13, build y setuptools previamente preparados):

```powershell
.venv/Scripts/python.exe scripts/prepare_distribution.py
.venv/Scripts/python.exe scripts/generate_schemas.py
.venv/Scripts/python.exe -m build --wheel --no-isolation
```

La preparación descarga únicamente wheels de las versiones presentes revisadas
del runtime, guarda SHA y licencia, y no los activa globalmente. Para reproducir
el candidato publicado usar su lock exacto; regenerar con otras versiones crea
un nuevo candidato que requiere revisión. El hash del wheel construido se
registra externamente: incluirlo dentro del propio wheel sería circular.

## Contratos y comandos nuevos

`ReleaseManifest`, `InstallationBinding`, `UpdatePlan`, `UpdateRequest`,
`UpdateJournal` y `PilotReport` tienen schemas independientes v1, campos extra
prohibidos y rechazo de secretos. Se conservan los contratos anteriores.

```powershell
harness bootstrap --json
harness release candidate --json
harness update preview --path C:/Clients/alpha --policy C:/Config/alpha-policy.json --binding C:/Config/alpha-binding.json --input C:/Plans/request.json --plan-out C:/Plans/update.json --json
harness update apply --path C:/Clients/alpha --policy C:/Config/alpha-policy.json --plan C:/Plans/update.json --json
harness update recover --path C:/Clients/alpha --policy C:/Config/alpha-policy.json --plan C:/Plans/update.json --json
harness update recover --path C:/Clients/alpha --policy C:/Config/alpha-policy.json --plan C:/Plans/update.json --apply --json
harness release gate --input docs/evidence/distribution/pending-pilot-report.json --evidence-root docs/evidence/distribution --json
```

`UpdateRequest` incluye manifiesto candidato, ownership revisado de la instalación
y contenido upstream fijado por sus hashes. La instalación inicial declara solo
archivos propios revisados mediante `InstallationBinding.files`; no toma posesión
automática de archivos existentes. `kit.lock.json` registra ese ownership tras
update. Para cada recurso se comparan installed/upstream/local SHA; edición local,
ausencia del recurso o drift del plan produce conflicto. Resolver requiere revisar
el archivo y generar otro plan; no hay opción force.

Solo actualiza archivos ya gestionados. No añade/elimina recursos upstream ni
modifica `.git/` o `.harness/`. La política limita paths/tamaño/cantidad; los
handles Windows fijan identidad y padres, y el lock por checkout excluye otro
escritor. Backups, plan y journal viven fuera del cliente. Recover exige el mismo
plan/configuración y restaura solo objetos intactos cuya identidad/hash demuestra
ownership. Conserva backups, evidencia y estado personal. Un fallo intermedio se
registra; contenido parcialmente escrito requiere revisión manual conservadora.

Preview no crea estado/target ni autentica. Exportación externa explícita crea
exclusivamente el plan solicitado; rechaza destinos existentes/enlazados, dentro
del target/estado o superpuestos a entradas. JSON conserva schema_version,
command/status/checks. Código 0 indica operación local comprobada (partial
explícito en bootstrap/candidate), 1 bloqueo/conflicto/fallo, 2 entrada inválida.
Errores `update_drift`, `update_identity_mismatch`, `update_conflict` bloquean;
`update_unowned_file`, `update_upstream_unpinned` rechazan ownership no demostrado.

## Aceptación y límites de confianza

El protocolo preparado en `docs/evidence/distribution/protocols.json` conserva
once recorridos `not_run`, recursos/autoridad NaturaPet sin seleccionar y cero
ejecuciones reales. Alpha/beta son fixtures de diseño; sus políticas, bindings,
estado, aprobaciones y candidatos deben seleccionarse y verificarse por separado.
La operación real usa los gates y adaptadores existentes; preparar un fixture
no concede permisos a un catálogo productivo.

El gate importa recibos de operador por protocolo, SHA del candidato y archivos
externos de evidencia; exige fuente desktop_harness, resultado passed, simulated
false, eval report de promoción 07 (mínimo 144) y desktop-check certificado.
Dependencias not_run/blocked, evals simuladas, capturas ausentes, hashes cambiados
y publicación manual no satisfacen el gate. Aceptar evidencia manual supone
revisión humana de su veracidad; estos hashes no prueban por sí solos que un
operador ejecutó una acción ni constituyen firma. El gate no publica nada y no
reemplaza los gates actuales de HU/PR. El candidato permanece no certificado;
un reporte aceptado describe aceptación de esa identidad exacta.

Sync de specs y push de código no convierten estos protocolos en aceptación.
Archivo administrativo con pendientes requiere autorización explícita y conserva
las tareas abiertas; archivo como incremento aceptado permanece bloqueado.
