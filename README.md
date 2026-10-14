# Crea Harness Codex (Local-Harness)

Kit genérico para desarrollar sobre repositorios de clientes desde Codex Desktop.
El kit entrega contratos, diagnóstico local, preview, aplicación explícita de
onboarding y recuperación conservadora. Codex mantiene la conversación y las herramientas; este
paquete no invoca modelos ni sustituye su motor.

El incremento 02 añade [integración revisable de roles Desktop](docs/desktop-integration.md)
con preview/apply/recover propios y comprobación conservadora de observaciones.
La preparación supervisada de 02 está verificada con límites aceptados; la
certificación estricta sigue pendiente. El incremento 03 añade
[onboarding guiado por plantilla o entrevista](docs/guided-client-onboarding.md),
preview compuesto y aplicación/recuperación explícita por etapa.

## Instalación de desarrollo (Windows)

Requiere Python 3.13. Git, Node, OpenSpec y Databricks CLI se preparan por separado;
la instalación Python no los descarga. Ejecutar desde este repositorio:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[dev]'
.venv/Scripts/harness.exe --version
.venv/Scripts/python.exe -m harness_local --help
.venv/Scripts/harness.exe doctor --path . --json
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m build --wheel --no-isolation
```

En este proyecto `doctor --path .` puede devolver `partial`: no es un repositorio
cliente vinculado y las capacidades Desktop/autenticación remota no se comprueban.
Los recursos genéricos (matriz, AGENTS, kit OpenSpec y schemas) se incluyen en el wheel.

## Uso sobre un cliente

Abrir en Codex la carpeta del checkout cliente. El producto, sus especificaciones
y su venv permanecen aquí. El cliente conserva su código, OpenSpec y un descriptor
portable; la política y el binding son entradas explícitas del operador.

```powershell
.venv/Scripts/harness.exe doctor --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --json
.venv/Scripts/harness.exe init --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --dry-run --json
```

Las rutas son ejemplos; deben apuntar a archivos validados. Si falta el descriptor,
agregar `--repo demo/alpha --base-branch develop`. El preview no crea archivos,
salvo el plan externo solicitado con `--plan-out`. `init` sin `--dry-run` ni
`--apply` devuelve `apply_not_supported`, código 2.

Para un binding nuevo y una preparación explícita:

```powershell
harness init --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding-out C:/HarnessConfig/alpha-binding.json --checkout-id checkout --state-dir C:/HarnessState/alpha/checkout --dry-run --plan-out C:/HarnessPlans/alpha.json --json
# Revisar contenido, destinos, hashes y applicable antes de aplicar:
harness init --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --apply --plan C:/HarnessPlans/alpha.json --json
# RUN es el run_id devuelto por apply:
harness recover --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --plan C:/HarnessPlans/alpha.json --run RUN --dry-run --json
harness recover --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --plan C:/HarnessPlans/alpha.json --run RUN --apply --json
```

Las carpetas del plan y binding deben existir. La política debe autorizar las
creaciones: un descriptor ausente bajo `.harness/` protegido bloquea el plan.
`applicable` indica preparación local permitida; no certifica Desktop ni autenticación.

## Alcance

- `harness_core`: contratos, lectura segura, integridad y separación de clientes.
- `harness_local`: sondas, planes, aplicación Windows, journal y recuperación.
- `schemas`: JSON Schema generado desde los contratos Pydantic.
- `tests`: clientes sintéticos y comprobaciones de comportamiento sin conexión remota.

Los límites de la política se comprueban en comandos/adaptadores del kit. El
[flujo de HU](docs/hu-lifecycle.md) registra estado SQLite, planes, aprobación,
candidatos, evidencia y recuperación por cliente/checkout. No hay plugin certificado ni hooks operativos. El incremento 08 añade un
[launcher candidato y update/recover](docs/pilot-and-distribution.md). El incremento 05 añade [validación de candidatos](docs/candidate-validation.md),
workers seleccionados y adaptadores Databricks con autorización explícita; sin
sandbox/runtime requerido conserva blocked. Las plantillas de
roles y su configuración local revisada están disponibles; el kit no ejecuta agentes.
Tampoco se altera
la configuración global de Codex. El hash de política comprueba integridad,
no una firma ni autorización externa.

Ver [configuración](docs/configuracion-clientes.md),
[operación](docs/operacion-local.md),
[aplicación y recuperación](docs/onboarding-aplicacion.md),
[arquitectura](docs/propuesta-harness-local-codex.md) y
[evidencia](docs/evidence/bootstrap-codex-local-core.md).

La base versión 0.1.0 mantiene sus specs en `openspec/specs/`. El primer cambio
está cerrado en
`openspec/changes/archive/2026-10-09-bootstrap-codex-local-core/`.

El onboarding aplicado también está cerrado en
`openspec/changes/archive/2026-10-09-apply-client-onboarding/`.
El [roadmap de ocho incrementos](docs/planning/roadmap.md) propone onboarding
guiado, roles/herramientas Desktop, flujo de HU, validación Databricks,
observabilidad/evals, historias/PR y distribución. 01–03 entregan calidad, roles
supervisados y onboarding preparado; 04 añade HU/gates locales, 05 validación y
evidencia con smoke remoto blocked; 06 y 07 entregan infraestructura local,
con evaluaciones y publicación reales pendientes; 08 entrega implementación local
y distribución candidata, con aceptación y release bloqueados.
Los [casos de calidad](docs/planning/quality/README.md)
conservan definiciones not_run; su carga e integridad se verifican en 01. Las Skills oficiales descargadas se
conservan como [snapshot de referencia](resources/vendor/README.md).

El cambio `01-quality-practices-and-eval-foundation` entrega la [API de calidad](docs/quality-foundation.md), schemas, composición por cliente y recursos verificados dentro del wheel. Los casos de agente pendientes conservan `not_run`; 05 incorpora validación/evidencia, 06 observabilidad/evals y 07 historias/PR locales. Ver [evidencia](docs/evidence/quality-foundation.md).

## Observabilidad y evaluación manual

`harness usage report --input observaciones.json --json` reporta actividad
recibida por cliente/HU/intento y uso desconocido en `null` con motivo.
`harness eval validate`, `harness eval run` y `harness eval report`, con
`--input batch.json --json`, validan/importan
recibos manuales y calcula el gate de promoción. La automatización Desktop
sin interfaz certificada devuelve `blocked`.

Ver [contratos y protocolo](docs/observability-and-evals.md) y
[evidencia del incremento 06](docs/evidence/observability-evals-verification.md).
Las 126 evaluaciones Luna/medium están pendientes; el runner no las inventa.

## Historias y PR

`harness story read` congela una HU de fixture o GitHub seleccionado;
`harness story bind` fija el vínculo técnicamente aprobado entre historia y plan.
`harness pr preview` prepara título/cuerpo/candidato/evidencia sin autenticar
ni escribir. `harness pr publish` y `reconcile` exigen autorización explícita,
gates actuales, identidad y evaluaciones reales; no duplican un PR ni
reemplazan ramas ajenas. El flujo completo se prueba con dobles declarados.

Ver [contratos y comandos](docs/story-pr-integrations.md) y
[evidencia de 07](docs/evidence/story-pr-verification.md). Las 144 evaluaciones
Luna/medium y el smoke de escritura real permanecen pendientes; el archivo
autorizado con advertencias conserva publicación y aceptación de 08 bloqueadas.

## Piloto y distribución candidata

`harness bootstrap --json` muestra herramientas y preparación/login/confianza
pendientes. `harness release candidate --json` describe recursos, dependencias y
hashes; `harness update preview/apply/recover` opera solo sobre ownership revisado
y conserva personalizaciones, backups y estado. `harness release gate` exige
evidencia real ligada al candidato; no publica el producto.

08 permanece activo con ocho de trece tareas completas y cinco de aceptación
abiertas. Ver [guía](docs/pilot-and-distribution.md) y
[verificación](docs/evidence/distribution-verification.md). El wheel candidato y
el push de código no cierran las 144 evaluaciones de 06/07 ni certifican Desktop.
