# Integración de roles y herramientas de Desktop

El incremento 02 entrega una API y comandos locales para configurar un proyecto
mediante un plan explícito. La presencia de archivos, un smoke Python o una
sonda CLI no certifican descubrimiento ni ejecución en Desktop.

## Contratos y responsabilidades

`harness_core.desktop` define `ToolRequirement`, `RoleCatalog`, `RoleAssignment`,
`DesktopIntegrationPlan`, `IntegrationJournal` y `DesktopCertificate`, todos
estrictos y con schema_version 1. Los schemas se distribuyen en `schemas/` y
`harness_core/schemas/`; `scripts/generate_schemas.py` regenera ambas copias.

| Rol | Entrada / salida | Escritura |
| --- | --- | --- |
| principal | HU y límites / alcance y assignments | Solo rutas asignadas |
| analyst (enrich-HU) | HU/contexto / criterios y preguntas | Ninguna |
| impact-analyzer | Diff/fixture / consumidores, grano y pruebas | Ninguna |
| planner | HU/impacto / tareas, ownership y controles | Ninguna |
| developer | Plan/assignment / candidato y pruebas | Solo rutas asignadas |
| tester | Candidato/criterios / resultados y controles | Solo tests asignados |
| auditor | Candidato inmutable / hallazgos verificables | Ninguna |
| verifier | Specs/candidato/evidencia / verificación | Ninguna |

Una HU pequeña puede usar solo principal. `check_assignments` rechaza rutas de
escritura solapadas, incluso descendientes y diferencias de mayúsculas Windows,
salvo isolation diferente. Máximo cuatro assignments; solo principal permite
profundidad de delegación 1. Estas reglas comprueban los assignments del kit:
no interceptan las herramientas de Codex ni garantizan que otra sesión las use.

Cada rol declara local-files y git requeridos y Databricks MCP opcional, con
propósito. Una fase que requiera Databricks debe seleccionar ese requisito antes
de certificarse; no hay alternativas automáticas. Auditor/verifier proponen
`read-only`; la comprobación de permisos efectivos es independiente del texto.

## Recursos pasivos y selección explícita

`load_desktop()` comprueba hashes y referencias a la versión del paquete de
prácticas 01. Recursos propios en `harness_local.desktop_kit`; la Skill
`harness-hu` consulta `load_quality()` y `practices.json`, conserva identidad
cliente y limita delegación. No activa copias upstream ni instala globalmente.
Modelos/esfuerzos no se fijan con nombres universales en recursos distribuidos.

```python
from harness_core.desktop import activate_profiles
from harness_local.desktop_resources import load_desktop

# Datos que debe aportar la cuenta seleccionada, después de observar su selector.
# No son una comprobación automática de disponibilidad.
available = {'modelo-observado-en-la-cuenta': ['high']}
selected = {'developer': {'model': 'modelo-observado-en-la-cuenta', 'effort': 'high'}}
catalog = activate_profiles(load_desktop(), selected, available)
```

