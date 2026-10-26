# Entrega Git — rama temporal y PR por proveedor

## 1. Contrato
El agente principal prepara la rama, hace commit/push del cambio revisado y entrega un
PR Azure con az repos tras aprobacion expresa; en GitHub, enlace al formulario. Planner/developer/reviewer no hacen commit ni push.
Se conservan las confirmaciones OpenSpec y la aprobacion humana de archivo/publicacion.
No hay creacion desatendida de PR, auto-complete, merge, deploy, force-push ni borrado de ramas.
No configurar automatizaciones, Boards, pipelines, politicas ni recursos Azure.
Crear un PR puede activar validaciones que el equipo ya tenga configuradas; el kit no las configura ni ejecuta por CLI.
La rama es temporal por HU; se conserva en remoto hasta que la persona complete su PR.

## 2. Antes de la primera escritura
Leer project.repository, project.base_branch y delivery. Los siguientes comandos son
ejemplos con origin/main y un slug; sustituir por los valores reales, no ejecutarlos a ciegas.
Comprobar repo, identidad Git, HEAD, remotos y estado:
```powershell
git rev-parse --show-toplevel
git rev-parse --verify HEAD
git status --porcelain=v1 --untracked-files=all
git remote -v
git branch --show-current
```
Para una HU nueva, exigir arbol/indice limpios y base remota existente. Si hay cambios
previos, no stash/reset/commit automatico: separar el setup o pedir que se resuelvan.
Una rama con cambios propios de la misma HU puede reanudarse verificando su registro.
En repo sin HEAD o sin base publicada, terminar primero bootstrap manual de la guia.
Verificar que URL Git real y configurada identifican el mismo repo; sin tokens en evidencia.

Si delivery.branch_name esta configurado, usarlo tras validarlo; si es null, elegir
delivery.branch_prefix + <slug-hu> (feature/<slug-hu> por defecto). Si hay colision,
agregar un sufijo unico y registrarlo antes de escribir, sin reutilizar ramas ajenas. Validar con
git check-ref-format --branch. Nunca usar la base ni una rama protegida como rama de HU.
Comprobar ausencia local/remota antes de crearla. Con ls-remote --exit-code, 2 significa
sin coincidencia; 0 significa existente; errores de conexion/permisos no significan libre.
```powershell
git check-ref-format --branch feature/hu-normalizacion
git branch --list feature/hu-normalizacion
git ls-remote --exit-code --heads origin refs/heads/feature/hu-normalizacion
git fetch origin main
git rev-parse --verify refs/remotes/origin/main
git switch --no-track -c feature/hu-normalizacion origin/main
```
Revisar cada codigo de salida antes de continuar. El fetch comprueba el remoto real;
si el refspec del repo no actualizo origin/main, obtener/verificar la referencia correcta
antes de crear la rama. No modificar una rama ajena ni basarse silenciosamente en HEAD
de otra HU. Registrar nombre, remoto y SHA base antes de delegar escrituras al planner.

## 3. Revision, archivo y aprobacion
El workflow llega a verify y sync. Principal prepara docs/hu/<change>/pr.md con la
plantilla de PR, titulo/cuerpo y enlace determinable, y presenta candidato, pruebas, diff,
rama origen, base, remoto y lista de archivos a versionar (incluidos nuevos/borrados).
Pide una confirmacion concreta: "Aprobar archivo de <change> y commit/push del alcance
mostrado a <remoto>/<feature> y crear PR Azure hacia <base> con titulo/cuerpo presentados". Esperar la respuesta humana.
Si se aprueba solo archive, no inferir push. Si se aprueba commit/push pero no crear PR,
publicar solo lo autorizado y dejar el PR pendiente. No renovar una aprobacion ya explicita.
Con autorizacion completa, reviewer archiva. El recibo de aprobacion y los metadatos
previstos de archivo/publicacion se pueden agregar sin pedir otra aprobacion mientras
no alteren el candidato revisado, los resultados de pruebas, las specs o el alcance.
Principal revisa las modificaciones finales
de specs/evidencia y los movimientos de archive. Si aparece codigo/cambio funcional nuevo,
volver a pruebas/revision y renovar la aprobacion; los movimientos de archivo previstos
no cambian por si solos el candidato funcional aprobado.

