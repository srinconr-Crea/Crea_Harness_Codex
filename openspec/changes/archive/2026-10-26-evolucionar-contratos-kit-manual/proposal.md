# Proposal

## Why

El kit manual Crea 0.1.4 ya organiza cuatro roles y pruebas con evidencia, pero sus handoffs descriptivos no comprueban las condiciones de cada transferencia ni comparten una selección explícita de reglas del proyecto. Se necesita conectar criterios, reglas, candidato, objetos y entrega sin repetir pruebas válidas, inventar despliegues o añadir otra cadena de ejecución.

## What Changes

- Incorporar constituciones comunes, por capa y capacidad, con identificadores y evidencia; separar obligaciones justificadas, plantillas de proyecto y especialidades pendientes. Planner, Developer y Reviewer consumirán la misma selección congelada para la HU.
- Evolucionar el handoff a un contrato JSON base y una presentación humana derivada, con requisitos distintos para planificación, implementación, pruebas, revisión y cierre. Conservar intentos y referencias canónicas.
- Incorporar `scripts/crea/transiciones.py`, invocado por el principal antes de continuar, prioritariamente antes de Apply y del cierre/publicación. Reutilizar schemas, Git y gate del kit; comenzar en modo informativo y habilitar bloqueos objetivos solo mediante configuración expresamente aprobada.
- Concretar lectura/escritura por rol y HU y detectar diferencias desde el último handoff, separándolas de cambios anteriores. Las instrucciones y el JSON no crearán permisos nativos ni interceptarán herramientas.
- Ampliar evidencia con inventario de objetos previstos, implementados, desplegados y verificados, sin inferir estados ni convertirlo en linaje operativo.
- Mantener una estructura canónica de contenido del PR para GitHub y Azure DevOps; transportar título/cuerpo revisados y distinguir borrador, formulario preparado y PR creado/verificado. Conservar GitHub manual y Azure Services por CLI autorizada.
- Preparar una siguiente entrega independiente, propuesta como 0.1.5, preservando 0.1.3 y 0.1.4, sus ZIP y hashes. La adopción en proyectos existentes será una combinación revisada, con extensiones opcionales y controles nuevos inicialmente informativos.

Esta solicitud produce **solo planificación**: no modifica código, perfiles, plantillas del producto, configuración estable ni distribuciones; no ejecuta Apply, Sync, Archive, empaquetado o publicación.

## Capabilities

### New Capabilities

- `manual-project-rules`: selección común de reglas de proyecto, gobierno proporcional y excepciones trazables para el kit manual.
- `manual-phase-contracts`: handoffs versionados, alcance por rol, comprobaciones de transición, vigencia y recuperación local sin repetir trabajo válido.
- `manual-delivery-traceability`: estados comprobables de objetos, resumen humano derivado y entrega coherente de contenido del PR por proveedor.
- `manual-kit-distribution`: evolución versionada del kit manual y adopción compatible sin alterar distribuciones anteriores.

### Modified Capabilities

Ninguna del motor histórico. Se inspeccionaron `hu-lifecycle`, `candidate-validation`, `client-configuration`, `story-pr-integration` y `harness-distribution`: sus contratos dependen de runtime/binding, workers, GitProvider o certificación histórica que no están conectados al kit manual. Los nombres nuevos delimitan esa implementación separada; no trasladan sus garantías ni cambian sus requisitos.

## Impact

Base comprobada: `README.md` identifica 0.1.4 como entrega principal y excluye la instalación de `harness_local`. El contenido mantenido está actualmente en `artifacts/crea-manual-kit-0.1.4/`; `scripts/integrate_testing_014.py`, `scripts/update_testing_docs_014.py` y `scripts/package_manual_014.py` componen/adaptan/empaquetan esa versión. No existe una fuente general del kit manual en `src/`; `src/harness_local/desktop_kit` pertenece al producto histórico.

En el futuro staging `artifacts/crea-manual-kit-0.1.5/` cambiarían `AGENTS.md`, los cuatro perfiles `.codex/agents/*.toml`, el orquestador Crea, `docs/proyecto.json` y su schema, plantillas de handoff/evidencia/PR, `docs/entrega-git.md`, documentación de pruebas y adaptadores compartidos. Se añadirían constituciones selectivas, un schema de handoff, el pequeño validador y pruebas focalizadas. `design.md` enumera rutas y contratos concretos, incluida la adaptación necesaria para que registros derivados no invaliden circularmente las pruebas.

Las rutas `docs/...` y `scripts/crea/...` de esta propuesta son relativas al repositorio **consumidor**; en desarrollo se materializarían dentro del nuevo staging versionado. La configuración y reglas de cada cliente se completan en su repositorio, nunca con datos de un cliente en el kit genérico.

Se reutilizan Python/jsonschema y los adaptadores existentes, sin nuevo runtime, BD, agentes, fases, dossier obligatorio, auditoría universal, clasificador de riesgo avanzado, Boards, integraciones remotas, merge o despliegue. La aprobación de esta propuesta no autoriza Apply ni publicar una versión. Versión final, reglas propias del cliente y promoción de condiciones bloqueantes quedan sujetas a revisión explícita.
