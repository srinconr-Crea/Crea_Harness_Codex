# Trabajo de equipo — kit portable 0.1.9

Cada persona usa su sesión Codex y un checkout/índice independiente. Los roles siguen
secuenciales dentro de cada HU. Contexto, reglas, perfiles aprobados, OpenSpec y catálogo
se comparten por Git, con sus revisiones; no se sincronizan sesiones ni se añade un coordinador.

## Configurar una vez y clonar después

A prepara la configuración compartida en una rama de setup. Se publica e integra por
el proceso autorizado del equipo antes de crear HUs desde esa base remota. El setup no
autoriza push/PR por sí solo. Los demás clonan, abren y usan [C](preparar-desarrollador.md),
con entorno y credenciales personales sin editar la configuración común.

Ejemplo a revisar por el responsable, conservando el resto de delivery:

```json
{"project":{"base_branch":"sprint/XX"},"delivery":{"pr_target_branch":"quality",
 "remote":"origin","branch_prefix":"feature/","protected_branches":["main","master","develop","quality","test"],
 "compatibility":{"enabled":false}}}
```

`pr_target_branch` ausente/null conserva destino igual a base. Compatibilidad se adopta
explícitamente y empieza informativa; no activar enforcing ni adaptadores por instalar.
La receta de equipo no es otro perfil de ejecución ni un segundo catálogo.

## Una HU hasta el PR

Principal verifica repo/remoto/HEAD limpio y base remota real; crea feature libre desde
su SHA B antes de escribir. Nunca trabaja/publica la HU sobre base, destino, quality,
test o protegidas. Colisión de nombre no autoriza reutilizar una rama ajena. Para reanudar,
verifica el registro propio sin reset/stash. Usa `entrega.py inspect` para contrastar
rama y repo localmente, y la operación explícita snapshot para observar el remoto.

Planner usa OpenSpec y presenta artefactos; espera nueva indicación humana de Apply.
Developer implementa/prueba lo previsto. Principal reconcilia diff completo y plan;
Tester ejecuta la selección; Reviewer consume gate, verifica código/specs y semántica.
Se aplica [compatibilidad](compatibilidad.md) antes de presentar el PR y se contrasta
de nuevo el destino justo antes de crearlo o preparar el formulario.

Se conservan B (nacimiento), V (`scope.base`, base técnica ancestral del plan), H (candidato)
y Q (destino observado). No usar quality divergente como base de `collect`. Si sprint
incluye commits ausentes de quality, `entrega.ranges` los presenta como heredados; decidir
su inclusión expresamente antes de publicar. Los SHA aprobados pueden registrarse en
`scope.git_delivery.approved_inherited_commits`, que participa en el contexto autorizado.
No ampliar rutas ni atribuirlos a la HU para hacer pasar el control.

Tras revisión y Sync favorables, presentar diff/candidato, pruebas, alcance completo,
remoto, feature, destino, título/cuerpo e informe. Conservar aprobación concreta de
Archive/commit/push y PR según proveedor. Archive solo mueve lo previsto; cambios
funcionales requieren reconciliar plan/revisión. Publicar rutas explícitas y verificar
árbol, índice, todos los commits publicables y SHA remoto. No `git add .`, force-push o
edición posterior del commit solo para incorporar su propio SHA.

Azure DevOps Services conserva `az repos pr create` después de aprobación y lectura
posterior de ID/URL/repo/ramas/SHA/textos. GitHub y Server conservan formulario/borrador
manual; enlace no equivale a PR creado. Solo push no autoriza PR. Una aprobación completa
vigente no se pide de nuevo por cambiar de rol o por un avance independiente del destino.

## Después del PR

La revisión humana, merge a quality y promoción a test pertenecen al equipo. El kit no
completa PR, activa auto-complete, despliega, ejecuta pipelines ni borra ramas. Un snapshot
es puntual: quality puede cambiar después; la revisión final debe considerar ese estado.
No merge/rebase/cherry-pick automático para resolver incompatibilidades. Si el equipo
aporta una feature actualizada, preservar B y acordar V/candidato nuevos con sus pruebas.

## Actualizar o revertir

B combina distribución origen exacta, cliente personalizado y kit nuevo. Actualiza
schemas/consumidores/configuración juntos en un punto acordado; conserva modelos,
reglas, activaciones, catálogos y evidencia. Opcionales ausentes siguen ausentes. Si falta
baseline, reconocer el límite y conservar personalizaciones inciertas. Revertir el mismo
conjunto y mantener expedientes nuevos como historia no consumida; no reescribir recibos,
reiniciar max_fix_rounds o desactivar gates para aprobar. Ver [composición](composicion-kit.md).

La entrega con destino separado exige `evidence.target_snapshot` con path/hash del snapshot
verificado y `scope.git_delivery` aunque compatibilidad esté desactivada. Antes de publicar,
usar `entrega.py scope --repo . --handoff <handoff.json>`: contrasta B/H/Q y los SHA
heredados aprobados sin contactar al remoto. Esto no sustituye la lectura final de vigencia.
