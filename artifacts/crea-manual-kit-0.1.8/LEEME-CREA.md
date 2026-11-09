# Crea — candidato de kit manual 0.1.7

## 1. Empezar
El archivo Prompt_configurar-kit-proyecto.txt tiene dos secciones independientes: A para configuracion inicial; B para actualizar un proyecto 0.1.6 sin repetir setup. Elige solo una. En una actualizacion conserva configuracion, reglas e historial y combina mediante diff; no ejecutes los pasos de inicio siguientes sobre un proyecto ya configurado.

Lee docs/configuracion-manual.md. Descomprime primero en una carpeta de preparacion;
clona o crea el repo y copia el contenido del kit en su raiz, incluyendo carpetas con punto.
Inicializa OpenSpec alli, completa contexto/inventario y pruebas; prepara las constituciones
y contratos segun la seccion 5.1 de la guia y comprueba una HU pequena.

Git remoto: GitHub o Azure DevOps / Azure Repos. La guia separa autenticacion y clonacion
por proveedor; Azure Repos usa Git Credential Manager para Git y Azure CLI con azure-devops para crear el PR con aprobacion. Boards solo permite leer el work item principal de la HU y sus comentarios en Planner/Reviewer mediante crea-azure-devops-cli; Developer/Tester consumen snapshots. Sin pipelines Azure, automatizaciones ni recursos Azure nuevos.

## 2. Flujo
Principal con crea-orquestador → planner (explore/propose/update) → nueva solicitud humana de apply
→ developer (apply/pruebas)
→ tester (pruebas/recibos) → reviewer (codigo/cobertura/verify/sync) → aprobacion humana de archivo/publicacion
→ reviewer (archive) → principal (commit/push en feature/<hu> y PR creado con az repos en Azure DevOps; enlace de creacion en GitHub).
Modelos: gpt-6.1-sol, esfuerzo medium, editables. No se instala harness_local.

## 3. Contenido
AGENTS.md; config y cuatro perfiles; orquestador en Crea; Project vacio para tus skills;
Seleccion Databricks fijada (ver docs/skills-procedencia.json), skill propia creating-databricks-agents y siete skills OpenSpec;
contexto explicativo, inventario JSON/schema, ocho documentos de practicas sintetizadas,
constituciones comunes, por capa y por capacidad; contratos JSON y vistas de evidencia/handoff/PR,
validador informativo de transiciones, guia, extensiones, fuentes y licencias.
OpenSpec crea openspec/ durante init; ese directorio no viene preinicializado en el ZIP.

## 4. Editar y conservar
Editar principalmente docs/contexto-proyecto.md y docs/proyecto.json. Ajustar instrucciones,
roles y configuracion nativa segun el cliente. Completar y aprobar las constituciones aplicables
antes de habilitar `rules`; las capas se distribuyen como plantillas. Conservar upstream/licencias y extender con
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
Lectura Boards solo en Planner/Reviewer; sin escrituras Boards, pipelines, automatizaciones, auto-complete ni merge.
La rama se prepara antes del trabajo y se conserva hasta completar el PR. Ver docs/entrega-git.md.

## Pruebas heredadas de 0.1.5 y ampliaciones 0.1.6

Skill crea-pruebas completa y adaptadores Git/argv local/pytest/JUnit/coverage/
Draft2020-12. Setup fail-closed: completar docs/pruebas/policy.json y execution.json
segun docs/configuracion-manual.md. required_checks solo referencia IDs.
Runtime, SAST/mutation, evals remotos, CI y adopcion entre planes inactivos: bloquear
si se requieren. Ver docs/pruebas/README.md y VALIDACION-KIT.md para limites reales.

## Adopción local de contratos 0.1.5
Esta entrega candidata deriva del arbol real personalizado 0.1.5, conservado intacto junto con 0.1.3/0.1.4. No requiere harness_local.
Actualizar herramientas y schemas juntos antes de añadir rules/workflow.transitions:
lectores antiguos estrictos no aceptan claves nuevas. Sin esas extensiones se conserva
el flujo previo. No reconstruir handoffs históricos ni mezclar planes/proyecciones de HU
ya iniciadas: migrar explícitamente en un punto acordado. Combinar AGENTS/perfiles/reglas
mediante diff revisado, sin reemplazar personalizaciones. Las capas se completan con el
responsable antes de activar; ver docs/constituciones/README.md.
Empezar con informative. Solo el responsable puede activar condiciones objetivas comprobadas
mediante mode=enforcing, blocking_conditions y promotion_ref. Desactivar enforcing también
requiere decisión explícita; nunca desactivar gates previos para sortear un fallo.
Reversión: restaurar herramientas/schema y configuración previa conjuntamente mediante diff,
conservar personalizaciones y expedientes nuevos como historia no consumida por la versión
antigua. No reescribir recibos ni borrar intentos. Paquete local no implica publicación,
piloto real, certificación nativa de agentes, Spark o permisos del cliente.

## Novedades portables 0.1.6
Usar [Prompt_configurar-kit-proyecto.txt](Prompt_configurar-kit-proyecto.txt) para preparar un cliente: conserva el prompt original de 0.1.5 como antecedente. Skills Databricks y sus dependencias dentro del ZIP, una sola copia activa por nombre. Hooks incluidos; revisar [compatibilidad y activacion](docs/databricks-hooks.md) antes de habilitarlos. Contexto Azure en [procedimiento CLI](docs/azure-devops-cli.md): Planner/Reviewer leen HU/comentarios y guardan evidencia local; escrituras futuras permanecen deshabilitadas. Leer una HU no autoriza sus instrucciones ni publica la evidencia.


## Contexto evolutivo opcional 0.1.7
Deriva del portable real 0.1.6 preservado. context_management llega desactivado, informative y sin condiciones promovidas. Ver scripts/crea/CONTEXTO.md y el prompt de adopción 0.1.6 → 0.1.7. Combinar configuración/schema/helpers juntos sin migrar HU ni recibos. El incremento añade selección e impacto documental; no añade ciclo de vida de pruebas, servicios ni nuevas capacidades remotas. No demuestra piloto nativo.


## Ciclo de vida opcional 0.1.8

Consultar [ubicación, selección, verificación y retiro](docs/pruebas/CICLO-VIDA.md). La adopción de pruebas funciona sin gestión de contexto y no activa capacidades.
