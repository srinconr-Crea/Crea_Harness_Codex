# Operación del primer incremento

## Diagnóstico

```powershell
harness doctor --json
harness doctor --path C:/Clientes/alpha
harness doctor --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --json
```

Ejecutar con el venv activado o usar `.venv/Scripts/harness.exe` desde el producto.
`--policy` y `--binding` aparecen juntos; requieren `--path`. Sin ellos la
validación operativa queda `not_checked`.

Sondas locales de Python, Git, Node, OpenSpec y Databricks: argumentos separados,
sin shell, máximo 10 segundos y 64 KiB combinados de stdout/stderr por proceso.
Windows usa la entrada Node de OpenSpec en lugar de ejecutar su shim CMD/PowerShell.
Un launcher no verificado queda pendiente. No se instalan herramientas ni se
solicitan login. Telemetría OpenSpec desactivada para la sonda.

| Herramienta | Rango aceptado | Versión probada aquí |
| --- | --- | --- |
| Python | >=3.13, <3.14 | 3.13.14 |
| Git | >=2 | 2.53.0.windows.3 |
| Node | >=20.19 | 24.15.0 |
| OpenSpec | ==1.13.2 | 1.13.2 |
| Databricks CLI | >=0.292 | 1.18.0 |

Aceptar un rango no certifica releases futuras ni capacidades Desktop. La matriz
versionada está en el paquete. Sondas asumen binarios instalados confiables;
el kit no verifica su supply chain ni neutraliza un ejecutable malicioso.

Con target: comprobar raíz Git (incluye worktrees), origin local para validación,
rama/HEAD separado, estado y configuración OpenSpec. Git usa locks opcionales
deshabilitados, sin fsmonitor ni clean/process filters del cliente. Un nombre
de filtro no admisible deja el estado pendiente. No se importan módulos ni se
ejecutan tests del cliente. OpenSpec requiere `schema: spec-driven` y siete Skills
con `name` correspondiente y `metadata.generatedBy: "1.13.2"`.

Los siete workflows son explore, propose, update-change, apply-change,
verify-change, sync-specs y archive-change. El perfil global core no basta para
este conjunto: su preparación debe seleccionar los siete workflows en un cambio
revisado; `doctor` solo indica faltantes/incompatibles. No ejecutar `openspec update`
indiscriminadamente sobre todos los clientes.

## Preview

```powershell
harness init --path C:/Clientes/alpha --policy C:/HarnessConfig/alpha-policy.json --binding C:/HarnessConfig/alpha-binding.json --dry-run --json
# Solo si falta el descriptor:
harness init --path C:/Clientes/beta --policy C:/HarnessConfig/beta-policy.json --binding C:/HarnessConfig/beta-binding.json --repo demo/beta --base-branch develop --dry-run
```

El target debe existir y ser raíz de checkout. No se clona. Descriptor ausente
requiere datos explícitos; los flags redundantes de un descriptor presente deben
coincidir. El plan lleva identidad, hashes de entradas, comprobaciones y acciones
ordenadas, sin fechas ni identificadores aleatorios:

- `proposed`: descriptor o AGENTS que puede revisarse como contenido y SHA-256.
- `existing`: conservar el archivo compatible.
- `conflict`: integrar manualmente AGENTS distinto o artefacto incompatible.
- `manual`: preparar workflows ausentes, revisar Codex y autenticación futura.

No aplicar ninguna acción; no escribir target/estado/configuración global. El
estado externo declarado se valida, no se crea. No hay SQLite todavía. La carpeta
`openspec/` del producto guarda este desarrollo; cada cliente mantiene sus propias
specs e instrucciones. No copiar conocimiento de un cliente a las plantillas.

## Resultados

JSON por stdout: `schema_version`, `command`, `status`, `checks`; preview agrega
`identities`, `input_hashes`, `actions`. La salida humana representa esos mismos
datos, incluidas versiones, remedios y hashes. Mensajes sanitizados.

| Código | Significado |
| --- | --- |
| 0 | Sin fallos comprobados; puede haber capacidades pendientes |
| 1 | Herramienta ausente/incompatible, diagnóstico incompleto o conflicto |
| 2 | Uso o configuración inválidos; incluye init sin dry-run |

Estado global `ready`, `partial`, `blocked` o `invalid`. `not_checked` produce
`partial` cuando no hay fallos, sin transformar lo pendiente en éxito.
Autenticación/acceso Databricks y descubrimiento Skills/modelos/agentes/hooks
en Desktop requieren pruebas futuras; archivos TOML presentes no bastan.

## Próximos cambios

Onboarding aplicable, instalador/plugin, gates de HU, validaciones remotas y
persistencia requieren sus propias propuestas OpenSpec. Este cambio no implementa
`harness update`, despliegue, agentes ni modificaciones del TOML global.
