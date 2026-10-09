# Aplicación y recuperación de onboarding

El preview admite `--binding FILE` existente o `--binding-out FILE` con
`--checkout-id ID --state-dir ABSOLUTE`. No se pueden combinar. Para un
descriptor ausente se requieren `--repo OWNER/NAME --base-branch BRANCH`.
El cliente procede de la política; el estado termina en cliente/checkout.
Se rechazan solapamientos, symlinks/junctions, aliases Windows (ADS, device
names, trailing dot/space), rutas globales administradas y padres inexistentes
del plan/binding. Exportación exclusiva: no crea padres ni sobrescribe archivos.

El reporte distingue `applicable` de readiness. Herramientas opcionales ausentes
pueden producir diagnóstico blocked/código 1, mientras el plan permite crear
archivos del kit. Python y Git compatibles son indispensables. Apply puede
terminar con `application_status: completed` y código 1 por doctor fallido.
Desktop y acceso Databricks conservan `not_checked`: no se autentica ni certifica
acceso remoto. No se ejecutan tests, modelos, instalaciones, jobs ni Git writes
sobre el cliente. Los ejemplos CLI completos están en README.

## Contratos y confianza

`OnboardingPlan` v1 contiene destinos, entradas/hashes, binding, descriptor,
contenido UTF-8 de operaciones create_file, manifiesto del kit y hash canónico.
JSON usa claves ordenadas, sin whitespace incidental. `plan_sha256` excluye
su propio campo; no es firma ni autorización. El operador vuelve a seleccionar
target y política en apply. Los contenidos se regeneran desde recursos propios
para rechazar un payload arbitrario aun con hashes recalculados.

Límites: plan/journal de hasta 1 MiB, hasta 64 creaciones de archivo por plan,
128 KiB UTF-8 por archivo y hasta 256 operaciones de journal, contando
directorios. JSON estricto rechaza duplicados, campos extra, versiones y secretos
reconocibles. Los schemas publicados y empaquetados proceden de Pydantic; los
límites relacionales, de bytes y de filesystem también requieren Python.

`read_only_paths` y `denied_paths` protegen archivo y descendientes del path
coincidente. `/` separa componentes; `*` y `?` no cruzan `/`, `**` representa
componentes completos, incluido cero. El matching ignora casing en Windows.
`max_files` y `max_bytes` suman todas las creaciones dentro del target. No hay
excepción para bootstrap: si falta `.harness/client.yaml` y `.harness/` está
protegido, revisar la política y generar otro plan. `branch_prefix` no cambia ramas.

## Escritura Windows

Se fijan handles de directorios, sin FILE_SHARE_DELETE, y se abre cada siguiente
componente respecto del handle padre con NtCreateFile, FILE_OPEN_REPARSE_POINT
y FILE_CREATE para nuevas entradas. Se comprueban atributos, links, identidad
de archivo y GetFinalPathNameByHandleW. La creación conserva la exclusividad y
confinamiento durante write/flush y registro de completion. El kit falla cerrado
en plataformas sin esta implementación. No ofrece una transacción distribuida
ni protección frente a un administrador que controla el equipo.

## Estado y recuperación

Estado externo: `state_dir/onboarding/RUN/plan.json` y `journal.json`;
`state_dir/onboarding.lock` excluye operaciones por checkout. No usa SQLite ni
configuración global. El journal permanece como evidencia y su confianza depende
de que el operador proteja el estado local: los hashes no autentican al propietario.

Estados de ejecución: in_progress, completed, failed, recovered y
recovery_conflict. Entradas: planned, creating, created, failed, removed y
conflict. Se persiste intent antes de crear y completion después de flush,
incluyendo identidad Windows (volumen, índice y fecha de creación) y hash.
Se escribe un temporal exclusivo con flush y se sustituye el journal en su
padre fijado. Una pérdida de energía puede dejar propiedad incierta; no hay
promesa de atomicidad entre journal y archivos, ni de rollback automático.

El lock registra PID, nacimiento del proceso y run_id. Un segundo proceso
rechaza el lock existente; no se elimina por edad. Recuperación explícita solo
retira el lock cuando se demuestra que el dueño original murió (incluye PID
reciclado); identidad inaccesible o dueño vivo requiere intervención manual.

Recover acepta binding existente o plan explícito cuando el binding todavía no
se creó. Usa el plan conservado y la política seleccionada para comprobar
identidad/allowlist antes de leer el journal. Dry-run no crea locks ni modifica
journal/archivos. Apply recorre operaciones en orden inverso: retira únicamente
creaciones con completion durable, identidad y hash actuales intactos; directorios
propios solo si vacíos. Un archivo parcial, editado o con intent sin propiedad
probada se conserva y produce recovery_conflict. No hay borrados recursivos.

Una aplicación completed intacta del mismo plan reutiliza run_id y archivos.
Modificaciones posteriores provocan conflicto. Una ejecución fallida exige
recuperar/resolver y generar un plan nuevo: no se reanuda automáticamente.
La recuperación conserva evidencia, temporales de fallo y directorios de estado;
la limpieza manual del estado exige revisión del operador.
