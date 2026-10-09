# Design

## Context

Ver `proposal.md` para motivación y `specs/` para requisitos. La base 0.1.0 tiene `onboarding.preview`, contratos v1 y doctor read-only; el preview exige un binding existente y solo propone contenido concreto de descriptor/AGENTS. OpenSpec faltante se marca manual, y faltantes bloquean el reporte.

`safe_path` y hashes actuales sirven de base, pero son validadores de lectura: no resuelven carreras al escribir. No hay journal ni locks. Las specs actuales de preview deben modificarse explícitamente; las de configuración y doctor conservarán sus garantías de validación sin escritura.

## Goals / Non-Goals

**Goals:** incorporar un aplicador local pequeño, con destinos finitos, política explícita y recuperación conservadora; conservar APIs/flags previos de lectura; no confundir readiness con autorización de archivos.

**Non-Goals:** actualizaciones/sustituciones de archivos existentes, transacción atómica de múltiples archivos/discos, protección contra un administrador del equipo, enforcement general de las herramientas Codex o ejecución remota. No generar reglas de negocio del cliente.

## Decisions

### 1. Dos modos explícitos y un plan exportable

CLI propuesta:

```text
harness init --path TARGET --policy POLICY --binding BINDING --dry-run
             [--repo OWNER/NAME --base-branch BRANCH] [--plan-out FILE] [--json]
harness init --path TARGET --policy POLICY --binding-out FILE
             --checkout-id ID --state-dir ABSOLUTE --dry-run
             [--repo OWNER/NAME --base-branch BRANCH --databricks-profile PROFILE]
             [--plan-out FILE] [--json]
harness init --apply --plan FILE --path TARGET --policy POLICY [--json]
harness recover --path TARGET --policy POLICY (--binding FILE | --plan FILE) --run ID
                (--dry-run | --apply) [--json]
```

`--binding` y `--binding-out` son excluyentes. Para binding nuevo, client_id procede de la política explícita, y checkout_id/estado/destino son explícitos. Repo/rama ausentes se obtienen del descriptor existente, nunca de conversación; si también falta descriptor, ambos flags son obligatorios. El binding nuevo conserva schema v1, calcula el hash de bytes de política y no persiste hasta apply.

Sin modo, conservar `apply_not_supported` código 2 por compatibilidad; modos combinados se rechazan. `--plan-out` solo admite ruta externa al target/estado/global administrado, padre existente y archivo ausente; exportación exclusiva, sin overwrite ni mkdir. Un preview normal no escribe ni crea staging. Exportar un plan con conflictos es admisible para revisión, pero `applicable: false` impide aplicarlo. Readiness y aplicabilidad se calculan separadamente: ausencia de herramientas no utilizadas para la creación deja diagnóstico incompleto, sin bloquear por sí sola las operaciones locales del kit.

Alternativa descartada: regenerar implícitamente el plan durante apply. Podría aplicar datos diferentes de lo revisado.

### 2. Contrato del plan y confianza

Nuevo contrato `OnboardingPlan` v1 separado del reporte CLI: `schema_version`, `kind`, `kit_version`, `resource_manifest_sha256`, identidad, target absoluto, referencias a política/binding (existente o propuesto), estado absoluto, hashes de entradas/archivos comparados, ausencias previstas y operaciones tipadas. Operaciones aplicables solo `create_file` con destino relativo al target o destino binding autorizado, contenido UTF-8 y hash; instrucciones manuales no son ejecutables.

Hasta 1 MiB por plan, máximo 64 operaciones y 128 KiB por archivo, además de los límites de política. Lectura JSON estricta, duplicados/secretos/campos extra rechazados. `plan_sha256` se calcula sobre JSON canónico sin ese campo; es integridad, no firma ni autorización. Apply exige target/política elegidos otra vez por flags, que deben coincidir con el plan. Recalcular contenido esperado desde recursos del kit y contratos: no confiar en hashes auto-declarados para admitir payloads arbitrarios.

Revalidar bytes de policy/binding, descriptor, origin, archivos comparados (incluye Codex si se observó) y ausencias. Cambios en código cliente ajeno al onboarding no invalidan el plan. No permitir alias Windows por casing, trailing dot/space, ADS, device names o dos destinos equivalentes; rechazar solapamientos entre target, binding, policy, plan y estado. Restricciones semánticas requieren Python además de JSON Schema.

### 3. Aplicación permitida y preservación

Solo crear descriptor ausente, AGENTS ausente, configuración OpenSpec ausente, Skills faltantes y binding nuevo. No tocar specs/changes existentes ni TOML de Codex. AGENTS distinto continúa como conflicto sin bypass; integración manual y nuevo preview.

En preview evaluar la política para cada creación dentro del target: patrones con `/`, coincidencia del path/directorio y glob `*`, `?`, `**` definidos sin expansión de shell; matching conservador sin depender de casing Windows. Un path protegido bloquea, incluso `.harness/client.yaml`. No excluir bootstrap de las restricciones; fixtures del nuevo onboarding usarán una política que permita expresamente sus creaciones mediante ausencia de restricciones sobre esos paths. `max_files`/`max_bytes` suman todas las creaciones del target; binding/journal externos están acotados por sus contratos y topes de tamaño. `branch_prefix` no crea ni cambia ramas durante onboarding.

Antes de primera escritura cliente: validar todo, checks indispensables Python/Git/recursos, restricciones, lock y journal disponible. Missing Node/OpenSpec/Databricks no bloquean la creación que usa recursos empaquetados; readiness queda pendiente y exit 1 si doctor falla, con `application_status: completed`. Conflictos de archivos y errores estructurales sí bloquean. No etiquetar esos resultados como readiness completa.

