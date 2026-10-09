# Contratos de configuración, versión 1

Separar tres documentos evita incorporar rutas personales y permisos al repositorio
portable. El preview valida o propone; apply crea únicamente los ausentes del plan revisado.

| Documento | Ubicación/selección | Responsabilidad |
| --- | --- | --- |
| Descriptor | `.harness/client.yaml` en el checkout | Identidad, repo, rama base, raíz OpenSpec |
| Política | `--policy FILE` explícito | Límites operativos propuestos por el operador |
| Binding | `--binding FILE` explícito | Relación entre cliente, checkout, política y estado externo |

Los ejemplos ejecutables de datos sintéticos viven en `tests/fixtures/alpha` y
`tests/fixtures/beta`. Sus rutas Windows son ilustrativas y no crean targets.

## Descriptor

```yaml
schema_version: 1
client_id: alpha
repository: demo/alpha
base_branch: develop
openspec_root: openspec
```

No admite permisos, selectores de política ni secretos. IDs ASCII de 1–64 caracteres;
repo GitHub `owner/name`; rama válida con reglas Git locales; raíz relativa sin
traversal ni segmentos vacíos. Default de raíz: `openspec`.

## Política

```yaml
schema_version: 1
policy_id: pilot
client_id: alpha
repository: demo/alpha
base_branch: develop
branch_prefix: feature/
read_only_paths: [.harness/]
denied_paths: [private/]
max_files: 40
max_bytes: 2000000
```

Las listas son rutas/patrones relativos; no permiten `/`, discos absolutos,
backslash, `..` ni segmentos vacíos. Los límites son enteros estrictos positivos.
Estos campos se aplican a las creaciones del onboarding. No impiden que Codex
edite directamente; las instrucciones AGENTS tampoco conceden permisos.

## Binding

```text
schema_version: 1
client_id: alpha
checkout_id: checkout
target_path: C:/Clientes/alpha
policy_sha256: SHA256 de los bytes exactos de la política (64 hex minúsculas)
state_dir: C:/HarnessState/alpha/checkout
databricks_profile: ALPHA_DEV   # opcional, solo referencia
```

El bloque explica campos; el fixture JSON contiene un hash real válido. Para
calcularlo: `(Get-FileHash C:/HarnessConfig/alpha-policy.json -Algorithm SHA256).Hash.ToLower()`.
Si cambia cualquier byte de política, incluso whitespace, actualizar el binding
solo después de revisar esa política.

Paths absolutos; target debe coincidir con el checkout seleccionado; estado debe
quedar fuera del target y terminar en `client_id/checkout_id`. Se inspeccionan
ancestros existentes, rechazando symlinks y junctions antes de normalizar. No
crear carpetas para validar. Tampoco se aceptan rutas de selección con `..`.

## Confianza y errores

Coincidir cliente en los tres documentos; repo/rama entre descriptor y política;
origen Git local contra repo. HTTPS, `git@github.com:owner/repo.git` y
`ssh://git@github.com/owner/repo` representan la misma identidad; se compara sin
red. Rechazar otros hosts/transportes, credenciales inline y origin ausente.

Un hash verifica integridad de archivos seleccionados; quien controla ambos
archivos puede cambiarlos. La política requiere selección confiable del operador.
El repo nunca puede activar una política añadiendo campos al descriptor.

Leer objetos YAML/JSON UTF-8 (BOM admitido), máximo 128 KiB por documento, solo
archivos regulares. Rechazar claves duplicadas, alias YAML, campos desconocidos,
versiones distintas de entero `1` y secretos reconocibles. No es un detector
universal de secretos. Los errores indican código, contrato y campos afectados
cuando hay validación de esquema, sin valores completos, stderr ni traceback.

Schemas: `schemas/descriptor.schema.json`, `policy.schema.json`,
`binding.schema.json`, `onboardingplan.schema.json`, `journal.schema.json` y
`lockowner.schema.json`. Se generan desde los modelos; restricciones relacionales,
filesystem y reglas Git requieren el validador Python, además del JSON Schema.

Las pruebas verifican fixtures y correspondencia schemas/modelos. Para regenerar:

```powershell
.venv/Scripts/python.exe scripts/generate_schemas.py
```
