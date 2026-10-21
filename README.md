# Crea Harness Codex MVP — kit manual 0.1.3

Kit de configuración para trabajar con Codex sobre repositorios de proyectos y clientes,
con contexto explícito, roles especializados y un flujo de desarrollo guiado por OpenSpec.
Está orientado a proyectos de datos y aplicaciones en Databricks, con entrega por GitHub
o Azure DevOps / Azure Repos.

La entrega principal de la rama `Crea_Harness_Codex_MVP` es **`crea-manual-kit` 0.1.3**:
archivos que se revisan, copian y adaptan a la raíz del repositorio destino.
El kit usa las capacidades de la sesión de Codex y las herramientas del equipo;
no requiere instalar el paquete Python `harness_local`.

## Descargar y empezar

- [Descargar ZIP 0.1.3](artifacts/crea-manual-kit-0.1.3.zip?raw=true).
- [SHA-256 del ZIP](artifacts/crea-manual-kit-0.1.3.zip.sha256).
- [Explorar el kit](artifacts/crea-manual-kit-0.1.3/).
- [Guía completa de configuración manual](artifacts/crea-manual-kit-0.1.3/docs/configuracion-manual.md).

1. Descarga el ZIP y su archivo `.sha256`. Compara el hash antes de extraer.
2. Extrae en una carpeta de preparación y verifica la distribución original.
3. Prepara las herramientas y autentica el proveedor Git siguiendo la guía.
4. Clona o crea el repositorio destino y copia el contenido del kit, incluidas
   `.agents` y `.codex`. En proyectos existentes, combina las instrucciones y
   configuraciones después de revisar diferencias.
5. Abre el repositorio destino en Codex, inicializa OpenSpec y completa el contexto
   y el inventario del proyecto.
6. Comprueba la configuración, versiona el setup como cambio separado e inicia
   una primera historia de usuario pequeña.

La guía está escrita para **Windows y PowerShell**. Requiere una sesión de Codex
con acceso al proyecto, Git, Node.js y OpenSpec. Las herramientas de Databricks y
del proveedor Git se preparan según el proyecto; el ZIP no incluye esos ejecutables.

## Qué contiene

| Recurso dentro del kit | Propósito |
| --- | --- |
| `AGENTS.md` | Instrucciones de inicio, responsabilidades y reglas del proyecto. |
| `.codex/config.toml` | Modelo principal y configuración de delegación. |
| `.codex/agents/` | Perfiles planner, developer y reviewer. |
| `.agents/skills/Crea/` | Orquestador y skill propia para agentes Databricks. |
| `.agents/skills/Project/` | Espacio para skills específicas del proyecto. |
| Otras carpetas de `.agents/skills/` | Quince skills Databricks y siete skills OpenSpec con sus recursos. |
| `docs/contexto-proyecto.md` | Plantilla para objetivos, negocio, arquitectura y restricciones. |
| `docs/proyecto.json` y su schema | Inventario, rutas, proveedor Git, validaciones y contrato de entrega. |
| `docs/buenas-practicas/` | Prácticas por herramienta para orientar implementación y revisión. |
| `docs/plantillas/` | Evidencia, handoff y borrador de PR. |
| `scripts/crea/verificar-kit.ps1` | Comprobación de estructura e integridad de la distribución. |
| `kit-manifest.json` | Inventario de archivos originales con tamaños y hashes SHA-256. |

Los perfiles incluidos usan `gpt-6.1-sol` con esfuerzo `medium`; son configurables.
Su disponibilidad y descubrimiento deben comprobarse en la app y cuenta de destino.

## Cómo se trabaja

El principal coordina el trabajo con `crea-orquestador`. Los roles se ejecutan
**en secuencia, con un agente activo por vez**:

1. **Planner:** explora cuando hace falta y prepara o actualiza la propuesta,
   especificaciones y tareas de OpenSpec.
2. **Persona:** revisa los artefactos y solicita expresamente la implementación.
3. **Developer:** aplica el cambio y ejecuta las pruebas pertinentes.
4. **Reviewer:** revisa el resultado, valida contra las especificaciones y sincroniza
   cuando corresponde. Presenta evidencia y solicita aprobación para archivar.