## 4. Commit y push del alcance revisado
Confirmar que la rama actual es exactamente la feature registrada; base, main/master/develop
y delivery.protected_branches estan prohibidas como destino de push de esta HU.
Revisar tambien todos los commits que la rama publicaria desde su base, no solo el diff
sin commit: deben pertenecer a la HU autorizada. Comprobar que no hay staging ajeno.
Agregar solo rutas aprobadas, incluidas altas/bajas de artefactos OpenSpec; no git add .
ni git add -A sin paths. Estos son ejemplos: seleccionar las rutas reales del candidato.
```powershell
git log --oneline origin/main..HEAD
git diff --name-status
git diff --cached --name-status
git add -- src/archivo.py tests/test_archivo.py
git diff --cached --check
git diff --cached
git commit -m "feat: normalizar identificadores"
git rev-parse HEAD
git push --set-upstream origin HEAD:refs/heads/feature/hu-normalizacion
git ls-remote --heads origin refs/heads/feature/hu-normalizacion
```
No publicar si el diff staged no coincide con lo aprobado o faltan paths esperados.
Inspeccionar resultado de cada comando; un commit fallido impide el push. Comprobar que
el SHA remoto coincide con el SHA local despues del push. Si la rama remota aparece o
cambia sin corresponder a la HU, detenerse; nunca resolver con force-push ni rebase/reset
automaticos. Si una respuesta de red es ambigua, comprobar el SHA remoto antes de reintentar.
Si no hay cambios que versionar, no crear commits vacios. Solo reutilizar un commit existente
si pertenece al alcance aprobado y su revision sigue vigente. Reportar el estado real.
No editar evidencia despues para insertar el SHA del commit que contiene esa evidencia:
la respuesta final entrega SHA, resultado y enlace. Verificar estado local al terminar.

## 5. Azure DevOps Services: crear PR con Azure CLI
Solo principal y solo con aprobacion que incluya crear PR. Con delivery.enabled=false
no publicar ni crear PR. La instalacion/login son pasos manuales del setup; una HU no
autoriza instalar herramientas ni cambiar configuracion global.
Leer provider=azure_devops, organization (URL HTTPS), project y name_or_id. Resolver
repo con az repos show y comparar remoteUrl con el remoto Git real. No inferir destino
desde defaults globales. Usar parametros explicitos y --detect false en cada consulta.
Verificar push/SHA antes del PR. Usar feature registrada y project.base_branch exacta.

