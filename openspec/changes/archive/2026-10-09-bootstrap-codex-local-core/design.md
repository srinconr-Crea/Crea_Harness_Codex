# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para el comportamiento requerido. El workspace tiene Git sin commits/remoto, la propuesta arquitectónica y OpenSpec 1.13.2 con siete Skills; aún no tiene paquete Python ni CLI del producto.

La arquitectura general describe incrementos posteriores de HU, gates, agentes y persistencia. Este cambio limita esa dirección a contratos y diagnóstico/preview local. La estructura conocida de NaturaPet orienta la compatibilidad de onboarding; las pruebas iniciales usan fixtures sintéticos sin copiar el cliente.

## Goals / Non-Goals

**Goals:**
- Producir un paquete instalable en un entorno de desarrollo aislado con entry point `harness`.
- Separar contratos puros de comandos y sondas del sistema.
- Entregar errores y planes revisables sin cambios en targets o configuración global.
- Establecer interfaces reutilizables por un futuro instalador, sin implementarlo ahora.

**Non-Goals:**
- Certificar capacidades de Desktop a partir de un binario CLI o archivos TOML.
- Ejecutar modelos, pruebas del cliente o recursos remotos.
- Implementar autorización de HUs, editor mediado, SQLite, publicación, instalador/plugin o activación de agentes/hooks.
- Generar o sincronizar specs en `openspec/specs/` antes del cierre de este cambio.

## Decisions

### 1. Paquete con dos responsabilidades

Usar Python 3.13 y packaging estándar con `pyproject.toml`. El núcleo valida datos sin importar módulos de comandos; el adaptador local puede importar el núcleo. `argparse` evita agregar una dependencia solo para CLI. Pydantic 2 aporta validación estricta y generación de JSON Schema; PyYAML aporta carga segura de YAML. pytest cubre los contratos observables.

Archivos previstos durante apply:

```text
pyproject.toml
README.md
.gitignore
src/harness_core/
  __init__.py
  contracts.py            # Descriptor, política, binding y reportes
  configuration.py        # Lectura acotada, integridad y validación cruzada
  paths.py                # Normalización/traversal/enlaces
src/harness_local/
  __init__.py
  __main__.py
  cli.py                  # Parsing, representación y códigos de salida
  probes.py               # Sondas de herramientas y Git
  doctor.py
  onboarding.py           # Construcción del plan sin aplicación
  compatibility.json      # Matriz del incremento
  templates/AGENTS.md      # Instrucciones genéricas propuestas, sin negocio
schemas/
  client-descriptor-v1.schema.json
  operator-policy-v1.schema.json
  developer-binding-v1.schema.json
tests/
  fixtures/               # Dos clientes sintéticos
  test_configuration.py
  test_doctor.py
  test_onboarding.py
  test_cli.py
docs/
  configuracion-clientes.md
  operacion-local.md
```

Son archivos propuestos, no generados en la fase propose. Los schemas se generan desde los mismos modelos y una prueba detecta divergencia; no mantener dos validadores independientes. Los recursos necesarios se incluyen en el wheel.

Detalle de implementación del primer incremento: las rutas y lectura segura están
consolidadas en `configuration.py`; sondas y doctor en `diagnostics.py`. Los tests
de doctor/onboarding/CLI están agrupados en `test_local.py`. Los schemas generados
se llaman `descriptor.schema.json`, `policy.schema.json`, `binding.schema.json`.
Esta agrupación evita módulos puente sin lógica en el paquete pequeño, conservando
la separación `harness_core`/`harness_local` y todos los contratos de comportamiento.
`scripts/generate_schemas.py` y `scripts/smoke_wheel.py` reproducen la evidencia.

Alternativa considerada: copiar el harness Databricks entero. Se descarta para este incremento porque arrastra autenticación, proveedores LLM y contratos de llamadas/costos no necesarios para doctor/preview.

### 2. Tres contratos sin activación implícita

Todos rechazan campos extra y secretos, con nombres de identidad acotados y versiones explícitas.