5. **Principal:** tras la aprobación que incluya publicación, realiza commit y push
   en la rama de la HU y entrega el PR según el proveedor.

La rama de trabajo se prepara antes de modificar el proyecto. El flujo conserva
las pausas humanas de OpenSpec y la aprobación de archivo/publicación. Las rutas
y responsabilidades declaradas orientan a los agentes; no crean aislamiento técnico.

## Adaptar al proyecto

Completa primero estos archivos del **repositorio destino**:

- `docs/contexto-proyecto.md`: propósito, negocio, stack, fuentes, entornos y restricciones.
- `docs/proyecto.json`: proveedor y URL del repositorio, rama base real, rutas existentes,
  perfil Databricks elegido, comprobaciones aplicables y entrega. Marca `setup_complete`
  al terminar la preparación.
- `AGENTS.md`: convenciones e instrucciones que deben convivir con las del cliente.
- `.codex/config.toml` y `.codex/agents/*.toml`: modelos e instrucciones por rol.
- `openspec/config.yaml`: contexto y reglas del proyecto, una vez inicializado OpenSpec.

El ZIP incluye las skills de OpenSpec, pero **no trae un directorio `openspec/`
preinicializado**. Sigue la guía para crearlo en el repositorio correcto y comprobar
los workflows disponibles. Conserva las licencias y las skills upstream; agrega
extensiones propias en `Crea/` o `Project/`.

## Verificar el kit

Desde la carpeta donde descargaste el ZIP:

```powershell
Get-FileHash -LiteralPath .\crea-manual-kit-0.1.3.zip -Algorithm SHA256
Get-Content -LiteralPath .\crea-manual-kit-0.1.3.zip.sha256
```

Compara ambos hashes. Después de extraer, ejecuta desde la raíz del kit:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\crea\verificar-kit.ps1 -OriginalDistribution
```

`Bypass` se aplica al proceso invocado; las directivas corporativas siguen vigentes.
Tras personalizar el kit, omite `-OriginalDistribution` para comprobar la estructura
sin exigir los bytes originales. El verificador no ejecuta pruebas de negocio,
no autentica servicios y no acredita la ejecución de agentes en Codex.

## Entrega por proveedor

| Proveedor | Entrega prevista por el kit |
| --- | --- |
| GitHub | Commit y push en la rama de la HU; enlace al formulario web y borrador para crear el PR manualmente. |
| Azure DevOps Services | Git/Git Credential Manager para operaciones Git; Azure CLI con `azure-devops` para crear y verificar el PR tras aprobación expresa. |
| Azure DevOps Server | Operaciones Git y formulario web como alternativa; la integración CLI del kit está orientada a Services. |

El alcance termina en la entrega para revisión. No incluye merge, auto-complete,
borrado automático de ramas, despliegues, Boards ni pipelines.
Consulta el [procedimiento de entrega](artifacts/crea-manual-kit-0.1.3/docs/entrega-git.md).

## Estado del MVP y estructura de esta rama

La versión 0.1.3 incorpora la preparación y entrega por Azure CLI para Azure DevOps
Services. El kit cuenta con comprobaciones locales de estructura, configuración e
integridad. La autenticación, los permisos, el descubrimiento de agentes y una HU
real deben validarse en el entorno destino. Los detalles y límites están en el
[registro de validación](artifacts/crea-manual-kit-0.1.3/docs/VALIDACION-KIT.md).

El contenido que debes llevar a un proyecto nuevo está en
[`artifacts/crea-manual-kit-0.1.3/`](artifacts/crea-manual-kit-0.1.3/), o en su ZIP.
Las carpetas raíz `src/`, `tests/`, `resources/`, `openspec/` y parte de `docs/` y
`scripts/` conservan el desarrollo anterior del motor Python Local-Harness.
Permanecen como antecedente técnico; no forman parte de la instalación del kit manual.

Para ampliar o personalizar el kit, consulta su
[LEEME](artifacts/crea-manual-kit-0.1.3/LEEME-CREA.md), el
[catálogo de skills](artifacts/crea-manual-kit-0.1.3/docs/catalogo-skills.md) y la
[guía de extensiones](artifacts/crea-manual-kit-0.1.3/docs/extensiones.md).