Ejemplo PowerShell: sustituir todos los valores por los datos reales aprobados.
```powershell
$organization = 'https://dev.azure.com/ORGANIZACION'
$project = 'PROYECTO'
$repository = 'ID-O-NOMBRE-REPOSITORIO'
$sourceBranch = 'feature/hu-normalizacion'
$targetBranch = 'main'
az repos show --organization "$organization" --project "$project" --repository "$repository" --detect false --output json
az repos pr list --organization "$organization" --project "$project" --repository "$repository" --source-branch "$sourceBranch" --target-branch "$targetBranch" --status active --detect false --output json
```
Comprobar cada codigo de salida. Si ya hay PR activo para repo/origen/destino, verificarlo
y entregar su ID/URL; no duplicarlo ni cambiar su titulo/cuerpo por iniciativa propia.
Si hay varios, informar ambiguedad. Una consulta fallida no equivale a lista vacia.
Si no existe PR, crear usando el titulo/cuerpo exactos presentados. Separar el cuerpo
revisado en lineas (por ejemplo, cargar un archivo UTF-8 que contenga solo la descripcion;
no enviar la plantilla completa con metadatos como descripcion). Pasar argumentos con
variables/arrays PowerShell, sin Invoke-Expression ni concatenar comandos con contenido.
```powershell
$prTitle = 'feat: normalizar identificadores'
$descriptionLines = @('Problema y comportamiento resultante aprobados.', 'Pruebas ejecutadas y sus resultados.')
$prArgs = @('repos', 'pr', 'create', '--organization', $organization,
  '--project', $project, '--repository', $repository, '--source-branch', $sourceBranch,
  '--target-branch', $targetBranch, '--title', $prTitle, '--description') + $descriptionLines + @(
  '--detect', 'false', '--auto-complete', 'false', '--delete-source-branch', 'false',
  '--output', 'json')
$prResult = & az @prArgs
if ($LASTEXITCODE -ne 0) { throw 'PR no confirmado: consultar PR existentes antes de reintentar' }
$createdPr = ($prResult -join "`n") | ConvertFrom-Json
if (-not $createdPr.pullRequestId) { throw 'Respuesta sin ID de PR: verificar antes de reintentar' }
az repos pr show --id $createdPr.pullRequestId --organization "$organization" --detect false --output json
```
Antes de reportar exito, verificar respuesta/exit code: ID, repository.id, estado active,
sourceRefName=refs/heads/<feature>, targetRefName=refs/heads/<base> y commit origen esperado.
Entregar URL web del PR desde sus enlaces o repository.webUrl verificada + /pullrequest/<ID>.
Si la creacion termina con timeout/respuesta ambigua, consultar por repo/origen/destino
antes de reintentar. Si no se puede confirmar, reportar PR no confirmado; nunca duplicar a ciegas.
No completar el PR, activar auto-complete, saltar politicas, votar, enlazar work items,
ejecutar pipelines ni borrar ramas. El kit termina al crear y verificar el PR.

## 6. GitHub y alternativa web
GitHub conserva el enlace /compare/<base>...<feature>?quick_pull=1 y el borrador;
codificar nombres de ramas para URL y verificar repo real. No ejecutar gh pr create.
La extension Azure DevOps CLI no soporta Azure DevOps Server. Para Server, entregar
el formulario web real del servidor y el titulo/cuerpo, origen/base, indicando creacion manual.
Si falta az/login/permisos en Services, informar bloqueo y entregar borrador/formulario;
no afirmar PR creado ni instalar herramientas como efecto lateral de la HU.

## 7. Salida y configuracion
Entregar SHA local/remoto, origen/base, repo, resultado de push y estado real del PR.
Azure Services: ID, URL y verificacion. GitHub/Server: formulario y borrador, sin afirmar creacion.
Conservar rama temporal. Merge, cierre y borrado quedan para una accion posterior.
Configurar delivery, project.repository y project.base_branch. auto_create_pr=false
prohibe creacion desatendida, mientras pr_creation.azure_devops permite CLI tras aprobacion.
Los valores JSON orientan al agente; no son protecciones tecnicas del servidor.

Fuentes: [Azure CLI PR](https://learn.microsoft.com/en-us/cli/azure/repos/pr?view=azure-cli-latest),
[Azure DevOps CLI](https://learn.microsoft.com/en-us/azure/devops/cli/?view=azure-devops),
[GitHub formulario](https://docs.github.com/en/pull-requests/reference/using-query-parameters-to-create-a-pull-request).

## Contenido canónico y confirmación 0.1.5

Una estructura: docs/plantillas/pr.md; una instancia canónica: evidence.delivery del handoff.
Materializar pr-title.txt y pr-body.md con solo los textos revisados, no la plantilla completa.
pr.md es vista derivada. El digest de aprobación incluye título/cuerpo/repositorio/ramas;
el candidate_digest técnico se autoriza por separado. El SHA que resulte del commit se registra
y contrasta con el contenido probado mediante gate y equivalencia permitida; agregar ese SHA
no cambia por sí solo el contenido autorizado ni provoca una aprobación circular. Un check que
consuma ese SHA como entrada funcional sí requiere validar su vigencia. No editar el commit
para insertar su propio SHA.

GitHub conserva creación manual. `transiciones.github_form` prepara parámetros codificados y
comprueba que decodifican al título/cuerpo exactos; cuando hay navegador, comprobar los campos
reales. Esto no prueba creación. Si no cabe el cuerpo o no se confirma el formulario, entregar
ambos archivos/textos para pegar y marcar draft con contenido pendiente de confirmar, no
form_prepared completo. No fijar un límite universal ni ejecutar gh pr create por iniciativa propia.

Azure Services: cargar UTF-8 del título/cuerpo revisados mediante argumentos estructurados
como en el procedimiento existente; nunca concatenar un comando con su contenido. Leer luego
el PR real y comparar ID/URL, estado, repo, ramas, SHA y título/cuerpo; normalizar únicamente
CRLF/LF y un salto final. `transiciones.verify_pr` contrasta un recibo normalizado de esa lectura;
no consulta el proveedor ni acredita autenticidad por sí mismo. Registrar push_ref y observed_ref
cuando corresponda en el contrato, con path/hash del recibo real. Ante respuesta ambigua,
reconciliar PR existentes antes de reintentar; no reescribir remoto ni duplicar a ciegas.

Estados locales: draft, form_prepared, creation_unconfirmed, created_verified; draft del proveedor
es otra propiedad. Solo lectura real contrastada acredita creado/verificado. Archive no autoriza
push; push no autoriza crear PR. Una autorización completa y vigente evita confirmaciones
repetidas. Falta de CLI/login/permisos permite borrador/formulario, sin instalación implícita.
Sin plantilla nativa duplicada, nuevas integraciones, Boards, merge, deploy o auto-complete.


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
