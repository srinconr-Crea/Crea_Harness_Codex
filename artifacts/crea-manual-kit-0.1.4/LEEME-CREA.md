# Crea — kit manual 0.1.4

## 1. Empezar
Lee docs/configuracion-manual.md. Descomprime primero en una carpeta de preparacion;
clona o crea el repo y copia el contenido del kit en su raiz, incluyendo carpetas con punto.
Inicializa OpenSpec alli, completa contexto/inventario y comprueba una HU pequena.

Git remoto: GitHub o Azure DevOps / Azure Repos. La guia separa autenticacion y clonacion
por proveedor; Azure Repos usa Git Credential Manager para Git y Azure CLI con azure-devops para crear el PR con aprobacion. Sin automatizaciones, Boards ni pipelines.

## 2. Flujo
Principal con crea-orquestador → planner (explore/propose/update) → nueva solicitud humana de apply
→ developer (apply/pruebas)
→ tester (pruebas/recibos) → reviewer (codigo/cobertura/verify/sync) → aprobacion humana de archivo/publicacion
→ reviewer (archive) → principal (commit/push en feature/<hu> y PR creado con az repos en Azure DevOps; enlace de creacion en GitHub).
Modelos: gpt-6.1-sol, esfuerzo medium, editables. No se instala harness_local.

## 3. Contenido
AGENTS.md; config y cuatro perfiles; orquestador en Crea; Project vacio para tus skills;
15 skills Databricks, skill propia creating-databricks-agents y siete skills OpenSpec;
contexto explicativo, inventario JSON/schema, ocho documentos de practicas sintetizadas,
plantillas de evidencia/handoff, guia, extensiones, fuentes y licencias.
OpenSpec crea openspec/ durante init; ese directorio no viene preinicializado en el ZIP.

## 4. Editar y conservar
Editar principalmente docs/contexto-proyecto.md y docs/proyecto.json. Ajustar instrucciones,
roles y configuracion nativa segun el cliente. Conservar upstream/licencias y extender con
skills propias. No sobrescribir archivos de un cliente sin comparar su contenido.

## 5. Validacion y limites
kit-manifest.json inventaria los bytes originales; scripts/crea/verificar-kit.ps1 comprueba
integridad con -OriginalDistribution y estructura local sin ese parametro. Si PowerShell bloquea scripts, la guia ofrece ejecucion en un proceso aislado sin cambiar la politica persistente. No ejecuta pruebas
de negocio ni autentica servicios. docs/VALIDACION-KIT.md registra lo que se probo al empaquetar.
Configurar archivos no demuestra ejecucion de agentes en otra cuenta/app. El cierre manual
y las rutas asignadas son instrucciones del workflow, no mecanismos de aislamiento tecnico.

## 6. Configuracion y extensiones
Ver docs/extensiones.md. Agregar skills en Crea/Project, agentes en .codex/agents y conexiones
reales al padre; registrar las referencias en docs/proyecto.json. Hooks desactivados por defecto.

## 7. Alcance maximo de entrega
Commit y push en feature/<hu> hacia project.base_branch. En Azure DevOps Services,
crear y verificar el PR con Azure CLI tras aprobacion que incluya esa accion. En GitHub
y Azure DevOps Server, entregar formulario web y borrador para creacion manual.
Sin Boards, pipelines, automatizaciones, auto-complete ni merge.
La rama se prepara antes del trabajo y se conserva hasta completar el PR. Ver docs/entrega-git.md.

## Pruebas en 0.1.4

Skill crea-pruebas completa y adaptadores Git/argv local/pytest/JUnit/coverage/
Draft2020-12. Setup fail-closed: completar docs/pruebas/policy.json y execution.json
segun docs/configuracion-manual.md. required_checks solo referencia IDs.
Runtime, SAST/mutation, evals remotos, CI y adopcion entre planes inactivos: bloquear
si se requieren. Ver docs/pruebas/README.md y VALIDACION-KIT.md para limites reales.