Usar creación exclusiva, escritura completa y comprobación del resultado; nunca overwrite/replace de archivos cliente. Revalidar componentes y enlaces junto a cada operación; Windows requiere protección de apertura contra reparse points y resolución final de handles. Si no se puede garantizar confinamiento, fallar cerrado. No prometer que `safe_path` por sí solo evita carreras. Una muerte a mitad puede dejar archivos parciales: no se elimina nada cuya propiedad/hash no sea comprobable.

### 4. OpenSpec preparado en build, no en runtime

Inspección actual: CLI 1.13.2 admite `init --tools codex --profile custom`; el conjunto de siete workflows depende de configuración custom. Primera tarea específica: generar un fixture con ese CLI, HOME/XDG aislados y telemetría desactivada; medir diferencias, side effects y reproducibilidad. No ejecutarlo sobre un cliente real.

Empaquetar únicamente configuración spec-driven y siete SKILL.md resultantes aprobados en recursos del producto, con manifiesto SHA-256, versión, licencia/procedencia y nombres. Parametrizar solo identidades/raíces explícitas admitidas; no añadir contexto de otro cliente. Runtime lee recursos sin iniciar OpenSpec/npm. `openspec_root` sigue soportado como ruta local del cliente; no usar tiendas externas ni registrar stores. No generar comandos adicionales o metadata de instalación salvo que se incluyan explícitamente en la allowlist revisada.

Si la prueba de generación no entrega recursos verificables, bloquear esta tarea y revisar design mediante update-change; no recortar silenciosamente el soporte a clientes ya preparados ni presentar generación como probada.

Alternativa descartada: `openspec init/update` directamente sobre target durante apply, porque ampliaría escrituras fuera del plan y podría afectar perfil global.

### 5. Journal, exclusión y recuperación

Estado: `<state_dir>/onboarding/<run_id>/journal.json` y lock por checkout. run_id aparece solo en apply, nunca introduce aleatoriedad en preview. Journal con escritura temporal+flush/fsync+replace dentro de estado autorizado, operaciones `planned/creating/created/failed`, hashes y prueba de propiedad cuando se dispone (identidad de archivo y resultado durable). Cada operación tiene intent durable antes de crear y completion durable después.

No hay transacción distribuida entre target/binding/estado. Crear binding como última operación de datos, antes del doctor; el plan propuesto conserva el binding suficiente para recuperar aun si no llegó a crearse. Recovery acepta `--binding` existente o `--plan` explícito validado para obtener ese binding; no deduce permisos desde el journal. Los destinos del plan deben coincidir con el journal y target/política seleccionados por el operador. Un estado completado del mismo plan e iguales archivos se devuelve idempotentemente, sin otra ejecución; cambios posteriores producen conflicto. No hay resume automático de aplicación interrumpida: recuperar o resolver manualmente, luego generar plan nuevo.

Lock exclusivo contiene PID, inicio de proceso y run_id; comprobar identidad del dueño para evitar confundir PID reciclado. No borrar locks por edad. `recover --dry-run` no adquiere/escribe lock ni cambia journal; `--apply` requiere exclusión y dueño anterior muerto demostrado. Si no puede probarse, conservar y pedir intervención manual.

Recuperar en orden inverso solo archivos confirmados propios e intactos; directorios propios solo si vacíos. Registro intent sin prueba durable suficiente, archivo parcial o archivo editado: conservar como `recovery_conflict`. No tomar coincidencia de hash sola como prueba de propiedad de una operación incierta. El journal se conserva como evidencia y no se elimina recursivamente. Si cambió la política seleccionada, revalidar y rechazar recuperación incompatible, sin borrar datos.

### 6. Separación de módulos y evidencia

Agregar contratos de plan/journal y autorizador acotado en core; aplicador, journal/locks, recuperación y recursos OpenSpec en local. Mantener doctor reutilizable/read-only y el preview v1 existente. Actualizar schemas generados, recursos del wheel y docs durante apply.

Códigos: 0 operación completada sin fallos locales (puede quedar partial por not_checked); 1 conflicto, lock, fallo operacional/recuperación pendiente o doctor fallido; 2 argumentos/contratos inválidos. Reusar reporte con `command`, `schema_version`, `status`, `checks`; apply/recover agregan `application_status`/`recovery_status`, run_id y operaciones efectivas. Estados globales existentes no cambian. No traceback ni secretos, ni falsos mensajes de rollback total.

## Risks / Trade-offs

- Mutación concurrente de paths Windows: aperturas exclusivas, protección reparse y pruebas de carreras; fallar cerrado ante garantía insuficiente.
- Pérdida de energía entre archivo y journal: mantener estados ambiguos como conflicto, evitando borrados basados en suposiciones.
- Recursos OpenSpec cambiantes: versión/manifiesto, prueba de generación aislada y comparación del wheel; no usar latest.
- Dos clientes mezclados: identidad cruzada y destinos externos vinculados al mismo checkout; pruebas alpha/beta.
- Política de ejemplo protege `.harness/`: no bypass; preparar una política de onboarding revisada que autorice lo necesario.
- Plan manipulable localmente: validar contra kit y política explícita; el hash no sustituye confianza del operador ni protege contra quien controla todo el equipo.

## Migration Plan

Conservar descriptor/policy/binding v1 y llamadas dry-run existentes. Añadir schemas independientes y reportes extendidos; migrar pruebas del rechazo de init sin modo conservándolo. No ejecutar onboarding contra clientes durante desarrollo. Validar en dos fixtures Windows y wheel aislado. Recuperación es retiro conservador de creaciones del onboarding, no desinstalador general ni reversión de cambios del desarrollador. Sync/archive/publicación requieren una solicitud posterior.
