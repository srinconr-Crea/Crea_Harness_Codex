# Crea Harness Codex (Local-Harness)

Kit genérico para desarrollar sobre repositorios de clientes desde Codex Desktop.
El primer incremento entrega contratos de configuración, diagnóstico local y
preview de onboarding. Codex mantiene la conversación y las herramientas; este
paquete no invoca modelos ni sustituye su motor.

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
Los recursos genéricos (matriz y plantilla AGENTS) se incluyen en el wheel.

## Uso sobre un cliente

Abrir en Codex la carpeta del checkout cliente. El producto, sus especificaciones
y su venv permanecen aquí. El cliente conserva su código, OpenSpec y un descriptor
portable; la política y el binding son entradas explícitas del operador.

```powershell
.venv/Scripts/harness.exe doctor --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --json
.venv/Scripts/harness.exe init --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --dry-run --json
```

Las rutas son ejemplos; deben apuntar a archivos validados. Si falta el descriptor,
agregar `--repo demo/alpha --base-branch develop`. El preview no crea archivos.
`init` sin `--dry-run` devuelve `apply_not_supported`, código 2.

## Alcance

- `harness_core`: contratos, lectura segura, integridad y separación de clientes.
- `harness_local`: sondas de versión, inspección Git/OpenSpec y planes deterministas.
- `schemas`: JSON Schema generado desde los contratos Pydantic.
- `tests`: clientes sintéticos y comprobaciones de comportamiento sin conexión remota.

Los límites de la política todavía no son controles de edición de Codex. No hay
SQLite, instalador/plugin, registro persistente de HUs, agentes personalizados,
hooks operativos ni ejecución Databricks en este incremento. Tampoco se altera
la configuración global de Codex. El hash de política comprueba integridad,
no una firma ni autorización externa.

Ver [configuración](docs/configuracion-clientes.md),
[operación](docs/operacion-local.md),
[arquitectura](docs/propuesta-harness-local-codex.md) y
[evidencia](docs/evidence/bootstrap-codex-local-core.md).

La base versión 0.1.0 mantiene sus specs en `openspec/specs/`. El primer cambio
está cerrado en
`openspec/changes/archive/2026-10-09-bootstrap-codex-local-core/`.