| Contrato | Campos versión 1 |
| --- | --- |
| Descriptor del repo | `schema_version`, `client_id`, `repository`, `base_branch`, `openspec_root` |
| Política explícita | `schema_version`, `policy_id`, `client_id`, `repository`, `base_branch`, `branch_prefix`, `read_only_paths`, `denied_paths`, `max_files`, `max_bytes` |
| Binding del desarrollador | `schema_version`, `client_id`, `checkout_id`, `target_path`, `policy_sha256`, `state_dir`, `databricks_profile` opcional |

El descriptor vive en `.harness/client.yaml`. Política y binding se pasan mediante flags y pueden estar fuera del target. La política define límites futuros pero este incremento no ejecuta cambios del cliente ni declara esos límites efectivos en Codex. El binding no contiene tokens ni job IDs; el perfil Databricks es únicamente una referencia local no comprobada remotamente.

Reglas: `client_id`, `policy_id` y `checkout_id` usan identificadores ASCII de 1–64 caracteres; `repository` es `owner/name` de GitHub; ramas/prefijos se validan con reglas Git locales. `openspec_root` y patrones de rutas son relativos, sin `..`, rutas absolutas ni segmentos vacíos. Límites son enteros positivos. `policy_sha256` contiene 64 caracteres hexadecimales minúsculos y se calcula sobre bytes originales.

`target_path` y `state_dir` son absolutos. `state_dir` debe terminar en `<client_id>/<checkout_id>` y quedar fuera del target. Para rutas existentes se rechazan componentes symlink/junction antes de normalizar; para rutas propuestas se comprueban ancestros existentes y sintaxis. No crear directorios para validar.

Comparar el remote origin local aceptando `https://github.com/owner/repo[.git]`, `ssh://git@github.com/owner/repo[.git]` y `git@github.com:owner/repo[.git]`. Normalizar sufijo `.git` y casing para comparación de identidad GitHub. Rechazar transportes/hosts no soportados y credenciales inline sin mostrarlas. Git worktrees válidos se admiten, aunque `.git` sea un archivo; no exigir una carpeta `.git`.

Leer como máximo 128 KiB por documento, UTF-8 con BOM permitido y YAML seguro/JSON objeto. Rechazar claves duplicadas, campos de credenciales y patrones reconocibles de secretos. Esto reduce filtraciones accidentales; no garantiza detectar cualquier secreto arbitrario.

Alternativa considerada: un `client.yaml` con todo. Se descarta porque confunde identidad portable, autorización y credenciales/rutas personales. Un hash verifica integridad; la selección de política no certifica que el usuario del equipo no pueda cambiar sus archivos.

### 3. CLI y reportes

Superficies de este incremento:

```text
harness --version
harness doctor [--path TARGET] [--policy FILE --binding FILE] [--json]
harness init --path TARGET --policy FILE --binding FILE --dry-run
             [--repo OWNER/NAME --base-branch BRANCH] [--json]
```

`--policy` y `--binding` deben aparecer juntos en doctor. En init son obligatorios. Si falta el descriptor, `--repo` y `--base-branch` son obligatorios; si existe, flags redundantes deben coincidir o rechazarse. No hay `harness update` ni modo apply en esta versión.

Reporte común: `schema_version: 1`, `command`, `status`, `checks`. Cada check contiene `id`, `status`, `code`, `message`, `observed_version` cuando exista y `remediation` cuando corresponda. El JSON usa stdout; no mezclarlo con progreso. Excepciones previstas se traducen a errores sanitizados; no mostrar YAML completo, stderr crudo o traceback con entradas sensibles.

Códigos: 0 sin fallos comprobados, 1 diagnóstico/preparación incompletos o conflictos, 2 uso/configuración inválidos. `not_checked` no produce un fallo por sí solo, pero el resultado se describe como `partial` y nunca como certificación completa. `status` global usa `ready`, `partial`, `blocked` o `invalid`.

### 4. Diagnóstico offline y acotado

Resolver binarios por PATH, registrar disponibilidad y ejecutar únicamente sondas de versión con argumentos fijos, sin shell y con timeout de 10 segundos por sonda. Para OpenSpec en Windows resolver la entrada Node o un lanzador nativo seguro sin interpolar texto arbitrario. Todas las sondas tienen límite de salida de 64 KiB. Procesos que escriban directorios de caché/telemetría deben recibir configuración para evitarlos o quedar `not_checked`; doctor no los ejecuta si no puede preservar esa garantía.

