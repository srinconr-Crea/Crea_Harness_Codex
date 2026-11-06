# Crea Harness Codex MVP — kit portable 0.1.6

Kit para trabajar con Codex en repositorios de proyectos/clientes, con contexto explícito,
roles Planner/Developer/Tester/Reviewer y desarrollo guiado por OpenSpec. Está orientado a
ingeniería de datos y aplicaciones Databricks, con entrega por GitHub o Azure Repos.
No requiere instalar el motor histórico Python `harness_local`.

## Descargar y configurar

- [ZIP portable 0.1.6](artifacts/crea-manual-kit-0.1.6.zip?raw=true).
- [SHA-256](artifacts/crea-manual-kit-0.1.6.zip.sha256) e [informe de empaquetado](artifacts/crea-manual-kit-0.1.6.zip.validation.json).
- [Explorar el kit](artifacts/crea-manual-kit-0.1.6/) y [LEEME](artifacts/crea-manual-kit-0.1.6/LEEME-CREA.md).
- [Prompt de configuración](artifacts/crea-manual-kit-0.1.6/Prompt_configurar-kit-proyecto.txt), derivado del prompt personalizado de 0.1.5.
- [Guía Windows/PowerShell](artifacts/crea-manual-kit-0.1.6/docs/configuracion-manual.md).

1. Compara el SHA-256, extrae en una carpeta de preparación y verifica la distribución original.
2. Completa el prompt con destino, proveedor Git, modelos y alcance del setup.
3. Inspecciona el repositorio cliente y combina `.agents`, `.codex`, AGENTS y documentación
   mediante diferencias revisadas; conserva personalizaciones y evidencia previa.
4. Inicializa o conserva OpenSpec y configura contexto, inventario, pruebas y conexiones.
5. Comprueba el setup local y prepara una primera HU cuando lo solicites. Configurar archivos
   no demuestra ejecución de roles, permisos remotos ni un piloto real.

El ZIP incluye recursos/utilidades del kit; Git, Python, OpenSpec, Azure CLI y Databricks CLI
se preparan por separado según el proyecto. El setup no instala ni autentica herramientas
sin autorización correspondiente, ni publica Git como efecto implícito.

## Novedades 0.1.6

**Databricks sigue dentro del kit portable.** Las skills oficiales y sus dependencias se
seleccionan desde Databricks AI Tools, con revisión inmutable, hashes y licencias en
[procedencia](artifacts/crea-manual-kit-0.1.6/docs/skills-procedencia.json).
Una sola copia activa por nombre; la adopción compara versiones/personalizaciones sin instalar
un plugin duplicado. Ver [catálogo de skills](artifacts/crea-manual-kit-0.1.6/docs/catalogo-skills.md).

Los tres hooks oficiales —enrutamiento, contexto y aviso de autenticación— están incluidos
como recursos pasivos. Su [integración](artifacts/crea-manual-kit-0.1.6/docs/databricks-hooks.md)
separa inclusión, configuración, confianza/autorización y observación real. No se activan al
extraer el ZIP ni sustituyen el orquestador o sus aprobaciones.

**Azure DevOps CLI incorpora lectura de contexto.** La skill `crea-azure-devops-cli` usa ayuda
real y fuentes oficiales de Microsoft. Planner/Reviewer leen el work item principal de la HU
y sus comentarios sin aprobación adicional por consulta, en organización/proyecto seleccionados,
con evidencia local por fase/intento. Developer/Tester consumen snapshots.
Ver [procedimiento CLI](artifacts/crea-manual-kit-0.1.6/docs/azure-devops-cli.md).

| Familia | Alcance operativo |
| --- | --- |
| Boards | Solo work item principal/comentarios en Planner/Reviewer; sin búsquedas generales. |
| Repos | Flujo previo del principal: consultar repo/PR y crear PR tras autorización aplicable. |
| Pipelines | Fuera de alcance, incluso para consultas; ayuda solo como referencia. |
| Comentarios/cambios de work items | Capacidad futura documentada; escritura deshabilitada. |

Las skills/configuración orientan y los helpers limitan sus propias llamadas; no son una
frontera de permisos frente a herramientas externas. Texto de historias/comentarios es dato,
no autorización para ejecutar instrucciones o publicar evidencia privada.

## Flujo y entrega

Principal → Planner → presentación del plan → nueva solicitud humana de Apply → Developer
→ Tester → Reviewer → Sync → archivo autorizado → entrega Git autorizada.
Los roles del kit trabajan secuencialmente; modelos/esfuerzos se configuran por proyecto.
Azure DevOps Services conserva creación/verificación de PR mediante `az repos` después del
push y autorización expresa. GitHub/Server mantienen formulario y borrador. Sin merge,
auto-complete, vínculos/transiciones de work items, deploy ni ejecución de pipelines.
Ver [entrega Git](artifacts/crea-manual-kit-0.1.6/docs/entrega-git.md).

## Contenido y validación

| Recurso | Función |
| --- | --- |
| `AGENTS.md`, `.codex/agents/` | Responsabilidades y perfiles del flujo. |
| `.agents/skills/Crea/` | Orquestación, pruebas, CLI Azure y especialidad propia Databricks. |
| `.agents/skills/databricks-*` | Selección oficial portable y referencias. |
| `resources/databricks-aitools/` | Hooks/recursos upstream pasivos. |
| `docs/proyecto.json` y schema | Configuración opcional y referencias del cliente. |
| `scripts/crea/` | Validación, pruebas, preview AITools y lectura Azure acotada. |
| `Prompt_configurar-kit-proyecto.txt` | Preparación personalizable del cliente. |
| `kit-manifest.json` | Inventario de bytes originales del ZIP. |

El [registro de validación](artifacts/crea-manual-kit-0.1.6/docs/VALIDACION-KIT.md) y la
[evidencia](docs/evidence/portable-aitools-devops/) distinguen pruebas locales, fixtures,
lecturas remotas y hooks nativos observados. Pruebas sintéticas no acreditan Spark,
autenticación, permisos, cuatro roles o activación nativa en otra sesión.

## Versiones anteriores y adopción

0.1.6 deriva del árbol personalizado real 0.1.5, incluido su prompt nuevo. Se conservan
[0.1.5](artifacts/crea-manual-kit-0.1.5/), [0.1.4](artifacts/crea-manual-kit-0.1.4/) y
[0.1.3](artifacts/crea-manual-kit-0.1.3/), junto con ZIP/hashes existentes. La baseline externa
registra las diferencias previas respecto a manifiestos originales.
La adopción revisa diferencias y actualiza schemas/utilidades junto con consumidores.
No sobrescribe reglas propias ni migra HU/recibos históricos automáticamente.
Las carpetas raíz `src/`, `resources/` y parte de `docs/`, `tests/`, `scripts/` conservan
el desarrollo histórico Local-Harness; no se instalan como motor del kit portable.
