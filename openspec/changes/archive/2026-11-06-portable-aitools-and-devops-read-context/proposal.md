# Proposal

## Why

El kit portable 0.1.5 combina 15 skills Databricks de varias revisiones y no incluye los hooks oficiales operativos. Su alcance Azure DevOps permite entrega Git/PR, pero excluye leer work items y comentarios para planificar y revisar una HU.

## What Changes

- Preparar la siguiente distribución portable, propuesta como 0.1.6, preservando árboles, ZIP, hashes y cambios locales previos de 0.1.5. Un solo candidato reúne dos bloques verificables y evita empaquetados intermedios incompatibles.
- Actualizar las 15 skills Databricks desde Databricks AI Tools, incorporar una selección justificada de skills faltantes y cerrar dependencias, con revisión fijada, hashes y licencias. Una sola copia activa por nombre; no instalar otro plugin que vuelva a aportar las mismas skills.
- Incluir los tres hooks oficiales con sus dependencias y una integración opcional para el host Codex compatible, revisada para Windows. Distinguir incluido, configurado, autorizado y observado; no equiparar `extensions.hooks` a registro nativo.
- Añadir `crea-azure-devops-cli`, orientada por ayuda real del CLI y referencias oficiales de Microsoft. La única ampliación operativa será lectura de work items y comentarios de la HU en planner y reviewer, sin aprobación adicional por consulta.
- Conservar entrega Azure Repos existente: consultas de repo/PR y creación de PR exclusivamente por principal con autorización aplicable. Pipelines y otras operaciones nuevas continúan fuera de alcance.
- Documentar escritura futura de comentarios/work items como deshabilitada: existencia de comandos, credenciales o aprobación genérica no la activa.
- Registrar consultas, revisiones y cobertura de comentarios en evidencia local por HU/intento, sin ejecutar instrucciones de contenidos remotos.
- Actualizar README raíz, `LEEME-CREA.md`, guía/extensiones y `Prompt_configurar-kit-proyecto.txt` en la nueva distribución. El prompt de 0.1.5 indicado por el usuario es la fuente que se debe conservar e incorporar, no una plantilla que deba reconstruirse de memoria.

## Capabilities

### New Capabilities

- `portable-databricks-aitools`: selección portable mantenida y sin duplicados, procedencia reproducible y hooks opcionales observables.
- `azure-devops-cli-context`: orientación CLI con matriz de alcance y lectura acotada de work items/comentarios en planificación y revisión, con evidencia y escrituras futuras deshabilitadas.

### Modified Capabilities

- `manual-kit-distribution`: nueva entrega que conserva la fuente 0.1.5 y sus personalizaciones, e incluye README, prompt, documentación, inventario y validación consistentes con ambas capacidades.

## Impact

El destino de implementación será `artifacts/crea-manual-kit-0.1.6/`, un nuevo empaquetador y verificaciones asociadas. Cambiarán sus skills, hooks empaquetados, AGENTS, perfiles planner/reviewer, orquestación, JSON/schema de configuración, procedencia/licencias y documentación. No se conecta el motor histórico `harness_local`, ni se actualiza su snapshot de nueve skills como efecto lateral.

No se instalan herramientas, plugins o hooks globales durante esta propuesta. No hay login, consulta de datos privados, escritura remota, commit/push/PR, merge, deploy ni ejecución de pipelines. Ayuda CLI observada: Azure CLI 2.91.0 + azure-devops 1.0.9. La investigación y las tareas separan ayuda comprobada, documentación oficial y pruebas remotas aún no realizadas.