Matriz inicial: Python `>=3.13,<3.14`, Node `>=20.19`, Git `>=2`, OpenSpec `==1.13.2`, Databricks CLI `>=0.292`. El mínimo Databricks es preparación de herramientas, no certificación de cualquier release futura; el reporte distingue rango aceptado de versiones concretamente probadas. Node/Git/CLI no se instalan mediante dependencias Python.

Con target, usar Git con `GIT_OPTIONAL_LOCKS=0` para identificar raíz, origin, rama y estado, sin ejecutar hooks o comandos remotos. No cargar imports, ejecutar tests ni recorrer datos del cliente. Leer solo configuración e instrucciones necesarias, de forma acotada.

Comprobar presencia de OpenSpec y siete Skills con `name` y `metadata.generatedBy` compatibles. Los archivos Codex solo permiten informar presencia. La selección de modelos, agentes y hooks en Desktop continúa como `not_checked`.

### 5. Plan de onboarding inmutable

Después de validar entradas, construir una lista ordenada de acciones con `kind`, `status`, `path` opcional, `reason` y `content`/`sha256` cuando el kit posee plantilla o contenido determinista. Registrar hashes del descriptor, política, binding y archivos existentes comparados; no generar run IDs, fechas o estado persistente.

Acciones del preview: descriptor faltante, AGENTS genérico faltante, detección/preservación de OpenSpec y sus Skills, preparación manual de workflows ausentes, revisión de configuración Codex existente y futuras autenticaciones/confianza. No proponer crear agentes/hooks operativos ni archivos TOML ficticios en este incremento.

Un AGENTS existente distinto de la plantilla se informa como conflicto de integración manual. OpenSpec/Skills compatibles se preservan; incompatibles se informan como conflicto. Si faltan, mostrar la operación manual de preparación y comprobar que verify esté incluido: no fingir que el kit ya generó esas Skills o que OpenSpec está instalado cuando falta.

Herramientas faltantes o conflictos producen plan `blocked` y exit 1; entradas inválidas producen exit 2 sin un plan válido. El formato humano representa el mismo plan JSON. Dry-run repetido con las mismas entradas conserva el plan semántico.

### 6. Pruebas y evidencia

Fixtures: dos repos Git locales creados en directorios temporales de test con remotes sintéticos; un cliente preparado con OpenSpec/Skills y otro sin preparación. No clonar ni acceder a NaturaPet o GitHub durante tests.

Verificar contratos inválidos, hashes divergentes, origen SSH/HTTPS, worktrees, traversal, junctions/symlinks Windows, secretos sanitizados, timeout/versiones, CLI JSON/códigos, conflictos y repetición del preview. Las sondas se inyectan/simulan para pruebas deterministas.

Prueba de efectos: snapshots de bytes/listado del target, política, binding y estado antes/después; un ejecutor instrumentado rechaza cualquier intento de red, instalación o escritura. Un smoke test del paquete instalado comprueba entry point y recursos incluidos. Las pruebas certifican esta CLI, no el motor Desktop.

## Risks / Trade-offs

- Archivos locales manipulables por el usuario → no prometer enforcement de plataforma; mantener confianza externa para incrementos posteriores.
- Sondas de terceros con efectos secundarios → ejecutar solo modos comprobados y acotados; reportar `not_checked` si no hay vía segura.
- Configuración específica de cliente filtrada al producto → usar datos sintéticos y schemas genéricos, sin perfiles reales en fixtures.
- Duplicación schemas/modelos → generar schemas del modelo y comprobar igualdad en tests.
- Reporte parcial interpretado como preparación completa → estado `partial` y capacidades Desktop/remotas explícitamente pendientes.
- Un `openspec update` posterior con perfil global core puede cambiar los workflows → documentar la selección de los siete workflows; no alterar globalmente otros proyectos en este cambio.

## Migration Plan

No hay usuarios ni estado anterior que migrar. Durante apply se agregará el paquete y se probará su instalación en un venv de desarrollo. El preview no prepara targets realmente; una futura fase de aplicación tendrá su propio cambio OpenSpec.

Rollback del paquete de desarrollo: retirar su instalación del venv y volver a la revisión anterior, sin cambios en clientes ni estado que revertir. La inicialización OpenSpec ya autorizada permanece como infraestructura de planificación del producto.