`activate_profiles` bloquea modelo/esfuerzo ausente y no sustituye otro modelo.
`render_integration` produce TOML con name, description, model,
model_reasoning_effort, sandbox_mode y developer_instructions, así como
declaraciones de roles en configuración de proyecto. Solo genera perfiles
seleccionados. Estas claves y rutas se contrastaron con la
[documentación oficial de agentes](https://learn.chatgpt.com/docs/agent-configuration/subagents)
y la [referencia de configuración](https://learn.chatgpt.com/docs/config-file/config-reference).
Los overrides efectivos de la sesión padre pueden prevalecer sobre el sandbox
del archivo; el protocolo comprueba el permiso observado.

## Preview, apply y recover

Requiere checkout Git cliente, descriptor, política y binding externo ya
seleccionado. Configuración global y rutas gestionadas de usuario son rechazadas.
Los inputs, el target, el plan externo y el estado deben permanecer separados.

```powershell
harness integrate --path C:/Clientes/alpha --policy C:/HarnessConfig/policy.json --binding C:/HarnessConfig/binding.json --catalog C:/HarnessConfig/roles.json --dry-run --plan-out C:/HarnessPlans/desktop.json --json
harness integrate --path C:/Clientes/alpha --policy C:/HarnessConfig/policy.json --apply --plan C:/HarnessPlans/desktop.json --json
harness integrate --path C:/Clientes/alpha --policy C:/HarnessConfig/policy.json --recover --plan C:/HarnessPlans/desktop.json --json
harness integrate --path C:/Clientes/alpha --policy C:/HarnessConfig/policy.json --recover --recover-apply --plan C:/HarnessPlans/desktop.json --json
```

`preview` no edita target ni estado ni autentica. Exportar es una creación
exclusiva en la carpeta externa existente. Cada edición incluye owner,
old_hash, old_identity, new_hash y contenido concreto; backup relativo se
resuelve bajo `<binding.state_dir>/desktop-<run_id>/`. AGENTS y TOML
personalizados conservan su contenido previo. Configuración incompatible,
roles del kit existentes o Skills personalizadas producen conflict; no se
mezclan instrucciones incompatibles automáticamente. Archivos nuevos pueden
crearse; archivos existentes solo se editan con plan explícito.

`apply` revalida inputs, identidad del directorio, identidad/hash de originales,
contenido derivado de recursos íntegros y límites/globs de política. Todos los
originales se abren con handles exclusivos antes de escribir. Backups externos
se crean y se vacían a disco antes de editar; journal separado del onboarding
v1 registra intención y resultado. Padres Windows quedan fijados y no se
siguen junctions, enlaces ni hardlinks. El mismo lock de checkout evita una
operación de onboarding o integración simultánea.

Las ediciones existentes se hacen sobre el mismo handle exclusivo. No es una
transacción atómica del conjunto: un fallo puede dejar integración parcial;
se registra failed. Recuperación comprueba todos los archivos primero y solo
restaura bytes con backup cuyo hash coincide, o retira creaciones propias con
identidad/hash intactos. Cualquier drift, modificación, identidad distinta o
backup alterado conserva archivos y devuelve blocked. Un archivo parcialmente
escrito que no coincide con el estado esperado requiere resolución manual;
no se sobrescribe para forzar recuperación. Se conservan directorios creados
vacíos para no retirar contenedores que otra herramienta pueda compartir.

## Certificados y errores

`assess_certificate(catalog, certificate)` compara observaciones independientes
de role, model-effort, skill:harness-hu, permissions y herramientas por rol
activado. Fuente files/cli nunca cumple un check Desktop. Required ausente,
unsupported o conflict bloquea certificación; not_checked devuelve partial
explícito. Optional ausente no bloquea un rol que no lo requiere. Hooks se
registran por evento observado: este incremento no habilita ninguno.

```powershell
harness desktop-check --catalog C:/HarnessConfig/roles.json --observations C:/HarnessEvidence/certificate.json --json
```

Certificado contiene versión app/motor, referencia de cuenta sanitizada, hash
de catálogo, rol/configuración efectiva, herramientas y referencia de evidencia.
Es una declaración manual evaluada por el kit, no autenticación ni firma de la
app. El operador debe conservar el artefacto observado referido; inventar
`source=desktop` no constituye evidencia. El informe no copia outputs completos
ni credenciales. Inputs que contienen secretos conocidos son rechazados antes
de devolver planes. Los modelos directos se deben validar antes de mostrarlos.

Comandos nuevos conservan schema_version/command/status/checks. Código 0:
comprobación local sin bloqueo, incluido partial con certificado false; 1:
conflicto/bloqueo/fallo de E/S; 2: entrada inválida. Errores principales:
integration_drift, integration_conflict, integration_identity_mismatch,
integration_policy_blocked, integration_plan_invalid, desktop_resources_invalid,
model_unavailable, effort_unavailable, writer_collision, read_only_assignment,
delegation_limit y certificate_catalog_mismatch. No alteran contratos v1.

## Protocolo de aceptación Desktop pendiente

Abrir un checkout sintético en la app objetivo después de revisar/aplicar el
plan. Registrar versión visible de la app, versión efectiva del motor y cuenta
sanitizada. Abrir una sesión nueva y seleccionar realmente cada rol generado;
comprobar modelo/esfuerzo efectivo y descubrimiento de harness-hu. Si no hay
selector de rol disponible, registrar unsupported y no certificar.

Por rol, comprobar lectura de un fixture y git, y permisos sobre una ruta
sintética descartable. Un revisor con escritura efectiva produce conflict,
aunque su TOML declare read-only. Comprobar MCP por propósito y evento de hook
solo si la superficie lo permite; registrar ausencia como unavailable,
unsupported o not_checked. No usar producción ni ejecutar efectos remotos.

E03: pasar únicamente el input del catálogo y el fixture synthetic-sales-v1
al impact-analyzer; guardar su salida. Anotación humana contrasta 5 filas,
suma 40.00 y propuesta de unicidad antes del join. E04: pasar el cambio de
null policy y tres rutas sintéticas; guardar salida y anotar inclusión de job
consumidor/tests de null y ausencia de acceso productivo. Tres repeticiones
por caso; controles de falso positivo/defecto omitido con la rúbrica del 01.
El caso E04 público no es un holdout operativo reservado. Hasta observar y
anotar, resultados permanecen not_run; archivos no satisfacen el protocolo.

La aceptación actual distingue preparación supervisada y certificación estricta.
El cliente sintético ya aportó ejecuciones de roles y un conflicto de sandbox;
las llamadas originales y anotación humana están en
[desktop-runtime-2026-10-09](evidence/desktop-runtime-2026-10-09/verification.md).
Auditor/verifier pudieron escribir; la restricción read-only no está certificada.
E04 mantiene el defecto aceptado de pruebas de null omitidas en dos repeticiones.

Uso y límites de los nuevos contratos/comandos de preparación y comparación:
[revisión supervisada](supervised-review.md). Nunca transformar prepared en
certified ni habilitar fases con capacidad requerida fallida.
